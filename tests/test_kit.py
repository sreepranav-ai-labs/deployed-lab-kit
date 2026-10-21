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


def test_chat_completions_url_for_servers_and_cloud_providers():
    from deployed_kit.gateway import chat_completions_url as u
    assert u("http://localhost:8000") == "http://localhost:8000/v1/chat/completions"
    assert u("http://localhost:8000/") == "http://localhost:8000/v1/chat/completions"
    assert u("https://res.openai.azure.com/openai/v1/") == "https://res.openai.azure.com/openai/v1/chat/completions"
    assert u("https://bedrock-runtime.ap-south-1.amazonaws.com/openai/v1").endswith("/openai/v1/chat/completions")
    assert u("https://acct.snowflakecomputing.com/api/v2/cortex/v1").endswith("/cortex/v1/chat/completions")
    assert u("https://x.cloud.databricks.com/ai-gateway/mlflow/v1").endswith("/mlflow/v1/chat/completions")
    assert u("https://asia-south1-aiplatform.googleapis.com/v1/projects/p/locations/asia-south1/endpoints/openapi").endswith(
        "/endpoints/openapi/chat/completions")


def test_stats_ranges_repeats_and_comparisons():
    from deployed_kit import stats
    assert stats.wilson(57, 60) == (0.863, 0.983)
    assert stats.wilson(60, 60)[0] == 0.94
    assert stats.pass_at_k(2, 3, 3) == 1.0 and stats.pass_hat_k(2, 3, 3) == 0.0 and stats.pass_hat_k(3, 3, 3) == 1.0
    assert stats.mean_pass([(3, 3), (2, 3)], 3, every_time=True) == 0.5
    assert stats.mean_pass([(3, 3), (0, 3)], 3, every_time=False) == 0.5
    mean, lo, hi = stats.t_interval([0.9, 0.95, 0.92])
    assert lo < mean < hi and round(mean, 2) == 0.92
    assert stats.mcnemar(5, 2) == 0.4531 and stats.mcnemar(0, 0) == 1.0 and stats.mcnemar(10, 0) < 0.01
    assert stats.disagreement([3, 0], 3) == 0.0 and stats.disagreement([2], 3) == 0.6667
    assert stats.flip_rate([["A", "A"], ["A", "B"]]) == 0.5


def test_ollama_context_window_is_set_only_when_asked():
    import os
    from deployed_kit import gateway as g
    sent = {}
    gw = g.Gateway(provider="ollama", model="m")
    gw._post = lambda url, body, headers: sent.update(body) or {"message": {"content": "{}"}}
    os.environ.pop("LAB_NUM_CTX", None)
    gw.complete([{"role": "user", "content": "x"}])
    assert "num_ctx" not in sent["options"]
    os.environ["LAB_NUM_CTX"] = "8192"
    try:
        gw.complete([{"role": "user", "content": "x"}])
        assert sent["options"]["num_ctx"] == 8192
    finally:
        os.environ.pop("LAB_NUM_CTX")
