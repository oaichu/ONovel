"""Shared MiMo (api.b.ai, OpenAI-compatible) helper + fallback chain for every caller.
Kill switch: flag file runs/mimo-off (MIMO_OFF_FLAG) -> MiMo is never called. On MiMo failure/off: Vercel AI Gateway (tools/vercel.py,
free/credit-guarded) -> OpenRouter FREE (tools/glm.py). fallback=False (gen.py has its own chain) or MIMO_FALLBACK=0 -> raise instead. Key from LOCKCHECK_API_KEY / BAI_API_KEY / INKOS_LLM_API_KEY. Never prints the key."""
import os, json, re, urllib.request
MODEL = os.environ.get("MIMO_MODEL", "mimo-v2.6-flash")
BASE = os.environ.get("LOCKCHECK_BASE_URL", "https://api.b.ai/v1").rstrip("/")
def key():
    k = os.environ.get("LOCKCHECK_API_KEY") or os.environ.get("BAI_API_KEY") or os.environ.get("INKOS_LLM_API_KEY")
    if not k: raise RuntimeError("no MiMo API key in env (BAI_API_KEY)")
    return k
OFF_FLAG = os.environ.get("MIMO_OFF_FLAG", "/CODE/inkos/runs/mimo-off")
def off(): return os.path.exists(OFF_FLAG)
T_CONN = int(os.environ.get("MIMO_CONNECT_TIMEOUT", 20)); T_IDLE = int(os.environ.get("MIMO_IDLE_TIMEOUT", 90)); T_CAP = int(os.environ.get("MIMO_CALL_CAP", 300))
def _stream(body):
    """SSE call: 20s connect/headers, 90s without new tokens, 5 min hard cap (survives dead sockets after box pause)."""
    import socket, time
    b = dict(body, stream=True)
    req = urllib.request.Request(BASE + "/chat/completions", json.dumps(b).encode(),
                                 {"Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    t0 = last = time.time(); r = urllib.request.urlopen(req, timeout=T_CONN); parts = []
    try: r.fp.raw._sock.settimeout(5)
    except Exception: pass
    try:
        while True:
            now = time.time()
            if now - t0 > T_CAP: raise TimeoutError(f"mimo hard cap {T_CAP}s")
            if now - last > T_IDLE: raise TimeoutError(f"mimo idle {now-last:.0f}s")
            try: line = r.readline()
            except (socket.timeout, TimeoutError): continue
            if not line: break
            line = line.strip()
            if not line.startswith(b"data:"): continue
            d = line[5:].strip()
            if d == b"[DONE]": break
            try: e = json.loads(d)
            except Exception: continue
            if "error" in e: raise RuntimeError("mimo error: " + str(e["error"])[:200])
            for c in e.get("choices", []):
                dl = c.get("delta") or {}
                if dl.get("content") or dl.get("reasoning_content"): last = time.time()
                if dl.get("content"): parts.append(dl["content"])
                if c.get("finish_reason") == "content_filter": raise RuntimeError("mimo content_filter")
    finally: r.close()
    return "".join(parts)
def fallback_chat(prompt, system=None, temperature=0.3, max_tokens=16000, why=""):
    """Non-MiMo chain: Vercel AI Gateway (free models / guarded credit) -> OpenRouter FREE via glm.py. Raises if all fail."""
    import sys, subprocess, tempfile
    print(f"mimo: {why or 'off'} -> fallback Vercel AI Gateway", file=sys.stderr, flush=True)
    try:
        import vercel; return vercel.chat(prompt, system=system, temperature=temperature, max_tokens=max_tokens)
    except Exception as e: print(f"mimo: vercel failed ({str(e)[:150]}) -> OpenRouter FREE (glm.py)", file=sys.stderr, flush=True)
    d = tempfile.mkdtemp(prefix="mimo-fb-"); fi, fo = os.path.join(d, "in.md"), os.path.join(d, "out.md")
    try:
        open(fi, "w", encoding="utf-8").write(((system + "\n\n") if system else "") + prompt)
        env = dict(os.environ); env.setdefault("GLM_MAX_TRIES", os.environ.get("MIMO_GLM_TRIES", "12"))
        rc = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "glm.py"), fi, fo, "--task", "",
                             "--max-tokens", str(max_tokens)], env=env, timeout=int(os.environ.get("MIMO_GLM_TIMEOUT", 3000))).returncode
        if rc != 0 or not os.path.exists(fo): raise RuntimeError(f"fallback chain failed (vercel + OpenRouter FREE rc={rc})")
        return open(fo, encoding="utf-8").read().strip()
    finally:
        import shutil; shutil.rmtree(d, ignore_errors=True)
def chat(prompt, system=None, temperature=0.3, max_tokens=16000, timeout=None, thinking=False, retries=1, fallback=None):
    mock = os.environ.get("ONOVEL_MOCK_LLM")  # tests/CI only: "1" canned JSON, "error" simulated API failure
    if mock == "error": raise TimeoutError("mock MiMo timeout")
    if mock: return json.dumps({"items": [], "summary": "Tóm tắt giả lập.", "current_state": "Trạng thái giả lập.", "characters": [{"name": "Lâm Phong", "realm": "Luyện Khí"}]}, ensure_ascii=False)
    if fallback is None: fallback = os.environ.get("MIMO_FALLBACK", "1") == "1"
    if off():
        if not fallback: raise RuntimeError(f"mimo off (flag {OFF_FLAG})")
        out = fallback_chat(prompt, system, temperature, max_tokens, why=f"MiMo off (flag {OFF_FLAG})")
        return re.sub(r"^```\w*\n|\n```\s*$", "", out.strip())
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    body = {"model": MODEL, "messages": msgs, "temperature": temperature, "max_tokens": max_tokens}
    if not thinking: body["thinking"] = {"type": "disabled"}
    for k in range(retries + 1):
        try: out = _stream(body); break
        except Exception as e:
            if k == retries:
                if not fallback: raise
                out = fallback_chat(prompt, system, temperature, max_tokens, why=f"MiMo failed {type(e).__name__}: {str(e)[:120]}"); break
            import sys; print(f"mimo retry after {type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
    return re.sub(r"^```\w*\n|\n```\s*$", "", out.strip())
def chat_json(prompt, **kw):
    t = chat(prompt + "\n\nChỉ trả về JSON hợp lệ, không giải thích.", temperature=0.1, **kw)
    m = re.search(r"[\[{].*[\]}]", t, re.S)
    return json.loads(m.group(0) if m else t)
