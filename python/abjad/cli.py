"""Zero-dependency CLI for the ABJADCOMPUTER engine.

    python3 -m abjad.cli value   الحروف
    python3 -m abjad.cli expand  ا --depth 3
    python3 -m abjad.cli eval    'آ(آ(آلف)ل(لام)ف(فا))'
    python3 -m abjad.cli addr    الحروف --depth 1
    python3 -m abjad.cli line    107
    python3 -m abjad.cli cipher
    python3 -m abjad.cli boot
    python3 -m abjad.cli synth   برشق
    python3 -m abjad.cli graph   --expand 1
    python3 -m abjad.cli jump    111
    python3 -m abjad.cli report  --out docs
"""
from __future__ import annotations

import argparse
import json
import sys

from .cipher import resolve
from .corpus import Jazariyyah
from .expand import depth_series, evaluate, expand_letter, trace
from .hashaddr import BOOTLOADER, HashAddress
from .letters import (ALPHABET_SUM, BY_ORDER, NAME, VALUE, abjad, breakdown,
                      digital_root, to_abjad_numeral)
from .report import generate
from .states import STRIDE, analyse_word, open_ta_pairs
from .synth import _word_index, synthesise


def _p(*a):
    print(*a)


def cmd_value(ns):
    for w in ns.words:
        b = breakdown(w, ta_state=ns.state)
        v = sum(x for _, x in b)
        _p(f"{w}")
        _p("  " + " + ".join(f"{c}({x})" for c, x in b) + f" = {v}")
        _p(f"  numeral {to_abjad_numeral(v)}   dr {digital_root(v)}   "
           f"address {HashAddress(v,0,'0',ns.state).key}")


def cmd_expand(ns):
    for ch in ns.letter:
        e = expand_letter(ch, ns.depth, variant=ns.variant)
        _p(f"{ch}  depth {ns.depth}  variant {ns.variant}")
        _p(f"  series L0..L{ns.depth}: {depth_series(ch, ns.depth, variant=ns.variant)}")
        _p(f"  sexpr  {e.sexpr()}")
        _p(f"  value  {e.value}   surface {e.surface()}")
        for n in e.walk():
            _p(f"    {'  '*n.path.count('.')}{n.ch}@{n.path} = {n.value}")


def cmd_eval(ns):
    _p(f"{ns.expr}")
    for ln in trace(ns.expr):
        _p("  " + ln)
    _p(f"  => {evaluate(ns.expr)}")


def cmd_addr(ns):
    a = HashAddress.of(ns.word, ns.depth, ns.path, ns.state)
    _p(json.dumps({"word": ns.word, "key": a.key, "value": a.value,
                   "numeral": a.numeral, "digital_root": a.digital_root,
                   "ring": a.ring, "ring_letter": a.ring_letter,
                   "bucket": a.bucket, "opcode": a.opcode},
                  ensure_ascii=False, indent=1))


def cmd_line(ns):
    J = Jazariyyah()
    for n in ns.n:
        a = J.line(n)
        _p(f"[{a.n}] {a.section}")
        _p(f"  {a.sadr}  ✽  {a.ajuz}")
        _p(f"  bridge: {a.bridge_sadr}  ✽  {a.bridge_ajuz}")
        _p(f"  sadr {a.sadr_value} + ajuz {a.ajuz_value} = {a.total} ({a.numeral})")
        _p(f"  dr {a.dr}  ring {a.ring}={a.ring_letter}  {a.key}  {a.opcode}")
        if a.ta_bits:
            _p(f"  state: {a.ta_bits} bit(s) {a.ta_words} waṣl {a.total_wasl} Δ {a.ta_delta}")


def cmd_cipher(ns):
    _p(json.dumps(resolve(Jazariyyah()), ensure_ascii=False, indent=1))


def cmd_boot(ns):
    _p("primordial sequence:")
    for c in BY_ORDER[:8]:
        _p(f"  {c} = {VALUE[c]:2d}  {NAME[c]}")
    _p("\npairs:")
    for w, ls, s, op, gloss in BOOTLOADER:
        _p(f"  {w}: {' + '.join(f'{c}({VALUE[c]})' for c in ls)} = {s} "
           f"-> {to_abjad_numeral(s)}   {op:12s} {gloss}")
    _p(f"\nsums {[s for _,_,s,_,_ in BOOTLOADER]}  stride 4  total "
       f"{sum(s for _,_,s,_,_ in BOOTLOADER)}")


def cmd_synth(ns):
    J = Jazariyyah()
    for t in ns.tokens:
        s = synthesise(J, t)
        _p(f"== {t}")
        _p("  " + " + ".join(f"{c}({v})" for c, v in s.working) + f" = {s.manifest.value}")
        _p(f"  root ({'·'.join(s.root)}) = {s.root_value}   in-corpus: {s.in_lexicon}")
        _p(f"  manifest {s.manifest.value} {s.manifest.key}")
        _p(f"  hidden   {s.hidden.value} {s.hidden.key}")
        _p(f"  near: " + ", ".join(f"{n['word']}({n['distance']:+d})"
                                   for n in s.manifest.neighbours))
        _p(f"  {s.definition}")


def cmd_graph(ns):
    J = Jazariyyah()
    g = J.graph(expand_depth=ns.expand)
    _p(json.dumps(g.stats(), ensure_ascii=False, indent=1))


def cmd_jump(ns):
    J = Jazariyyah()
    wi = _word_index(J)
    hits = [w for w in wi if w["value"] == ns.value]
    _p(f"address {ns.value} ({to_abjad_numeral(ns.value)}) — {len(hits)} word(s)")
    for w in hits:
        _p(f"  {w['word']:<16} lines {w['lines']}")
    lines = [a for a in J.lines if a.total == ns.value]
    for a in lines:
        _p(f"  LINE {a.n}: {a.sadr} ✽ {a.ajuz}")


def cmd_states(ns):
    _p(f"stride = ت(400) - ه(5) = {STRIDE}")
    for p in open_ta_pairs():
        _p(f"  {p['closed']:<8} {p['closed_value']:>5}  <->  {p['open']:<8} "
           f"{p['open_value']:>5}   Δ {p['delta']}")


def cmd_report(ns):
    for path in generate(ns.out):
        _p("wrote " + path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="abjad", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("value"); p.add_argument("words", nargs="+")
    p.add_argument("--state", choices=["waqf", "wasl"], default="waqf")
    p.set_defaults(fn=cmd_value)

    p = sub.add_parser("expand"); p.add_argument("letter")
    p.add_argument("--depth", type=int, default=2)
    p.add_argument("--variant", choices=["long", "short"], default="long")
    p.set_defaults(fn=cmd_expand)

    p = sub.add_parser("eval"); p.add_argument("expr"); p.set_defaults(fn=cmd_eval)

    p = sub.add_parser("addr"); p.add_argument("word")
    p.add_argument("--depth", type=int, default=0)
    p.add_argument("--path", default="0")
    p.add_argument("--state", choices=["waqf", "wasl"], default="waqf")
    p.set_defaults(fn=cmd_addr)

    p = sub.add_parser("line"); p.add_argument("n", nargs="+", type=int)
    p.set_defaults(fn=cmd_line)

    sub.add_parser("cipher").set_defaults(fn=cmd_cipher)
    sub.add_parser("boot").set_defaults(fn=cmd_boot)
    sub.add_parser("states").set_defaults(fn=cmd_states)

    p = sub.add_parser("synth"); p.add_argument("tokens", nargs="+")
    p.set_defaults(fn=cmd_synth)

    p = sub.add_parser("graph"); p.add_argument("--expand", type=int, default=0)
    p.set_defaults(fn=cmd_graph)

    p = sub.add_parser("jump"); p.add_argument("value", type=int)
    p.set_defaults(fn=cmd_jump)

    p = sub.add_parser("report"); p.add_argument("--out", default="docs")
    p.set_defaults(fn=cmd_report)

    ns = ap.parse_args(argv)
    ns.fn(ns)
    return 0


if __name__ == "__main__":
    sys.exit(main())
