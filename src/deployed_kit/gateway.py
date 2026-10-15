"""A thin model gateway.

Every lab calls models through this one class, so a lab can switch from a local
open-weight model to a cloud provider by changing configuration, not code
(Chapter 5, "keep a second model in reach"). It also records tokens, latency
and cost for every call, which the operations milestone builds on (Chapter 14).

Providers:
  mock               a Python function you pass in; used by tests and CI
  ollama             a local Ollama server (default http://localhost:11434)
  openai_compatible  any server with an OpenAI-style /v1/chat/completions
                     endpoint, such as vLLM or a cloud provider's compatible API
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Callable

Message = dict  # {"role": "system" | "user" | "assistant", "content": str}


@dataclass
class Completion:
    text: str
    provider: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0
    cost: float = 0.0
    raw: dict = field(default_factory=dict)

    def json(self) -> dict:
        """Parse the text as JSON, tolerating a fenced code block around it."""
        text = self.text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"model did not return JSON: {self.text[:200]!r}")
        return json.loads(text[start : end + 1])


class Gateway:
    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        mock_fn: Callable[[list[Message]], str] | None = None,
        price_in_per_1k: float | None = None,
        price_out_per_1k: float | None = None,
        timeout_s: float = 120.0,
    ):
        self.provider = provider or os.getenv("LAB_PROVIDER", "mock")
        self.model = model or os.getenv("LAB_MODEL", "mock")
        self.base_url = (base_url or os.getenv("LAB_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("LAB_API_KEY", "")
        self.mock_fn = mock_fn
        self.price_in = price_in_per_1k if price_in_per_1k is not None else float(os.getenv("LAB_PRICE_IN_PER_1K", "0"))
        self.price_out = price_out_per_1k if price_out_per_1k is not None else float(os.getenv("LAB_PRICE_OUT_PER_1K", "0"))
        self.timeout_s = timeout_s
        if self.provider == "mock" and mock_fn is None:
            raise ValueError("the mock provider needs a mock_fn")

    # ------------------------------------------------------------------ public
    def complete(self, messages: list[Message], json_mode: bool = False, temperature: float = 0.0) -> Completion:
        started = time.perf_counter()
        if self.provider == "mock":
            result = self._mock(messages)
        elif self.provider == "ollama":
            result = self._ollama(messages, json_mode, temperature)
        elif self.provider == "openai_compatible":
            result = self._openai_compatible(messages, json_mode, temperature)
        else:
            raise ValueError(f"unknown provider {self.provider!r}")
        result.latency_ms = (time.perf_counter() - started) * 1000
        result.cost = result.tokens_in / 1000 * self.price_in + result.tokens_out / 1000 * self.price_out
        return result

    # --------------------------------------------------------------- providers
    def _mock(self, messages: list[Message]) -> Completion:
        text = self.mock_fn(messages)  # type: ignore[misc]
        tokens_in = sum(len(m["content"].split()) for m in messages)
        return Completion(text=text, provider="mock", model=self.model, tokens_in=tokens_in, tokens_out=len(text.split()))

    def _ollama(self, messages, json_mode, temperature) -> Completion:
        url = (self.base_url or "http://localhost:11434") + "/api/chat"
        body = {"model": self.model, "messages": messages, "stream": False, "options": {"temperature": temperature}}
        if json_mode:
            body["format"] = "json"
        data = self._post(url, body, headers={})
        return Completion(
            text=data.get("message", {}).get("content", ""),
            provider="ollama",
            model=self.model,
            tokens_in=int(data.get("prompt_eval_count", 0)),
            tokens_out=int(data.get("eval_count", 0)),
            raw=data,
        )

    def _openai_compatible(self, messages, json_mode, temperature) -> Completion:
        if not self.base_url:
            raise ValueError("openai_compatible needs LAB_BASE_URL, for example http://localhost:8000")
        url = self.base_url + "/v1/chat/completions"
        body = {"model": self.model, "messages": messages, "temperature": temperature}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        data = self._post(url, body, headers=headers)
        usage = data.get("usage", {})
        return Completion(
            text=data["choices"][0]["message"]["content"],
            provider="openai_compatible",
            model=self.model,
            tokens_in=int(usage.get("prompt_tokens", 0)),
            tokens_out=int(usage.get("completion_tokens", 0)),
            raw=data,
        )

    def _post(self, url: str, body: dict, headers: dict) -> dict:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            return json.loads(resp.read().decode())
