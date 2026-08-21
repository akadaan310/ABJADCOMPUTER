/** Emit a canonical JSON digest of the whole engine state, for cross-checking. */
import { Jazariyyah } from "./corpus.js";
import { depthSeries } from "./expand.js";
import { BOOTLOADER, HashAddress } from "./hashaddr.js";
import { ALPHABET_SUM, BY_ORDER, VALUE, abjad, toAbjadNumeral } from "./letters.js";
import { STRIDE, openTaPairs } from "./states.js";

const J = new Jazariyyah();
const digest = {
  alphabetSum: ALPHABET_SUM,
  letters: BY_ORDER.map(c => ({
    ch: c, value: VALUE[c], series: depthSeries(c, 3),
    addr: new HashAddress(VALUE[c], 0, "0").key,
    bucket: new HashAddress(VALUE[c], 0, "0").bucket,
    opcode: new HashAddress(VALUE[c], 0, "0").opcode,
  })),
  bootloader: BOOTLOADER.map(p => ({ w: p.word, sum: p.sum, num: toAbjadNumeral(p.sum), op: p.opcode })),
  stride: STRIDE,
  taPairs: openTaPairs(),
  lines: J.lines.map(a => ({
    n: a.n, sadr: a.sadrValue, ajuz: a.ajuzValue, total: a.total,
    wasl: a.totalWasl, dr: a.dr, ring: a.ring, numeral: a.numeral,
    key: a.key, opcode: a.opcode, taBits: a.taBits,
    bridge: [a.bridgeSadr, a.bridgeAjuz],
  })),
  graph: J.graph().stats(),
  keyWords: ["العدد", "قط", "معرفة", "الف", "قاف", "زاي"].map(w => ({ w, v: abjad(w) })),
};
console.log(JSON.stringify(digest, null, 1));
