"""Non-dictionary linguistic synthesis.

A string with no lexical entry is still fully determined *structurally*: its
letters have weights, its weights have a position on the ring, and that
position has neighbours inside the corpus.  This module reads a definition off
that structure alone.

It makes no claim about attested Arabic lexicography.  What it returns is a
formal, reproducible placement of a token inside this corpus, not a dictionary
sense.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .corpus import Jazariyyah
from .expand import expand_word
from .hashaddr import HashAddress
from .letters import (NAME, VALUE, abjad, breakdown, digital_root,
                      modulo_letter, normalise, to_abjad_numeral)
from .makharij import makhraj, makhraj_line, sifat_of, triliteral


@dataclass
class Projection:
    """One of the two readings of a token."""
    name: str
    depth: int
    value: int
    numeral: str
    dr: int
    ring: int
    ring_letter: str
    key: str
    neighbours: List[dict] = field(default_factory=list)


@dataclass
class Synthesis:
    token: str
    letters: List[str]
    working: List[tuple]
    root: List[str]
    root_value: int
    manifest: Projection          # إنسي  -- surface, depth 0
    hidden: Projection            # جنّي  -- expanded, depth 1
    in_lexicon: bool
    definition: str
    articulation: List[dict] = field(default_factory=list)
    attributes: Dict[str, List[str]] = field(default_factory=dict)


def _word_index(J: Jazariyyah) -> List[dict]:
    """Every distinct word of the corpus with its address, cached on J."""
    cached = getattr(J, "_wordidx", None)
    if cached is not None:
        return cached
    g = J.graph()
    seen: Dict[str, dict] = {}
    for n in g.nodes.values():
        if n.kind != "word":
            continue
        surf = normalise(n.label)
        if not surf:
            continue
        line_n = int(str(n.address.path).split(".")[0])
        row = seen.setdefault(surf, {"word": n.label, "surface": surf,
                                     "value": n.value, "dr": n.address.digital_root,
                                     "ring": n.address.ring, "lines": []})
        if line_n not in row["lines"]:
            row["lines"].append(line_n)
    idx = sorted(seen.values(), key=lambda r: r["value"])
    setattr(J, "_wordidx", idx)
    return idx


def _neighbours(J: Jazariyyah, value: int, limit: int = 5) -> List[dict]:
    """Corpus WORDS nearest this address, by absolute abjad distance."""
    idx = _word_index(J)
    rows = sorted(idx, key=lambda r: (abs(r["value"] - value), r["surface"]))[:limit]
    out = []
    for r in rows:
        a = J.line(r["lines"][0])
        out.append({"word": r["word"], "value": r["value"],
                    "distance": r["value"] - value, "dr": r["dr"],
                    "lines": r["lines"], "section": a.section})
    return out


def _cluster(J: Jazariyyah, dr: int, ring: int) -> dict:
    same_dr = [a for a in J.lines if a.dr == dr]
    same_ring = [a for a in J.lines if a.ring == ring]
    both = [a for a in J.lines if a.dr == dr and a.ring == ring]
    secs: Dict[str, int] = {}
    for a in (both or same_dr):
        secs[a.section] = secs.get(a.section, 0) + 1
    dominant = max(secs.items(), key=lambda kv: (kv[1], kv[0]))[0] if secs else "—"
    return {"same_dr": [a.n for a in same_dr], "same_ring": [a.n for a in same_ring],
            "both": [a.n for a in both], "dominant_section": dominant,
            "section_histogram": secs}


def _project(J: Jazariyyah, token: str, depth: int, label: str) -> Projection:
    if depth == 0:
        v = abjad(token)
    else:
        v = sum(e.value for e in expand_word(token, depth))
    addr = HashAddress(v, depth, "0", "waqf")
    return Projection(label, depth, v, to_abjad_numeral(v), addr.digital_root,
                      addr.ring, addr.ring_letter, addr.key,
                      _neighbours(J, v))


def _definition(token: str, root: List[str], manifest: Projection,
                hidden: Projection, cluster: dict, in_lex: bool) -> str:
    r = "".join(root)
    parts = [
        f"«{token}»",
        ("لفظٌ مثبتٌ في المتن" if in_lex else "لفظٌ خارج معجم المتن"),
        f"جذرُه البنيويّ ({r})",
        f"وجملتُه {manifest.value} ({manifest.numeral})",
        f"وجذرُه العدديّ {manifest.dr}",
        f"وموقعُه على الحلقة {manifest.ring} = {NAME[manifest.ring_letter]}.",
        f"وبالبسط تصير جملتُه {hidden.value} فينتقل إلى {NAME[hidden.ring_letter]}.",
        f"وأقربُ ما يجاورُه من المتن بابُ {cluster['dominant_section']}،",
        f"ومخارجُ أصولِه: " + "، ".join(f"{c}: {makhraj(c)}" for c in root) + ".",
    ]
    return " ".join(parts)


def synthesise(J: Jazariyyah, token: str) -> Synthesis:
    letters = list(normalise(token))
    if not letters:
        raise ValueError("token contains no abjad letters")
    root = triliteral(letters)
    manifest = _project(J, token, 0, "إنسي / manifest")
    hidden = _project(J, token, 1, "جنّي / hidden")
    in_lex = bool(J.find(token))
    cluster = _cluster(J, manifest.dr, manifest.ring)
    return Synthesis(
        token=token, letters=letters, working=breakdown(token),
        root=root, root_value=sum(VALUE[c] for c in root),
        manifest=manifest, hidden=hidden, in_lexicon=in_lex,
        definition=_definition(token, root, manifest, hidden, cluster, in_lex),
        articulation=[{"letter": c, "makhraj": makhraj(c),
                       "cited_line": makhraj_line(c)} for c in letters],
        attributes={c: sifat_of(c) for c in letters},
    )
