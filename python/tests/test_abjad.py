"""By-hand-verifiable regression tests.  Run: python3 -m unittest discover python/tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abjad.cipher import is_prime, resolve, transformation
from abjad.corpus import Jazariyyah
from abjad.expand import (ExprError, depth_series, evaluate, expand_letter,
                          parse, word_value_at_depth)
from abjad.graphtree import TreeGraph
from abjad.hashaddr import BOOTLOADER, HashAddress
from abjad.letters import (ALPHABET_SIZE, ALPHABET_SUM, BY_ORDER, VALUE, abjad,
                           digital_root, normalise, to_abjad_numeral)
from abjad.makharij import triliteral
from abjad.states import STRIDE, analyse_word, open_ta_pairs
from abjad.synth import synthesise


class TestLetters(unittest.TestCase):
    def test_table_is_complete(self):
        self.assertEqual(len(VALUE), ALPHABET_SIZE)
        self.assertEqual(sorted(VALUE.values()),
                         list(range(1, 10)) + list(range(10, 100, 10))
                         + list(range(100, 1100, 100)))
        self.assertEqual(ALPHABET_SUM, 5995)

    def test_known_values(self):
        self.assertEqual(abjad("الف"), 111)          # 1 + 30 + 80
        self.assertEqual(abjad("قاف"), 181)
        self.assertEqual(abjad("زاي"), 18)
        self.assertEqual(abjad("العدد"), 109)        # 1+30+70+4+4
        self.assertEqual(abjad("قط"), 109)           # 100 + 9
        self.assertEqual(abjad("معرفة"), 395)

    def test_hamza_folds_onto_alif(self):
        for ch in "أإآٱءؤئ":
            self.assertEqual(abjad(ch), 1, ch)
        self.assertEqual(abjad("ى"), 10)

    def test_diacritics_are_ignored(self):
        self.assertEqual(abjad("مُحَمَّدٌ"), abjad("محمد"))

    def test_digital_root(self):
        for n, want in [(107, 8), (109, 1), (111, 3), (9, 9), (18, 9), (0, 0)]:
            self.assertEqual(digital_root(n), want, n)

    def test_numerals_roundtrip(self):
        for n in (1, 9, 107, 109, 111, 395, 5995):
            self.assertEqual(abjad(to_abjad_numeral(n)), n, n)


class TestExpansion(unittest.TestCase):
    def test_alif_series_matches_spec(self):
        s = depth_series("ا", 2)
        self.assertEqual(s[0], 1)                    # level 0
        self.assertEqual(s[1], 111)                  # level 1, stated in the spec
        self.assertEqual(s[2], 111 + 71 + 82)        # 264

    def test_expansion_is_monotone(self):
        for ch in BY_ORDER:
            s = depth_series(ch, 3)
            self.assertEqual(sorted(s), s, ch)

    def test_sexpr_roundtrips(self):
        e = expand_letter("ا", 2)
        self.assertEqual(evaluate(e.sexpr()), e.value)

    def test_spec_expression(self):
        # the defective spelling فا (81) is honoured as written
        self.assertEqual(evaluate("آ(آ(آلف)ل(لام)ف(فا))"), 263)
        self.assertEqual(evaluate("آ(آلف)"), 111)

    def test_bad_expressions_raise(self):
        for bad in ["آ(", "آ()", "()", "آ(آلف))"]:
            with self.subTest(bad=bad), self.assertRaises((ExprError, ValueError)):
                parse(bad)

    def test_leaf_equals_letter_weight(self):
        for ch in BY_ORDER:
            self.assertEqual(expand_letter(ch, 0).value, VALUE[ch])


class TestHashAddress(unittest.TestCase):
    def test_roundtrip(self):
        for state in ("waqf", "wasl"):
            a = HashAddress(109, 2, "3.1.0", state)
            self.assertEqual(HashAddress.parse(a.key), a)

    def test_address_is_a_function_of_the_datum(self):
        self.assertEqual(HashAddress.of("العدد").key, HashAddress.of("قط").key)

    def test_ring_is_1_based_and_in_range(self):
        for n in range(1, 500):
            r = HashAddress(n, 0, "0").ring
            self.assertTrue(1 <= r <= ALPHABET_SIZE, n)

    def test_opcode_is_total(self):
        for n in range(0, 200):
            self.assertIn(HashAddress(n, 0, "0").opcode,
                          {"PARENT", "GRANDPARENT", "IDENTITY", "SHIFT"})


class TestBootloader(unittest.TestCase):
    def test_pair_sums(self):
        self.assertEqual([s for _, _, s, _, _ in BOOTLOADER], [3, 7, 11, 15])

    def test_stride_is_four(self):
        s = [x for _, _, x, _, _ in BOOTLOADER]
        self.assertEqual([b - a for a, b in zip(s, s[1:])], [4, 4, 4])

    def test_renderings(self):
        self.assertEqual(to_abjad_numeral(3), "ج")
        self.assertEqual(to_abjad_numeral(7), "ز")
        self.assertEqual(to_abjad_numeral(11), "يا")
        self.assertEqual(to_abjad_numeral(15), "يه")

    def test_octet_sums_to_36(self):
        self.assertEqual(sum(VALUE[c] for c in BY_ORDER[:8]), 36)
        self.assertEqual(sum(s for _, _, s, _, _ in BOOTLOADER), 36)


class TestStates(unittest.TestCase):
    def test_stride(self):
        self.assertEqual(STRIDE, 395)

    def test_every_bab_al_taat_word_has_uniform_stride(self):
        for p in open_ta_pairs():
            self.assertEqual(p["delta"], STRIDE, p["open"])

    def test_bits_scale_the_delta(self):
        for w in ("رحمة", "الصلاة", "مقدمة"):
            s = analyse_word(w)
            self.assertEqual(s.delta, s.count * STRIDE, w)


class TestCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.J = Jazariyyah()

    def test_line_count(self):
        self.assertEqual(len(self.J.lines), 109)
        self.assertEqual(len(self.J.lines), self.J.meta["line_count"])

    def test_every_line_has_both_hemistichs(self):
        for a in self.J.lines:
            self.assertTrue(normalise(a.sadr), a.n)
            self.assertTrue(normalise(a.ajuz), a.n)

    def test_totals_are_additive(self):
        for a in self.J.lines:
            self.assertEqual(a.sadr_value + a.ajuz_value, a.total, a.n)

    def test_wasl_total_is_never_smaller(self):
        for a in self.J.lines:
            self.assertGreaterEqual(a.total_wasl, a.total, a.n)
            self.assertEqual(a.ta_delta, a.ta_bits * STRIDE, a.n)

    def test_colophon_sits_at_its_own_count(self):
        n = self.J.meta["authorial_count_line"]
        self.assertEqual(n, self.J.authorial_count)
        self.assertIn("قَاف", self.J.line(n).sadr)

    def test_bridges_are_deterministic(self):
        again = Jazariyyah()
        for a, b in zip(self.J.lines, again.lines):
            self.assertEqual((a.bridge_sadr, a.bridge_ajuz),
                             (b.bridge_sadr, b.bridge_ajuz), a.n)

    def test_graph_is_well_formed(self):
        g = self.J.graph()
        for nid, n in g.nodes.items():
            if n.parent:
                self.assertIn(nid, g.nodes[n.parent].children, nid)
            for c in n.children:
                self.assertEqual(g.nodes[c].parent, nid)

    def test_o1_lookup_finds_the_node(self):
        g = self.J.graph()
        for n in list(g.nodes.values())[:200]:
            self.assertIsNotNone(g.by_key(n.address.key), n.nid)


class TestCipher(unittest.TestCase):
    def test_qaf_plus_zay(self):
        self.assertEqual(VALUE["ق"] + VALUE["ز"], 107)

    def test_qaf_plus_ta(self):
        self.assertEqual(VALUE["ق"] + VALUE["ط"], 109)

    def test_twin_primes(self):
        t = transformation()
        self.assertTrue(is_prime(107) and is_prime(109))
        self.assertTrue(t["twin_primes"])

    def test_digital_roots_wrap_the_octet(self):
        self.assertEqual(digital_root(107), 8)       # ح, last of آبجد هوز ح
        self.assertEqual(digital_root(109), 1)       # ا, its first

    def test_resolution_is_self_consistent(self):
        r = resolve(Jazariyyah())
        self.assertTrue(r["colophon_self_consistent"])
        self.assertEqual(len(r["interpolation_keys"]), 2)


class TestSynthesis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.J = Jazariyyah()

    def test_triliteral(self):
        self.assertEqual(triliteral(list("الحروف")), list("حرف"))
        self.assertEqual(len(triliteral(list("ا"))), 3)

    def test_is_deterministic(self):
        a = synthesise(self.J, "برشق")
        b = synthesise(self.J, "برشق")
        self.assertEqual(a.definition, b.definition)
        self.assertEqual(a.manifest.key, b.manifest.key)

    def test_manifest_is_order_blind(self):
        self.assertEqual(synthesise(self.J, "زحقل").manifest.value,
                         synthesise(self.J, "قلزح").manifest.value)

    def test_empty_token_rejected(self):
        with self.assertRaises(ValueError):
            synthesise(self.J, "!!!")

    def test_known_word_is_found_in_corpus(self):
        self.assertTrue(synthesise(self.J, "التجويد").in_lexicon)
        self.assertFalse(synthesise(self.J, "زحقل").in_lexicon)


if __name__ == "__main__":
    unittest.main(verbosity=2)
