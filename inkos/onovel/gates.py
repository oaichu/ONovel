"""Gate verdicts. Every gate returns
  {gate, verdict: PASS|FAIL|ERROR, chapter, sha256, blocking[], soft[], warnings[], error, llm, ts}
issue = {rule_id, source: rule|llm, severity, confidence, evidence_span, reason, word, para}.
Exit codes everywhere: PASS 0, FAIL 1, ERROR 2.  Gate-level: ERROR if an LLM pass was requested and failed (or the gate
crashed); FAIL if any blocking issue (incl. LLM severity=high, see promote());
else PASS (soft issues are reported; REVIEW items count as soft). combine(): ERROR > FAIL > soft_max check > PASS."""
import os, re, json, hashlib, datetime
EXIT = {"PASS": 0, "FAIL": 1, "ERROR": 2}
def sha(text): return hashlib.sha256(text.encode("utf-8")).hexdigest()
def now(): return datetime.datetime.now().astimezone().isoformat(timespec="seconds")
def count_words(text):
    """Unified word counter: drop markdown heading lines and front matter, count tokens containing a letter or digit."""
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    body = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))
    return sum(1 for t in body.split() if re.search(r"\w", t))
def promote(blocking, soft):
    """Audit A04: an LLM finding with severity high (verified evidence, confidence >= judge.MIN_CONF, not a REVIEW item) is BLOCKING."""
    blocking = list(blocking); keep = []
    for v in soft:
        if v.get("severity") == "high" and not v.get("review"): blocking.append(dict(v, blocking_reason="llm-high-severity"))
        else: keep.append(v)
    return blocking, keep
def verdict(gate, chap, text, blocking, soft, warnings, err, llm=True):
    blocking, soft = promote(blocking, soft)
    v = "ERROR" if err else "FAIL" if blocking else "PASS"
    r = dict(gate=gate, verdict=v, chapter=chap, sha256=sha(text), blocking=blocking, soft=soft, warnings=warnings, error=err, llm=llm, ts=now())
    # legacy readers (old novel.sh / publish / review scripts): issues/violations/llm_error
    r["issues"] = blocking + soft + [dict(w, source="layout") for w in warnings]; r["violations"] = blocking + soft; r["llm_error"] = err
    return r
def error(gate, chap, msg):
    return dict(gate=gate, verdict="ERROR", chapter=chap, sha256=None, blocking=[], soft=[], warnings=[], error=str(msg)[:300], llm=None, ts=now())
def combine(results, soft_max):
    res = list(results)
    nsoft = sum(len(r.get("soft", [])) for r in res); nblk = sum(len(r.get("blocking", [])) for r in res)
    if any(r["verdict"] == "ERROR" for r in res): v = "ERROR"
    elif any(r["verdict"] == "FAIL" for r in res): v = "FAIL"
    elif nsoft > soft_max: v = "FAIL"
    else: v = "PASS"
    shas = {r.get("sha256") for r in res if r.get("sha256")}
    return dict(verdict=v, blocking=nblk, soft=nsoft, soft_max=soft_max, sha256=shas.pop() if len(shas) == 1 else None,
                errors=[f"{r['gate']}: {r['error']}" for r in res if r.get("error")], gates=res, ts=now())
def summary(c):
    return f"verdict={c['verdict']} blocking={c['blocking']} soft={c['soft']}/{c['soft_max']} errors={len(c['errors'])}"
def fix_list(c):
    """Fix instructions for MiMo fix.py: blocking first, then soft."""
    out = []
    for r in c["gates"]:
        for v in r.get("blocking", []) + r.get("soft", []):
            out.append(f"- [{v['rule_id']}] {v.get('word','')} {v.get('reason','')} | trích: {(v.get('evidence_span') or '')[:200]}")
    return "\n".join(out)
def run_all(book, chap, n=None, use_llm=True, soft_max=3, retries=1, style=None, lock=None, canon=None):
    """Run style, lock, canon gates; LLM gates are retried `retries` times on ERROR."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
    if style is None: import stylegate; style = stylegate.check
    if lock is None: import lockcheck; lock = lockcheck.check
    if canon is None: from . import state; canon = state.canon_gate
    out = []
    for name, fn in (("style", style), ("lock", lock)):
        for k in range(retries + 1):
            try: r = fn(book, chap, use_llm)
            except Exception as e: r = error(name, chap, f"{type(e).__name__}: {e}")
            if r["verdict"] != "ERROR": break
        out.append(r)
    try: out.append(canon(book, chap, n))
    except Exception as e: out.append(error("canon", chap, f"{type(e).__name__}: {e}"))
    return combine(out, soft_max)
