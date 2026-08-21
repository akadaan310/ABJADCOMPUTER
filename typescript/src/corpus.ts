/** Load al-Muqaddimah al-Jazariyyah and analyse it line by line. */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { TreeGraph } from "./graphtree.js";
import { HashAddress, type Opcode } from "./hashaddr.js";
import { NAME, abjad, digitalRoot, normalise, stripDiacritics, toAbjadNumeral } from "./letters.js";
import { STRIDE, stateWords } from "./states.js";

const HERE = dirname(fileURLToPath(import.meta.url));
export const DATA_PATH = join(HERE, "..", "..", "data", "jazariyyah.json");

const ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩";
export function arabicNumber(n: number): string {
  return String(n).split("").map(d => ARABIC_DIGITS[Number(d)]).join("");
}

export const OPCODE_AR: Record<Opcode, string> = {
  PARENT: "أَبٌ", GRANDPARENT: "جَدٌّ", IDENTITY: "هُوَ", SHIFT: "زَحْ",
};
export const OPCODE_EN: Record<Opcode, string> = {
  PARENT: "ascend one level", GRANDPARENT: "ascend two levels",
  IDENTITY: "hold position", SHIFT: "displace to next container member",
};

export interface RawLine { n: number; section: string; sadr: string; ajuz: string; }

export interface LineAnalysis {
  n: number; section: string; sadr: string; ajuz: string;
  sadrValue: number; ajuzValue: number; total: number; totalWasl: number;
  dr: number; ring: number; ringLetter: string; numeral: string;
  address: HashAddress; key: string; opcode: Opcode;
  taWords: string[]; taBits: number; taDelta: number;
  bridgeSadr: string; bridgeAjuz: string;
}

function analyse(row: RawLine): LineAnalysis {
  const whole = row.sadr + " " + row.ajuz;
  const total = abjad(whole, "waqf");
  const address = new HashAddress(total, 0, String(row.n), "waqf");
  const taWords = stateWords(whole).map(s => s.word);
  const totalWasl = abjad(whole, "wasl");
  const a: LineAnalysis = {
    n: row.n, section: row.section, sadr: row.sadr, ajuz: row.ajuz,
    sadrValue: abjad(row.sadr), ajuzValue: abjad(row.ajuz),
    total, totalWasl, dr: digitalRoot(total), ring: address.ring,
    ringLetter: address.ringLetter, numeral: toAbjadNumeral(total),
    address, key: address.key, opcode: address.opcode,
    taWords, taBits: taWords.length, taDelta: totalWasl - total,
    bridgeSadr: "", bridgeAjuz: "",
  };
  a.bridgeSadr = `جُمْلَتُهُ ${arabicNumber(a.total)} وَجَذْرُهُ ${arabicNumber(a.dr)} ظَهَرْ`;
  a.bridgeAjuz = `وَبَابُهُ ${NAME[a.ringLetter]} ${OPCODE_AR[a.opcode]} لِمَنِ اعْتَبَرْ`;
  return a;
}

export class Jazariyyah {
  meta: Record<string, any>;
  lines: LineAnalysis[];
  private cachedGraph?: TreeGraph;

  constructor(path: string = DATA_PATH) {
    const raw = JSON.parse(readFileSync(path, "utf-8"));
    const { lines, ...meta } = raw;
    this.meta = meta;
    this.lines = (lines as RawLine[]).map(analyse);
  }

  line(n: number): LineAnalysis { return this.lines[n - 1]; }
  get authorialCount(): number { return this.meta.authorial_count; }
  get interpolated(): LineAnalysis[] {
    return (this.meta.interpolated_lines as number[]).map(n => this.line(n));
  }

  find(needle: string): LineAnalysis[] {
    const q = normalise(needle);
    return q ? this.lines.filter(a => normalise(a.sadr + " " + a.ajuz).includes(q)) : [];
  }

  totals() {
    const v = this.lines.map(a => a.total);
    const min = Math.min(...v), max = Math.max(...v);
    return {
      sum: v.reduce((s, x) => s + x, 0), min, max,
      mean: Math.floor(v.reduce((s, x) => s + x, 0) / v.length),
      argmin: v.indexOf(min) + 1, argmax: v.indexOf(max) + 1,
    };
  }

  graph(expandDepth = 0): TreeGraph {
    if (this.cachedGraph) return this.cachedGraph;
    const g = new TreeGraph();
    const root = g.add(this.meta.work, "corpus");
    const secs = new Map<string, string>();
    for (const a of this.lines) {
      if (!secs.has(a.section)) {
        secs.set(a.section, g.add(a.section, "section", { parent: root.nid }).nid);
      }
      const ln = g.add(a.sadr + " " + a.ajuz, "line", {
        parent: secs.get(a.section)!, path: String(a.n),
        meta: { n: a.n, section: a.section, dr: a.dr, taBits: a.taBits },
      });
      for (const [half, txt] of [["sadr", a.sadr], ["ajuz", a.ajuz]] as const) {
        const h = g.add(txt, "hemistich", {
          parent: ln.nid, path: `${a.n}.${half}`, meta: { half },
        });
        stripDiacritics(txt).split(/\s+/).forEach((w, i) => {
          if (normalise(w)) g.add(w, "word", { parent: h.nid, path: `${a.n}.${half}.${i}` });
        });
      }
    }
    if (expandDepth) {
      for (const n of [...g.nodes.values()].filter(x => x.kind === "word")) {
        g.graftExpansion(n.nid, expandDepth);
      }
    }
    this.cachedGraph = g;
    return g;
  }
}

export { STRIDE };
