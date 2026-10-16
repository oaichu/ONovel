"""Shared MiMo (api.b.ai, OpenAI-compatible) helper. Key from LOCKCHECK_API_KEY / BAI_API_KEY / INKOS_LLM_API_KEY. Never prints the key."""
import os, json, re, urllib.request
MODEL = os.environ.get("MIMO_MODEL", "mimo-v2.6-flash")
BASE = os.environ.get("LOCKCHECK_BASE_URL", "https://api.b.ai/v1").rstrip("/")
def key():
    k = os.environ.get("LOCKCHECK_API_KEY") or os.environ.get("BAI_API_KEY") or os.environ.get("INKOS_LLM_API_KEY")
    if not k: raise RuntimeError("no MiMo API key in env (BAI_API_KEY)")
    return k
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
def chat(prompt, system=None, temperature=0.3, max_tokens=16000, timeout=None, thinking=False, retries=1):
    mock = os.environ.get("ONOVEL_MOCK_LLM")  # tests/CI only: "1" canned JSON, "error" simulated API failure
    if mock == "error": raise TimeoutError("mock MiMo timeout")
    if mock: return json.dumps({"items": [], "summary": "Tóm tắt giả lập.", "current_state": "Trạng thái giả lập.", "characters": [{"name": "Lâm Phong", "realm": "Luyện Khí"}]}, ensure_ascii=False)
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    body = {"model": MODEL, "messages": msgs, "temperature": temperature, "max_tokens": max_tokens}
    if not thinking: body["thinking"] = {"type": "disabled"}
    for k in range(retries + 1):
        try: out = _stream(body); break
        except Exception as e:
            if k == retries: raise
            import sys; print(f"mimo retry after {type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
    return re.sub(r"^```\w*\n|\n```\s*$", "", out.strip())
def chat_json(prompt, **kw):
    t = chat(prompt + "\n\nChỉ trả về JSON hợp lệ, không giải thích.", temperature=0.1, **kw)
    m = re.search(r"[\[{].*[\]}]", t, re.S)
    return json.loads(m.group(0) if m else t)
