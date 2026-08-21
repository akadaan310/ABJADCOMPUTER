"""The قاف وزاي cipher: resolving 107 against the transmitted 109 lines."""
from __future__ import annotations

from typing import Dict, List

from .corpus import Jazariyyah
from .letters import (NAME, VALUE, abjad, breakdown, digital_root,
                      letter_for_value, to_abjad_numeral)


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def qaf_zay() -> Dict:
    """ق + ز == 100 + 7 == 107, read as letter NAMES denoting letters."""
    return {
        "phrase": "قَافٌ وَزَاىٌ",
        "reading": "letter-denoting",
        "letters": [("ق", VALUE["ق"]), ("ز", VALUE["ز"])],
        "total": VALUE["ق"] + VALUE["ز"],
        "word_reading": {
            "قاف": abjad("قاف"), "زاي": abjad("زاي"),
            "total": abjad("قاف") + abjad("زاي"),
        },
    }


def count_109() -> Dict:
    """109 written as a scribe would write it: ق + ط."""
    return {
        "value": 109,
        "numeral": to_abjad_numeral(109),
        "letters": [("ق", VALUE["ق"]), ("ط", VALUE["ط"])],
        "check": VALUE["ق"] + VALUE["ط"],
    }


def transformation() -> Dict:
    """The 107 <-> 109 bridge, every step hand-checkable."""
    a, b = 107, 109
    return {
        "from": a, "to": b, "delta": b - a,
        "delta_letter": letter_for_value(b - a),
        "delta_name": NAME[letter_for_value(b - a)],
        "numeral_from": to_abjad_numeral(a),      # قز
        "numeral_to": to_abjad_numeral(b),        # قط
        "shared_head": "ق",
        "tail_from": ("ز", VALUE["ز"]),
        "tail_to": ("ط", VALUE["ط"]),
        "dr_from": digital_root(a), "dr_to": digital_root(b),
        "dr_from_letter": letter_for_value(digital_root(a)),
        "dr_to_letter": letter_for_value(digital_root(b)),
        "both_prime": is_prime(a) and is_prime(b),
        "twin_primes": is_prime(a) and is_prime(b) and b - a == 2,
    }


def interpolation_keys(J: Jazariyyah) -> List[Dict]:
    """Treat the two surplus lines as operational hash keys."""
    out = []
    for a in J.interpolated:
        out.append({
            "n": a.n, "text": f"{a.sadr} ✽ {a.ajuz}",
            "total": a.total, "numeral": a.numeral, "dr": a.dr,
            "ring": a.ring, "ring_letter": a.ring_letter,
            "key": a.key, "opcode": a.opcode,
            "unlocks": a.total % 109 or 109,
        })
    return out


def resolve(J: Jazariyyah) -> Dict:
    colophon = J.line(J.meta["authorial_count_line"])
    keys = interpolation_keys(J)
    surplus = sum(k["total"] for k in keys)
    return {
        "qaf_zay": qaf_zay(),
        "count_109": count_109(),
        "transformation": transformation(),
        "colophon_ordinal": colophon.n,
        "colophon_text": f"{colophon.sadr} ✽ {colophon.ajuz}",
        "colophon_self_consistent": colophon.n == J.authorial_count,
        "interpolation_keys": keys,
        "surplus_total": surplus,
        "surplus_dr": digital_root(surplus),
        "surplus_numeral": to_abjad_numeral(surplus),
        "apparatus": J.meta.get("recension_apparatus", {}),
    }
