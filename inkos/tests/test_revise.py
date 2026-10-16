import os, json
from conftest import chapter_text
from onovel import state, txn, revise, gates, cli
def _commit(book, run_dir, n, text):
    d = run_dir(n, text, "c"); cli.main(["gate", book, os.path.join(d, "chapter.md"), "--n", str(n), "--no-llm", "--out", os.path.join(d, "gate.json")])
    open(os.path.join(d, "facts.json"), "w").write(json.dumps({"summary": "s", "facts": []}))
    return txn.commit(book, d, n, extracted={"summary": "s"})
def test_sync_files_adds_untracked(book, run_dir):
    cli.main(["migrate", book])
    open(os.path.join(book, "chapters", "0001_X.md"), "w").write(chapter_text(1))
    assert state.sync_files(book, published_upto=1)["synced"] == [1]
    assert state.chapter(book, 1)["status"] == "PUBLISHED" and state.sync_files(book)["synced"] == []
def test_revise_short_chapter(book, run_dir, monkeypatch, tmp_path):
    cli.main(["migrate", book]); short = chapter_text(1, words=1200)
    open(os.path.join(book, "chapters", "0001_X.md"), "w").write(short); state.sync_files(book, 1)
    def fake_expand(rd, mn, tg, passes=1, log=None):
        open(os.path.join(rd, "draft.md"), "w").write(chapter_text(1)); return gates.count_words(chapter_text(1))
    monkeypatch.setattr(revise.expand, "expand", fake_expand); monkeypatch.setenv("ONOVEL_MOCK_LLM", "1")
    monkeypatch.setattr(revise.gates, "run_all", lambda b, c, n, **k: dict(gates.combine([gates.verdict("all", c, open(c).read(), [], [], [], None, llm=False)], 3), sha256=gates.sha(open(c).read())))
    r = revise.revise_expand(book, 1, runs=str(tmp_path / "runs"))
    assert r["status"] == "REVISED", r
    live = open(os.path.join(book, "chapters", "0001_X.md")).read(); assert gates.count_words(live) >= 3000
    assert os.listdir(os.path.join(book, ".onovel", "revisions"))
    assert txn.check_publishable(book, 1, os.path.join(book, "chapters", "0001_X.md"))[0] == "publish"
