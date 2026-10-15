#!/usr/bin/env python3
"""polish.py <chapter.md> [--bible style-bible.md] [--out file] : MiMo polish pass (REWRITTEN 2026-10-15, minimal).
Keeps heading, plot, names; rejects output if length drifts >15%, names lost, Han chars or em dash appear.
Exports names(text), HAN for other tools."""
import sys, os, re, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mimo
HAN = re.compile(r"[\u3400-\u9fff\uf900-\ufaff\u3000-\u303f\uff00-\uffef]")
_STOP = set("Chương Hắn Nàng Ta Ngươi Nhưng Rồi Khi Một Cái Không Đó Này Lúc Sau Trong Ngay Thế Vậy Còn Đã Và Thì Là Có".split())
def names(t):
    """Capitalised multi-word Vietnamese proper names (rough)."""
    out = set()
    for m in re.finditer(r"(?<![.!?\"\n]\s)\b([A-ZĐÀ-Ỹ][a-zà-ỹđ]+(?:\s[A-ZĐÀ-Ỹ][a-zà-ỹđ]+)+)", t):
        n = m.group(1)
        if all(w[0].isupper() for w in n.split()) and n.split()[0] not in _STOP: out.add(n)
    return out
def polish(text, bible=""):
    head, rest = (text.split("\n", 1) + [""])[:2] if text.lstrip().startswith("#") else ("", text)
    prompt = ("Bạn là biên tập viên văn học tiếng Việt. Trau chuốt chương dưới đây: câu chữ tự nhiên, nhịp văn mượt, bỏ lặp từ, "
      "giữ NGUYÊN cốt truyện, sự kiện, tên riêng, số cảnh, xưng hô theo style bible. Thoại trong ngoặc kép thẳng \"...\". "
      "Cấm dấu gạch dài (—), cấm chữ Hán, icon, ghi chú. Chỉ trả về toàn văn (không tiêu đề).\n\nSTYLE BIBLE:\n"
      + bible[:12000] + "\n\nCHƯƠNG:\n" + rest.strip())
    out = mimo.chat(prompt, temperature=0.4)
    if out.lstrip().startswith("#"): out = out.split("\n", 1)[1] if "\n" in out else ""
    wd, wo = len(rest.split()), len(out.split()); lost = sorted(names(rest) - names(out))
    why = None
    if not out.strip() or abs(wo - wd) > 0.15 * max(wd, 1): why = f"length {wd}->{wo}"
    elif HAN.search(out): why = "Han"
    elif len(lost) > 2: why = f"names lost {lost[:6]}"
    out = out.replace("—", ",")
    return ((head + "\n\n" if head else "") + out.strip() + "\n") if not why else text, {"words": [wd, wo], "applied": not why, "rejected": why}
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("chapter"); ap.add_argument("--bible"); ap.add_argument("--out")
    a = ap.parse_args(); t = open(a.chapter, encoding="utf-8").read()
    b = open(a.bible, encoding="utf-8").read() if a.bible and os.path.exists(a.bible) else ""
    new, info = polish(t, b); open(a.out or a.chapter, "w", encoding="utf-8").write(new)
    print(json.dumps(dict(chapter=a.chapter, **info), ensure_ascii=False))
