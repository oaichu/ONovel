import json, pytest
from onovel import judge
TEXT = 'Lâm Phong nói: "Tôi đi đây." Gió thổi qua núi.'
def item(**kw):
    d = dict(rule_id="xung-ho", verdict="violation", severity="high", confidence=0.9, evidence_span='"Tôi đi đây."', reason="tu sĩ xưng tôi", word="Tôi"); d.update(kw); return d
def test_accept_structural():
    out = judge.accept([item(), item(), item(verdict="ok"), item(confidence=0.3), item(evidence_span="không có trong chương"), item(word="xyz")], TEXT)
    assert len(out) == 1 and out[0]["rule_id"] == "xung-ho" and out[0]["source"] == "llm"
def test_reason_keywords_do_not_filter():
    assert len(judge.accept([item(reason="từ này phù hợp? không, sai xưng hô")], TEXT)) == 1
def test_api_error_raises():
    def boom(*a, **k): raise TimeoutError("x")
    with pytest.raises(judge.JudgeError): judge.judge("t", TEXT, chat=boom)
def test_bad_json_raises():
    with pytest.raises(judge.JudgeError): judge.judge("t", TEXT, chat=lambda *a, **k: "không phải json")
    with pytest.raises(judge.JudgeError): judge.judge("t", TEXT, chat=lambda *a, **k: '{"x": 1}')
def test_ok():
    assert judge.judge("t", TEXT, chat=lambda *a, **k: json.dumps({"items": [item()]})) [0]["word"] == "Tôi"
