# ABJADCOMPUTER

A computational engine that models the Arabic alphabet as a **graph-tree hybrid** — a
hierarchical tree for local branching and a containerised graph for global addressing —
and runs it over the 109 transmitted lines of **al-Muqaddimah al-Jazariyyah**.

Two independent implementations (Python and TypeScript), zero runtime dependencies, and
ten generated reports. Every number the engine prints is a sum of table look-ups, so any
result can be re-checked with pencil and paper.

```
ق = 100          ا =   1          ة → ه =   5   (waqf)
ز =   7          ل =  30          ة → ت = 400   (waṣl)
-----            ف =  80          -------------
    107              111              stride 395
```

## Quick start

```bash
make build          # compile the TypeScript engine
make test           # 41 Python tests + 35 TypeScript tests
make verify         # assert both engines produce an identical digest
make report         # regenerate all ten documents in docs/
```

Neither engine needs anything beyond the standard library; TypeScript is a build-time
dependency only.

## CLI

Identical surface in both languages:

```bash
python3 -m abjad.cli <cmd>      # from python/
node typescript/dist/cli.js <cmd>
```

| command | does |
|---|---|
| `value <word…>` | abjad total with the full addition column |
| `expand <letter> --depth N` | recursive nested letter expansion |
| `eval '<expr>'` | execute a hash address as a function |
| `addr <word>` | the canonical hash address of a token |
| `line <n…>` | one line of the Jazariyyah with its arithmetic and generated bridge |
| `cipher` | the 107 ↔ 109 resolution |
| `boot` | the `آب جد هو زح` bootloader |
| `states` | the tāʾ marbūṭah stride table |
| `graph --expand N` | graph-tree statistics |
| `jump <value>` | everything in the corpus at one address |
| `report --out docs` | regenerate the ten documents (Python only) |

Worked example — an address executed as a first-class function:

```console
$ python3 -m abjad.cli eval 'آ(آ(آلف)ل(لام)ف(فا))'
  apply ا@0  111 + 71 + 81 = 263
    apply ا@0.0  1 + 30 + 80 = 111
    apply ل@0.1  30 + 1 + 40 = 71
    apply ف@0.2  80 + 1 = 81
  => 263
```

## Architecture

**Hash addressing.** Every node's key is `J<value>/D<depth>/P<path>/S<state>`, a pure
function of the node itself — so retrieval is one dictionary probe, not a search.

**Containerised graph.** A node's container is `C<digital-root>.<ring-position>`, both
derived from its abjad total. A container of *k* nodes behaves as a clique, but only
membership is stored: O(n) storage with single-hop reachability instead of O(n²). Over
this corpus that is 1 350 cells standing in for 5 781 implied edges.

**Four inherited operations.** The alphabet's opening pairs sum to 3, 7, 11, 15 — an
arithmetic progression of stride 4 — so an address reduced modulo 4 selects exactly one
of `PARENT` / `GRANDPARENT` / `IDENTITY` / `SHIFT`. Three walk tree edges, one walks a
graph edge.

**State bit.** The feminine ending is genuinely bistable in recitation (`ة` → `ه` = 5 at
a stop, → `ت` = 400 in continuation), so it carries one real bit per grapheme with a
uniform stride of 395. That bit is the `S` component of the address.

## Documents

| file | contents |
|---|---|
| [`docs/01`](docs/01_jazariyyah_109_interleaved_recitation.md) | all 109 lines, each interleaved with a generated *bayt abjadī* and its routing state |
| [`docs/02`](docs/02_qaf_zay_cipher_resolution.md) | the قاف وزاي cipher: why 107 and 109 are both right |
| [`docs/03`](docs/03_primordial_alphabet_bootloader.md) | `آب جد هو زح` as a four-instruction bootloader |
| [`docs/04`](docs/04_nested_expansion_atlas.md) | nested letter expansion, L0–L3, all 28 letters |
| [`docs/05`](docs/05_hash_address_lookup_tables.md) | address format, cost model, full lookup tables |
| [`docs/06`](docs/06_graph_tree_hybrid_topology.md) | the two link systems and where they disagree |
| [`docs/07`](docs/07_ta_marbutah_routing_states.md) | the feminine ending as a uniform-stride bit field |
| [`docs/08`](docs/08_non_dictionary_root_synthesis.md) | reading tokens that have no lexical entry |
| [`docs/09`](docs/09_constellation_modulo_map.md) | modulo-equivalence constellations across the corpus |
| [`docs/10`](docs/10_corpus_findings_and_verification.md) | findings, provenance and the verification record |

## Two results worth the arithmetic

**الْعَدَدْ weighs 109.** The colophon states the poem's length as *qāf wa-zāy* = 100 + 7
= 107. Its own last word, `الْعَدَدْ` ("the count"), weighs 1 + 30 + 70 + 4 + 4 = **109** —
the number of lines actually transmitted. Of 741 distinct words in the poem, exactly two
sit at address 109: `الْعَدَدْ`, and `قَطٍ`, which is how a scribe writes 109. The
arithmetic is exact; authorial intent is not claimed.

**The paradox is positional, not arithmetical.** The two witnesses collated here carry the
same closing lines in a different order. Where the colophon stands at ordinal 107 its
statement is true of its own position and the doxology follows as an appendix; where the
same two lines are spliced in ahead of it, the colophon is displaced to 109 and a line
reading *"its verses are 107"* ends up sitting at position 109. See `docs/02` §5.

## Corpus and provenance

`data/jazariyyah.json` carries the 109 lines, vocalised, with section divisions,
a variant apparatus and a record of every correction applied.

- **Primary witness:** takw.in vocalised recension, retrieved 2026-08-21.
- **Collated against:** [ar.wikisource.org](https://ar.wikisource.org/wiki/الجزرية) — unvocalised, 108 lines, omitting `مِنْهُ وَمِنْ فَوْقِ الثَّنَايَا السُّفْلَى`.
- The two witnesses disagree in **34 hemistichs**; two obvious dropped letters were
  corrected where the second witness and the rhyme both agree. Both corrections are
  logged in the data file.

> **This is a transmitted recension, not a critical edition.** Collate against a printed
> critical edition before citing any of it in scholarship. The engine is exact; the corpus
> is only as good as its witnesses.

## Scope note

`docs/08` derives readings for strings with no lexical entry. That procedure is a formal,
deterministic placement of a token inside *this corpus*. It is not a claim about attested
Arabic lexicography, and a reading it produces is not evidence that a word exists or means
anything in the language.

## Layout

```
data/       jazariyyah.json (109 lines + apparatus), letters.json (28-letter table)
python/     abjad/ engine + CLI, tests/, dump.py
typescript/ src/ engine + CLI + tests, compiled to dist/
docs/       the ten generated reports
```

## Licence

MIT.
