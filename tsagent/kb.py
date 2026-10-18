"""Knowledge base: markdown docs split into numbered sections + a small BM25 index (pure Python, no deps).

Section ids look like ``breaker_trip_circuit:2`` (doc id = file stem, number = "## N." heading).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

KB_DIR = Path(__file__).resolve().parent.parent / "kb"
_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = set("""a an and are as at be by can do does for from has have how if in into is it its of on or that the
then this to was what when which while will with without not no you your i my me we our should""".split())
# a few domain synonyms so short user phrasings hit the right sections
_SYN = {"trips": "trip", "tripping": "trip", "tripped": "trip", "breakers": "breaker", "megger": "insulation",
        "pt": "vt", "pts": "vt", "cts": "ct", "relays": "relay", "batteries": "battery", "motors": "motor",
        "loto": "lockout", "lockout": "lockout", "starter": "starter", "contactor": "starter", "hums": "hum",
        "humming": "hum", "fuses": "fuse", "volts": "voltage", "amps": "current", "ohms": "resistance"}


def tokenize(text: str) -> list[str]:
    toks = [_SYN.get(t, t) for t in _TOKEN.findall(text.lower())]
    return [t for t in toks if t not in _STOP and not t.isdigit()]   # bare numbers carry no topic signal


@dataclass
class Section:
    id: str          # e.g. "breaker_trip_circuit:2"
    doc_id: str      # e.g. "breaker_trip_circuit"
    doc_title: str
    title: str
    text: str
    categories: tuple = ()   # fault-category tags from kb/_section_categories.json


def load_sections(kb_dir: Path = KB_DIR) -> list[Section]:
    import json
    tag_file = Path(kb_dir) / "_section_categories.json"
    tags = json.loads(tag_file.read_text()) if tag_file.exists() else {}
    sections = []
    for path in sorted(Path(kb_dir).glob("*.md")):
        raw = path.read_text()
        doc_title = re.search(r"^# (.+)$", raw, re.M).group(1).strip()
        for m in re.finditer(r"^## (\d+)\. (.+?)\n(.*?)(?=^## |\Z)", raw, re.M | re.S):
            sid = f"{path.stem}:{m.group(1)}"
            sections.append(Section(sid, path.stem, doc_title, m.group(2).strip(), m.group(3).strip(),
                                    tuple(tags.get(sid, ()))))
    return sections


class BM25:
    def __init__(self, sections: list[Section], k1: float = 1.4, b: float = 0.75):
        self.sections, self.k1, self.b = sections, k1, b
        # title + doc title are included (and title doubled) so headings carry weight
        self.docs = [tokenize(f"{s.doc_title} {s.title} {s.title} {s.text}") for s in sections]
        self.avgdl = sum(map(len, self.docs)) / max(1, len(self.docs))
        df: dict[str, int] = {}
        for d in self.docs:
            for t in set(d):
                df[t] = df.get(t, 0) + 1
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def search(self, query: str, k: int = 3) -> list[tuple[Section, float]]:
        q = tokenize(query)
        scores = []
        for s, d in zip(self.sections, self.docs):
            tf: dict[str, int] = {}
            for t in d:
                tf[t] = tf.get(t, 0) + 1
            sc = 0.0
            for t in set(q):
                if t in tf:
                    f = tf[t]
                    sc += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(d) / self.avgdl))
            scores.append((s, sc))
        scores.sort(key=lambda x: -x[1])
        return [x for x in scores[:k] if x[1] > 0]


_INDEX: BM25 | None = None


def index() -> BM25:
    global _INDEX
    if _INDEX is None:
        _INDEX = BM25(load_sections())
    return _INDEX


def catalog() -> list[tuple[str, str]]:
    """(doc_id, title) for every doc: shown to both baseline and agent."""
    seen = {}
    for s in index().sections:
        seen.setdefault(s.doc_id, s.doc_title)
    return list(seen.items())


def get_section(section_id: str) -> Section | None:
    return next((s for s in index().sections if s.id == section_id), None)
