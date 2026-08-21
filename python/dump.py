"""Emit a canonical JSON digest of the whole engine state, for cross-checking."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from abjad.corpus import Jazariyyah
from abjad.expand import depth_series
from abjad.hashaddr import BOOTLOADER, HashAddress
from abjad.letters import ALPHABET_SUM, BY_ORDER, VALUE, abjad, to_abjad_numeral
from abjad.states import STRIDE, open_ta_pairs

J = Jazariyyah()
digest = {
    "alphabetSum": ALPHABET_SUM,
    "letters": [{"ch": c, "value": VALUE[c], "series": depth_series(c, 3),
                 "addr": HashAddress(VALUE[c], 0, "0").key,
                 "bucket": HashAddress(VALUE[c], 0, "0").bucket,
                 "opcode": HashAddress(VALUE[c], 0, "0").opcode} for c in BY_ORDER],
    "bootloader": [{"w": w, "sum": s, "num": to_abjad_numeral(s), "op": op}
                   for w, _ls, s, op, _g in BOOTLOADER],
    "stride": STRIDE,
    "taPairs": [{"open": p["open"], "closed": p["closed"],
                 "openValue": p["open_value"], "closedValue": p["closed_value"],
                 "delta": p["delta"]} for p in open_ta_pairs()],
    "lines": [{"n": a.n, "sadr": a.sadr_value, "ajuz": a.ajuz_value,
               "total": a.total, "wasl": a.total_wasl, "dr": a.dr, "ring": a.ring,
               "numeral": a.numeral, "key": a.key, "opcode": a.opcode,
               "taBits": a.ta_bits, "bridge": [a.bridge_sadr, a.bridge_ajuz]}
              for a in J.lines],
    "graph": {"nodes": J.graph().stats()["nodes"],
              "kinds": J.graph().stats()["kinds"],
              "containers": J.graph().stats()["containers"],
              "populatedContainers": J.graph().stats()["populated_containers"],
              "largestContainer": J.graph().stats()["largest_container"],
              "impliedGraphEdges": J.graph().stats()["implied_graph_edges"],
              "storedMembershipCells": J.graph().stats()["stored_membership_cells"]},
    "keyWords": [{"w": w, "v": abjad(w)}
                 for w in ["العدد", "قط", "معرفة", "الف", "قاف", "زاي"]],
}
print(json.dumps(digest, ensure_ascii=False, indent=1))
