#!/usr/bin/env python3
"""lockcheck.py check <book_dir> <chapter.md> [--no-llm] -> gate verdict JSON, exit 0 PASS / 1 FAIL / 2 ERROR.
Locked facts come from the canonical story state (onovel/state.py; falls back to the locked_facts.yaml view).
Regex `forbid` matches are rule-based and BLOCK (negated statements like 'không thể ...' are skipped); the structured MiMo
judge reports contradictions as soft issues; judge errors are ERROR. Rewritten 2026-10-16 (ONovel audit).
  lockcheck.py add <book_dir> <id> <entity> <fact> [--since N]   add an author-locked fact (via the state engine)."""
import sys, os, re, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bookfiles as bf
from onovel import gates
NEG = re.compile(r"(?<![\wÀ-ỹ])(không|chẳng|chưa|không thể|đâu có|chả|cấm|không cho phép)(?![\wÀ-ỹ])", re.I)
def active(book, n):
    from onovel import state
    return state.active_facts(book, n)
def check(book, chap, use_llm=True, chat=None):
    text = open(chap, encoding="utf-8").read(); n = bf.chapter_no(chap, text); facts = active(book, n); blocking = []; soft = []; err = None
    for f in facts:
        ai = f.get("allow_if") or []; ai = [ai] if isinstance(ai, str) else ai
        if any(a and a in text for a in ai): continue
        for rx in f.get("forbid") or []:
            for m in re.finditer(rx, text):
                if NEG.search(text[max(m.start(), m.end() - 60):m.end()]): continue
                s = max(0, m.start() - 80)
                blocking.append(dict(rule_id=f"fact:{f['id']}", source="rule", severity="high", confidence=1.0,
                                     evidence_span=text[s:m.end() + 80], reason=f"khớp mẫu cấm {rx}", word=m.group(0), para=None))
    if use_llm and facts:
        from onovel import judge
        fl = "\n".join(f"- [{f['id']}] ({f.get('entity','')}) {f['fact']}" + (f" | NGOẠI LỆ HỢP LỆ: {f['allow_if']}" if isinstance(f.get('allow_if'), str) and len(f.get('allow_if')) > 20 else "") for f in facts)
        task = ("Kiểm tra chương truyện có MÂU THUẪN với các sự thật đã khóa dưới đây không. rule_id = id của sự thật bị vi phạm. "
                "Chỉ báo mâu thuẫn rõ ràng, evidence_span trích nguyên văn. Hồi ức/ảo ảnh có khung rõ thì không tính; tôn trọng NGOẠI LỆ HỢP LỆ."
                "\n\nSỰ THẬT KHÓA:\n" + fl + "\n\nCHƯƠNG:\n" + text)
        try:
            ids = {f["id"] for f in facts}
            # unknown rule ids are never dropped silently (audit A03): kept as REVIEW soft issues
            soft = [dict(v, rule_id="fact:" + v["rule_id"]) if v["rule_id"] in ids else
                    dict(v, rule_id="fact:unknown:" + v["rule_id"], severity="low", review=True, review_reason="rule_id is not an active locked fact")
                    for v in judge.judge(task, text, chat=chat)]
        except Exception as e: err = f"{type(e).__name__}: {e}"[:300]
    r = gates.verdict("lock", chap, text, blocking, soft, [], err, llm=use_llm and bool(facts))
    r["active_facts"] = [f["id"] for f in facts]; return r
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["check", "add"]); ap.add_argument("book"); ap.add_argument("rest", nargs="*")
    ap.add_argument("--no-llm", action="store_true"); ap.add_argument("--since", type=int, default=1); a = ap.parse_args()
    if a.cmd == "add":
        from onovel import state
        fid, ent, fact = a.rest[:3]; state.add_fact(a.book, fid, ent, fact, since=a.since, source="author"); print("added", fid); sys.exit(0)
    try: r = check(a.book, a.rest[0], not a.no_llm)
    except Exception as e: r = gates.error("lock", a.rest[0], f"{type(e).__name__}: {e}")
    print(json.dumps(r, ensure_ascii=False, indent=2)); sys.exit(gates.EXIT[r["verdict"]])
