"""The graph-tree hybrid: local branching (tree) + global addressing (stars).

Two link systems coexist over one node set.

*Tree edges*  -- parent / child / sibling, produced by textual containment and
by abjad letter expansion.  These are stored explicitly: a node knows its
parent id and its children ids.

*Graph edges* -- "constellations".  Any two nodes whose addresses agree on a
modulo/abjad equivalence belong to the same container.  Membership is stored
once per container instead of materialising every pair, so a container of *k*
nodes costs O(k) storage rather than O(k^2) while still answering "give me
everything equivalent to this node" in one dict hit.  A jump between any two
members is therefore one hop through the container handle, and the container
behaves as a clique without paying clique storage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from .expand import expand_letter
from .hashaddr import HashAddress
from .letters import abjad, digital_root, normalise, VALUE


@dataclass
class Node:
    nid: str
    label: str                       # surface Arabic text
    kind: str                        # corpus|line|hemistich|word|letter|expansion
    address: HashAddress
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    @property
    def value(self) -> int:
        return self.address.value

    def to_dict(self) -> dict:
        return {"nid": self.nid, "label": self.label, "kind": self.kind,
                "key": self.address.key, "value": self.value,
                "dr": self.address.digital_root, "ring": self.address.ring,
                "bucket": self.address.bucket, "opcode": self.address.opcode,
                "parent": self.parent, "children": self.children,
                "meta": self.meta}


class TreeGraph:
    """Containerised fully-connected graph laid over a hierarchical tree."""

    def __init__(self) -> None:
        self.nodes: Dict[str, Node] = {}
        self.roots: List[str] = []
        # constellation indices -- each is  handle -> [nid, ...]
        self.by_bucket: Dict[str, List[str]] = {}
        self.by_value: Dict[int, List[str]] = {}
        self.by_dr: Dict[int, List[str]] = {}
        self.by_ring: Dict[int, List[str]] = {}
        self.by_surface: Dict[str, List[str]] = {}
        self._seq = 0

    # --- construction -----------------------------------------------------
    def add(self, label: str, kind: str, *, parent: Optional[str] = None,
            depth: int = 0, path: str = "0", state: str = "waqf",
            meta: Optional[dict] = None) -> Node:
        addr = HashAddress.of(label, depth, path, state)
        self._seq += 1
        nid = f"{kind[0].upper()}{self._seq}"
        node = Node(nid, label, kind, addr, parent, [], dict(meta or {}))
        self.nodes[nid] = node
        if parent is not None:
            self.nodes[parent].children.append(nid)
        else:
            self.roots.append(nid)
        self._index(node)
        return node

    def _index(self, n: Node) -> None:
        a = n.address
        self.by_bucket.setdefault(a.bucket, []).append(n.nid)
        self.by_value.setdefault(a.value, []).append(n.nid)
        self.by_dr.setdefault(a.digital_root, []).append(n.nid)
        self.by_ring.setdefault(a.ring, []).append(n.nid)
        self.by_surface.setdefault(normalise(n.label), []).append(n.nid)

    # --- O(1) retrieval ---------------------------------------------------
    def container(self, bucket: str) -> List[str]:
        """All nodes sharing a constellation container -- one dict hit."""
        return self.by_bucket.get(bucket, [])

    def by_key(self, key: str) -> Optional[Node]:
        """Resolve a canonical hash address to its node, O(1) average."""
        want = HashAddress.parse(key)
        for nid in self.by_value.get(want.value, []):
            if self.nodes[nid].address == want:
                return self.nodes[nid]
        return None

    def jump(self, nid: str, relation: str = "bucket") -> List[Node]:
        """Instantaneous context jump across the corpus."""
        a = self.nodes[nid].address
        table = {"bucket": (self.by_bucket, a.bucket),
                 "value": (self.by_value, a.value),
                 "dr": (self.by_dr, a.digital_root),
                 "ring": (self.by_ring, a.ring)}
        if relation not in table:
            raise KeyError(f"unknown relation {relation!r}")
        idx, handle = table[relation]
        return [self.nodes[i] for i in idx.get(handle, []) if i != nid]

    def execute(self, nid: str, key: Optional[str] = None) -> Optional[Node]:
        """Run a hash address as a function against a node."""
        addr = HashAddress.parse(key) if key else self.nodes[nid].address
        return addr(self, nid)

    # --- tree helpers -----------------------------------------------------
    def siblings(self, nid: str) -> List[Node]:
        n = self.nodes[nid]
        if n.parent is None:
            return [self.nodes[i] for i in self.roots if i != nid]
        return [self.nodes[i] for i in self.nodes[n.parent].children if i != nid]

    def path_to_root(self, nid: str) -> List[Node]:
        out, cur = [], self.nodes.get(nid)
        while cur:
            out.append(cur)
            cur = self.nodes.get(cur.parent) if cur.parent else None
        return out

    def descendants(self, nid: str) -> Iterable[Node]:
        stack = [nid]
        while stack:
            cur = self.nodes[stack.pop()]
            yield cur
            stack.extend(reversed(cur.children))

    # --- expansion grafting ----------------------------------------------
    def graft_expansion(self, nid: str, depth: int = 1,
                        variant: str = "long") -> List[Node]:
        """Attach the abjad letter-expansion tree beneath a word node."""
        host = self.nodes[nid]
        made = []
        for i, ch in enumerate(normalise(host.label)):
            exp = expand_letter(ch, depth, variant=variant, _path=str(i))
            made.extend(self._graft(exp, nid))
        return made

    def _graft(self, exp, parent: str) -> List[Node]:
        n = self.add(exp.surface(), "expansion", parent=parent,
                     depth=exp.depth, path=exp.path,
                     meta={"head": exp.ch, "sexpr": exp.sexpr()})
        made = [n]
        for kid in exp.children:
            made.extend(self._graft(kid, n.nid))
        return made

    # --- reporting --------------------------------------------------------
    def stats(self) -> dict:
        kinds: Dict[str, int] = {}
        for n in self.nodes.values():
            kinds[n.kind] = kinds.get(n.kind, 0) + 1
        multi = {k: v for k, v in self.by_bucket.items() if len(v) > 1}
        implied = sum(len(v) * (len(v) - 1) // 2 for v in self.by_bucket.values())
        return {"nodes": len(self.nodes), "kinds": kinds,
                "containers": len(self.by_bucket),
                "populated_containers": len(multi),
                "largest_container": max((len(v) for v in self.by_bucket.values()),
                                         default=0),
                "implied_graph_edges": implied,
                "stored_membership_cells": sum(len(v) for v in self.by_bucket.values())}
