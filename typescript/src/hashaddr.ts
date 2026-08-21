/** Deterministic abjad hash addressing; addresses are callable transformations. */
import { ALPHABET_SIZE, abjad, digitalRoot, moduloLetter, toAbjadNumeral } from "./letters.js";
import type { TaState } from "./letters.js";
import type { TreeGraph, Node } from "./graphtree.js";

export const STATE_BIT: Record<TaState, number> = { waqf: 0, wasl: 1 };
export type Opcode = "PARENT" | "GRANDPARENT" | "IDENTITY" | "SHIFT";
export const OPS_ORDER: Opcode[] = ["IDENTITY", "PARENT", "GRANDPARENT", "SHIFT"];

export class HashAddress {
  constructor(
    public readonly value: number,
    public readonly depth: number,
    public readonly path: string,
    public readonly state: TaState = "waqf"
  ) {}

  get key(): string {
    return `J${this.value}/D${this.depth}/P${this.path}/S${STATE_BIT[this.state]}`;
  }
  get numeral(): string { return toAbjadNumeral(this.value); }
  get digitalRoot(): number { return digitalRoot(this.value); }
  get ring(): number { return this.value ? ((this.value - 1) % ALPHABET_SIZE) + 1 : 1; }
  get ringLetter(): string { return moduloLetter(this.value); }
  get bucket(): string { return `C${this.digitalRoot}.${this.ring}`; }
  get opcode(): Opcode { return OPS_ORDER[this.value % 4]; }

  equals(o: HashAddress): boolean { return this.key === o.key; }
  toString(): string { return this.key; }

  /** Execute this address against a graph, returning the node reached. */
  call(graph: TreeGraph, nid: string): Node | undefined {
    return OPS[this.opcode](graph, nid);
  }

  static of(text: string, depth = 0, path = "0", state: TaState = "waqf"): HashAddress {
    return new HashAddress(abjad(text, state), depth, path, state);
  }

  static parse(key: string): HashAddress {
    const m = /^J(-?\d+)\/D(-?\d+)\/P(.*)\/S([01])$/.exec(key);
    if (!m) throw new Error(`malformed address ${key}`);
    return new HashAddress(Number(m[1]), Number(m[2]), m[3], m[4] === "0" ? "waqf" : "wasl");
  }
}

/** آب == 1+2 == 3 == ج -> ascend one level. */
const opParent = (g: TreeGraph, nid: string) => {
  const n = g.nodes.get(nid);
  return n?.parent ? g.nodes.get(n.parent) : undefined;
};
/** جد == 3+4 == 7 == ز -> ascend two levels. */
const opGrandparent = (g: TreeGraph, nid: string) => {
  const p = opParent(g, nid);
  return p?.parent ? g.nodes.get(p.parent) : undefined;
};
/** هو == 5+6 == 11 == يا -> hold. */
const opIdentity = (g: TreeGraph, nid: string) => g.nodes.get(nid);
/** زح == 7+8 == 15 == يه -> next member of the container. */
const opShift = (g: TreeGraph, nid: string) => {
  const n = g.nodes.get(nid);
  if (!n) return undefined;
  const members = g.container(n.address.bucket);
  if (members.length === 0) return undefined;
  const i = members.indexOf(nid);
  return g.nodes.get(members[(i + 1) % members.length]);
};

export const OPS: Record<Opcode, (g: TreeGraph, nid: string) => Node | undefined> = {
  PARENT: opParent, GRANDPARENT: opGrandparent,
  IDENTITY: opIdentity, SHIFT: opShift,
};

export interface BootPair {
  word: string; letters: string[]; sum: number; opcode: Opcode; gloss: string;
}
export const BOOTLOADER: BootPair[] = [
  { word: "آب", letters: ["ا", "ب"], sum: 3, opcode: "PARENT", gloss: "الأب / parent" },
  { word: "جد", letters: ["ج", "د"], sum: 7, opcode: "GRANDPARENT", gloss: "الجد / grandparent" },
  { word: "هو", letters: ["ه", "و"], sum: 11, opcode: "IDENTITY", gloss: "هو / identity" },
  { word: "زح", letters: ["ز", "ح"], sum: 15, opcode: "SHIFT", gloss: "الزحزحة / displacement" },
];
