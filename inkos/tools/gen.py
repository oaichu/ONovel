#!/usr/bin/env python3
"""gen.py <prompt-file> <out> [--task ...]   primary generator for plan / scene draft / expand.
NOVEL_LLM=mimo (default): MiMo V2.6 Flash (tools/mimo.py, api.b.ai, model id mimo-v2.6-flash; streaming with 20s/90s/cap timeouts).
On MiMo failure (content_filter, timeout, empty/too-short output) -> fallback tools/glm.py (OpenRouter FREE only, never paid).
Exit codes follow glm.py (0 ok, 4 all free models blocked)."""
import os, sys, time, subprocess, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument("prompt"); ap.add_argument("out")
ap.add_argument("--task", default="Thực hiện đúng phần NHIỆM VỤ ở cuối tài liệu. Chỉ trả về kết quả.")
a, rest = ap.parse_known_args()
def fallback(why):
    print(f"gen: MiMo -> fallback OpenRouter FREE (glm.py): {why}", file=sys.stderr, flush=True)
    os.execv(sys.executable, [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "glm.py"), a.prompt, a.out, "--task", a.task] + rest)
if os.environ.get("NOVEL_LLM", "mimo") == "mimo" and not os.environ.get("ONOVEL_MOCK_LLM"):
    os.environ.setdefault("MIMO_CONNECT_TIMEOUT", "60")
    import mimo
    os.environ.setdefault("MIMO_CALL_CAP", os.environ.get("GEN_MIMO_CAP", "600"))
    mimo.T_CAP = int(os.environ["MIMO_CALL_CAP"])
    p = open(a.prompt, encoding="utf-8", errors="ignore").read() + "\n\n" + a.task
    t0 = time.time(); print(f"gen: {mimo.MODEL} ({len(p)} chars prompt)", file=sys.stderr, flush=True)
    try:
        out = mimo.chat(p, temperature=float(os.environ.get("GEN_TEMPERATURE", 0.8)), max_tokens=int(os.environ.get("GEN_MAX_TOKENS", 24000)), retries=1)
    except Exception as e: fallback(f"{type(e).__name__}: {str(e)[:150]}")
    if len(out.split()) < int(os.environ.get("GEN_MIN_WORDS", 80)): fallback(f"output too short ({len(out.split())} words)")
    tmp = a.out + ".tmp"; open(tmp, "w", encoding="utf-8").write(out.strip() + "\n"); os.replace(tmp, a.out)
    print(f"gen: {mimo.MODEL} ok {len(out.split())} words in {time.time()-t0:.0f}s", file=sys.stderr, flush=True); sys.exit(0)
fallback("NOVEL_LLM != mimo")
