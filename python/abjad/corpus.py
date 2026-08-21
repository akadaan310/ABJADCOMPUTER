"""Load al-Muqaddimah al-Jazariyyah and analyse it line by line."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .graphtree import TreeGraph
from .hashaddr import HashAddress
from .letters import (abjad, breakdown, digital_root, modulo_letter, NAME,
                      normalise, strip_diacritics, to_abjad_numeral)
from .states import STRIDE, state_words

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data", "jazariyyah.json")

ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"


def arabic_number(n: int) -> str:
    return "".join(ARABIC_DIGITS[int(d)] for d in str(n))


OPCODE_AR = {"PARENT": "أَبٌ", "GRANDPARENT": "جَدٌّ",
             "IDENTITY": "هُوَ", "SHIFT": "زَحْ"}
OPCODE_EN = {"PARENT": "ascend one level",
             "GRANDPARENT": "ascend two levels",
             "IDENTITY": "hold position",
             "SHIFT": "displace to next container member"}


@dataclass
class LineAnalysis:
    n: int
    section: str
    sadr: str
    ajuz: str
    sadr_value: int
    ajuz_value: int
    total: int
    total_wasl: int
    dr: int
    ring: int
    ring_letter: str
    numeral: str
    address: HashAddress
    ta_words: List[str] = field(default_factory=list)
    ta_bits: int = 0
    bridge_sadr: str = ""
    bridge_ajuz: str = ""

    @property
    def key(self) -> str:
        return self.address.key

    @property
    def opcode(self) -> str:
        return self.address.opcode

    @property
    def ta_delta(self) -> int:
        return self.total_wasl - self.total

    def to_dict(self) -> dict:
        return {"n": self.n, "section": self.section, "sadr": self.sadr,
                "ajuz": self.ajuz, "sadr_value": self.sadr_value,
                "ajuz_value": self.ajuz_value, "total": self.total,
                "total_wasl": self.total_wasl, "dr": self.dr, "ring": self.ring,
                "ring_letter": self.ring_letter, "numeral": self.numeral,
                "key": self.key, "opcode": self.opcode,
                "ta_words": self.ta_words, "ta_bits": self.ta_bits,
                "bridge_sadr": self.bridge_sadr, "bridge_ajuz": self.bridge_ajuz}


def make_bridge(a: LineAnalysis) -> tuple:
    """Deterministically synthesise the interleaved بيت أبجدي for a line.

    Both hemistichs are a pure function of the line's own numbers, so the
    bridge can be recomputed by hand from the arithmetic column alone.
    Rhyme is fixed on ـَرْ throughout, echoing line 9's ``مَنِ اخْتَبَرْ``.
    """
    name = NAME[a.ring_letter]
    sadr = (f"جُمْلَتُهُ {arabic_number(a.total)} وَجَذْرُهُ "
            f"{arabic_number(a.dr)} ظَهَرْ")
    ajuz = (f"وَبَابُهُ {name} {OPCODE_AR[a.opcode]} لِمَنِ اعْتَبَرْ")
    return sadr, ajuz


class Jazariyyah:
    """The corpus, its arithmetic, and the graph-tree built over it."""

    def __init__(self, path: str = _DATA) -> None:
        with open(path, encoding="utf-8") as f:
            self.raw = json.load(f)
        self.meta = {k: v for k, v in self.raw.items() if k != "lines"}
        self.lines: List[LineAnalysis] = [self._analyse(r)
                                          for r in self.raw["lines"]]
        for a in self.lines:
            a.bridge_sadr, a.bridge_ajuz = make_bridge(a)
        self._graph: Optional[TreeGraph] = None

    # --- analysis ---------------------------------------------------------
    @staticmethod
    def _analyse(row: dict) -> LineAnalysis:
        sadr, ajuz = row["sadr"], row["ajuz"]
        whole = sadr + " " + ajuz
        total = abjad(whole, ta_state="waqf")
        tw = [s.word for s in state_words(whole)]
        addr = HashAddress(total, 0, str(row["n"]), "waqf")
        return LineAnalysis(
            n=row["n"], section=row["section"], sadr=sadr, ajuz=ajuz,
            sadr_value=abjad(sadr), ajuz_value=abjad(ajuz),
            total=total, total_wasl=abjad(whole, ta_state="wasl"),
            dr=digital_root(total), ring=addr.ring,
            ring_letter=addr.ring_letter, numeral=to_abjad_numeral(total),
            address=addr, ta_words=tw, ta_bits=len(tw))

    def line(self, n: int) -> LineAnalysis:
        return self.lines[n - 1]

    @property
    def authorial_count(self) -> int:
        return self.meta["authorial_count"]

    @property
    def interpolated(self) -> List[LineAnalysis]:
        return [self.line(n) for n in self.meta["interpolated_lines"]]

    def sections(self) -> Dict[str, List[LineAnalysis]]:
        out: Dict[str, List[LineAnalysis]] = {}
        for a in self.lines:
            out.setdefault(a.section, []).append(a)
        return out

    def find(self, needle: str) -> List[LineAnalysis]:
        n = normalise(needle)
        return [a for a in self.lines
                if n and n in normalise(a.sadr + " " + a.ajuz)]

    def totals(self) -> dict:
        vals = [a.total for a in self.lines]
        return {"sum": sum(vals), "min": min(vals), "max": max(vals),
                "mean": sum(vals) // len(vals),
                "argmin": vals.index(min(vals)) + 1,
                "argmax": vals.index(max(vals)) + 1}

    # --- graph-tree -------------------------------------------------------
    def graph(self, expand_depth: int = 0) -> TreeGraph:
        if self._graph is not None:
            return self._graph
        g = TreeGraph()
        root = g.add(self.meta["work"], "corpus")
        secs: Dict[str, str] = {}
        for a in self.lines:
            if a.section not in secs:
                secs[a.section] = g.add(a.section, "section",
                                        parent=root.nid).nid
            ln = g.add(a.sadr + " " + a.ajuz, "line", parent=secs[a.section],
                       path=str(a.n),
                       meta={"n": a.n, "section": a.section, "dr": a.dr,
                             "ta_bits": a.ta_bits})
            for half, txt in (("sadr", a.sadr), ("ajuz", a.ajuz)):
                h = g.add(txt, "hemistich", parent=ln.nid, path=f"{a.n}.{half}",
                          meta={"half": half})
                for i, w in enumerate(strip_diacritics(txt).split()):
                    if normalise(w):
                        g.add(w, "word", parent=h.nid, path=f"{a.n}.{half}.{i}")
        if expand_depth:
            for nid in [n.nid for n in g.nodes.values() if n.kind == "word"]:
                g.graft_expansion(nid, expand_depth)
        self._graph = g
        return g
