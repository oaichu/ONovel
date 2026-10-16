"""Short-draft repair (ONovel audit step 4): instead of blind redrafts, an 'expand missing scenes' pass on the FREE model chain
(tools/glm.py: openrouter/free first, then :free list; never paid). The model gets the plan + current draft, must keep the
existing text and expand the thin/missing scenes. Result accepted only if longer and not degenerate (tools/draftcheck.py).
MiMo polish runs afterwards in novel.sh as usual."""
import os, subprocess, sys
from . import TOOLS
from .gates import count_words
def expand(run_dir, min_words=2400, target=3000, passes=2, llm=None, log=print):
    """Returns final word count, or -4 when the free models are blocked."""
    d = os.path.join(run_dir, "draft.md"); plan = open(os.path.join(run_dir, "plan.md"), encoding="utf-8").read() if os.path.exists(os.path.join(run_dir, "plan.md")) else ""
    ctx = open(os.path.join(run_dir, "context.md"), encoding="utf-8").read()[:30000] if os.path.exists(os.path.join(run_dir, "context.md")) else ""
    for k in range(1, passes + 1):
        cur = open(d, encoding="utf-8").read(); w = count_words(cur)
        if w >= min_words: return w
        p = os.path.join(run_dir, f"expand{k}.prompt")
        open(p, "w", encoding="utf-8").write(ctx + "\n\n# DÀN Ý\n" + plan + "\n\n# BẢN NHÁP HIỆN TẠI (" + str(w) + " chữ)\n" + cur +
            f"\n\n# NHIỆM VỤ\nBản nháp quá ngắn ({w} chữ, cần khoảng {target}, tối thiểu {min_words}). Đối chiếu dàn ý, tìm các cảnh bị thiếu hoặc "
            "chỉ được tóm tắt, rồi viết lại TOÀN VĂN chương: giữ nguyên các đoạn đã có (có thể nối thêm câu), triển khai đầy đủ cảnh thiếu bằng "
            "hành động, thoại, chi tiết cảm giác. Không lặp đoạn, không đổi tên riêng hay sự kiện. Dòng đầu là tiêu đề chương như bản nháp. "
            "Thoại trong ngoặc kép thẳng, không dấu gạch dài, không chữ Hán, tu sĩ không xưng 'tôi'. Chỉ trả về chương.")
        out = os.path.join(run_dir, f"draft.expand{k}.md")
        rc = (llm or _glm)(p, out)
        if rc == 4: return -4
        if rc != 0 or not os.path.exists(out): log(f"expand pass {k}: LLM failed rc={rc}"); continue
        nw = count_words(open(out, encoding="utf-8").read())
        dc = subprocess.run([sys.executable, os.path.join(TOOLS, "draftcheck.py"), out, str(target)], capture_output=True, text=True)
        if dc.returncode != 0: log(f"expand pass {k}: rejected ({dc.stdout.strip()})"); continue
        if nw <= w: log(f"expand pass {k}: not longer ({w}->{nw})"); continue
        os.replace(d, os.path.join(run_dir, f"draft.pre-expand{k}.md")); os.replace(out, d); log(f"expand pass {k}: {w} -> {nw} words")
    return count_words(open(d, encoding="utf-8").read())
def _glm(prompt, out):
    """glm.py stderr goes to the run's run.log so progress stays visible (and the supervisor sees a live log)."""
    rl = os.path.join(os.path.dirname(out), "run.log")
    with open(rl, "a", encoding="utf-8") as f:
        f.write(f"expand: calling free model chain for {os.path.basename(out)}\n"); f.flush()
        return subprocess.run(["timeout", "3600", sys.executable, os.path.join(TOOLS, "glm.py"), prompt, out], stderr=f).returncode
