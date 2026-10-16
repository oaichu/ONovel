import os, json, yaml
import stylegate, lockcheck
from onovel import gates, state
from conftest import chapter_text
def w(p, t): open(p, "w", encoding="utf-8").write(t); return p
def test_judge_error_is_ERROR(book, tmp_path):
    c = w(tmp_path / "c.md", chapter_text(1))
    def boom(*a, **k): raise TimeoutError("down")
    r = stylegate.check(book, c, True, chat=boom); assert r["verdict"] == "ERROR" and gates.EXIT["ERROR"] == 2
def test_rule_fail_blocks(book, tmp_path):
    c = w(tmp_path / "c.md", chapter_text(1, extra="\n\nHắn cười — rồi đi."))
    r = stylegate.check(book, c, False); assert r["verdict"] == "FAIL" and r["blocking"][0]["rule_id"] == "em-dash"
def test_layout_blocking_per_manifest(book, tmp_path):
    c = w(tmp_path / "c.md", chapter_text(1, words=300))
    assert stylegate.check(book, c, False)["verdict"] == "FAIL"
    m = yaml.safe_load(open(os.path.join(book, "onovel.yaml"))); m["layout"]["blocking"] = ["heading"]
    open(os.path.join(book, "onovel.yaml"), "w").write(yaml.safe_dump(m, allow_unicode=True))
    r = stylegate.check(book, c, False); assert r["verdict"] == "PASS" and r["warnings"][0]["rule_id"] == "layout-length"
def test_soft_issues_and_combine(book, tmp_path):
    c = w(tmp_path / "c.md", chapter_text(1))
    soft = json.dumps({"items": [{"rule_id": f"r{i}", "verdict": "violation", "severity": "low", "confidence": 0.8, "evidence_span": f"lần {i}. \"Ta", "reason": "x"} for i in range(5)]})
    r = stylegate.check(book, c, True, chat=lambda *a, **k: soft); assert r["verdict"] == "PASS" and len(r["soft"]) == 5
    ok = gates.verdict("lock", c, "", [], [], [], None)
    assert gates.combine([r, ok], 3)["verdict"] == "FAIL" and gates.combine([r, ok], 5)["verdict"] == "PASS"
    assert gates.combine([r, gates.error("lock", c, "x")], 99)["verdict"] == "ERROR"
def test_lock_regex_blocks_and_negation(book, tmp_path):
    state.add_fact(book, "phong-mu", "Lâm Phong", "Lâm Phong bị mù", forbid=[r"Lâm Phong nhìn thấy"])
    c = w(tmp_path / "c.md", chapter_text(1, extra="\n\nLâm Phong nhìn thấy ánh trăng."))
    assert lockcheck.check(book, c, False)["verdict"] == "FAIL"
    c2 = w(tmp_path / "c2.md", chapter_text(1, extra="\n\nKhông, Lâm Phong nhìn thấy gì đâu."))
    assert lockcheck.check(book, c2, False)["verdict"] == "FAIL"  # negation must be right before the verb phrase
    c3 = w(tmp_path / "c3.md", chapter_text(1, extra="\n\nLâm Phong không thể nhìn thấy."))
    assert lockcheck.check(book, c3, False)["verdict"] == "PASS"
def test_canon_gate_sequence(book, tmp_path):
    c = w(tmp_path / "c.md", chapter_text(2))
    assert state.canon_gate(book, c, 2)["verdict"] == "FAIL"
    assert state.canon_gate(book, c, 1)["verdict"] == "PASS"
def test_cli_exit_codes(book, tmp_path, monkeypatch):
    from onovel import cli
    c = str(w(tmp_path / "c.md", chapter_text(1))); out = str(tmp_path / "g.json")
    assert cli.main(["gate", book, c, "--n", "1", "--no-llm", "--out", out]) == 0
    monkeypatch.setenv("ONOVEL_MOCK_LLM", "error")
    assert cli.main(["gate", book, c, "--n", "1", "--out", out]) == 2 and json.load(open(out))["verdict"] == "ERROR"
