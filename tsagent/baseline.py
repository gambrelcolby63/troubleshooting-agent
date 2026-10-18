"""BASELINE: the same model, one plain chat call, no tools/retrieval/guardrails."""
from __future__ import annotations

import time

from .prompts import baseline_system


def run_baseline(llm, question: str, max_tokens: int = 512) -> dict:
    t0 = time.time()
    out = llm.chat([{"role": "system", "content": baseline_system()}, {"role": "user", "content": question}],
                   max_tokens=max_tokens)
    return {"question": question, "rendered": out["content"], "llm_calls": 1, "latency_s": round(time.time() - t0, 2),
            "output_tokens": out.get("output_tokens"), "done_reason": out.get("done_reason")}
