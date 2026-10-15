#!/usr/bin/env python3
"""canon.py (REWRITTEN 2026-10-15, minimal)
  canon.py context <book_dir> [--n 5]        print planning context: current_state + last N chapter summaries + locked facts
  canon.py update  <book_dir> <chapter.md>   MiMo: append summary to story/chapter_summaries.md, rewrite story/current_state.md,
                                             write proposed new locked facts to locked_facts.proposed.yaml (never auto-locks)."""
import sys, os, re, json, argparse, yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mimo, bookfiles as bf
def rd(p): return open(p, encoding="utf-8").read() if os.path.exists(p) else ""
def context(book, n=5):
    s = os.path.join(book, "story"); summ = rd(os.path.join(s, "chapter_summaries.md"))
    blocks = re.split(r"\n(?=## )", summ); facts = bf.load_facts(book)
    return ("# Trạng thái hiện tại\n" + rd(os.path.join(s, "current_state.md")) + "\n\n# Tóm tắt các chương gần nhất\n" + "\n".join(blocks[-n:])
            + "\n\n# Sự thật đã khóa\n" + "\n".join(f"- [{f['id']}] {f['fact']}" for f in facts))
def update(book, chap):
    s = os.path.join(book, "story"); os.makedirs(s, exist_ok=True); text = rd(chap); n = bf.chapter_no(chap, text)
    r = mimo.chat_json("Đọc chương truyện và trạng thái cũ. Trả về JSON {\"summary\":\"tóm tắt 5-8 câu\",\"current_state\":\"markdown trạng thái mới "
        "(vị trí, thời gian, thương tích, vật phẩm, quan hệ, phục bút mở)\",\"new_facts\":[{\"id\":\"kebab-id\",\"entity\":\"...\",\"fact\":\"sự thật "
        "không đổi được (chết, mất tay, cảnh giới...)\"}]}\n\nTRẠNG THÁI CŨ:\n" + rd(os.path.join(s, "current_state.md"))[:8000] + "\n\nCHƯƠNG:\n" + text)
    with open(os.path.join(s, "chapter_summaries.md"), "a", encoding="utf-8") as f: f.write(f"\n## Chương {n}\n{r.get('summary','').strip()}\n")
    if r.get("current_state"): open(os.path.join(s, "current_state.md"), "w", encoding="utf-8").write(r["current_state"].strip() + "\n")
    nf = r.get("new_facts") or []
    if nf:
        p = os.path.join(book, "locked_facts.proposed.yaml"); d = (yaml.safe_load(rd(p)) if os.path.exists(p) else None) or {"proposed": []}
        for f in nf: f["since_chapter"] = n; d["proposed"].append(f)
        yaml.safe_dump(d, open(p, "w", encoding="utf-8"), allow_unicode=True, sort_keys=False)
    return {"chapter": n, "summary_chars": len(r.get("summary", "")), "proposed_facts": len(nf)}
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["context", "update"]); ap.add_argument("book"); ap.add_argument("chapter", nargs="?")
    ap.add_argument("--n", type=int, default=5); a = ap.parse_args()
    print(context(a.book, a.n) if a.cmd == "context" else json.dumps(update(a.book, a.chapter), ensure_ascii=False))
