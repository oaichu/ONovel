import os
from onovel import context, expand, state
from conftest import chapter_text
def test_outline_window_and_budget(book):
    open(os.path.join(book, "chapters", "0012_c.md"), "w").write(chapter_text(12, 400))
    ctx = context.build(book, 13, budget=6000)
    assert "xuống núi, gặp Huyết Ma" in ctx and "tương lai" not in ctx and "# ĐOẠN CUỐI CHƯƠNG TRƯỚC" in ctx
    assert context.tok(ctx) < 6000 * 1.3
def test_cut_paragraph_boundary():
    t = "\n\n".join(f"đoạn {i} " + "chữ " * 50 for i in range(20)); c = context.cut(t, 100)
    assert c.rstrip().endswith("chữ") and context.tok(c) <= 100 and c.count("đoạn") >= 1
    tail = context.cut(t, 100, tail=True); assert "đoạn 19" in tail and "đoạn 0 " not in tail
def test_expand_accepts_longer(tmp_path):
    d = str(tmp_path); open(os.path.join(d, "draft.md"), "w").write(chapter_text(1, 500)); open(os.path.join(d, "plan.md"), "w").write("Cảnh 1. Cảnh 2.")
    def llm(p, out): open(out, "w").write(chapter_text(1, 2600)); return 0
    assert expand.expand(d, 2400, 3000, llm=llm, log=lambda s: None) >= 2400
def test_expand_rejects_degenerate(tmp_path):
    d = str(tmp_path); open(os.path.join(d, "draft.md"), "w").write(chapter_text(1, 500))
    def llm(p, out): open(out, "w").write("# Chương 1: X\n\n" + ("Hắn đứng đó nhìn trời rất lâu. " * 3000)); return 0
    w = expand.expand(d, 2400, 3000, llm=llm, log=lambda s: None); assert w < 1000
def test_draftcheck(tmp_path):
    import subprocess, sys
    T = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "draftcheck.py")
    p = tmp_path / "d.md"; p.write_text(chapter_text(1, 9000)); assert subprocess.run([sys.executable, T, str(p), "3000"]).returncode == 1
    p.write_text(chapter_text(1, 2500)); assert subprocess.run([sys.executable, T, str(p), "3000"]).returncode == 0
