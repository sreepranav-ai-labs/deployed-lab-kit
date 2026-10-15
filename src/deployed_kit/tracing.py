"""Minimal tracing: one JSON line per step, grouped by task.

Deliberately simple so it runs anywhere. The production milestone of each lab
adds an OpenTelemetry exporter on top; the record shape here maps onto spans.
"""

from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from pathlib import Path


class Tracer:
    def __init__(self, path: str | Path | None):
        self.path = Path(path) if path else None
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def new_trace(self) -> str:
        return uuid.uuid4().hex[:16]

    @contextmanager
    def span(self, trace_id: str, name: str, **attrs):
        record = {"trace_id": trace_id, "span": name, "start": time.time(), **attrs}
        try:
            yield record
            record["status"] = "ok"
        except Exception as exc:  # recorded, then re-raised
            record["status"] = "error"
            record["error"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            record["duration_ms"] = round((time.time() - record["start"]) * 1000, 2)
            self._write(record)

    def _write(self, record: dict) -> None:
        if not self.path:
            return
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
