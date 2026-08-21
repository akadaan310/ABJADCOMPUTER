/** The graph-tree hybrid: explicit tree edges + containerised constellation edges. */
import { expandLetter, Expansion } from "./expand.js";
import { HashAddress } from "./hashaddr.js";
import type { TaState } from "./letters.js";
import { normalise } from "./letters.js";

export interface Node {
  nid: string;
  label: string;
  kind: string;
  address: HashAddress;
  parent?: string;
  children: string[];
  meta: Record<string, unknown>;
}

export interface GraphStats {
  nodes: number;
  kinds: Record<string, number>;
  containers: number;
  populatedContainers: number;
  largestContainer: number;
  impliedGraphEdges: number;
  storedMembershipCells: number;
}

function push<K, V>(m: Map<K, V[]>, k: K, v: V): void {
  const a = m.get(k);
  if (a) a.push(v); else m.set(k, [v]);
}

export class TreeGraph {
  nodes = new Map<string, Node>();
  roots: string[] = [];
  byBucket = new Map<string, string[]>();
  byValue = new Map<number, string[]>();
  byDr = new Map<number, string[]>();
  byRing = new Map<number, string[]>();
  bySurface = new Map<string, string[]>();
  private seq = 0;

  add(label: string, kind: string, opts: {
    parent?: string; depth?: number; path?: string;
    state?: TaState; meta?: Record<string, unknown>;
  } = {}): Node {
    const { parent, depth = 0, path = "0", state = "waqf", meta = {} } = opts;
    const address = HashAddress.of(label, depth, path, state);
    this.seq += 1;
    const nid = `${kind[0].toUpperCase()}${this.seq}`;
    const node: Node = { nid, label, kind, address, parent, children: [], meta: { ...meta } };
    this.nodes.set(nid, node);
    if (parent !== undefined) this.nodes.get(parent)!.children.push(nid);
    else this.roots.push(nid);
    this.index(node);
    return node;
  }

  private index(n: Node): void {
    push(this.byBucket, n.address.bucket, n.nid);
    push(this.byValue, n.address.value, n.nid);
    push(this.byDr, n.address.digitalRoot, n.nid);
    push(this.byRing, n.address.ring, n.nid);
    push(this.bySurface, normalise(n.label), n.nid);
  }

  /** All nodes sharing a constellation container -- one map hit. */
  container(bucket: string): string[] { return this.byBucket.get(bucket) ?? []; }

  /** Resolve a canonical hash address to its node, O(1) average. */
  byKey(key: string): Node | undefined {
    const want = HashAddress.parse(key);
    for (const nid of this.byValue.get(want.value) ?? []) {
      const n = this.nodes.get(nid)!;
      if (n.address.equals(want)) return n;
    }
    return undefined;
  }

  jump(nid: string, relation: "bucket" | "value" | "dr" | "ring" = "bucket"): Node[] {
    const a = this.nodes.get(nid)!.address;
    const ids =
      relation === "bucket" ? this.byBucket.get(a.bucket) :
      relation === "value" ? this.byValue.get(a.value) :
      relation === "dr" ? this.byDr.get(a.digitalRoot) :
      this.byRing.get(a.ring);
    return (ids ?? []).filter(i => i !== nid).map(i => this.nodes.get(i)!);
  }

  execute(nid: string, key?: string): Node | undefined {
    const addr = key ? HashAddress.parse(key) : this.nodes.get(nid)!.address;
    return addr.call(this, nid);
  }

  siblings(nid: string): Node[] {
    const n = this.nodes.get(nid)!;
    const ids = n.parent === undefined ? this.roots : this.nodes.get(n.parent)!.children;
    return ids.filter(i => i !== nid).map(i => this.nodes.get(i)!);
  }

  pathToRoot(nid: string): Node[] {
    const out: Node[] = [];
    let cur = this.nodes.get(nid);
    while (cur) { out.push(cur); cur = cur.parent ? this.nodes.get(cur.parent) : undefined; }
    return out;
  }

  graftExpansion(nid: string, depth = 1, variant: "long" | "short" = "long"): Node[] {
    const host = this.nodes.get(nid)!;
    const made: Node[] = [];
    [...normalise(host.label)].forEach((ch, i) => {
      made.push(...this.graft(expandLetter(ch, depth, variant, String(i)), nid));
    });
    return made;
  }

  private graft(exp: Expansion, parent: string): Node[] {
    const n = this.add(exp.surface(), "expansion", {
      parent, depth: exp.depth, path: exp.path,
      meta: { head: exp.ch, sexpr: exp.sexpr() },
    });
    const made = [n];
    for (const kid of exp.children) made.push(...this.graft(kid, n.nid));
    return made;
  }

  stats(): GraphStats {
    const kinds: Record<string, number> = {};
    for (const n of this.nodes.values()) kinds[n.kind] = (kinds[n.kind] ?? 0) + 1;
    let implied = 0, cells = 0, largest = 0, populated = 0;
    for (const v of this.byBucket.values()) {
      implied += (v.length * (v.length - 1)) / 2;
      cells += v.length;
      if (v.length > largest) largest = v.length;
      if (v.length > 1) populated += 1;
    }
    return {
      nodes: this.nodes.size, kinds, containers: this.byBucket.size,
      populatedContainers: populated, largestContainer: largest,
      impliedGraphEdges: implied, storedMembershipCells: cells,
    };
  }
}
