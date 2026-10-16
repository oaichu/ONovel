import os, sys, pytest
HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HOME); sys.path.insert(0, os.path.join(HOME, "tools"))
os.environ.setdefault("ONOVEL_LESSONS", "/nonexistent-lessons")  # never write to the real library from tests
POOL = ("gió núi sương mù bậc đá kiếm khí đan lô linh thạch tàng kinh các sư huynh sư muội trưởng lão ngọn đèn mái ngói vách đá suối lạnh "
        "ánh trăng tiếng chuông bóng tối lá trúc mùi máu áo bào phù lục trận pháp cổ thụ bờ vực ngựa hoang quán trọ chén trà con đường "
        "thôn nhỏ dòng sông cánh cổng ngọn lửa lò rèn chiếc túi").split()
def chapter_text(n, words=3300, extra=""):
    import random
    rnd = random.Random(n * 7919 + words); body = []; total = 0; i = 0
    while total < words:
        s = " ".join(rnd.choice(POOL) for _ in range(rnd.randint(8, 16)))
        p = f'Lâm Phong {s} lần {i}. "Ta {rnd.choice(POOL)} {rnd.choice(POOL)} {i}," hắn nói.'; body.append(p); total += len(p.split()); i += 1
    return f"# Chương {n}: Thử nghiệm\n\n" + "\n\n".join(body) + extra + "\n"
@pytest.fixture
def book(tmp_path, monkeypatch):
    from onovel import cli
    monkeypatch.setenv("INKOS_PROJECT", str(tmp_path))
    cli.main(["new", "test-book", "--title", "Sách Thử", "--genre", "tien-hiep", "--project", str(tmp_path)])
    b = tmp_path / "books" / "test-book"
    (b / "story" / "outline" / "volume_map.md").write_text("# Volume map\n\nCh 1–10: Lâm Phong nhập môn Thanh Vân.\n\nCh 11–20: Lâm Phong xuống núi, gặp Huyết Ma.\n\nCh 50–60: Trận chiến cuối với Huyết Ma (tương lai).\n", encoding="utf-8")
    return str(b)
@pytest.fixture
def run_dir(tmp_path):
    def mk(n, text, name="run"):
        d = tmp_path / f"{name}-{n}"; d.mkdir(); (d / "chapter.md").write_text(text, encoding="utf-8"); return str(d)
    return mk
