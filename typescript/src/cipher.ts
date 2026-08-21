/** The qaf-wa-zay cipher: resolving 107 against the transmitted 109 lines. */
import type { Jazariyyah } from "./corpus.js";
import { NAME, VALUE, abjad, digitalRoot, letterForValue, toAbjadNumeral } from "./letters.js";

export function isPrime(n: number): boolean {
  if (n < 2) return false;
  for (let i = 2; i * i <= n; i++) if (n % i === 0) return false;
  return true;
}

export function qafZay() {
  return {
    phrase: "قَافٌ وَزَاىٌ",
    letters: [["ق", VALUE["ق"]], ["ز", VALUE["ز"]]] as [string, number][],
    total: VALUE["ق"] + VALUE["ز"],
    wordReading: { "قاف": abjad("قاف"), "زاي": abjad("زاي"),
                   total: abjad("قاف") + abjad("زاي") },
  };
}

export function count109() {
  return {
    value: 109, numeral: toAbjadNumeral(109),
    letters: [["ق", VALUE["ق"]], ["ط", VALUE["ط"]]] as [string, number][],
    check: VALUE["ق"] + VALUE["ط"],
  };
}

export function transformation() {
  const a = 107, b = 109, d = b - a;
  return {
    from: a, to: b, delta: d,
    deltaLetter: letterForValue(d), deltaName: NAME[letterForValue(d)],
    numeralFrom: toAbjadNumeral(a), numeralTo: toAbjadNumeral(b),
    sharedHead: "ق",
    tailFrom: ["ز", VALUE["ز"]] as [string, number],
    tailTo: ["ط", VALUE["ط"]] as [string, number],
    drFrom: digitalRoot(a), drTo: digitalRoot(b),
    drFromLetter: letterForValue(digitalRoot(a)),
    drToLetter: letterForValue(digitalRoot(b)),
    bothPrime: isPrime(a) && isPrime(b),
    twinPrimes: isPrime(a) && isPrime(b) && d === 2,
  };
}

export function interpolationKeys(J: Jazariyyah) {
  return J.interpolated.map(a => ({
    n: a.n, text: `${a.sadr} ✽ ${a.ajuz}`, total: a.total, numeral: a.numeral,
    dr: a.dr, ring: a.ring, ringLetter: a.ringLetter, key: a.key,
    opcode: a.opcode, unlocks: a.total % 109 || 109,
  }));
}

export function resolve(J: Jazariyyah) {
  const colophon = J.line(J.meta.authorial_count_line);
  const keys = interpolationKeys(J);
  const surplus = keys.reduce((s, k) => s + k.total, 0);
  return {
    qafZay: qafZay(), count109: count109(), transformation: transformation(),
    colophonOrdinal: colophon.n,
    colophonText: `${colophon.sadr} ✽ ${colophon.ajuz}`,
    colophonSelfConsistent: colophon.n === J.authorialCount,
    interpolationKeys: keys, surplusTotal: surplus,
    surplusDr: digitalRoot(surplus), surplusNumeral: toAbjadNumeral(surplus),
    apparatus: J.meta.recension_apparatus ?? {},
  };
}
