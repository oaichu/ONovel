#!/usr/bin/env python3
"""glm.py  (plan/draft LLM: OpenRouter FREE models only, chain GLM_FREE_MODELS; never paid. GLM_PROVIDER=bigmodel = explicit opt-in only)
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
FREE = os.environ.get("GLM_FREE_MODELS", "nvidia/nemotron-3-ultra-550b-a55b:free,google/gemma-4-31b-it:free,openrouter/free").split(",")
PAID = body["model"]
CHAIN = [PAID] if BIG else [m for m in FREE if m]  # NO paid models: only OpenRouter :free (bigmodel only if explicitly GLM_PROVIDER=bigmodel)
BLOCKED = "/CODE/inkos/runs/llm-blocked.txt"
def blocked(why):
    open(BLOCKED, "a").write(f"[{time.strftime('%F %T')}] LLM BLOCKED: {why}\n")
    print("glm blocked: " + why, file=sys.stderr); sys.exit(4)
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
        with urllib.request.urlopen(req, timeout=a.timeout) as r: j = json.load(r)
        if "choices" not in j: raise RuntimeError("no choices: " + json.dumps(j.get("error", j), ensure_ascii=False)[:250])
        c = j["choices"][0]; txt = re.sub(r"(?s)<think>.*?</think>", "", c["message"].get("content") or "").strip()
        if txt:
            open(a.out, "w", encoding="utf-8").write(txt + "\n")
            u = j.get("usage", {})
            print(f"glm ok model={model} try={i} {time.time()-t0:.0f}s in={u.get('prompt_tokens')} out={u.get('completion_tokens')} finish={c.get('finish_reason')}", file=sys.stderr)
            sys.exit(0)
        err = f"empty content finish={c.get('finish_reason')}"
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "replace")[:300]; err = f"HTTP {e.code} {msg}"
        if e.code == 429 and "per-day" in msg: daily.add(model)
        if e.code in (400, 401, 403) and "1305" not in msg and "1302" not in msg and e.code != 408: print("glm fatal: " + err, file=sys.stderr); sys.exit(2)
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
