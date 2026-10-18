"""Tiny local web UI (stdlib only):  python -m tsagent.web  ->  http://127.0.0.1:8765
Type a symptom, the agent runs, and the page shows the tool-call trace and the final report."""
from __future__ import annotations

import html
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .agent import Agent
from .llm import OllamaLLM
from .trace_view import html_trace

FORM = """<!doctype html><meta charset=utf-8><title>tsagent</title>
<body style="font-family:system-ui;max-width:900px;margin:2em auto">
<h1>Troubleshooting agent <small style="color:#888">(educational)</small></h1>
<form method=post><textarea name=q rows=3 style="width:100%" placeholder="e.g. breaker trips immediately on close">{q}</textarea>
<button>Run agent</button> <span style="color:#888">runs locally on CPU; expect 20-60 s</span></form>
<p style="color:#a00">Educational only. Follow your site procedures, the manufacturer's instructions and qualified personnel.</p>
{body}</body>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, page: str):
        data = page.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(FORM.format(q="", body=""))

    def do_POST(self):
        n = min(int(self.headers.get("Content-Length", 0)), 4000)
        q = urllib.parse.parse_qs(self.rfile.read(n).decode()).get("q", [""])[0].strip()[:1000]
        body = html_trace(Agent(OllamaLLM(model=os.environ.get("TSAGENT_MODEL", "dolphin3-3b"))).run(q).to_dict()) if q else ""
        self._send(FORM.format(q=html.escape(q), body=body))


def main(host: str = "127.0.0.1", port: int = 8765):
    print(f"tsagent web UI on http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
