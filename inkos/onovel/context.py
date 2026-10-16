"""Semantic context retrieval for plan/draft (replaces byte truncation; ONovel audit P1.1).
Builds context for chapter N within a token budget (ONOVEL_CTX_TOKENS, default 18000; ~3 chars/token for Vietnamese):
  guardrails, style bible (front matter + body cut at paragraph boundaries), lessons, genre skills,
  outline blocks scored by chapter range (Ch 5–16 / Chapters 1–40 / Chương 10-20) and term overlap with the previous ending,
  visibility window (blocks whose range starts after N are never included), canonical state: current snapshot, last
  summaries, relevant characters/roles, locked facts (relevant first), open plot debts / promises / secrets visible at N,
  and the previous chapter's ending cut at a paragraph boundary."""
import os, re, glob, subprocess, sys
from . import TOOLS, state, manifest as mf
CPT = 3.0
def tok(s): return int(len(s) / CPT) + 1
def cut(text, budget, tail=False):
    """Cut to `budget` tokens at paragraph boundaries (never mid-paragraph unless one paragraph exceeds the budget)."""
    if tok(text) <= budget: return text
    ps = re.split(r"\n\s*\n", text); out = []; used = 0
    for p in (reversed(ps) if tail else ps):
        t = tok(p) + 1
        if used + t > budget:
            if not out: out.append(p[-int(budget * CPT):] if tail else p[:int(budget * CPT)])
            break
        out.append(p); used += t
    return "\n\n".join(reversed(out) if tail else out)
RANGE = re.compile(r"(?:Ch(?:apters?|ương|\.)?|chương)\s*(\d+)\s*(?:[-–~]|đến|to)\s*(\d+)", re.I)
SINGLE = re.compile(r"(?:Ch(?:apter|ương|\.)?|chương)\s+(\d+)\b", re.I)
def words(s): return {w for w in re.findall(r"[\wÀ-ỹ]{3,}", s.lower())}
def outline_blocks(book):
    files = sorted(glob.glob(os.path.join(book, "story", "outline", "*.md"))) + [p for p in (os.path.join(book, "de-cuong.md"),) if os.path.exists(p)]
    out = []
    for f in files:
        t = open(f, encoding="utf-8").read(); cur = None
        for blk in re.split(r"\n\s*\n|\n(?=#)", t):
            b = blk.strip()
            if not b: continue
            m = RANGE.search(b) or None
            rng = (int(m.group(1)), int(m.group(2))) if m else None
            if not rng:
                s = SINGLE.search(b); rng = (int(s.group(1)), int(s.group(1))) if s else None
            if b.startswith("#") and len(b) < 200 and not rng: cur = b; continue  # heading line: carry as label
            out.append(dict(file=os.path.basename(f), heading=cur, text=b, range=rng, idx=len(out)))
    return out
def pick_outline(book, n, query, budget):
    qs = words(query); picked = []
    for b in outline_blocks(book):
        r = b["range"]
        if r and r[0] > n: continue  # visibility window: no future arcs
        score = 0.0
        if r and r[0] <= n <= r[1]: score += 100
        elif r: score -= min(50, (n - r[1]) / 5)
        if b["file"].startswith("story_frame") and b["idx"] < 3: score += 30
        ov = len(words(b["text"]) & qs); score += min(40, ov * 2)
        picked.append((score, b))
    picked.sort(key=lambda x: -x[0]); out = []; used = 0
    for sc, b in picked:
        t = tok(b["text"])
        if sc <= 0 or used + t > budget: continue
        out.append(b); used += t
    out.sort(key=lambda b: (b["file"], b["idx"]))
    return "\n\n".join(((b["heading"] + "\n") if b["heading"] else "") + b["text"] for b in out)
def prev_ending(book, n, budget):
    fs = [f for f in state.chapter_files(book) if int(re.match(r"\d+", f).group(0)) == n - 1]
    if not fs: return ""
    return cut(open(os.path.join(book, "chapters", fs[0]), encoding="utf-8").read(), budget, tail=True)
def roles(book, query, budget):
    qs = words(query); items = []
    for f in glob.glob(os.path.join(book, "story", "roles", "**", "*.md"), recursive=True):
        t = open(f, encoding="utf-8").read(); name = os.path.splitext(os.path.basename(f))[0]
        items.append((len(words(name) & qs) * 10 + len(words(t[:2000]) & qs) / 50, f"### {name}\n{t}"))
    items.sort(key=lambda x: -x[0]); out = []; used = 0
    for sc, t in items:
        t = cut(t, max(200, budget // 3))
        if used + tok(t) > budget: continue
        out.append(t); used += tok(t)
    return "\n\n".join(out)
def run(cmd):
    try: return subprocess.run(cmd, capture_output=True, text=True, timeout=120).stdout
    except Exception: return ""
def build(book, n, budget=None, hint=""):
    budget = budget or int(os.environ.get("ONOVEL_CTX_TOKENS", 18000))
    meta_txt = ""; B = {k: int(budget * v) for k, v in dict(bible=.18, lessons=.05, skills=.12, outline=.17, state=.10, summaries=.07,
                                                              roles=.06, facts=.08, debts=.06, prev=.08).items()}
    bible_p = os.path.join(book, "style-bible.md")
    try: man = mf.load(book); bible_p = os.path.join(book, man["style_profile"])
    except mf.ManifestError: man = None
    bible = open(bible_p, encoding="utf-8").read() if os.path.exists(bible_p) else ""
    prev = prev_ending(book, n, B["prev"]); cs = cut(state.current_state(book), B["state"])
    query = prev + "\n" + cs + "\n" + hint
    facts = state.active_facts(book, n); qs = words(query)
    facts.sort(key=lambda f: -(len(words(f.get("entity", "")) & qs) * 5 + len(words(f.get("fact", "")) & qs)))
    ftxt = []; used = 0
    for f in facts:
        line = f"- [{f['id']}] ({f.get('entity','')}) {f['fact']}"
        if used + tok(line) > B["facts"]: break
        ftxt.append(line); used += tok(line)
    debts = []; used = 0
    for d in sorted(state.open_foreshadowing(book, n), key=lambda d: -len(words(d["content"]) & qs)):
        line = f"- (ch{d['planted_chapter'] or 0}) {d['content']}"
        if used + tok(line) > B["debts"] * 0.6: break
        debts.append(line); used += tok(line)
    for p in state.open_promises(book): debts.append(f"- LỜI HỨA ch{p['made_chapter']}: {p['who']} → {p['to_whom']}: {p['content']}" + (f" (hạn ch{p['due_chapter']})" if p.get("due_chapter") else ""))
    for s in state.secrets(book): debts.append(f"- BÍ MẬT: {s['content']} | người biết: {', '.join(s['knowers']) or 'chưa ai'}")
    ents = [f"- {e['kind']} {e['name']}: " + ", ".join(f"{k}={v}" for k, v in e["attrs"].items() if k != "realm_history") for e in state.entities(book)
            if words(e["name"]) & qs][:40]
    summ = "\n".join(f"## Chương {r['n']}\n{r['summary']}" for r in state.summaries(book, last=3, before=n))
    if not summ:
        p = os.path.join(book, "story", "chapter_summaries.md")
        summ = cut(open(p, encoding="utf-8").read(), B["summaries"], tail=True) if os.path.exists(p) else ""
    guard = os.path.join(TOOLS, "editor-guardrails.md")
    parts = [("# QUY TẮC BIÊN TẬP", open(guard, encoding="utf-8").read() if os.path.exists(guard) else ""),
             ("", cut(run([sys.executable, os.path.join(TOOLS, "lessons.py"), "prompt", book]), B["lessons"])),
             ("", cut(run([sys.executable, os.path.join(TOOLS, "skills.py"), "prompt", book, "--max", str(int(B["skills"] * CPT))]), B["skills"])),
             ("# STYLE BIBLE (KHÓA)", cut(bible, B["bible"])),
             ("# TRẠNG THÁI HIỆN TẠI", cs), ("# TÓM TẮT CÁC CHƯƠNG GẦN NHẤT", cut(summ, B["summaries"], tail=True)),
             ("# NHÂN VẬT LIÊN QUAN", "\n".join(ents) + "\n\n" + roles(book, query, B["roles"])),
             ("# SỰ THẬT ĐÃ KHÓA", "\n".join(ftxt)), ("# NỢ CỐT TRUYỆN (phục bút / lời hứa / bí mật đang mở)", cut("\n".join(debts), B["debts"])),
             (f"# ĐỀ CƯƠNG (phần liên quan chương {n})", pick_outline(book, n, query, B["outline"])),
             ("# ĐOẠN CUỐI CHƯƠNG TRƯỚC", prev)]
    return "\n\n".join((h + "\n" + t.strip()) if h else t.strip() for h, t in parts if t and t.strip()) + "\n"
