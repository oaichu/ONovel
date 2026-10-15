#!/usr/bin/env python3
"""stylegate.py check <book_dir> <chapter.md> [--no-llm]  -> JSON {chapter, issues[], llm_error}
REWRITTEN 2026-10-15 (minimal). Deterministic checks: Han/CJK, emoji, em dash, curly quotes, banned words from the style
bible front matter (`banned:`), heading/layout, length. Then one MiMo pass for genre drift, xưng hô by speaker identity,
POV leaks. Issue fields: para, source, word, reason, quote. Exit 0 = no issues (layout ignored), 1 = issues, 2 = error.
Words listed under `llm_only:` in the bible are never grepped (e.g. 'tôi' in xianxia), only judged by the LLM."""
import sys, os, re, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mimo, bookfiles as bf
MODEL = mimo.MODEL
HAN = re.compile(r"[\u3400-\u9fff\uf900-\ufaff\u3000-\u303f\uff00-\uffef\u3040-\u30ff\uac00-\ud7af]")
EMOJI = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2190-\u21FF\u25A0-\u25FF\u200b-\u200f\ufeff]")
def grep_issues(text, meta):
    issues = []; ps = bf.paras(text)
    llm_only = set(w.lower() for w in (meta.get("llm_only") or []))
    banned = [w for w in (meta.get("banned") or []) if isinstance(w, str) and w.lower() not in llm_only]
    for i, p in enumerate(ps):
        q = p[:200]
        if HAN.search(p): issues.append(dict(para=i, source="han-script", word=HAN.search(p).group(0), reason="chữ Hán/CJK", quote=q))
        if EMOJI.search(p): issues.append(dict(para=i, source="symbol", word=EMOJI.search(p).group(0), reason="icon/ký hiệu lạ", quote=q))
        if "—" in p: issues.append(dict(para=i, source="em-dash", word="—", reason="cấm dấu gạch dài, thay bằng dấu phẩy", quote=q))
        if re.search(r"[“”]", p): issues.append(dict(para=i, source="quotes", word="“”", reason="thoại dùng ngoặc kép thẳng", quote=q))
        for w in banned:
            if re.search(r"(?<![\wÀ-ỹ])" + re.escape(w) + r"(?![\wÀ-ỹ])", p, re.I):
                issues.append(dict(para=i, source="banned-grep", word=w, reason="từ cấm theo style bible", quote=q))
    lay = meta.get("layout") or {}
    first = text.lstrip().split("\n", 1)[0]
    if not re.match(r"#\s*Chương\s+\d+", first): issues.append(dict(para=0, source="layout", word="heading", reason="dòng đầu phải là '# Chương N...'", quote=first[:120]))
    rng = lay.get("length_words")
    if isinstance(rng, list) and len(rng) == 2:
        n = len(text.split())
        if not (rng[0] * 0.8 <= n <= rng[1] * 1.3): issues.append(dict(para=0, source="layout", word="length", reason=f"{n} chữ ngoài khoảng {rng}", quote=""))
    return issues
def llm_issues(text, bible):
    prompt = ("Bạn là cổng kiểm tra văn phong cho truyện tiếng Việt. Đối chiếu CHƯƠNG với STYLE BIBLE (đã khóa). Chỉ báo lỗi THẬT: "
      "lệch thể loại/giọng, từ hiện đại hoặc cổ trang sai bối cảnh, xưng hô sai theo danh tính người nói (tiên hiệp: chỉ phàm nhân xưng 'tôi'), "
      "lỗi ngôi kể (lách vào đầu nhân vật khác khi POV giới hạn). Không báo lỗi chính tả vặt. Từ vựng mà style bible cho phép "
      "(register, allowed, thuật ngữ đặc thù của truyện như từ kiểm toán/tài chính trong truyện tiên hiệp kiểm toán) KHÔNG phải lỗi. "
      "Chỉ báo khi chắc chắn từ đó phá bối cảnh. KHÔNG liệt kê từ hợp lệ, không ghi mục 'bỏ qua'. Tối đa 15 lỗi nghiêm trọng nhất. Trả về JSON "
      '{"issues":[{"para":<số đoạn từ 0>,"reason":"...","word":"...","quote":"<trích nguyên văn ≤200 ký tự>"}]}'
      "\n\nSTYLE BIBLE:\n" + bible[:14000] + "\n\nCHƯƠNG (các đoạn cách nhau dòng trống):\n" + text)
    r = mimo.chat_json(prompt, max_tokens=6000)
    out = r.get("issues", []) if isinstance(r, dict) else r
    NOISE = re.compile(r"hợp lệ|bỏ qua|không phải lỗi|chấp nhận được|có thể chấp nhận|không mâu thuẫn|không sai|vẫn ổn|phù hợp", re.I)
    out = [v for v in out if isinstance(v, dict) and not NOISE.search(str(v.get("reason", "")))]
    low = text.lower()
    out = [v for v in out if not v.get("word") or str(v["word"]).lower() in low]  # flagged word must exist in the chapter
    for v in out: v["source"] = "llm"
    return out
def check(book, chap, use_llm=True):
    text = open(chap, encoding="utf-8").read(); meta, bible = bf.load_bible(book)
    allowed = [w.lower() for w in (meta.get("allowed") or []) if isinstance(w, str)]
    issues = grep_issues(text, meta); err = None
    if use_llm and bible:
        try: issues += [v for v in llm_issues(text, bible) if str(v.get("word", "")).lower().strip() not in allowed]
        except Exception as e: err = f"{type(e).__name__}: {e}"[:300]
    return {"chapter": chap, "issues": issues, "llm_error": err}
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["check"]); ap.add_argument("book"); ap.add_argument("chapter")
    ap.add_argument("--no-llm", action="store_true"); a = ap.parse_args()
    try: r = check(a.book, a.chapter, not a.no_llm)
    except Exception as e: print(json.dumps({"chapter": a.chapter, "error": str(e)}, ensure_ascii=False)); sys.exit(2)
    print(json.dumps(r, ensure_ascii=False, indent=2)); sys.exit(1 if [i for i in r["issues"] if i.get("source") != "layout"] else 0)
