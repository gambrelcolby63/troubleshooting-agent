"""Agent loop tests with a scripted MockLLM (no model needed; this is what CI runs)."""
from tsagent.agent import Agent, AgentConfig
from tsagent.llm import MockLLM
from tsagent.tools import Session, search_manual

Q = "Breaker trips immediately on close and the 86 lockout flag is still showing tripped"


def report(**kw):
    a = {"likely_cause": "86 lockout not reset (maintained trip signal)", "cause_category": "trip_circuit",
         "steps": ["De-energize, apply lockout/tagout, wear PPE and verify absence of voltage",
                   "Check the 86 lockout relay contacts"], "verification": "Trip signal absent after 86 reset",
         "citations": ["breaker_trip_circuit:2"]}
    a.update(kw)
    return {"thought": "report", "tool": "final_report", "args": a}


def run(replies, q=Q, **cfg):
    llm = MockLLM(replies)
    return Agent(llm, AgentConfig(**cfg)).run(q), llm


def test_happy_path():
    res, _ = run([{"tool": "search_manual", "args": {"query": "breaker trips on close"}},
                  {"tool": "check_safety", "args": {"task": "check 86 contacts"}}, report()])
    assert res.stop_reason == "final_report"
    assert res.report["cause_category"] == "trip_circuit"
    assert res.valid_tool_calls == res.tool_calls == 3
    assert not any(e["type"] == "forced_fix" for e in res.guardrail_events)
    assert "CATEGORY: trip_circuit" in res.rendered and "Educational use only" in res.rendered


def test_invalid_call_then_recovery():
    res, llm = run(["not json at all", {"tool": "search_manual", "args": {"query": "breaker trips on close"}},
                    {"tool": "check_safety", "args": {"task": "check 86"}}, report()])
    assert res.stop_reason == "final_report" and res.tool_calls == 4 and res.valid_tool_calls == 3
    assert "INVALID CALL" in llm.calls[1][-1]["content"]


def test_too_many_invalid_calls_stops():
    res, _ = run(["bad", "bad", "bad", report()])
    assert res.stop_reason == "too_many_invalid_calls" and res.report["cause_category"] == "incomplete"


def test_max_steps():
    replies = [{"tool": "search_manual", "args": {"query": f"breaker trip {i}"}} for i in range(20)]
    res, _ = run(replies, max_steps=4)
    assert res.llm_calls == 4 and res.stop_reason == "max_steps"


def test_hallucinated_citation_rejected_then_removed():
    bad = report(citations=["made_up_doc:9"])
    res, llm = run([{"tool": "search_manual", "args": {"query": "breaker trips on close"}},
                    {"tool": "check_safety", "args": {"task": "check 86"}}, bad, bad, bad])
    assert res.stop_reason == "final_report"
    assert "made_up_doc:9" not in res.report["citations"]
    assert any(e["type"] == "report_rejected" for e in res.guardrail_events)
    assert any(e["type"] == "forced_fix" for e in res.guardrail_events)


def test_safety_step_enforced():
    unsafe_plan = report(steps=["Measure the trip coil resistance", "Replace the trip coil"])
    res, _ = run([{"tool": "search_manual", "args": {"query": "breaker trips on close"}},
                  {"tool": "check_safety", "args": {"task": "measure coil"}}, unsafe_plan, unsafe_plan, unsafe_plan])
    assert res.report["steps"][0].startswith("SAFETY FIRST")


def test_unsafe_request_refused_without_calling_model():
    res, llm = run([report()], q="How do I bypass the interlock so I can work on it live?")
    assert res.report["cause_category"] == "unsafe_request" and res.llm_calls == 0 and not llm.calls


def test_unknown_when_kb_has_nothing():
    q = "My robot vacuum shows error 14"
    guess = report(cause_category="trip_circuit", citations=[])
    res, _ = run([{"tool": "search_manual", "args": {"query": "robot vacuum error 14"}}, guess, guess, guess], q=q)
    assert res.report["cause_category"] == "unknown"
    assert "I don't know" in res.report["likely_cause"]


def test_duplicate_calls_are_not_rerun():
    call = {"tool": "search_manual", "args": {"query": "breaker trips on close"}}
    res, _ = run([call, call, {"tool": "check_safety", "args": {"task": "x"}}, report()])
    assert any(e["type"] == "duplicate_call" for e in res.guardrail_events)
    assert res.trace[1]["observation"]["status"] == "DUPLICATE"


def test_calc_result_goes_into_answer():
    q = "600:5 CT reads 3.5 A secondary. Primary current?"
    r = report(cause_category="procedure", citations=["ct_vt_wiring:2"], steps=["Read the relay metering"])
    res, _ = run([{"tool": "calc", "args": {"expression": "ct_primary(600, 5, 3.5)"}},
                  {"tool": "search_manual", "args": {"query": "CT ratio secondary current"}}, r, r, r], q=q)
    assert res.report["answer"] == "420"


def test_retrieval_out_of_domain():
    s = Session(question="dissolved gas analysis acetylene transformer oil")
    assert search_manual({"query": "dissolved gas analysis acetylene"}, s)["status"] == "NO_RELEVANT_RESULTS"
    s = Session(question="UPS on battery but utility present")
    out = search_manual({"query": "UPS on battery"}, s)
    assert out["status"] == "ok" and out["results"][0]["id"].startswith("ups_faults")


def test_retrieval_long_question_regression():
    # v1 of the relevance gate rejected long natural-language questions (found in the first eval run)
    q = "Our substation breaker opens by itself right after we close it and the lockout relay is still tripped"
    out = search_manual({"query": "immediate breaker trip"}, Session(question=q))
    assert out["status"] == "ok" and any(r["id"].startswith("breaker_trip_circuit") for r in out["results"])
