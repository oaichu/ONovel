import json, pytest
from onovel import judge
TEXT = 'Lâm Phong nói: "Tôi đi đây." Gió thổi qua núi.'
def item(**kw):
    d = dict(rule_id="xung-ho", verdict="violation", severity="high", confidence=0.9, evidence_span='"Tôi đi đây."', reason="tu sĩ xưng tôi", word="Tôi"); d.update(kw); return d
def test_accept_structural():
    out = judge.accept([item(), item(), item(verdict="ok")], TEXT)
    assert len(out) == 1 and out[0]["rule_id"] == "xung-ho" and out[0]["source"] == "llm" and not out[0].get("review")
def test_low_confidence_and_unverifiable_become_review_not_dropped():
    out = judge.accept([item(confidence=0.3), item(rule_id="a", evidence_span="không có trong chương"), item(rule_id="b", word="xyz")], TEXT)
    assert len(out) == 3 and all(v["review"] and v["severity"] == "low" for v in out)
@pytest.mark.parametrize("bad", [dict(confidence="cao"), dict(confidence=None), dict(confidence=1.7), dict(confidence=True),
                                 dict(evidence_span=None), dict(evidence_span="ab"), dict(evidence_span=5), dict(verdict="maybe"), dict(verdict=None)])
def test_malformed_items_raise(bad):
    with pytest.raises(judge.JudgeError): judge.accept([item(**bad)], TEXT)
def test_non_dict_item_raises():
    with pytest.raises(judge.JudgeError): judge.accept(["oops"], TEXT)
def test_malformed_item_makes_judge_error_not_empty_pass():
    with pytest.raises(judge.JudgeError): judge.judge("t", TEXT, chat=lambda *a, **k: json.dumps({"items": [item(confidence="x")]}))
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
