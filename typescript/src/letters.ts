/**
 * Abjad alphabet table, orthographic normalisation and scalar valuation.
 * Mirror of python/abjad/letters.py -- the two must agree value for value.
 */

export interface LetterRow {
  ch: string; value: number; name: string; spell: string;
  order: number; group: string;
}

export const LETTERS: LetterRow[] = [
  { ch: "ا", value: 1, name: "ألف", spell: "الف", order: 1, group: "أبجد" },
  { ch: "ب", value: 2, name: "باء", spell: "باء", order: 2, group: "أبجد" },
  { ch: "ج", value: 3, name: "جيم", spell: "جيم", order: 3, group: "أبجد" },
  { ch: "د", value: 4, name: "دال", spell: "دال", order: 4, group: "أبجد" },
  { ch: "ه", value: 5, name: "هاء", spell: "هاء", order: 5, group: "هوز" },
  { ch: "و", value: 6, name: "واو", spell: "واو", order: 6, group: "هوز" },
  { ch: "ز", value: 7, name: "زاي", spell: "زاي", order: 7, group: "هوز" },
  { ch: "ح", value: 8, name: "حاء", spell: "حاء", order: 8, group: "حطي" },
  { ch: "ط", value: 9, name: "طاء", spell: "طاء", order: 9, group: "حطي" },
  { ch: "ي", value: 10, name: "ياء", spell: "ياء", order: 10, group: "حطي" },
  { ch: "ك", value: 20, name: "كاف", spell: "كاف", order: 11, group: "كلمن" },
  { ch: "ل", value: 30, name: "لام", spell: "لام", order: 12, group: "كلمن" },
  { ch: "م", value: 40, name: "ميم", spell: "ميم", order: 13, group: "كلمن" },
  { ch: "ن", value: 50, name: "نون", spell: "نون", order: 14, group: "كلمن" },
  { ch: "س", value: 60, name: "سين", spell: "سين", order: 15, group: "سعفص" },
  { ch: "ع", value: 70, name: "عين", spell: "عين", order: 16, group: "سعفص" },
  { ch: "ف", value: 80, name: "فاء", spell: "فاء", order: 17, group: "سعفص" },
  { ch: "ص", value: 90, name: "صاد", spell: "صاد", order: 18, group: "سعفص" },
  { ch: "ق", value: 100, name: "قاف", spell: "قاف", order: 19, group: "قرشت" },
  { ch: "ر", value: 200, name: "راء", spell: "راء", order: 20, group: "قرشت" },
  { ch: "ش", value: 300, name: "شين", spell: "شين", order: 21, group: "قرشت" },
  { ch: "ت", value: 400, name: "تاء", spell: "تاء", order: 22, group: "قرشت" },
  { ch: "ث", value: 500, name: "ثاء", spell: "ثاء", order: 23, group: "ثخذ" },
  { ch: "خ", value: 600, name: "خاء", spell: "خاء", order: 24, group: "ثخذ" },
  { ch: "ذ", value: 700, name: "ذال", spell: "ذال", order: 25, group: "ثخذ" },
  { ch: "ض", value: 800, name: "ضاد", spell: "ضاد", order: 26, group: "ضظغ" },
  { ch: "ظ", value: 900, name: "ظاء", spell: "ظاء", order: 27, group: "ضظغ" },
  { ch: "غ", value: 1000, name: "غين", spell: "غين", order: 28, group: "ضظغ" },
];

export const ALPHABET_SIZE = 28;
export const VALUE: Record<string, number> = {};
export const NAME: Record<string, string> = {};
export const ORDER: Record<string, number> = {};
export const GROUP: Record<string, string> = {};
export const BY_VALUE: Record<number, string> = {};
for (const r of LETTERS) {
  VALUE[r.ch] = r.value; NAME[r.ch] = r.name;
  ORDER[r.ch] = r.order; GROUP[r.ch] = r.group; BY_VALUE[r.value] = r.ch;
}
export const BY_ORDER: string[] = [...LETTERS].sort((a, b) => a.order - b.order).map(r => r.ch);
export const ALPHABET_SUM = LETTERS.reduce((s, r) => s + r.value, 0); // 5995

export const SPELLING_VARIANTS: Record<string, { short: string; long: string }> = {
  "ف": { short: "فا", long: "فاء" }, "ه": { short: "ها", long: "هاء" },
  "ط": { short: "طا", long: "طاء" }, "ح": { short: "حا", long: "حاء" },
  "ب": { short: "با", long: "باء" }, "ت": { short: "تا", long: "تاء" },
  "ث": { short: "ثا", long: "ثاء" }, "خ": { short: "خا", long: "خاء" },
  "ر": { short: "را", long: "راء" }, "ظ": { short: "ظا", long: "ظاء" },
  "ي": { short: "يا", long: "ياء" },
};

const DIACRITICS = new Set(
  ("ًٌٍَُِّْٕٓٔ" + "ٖٜٟٗ٘ٙٚٛٝٞـ" + "ٰۖۗۘۙۚۛۜ۟۠ۡ" + "ۣۢۤۥۦ۪ۭۧۨ۫۬").split("")
);

export const FOLD: Record<string, string> = {
  "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ء": "ا", "ؤ": "ا", "ئ": "ا",
  "ى": "ي", "ﻯ": "ي", "ﻰ": "ي",
};

export const TA_MARBUTA = "ة";
export type TaState = "waqf" | "wasl";

export function stripDiacritics(text: string): string {
  return [...text].filter(c => !DIACRITICS.has(c)).join("");
}

export function normalise(text: string, taState: TaState = "waqf"): string {
  const out: string[] = [];
  for (let ch of stripDiacritics(text)) {
    ch = FOLD[ch] ?? ch;
    if (ch === TA_MARBUTA) ch = taState === "waqf" ? "ه" : "ت";
    if (ch in VALUE) out.push(ch);
  }
  return out.join("");
}

export function abjad(text: string, taState: TaState = "waqf"): number {
  let t = 0;
  for (const c of normalise(text, taState)) t += VALUE[c];
  return t;
}

export function breakdown(text: string, taState: TaState = "waqf"): [string, number][] {
  return [...normalise(text, taState)].map(c => [c, VALUE[c]] as [string, number]);
}

export function digitalRoot(n: number): number {
  if (n === 0) return 0;
  n = Math.abs(n);
  return 1 + ((n - 1) % 9);
}

export function toAbjadNumeral(n: number): string {
  if (n <= 0) return "";
  const out: string[] = [];
  const weights = [...new Set(LETTERS.map(r => r.value))].sort((a, b) => b - a);
  for (const v of weights) while (n >= v) { out.push(BY_VALUE[v]); n -= v; }
  return out.join("");
}

export function letterForValue(n: number): string {
  return BY_VALUE[n] ?? "";
}

export function moduloLetter(n: number, modulus = ALPHABET_SIZE): string {
  const idx = n ? ((n - 1) % modulus) + 1 : 1;
  return BY_ORDER[idx - 1];
}

export function spell(ch: string, variant: "long" | "short" = "long"): string {
  if (variant === "short" && SPELLING_VARIANTS[ch]) return SPELLING_VARIANTS[ch].short;
  return NAME[ch] ?? ch;
}
