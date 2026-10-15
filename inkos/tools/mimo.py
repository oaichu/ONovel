"""Shared MiMo (api.b.ai, OpenAI-compatible) helper. Key from LOCKCHECK_API_KEY / BAI_API_KEY / INKOS_LLM_API_KEY. Never prints the key."""
import os, json, re, urllib.request
MODEL = os.environ.get("MIMO_MODEL", "mimo-v2.6-flash")
BASE = os.environ.get("LOCKCHECK_BASE_URL", "https://api.b.ai/v1").rstrip("/")
def key():
    k = os.environ.get("LOCKCHECK_API_KEY") or os.environ.get("BAI_API_KEY") or os.environ.get("INKOS_LLM_API_KEY")
    if not k: raise RuntimeError("no MiMo API key in env (BAI_API_KEY)")
    return k
def chat(prompt, system=None, temperature=0.3, max_tokens=16000, timeout=900, thinking=False):
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    body = {"model": MODEL, "messages": msgs, "temperature": temperature, "max_tokens": max_tokens}
    if not thinking: body["thinking"] = {"type": "disabled"}
    req = urllib.request.Request(BASE + "/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    out = json.load(urllib.request.urlopen(req, timeout=timeout))["choices"][0]["message"]["content"] or ""
    return re.sub(r"^```\w*\n|\n```\s*$", "", out.strip())
def chat_json(prompt, **kw):
    t = chat(prompt + "\n\nChỉ trả về JSON hợp lệ, không giải thích.", temperature=0.1, **kw)
    m = re.search(r"[\[{].*[\]}]", t, re.S)
    return json.loads(m.group(0) if m else t)
