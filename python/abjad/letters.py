"""Abjad alphabet table, orthographic normalisation and scalar valuation.

Zero dependencies.  Every quantity produced here is reproducible with pencil
and paper: a value is a sum of table look-ups, nothing more.
"""
from __future__ import annotations

import json
import os
from typing import Dict, Iterable, List, Tuple

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data", "letters.json")

with open(_DATA, encoding="utf-8") as _f:
    _TABLE = json.load(_f)

LETTERS: List[dict] = _TABLE["letters"]
VALUE: Dict[str, int] = {x["ch"]: x["value"] for x in LETTERS}
NAME: Dict[str, str] = {x["ch"]: x["name"] for x in LETTERS}
ORDER: Dict[str, int] = {x["ch"]: x["order"] for x in LETTERS}
GROUP: Dict[str, str] = {x["ch"]: x["group"] for x in LETTERS}
BY_ORDER: List[str] = [x["ch"] for x in sorted(LETTERS, key=lambda x: x["order"])]
BY_VALUE: Dict[int, str] = {x["value"]: x["ch"] for x in LETTERS}
VARIANTS: Dict[str, Dict[str, str]] = _TABLE["spelling_variants"]

ALPHABET_SIZE = 28
#: value of the whole alphabet, 1..1000 -- the modulus of the "sky"
ALPHABET_SUM = sum(VALUE.values())          # 5995

# --- orthographic normalisation ------------------------------------------
#: Arabic combining marks (harakat, shadda, sukun, quranic annotation).
DIACRITICS = set(
    "ًٌٍَُِّْٕٓٔ"
    "ٖٜٟٗ٘ٙٚٛٝٞـ"
    "ٰۖۗۘۙۚۛۜ۟۠ۡ"
    "ۣۢۤۥۦ۪ۭۧۨ۫۬"
)

#: every hamza carrier collapses onto alif == 1; alif maqsura onto ya == 10.
FOLD = {
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ء": "ا", "ؤ": "ا", "ئ": "ا",
    "ى": "ي", "ﻯ": "ي", "ﻰ": "ي",
}

#: ta marbuta is deliberately NOT folded here -- it is bistable, see states.py
TA_MARBUTA = "ة"


def strip_diacritics(text: str) -> str:
    """Drop every combining mark, leaving the bare rasm (skeleton)."""
    return "".join(c for c in text if c not in DIACRITICS)


def normalise(text: str, *, ta_state: str = "waqf") -> str:
    """Reduce *text* to countable abjad letters.

    ``ta_state`` selects the resolution of ta marbuta:
    ``"waqf"`` (pausal) -> ha == 5, ``"wasl"`` (continuous) -> ta == 400.
    """
    if ta_state not in ("waqf", "wasl"):
        raise ValueError("ta_state must be 'waqf' or 'wasl'")
    out = []
    for ch in strip_diacritics(text):
        ch = FOLD.get(ch, ch)
        if ch == TA_MARBUTA:
            ch = "ه" if ta_state == "waqf" else "ت"
        if ch in VALUE:
            out.append(ch)
    return "".join(out)


def letters_of(text: str, *, ta_state: str = "waqf") -> List[str]:
    return list(normalise(text, ta_state=ta_state))


def abjad(text: str, *, ta_state: str = "waqf") -> int:
    """Total abjad value of *text* -- a plain sum of letter weights."""
    return sum(VALUE[c] for c in normalise(text, ta_state=ta_state))


def breakdown(text: str, *, ta_state: str = "waqf") -> List[Tuple[str, int]]:
    """Per-letter working, so a reader can re-add the column by hand."""
    return [(c, VALUE[c]) for c in normalise(text, ta_state=ta_state)]


def digital_root(n: int) -> int:
    """Repeated digit sum, 1..9 (0 only for 0).  dr(n) == 1+(n-1) mod 9."""
    if n == 0:
        return 0
    n = abs(n)
    return 1 + (n - 1) % 9


def digit_sum(n: int) -> int:
    return sum(int(d) for d in str(abs(n)))


def to_abjad_numeral(n: int) -> str:
    """Write *n* the way a scribe would: greedy descending letter weights.

    109 -> قط  (100 + 9),  111 -> قيا (100+10+1).
    """
    if n <= 0:
        return ""
    out = []
    for v in sorted(VALUE.values(), reverse=True):
        while n >= v:
            out.append(BY_VALUE[v])
            n -= v
    return "".join(out)


def letter_for_value(n: int) -> str:
    """The single letter of weight *n*, or '' if *n* is not a letter weight."""
    return BY_VALUE.get(n, "")


def modulo_letter(n: int, modulus: int = ALPHABET_SIZE) -> str:
    """Map any integer onto the 28-letter ring (1-based)."""
    idx = ((n - 1) % modulus) + 1 if n else 1
    return BY_ORDER[idx - 1]


def spell(ch: str, variant: str = "long") -> str:
    """The spelled-out name of *ch* under a spelling profile."""
    if variant not in ("long", "short"):
        raise ValueError("variant must be 'long' or 'short'")
    if variant == "short" and ch in VARIANTS:
        return VARIANTS[ch]["short"]
    return NAME.get(ch, ch)
