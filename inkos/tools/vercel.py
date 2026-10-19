"""Vercel AI Gateway helper (OpenAI-compatible, https://ai-gateway.vercel.sh/v1). Key from env AI_GATEWAY_API_KEY; never printed.
Fallback provider after MiMo, before OpenRouter FREE. NEVER causes a charge:
 - default chain = models priced 0 on the gateway only (VERCEL_MODELS); priced models only with explicit VERCEL_ALLOW_CREDIT=1.
 - credit balance (GET /v1/credits, cached VERCEL_CREDIT_TTL=300s) must be >= VERCEL_MIN_BALANCE ($0.25) and readable, else skip.
 - any 402 / insufficient credit / billing / quota error, or a reported cost > 0 on a free model -> flag runs/vercel-down (1h, like gemini-down).
 - never touches billing settings (no top-up)."""
import os, json, re, time, socket, urllib.request, urllib.error, sys
BASE = os.environ.get("VERCEL_BASE_URL", "https://ai-gateway.vercel.sh/v1").rstrip("/")
FREE_DEFAULT = "stealth/cat-jam,reflection/beam-free,nvidia/nemotron-3.5-lightning-free"
MODELS = [m.strip() for m in os.environ.get("VERCEL_MODELS", FREE_DEFAULT).split(",") if m.strip()]
PAID_MODELS = [m.strip() for m in os.environ.get("VERCEL_PAID_MODELS", "deepseek/deepseek-v4-flash").split(",") if m.strip()]
ALLOW_CREDIT = os.environ.get("VERCEL_ALLOW_CREDIT") == "1"  # opt-in: spend gateway credit on priced models (still balance-guarded)
MIN_BAL = float(os.environ.get("VERCEL_MIN_BALANCE", 0.25))
RUNS = os.environ.get("ONOVEL_RUNS", "/CODE/inkos/runs")
FLAG = os.environ.get("VERCEL_DOWN_FLAG", os.path.join(RUNS, "vercel-down")); FLAG_TTL = int(os.environ.get("VERCEL_DOWN_TTL", 3600))
CACHE = os.path.expanduser("~/.cache/inkos"); CRED = os.path.join(CACHE, "vercel-credits.json"); MODF = os.path.join(CACHE, "vercel-models.json")
CRED_TTL = int(os.environ.get("VERCEL_CREDIT_TTL", 300)); MOD_TTL = 6 * 3600
T_CONN = int(os.environ.get("VERCEL_CONNECT_TIMEOUT", 60)); T_IDLE = int(os.environ.get("VERCEL_IDLE_TIMEOUT", 90)); T_CAP = int(os.environ.get("VERCEL_CALL_CAP", 600))
BILLING = re.compile(r"insufficient|credit|billing|payment|top.?up|quota|purchase|balance|spend", re.I)
MODEL = MODELS[0] if MODELS else ""
def log(m): print("vercel: " + m, file=sys.stderr, flush=True)
def key(): return os.environ.get("AI_GATEWAY_API_KEY") or ""
def _get(path, timeout=20):
    req = urllib.request.Request(BASE + path, headers={"Authorization": "Bearer " + key()})
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.load(r)
def _save(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True); t = p + f".{os.getpid()}.tmp"; json.dump(obj, open(t, "w")); os.replace(t, p)
def flag(why):
    try:
        os.makedirs(os.path.dirname(FLAG), exist_ok=True); t = FLAG + f".{os.getpid()}"
        open(t, "w").write(f"[{time.strftime('%F %T')}] {why[:300]}\n"); os.replace(t, FLAG)
    except Exception: pass
    log(f"DOWN flag {FLAG} set for {FLAG_TTL//60}min: {why[:200]}")
def flagged():
    try: return time.time() - os.path.getmtime(FLAG) < FLAG_TTL
    except OSError: return False
def balance(fresh=False):
    """Remaining gateway credit in USD (cached CRED_TTL s), or None if it cannot be confirmed."""
    if not fresh:
        try:
            if time.time() - os.path.getmtime(CRED) < CRED_TTL: return float(json.load(open(CRED))["balance"])
        except Exception: pass
    try:
        d = _get("/credits"); b = float(d["balance"]); _save(CRED, {"balance": b, "total_used": d.get("total_used"), "t": time.time()}); return b
    except urllib.error.HTTPError as e:
        if e.code in (402, 403): flag(f"credits endpoint HTTP {e.code}")
        log(f"credits check failed HTTP {e.code}"); return None
    except Exception as e: log(f"credits check failed {type(e).__name__}"); return None
def prices():
    """{model_id: (input, output)} from /v1/models, cached 6h."""
    try:
        if time.time() - os.path.getmtime(MODF) < MOD_TTL: return {k: tuple(v) for k, v in json.load(open(MODF)).items()}
    except Exception: pass
    try:
        d = _get("/models", timeout=30)["data"]; out = {}
        for m in d:
            p = m.get("pricing") or {}
            try: out[m["id"]] = (float(p.get("input", "nan")), float(p.get("output", "nan")))
            except Exception: out[m["id"]] = (float("nan"), float("nan"))
        _save(MODF, out); return out
    except Exception as e: log(f"model list failed {type(e).__name__}"); return {}
def is_free(m, pr):
    p = pr.get(m); return bool(p) and p[0] == 0 and p[1] == 0
def chain():
    """Models allowed right now ([] = skip gateway). Free (price 0) models always first; priced only if ALLOW_CREDIT."""
    if not key(): log("no AI_GATEWAY_API_KEY in env -> skip"); return []
    if flagged(): log(f"skipped (down flag {FLAG})"); return []
    b = balance()
    if b is None: log("credit balance unconfirmed -> skip"); return []
    if b < MIN_BAL: flag(f"balance ${b:.2f} < margin ${MIN_BAL:.2f}"); return []
    pr = prices()
    if not pr: return []
    c = [m for m in MODELS if is_free(m, pr)]
    if ALLOW_CREDIT: c += [m for m in PAID_MODELS if m in pr and m not in c]
    return c
def available(): return bool(chain())
def _stream(body):
    """SSE: T_CONN connect/headers, T_IDLE without new tokens, T_CAP hard cap. Returns (text, usage, model)."""
    b = dict(body, stream=True, stream_options={"include_usage": True})
    req = urllib.request.Request(BASE + "/chat/completions", json.dumps(b).encode(),
                                 {"Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    t0 = last = time.time(); r = urllib.request.urlopen(req, timeout=T_CONN); parts = []; usage = {}; model = ""
    try: r.fp.raw._sock.settimeout(5)
    except Exception: pass
    try:
        while True:
            now = time.time()
            if now - t0 > T_CAP: raise TimeoutError(f"vercel hard cap {T_CAP}s")
            if now - last > T_IDLE: raise TimeoutError(f"vercel idle {now-last:.0f}s")
            try: line = r.readline()
            except (socket.timeout, TimeoutError): continue
            if not line: break
            line = line.strip()
            if not line.startswith(b"data:"): continue
            d = line[5:].strip()
            if d == b"[DONE]": break
            try: e = json.loads(d)
            except Exception: continue
            if "error" in e: raise RuntimeError("vercel error: " + json.dumps(e["error"], ensure_ascii=False)[:250])
            model = e.get("model") or model; usage = e.get("usage") or usage
            for c in e.get("choices", []):
                dl = c.get("delta") or {}
                if dl.get("content") or dl.get("reasoning") or dl.get("reasoning_content"): last = time.time()
                if dl.get("content"): parts.append(dl["content"])
                if c.get("finish_reason") == "content_filter": raise RuntimeError("vercel content_filter")
    finally: r.close()
    return "".join(parts), usage, model
def chat(prompt, system=None, temperature=0.8, max_tokens=16000, min_words=0):
    """Try the allowed gateway models in order; raise RuntimeError if none produced text."""
    c = chain()
    if not c: raise RuntimeError("vercel gateway unavailable (guard)")
    pr = prices(); msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    err = None
    for m in c:
        free = is_free(m, pr)
        if not free:  # re-check balance right before spending credit
            b = balance(fresh=True)
            if b is None or b < MIN_BAL: flag(f"balance {b} < margin before priced call"); break
        body = {"model": m, "messages": msgs, "temperature": temperature, "max_tokens": max(max_tokens, int(os.environ.get("VERCEL_MIN_MAX_TOKENS", 2048))) if free else max_tokens}  # free models reason first; tiny budgets yield empty content
        if "nemotron" in m: body["reasoning"] = {"enabled": False}
        t0 = time.time()
        try:
            out, u, rm = _stream(body)
            cost = float(u.get("cost") or 0)
            log(f"{m} (resp {rm}) {time.time()-t0:.0f}s in={u.get('prompt_tokens')} out={u.get('completion_tokens')} cost=${cost:.6f}")
            if free and cost > 0: flag(f"free model {m} reported cost ${cost}")  # keep this output, but stop using the gateway
            out = re.sub(r"(?s)<think>.*?</think>", "", out).strip()
            if len(out.split()) >= max(1, min_words): return re.sub(r"^```\w*\n|\n```\s*$", "", out)
            err = f"{m}: output too short ({len(out.split())} words)"
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:300]; err = f"{m}: HTTP {e.code} {msg[:160]}"
            if e.code == 402 or (e.code in (400, 429) and BILLING.search(msg) and "rate" not in msg.lower()): flag(err); break
            if e.code == 401: flag(err); break
        except Exception as e:
            err = f"{m}: {type(e).__name__}: {str(e)[:160]}"
            if BILLING.search(str(e)) and "402" in str(e): flag(err); break
        log("try failed " + err)
    raise RuntimeError("vercel: all models failed: " + str(err))
if __name__ == "__main__":  # python3 vercel.py [--status] | [prompt]
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        b = balance(fresh=True); print(json.dumps({"key": bool(key()), "flagged": flagged(), "balance": b, "min": MIN_BAL, "chain": chain()})); sys.exit(0)
    print(chat(" ".join(sys.argv[1:]) or "Chào", max_tokens=int(os.environ.get("VERCEL_TEST_TOKENS", 60))))
