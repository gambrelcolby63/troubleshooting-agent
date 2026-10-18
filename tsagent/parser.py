"""Strict parser + schema validation for the model's JSON tool calls.

The model must reply with exactly one JSON object: {"thought": str?, "tool": str, "args": {...}}.
Anything else raises ParseError with a message that is fed back to the model so it can retry.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

CATEGORIES = {
    "trip_circuit": "breaker trip/close control wiring, trip coil, 52a contact, 86 lockout, DC trip fuse",
    "breaker_mechanism": "closing spring, charging motor, latch or other mechanical breaker problem",
    "relay_settings": "wrong relay setting (pickup, CT ratio setting, curve, settings group)",
    "ct_circuit": "current transformer wiring: polarity, open/shorted CT, wrong CT tap",
    "vt_circuit": "voltage transformer (PT) circuit: blown VT fuse, loss of potential",
    "dc_supply": "station battery, battery charger, DC ground faults",
    "ups": "UPS input, battery, overload, bypass problems",
    "motor_control_circuit": "starter control circuit: control fuse, coil, stop/permissive contacts",
    "motor_overload": "motor overloaded mechanically or overload relay set wrong",
    "single_phasing": "loss of one supply phase (blown fuse, failed contactor pole, open conductor)",
    "insulation_failure": "insulation breakdown / ground fault in a winding or cable",
    "procedure": "the question is a how-to or calculation, not a fault",
    "unknown": "the knowledge base does not cover it: say I don't know",
    "unsafe_request": "the request is unsafe and must be refused",
}

# tool name -> {arg: (type(s), required)}
SCHEMAS: dict[str, dict[str, tuple]] = {
    "search_manual": {"query": (str, True)},
    "calc": {"expression": (str, True)},
    "check_safety": {"task": (str, True)},
    "log_step": {"step": (str, True), "hands_on": (bool, True), "finding": (str, False)},
    "final_report": {"likely_cause": (str, True), "cause_category": (str, True), "steps": (list, True),
                     "verification": (str, True), "citations": (list, True), "answer": ((str, int, float), False)},
}


class ParseError(ValueError):
    pass


@dataclass
class ToolCall:
    tool: str
    args: dict
    thought: str = ""
    raw: str = field(default="", repr=False)


def _first_json_object(text: str) -> str:
    """Return the first balanced {...} substring, honouring JSON strings/escapes."""
    start = text.find("{")
    if start < 0:
        raise ParseError("no JSON object found")
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ParseError("unterminated JSON object")


def validate_args(tool: str, args: dict) -> dict:
    if tool not in SCHEMAS:
        raise ParseError(f"unknown tool {tool!r}; valid tools: {', '.join(SCHEMAS)}")
    if not isinstance(args, dict):
        raise ParseError("'args' must be a JSON object")
    schema = SCHEMAS[tool]
    extra = set(args) - set(schema)
    if extra:
        raise ParseError(f"{tool}: unexpected argument(s) {sorted(extra)}; allowed: {sorted(schema)}")
    for name, (typ, required) in schema.items():
        if name not in args:
            if required:
                raise ParseError(f"{tool}: missing required argument {name!r}")
            continue
        v = args[name]
        if typ is bool and not isinstance(v, bool):
            raise ParseError(f"{tool}: {name!r} must be true or false")
        if not isinstance(v, typ) or (typ is not bool and isinstance(v, bool)):
            raise ParseError(f"{tool}: {name!r} has the wrong type")
        if isinstance(v, str) and not v.strip() and required:
            raise ParseError(f"{tool}: {name!r} must not be empty")
    if tool == "final_report":
        if args["cause_category"] not in CATEGORIES:
            raise ParseError(f"final_report: cause_category must be one of {sorted(CATEGORIES)}")
        if not all(isinstance(s, str) for s in args["steps"]) or not args["steps"]:
            raise ParseError("final_report: 'steps' must be a non-empty list of strings")
        if not all(isinstance(s, str) for s in args["citations"]):
            raise ParseError("final_report: 'citations' must be a list of section id strings")
    return args


def parse_tool_call(text: str) -> ToolCall:
    if not text or not text.strip():
        raise ParseError("empty reply")
    blob = _first_json_object(text)
    try:
        obj = json.loads(blob)
    except json.JSONDecodeError as e:
        raise ParseError(f"invalid JSON: {e.msg}") from None
    if not isinstance(obj, dict):
        raise ParseError("top level must be a JSON object")
    extra = set(obj) - {"thought", "tool", "args"}
    if extra:
        raise ParseError(f"unexpected top-level key(s) {sorted(extra)}; use {{\"thought\", \"tool\", \"args\"}}")
    tool = obj.get("tool")
    if not isinstance(tool, str):
        raise ParseError("missing 'tool' (string)")
    args = obj.get("args", None)
    if args is None:
        raise ParseError("missing 'args' (object)")
    validate_args(tool, args)
    thought = obj.get("thought", "")
    return ToolCall(tool=tool, args=args, thought=thought if isinstance(thought, str) else "", raw=text)


_JSON_TYPES = {str: {"type": "string"}, bool: {"type": "boolean"}, list: {"type": "array", "items": {"type": "string"}}}


def tool_call_schema(allowed_citations: list[str] | None = None, allowed_tools: list[str] | None = None) -> dict:
    """JSON Schema (anyOf one object per tool) for Ollama structured outputs / constrained decoding.
    Citations are restricted to ids the tools have actually returned in this session."""
    variants = []
    for tool, spec in SCHEMAS.items():
        if allowed_tools is not None and tool not in allowed_tools:
            continue
        props, req = {}, []
        for name, (typ, required) in spec.items():
            if isinstance(typ, tuple):
                props[name] = {"type": "string"}
            else:
                props[name] = dict(_JSON_TYPES[typ])
            if required:
                req.append(name)
        if tool == "calc":
            props["expression"]["pattern"] = r"^[0-9a-z_+*/(). ,-]+$"
        if tool == "final_report":
            props["cause_category"] = {"type": "string", "enum": list(CATEGORIES)}
            props["steps"] = {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 6}
            cites = sorted(allowed_citations or [])
            props["citations"] = ({"type": "array", "items": {"type": "string", "enum": cites}, "maxItems": 4}
                                  if cites else {"type": "array", "maxItems": 0})
        variants.append({"type": "object", "additionalProperties": False, "required": ["thought", "tool", "args"],
                         "properties": {"thought": {"type": "string"}, "tool": {"const": tool},
                                        "args": {"type": "object", "properties": props, "required": req,
                                                 "additionalProperties": False}}})
    return {"anyOf": variants}
