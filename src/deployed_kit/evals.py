"""Evaluation and the regression gate (Chapter 13).

evaluate() compares predictions with an answer key, field by field.
gate() checks the metrics against agreed thresholds and says why it failed.
write_report() saves a JSON and a Markdown report a reviewer can read.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


def _field_metrics(pairs: list[tuple[str, str]]) -> dict:
    labels = sorted({t for t, _ in pairs} | {p for _, p in pairs})
    correct = sum(1 for t, p in pairs if t == p)
    confusion: dict[str, Counter] = defaultdict(Counter)
    for t, p in pairs:
        confusion[t][p] += 1
    per_label = {}
    for label in labels:
        tp = confusion[label][label]
        fp = sum(confusion[t][label] for t in labels if t != label)
        fn = sum(c for p, c in confusion[label].items() if p != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        support = sum(confusion[label].values())
        per_label[label] = {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4), "support": support}
    supported = [v for v in per_label.values() if v["support"] > 0]
    macro_f1 = sum(v["f1"] for v in supported) / len(supported) if supported else 0.0
    return {
        "accuracy": round(correct / len(pairs), 4) if pairs else 0.0,
        "macro_f1": round(macro_f1, 4),
        "per_label": per_label,
        "confusion": {t: dict(c) for t, c in confusion.items()},
    }


def evaluate(gold: list[dict], predicted: list[dict], key: str, fields: list[str]) -> dict:
    """Score predicted records against gold records matched on `key`."""
    by_key = {p[key]: p for p in predicted}
    missing = [g[key] for g in gold if g[key] not in by_key]
    results = {"n": len(gold), "missing": len(missing), "fields": {}}
    for f in fields:
        pairs = [(str(g[f]), str(by_key.get(g[key], {}).get(f, "__MISSING__"))) for g in gold]
        results["fields"][f] = _field_metrics(pairs)
    return results


def gate(metrics: dict, thresholds: dict) -> tuple[bool, list[str]]:
    """thresholds: {"field.metric": minimum, "aggregate.metric": minimum or maximum}

    Keys ending in _max are upper limits (for example cost or failure rates);
    every other key is a lower limit.
    """
    failures = []
    for name, limit in thresholds.items():
        path = name[:-4] if name.endswith("_max") else name
        scope, metric = path.split(".", 1)
        value = metrics["fields"][scope][metric] if scope in metrics.get("fields", {}) else metrics.get(scope, {}).get(metric)
        if value is None:
            failures.append(f"{name}: no value")
        elif name.endswith("_max") and value > limit:
            failures.append(f"{path} = {value} is above the limit {limit}")
        elif not name.endswith("_max") and value < limit:
            failures.append(f"{path} = {value} is below the minimum {limit}")
    return (not failures, failures)


def write_report(metrics: dict, out_dir: str | Path, title: str, passed: bool, failures: list[str]) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    lines = [f"# {title}", "", f"**Gate: {'PASSED' if passed else 'FAILED'}**", ""]
    lines += [f"- {f}" for f in failures] or ["All thresholds met."]
    lines += ["", f"Records: {metrics['n']} (missing predictions: {metrics['missing']})", ""]
    for field_name, m in metrics["fields"].items():
        lines += [f"## {field_name}", "", f"Accuracy {m['accuracy']}, macro F1 {m['macro_f1']}", "",
                  "| Label | Precision | Recall | F1 | Support |", "| --- | --- | --- | --- | --- |"]
        for label, v in m["per_label"].items():
            lines.append(f"| {label} | {v['precision']} | {v['recall']} | {v['f1']} | {v['support']} |")
        lines.append("")
    for scope, values in metrics.items():
        if isinstance(values, dict) and scope not in ("fields",):
            lines += [f"## {scope}", ""] + [f"- {k}: {v}" for k, v in values.items()] + [""]
    path = out / "report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
