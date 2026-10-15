#!/usr/bin/env python3
"""lockcheck.py check <book_dir> <chapter.md> [--no-llm] -> JSON {chapter, active_facts, violations[], llm_error}
REWRITTEN 2026-10-15 (minimal). Reads <book>/locked_facts.yaml: facts[{id, entity, fact, since_chapter, forbid[regex], allow_if[]}],
changes[{fact_id, from_chapter, ...}] (a change retires a fact from that chapter on). Regex pass, then MiMo judges every active fact.
Violation fields: fact_id, source (regex|llm), reason, quote. Exit 0 clean, 1 violations, 2 error.
  lockcheck.py add <book_dir> <id> <entity> <fact> [--since N]   append a fact."""
import sys, os, re, json, argparse, yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mimo, bookfiles as bf
def active(book, n):
    p = os.path.join(book, "locked_facts.yaml"); d = yaml.safe_load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    d = d or {}; retired = {c.get("fact_id") for c in (d.get("changes") or []) if int(c.get("from_chapter", 10**9)) <= n}
    return [f for f in (d.get("facts") or []) if int(f.get("since_chapter", 0)) <= n and f.get("id") not in retired]
def check(book, chap, use_llm=True):
    text = open(chap, encoding="utf-8").read(); n = bf.chapter_no(chap, text); facts = active(book, n); viol = []; err = None
    for f in facts:
        ai = f.get("allow_if") or []; ai = [ai] if isinstance(ai, str) else ai
        if any(a and a in text for a in ai): continue
        for rx in f.get("forbid") or []:
            for m in re.finditer(rx, text):
                s = max(0, m.start() - 80); viol.append(dict(fact_id=f["id"], source="regex", reason=f"khớp mẫu cấm {rx}", quote=text[s:m.end() + 80]))
    if use_llm and facts:
        fl = "\n".join(f"- [{f['id']}] ({f.get('entity','')}) {f['fact']}" + (f" | NGOẠI LỆ HỢP LỆ: {f['allow_if']}" if isinstance(f.get('allow_if'), str) and len(f.get('allow_if')) > 20 else "") for f in facts)
        try:
            r = mimo.chat_json("Kiểm tra chương truyện có MÂU THUẪN với các sự thật đã khóa dưới đây không. Chỉ báo mâu thuẫn rõ ràng, "
                "có trích dẫn nguyên văn. Hồi ức/ảo ảnh có khung rõ thì không tính; tôn trọng NGOẠI LỆ HỢP LỆ. Không liệt kê mục không mâu thuẫn. Trả về JSON "
                '{"violations":[{"fact_id":"...","reason":"...","quote":"..."}]}\n\nSỰ THẬT KHÓA:\n' + fl + "\n\nCHƯƠNG:\n" + text)
            NOISE = re.compile(r"không mâu thuẫn|khớp với|không vi phạm|hợp lệ|không có mâu thuẫn", re.I)
            for v in (r.get("violations", []) if isinstance(r, dict) else r):
                if isinstance(v, dict) and not NOISE.search(str(v.get("reason", ""))): v["source"] = "llm"; viol.append(v)
        except Exception as e: err = f"{type(e).__name__}: {e}"[:300]
    return {"chapter": chap, "active_facts": [f["id"] for f in facts], "violations": viol, "llm_error": err}
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["check", "add"]); ap.add_argument("book"); ap.add_argument("rest", nargs="*")
    ap.add_argument("--no-llm", action="store_true"); ap.add_argument("--since", type=int, default=1); a = ap.parse_args()
    if a.cmd == "add":
        p = os.path.join(a.book, "locked_facts.yaml"); d = (yaml.safe_load(open(p)) if os.path.exists(p) else None) or {"language": "vi", "facts": [], "changes": []}
        fid, ent, fact = a.rest[:3]; d["facts"].append(dict(id=fid, entity=ent, fact=fact, since_chapter=a.since, forbid=[], allow_if=[]))
        yaml.safe_dump(d, open(p, "w", encoding="utf-8"), allow_unicode=True, sort_keys=False); print("added", fid); sys.exit(0)
    try: r = check(a.book, a.rest[0], not a.no_llm)
    except Exception as e: print(json.dumps({"chapter": a.rest[0], "error": str(e)}, ensure_ascii=False)); sys.exit(2)
    print(json.dumps(r, ensure_ascii=False, indent=2)); sys.exit(1 if r["violations"] else 0)
