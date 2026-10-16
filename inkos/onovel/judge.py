"""Structured LLM judge (MiMo). The model must return items with
{rule_id, verdict: violation|ok, severity: high|medium|low, confidence: 0..1, evidence_span: verbatim quote, reason, word?, para?}.
Acceptance is structural, not keyword based: verdict == violation, confidence >= ONOVEL_JUDGE_MIN_CONF (0.6),
evidence_span found verbatim (whitespace/quote-normalised) in the chapter, word (if any) inside the span; duplicates merged.
Any API/JSON/schema error raises JudgeError -> the gate verdict becomes ERROR (never PASS)."""
import os, re, json, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
MIN_CONF = float(os.environ.get("ONOVEL_JUDGE_MIN_CONF", 0.6))
class JudgeError(Exception): pass
ITEM_SPEC = ('{"items":[{"rule_id":"<mã luật ngắn, kebab-case>","verdict":"violation|ok","severity":"high|medium|low",'
             '"confidence":<0..1>,"evidence_span":"<trích NGUYÊN VĂN từ chương, 10-200 ký tự>","reason":"...","word":"<từ lỗi nếu có>","para":<số đoạn từ 0>}]}')
def norm(s):
    s = re.sub(r"[“”„]", '"', str(s)); s = re.sub(r"[‘’]", "'", s)
    return re.sub(r"\s+", " ", s).strip().lower()
def accept(items, text):
    nt = norm(text); out = []; seen = set()
    for v in items:
        if not isinstance(v, dict) or v.get("verdict") != "violation": continue
        try: conf = float(v.get("confidence", 0))
        except (TypeError, ValueError): continue
        span = norm(v.get("evidence_span") or "")
        if conf < MIN_CONF or len(span) < 4 or span.strip('."… ') not in nt and span not in nt: continue
        w = norm(v.get("word") or "")
        if w and w not in span: continue
        k = (str(v.get("rule_id", "")).lower(), span[:80])
        if k in seen: continue
        seen.add(k)
        out.append(dict(rule_id=str(v.get("rule_id") or "llm"), source="llm", severity=v.get("severity") if v.get("severity") in ("high", "medium", "low") else "medium",
                        confidence=round(conf, 2), evidence_span=str(v.get("evidence_span"))[:300], reason=str(v.get("reason", ""))[:300],
                        word=str(v.get("word") or ""), para=v.get("para")))
    return out
def judge(task, text, max_tokens=6000, chat=None):
    if chat is None:
        import mimo; chat = mimo.chat
    prompt = (task + "\n\nTrả về JSON đúng dạng: " + ITEM_SPEC + "\nChỉ liệt kê mục verdict=violation thật sự; nếu không có lỗi trả {\"items\":[]}.")
    try: raw = chat(prompt + "\n\nChỉ trả về JSON hợp lệ, không giải thích.", temperature=0.1, max_tokens=max_tokens)
    except Exception as e: raise JudgeError(f"api: {type(e).__name__}: {e}"[:300])
    m = re.search(r"\{.*\}", raw or "", re.S)
    try: d = json.loads(m.group(0) if m else raw)
    except Exception: raise JudgeError("json: unparseable judge output")
    if not isinstance(d, dict) or not isinstance(d.get("items"), list): raise JudgeError("schema: missing items[]")
    return accept(d["items"], text)
