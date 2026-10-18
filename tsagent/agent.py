"""The agent loop: LLM proposes one JSON tool call per turn; the controller parses, validates, executes,
enforces guardrails and feeds observations back until final_report (or a limit is hit)."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field

from .parser import ParseError, parse_tool_call, tool_call_schema
from .prompts import DISCLAIMER, agent_system
from .safety import is_hands_on_step, plan_safety_check, screen_request
from .tools import TOOLS, Session

SAFETY_STEP = ("SAFETY FIRST: de-energize, apply lockout/tagout to all sources, wear PPE per the arc-flash/shock "
               "risk assessment, and verify absence of voltage (live-dead-live) before any hands-on step.")


@dataclass
class AgentConfig:
    max_steps: int = 8            # max LLM turns per question
    max_consecutive_errors: int = 3
    max_report_rejections: int = 2
    max_tokens: int = 400
    decoding: str = "schema"      # "schema" = JSON-Schema constrained (tool/arg/enum/citation ids),
                                  # "json" = any valid JSON, "free" = unconstrained text. Parser + checks always run.
    retry_temperature: float = 0.5  # after an invalid call, resample with some randomness instead of repeating
    history_char_budget: int = 9000


@dataclass
class AgentResult:
    question: str
    report: dict | None
    rendered: str
    stop_reason: str
    trace: list = field(default_factory=list)
    session_log: list = field(default_factory=list)
    llm_calls: int = 0
    tool_calls: int = 0          # parsed attempts, valid or not
    valid_tool_calls: int = 0
    guardrail_events: list = field(default_factory=list)
    latency_s: float = 0.0

    def to_dict(self) -> dict:
        return dict(self.__dict__)


def render_report(r: dict) -> str:
    """Same text layout as the baseline output, so both are graded by the same graders."""
    lines = [f"CATEGORY: {r.get('cause_category', '')}", f"CAUSE: {r.get('likely_cause', '')}", "STEPS:"]
    lines += [f"{i}. {re.sub(r'^\s*(step\s*)?\d+[.):]\s*', '', s, flags=re.I)}" for i, s in enumerate(r.get("steps", []), 1)]
    lines += [f"VERIFY: {r.get('verification', '')}", f"CITATIONS: {', '.join(r.get('citations', []))}"]
    if r.get("answer") not in (None, ""):
        lines.append(f"ANSWER: {r['answer']}")
    return "\n".join(lines)


def refusal_report(reason: str) -> dict:
    return {"likely_cause": f"I can't help with that: the request involves {reason}, which can kill or injure "
                            f"people and destroy equipment.",
            "cause_category": "unsafe_request",
            "steps": [SAFETY_STEP,
                      "Treat the trip/interlock as information: read relay targets, alarms and event records.",
                      "Troubleshoot the root cause de-energized, or get a qualified person and an energized work "
                      "permit if de-energizing is truly infeasible."],
            "verification": "Root cause identified and corrected with all protection and interlocks in service.",
            "citations": ["nfpa70e_safety:5", "nfpa70e_safety:6"]}


class Agent:
    def __init__(self, llm, config: AgentConfig | None = None):
        self.llm, self.cfg = llm, config or AgentConfig()

    # ---- guardrails on final_report -------------------------------------------------------------
    def _check_report(self, args: dict, s: Session) -> list[str]:
        problems = []
        cat = args["cause_category"]
        bad = [c for c in args["citations"] if c not in s.retrieved]
        if bad:
            problems.append(f"citations {bad} were not returned by any tool; valid ids: {sorted(s.retrieved) or 'none'}")
        if re.search(r"<[^<>]{3,60}>", json.dumps(args)) or any(x.strip(" .") == "" for x in args["steps"]):
            problems.append("the report still contains <placeholder> text from the format example; write real content")
        if s.calcs and args.get("answer") in (None, ""):
            problems.append(f"put the calc result ({s.calcs[-1][1]:g}) with its unit in 'answer'")
        if cat == "unknown" and s.relevant_found:
            problems.append(f"the knowledge base DID return relevant sections {s.search_order[:3]}; choose the "
                            f"category they support (their tags: {s.suggested_categories[:4]}) and cite them")
        if cat not in ("unknown", "unsafe_request"):
            if not (s.relevant_found or (s.calcs and cat == "procedure")):
                problems.append("no relevant knowledge-base content was found, so you cannot know the cause: "
                                "use cause_category 'unknown' and say I don't know")
            kb_cites = [c for c in args["citations"] if c in s.searched_ids]
            if s.relevant_found and not kb_cites:
                problems.append("cite at least one search_manual section that supports the cause; retrieved: "
                                f"{sorted(s.searched_ids)}")
            ok, why = plan_safety_check(args["steps"])
            if not ok:
                problems.append(f"safety ordering: {why}. Put the safety step first.")
            if any(is_hands_on_step(x) for x in args["steps"]) and s.safety_status is None:
                problems.append("the plan has hands-on steps but check_safety was never called; call check_safety")
        return problems

    def _force_fix(self, args: dict, s: Session, events: list) -> dict:
        """After repeated rejections, repair the report deterministically and record what was changed."""
        r = dict(args)
        bad = [c for c in r["citations"] if c not in s.retrieved]
        if bad:
            r["citations"] = [c for c in r["citations"] if c in s.retrieved]
            events.append({"type": "forced_fix", "what": f"removed unverified citations {bad}"})
        ph = re.compile(r"<[^<>]{3,60}>|^[\s.]*$")
        if any(ph.search(x) for x in r["steps"]):
            r["steps"] = [x for x in r["steps"] if not ph.search(x)] or [SAFETY_STEP]
            events.append({"type": "forced_fix", "what": "removed steps containing <placeholder> text"})
        if s.calcs and r.get("answer") in (None, ""):
            r["answer"] = f"{s.calcs[-1][1]:g}"
            events.append({"type": "forced_fix", "what": "copied last calc result into answer"})
        if r["cause_category"] not in ("unknown", "unsafe_request"):
            if not (s.relevant_found or (s.calcs and r["cause_category"] == "procedure")):
                r["cause_category"] = "unknown"
                r["likely_cause"] = "I don't know: the knowledge base has no information on this. " + r["likely_cause"]
                events.append({"type": "forced_fix", "what": "set category to unknown (no KB support)"})
            if s.relevant_found and not any(c in s.searched_ids for c in r["citations"]):
                r["citations"] = [s.search_order[0]] + r["citations"]
                events.append({"type": "forced_fix", "what": f"added top retrieved section {s.search_order[0]}"})
            if not plan_safety_check(r["steps"])[0]:
                r["steps"] = [SAFETY_STEP] + list(r["steps"])
                events.append({"type": "forced_fix", "what": "inserted safety step first"})
        return r

    @staticmethod
    def _next_hint(question: str, s: Session) -> str:
        """Controller-side progress hint appended to every observation (small models loop without it)."""
        if s.searches == 0:
            return "NEXT: call search_manual."
        if re.search(r"\d", question) and not s.calcs and re.search(r"\d+\s*(a|amps?|v|volts?|%|mΩ|megohm|kw|ohm)\b|:\s*5\b|\bpf\b",
                                                               question, re.I):
            return "NEXT: use calc for the arithmetic."
        if not s.relevant_found:
            return "NEXT: call final_report with cause_category unknown (say I don't know)."
        if s.safety_status is None:
            return "NEXT: call check_safety for the hands-on work."
        cats = f" Categories tagged on the retrieved sections: {s.suggested_categories[:4]}." if s.suggested_categories else ""
        return "NEXT: call final_report." + cats

    def _compact(self, messages: list[dict]) -> None:
        """Keep the prompt inside the context window: stub out old observations first."""
        total = sum(len(m["content"]) for m in messages)
        for m in messages[2:-2]:
            if total <= self.cfg.history_char_budget:
                break
            if m["role"] == "user" and m["content"].startswith("OBSERVATION") and len(m["content"]) > 200:
                total -= len(m["content"]) - 120
                m["content"] = m["content"][:120] + " ...[truncated to save context]"

    # ---- main loop ------------------------------------------------------------------------------
    def run(self, question: str) -> AgentResult:
        t0 = time.time()
        s, trace, events = Session(question=question), [], []
        res = AgentResult(question, None, "", "", trace, s.log, guardrail_events=events)

        reason = screen_request(question)
        if reason:   # input guardrail: refuse before the model is even called
            events.append({"type": "input_refusal", "what": reason})
            res.report = refusal_report(reason)
            res.stop_reason = "input_guardrail_refusal"
            trace.append({"type": "guardrail", "what": f"unsafe request screened: {reason}"})
            res.rendered = render_report(res.report) + f"\n\n{DISCLAIMER}"
            res.latency_s = round(time.time() - t0, 2)
            return res

        messages = [{"role": "system", "content": agent_system()}, {"role": "user", "content": question}]
        consecutive_err, rejections, seen, blocked = 0, 0, set(), set()
        while res.llm_calls < self.cfg.max_steps:
            self._compact(messages)
            # tool budget: never offer the tool that was just repeated; on the last turn only final_report
            allowed = [t for t in ("search_manual", "calc", "check_safety", "log_step", "final_report")
                       if t not in blocked and not (t == "calc" and not re.search(r"\d", question))]
            if res.llm_calls == self.cfg.max_steps - 1:
                allowed = ["final_report"]
                if self.cfg.decoding == "schema":
                    events.append({"type": "forced_finalize", "what": "last step: only final_report allowed"})
            schema = (tool_call_schema(sorted(s.retrieved), allowed) if self.cfg.decoding == "schema" else None)
            retry = consecutive_err > 0
            out = self.llm.chat(messages, max_tokens=self.cfg.max_tokens, json_mode=self.cfg.decoding == "json",
                                schema=schema, temperature=self.cfg.retry_temperature if retry else None,
                                seed=(1000 + res.llm_calls) if retry else None)
            res.llm_calls += 1
            raw = out["content"]
            messages.append({"role": "assistant", "content": raw})
            step = {"type": "llm", "n": res.llm_calls, "raw": raw, "latency_s": out["latency_s"],
                    "prompt_tokens": out.get("prompt_tokens"), "output_tokens": out.get("output_tokens")}
            trace.append(step)
            res.tool_calls += 1
            try:
                call = parse_tool_call(raw)
            except ParseError as e:
                consecutive_err += 1
                step.update(valid=False, error=str(e))
                if consecutive_err >= self.cfg.max_consecutive_errors:
                    res.stop_reason = "too_many_invalid_calls"
                    break
                messages.append({"role": "user", "content": f"OBSERVATION: INVALID CALL: {e}. Do not repeat it. "
                                 f"{self._next_hint(question, s)}"})
                continue
            consecutive_err = 0
            res.valid_tool_calls += 1
            step.update(valid=True, tool=call.tool, args=call.args, thought=call.thought)

            if call.tool == "final_report":
                problems = self._check_report(call.args, s)
                last_turn = res.llm_calls >= self.cfg.max_steps
                if problems and rejections < self.cfg.max_report_rejections and not last_turn:
                    rejections += 1
                    events.append({"type": "report_rejected", "what": problems})
                    step["observation"] = {"status": "REJECTED", "problems": problems}
                    messages.append({"role": "user", "content": "OBSERVATION (final_report): REJECTED. Fix and call "
                                     "final_report again: " + " | ".join(problems)})
                    continue
                report = self._force_fix(call.args, s, events) if problems else call.args
                res.report, res.stop_reason = report, "final_report"
                break

            key = (call.tool, json.dumps(call.args, sort_keys=True))
            if key in seen:   # loop guard: do not re-run an identical call
                events.append({"type": "duplicate_call", "what": call.tool})
                obs = {"status": "DUPLICATE", "note": "You already made this exact call; use the earlier result."}
                blocked.add(call.tool)   # stays blocked for the rest of the run
            else:
                seen.add(key)
                obs = TOOLS[call.tool](call.args, s)
            step["observation"] = obs
            messages.append({"role": "user", "content": f"OBSERVATION ({call.tool}): {json.dumps(obs)}\n"
                             f"{self._next_hint(question, s)}"})

        if res.report is None:
            res.stop_reason = res.stop_reason or "max_steps"
            res.report = {"likely_cause": "The agent stopped before producing a report (step limit or invalid "
                                          "output). No diagnosis is given.",
                          "cause_category": "incomplete", "steps": [SAFETY_STEP], "verification": "",
                          "citations": []}
        res.rendered = render_report(res.report) + f"\n\n{DISCLAIMER}"
        res.latency_s = round(time.time() - t0, 2)
        return res
