"""CLI:  python -m tsagent "breaker trips immediately on close"  [--baseline] [--html trace.html] [--json]"""
from __future__ import annotations

import argparse
import json
import sys

from .agent import Agent, AgentConfig
from .baseline import run_baseline
from .llm import OllamaLLM
from .prompts import DISCLAIMER
from .trace_view import html_trace, text_trace


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="tsagent", description="Agentic electrical troubleshooting assistant (educational).")
    p.add_argument("question")
    p.add_argument("--model", default="dolphin3-3b")
    p.add_argument("--baseline", action="store_true", help="plain model, no tools (for comparison)")
    p.add_argument("--max-steps", type=int, default=8)
    p.add_argument("--decoding", choices=["schema", "json", "free"], default="schema")
    p.add_argument("--html", help="also write an HTML trace view to this path")
    p.add_argument("--json", action="store_true", help="print the full result as JSON")
    a = p.parse_args(argv)
    llm = OllamaLLM(model=a.model)
    if a.baseline:
        r = run_baseline(llm, a.question)
        print(r["rendered"] + f"\n\n{DISCLAIMER}")
        return 0
    res = Agent(llm, AgentConfig(max_steps=a.max_steps, decoding=a.decoding)).run(a.question).to_dict()
    print(json.dumps(res, indent=1, default=str) if a.json else text_trace(res))
    if a.html:
        open(a.html, "w").write(html_trace(res))
        print(f"\nHTML trace written to {a.html}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
