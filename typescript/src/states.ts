/** Orthographic state bits from the ta' marbuta / ta' maftuha rule. */
import { TA_MARBUTA, abjad, stripDiacritics } from "./letters.js";

export const TA_HA = 5;
export const TA_TA = 400;
export const STRIDE = TA_TA - TA_HA; // 395

export const OPEN_TA_RASM = ["رحمت", "نعمت", "لعنت", "امرأت", "معصيت", "شجرت",
  "سنت", "قرت", "جنت", "فطرت", "بقيت", "ابنت", "كلمت"];

export interface StateWord {
  word: string; count: number; waqf: number; wasl: number;
  delta: number; register: number[];
}

export function analyseWord(word: string): StateWord {
  const bare = stripDiacritics(word);
  const count = [...bare].filter(c => c === TA_MARBUTA).length;
  const waqf = abjad(word, "waqf");
  const wasl = abjad(word, "wasl");
  const register: number[] = [];
  for (let i = 0; i <= count; i++) register.push(waqf + i * STRIDE);
  return { word, count, waqf, wasl, delta: wasl - waqf, register };
}

export function stateWords(text: string): StateWord[] {
  return stripDiacritics(text).split(/\s+/)
    .filter(t => t.includes(TA_MARBUTA))
    .map(analyseWord);
}

export interface TaPair {
  open: string; closed: string; openValue: number; closedValue: number; delta: number;
}

export function openTaPairs(): TaPair[] {
  return OPEN_TA_RASM.map(open => {
    const closed = open.slice(0, -1) + TA_MARBUTA;
    return {
      open, closed,
      openValue: abjad(open),
      closedValue: abjad(closed, "waqf"),
      delta: abjad(open) - abjad(closed, "waqf"),
    };
  });
}
