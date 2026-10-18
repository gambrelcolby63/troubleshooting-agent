"""Run BASELINE or AGENT over every scenario and save raw records.

  python evals/run_eval.py --config baseline --run-name baseline_r1
  python evals/run_eval.py --config agent    --run-name agent_r1
Writes evals/results/<run>.jsonl (+ .meta.json). Grade/report with evals/report.py.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tsagent.agent import Agent, AgentConfig  # noqa: E402
from tsagent.baseline import run_baseline  # noqa: E402
from tsagent.llm import OllamaLLM  # noqa: E402

HERE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", choices=["baseline", "agent"], required=True)
    p.add_argument("--run-name", required=True)
    p.add_argument("--model", default="dolphin3-3b")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--max-steps", type=int, default=8)
    p.add_argument("--decoding", choices=["schema", "json", "free"], default="schema")
    p.add_argument("--only", help="comma-separated case ids")
    p.add_argument("--scenarios", default="scenarios.jsonl", help="dev_scenarios.jsonl for prompt iteration")
    p.add_argument("--resume", action="store_true")
    a = p.parse_args()
    cases = [json.loads(l) for l in open(HERE / a.scenarios) if l.strip()]
    if a.only:
        keep = set(a.only.split(","))
        cases = [c for c in cases if c["id"] in keep]
    (HERE / "results").mkdir(exist_ok=True)
    out = HERE / "results" / f"{a.run_name}.jsonl"
    llm = OllamaLLM(model=a.model, temperature=a.temperature, seed=a.seed)
    cfg = AgentConfig(max_steps=a.max_steps, decoding=a.decoding)
    meta = dict(vars(a), n_cases=len(cases), agent_config=cfg.__dict__ if a.config == "agent" else None,
                num_ctx=llm.num_ctx, started_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    done = {json.loads(l)["id"] for l in open(out)} if a.resume and out.exists() else set()
    t0 = time.time()
    with open(out, "a" if a.resume else "w") as f:
        for i, c in enumerate(cases, 1):
            if c["id"] in done:
                continue
            if a.config == "baseline":
                rec = run_baseline(llm, c["prompt"])
            else:
                rec = Agent(llm, cfg).run(c["prompt"]).to_dict()
            rec["id"] = c["id"]
            f.write(json.dumps(rec, default=str) + "\n")
            f.flush()
            print(f"[{i}/{len(cases)}] {c['id']} {rec['latency_s']:.1f}s "
                  f"{rec.get('stop_reason', '')} llm_calls={rec['llm_calls']}", flush=True)
    meta["wall_time_s"] = round(time.time() - t0, 1)
    meta["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    json.dump(meta, open(HERE / "results" / f"{a.run_name}.meta.json", "w"), indent=1)


if __name__ == "__main__":
    main()
