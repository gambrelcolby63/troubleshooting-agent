"""Render an agent trace for humans: terminal text or a self-contained HTML page."""
from __future__ import annotations

import html
import json


def _short(x, n=300):
    s = x if isinstance(x, str) else json.dumps(x)
    return s if len(s) <= n else s[:n] + " ..."


def text_trace(res: dict) -> str:
    out = [f"QUESTION: {res['question']}", ""]
    for t in res["trace"]:
        if t["type"] == "guardrail":
            out.append(f"[guardrail] {t['what']}")
            continue
        head = f"[step {t['n']}] {t['latency_s']:.1f}s"
        if not t.get("valid"):
            out.append(f"{head} INVALID tool call: {t.get('error')}\n    raw: {_short(t['raw'], 200)}")
            continue
        out.append(f"{head} {t['tool']}({_short(t['args'], 220)})")
        if t.get("thought"):
            out.append(f"    thought: {_short(t['thought'], 200)}")
        if "observation" in t:
            obs = t["observation"]
            if isinstance(obs, dict) and obs.get("results"):
                obs = {"status": obs["status"], "results": [f"{r['id']} ({r['title']}, score {r['score']})" for r in obs["results"]]}
            out.append(f"    -> {_short(obs, 300)}")
    for g in res.get("guardrail_events", []):
        if g["type"] != "input_refusal":
            out.append(f"[guardrail] {g['type']}: {_short(g['what'], 250)}")
    out += ["", f"stop: {res['stop_reason']} | llm calls: {res['llm_calls']} | valid tool calls: "
            f"{res['valid_tool_calls']}/{res['tool_calls']} | {res['latency_s']:.1f}s", "", res["rendered"]]
    return "\n".join(out)


def html_trace(res: dict) -> str:
    rows = []
    for t in res["trace"]:
        if t["type"] == "guardrail":
            rows.append(f"<div class='g'>guardrail: {html.escape(t['what'])}</div>")
            continue
        cls = "ok" if t.get("valid") else "bad"
        body = (f"<b>{html.escape(t.get('tool', 'INVALID'))}</b> <code>{html.escape(_short(t.get('args', t['raw']), 600))}</code>"
                + (f"<div class='th'>{html.escape(t.get('thought', ''))}</div>" if t.get("thought") else "")
                + (f"<div class='err'>{html.escape(t['error'])}</div>" if t.get("error") else "")
                + (f"<pre>{html.escape(json.dumps(t['observation'], indent=1)[:1500])}</pre>" if "observation" in t else ""))
        rows.append(f"<div class='step {cls}'><span class='n'>step {t['n']} &middot; {t['latency_s']:.1f}s</span>{body}</div>")
    for g in res.get("guardrail_events", []):
        rows.append(f"<div class='g'>guardrail {html.escape(g['type'])}: {html.escape(_short(g['what'], 400))}</div>")
    return f"""<!doctype html><meta charset=utf-8><title>tsagent trace</title>
<style>body{{font-family:system-ui,sans-serif;max-width:900px;margin:2em auto;color:#222}}
.step{{border-left:4px solid #4C78A8;padding:.4em .8em;margin:.6em 0;background:#f6f8fa}}.bad{{border-color:#d62728}}
.g{{border-left:4px solid #ff7f0e;padding:.4em .8em;margin:.6em 0;background:#fff4e5}}.n{{color:#777;font-size:.85em;margin-right:.6em}}
.th{{color:#555;font-style:italic}}.err{{color:#d62728}}pre{{white-space:pre-wrap;font-size:.8em}}</style>
<h2>Question</h2><p>{html.escape(res['question'])}</p><h2>Trace</h2>{''.join(rows)}
<p><i>stop: {res['stop_reason']} &middot; LLM calls {res['llm_calls']} &middot; valid tool calls {res['valid_tool_calls']}/{res['tool_calls']} &middot; {res['latency_s']:.1f}s</i></p>
<h2>Report</h2><pre>{html.escape(res['rendered'])}</pre>"""
