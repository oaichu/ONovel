"""Scene-by-scene drafting (free models only, via tools/glm.py): free models write ~1,200-2,000 words per call, so a 3,000+
word chapter is drafted as 4-5 separate scene calls and joined. The plan must list scenes as '## Cảnh k: ...' (novel.sh asks
for that); otherwise the plan is split into up to 5 groups. Each scene is checked for degeneracy (tools/draftcheck.py) and
retried once. Result: <run>/draft.md (heading + scenes)."""
import os, re, subprocess, sys
from . import TOOLS
from .gates import count_words
def parse_scenes(plan, max_scenes=5):
    parts = re.split(r"\n(?=\s*(?:#{1,4}\s*|\*\*)?\s*Cảnh\s+\d+)", "\n" + plan)
    sc = [p.strip() for p in parts if re.match(r"\s*(?:#{1,4}\s*|\*\*)?\s*Cảnh\s+\d+", p.strip())]
    if len(sc) >= 3: return sc[:max_scenes] if len(sc) <= max_scenes else sc[:max_scenes - 1] + ["\n\n".join(sc[max_scenes - 1:])]
    paras = [p.strip() for p in re.split(r"\n\s*\n", plan) if p.strip()]
    k = min(max_scenes, max(1, len(paras))); size = -(-len(paras) // k)
    return ["\n\n".join(paras[i:i + size]) for i in range(0, len(paras), size)]
def _glm(prompt, out):
    rl = os.path.join(os.path.dirname(out), "run.log")
    with open(rl, "a", encoding="utf-8") as f:
        f.write(f"scene draft: free model chain for {os.path.basename(out)}\n"); f.flush()
        return subprocess.run(["timeout", "1800", sys.executable, os.path.join(TOOLS, "glm.py"), prompt, out], stderr=f).returncode
def strip_heading(t):
    lines = t.strip().splitlines()
    while lines and (lines[0].lstrip().startswith("#") or re.match(r"\s*\**\s*Cảnh\s+\d+", lines[0]) or not lines[0].strip()): lines.pop(0)
    return "\n".join(lines).strip()
def draft_scenes(run_dir, n, target=3200, llm=None, log=print, title_hint=""):
    ctx = open(os.path.join(run_dir, "context.md"), encoding="utf-8").read()
    plan = open(os.path.join(run_dir, "plan.md"), encoding="utf-8").read()
    scenes = parse_scenes(plan); per = max(700, -(-int(target * 1.08) // len(scenes)))
    log(f"scene drafting: {len(scenes)} scenes x ~{per} words")
    done = []; title = None
    for k, sc in enumerate(scenes, 1):
        prev = "\n\n".join(done)[-6000:]
        p = os.path.join(run_dir, f"scene{k}.prompt"); out = os.path.join(run_dir, f"scene{k}.md")
        open(p, "w", encoding="utf-8").write(ctx + "\n\n# DÀN Ý CHƯƠNG " + str(n) + "\n" + plan + "\n\n# PHẦN ĐÃ VIẾT CỦA CHƯƠNG (cuối)\n" + (prev or "(chưa có, đây là cảnh đầu)") +
            f"\n\n# NHIỆM VỤ\nChỉ viết CẢNH {k}/{len(scenes)} của Chương {n}, nối tiếp liền mạch phần đã viết:\n{sc}\n\n"
            f"Độ dài BẮT BUỘC khoảng {per} chữ (tối thiểu {int(per * 0.85)}): triển khai bằng hành động, thoại, chi tiết cảm giác, nội tâm, không tóm tắt, "
            "không viết sang cảnh sau, không lặp lại phần đã viết. "
            + ("Dòng đầu tiên là tiêu đề chương dạng '# Chương " + str(n) + ": <tên chương>'. " if k == 1 else "Không viết tiêu đề. ")
            + "Thoại trong ngoặc kép thẳng, không dấu gạch dài, không chữ Hán, không ghi chú; tu sĩ không xưng 'tôi'. Chỉ trả về văn bản cảnh.")
        ok = False
        for t in (1, 2):
            rc = (llm or _glm)(p, out)
            if rc == 4: return -4
            if rc != 0 or not os.path.exists(out): log(f"scene {k} try {t}: LLM failed rc={rc}"); continue
            dc = subprocess.run([sys.executable, os.path.join(TOOLS, "draftcheck.py"), out, str(per)], capture_output=True, text=True)
            if dc.returncode != 0: log(f"scene {k} try {t}: rejected ({dc.stdout.strip()})"); continue
            ok = True; break
        if not ok: return -3
        txt = open(out, encoding="utf-8").read().strip()
        if k == 1:
            m = re.match(r"\s*#+\s*(Chương\s+\d+.*)", txt.split("\n", 1)[0])
            title = m.group(1).strip() if m else f"Chương {n}: {title_hint or 'Không đề'}"
        body = strip_heading(txt); done.append(body); log(f"scene {k}: {count_words(body)} words")
    text = f"# {title}\n\n" + "\n\n".join(done) + "\n"
    open(os.path.join(run_dir, "draft.md"), "w", encoding="utf-8").write(text)
    return count_words(text)
