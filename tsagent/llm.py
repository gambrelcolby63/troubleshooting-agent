"""LLM backends: Ollama (local) and a scripted mock used by tests/CI."""
from __future__ import annotations

import json
import os
import time
import urllib.request


class OllamaLLM:
    def __init__(self, model: str = "dolphin3-3b", url: str | None = None, temperature: float = 0.0,
                 seed: int = 0, num_ctx: int = 4096, timeout: int = 300):
        self.model, self.temperature, self.seed, self.num_ctx, self.timeout = model, temperature, seed, num_ctx, timeout
        self.url = url or os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")

    def chat(self, messages: list[dict], max_tokens: int = 320, json_mode: bool = False, schema: dict | None = None,
             temperature: float | None = None, seed: int | None = None) -> dict:
        body = {"model": self.model, "messages": messages, "stream": False,
                "options": {"temperature": self.temperature if temperature is None else temperature,
                            "seed": self.seed if seed is None else seed, "num_predict": max_tokens,
                            "num_ctx": self.num_ctx}}
        if schema is not None:
            body["format"] = schema   # Ollama structured outputs: grammar-constrained to this JSON Schema
        elif json_mode:
            body["format"] = "json"   # any syntactically valid JSON
        req = urllib.request.Request(f"{self.url}/api/chat", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            d = json.loads(r.read())
        return {"content": d["message"]["content"], "latency_s": round(time.time() - t0, 2),
                "prompt_tokens": d.get("prompt_eval_count"), "output_tokens": d.get("eval_count"),
                "done_reason": d.get("done_reason")}


class MockLLM:
    """Returns pre-scripted replies in order (str or dict -> JSON). Records every prompt it was sent."""

    def __init__(self, replies: list):
        self.replies = list(replies)
        self.calls: list[list[dict]] = []

    def chat(self, messages: list[dict], max_tokens: int = 320, json_mode: bool = False, schema: dict | None = None,
             temperature: float | None = None, seed: int | None = None) -> dict:
        self.calls.append([dict(m) for m in messages])
        r = self.replies.pop(0) if self.replies else '{"tool": "nothing"}'
        content = r if isinstance(r, str) else json.dumps(r)
        return {"content": content, "latency_s": 0.0, "prompt_tokens": 0, "output_tokens": 0, "done_reason": "stop"}
