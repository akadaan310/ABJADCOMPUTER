"""Recursive nested letter expansion (depth processing).

Level 0 : ا                          -> 1
Level 1 : ا -> (ا ل ف)               -> 1 + 30 + 80        = 111
Level 2 : (الف) -> ((الف)(لام)(فاء)) -> 111 + 71 + 82      = 264
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .letters import VALUE, normalise, spell


@dataclass
class Expansion:
    """One node of the expansion tree."""
    ch: str
    depth: int
    value: int                       # abjad total of this sub-tree
    children: List["Expansion"] = field(default_factory=list)
    path: str = ""                   # positional offset, e.g. "0.2.1"

    @property
    def is_leaf(self) -> bool:
        return not self.children

    def surface(self) -> str:
        """The flattened letter string this sub-tree spells out."""
        if self.is_leaf:
            return self.ch
        return "".join(c.surface() for c in self.children)

    def sexpr(self) -> str:
        """First-class-function rendering:  ا(ا(الف)ل(لام)ف(فاء))."""
        if self.is_leaf:
            return self.ch
        return self.ch + "(" + "".join(c.sexpr() for c in self.children) + ")"

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()

    def leaves(self) -> List["Expansion"]:
        return [n for n in self.walk() if n.is_leaf]

    def to_dict(self) -> dict:
        return {"ch": self.ch, "depth": self.depth, "value": self.value,
                "path": self.path, "surface": self.surface(),
                "children": [c.to_dict() for c in self.children]}


def expand_letter(ch: str, depth: int, *, variant: str = "long",
                  _path: str = "0") -> Expansion:
    """Expand *ch* to *depth* levels.  depth 0 == the bare letter."""
    if ch not in VALUE:
        raise KeyError("not an abjad letter: %r" % ch)
    if depth <= 0:
        return Expansion(ch, 0, VALUE[ch], [], _path)
    name = normalise(spell(ch, variant))
    kids = [expand_letter(c, depth - 1, variant=variant, _path=f"{_path}.{i}")
            for i, c in enumerate(name)]
    return Expansion(ch, depth, sum(k.value for k in kids), kids, _path)


def expand_word(word: str, depth: int, *, variant: str = "long",
                ta_state: str = "waqf") -> List[Expansion]:
    letters = normalise(word, ta_state=ta_state)
    return [expand_letter(c, depth, variant=variant, _path=str(i))
            for i, c in enumerate(letters)]


def word_value_at_depth(word: str, depth: int, *, variant: str = "long",
                        ta_state: str = "waqf") -> int:
    return sum(e.value for e in expand_word(word, depth, variant=variant,
                                            ta_state=ta_state))


def depth_series(ch: str, max_depth: int, *, variant: str = "long") -> List[int]:
    """[L0, L1, L2, ...] totals for a single letter."""
    return [expand_letter(ch, d, variant=variant).value
            for d in range(max_depth + 1)]


# --- first-class function evaluation --------------------------------------

class ExprError(ValueError):
    pass


def parse(src: str) -> Expansion:
    """Parse a hash-address expression such as ``آ(آ(الف)ل(لام)ف(فا))``.

    Grammar::

        expr := LETTER [ '(' expr+ ')' ]

    A bare run of letters inside parentheses is a sequence of leaf nodes, so
    ``آ(الف)`` is alif applied to (alif, lam, fa) == 1 + 30 + 80 == 111.
    """
    from .letters import FOLD, strip_diacritics
    src = "".join(FOLD.get(c, c) for c in strip_diacritics(src))
    src = "".join(c for c in src if c in VALUE or c in "()")
    pos = 0

    def peek() -> str:
        return src[pos] if pos < len(src) else ""

    def parse_one(path: str) -> Expansion:
        nonlocal pos
        ch = peek()
        if ch not in VALUE:
            raise ExprError(f"expected a letter at offset {pos}, got {ch!r}")
        pos += 1
        if peek() != "(":
            return Expansion(ch, 0, VALUE[ch], [], path)
        pos += 1                                   # consume '('
        kids: List[Expansion] = []
        while peek() and peek() != ")":
            kids.append(parse_one(f"{path}.{len(kids)}"))
        if peek() != ")":
            raise ExprError("unbalanced '(' -- missing ')'")
        pos += 1                                   # consume ')'
        if not kids:
            raise ExprError(f"empty application {ch}()")
        depth = 1 + max(k.depth for k in kids)
        return Expansion(ch, depth, sum(k.value for k in kids), kids, path)

    node = parse_one("0")
    if pos != len(src):
        raise ExprError(f"trailing input at offset {pos}: {src[pos:]!r}")
    return node


def evaluate(src: str) -> int:
    """Execute a hash address as a function; return its abjad total."""
    return parse(src).value


def trace(src: str) -> List[str]:
    """Human-readable reduction trace of an expression."""
    root = parse(src)
    out = []
    for node in root.walk():
        kind = "leaf " if node.is_leaf else "apply"
        indent = "  " * node.path.count(".")
        rhs = (" + ".join(str(k.value) for k in node.children) + f" = {node.value}"
               if node.children else str(node.value))
        out.append(f"{indent}{kind} {node.ch}@{node.path}  {rhs}")
    return out
