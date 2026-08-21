"""Orthographic state bits derived from the ta' marbuta / ta' maftuha rule.

Ibn al-Jazari makes the rule an explicit subject of the poem (line 8):

    مِنْ كُلِّ مَقْطُوعٍ وَمَوْصُولٍ بِهَا  /  وَتَاءِ أُنْثَى لَمْ تَكُنْ تُكْتَبْ بِهَا

The feminine ending is genuinely bistable in recitation: stopping on it
(waqf) realises it as ha' == 5, continuing (wasl) realises it as ta' == 400.
One grapheme therefore carries one bit, and the two readings of a word differ
by a constant stride:

    STRIDE = 400 - 5 = 395

A word carrying *k* such graphemes is a k-bit register whose addresses are
spaced 395 apart.  That is what the engine routes on.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .letters import TA_MARBUTA, abjad, normalise, strip_diacritics

TA_HA = 5           # waqf realisation
TA_TA = 400         # wasl realisation
STRIDE = TA_TA - TA_HA      # 395

#: feminine nouns written with an OPEN ta' in the Uthmanic rasm -- the content
#: of the poem's باب التاءات.  Each is the counterpart case of the same bit.
OPEN_TA_RASM = ["رحمت", "نعمت", "لعنت", "امرأت", "معصيت", "شجرت", "سنت",
                "قرت", "جنت", "فطرت", "بقيت", "ابنت", "كلمت"]


@dataclass
class StateWord:
    word: str
    count: int          # how many ta' marbuta graphemes it carries
    waqf: int           # abjad with every ta' marbuta read as ha'  (5)
    wasl: int           # abjad with every ta' marbuta read as ta'  (400)

    @property
    def delta(self) -> int:
        return self.wasl - self.waqf

    @property
    def bits(self) -> int:
        return self.count

    @property
    def register(self) -> List[int]:
        """Every address the word can occupy, low bit first."""
        return [self.waqf + i * STRIDE for i in range(self.count + 1)]


def analyse_word(word: str) -> StateWord:
    bare = strip_diacritics(word)
    return StateWord(word, bare.count(TA_MARBUTA),
                     abjad(word, ta_state="waqf"),
                     abjad(word, ta_state="wasl"))


def state_words(text: str) -> List[StateWord]:
    """Every whitespace-token of *text* that carries a ta' marbuta."""
    out = []
    for tok in strip_diacritics(text).split():
        if TA_MARBUTA in tok:
            out.append(analyse_word(tok))
    return out


def route_bit(word: str) -> int:
    """The routing bit a word contributes: 1 if it is state-bearing."""
    return 1 if TA_MARBUTA in strip_diacritics(word) else 0


def open_ta_pairs() -> List[dict]:
    """The باب التاءات set, each as its closed/open pair of addresses."""
    rows = []
    for open_form in OPEN_TA_RASM:
        closed = open_form[:-1] + TA_MARBUTA          # رحمت -> رحمة
        rows.append({
            "open": open_form,                        # as in the mushaf
            "closed": closed,                         # as in ordinary spelling
            "open_value": abjad(open_form),
            "closed_value": abjad(closed, ta_state="waqf"),
            "delta": abjad(open_form) - abjad(closed, ta_state="waqf"),
        })
    return rows
