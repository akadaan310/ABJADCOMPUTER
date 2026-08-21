/** Recursive nested letter expansion and first-class-function evaluation. */
import { FOLD, VALUE, normalise, spell, stripDiacritics } from "./letters.js";

export class Expansion {
  constructor(
    public ch: string,
    public depth: number,
    public value: number,
    public children: Expansion[] = [],
    public path: string = ""
  ) {}

  get isLeaf(): boolean { return this.children.length === 0; }

  surface(): string {
    return this.isLeaf ? this.ch : this.children.map(c => c.surface()).join("");
  }

  sexpr(): string {
    return this.isLeaf ? this.ch
      : this.ch + "(" + this.children.map(c => c.sexpr()).join("") + ")";
  }

  *walk(): Generator<Expansion> {
    yield this;
    for (const c of this.children) yield* c.walk();
  }

  leaves(): Expansion[] {
    return [...this.walk()].filter(n => n.isLeaf);
  }
}

export function expandLetter(
  ch: string, depth: number, variant: "long" | "short" = "long", path = "0"
): Expansion {
  if (!(ch in VALUE)) throw new Error(`not an abjad letter: ${ch}`);
  if (depth <= 0) return new Expansion(ch, 0, VALUE[ch], [], path);
  const name = normalise(spell(ch, variant));
  const kids = [...name].map((c, i) => expandLetter(c, depth - 1, variant, `${path}.${i}`));
  return new Expansion(ch, depth, kids.reduce((s, k) => s + k.value, 0), kids, path);
}

export function expandWord(
  word: string, depth: number, variant: "long" | "short" = "long"
): Expansion[] {
  return [...normalise(word)].map((c, i) => expandLetter(c, depth, variant, String(i)));
}

export function wordValueAtDepth(word: string, depth: number,
                                 variant: "long" | "short" = "long"): number {
  return expandWord(word, depth, variant).reduce((s, e) => s + e.value, 0);
}

export function depthSeries(ch: string, maxDepth: number,
                            variant: "long" | "short" = "long"): number[] {
  const out: number[] = [];
  for (let d = 0; d <= maxDepth; d++) out.push(expandLetter(ch, d, variant).value);
  return out;
}

export class ExprError extends Error {}

/** Parse a hash-address expression such as آ(آ(آلف)ل(لام)ف(فا)). */
export function parse(src: string): Expansion {
  let s = [...stripDiacritics(src)].map(c => FOLD[c] ?? c).join("");
  s = [...s].filter(c => c in VALUE || c === "(" || c === ")").join("");
  let pos = 0;
  const peek = () => (pos < s.length ? s[pos] : "");

  function parseOne(path: string): Expansion {
    const ch = peek();
    if (!(ch in VALUE)) throw new ExprError(`expected a letter at offset ${pos}, got '${ch}'`);
    pos++;
    if (peek() !== "(") return new Expansion(ch, 0, VALUE[ch], [], path);
    pos++;
    const kids: Expansion[] = [];
    while (peek() && peek() !== ")") kids.push(parseOne(`${path}.${kids.length}`));
    if (peek() !== ")") throw new ExprError("unbalanced '(' -- missing ')'");
    pos++;
    if (kids.length === 0) throw new ExprError(`empty application ${ch}()`);
    const depth = 1 + Math.max(...kids.map(k => k.depth));
    return new Expansion(ch, depth, kids.reduce((a, k) => a + k.value, 0), kids, path);
  }

  const node = parseOne("0");
  if (pos !== s.length) throw new ExprError(`trailing input at offset ${pos}`);
  return node;
}

export function evaluate(src: string): number { return parse(src).value; }

export function trace(src: string): string[] {
  const out: string[] = [];
  for (const n of parse(src).walk()) {
    const kind = n.isLeaf ? "leaf " : "apply";
    const indent = "  ".repeat((n.path.match(/\./g) ?? []).length);
    const rhs = n.children.length
      ? n.children.map(k => k.value).join(" + ") + ` = ${n.value}`
      : String(n.value);
    out.push(`${indent}${kind} ${n.ch}@${n.path}  ${rhs}`);
  }
  return out;
}
