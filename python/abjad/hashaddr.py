"""Deterministic abjad hash addressing, and addresses as first-class functions.

An address is built from four hand-computable components:

    J   the concatenated abjad total of the node's surface form
    D   the expansion depth at which the node sits
    P   the positional offset path inside its parent (e.g. "3.1.0")
    S   the orthographic state bit (waqf | wasl) -- see states.py

The canonical key is  ``J<value>/D<depth>/P<path>/S<state>``.  Because it is a
pure function of those four numbers it can be recomputed from the node alone,
so a dict keyed on it gives average-case O(1) retrieval with no search.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

from .letters import (ALPHABET_SIZE, abjad, digital_root, modulo_letter,
                      to_abjad_numeral)

STATE_BIT = {"waqf": 0, "wasl": 1}


@dataclass(frozen=True)
class HashAddress:
    """A hash address that is also a callable transformation."""
    value: int
    depth: int
    path: str
    state: str = "waqf"

    # --- addressing -------------------------------------------------------
    @property
    def key(self) -> str:
        return f"J{self.value}/D{self.depth}/P{self.path}/S{STATE_BIT[self.state]}"

    @property
    def numeral(self) -> str:
        """The address written in abjad numerals, as a scribe would."""
        return to_abjad_numeral(self.value)

    @property
    def digital_root(self) -> int:
        return digital_root(self.value)

    @property
    def ring(self) -> int:
        """Position on the 28-letter ring: value mod 28, 1-based."""
        return ((self.value - 1) % ALPHABET_SIZE) + 1 if self.value else 1

    @property
    def ring_letter(self) -> str:
        return modulo_letter(self.value)

    @property
    def bucket(self) -> str:
        """Constellation container id -- the O(1) context-jump handle."""
        return f"C{self.digital_root}.{self.ring}"

    # --- first-class function --------------------------------------------
    @property
    def opcode(self) -> str:
        """Which bootloader operation this address executes.

        The primordial pairs آب/جد/هو/زح sum to 3, 7, 11, 15 -- an arithmetic
        progression of stride 4.  Reducing the address modulo 4 therefore
        selects one of exactly four inherited transformations.
        """
        return OPS_ORDER[self.value % 4]

    def __call__(self, graph, nid: str):
        """Execute the address against *graph*, returning the reached node."""
        return OPS[self.opcode](graph, nid, self)

    def __str__(self) -> str:                       # pragma: no cover
        return self.key

    @staticmethod
    def of(text: str, depth: int = 0, path: str = "0",
           state: str = "waqf") -> "HashAddress":
        return HashAddress(abjad(text, ta_state=state), depth, path, state)

    @staticmethod
    def parse(key: str) -> "HashAddress":
        try:
            j, d, p, s = key.split("/")
            return HashAddress(int(j[1:]), int(d[1:]), p[1:],
                               "waqf" if s[1:] == "0" else "wasl")
        except Exception as exc:                    # pragma: no cover
            raise ValueError(f"malformed address {key!r}") from exc


# --- the four inherited operations (Task 2.2 bootloader) -------------------

def _op_parent(graph, nid, addr):
    """آب == 1+2 == 3 == ج  -> ascend one level."""
    n = graph.nodes[nid]
    return graph.nodes.get(n.parent) if n.parent else None


def _op_grandparent(graph, nid, addr):
    """جد == 3+4 == 7 == ز  -> ascend two levels."""
    n = graph.nodes[nid]
    p = graph.nodes.get(n.parent) if n.parent else None
    return graph.nodes.get(p.parent) if p and p.parent else None


def _op_identity(graph, nid, addr):
    """هو == 5+6 == 11 == يا -> stay; the node is what it is."""
    return graph.nodes.get(nid)


def _op_shift(graph, nid, addr):
    """زح == 7+8 == 15 == يه -> displace to the next node in the container."""
    n = graph.nodes[nid]
    members = graph.container(n.address.bucket)
    if not members:
        return None
    i = members.index(nid) if nid in members else -1
    return graph.nodes[members[(i + 1) % len(members)]]


OPS: Dict[str, Callable] = {
    "PARENT": _op_parent,
    "GRANDPARENT": _op_grandparent,
    "IDENTITY": _op_identity,
    "SHIFT": _op_shift,
}
#: selected by (address value mod 4)
OPS_ORDER = ["IDENTITY", "PARENT", "GRANDPARENT", "SHIFT"]

#: the primordial bootloader pairs: word, letters, sum, opcode, gloss
BOOTLOADER = [
    ("آب", ["ا", "ب"], 3, "PARENT", "الأب / parent"),
    ("جد", ["ج", "د"], 7, "GRANDPARENT", "الجد / grandparent"),
    ("هو", ["ه", "و"], 11, "IDENTITY", "هو / identity"),
    ("زح", ["ز", "ح"], 15, "SHIFT", "الزحزحة / displacement"),
]
