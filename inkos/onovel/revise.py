"""Revision pass for an existing chapter under the book's min_words: 'expand missing scenes' on free models (expand.py,
up to ONOVEL_EXPAND_ROUNDS rounds), MiMo polish (tools/polish.py), full gates (+ up to 3 MiMo fix rounds), then
txn.revise_commit (republished later by publish-inkos.sh). Text is only changed by the LLM passes and scripts."""
import os, re, json, shutil, subprocess, sys, time
from . import TOOLS, state, gates, txn, expand, context, manifest as mf
def _log(rd, s):
    line = f"[{time.strftime('%H:%M:%S')}] {s}"; print(line, file=sys.stderr)
    open(os.path.join(rd, "run.log"), "a", encoding="utf-8").write(line + "\n")
def revise_expand(book, n, runs=None):
    m = mf.load(book); lay = m["layout"]; MIN = lay.get("min_words", 3000); TGT = lay.get("target_words", 3200)
    fs = [f for f in state.chapter_files(book) if int(re.match(r"\d+", f).group(0)) == n]
    if not fs: return {"n": n, "status": "MISSING"}
    f = os.path.join(book, "chapters", fs[0]); text = open(f, encoding="utf-8").read(); w0 = gates.count_words(text)
    if w0 >= MIN: return {"n": n, "status": "OK", "words": w0}
    runs = runs or os.environ.get("ONOVEL_RUNS", os.path.join(os.path.dirname(TOOLS), "runs"))
    rd = os.path.join(runs, f"{m['id']}-{n:04d}-rev-{time.strftime('%Y%m%dT%H%M%S')}"); os.makedirs(rd)
    _log(rd, f"revise-expand {m['id']} ch{n}: {w0} < {MIN} words")
    open(os.path.join(rd, "draft.md"), "w", encoding="utf-8").write(text)
    row = state.chapter(book, n) or {}
    open(os.path.join(rd, "plan.md"), "w", encoding="utf-8").write("(Chương đã có; chỉ mở rộng, KHÔNG đổi sự kiện, tên, kết cục.)\nTóm tắt: " + (row.get("summary") or ""))
    ctx = context.build(book, n); open(os.path.join(rd, "context.md"), "w", encoding="utf-8").write(ctx)
    rounds = int(os.environ.get("ONOVEL_EXPAND_ROUNDS", 4)); bib = os.path.join(book, m["style_profile"]); w = w0
    for k in range(1, rounds + 1):
        w = expand.expand(rd, int(MIN * 1.05), TGT, passes=1, log=lambda s: _log(rd, s))
        if w == -4: return {"n": n, "status": "LLM_BLOCKED"}
        if w >= MIN * 1.05: break
    if w < MIN:
        dst = txn.revise_quarantine(book, rd, n, f"still {w} < {MIN} after {rounds} expand rounds"); _log(rd, "quarantined (too short)")
        return {"n": n, "status": "QUARANTINED", "words": [w0, w], "reason": "short", "run": dst}
    pr = subprocess.run([sys.executable, os.path.join(TOOLS, "polish.py"), os.path.join(rd, "draft.md"), "--bible", bib, "--out", os.path.join(rd, "chapter.md")], capture_output=True, text=True)
    _log(rd, "polish: " + pr.stdout.strip()[-300:])
    if not os.path.exists(os.path.join(rd, "chapter.md")): shutil.copy(os.path.join(rd, "draft.md"), os.path.join(rd, "chapter.md"))
    subprocess.run([sys.executable, os.path.join(TOOLS, "normalize-headings.py"), "--style", lay["heading_style"], os.path.join(rd, "chapter.md")], capture_output=True)
    chap = os.path.join(rd, "chapter.md"); noncanon = lambda b, c, k: gates.verdict("canon", c, open(c, encoding="utf-8").read(), [], [], [], None, llm=False)
    sm = mf.get(m, "soft_max")
    if len((txn.load(book, n) or {}).get("revision_failures", [])) >= mf.get(m, "max_attempts") - 1: sm = 999  # same attempt policy as novel.sh
    def gate():
        g = gates.run_all(book, chap, n, use_llm=True, soft_max=sm, canon=noncanon)
        open(os.path.join(rd, "gate.json"), "w", encoding="utf-8").write(json.dumps(g, ensure_ascii=False, indent=1)); _log(rd, "gate: " + gates.summary(g)); return g
    g = gate()
    for k in range(3):
        if g["verdict"] != "FAIL": break
        open(os.path.join(rd, "fix.txt"), "w", encoding="utf-8").write(gates.fix_list(g))
        r = subprocess.run([sys.executable, os.path.join(TOOLS, "fix.py"), chap, os.path.join(rd, "fix.txt")], capture_output=True, text=True); _log(rd, "fix: " + r.stdout.strip()[-200:])
        g = gate()
    w1 = gates.count_words(open(chap, encoding="utf-8").read())
    if g["verdict"] != "PASS":
        dst = txn.revise_quarantine(book, rd, n, gates.summary(g)); return {"n": n, "status": "QUARANTINED", "words": [w0, w1], "reason": gates.summary(g), "run": dst}
    try: txn.revise_commit(book, rd, n, f)
    except txn.TxnError as e:
        dst = txn.revise_quarantine(book, rd, n, str(e)); return {"n": n, "status": "QUARANTINED", "words": [w0, w1], "reason": str(e), "run": dst}
    _log(rd, f"REVISED ch{n}: {w0} -> {w1} words"); return {"n": n, "status": "REVISED", "words": [w0, w1]}
