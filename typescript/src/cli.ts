#!/usr/bin/env node
/** Zero-dependency CLI mirroring python -m abjad.cli. */
import { Jazariyyah } from "./corpus.js";
import { resolve } from "./cipher.js";
import { depthSeries, evaluate, expandLetter, trace } from "./expand.js";
import { BOOTLOADER, HashAddress } from "./hashaddr.js";
import {
  ALPHABET_SUM, BY_ORDER, NAME, VALUE, abjad, breakdown, digitalRoot,
  toAbjadNumeral, type TaState,
} from "./letters.js";
import { STRIDE, openTaPairs } from "./states.js";

const USAGE = `abjad <command> [args]

  value  <word...> [--state waqf|wasl]   abjad total with working
  expand <letter>  [--depth N] [--variant long|short]
  eval   <expr>                          execute a hash-address expression
  addr   <word>    [--depth N] [--path P] [--state S]
  line   <n...>                          a line of the Jazariyyah
  cipher                                 the 107 <-> 109 resolution
  boot                                   the آب جد هو زح bootloader
  states                                 the ta' marbuta stride table
  graph  [--expand N]                    graph-tree statistics
  jump   <value>                         everything at an address
`;

function flag(argv: string[], name: string, dflt: string): string {
  const i = argv.indexOf(`--${name}`);
  return i >= 0 && argv[i + 1] !== undefined ? argv[i + 1] : dflt;
}
const positional = (argv: string[]) => {
  const out: string[] = [];
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith("--")) { i++; continue; }
    out.push(argv[i]);
  }
  return out;
};

function main(argv: string[]): number {
  const cmd = argv[0];
  const rest = argv.slice(1);
  const pos = positional(rest);

  switch (cmd) {
    case "value": {
      const state = flag(rest, "state", "waqf") as TaState;
      for (const w of pos) {
        const b = breakdown(w, state);
        const v = b.reduce((s, [, x]) => s + x, 0);
        console.log(w);
        console.log("  " + b.map(([c, x]) => `${c}(${x})`).join(" + ") + ` = ${v}`);
        console.log(`  numeral ${toAbjadNumeral(v)}   dr ${digitalRoot(v)}   ` +
                    `address ${new HashAddress(v, 0, "0", state).key}`);
      }
      break;
    }
    case "expand": {
      const depth = Number(flag(rest, "depth", "2"));
      const variant = flag(rest, "variant", "long") as "long" | "short";
      for (const ch of pos[0] ?? "ا") {
        const e = expandLetter(ch, depth, variant);
        console.log(`${ch}  depth ${depth}  variant ${variant}`);
        console.log(`  series L0..L${depth}: ${JSON.stringify(depthSeries(ch, depth, variant))}`);
        console.log(`  sexpr  ${e.sexpr()}`);
        console.log(`  value  ${e.value}   surface ${e.surface()}`);
        for (const n of e.walk()) {
          const ind = "  ".repeat((n.path.match(/\./g) ?? []).length);
          console.log(`    ${ind}${n.ch}@${n.path} = ${n.value}`);
        }
      }
      break;
    }
    case "eval": {
      const expr = pos[0];
      console.log(expr);
      for (const l of trace(expr)) console.log("  " + l);
      console.log(`  => ${evaluate(expr)}`);
      break;
    }
    case "addr": {
      const a = HashAddress.of(pos[0], Number(flag(rest, "depth", "0")),
                               flag(rest, "path", "0"),
                               flag(rest, "state", "waqf") as TaState);
      console.log(JSON.stringify({
        word: pos[0], key: a.key, value: a.value, numeral: a.numeral,
        digitalRoot: a.digitalRoot, ring: a.ring, ringLetter: a.ringLetter,
        bucket: a.bucket, opcode: a.opcode,
      }, null, 1));
      break;
    }
    case "line": {
      const J = new Jazariyyah();
      for (const s of pos) {
        const a = J.line(Number(s));
        console.log(`[${a.n}] ${a.section}`);
        console.log(`  ${a.sadr}  ✽  ${a.ajuz}`);
        console.log(`  bridge: ${a.bridgeSadr}  ✽  ${a.bridgeAjuz}`);
        console.log(`  sadr ${a.sadrValue} + ajuz ${a.ajuzValue} = ${a.total} (${a.numeral})`);
        console.log(`  dr ${a.dr}  ring ${a.ring}=${a.ringLetter}  ${a.key}  ${a.opcode}`);
        if (a.taBits) {
          console.log(`  state: ${a.taBits} bit(s) ${JSON.stringify(a.taWords)} ` +
                      `waṣl ${a.totalWasl} Δ ${a.taDelta}`);
        }
      }
      break;
    }
    case "cipher":
      console.log(JSON.stringify(resolve(new Jazariyyah()), null, 1));
      break;
    case "boot": {
      console.log("primordial sequence:");
      for (const c of BY_ORDER.slice(0, 8)) {
        console.log(`  ${c} = ${String(VALUE[c]).padStart(2)}  ${NAME[c]}`);
      }
      console.log("\npairs:");
      for (const p of BOOTLOADER) {
        console.log(`  ${p.word}: ${p.letters.map(c => `${c}(${VALUE[c]})`).join(" + ")}` +
                    ` = ${p.sum} -> ${toAbjadNumeral(p.sum)}   ` +
                    `${p.opcode.padEnd(12)} ${p.gloss}`);
      }
      console.log(`\nsums ${JSON.stringify(BOOTLOADER.map(p => p.sum))}  stride 4  ` +
                  `total ${BOOTLOADER.reduce((s, p) => s + p.sum, 0)}`);
      break;
    }
    case "states": {
      console.log(`stride = ت(400) - ه(5) = ${STRIDE}`);
      for (const p of openTaPairs()) {
        console.log(`  ${p.closed.padEnd(8)} ${String(p.closedValue).padStart(5)}  <->  ` +
                    `${p.open.padEnd(8)} ${String(p.openValue).padStart(5)}   Δ ${p.delta}`);
      }
      break;
    }
    case "graph": {
      const J = new Jazariyyah();
      console.log(JSON.stringify(J.graph(Number(flag(rest, "expand", "0"))).stats(), null, 1));
      break;
    }
    case "jump": {
      const J = new Jazariyyah();
      const target = Number(pos[0]);
      console.log(`address ${target} (${toAbjadNumeral(target)})`);
      const g = J.graph();
      const seen = new Set<string>();
      for (const nid of g.byValue.get(target) ?? []) {
        const n = g.nodes.get(nid)!;
        if (n.kind !== "word") continue;
        const k = n.label;
        if (seen.has(k)) continue;
        seen.add(k);
        console.log(`  ${n.label}   (${n.address.path})`);
      }
      for (const a of J.lines.filter(x => x.total === target)) {
        console.log(`  LINE ${a.n}: ${a.sadr} ✽ ${a.ajuz}`);
      }
      break;
    }
    default:
      console.log(USAGE);
      return cmd ? 1 : 0;
  }
  return 0;
}

process.exit(main(process.argv.slice(2)));
