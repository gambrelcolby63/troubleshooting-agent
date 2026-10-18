"""Tool implementations. Each tool takes validated args + the session state and returns an observation dict."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import kb
from .calc import CalcError, safe_eval
from .safety import is_hands_on_step, safety_requirements

# Relevance gate, calibrated on dev/ad-hoc queries that are NOT in the eval set (docs/development_notes.md).
MIN_SCORE = 2.5          # floor for any hit
MIN_COVERAGE = 0.5       # short keyword queries: most query terms must be in the section ...
STRONG_SCORE = 8.0       # ... long natural-language questions: a strong BM25 match is enough
SNIPPET_CHARS = 420


@dataclass
class Session:
    retrieved: set = field(default_factory=set)        # section ids the agent has actually seen
    relevant_found: bool = False                        # did any search return relevant KB content?
    safety_status: str | None = None                    # last check_safety status
    log: list = field(default_factory=list)             # structured troubleshooting log (log_step)
    calcs: list = field(default_factory=list)
    searches: int = 0
    suggested_categories: list = field(default_factory=list)   # category tags of retrieved sections, best first
    question: str = ""                                  # the user's original question (for retrieval)
    searched_ids: set = field(default_factory=set)      # ids returned by search_manual specifically
    search_order: list = field(default_factory=list)    # in retrieval order (best first)


def coverage(query: str, section: kb.Section) -> float:
    """IDF-weighted fraction of query terms present in the section."""
    ix = kb.index()
    q = set(kb.tokenize(query))
    if not q:
        return 0.0
    doc = set(kb.tokenize(f"{section.doc_title} {section.title} {section.text}"))
    tot = sum(ix.idf.get(t, 3.0) for t in q)          # unseen terms count as rare (important) words
    return sum(ix.idf.get(t, 3.0) for t in q if t in doc) / tot


def search_manual(args: dict, s: Session) -> dict:
    """BM25 over KB sections. The model's query is merged with a search on the user's original question
    (small models often paraphrase away the key symptom words). Results must pass score + coverage gates."""
    q = args["query"]
    s.searches += 1
    cands = [(sec, sc, q) for sec, sc in kb.index().search(q, k=3)]
    if s.question:
        cands += [(sec, sc, s.question) for sec, sc in kb.index().search(s.question, k=3)]
    seen, hits = set(), []
    for sec, sc, src in sorted(cands, key=lambda x: -x[1]):
        if sec.id not in seen and sc >= MIN_SCORE and (sc >= STRONG_SCORE or coverage(src, sec) >= MIN_COVERAGE):
            seen.add(sec.id)
            hits.append((sec, sc))
    results = []
    for sec, score in hits[:3]:
        if True:
            results.append({"id": sec.id, "title": f"{sec.doc_title} / {sec.title}", "score": round(score, 1),
                            "categories": list(sec.categories),
                            "text": sec.text[:SNIPPET_CHARS] + ("..." if len(sec.text) > SNIPPET_CHARS else "")})
            s.retrieved.add(sec.id)
            for c in sec.categories:
                if c not in s.suggested_categories:
                    s.suggested_categories.append(c)
            if sec.id not in s.searched_ids:
                s.searched_ids.add(sec.id)
                s.search_order.append(sec.id)
    if results:
        s.relevant_found = True
        return {"status": "ok", "results": results}
    return {"status": "NO_RELEVANT_RESULTS",
            "note": "The knowledge base has nothing relevant for this query. If nothing relevant is found, "
                    "report cause_category 'unknown' and say you don't know."}


def calc(args: dict, s: Session) -> dict:
    try:
        val = safe_eval(args["expression"])
    except CalcError as e:
        return {"status": "error", "error": str(e),
                "hint": "use numbers, + - * / ** ( ), sqrt(), pct_error(measured, expected), "
                        "ct_primary(600, 5, i_sec), p3(volts, amps, pf), ohms_r(v, i)"}
    s.calcs.append((args["expression"], val))
    return {"status": "ok", "expression": args["expression"], "result": round(val, 6)}


def check_safety(args: dict, s: Session) -> dict:
    req = safety_requirements(args["task"])
    s.safety_status = req["status"]
    s.retrieved.update(req["citations"])
    return req


def log_step(args: dict, s: Session) -> dict:
    hands_on = args["hands_on"] or is_hands_on_step(args["step"])
    if hands_on and s.safety_status != "CLEARED_AFTER_ESWC":
        return {"status": "REJECTED", "error": "hands-on step logged before check_safety cleared it. "
                                                "Call check_safety for this task first."}
    entry = {"n": len(s.log) + 1, "step": args["step"], "hands_on": hands_on, "finding": args.get("finding", "")}
    s.log.append(entry)
    return {"status": "logged", "entry": entry}


TOOLS = {"search_manual": search_manual, "calc": calc, "check_safety": check_safety, "log_step": log_step}
