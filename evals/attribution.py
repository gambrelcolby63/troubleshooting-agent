"""How much of the agent's score is the model vs the deterministic guardrails?
Counts check passes that did NOT depend on a controller repair of that same property.
  python evals/attribution.py agent_r1 [agent_r2 ...]"""
import sys

from grade import grade_run

FIX_FOR = {"safety_first": "inserted safety step", "citation": "added top retrieved section", "calc": "copied last calc"}

for run in sys.argv[1:]:
    g = grade_run(run)
    print(f"## {run}")
    for check, marker in FIX_FOR.items():
        app = [x for x in g if check in x["checks"]]
        passed = [x for x in app if x["checks"][check]]
        own = [x for x in passed if not any(e["type"] == "forced_fix" and marker in e["what"] for e in x["guardrail_events"])]
        print(f"- {check}: {len(passed)}/{len(app)} with guardrails, {len(own)}/{len(app)} without a repair of that property")
    ref = [x for x in g if "refusal" in x["checks"]]
    print(f"- refusal: {sum(x['checks']['refusal'] for x in ref)}/{len(ref)} total, "
          f"{sum(x['stop_reason'] == 'input_guardrail_refusal' for x in ref)} by the input regex screen, "
          f"{sum(x['checks']['refusal'] and x['stop_reason'] != 'input_guardrail_refusal' for x in ref)} by the model")
    print(f"- reports repaired by the controller (any property): "
          f"{sum(any(e['type'] == 'forced_fix' for e in x['guardrail_events']) for x in g)}/{len(g)}")
