#!/usr/bin/env python3
"""glm.py  (plan/draft LLM: OpenRouter FREE models only, chain = dynamic :free list from /api/v1/models (cache ~/.cache/inkos/free-models.json 6h) or GLM_FREE_MODELS; never paid. openrouter/free (auto router) is tried FIRST (user 2026-10-16), response model must end ':free'. GLM_PROVIDER=bigmodel = explicit opt-in only)
 <prompt-file> <out-file> [--task TEXT] [--max-tokens N] [--thinking]
GLM 4.7 Flash via open.bigmodel.cn (OpenAI-compatible). Key: $ZAI_API_KEY or ~/.config/inkos/zai_api_key.
Retries overload (1305/429/5xx/network/empty) with backoff 20s..300s up to GLM_MAX_TRIES (default 40)."""
import json, os, sys, time, urllib.request, urllib.error, argparse, random
PROV = os.environ.get("GLM_PROVIDER", "openrouter")  # openrouter (default) | bigmodel
BIG = PROV == "bigmodel"
URL = os.environ.get("GLM_URL", "https://open.bigmodel.cn/api/paas/v4/chat/completions" if BIG else "https://openrouter.ai/api/v1/chat/completions")
ap = argparse.ArgumentParser()
ap.add_argument("prompt"); ap.add_argument("out")
ap.add_argument("--task", default="Thực hiện đúng phần NHIỆM VỤ ở cuối tài liệu. Chỉ trả về kết quả.")
ap.add_argument("--max-tokens", type=int, default=int(os.environ.get("GLM_MAX_TOKENS", 32000)))
ap.add_argument("--thinking", action="store_true", default=os.environ.get("GLM_THINKING") == "1")
ap.add_argument("--timeout", type=int, default=int(os.environ.get("GLM_TIMEOUT", 900)))
a = ap.parse_args()
kv, kf = ("ZAI_API_KEY", "zai_api_key") if BIG else ("OPENROUTER_API_KEY", "openrouter_api_key")
key = os.environ.get(kv) or open(os.path.expanduser("~/.config/inkos/" + kf)).read().strip()
body = {"model": os.environ.get("GLM_MODEL", "glm-4.7-flash"),
        "messages": [{"role": "user", "content": open(a.prompt, encoding="utf-8", errors="ignore").read() + "\n\n" + a.task}],
        "max_tokens": a.max_tokens, "temperature": 0.8,
        }
if BIG: body["thinking"] = {"type": "enabled" if a.thinking else "disabled"}
else: body["reasoning"] = {"enabled": bool(a.thinking)}
FALLBACK_FREE = ["thinkingmachines/inkling:free", "thinkingmachines/inkling-small:free", "nvidia/nemotron-3.5-super-vl:free",
    "nvidia/nemotron-3.5-lightning:free", "nvidia/nemotron-3-ultra-550b-a55b:free", "dots-studio/dots-3-note-preview:free",
    "poolside/laguna-s-2.1:free", "poolside/laguna-xs-2.1:free", "google/gemma-4-31b-it:free", "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "cohere/north-mini-code:free",
    "liquid/lfm-2.5-2.6b:free"]
BAD = ("content-safety", "safety", "guard", "lyria")
CACHE = os.path.expanduser("~/.cache/inkos/free-models.json"); CACHE_TTL = 6 * 3600
def _ok_id(m): return m.endswith(":free") and not m.startswith("openrouter/") and not any(x in m for x in BAD)
def free_models():
    """Dynamic list of truly-free (:free, price 0) text-output models, context_length desc; cached ~6h; hardcoded fallback."""
    try:
        if time.time() - os.path.getmtime(CACHE) < CACHE_TTL:
            l = [m for m in json.load(open(CACHE)) if _ok_id(m)]
            if l: return l
    except Exception: pass
    try:
        with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as r: d = json.load(r)["data"]
        def z(v):
            try: return float(v) == 0
            except Exception: return False
        keep = [m for m in d if _ok_id(m.get("id", "")) and z(m.get("pricing", {}).get("prompt")) and z(m.get("pricing", {}).get("completion"))
                and "text" in ((m.get("architecture") or {}).get("output_modalities") or ["text"])
                and (m.get("architecture") or {}).get("modality", "->text").split("->")[-1].strip() in ("text", "")]
        keep.sort(key=lambda m: -(m.get("context_length") or 0))
        l = [m["id"] for m in keep]
        if l:
            os.makedirs(os.path.dirname(CACHE), exist_ok=True)
            tmp = CACHE + f".{os.getpid()}.tmp"; json.dump(l, open(tmp, "w"), indent=0); os.replace(tmp, CACHE)
            return l
    except Exception as e: print(f"glm: free-model list fetch failed ({type(e).__name__}), using fallback", file=sys.stderr)
    try:
        l = [m for m in json.load(open(CACHE)) if _ok_id(m)]  # stale cache beats hardcoded list
        if l: return l
    except Exception: pass
    return FALLBACK_FREE
_env = os.environ.get("GLM_FREE_MODELS")
FREE = [m.strip() for m in _env.split(",") if _ok_id(m.strip())] if _env else []
FREE = FREE or ([] if BIG else free_models())  # NEVER openrouter/free, NEVER non-:free
if not BIG:  # hard-disallow paid: price cap 0 + no paid provider fallback
    body["provider"] = {"max_price": {"prompt": 0, "completion": 0}, "allow_fallbacks": False}
PAID = body["model"]
CHAIN = [PAID] if BIG else [m for m in FREE if m]  # NO paid models: only OpenRouter :free (bigmodel only if explicitly GLM_PROVIDER=bigmodel)
BLOCKED = "/CODE/inkos/runs/llm-blocked.txt"
def blocked(why):
    open(BLOCKED, "a").write(f"[{time.strftime('%F %T')}] LLM BLOCKED: {why}\n")
    print("glm blocked: " + why, file=sys.stderr); sys.exit(4)
BADF = os.path.expanduser("~/.cache/inkos/bad-models.json")  # permanent 402/403/404 (e.g. Inkling "agentic harnesses only")
def bad_load():
    try: return set(json.load(open(BADF)))
    except Exception: return set()
def bad_add(m):
    b = bad_load(); b.add(m); os.makedirs(os.path.dirname(BADF), exist_ok=True)
    tmp = BADF + f".{os.getpid()}"; json.dump(sorted(b), open(tmp, "w")); os.replace(tmp, BADF)
_bad = bad_load(); CHAIN = [m for m in CHAIN if m not in _bad] or blocked("every free model is in " + BADF)
if not BIG and os.environ.get("GLM_AUTO_ROUTER", "1") == "1": CHAIN = ["openrouter/free"] + CHAIN  # 2026-10-16 user: auto router first; :free list is fallback. Response must report a :free model.
T_FIRST = int(os.environ.get("GLM_FIRST_TIMEOUT", 20)); T_IDLE = int(os.environ.get("GLM_IDLE_TIMEOUT", 60)); T_CAP = int(os.environ.get("GLM_CALL_CAP", 300))
def stream_call(req):
    """SSE streaming call. 20s to connect/headers, 60s without any new content token (keepalives don't count), 5min hard cap."""
    import socket
    b = json.loads(req.data); b["stream"] = True; req.data = json.dumps(b).encode()
    t0 = time.time(); r = urllib.request.urlopen(req, timeout=T_FIRST)
    try: r.fp.raw._sock.settimeout(5)
    except Exception: pass
    parts = []; model = ""; fin = None; usage = {}; last = time.time(); buf = b""
    while True:
        now = time.time()
        if now - t0 > T_CAP: raise TimeoutError(f"hard cap {T_CAP}s ({len(''.join(parts))} chars)")
        if now - last > (T_IDLE if parts else max(T_IDLE, T_FIRST)): raise TimeoutError(f"idle {now-last:.0f}s ({len(''.join(parts))} chars)")
        try: line = r.readline()
        except (socket.timeout, TimeoutError): continue
        if not line: break
        line = line.strip()
        if not line.startswith(b"data:"): continue
        d = line[5:].strip()
        if d == b"[DONE]": break
        try: e = json.loads(d)
        except Exception: continue
        if "error" in e: raise RuntimeError("no choices: " + json.dumps(e["error"], ensure_ascii=False)[:250])
        model = e.get("model") or model; usage = e.get("usage") or usage
        for c in e.get("choices", []):
            dl = c.get("delta") or {}
            if dl.get("content"): parts.append(dl["content"]); last = time.time()
            elif dl.get("reasoning"): last = time.time()  # thinking tokens count as progress
            fin = c.get("finish_reason") or fin
    r.close()
    return {"model": model, "usage": usage, "choices": [{"message": {"content": "".join(parts)}, "finish_reason": fin}]}
daily = set()
import re, fcntl
SLOTS = int(os.environ.get("GLM_SLOTS", 1 if BIG else 3))  # concurrent-request slots across all processes
def acquire():
    while True:
        for k in range(SLOTS):
            fh = open(f"/tmp/glm-slot-{k}.lock", "w")
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                gap = float(os.environ.get("GLM_MIN_GAP", 10 if BIG else 0))
                try: last = os.path.getmtime("/tmp/glm-last")
                except OSError: last = 0
                w = last + gap - time.time()
                if w > 0: time.sleep(w)
                return fh
            except OSError: fh.close()
        time.sleep(3)
tries = int(os.environ.get("GLM_MAX_TRIES", 40)); t0 = time.time()
for i in range(1, tries + 1):
    err = None
    rnd = (i - 1) // len(CHAIN)
    model = CHAIN[(i - 1) % len(CHAIN)]
    if model in daily:
        if len(daily) >= len(CHAIN): blocked("all free models hit daily quota (free-models-per-day): " + ",".join(CHAIN))
        continue
    b2 = dict(body, model=model)
    if model != PAID: b2.pop("reasoning", None)
    data = json.dumps(b2).encode()
    try:
        slot = acquire()
        req = urllib.request.Request(URL, data, {"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        j = stream_call(req)
        if "choices" not in j: raise RuntimeError("no choices: " + json.dumps(j.get("error", j), ensure_ascii=False)[:250])
        rm = j.get("model") or ""
        if not BIG and not rm.endswith(":free"):
            raise RuntimeError(f"response model {rm!r} is not the requested :free model -> discarded")
        c = j["choices"][0]; txt = re.sub(r"(?s)<think>.*?</think>", "", c["message"].get("content") or "").strip()
        if txt:
            open(a.out, "w", encoding="utf-8").write(txt + "\n")
            u = j.get("usage", {})
            print(f"glm ok model={model} resp_model={j.get('model')} try={i} {time.time()-t0:.0f}s in={u.get('prompt_tokens')} out={u.get('completion_tokens')} finish={c.get('finish_reason')}", file=sys.stderr)
            sys.exit(0)
        err = f"empty content finish={c.get('finish_reason')}"
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "replace")[:300]; err = f"HTTP {e.code} {msg}"
        if e.code == 429 and "per-day" in msg: daily.add(model)
        if not BIG:
            if e.code == 401: print("glm fatal: " + err, file=sys.stderr); sys.exit(2)
            if e.code in (402, 403, 404): daily.add(model); bad_add(model)  # permanent skip via cache  # paid-only/unavailable now -> never retry this model in this call
        elif e.code in (400, 401, 403) and "1305" not in msg and "1302" not in msg and e.code != 408: print("glm fatal: " + err, file=sys.stderr); sys.exit(2)
    except Exception as e: err = f"{type(e).__name__}: {e}"
    finally:
        try: open("/tmp/glm-last", "w").close()
        except Exception: pass
        try: slot.close()
        except Exception: pass
    slot = None
    if i % len(CHAIN) and model != PAID: s = 3
    else: s = min(300, 20 * 2 ** min(rnd, 4)) + random.randint(0, 10)
    print(f"glm try {i}/{tries} model={model} failed: {err} -> sleep {s}s", file=sys.stderr); time.sleep(s)
blocked(f"free models failed {tries} tries (rate-limited/unavailable): last error {err}")
