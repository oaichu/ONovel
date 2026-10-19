"""Structured LLM judge (MiMo). The model must return items with
{rule_id, verdict: violation|ok, severity: high|medium|low, confidence: 0..1, evidence_span: verbatim quote, reason, word?, para?}.
Acceptance is structural, not keyword based: verdict == violation, confidence >= ONOVEL_JUDGE_MIN_CONF (0.6),
evidence_span found verbatim (whitespace/quote-normalised) in the chapter, word (if any) inside the span; duplicates merged.
Malformed items raise JudgeError; low-confidence / unverifiable items become REVIEW soft issues (audit A03, fail-closed).
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
def _issue(v, conf, review=None):
    sev = v.get("severity") if v.get("severity") in ("high", "medium", "low") else "medium"
    d = dict(rule_id=str(v.get("rule_id") or "llm"), source="llm", severity=sev, confidence=round(conf, 2), evidence_span=str(v.get("evidence_span"))[:300],
             reason=str(v.get("reason", ""))[:300], word=str(v.get("word") or ""), para=v.get("para"))
    if review: d.update(review=True, review_reason=review, severity="low")  # REVIEW: reported as a soft issue, never blocking, never dropped
    return d
def accept(items, text):
    """Fail-closed acceptance (audit A03). Returns the issue list; never silently drops a reported violation:
    - malformed item (not an object, verdict not violation|ok, confidence missing/non-numeric/outside 0..1, evidence_span missing/too short)
      -> JudgeError (gate ERROR);
    - confidence < MIN_CONF, evidence not found verbatim in the chapter, or `word` not inside the span -> REVIEW item (soft, review=True);
    - otherwise a normal issue (severity high is made blocking by gates.verdict)."""
    nt = norm(text); out = []; seen = set()
    for i, v in enumerate(items):
        if not isinstance(v, dict): raise JudgeError(f"schema: item {i} is not an object")
        vd = v.get("verdict")
        if vd == "ok": continue
        if vd != "violation": raise JudgeError(f"schema: item {i} verdict {str(vd)[:20]!r} not violation|ok")
        c = v.get("confidence")
        if isinstance(c, bool): raise JudgeError(f"schema: item {i} confidence not a number")
        try: conf = float(c)
        except (TypeError, ValueError): raise JudgeError(f"schema: item {i} confidence {str(c)[:20]!r} not a number")
        if not 0 <= conf <= 1: raise JudgeError(f"schema: item {i} confidence {conf} outside 0..1")
        ev = v.get("evidence_span")
        if not isinstance(ev, str) or len(norm(ev)) < 4: raise JudgeError(f"schema: item {i} evidence_span missing/too short")
        span = norm(ev); w = norm(v.get("word") or "")
        review = None
        if conf < MIN_CONF: review = f"low confidence {conf:.2f} < {MIN_CONF}"
        elif span.strip('."… ') not in nt and span not in nt: review = "evidence_span not found verbatim in chapter"
        elif w and w not in span: review = "word not inside evidence_span"
        k = (str(v.get("rule_id", "")).lower(), span[:80])
        if k in seen: continue
        seen.add(k); out.append(_issue(v, conf, review))
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
