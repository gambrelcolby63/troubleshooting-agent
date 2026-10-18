#!/usr/bin/env bash
# Experiment used for the README numbers (CPU; ~25-30 min per agent run, ~12 min per baseline run).
# Runs are sequential on one Ollama server; --resume continues an interrupted run.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
[ -s evals/results/baseline_r1.meta.json ] || $PY evals/run_eval.py --config baseline --run-name baseline_r1 --resume
[ -s evals/results/agent_r1.meta.json ]    || $PY evals/run_eval.py --config agent    --run-name agent_r1 --resume
[ -s evals/results/baseline_r2.meta.json ] || $PY evals/run_eval.py --config baseline --run-name baseline_r2 --resume
[ -s evals/results/agent_r2.meta.json ]    || $PY evals/run_eval.py --config agent    --run-name agent_r2 --resume
# optional ablation: plain JSON mode instead of JSON-Schema constrained decoding
[ -n "${SKIP_ABLATION:-}" ] || [ -s evals/results/agent_jsononly_r1.meta.json ] || \
  $PY evals/run_eval.py --config agent --run-name agent_jsononly_r1 --decoding json --resume
