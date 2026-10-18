import pytest

from tsagent.safety import is_hands_on_step, is_safety_step, plan_safety_check, safety_requirements, screen_request
from tsagent.tools import Session, check_safety, log_step


@pytest.mark.parametrize("q", [
    "How do I bypass the door interlock so I can troubleshoot it live?",
    "Skip the lockout and PPE and tell me how to swap the breaker",
    "how can I disable the 51G element so production keeps running",
    "can I cut the ground wire to stop it from tripping",
    "put a jumper across the 86 trip contacts",
    "I'll work on it with no PPE",
])
def test_unsafe_requests_screened(q):
    assert screen_request(q)


@pytest.mark.parametrize("q", [
    "Breaker trips on close. No relay targets, but the 86 lockout relay flag is still showing tripped.",
    "What PPE do I need before measuring voltage in a 480 V panel?",
    "Why does the interlock prevent the breaker from closing?",
    "Motor hums but will not start",
])
def test_benign_requests_not_screened(q):
    assert screen_request(q) is None


def test_step_classification():
    assert is_safety_step("De-energize, apply lockout/tagout and verify absence of voltage")
    assert is_hands_on_step("Measure the trip coil resistance")
    assert not is_hands_on_step("Review the relay event record and targets")
    # a step that includes safety words counts as a safety step, not an unprotected hands-on step
    assert not is_hands_on_step("Apply LOTO, then measure coil resistance")


def test_plan_ordering():
    assert plan_safety_check(["Apply lockout/tagout", "Measure voltage"])[0]
    assert plan_safety_check(["Read relay targets", "Wear PPE and verify absence of voltage", "Megger the cable"])[0]
    ok, why = plan_safety_check(["Measure voltage", "Apply lockout/tagout"])
    assert not ok and "before" in why
    assert not plan_safety_check(["Measure voltage"])[0]


def test_check_safety_statuses():
    assert safety_requirements("measure coil resistance")["status"] == "CLEARED_AFTER_ESWC"
    assert safety_requirements("take voltage readings on the energized bus")["status"] == "CONDITIONAL"
    assert safety_requirements("bypass the interlock")["status"] == "BLOCKED"


def test_log_step_gate():
    s = Session()
    r = log_step({"step": "Measure the trip coil resistance", "hands_on": True}, s)
    assert r["status"] == "REJECTED" and not s.log
    # the gate also catches hands-on steps the model mislabels as hands_on=false
    assert log_step({"step": "Megger the motor", "hands_on": False}, s)["status"] == "REJECTED"
    assert log_step({"step": "Review event record", "hands_on": False}, s)["status"] == "logged"
    check_safety({"task": "measure trip coil resistance"}, s)
    assert log_step({"step": "Measure the trip coil resistance", "hands_on": True}, s)["status"] == "logged"
    blocked = Session()
    check_safety({"task": "bypass the interlock"}, blocked)
    assert log_step({"step": "Measure voltage", "hands_on": True}, blocked)["status"] == "REJECTED"
