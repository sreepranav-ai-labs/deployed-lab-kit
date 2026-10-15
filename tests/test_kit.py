from deployed_kit import Gateway, evaluate, gate
from deployed_kit.synth import Synth


def test_mock_gateway_records_tokens_and_cost():
    gw = Gateway(provider="mock", mock_fn=lambda m: '{"label": "A"}', price_in_per_1k=1.0, price_out_per_1k=2.0)
    out = gw.complete([{"role": "user", "content": "one two three"}])
    assert out.json() == {"label": "A"}
    assert out.tokens_in == 3 and out.tokens_out == 2
    assert abs(out.cost - (3 / 1000 * 1.0 + 2 / 1000 * 2.0)) < 1e-9


def test_json_tolerates_code_fences():
    gw = Gateway(provider="mock", mock_fn=lambda m: '```json\n{"a": 1}\n```')
    assert gw.complete([{"role": "user", "content": "x"}]).json() == {"a": 1}


def test_evaluate_and_gate():
    gold = [{"id": 1, "c": "x"}, {"id": 2, "c": "y"}, {"id": 3, "c": "y"}, {"id": 4, "c": "x"}]
    pred = [{"id": 1, "c": "x"}, {"id": 2, "c": "y"}, {"id": 3, "c": "x"}]
    m = evaluate(gold, pred, key="id", fields=["c"])
    assert m["missing"] == 1
    assert m["fields"]["c"]["accuracy"] == 0.5
    ok, why = gate(m, {"c.accuracy": 0.6})
    assert not ok and "below the minimum" in why[0]
    ok, _ = gate(m, {"c.accuracy": 0.5})
    assert ok


def test_gate_upper_limits():
    m = {"fields": {}, "ops": {"cost_per_task": 0.02}}
    ok, why = gate(m, {"ops.cost_per_task_max": 0.01})
    assert not ok and "above the limit" in why[0]


def test_synth_is_seeded_and_ids_are_not_real():
    a, b = Synth(7), Synth(7)
    assert [a.name() for _ in range(5)] == [b.name() for _ in range(5)]
    assert a.fake_phone().startswith("5")
    assert a.fake_national_id().startswith("0")
