import os, json, pytest, sqlite3
from onovel import state, txn, gates
from conftest import chapter_text
EX = {"summary": "Lâm Phong nhập môn.", "current_state": "Lâm Phong ở Thanh Vân.", "characters": [{"name": "Lâm Phong", "realm": "Luyện Khí", "status": "sống"}],
      "treasures": [{"name": "Huyết Kiếm", "owner": "Lâm Phong"}], "secrets": [{"content": "Lâm Phong là con Huyết Ma", "knowers": ["Sư phụ"]}],
      "promises": [{"who": "Lâm Phong", "to_whom": "Sư muội", "content": "trở về trước mùa xuân", "due_chapter": 10}],
      "foreshadowing": {"planted": ["Vết sẹo trên tay Lâm Phong"], "paid_off": []}, "new_facts": [{"id": "lp-con-huyet-ma", "entity": "Lâm Phong", "fact": "là con Huyết Ma"}]}
def gated(book, d, n, use_llm=False):
    g = gates.run_all(book, os.path.join(d, "chapter.md"), n, use_llm=use_llm, soft_max=3, retries=0)
    open(os.path.join(d, "gate.json"), "w").write(json.dumps(g, ensure_ascii=False)); return g
def test_commit_and_state(book, run_dir):
    d = run_dir(1, chapter_text(1)); assert gated(book, d, 1)["verdict"] == "PASS"
    m = txn.commit(book, d, 1, extract=lambda b, t: EX); assert m["status"] == "COMMITTED"
    assert os.path.exists(os.path.join(book, "chapters", m["file"])) and state.next_chapter(book) == 2
    ch = state.entities(book, "character")[0]; assert ch["attrs"]["realm"] == "Luyện Khí" and ch["attrs"]["realm_history"] == [[1, "Luyện Khí"]]
    assert state.secrets(book)[0]["knowers"] == ["Sư phụ"] and state.open_promises(book)[0]["due_chapter"] == 10
    assert state.open_foreshadowing(book, 1) and "Lâm Phong ở Thanh Vân" in open(os.path.join(book, "story", "current_state.md")).read()
    assert state.active_facts(book, 1) == []  # new facts are only proposals, never auto-locked
    assert txn.check_publishable(book, 1, os.path.join(book, "chapters", m["file"]))[0] == "publish"
    txn.mark_published(book, 1); txn.mark_published(book, 1)
    assert txn.check_publishable(book, 1, os.path.join(book, "chapters", m["file"]))[0] == "published" and state.chapter(book, 1)["status"] == "PUBLISHED"
    with pytest.raises(txn.TxnError): txn.commit(book, d, 1, extract=lambda b, t: EX)  # duplicate
def test_rollback_when_state_update_fails(book, run_dir, monkeypatch):
    d = run_dir(1, chapter_text(1)); gated(book, d, 1)
    before = state.chapters(book)
    def bad(*a, **k): raise sqlite3.OperationalError("disk full")
    monkeypatch.setattr(state, "commit_chapter", bad)
    with pytest.raises(txn.TxnError): txn.commit(book, d, 1, extract=lambda b, t: EX)
    assert state.chapter_files(book) == [] and state.chapters(book) == before
    assert txn.load(book, 1)["status"] == "QUARANTINED" and any(h["status"] == "COMMIT_FAILED" for h in txn.load(book, 1)["history"])
def test_extraction_error_quarantines(book, run_dir):
    d = run_dir(1, chapter_text(1)); gated(book, d, 1)
    def boom(b, t): raise TimeoutError("mimo down")
    with pytest.raises(txn.TxnError): txn.commit(book, d, 1, extract=boom)
    assert state.chapter_files(book) == [] and txn.load(book, 1)["status"] == "QUARANTINED"
def test_error_verdict_never_commits(book, run_dir, monkeypatch):
    d = run_dir(1, chapter_text(1)); monkeypatch.setenv("ONOVEL_MOCK_LLM", "error")
    assert gated(book, d, 1, use_llm=True)["verdict"] == "ERROR"
    with pytest.raises(txn.TxnError): txn.commit(book, d, 1, extract=lambda b, t: EX)
    assert state.chapter_files(book) == [] and txn.check_publishable(book, 1, os.path.join(d, "chapter.md"))[0] == "block"
def test_sha_mismatch_rejected(book, run_dir):
    d = run_dir(1, chapter_text(1)); gated(book, d, 1)
    open(os.path.join(d, "chapter.md"), "a").write("\nthêm\n")
    with pytest.raises(txn.TxnError): txn.commit(book, d, 1, extract=lambda b, t: EX)
def test_publish_blocks_edited_chapter(book, run_dir):
    d = run_dir(1, chapter_text(1)); gated(book, d, 1); m = txn.commit(book, d, 1, extract=lambda b, t: EX)
    f = os.path.join(book, "chapters", m["file"]); open(f, "a").write("\nsửa tay\n")
    assert txn.check_publishable(book, 1, f)[0] == "block"
def test_migrate_legacy(tmp_path):
    from onovel import cli
    cli.main(["new", "legacy", "--title", "Cũ", "--project", str(tmp_path)]); b = str(tmp_path / "books" / "legacy")
    os.remove(state.path(b))
    open(os.path.join(b, "locked_facts.yaml"), "w").write("facts:\n- {id: a, entity: X, fact: X chết, since_chapter: 2, forbid: ['X sống']}\nchanges:\n- {fact_id: a, from_chapter: 5}\n")
    open(os.path.join(b, "story", "chapter_summaries.md"), "w").write("# S\n\n| Chapter | Title | Key Events |\n| --- | --- | --- |\n| 1 | C1 | X gặp Y |\n")
    open(os.path.join(b, "story", "pending_hooks.md"), "w").write("| hook_id | start_chapter | status | expected_payoff |\n| --- | --- | --- | --- |\n| H1 | 0 | open | bí mật thanh kiếm cổ |\n| H2 | 90 | open | trận chiến tương lai xa |\n")
    for n in (1, 2): open(os.path.join(b, "chapters", f"{n:04d}_c.md"), "w").write(chapter_text(n, 50))
    r = state.migrate(b, published_upto=1); assert r["facts"] == 1 and r["chapters"] == 2
    assert [f["id"] for f in state.active_facts(b, 3)] == ["a"] and state.active_facts(b, 5) == [] and state.active_facts(b, 1) == []
    assert state.chapter(b, 1)["status"] == "PUBLISHED" and state.chapter(b, 2)["status"] == "COMMITTED" and "X gặp Y" in state.chapter(b, 1)["summary"]
    assert [x["content"] for x in state.open_foreshadowing(b, 3)] == ["[H1] bí mật thanh kiếm cổ"]  # visibility window
    assert state.next_chapter(b) == 3
