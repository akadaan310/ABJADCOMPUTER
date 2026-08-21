/** By-hand-verifiable regression tests. Run: node dist/test.js */
import { strict as assert } from "node:assert";

import { resolve, isPrime, transformation } from "./cipher.js";
import { Jazariyyah } from "./corpus.js";
import { depthSeries, evaluate, expandLetter, parse } from "./expand.js";
import { BOOTLOADER, HashAddress } from "./hashaddr.js";
import {
  ALPHABET_SIZE, ALPHABET_SUM, BY_ORDER, LETTERS, VALUE, abjad,
  digitalRoot, normalise, toAbjadNumeral,
} from "./letters.js";
import { STRIDE, analyseWord, openTaPairs } from "./states.js";

let passed = 0, failed = 0;
function test(name: string, fn: () => void): void {
  try { fn(); passed++; console.log(`  ok   ${name}`); }
  catch (e) { failed++; console.log(`  FAIL ${name}\n       ${(e as Error).message}`); }
}

console.log("letters");
test("table is complete", () => {
  assert.equal(LETTERS.length, ALPHABET_SIZE);
  assert.equal(ALPHABET_SUM, 5995);
});
test("known values", () => {
  assert.equal(abjad("الف"), 111);
  assert.equal(abjad("قاف"), 181);
  assert.equal(abjad("زاي"), 18);
  assert.equal(abjad("العدد"), 109);
  assert.equal(abjad("قط"), 109);
  assert.equal(abjad("معرفة"), 395);
});
test("hamza folds onto alif", () => {
  for (const ch of "أإآٱءؤئ") assert.equal(abjad(ch), 1);
  assert.equal(abjad("ى"), 10);
});
test("diacritics ignored", () => assert.equal(abjad("مُحَمَّدٌ"), abjad("محمد")));
test("digital root", () => {
  for (const [n, w] of [[107, 8], [109, 1], [111, 3], [9, 9], [18, 9], [0, 0]]) {
    assert.equal(digitalRoot(n), w);
  }
});
test("numerals roundtrip", () => {
  for (const n of [1, 9, 107, 109, 111, 395, 5995]) {
    assert.equal(abjad(toAbjadNumeral(n)), n);
  }
});

console.log("expansion");
test("alif series matches spec", () => {
  const s = depthSeries("ا", 2);
  assert.equal(s[0], 1);
  assert.equal(s[1], 111);
  assert.equal(s[2], 111 + 71 + 82);
});
test("expansion is monotone", () => {
  for (const ch of BY_ORDER) {
    const s = depthSeries(ch, 3);
    assert.deepEqual([...s].sort((a, b) => a - b), s);
  }
});
test("sexpr roundtrips", () => {
  const e = expandLetter("ا", 2);
  assert.equal(evaluate(e.sexpr()), e.value);
});
test("spec expression", () => {
  assert.equal(evaluate("آ(آ(آلف)ل(لام)ف(فا))"), 263);
  assert.equal(evaluate("آ(آلف)"), 111);
});
test("bad expressions raise", () => {
  for (const bad of ["آ(", "آ()", "()", "آ(آلف))"]) assert.throws(() => parse(bad));
});
test("leaf equals letter weight", () => {
  for (const ch of BY_ORDER) assert.equal(expandLetter(ch, 0).value, VALUE[ch]);
});

console.log("hash address");
test("roundtrip", () => {
  for (const st of ["waqf", "wasl"] as const) {
    const a = new HashAddress(109, 2, "3.1.0", st);
    assert.equal(HashAddress.parse(a.key).key, a.key);
  }
});
test("address is a function of the datum", () => {
  assert.equal(HashAddress.of("العدد").key, HashAddress.of("قط").key);
});
test("ring is 1-based and in range", () => {
  for (let n = 1; n < 500; n++) {
    const r = new HashAddress(n, 0, "0").ring;
    assert.ok(r >= 1 && r <= ALPHABET_SIZE);
  }
});
test("opcode is total", () => {
  const ok = new Set(["PARENT", "GRANDPARENT", "IDENTITY", "SHIFT"]);
  for (let n = 0; n < 200; n++) assert.ok(ok.has(new HashAddress(n, 0, "0").opcode));
});

console.log("bootloader");
test("pair sums", () => assert.deepEqual(BOOTLOADER.map(p => p.sum), [3, 7, 11, 15]));
test("stride is four", () => {
  const s = BOOTLOADER.map(p => p.sum);
  assert.deepEqual(s.slice(1).map((x, i) => x - s[i]), [4, 4, 4]);
});
test("renderings", () => {
  assert.equal(toAbjadNumeral(3), "ج");
  assert.equal(toAbjadNumeral(7), "ز");
  assert.equal(toAbjadNumeral(11), "يا");
  assert.equal(toAbjadNumeral(15), "يه");
});
test("octet sums to 36", () => {
  assert.equal(BY_ORDER.slice(0, 8).reduce((s, c) => s + VALUE[c], 0), 36);
  assert.equal(BOOTLOADER.reduce((s, p) => s + p.sum, 0), 36);
});

console.log("states");
test("stride", () => assert.equal(STRIDE, 395));
test("uniform stride across bab al-taat", () => {
  for (const p of openTaPairs()) assert.equal(p.delta, STRIDE);
});
test("bits scale the delta", () => {
  for (const w of ["رحمة", "الصلاة", "مقدمة"]) {
    const s = analyseWord(w);
    assert.equal(s.delta, s.count * STRIDE);
  }
});

console.log("corpus");
const J = new Jazariyyah();
test("line count", () => {
  assert.equal(J.lines.length, 109);
  assert.equal(J.lines.length, J.meta.line_count);
});
test("every line has both hemistichs", () => {
  for (const a of J.lines) { assert.ok(normalise(a.sadr)); assert.ok(normalise(a.ajuz)); }
});
test("totals are additive", () => {
  for (const a of J.lines) assert.equal(a.sadrValue + a.ajuzValue, a.total);
});
test("wasl total never smaller", () => {
  for (const a of J.lines) {
    assert.ok(a.totalWasl >= a.total);
    assert.equal(a.taDelta, a.taBits * STRIDE);
  }
});
test("colophon sits at its own count", () => {
  const n = J.meta.authorial_count_line;
  assert.equal(n, J.authorialCount);
  assert.ok(J.line(n).sadr.includes("قَاف"));
});
test("graph is well formed", () => {
  const g = J.graph();
  for (const [nid, n] of g.nodes) {
    if (n.parent) assert.ok(g.nodes.get(n.parent)!.children.includes(nid));
    for (const c of n.children) assert.equal(g.nodes.get(c)!.parent, nid);
  }
});
test("O(1) lookup finds the node", () => {
  const g = J.graph();
  let i = 0;
  for (const n of g.nodes.values()) {
    if (i++ >= 200) break;
    assert.ok(g.byKey(n.address.key));
  }
});

console.log("cipher");
test("qaf plus zay", () => assert.equal(VALUE["ق"] + VALUE["ز"], 107));
test("qaf plus ta", () => assert.equal(VALUE["ق"] + VALUE["ط"], 109));
test("twin primes", () => {
  assert.ok(isPrime(107) && isPrime(109));
  assert.ok(transformation().twinPrimes);
});
test("digital roots wrap the octet", () => {
  assert.equal(digitalRoot(107), 8);
  assert.equal(digitalRoot(109), 1);
});
test("resolution is self consistent", () => {
  const r = resolve(J);
  assert.ok(r.colophonSelfConsistent);
  assert.equal(r.interpolationKeys.length, 2);
});

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
