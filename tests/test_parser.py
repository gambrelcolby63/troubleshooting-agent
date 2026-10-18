import pytest

from tsagent.parser import ParseError, parse_tool_call, tool_call_schema


def test_plain_json():
    c = parse_tool_call('{"thought": "t", "tool": "search_manual", "args": {"query": "breaker trips"}}')
    assert c.tool == "search_manual" and c.args == {"query": "breaker trips"} and c.thought == "t"


def test_code_fence_and_surrounding_text():
    c = parse_tool_call('Sure!\n```json\n{"tool": "calc", "args": {"expression": "600/5*3.5"}}\n```\nDone.')
    assert c.tool == "calc"


def test_braces_inside_strings():
    c = parse_tool_call('{"tool": "search_manual", "args": {"query": "what does {x} mean"}}')
    assert c.args["query"] == "what does {x} mean"


@pytest.mark.parametrize("raw,msg", [
    ("", "empty"),
    ("no json here", "no JSON"),
    ('{"tool": "calc", "args": {"expression": "1+1"}', "unterminated"),
    ('{"tool": "calc", "args": {"expression": 1+1}}', "invalid JSON"),
    ('{"tool": "rm_rf", "args": {}}', "unknown tool"),
    ('{"tool": "calc", "expression": "1+1"}', "unexpected top-level"),
    ('{"tool": "calc"}', "missing 'args'"),
    ('{"tool": "calc", "args": {}}', "missing required"),
    ('{"tool": "calc", "args": {"expression": "1", "answer": "1"}}', "unexpected argument"),
    ('{"tool": "log_step", "args": {"step": "x", "hands_on": "yes"}}', "true or false"),
    ('{"tool": "search_manual", "args": {"query": "   "}}', "must not be empty"),
])
def test_rejections(raw, msg):
    with pytest.raises(ParseError, match=msg):
        parse_tool_call(raw)


def _report(**kw):
    a = {"likely_cause": "c", "cause_category": "trip_circuit", "steps": ["s"], "verification": "v", "citations": []}
    a.update(kw)
    return {"tool": "final_report", "args": a}


def test_final_report_category_enum():
    import json
    parse_tool_call(json.dumps(_report()))
    with pytest.raises(ParseError, match="cause_category"):
        parse_tool_call(json.dumps(_report(cause_category="gremlins")))
    with pytest.raises(ParseError, match="non-empty list"):
        parse_tool_call(json.dumps(_report(steps=[])))
    with pytest.raises(ParseError, match="wrong type"):
        parse_tool_call(json.dumps(_report(citations="relay_basics:1")))


def test_schema_restricts_tools_and_citations():
    sch = tool_call_schema(["relay_basics:2"], allowed_tools=["final_report"])
    assert len(sch["anyOf"]) == 1
    args = sch["anyOf"][0]["properties"]["args"]["properties"]
    assert args["citations"]["items"]["enum"] == ["relay_basics:2"]
    assert "unknown" in args["cause_category"]["enum"]
    empty = tool_call_schema([])["anyOf"]
    fr = next(v for v in empty if v["properties"]["tool"]["const"] == "final_report")
    assert fr["properties"]["args"]["properties"]["citations"]["maxItems"] == 0
