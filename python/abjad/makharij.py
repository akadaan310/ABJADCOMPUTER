"""Articulation and attribute table read straight off the poem itself.

Every row cites the line of al-Muqaddimah al-Jazariyyah that states it, so the
table is a transcription of the corpus rather than an outside import.
"""
from __future__ import annotations

from typing import Dict, List

#: letter -> (articulation group, poem line stating it)
MAKHRAJ: Dict[str, tuple] = {
    "ا": ("الجوف", 10), "و": ("الشفتان / الجوف", 19), "ي": ("وسط اللسان / الجوف", 13),
    "ه": ("أقصى الحلق", 11), "ع": ("وسط الحلق", 11), "ح": ("وسط الحلق", 11),
    "غ": ("أدنى الحلق", 12), "خ": ("أدنى الحلق", 12),
    "ق": ("أقصى اللسان", 12), "ك": ("أقصى اللسان أسفل", 13),
    "ج": ("وسط اللسان", 13), "ش": ("وسط اللسان", 13),
    "ض": ("حافة اللسان", 14), "ل": ("أدنى حافة اللسان", 14),
    "ن": ("طرف اللسان", 15), "ر": ("طرف اللسان لظهر", 15),
    "ط": ("طرف اللسان وعليا الثنايا", 16), "د": ("طرف اللسان وعليا الثنايا", 16),
    "ت": ("طرف اللسان وعليا الثنايا", 16),
    "ص": ("الصفير", 17), "ز": ("الصفير", 17), "س": ("الصفير", 17),
    "ظ": ("طرف اللسان وأطراف الثنايا العليا", 18),
    "ذ": ("طرف اللسان وأطراف الثنايا العليا", 18),
    "ث": ("طرف اللسان وأطراف الثنايا العليا", 18),
    "ف": ("بطن الشفة وأطراف الثنايا", 18),
    "ب": ("الشفتان", 19), "م": ("الشفتان", 19),
}

#: attribute -> (member letters, mnemonic as the poem gives it, line)
SIFAT: Dict[str, tuple] = {
    "مهموس":  ("فحثه شخص سكت", 21),
    "شديد":   ("أجد قط بكت", 21),
    "بيني":   ("لن عمر", 22),
    "مستعلٍ": ("خص ضغط قظ", 22),
    "مطبق":   ("صضطظ", 23),
    "مذلق":   ("فر من لب", 23),
    "صفير":   ("صزس", 24),
    "قلقلة":  ("قطب جد", 24),
}

WEAK = set("اوي")
SUN = set("تثدذرزسشصضطظلن")


def makhraj(ch: str) -> str:
    return MAKHRAJ.get(ch, ("غير مصنَّف", 0))[0]


def makhraj_line(ch: str) -> int:
    return MAKHRAJ.get(ch, ("", 0))[1]


def sifat_of(ch: str) -> List[str]:
    """Which of the poem's mnemonic sets a letter belongs to."""
    from .letters import normalise
    out = []
    for name, (mnemonic, _ln) in SIFAT.items():
        if ch in set(normalise(mnemonic)):
            out.append(name)
    return out


def triliteral(letters: List[str]) -> List[str]:
    """Extract a three-consonant root, weak letters shed last.

    Rule (deterministic): drop a leading definite article, then prefer strong
    consonants in order of appearance; if fewer than three remain, re-admit the
    shed weak letters in order until three are held.
    """
    ls = list(letters)
    if len(ls) > 3 and ls[0] == "ا" and ls[1] == "ل":
        ls = ls[2:]
    strong = [c for c in ls if c not in WEAK]
    weak = [c for c in ls if c in WEAK]
    root = strong[:3]
    i = 0
    while len(root) < 3 and i < len(weak):
        root.append(weak[i]); i += 1
    while len(root) < 3 and ls:
        root.append(ls[len(root) % len(ls)])
    return root[:3]
