#!/usr/bin/env python3
"""stylegate.py check <book_dir> <chapter.md> [--no-llm]  -> gate verdict JSON (onovel/gates schema), exit 0 PASS / 1 FAIL / 2 ERROR.
Deterministic rules (blocking): Han/CJK, emoji, em dash, curly quotes, banned words (style bible `banned:`; `llm_only:` words are
never grepped). Layout (heading, length) is blocking or a warning per book manifest layout.blocking. Then one structured MiMo
judge (onovel/judge.py) for genre drift, xưng hô by speaker identity (cultivators never say 'tôi'), POV leaks: soft issues.
A judge error is ERROR, never PASS. Rewritten 2026-10-16 (ONovel audit P0.1/P0.2/P1.3)."""
import sys, os, re, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import mimo, bookfiles as bf
from onovel import gates
MODEL = mimo.MODEL
HAN = re.compile(r"[\u3400-\u9fff\uf900-\ufaff\u3000-\u303f\uff00-\uffef\u3040-\u30ff\uac00-\ud7af]")
EMOJI = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2190-\u21FF\u25A0-\u25FF\u200b-\u200f\ufeff]")
def I(rule, para, word, reason, quote, source="rule", severity="high"):
    return dict(rule_id=rule, source=source, severity=severity, confidence=1.0, evidence_span=quote[:200], reason=reason, word=word, para=para)
def rule_issues(text, meta):
    out = []; ps = bf.paras(text)
    llm_only = set(w.lower() for w in (meta.get("llm_only") or []))
    banned = [w for w in (meta.get("banned") or []) if isinstance(w, str) and w.lower() not in llm_only]
    for i, p in enumerate(ps):
        if i == 0 and p.lstrip().startswith("#"): continue
        q = p[:200]
        if HAN.search(p): out.append(I("han-script", i, HAN.search(p).group(0), "chữ Hán/CJK", q))
        if EMOJI.search(p): out.append(I("symbol", i, EMOJI.search(p).group(0), "icon/ký hiệu lạ", q))
        if "—" in p: out.append(I("em-dash", i, "—", "cấm dấu gạch dài, thay bằng dấu phẩy", q))
        if re.search(r"[“”]", p): out.append(I("quotes", i, "“”", "thoại dùng ngoặc kép thẳng", q))
        for w in banned:
            if re.search(r"(?<![\wÀ-ỹ])" + re.escape(w) + r"(?![\wÀ-ỹ])", p, re.I): out.append(I("banned-word", i, w, "từ cấm theo style bible", q))
    return out
def layout_issues(text, meta, man):
    out = []; first = text.lstrip().split("\n", 1)[0]
    if not re.match(r"#\s*Chương\s+\d+", first): out.append(I("layout-heading", 0, "heading", "dòng đầu phải là '# Chương N...'", first[:120]))
    lay = (man or {}).get("layout") or {}; n = gates.count_words(text)
    lo = lay.get("min_words"); hi = lay.get("max_words")
    rng = (meta.get("layout") or {}).get("length_words")
    if lo is None and isinstance(rng, list) and len(rng) == 2: lo, hi = int(rng[0] * 0.8), int(rng[1] * 1.3)
    if (lo and n < lo) or (hi and n > hi): out.append(I("layout-length", 0, "length", f"{n} chữ ngoài khoảng [{lo}, {hi}]", ""))
    return out
def llm_issues(text, bible, chat=None):
    from onovel import judge
    task = ("Bạn là cổng kiểm tra văn phong cho truyện tiếng Việt. Đối chiếu CHƯƠNG với STYLE BIBLE (đã khóa). Chỉ báo lỗi THẬT, có trích dẫn nguyên văn: "
      "lệch thể loại/giọng (rule_id genre-drift), từ hiện đại hoặc cổ trang sai bối cảnh (anachronism), xưng hô sai theo danh tính người nói, "
      "tu sĩ xưng 'tôi' (xung-ho), lỗi ngôi kể khi POV giới hạn (pov-leak). Từ vựng style bible cho phép KHÔNG phải lỗi. "
      "Tối đa 15 mục.\n\nSTYLE BIBLE:\n" + bible[:14000] + "\n\nCHƯƠNG (các đoạn cách nhau dòng trống):\n" + text)
    return judge.judge(task, text, chat=chat)
def check(book, chap, use_llm=True, chat=None):
    from onovel import manifest as mf
    text = open(chap, encoding="utf-8").read(); meta, bible = bf.load_bible(book)
    try: man = mf.load(book)
    except mf.ManifestError: man = None
    allowed = {w.lower() for w in (meta.get("allowed") or []) if isinstance(w, str)}
    blocking = rule_issues(text, meta); warnings = []
    blk = set(((man or {}).get("layout") or {}).get("blocking", ["heading"]))
    for v in layout_issues(text, meta, man): (blocking if v["rule_id"].split("-", 1)[1] in blk else warnings).append(v)
    soft = []; err = None
    if use_llm and bible:
        try: soft = [v for v in llm_issues(text, bible, chat) if v["word"].lower().strip() not in allowed]
        except Exception as e: err = f"{type(e).__name__}: {e}"[:300]
    return gates.verdict("style", chap, text, blocking, soft, warnings, err, llm=use_llm)
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["check"]); ap.add_argument("book"); ap.add_argument("chapter")
    ap.add_argument("--no-llm", action="store_true"); a = ap.parse_args()
    try: r = check(a.book, a.chapter, not a.no_llm)
    except Exception as e: r = gates.error("style", a.chapter, f"{type(e).__name__}: {e}")
    print(json.dumps(r, ensure_ascii=False, indent=2)); sys.exit(gates.EXIT[r["verdict"]])
