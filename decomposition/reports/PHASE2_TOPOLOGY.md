# Phase 2 — Topology of the Street Network

## Does it form closed regions?

**Yes, almost perfectly.** With ink defined as `value < 255` and the canvas border treated as a
virtual closing wall, the white space partitions into **3 623 regions**, of which **2 560 are
≥ 50 px** — these are the atomic street cells (city blocks, plazas, river segments, park
interiors). The street network itself is a single connected component (established in the
master QA), which is exactly why closure works: there are no dangling breaks in the linework.

## Is preprocessing / repair required?

**No pixel of the master was modified.** Three segmentation *conventions* (not repairs) were adopted:

1. **Virtual frame wall** — the canvas edge closes cells clipped by the band limits. This is a
   property of the segmentation, applied on a copy; it reflects the physical reality that the
   fresco ends there.
2. **Ink threshold `< 255`** (anti-aliasing counts as wall) — see below.
3. **Sliver absorption** — the 1 063 white fragments < 50 px (anti-aliasing pockets, acute
   intersection wedges) are not treated as cells; they are absorbed into the nearest real cell
   by label propagation when building the seamless partition.

## Does anti-aliasing affect region detection?

Measured directly by comparing both thresholds:

| | ink `<255` (AA = wall) | ink `<128` (core only) |
|---|---|---|
| total white regions | 3 623 | 4 064 |
| regions ≥ 100 px | 2 519 | 2 528 |

Effect on meaningful regions: **±0.4%** — negligible. The decisive argument for `<255`: the
master contains 72 nearly-collapsed white channels between parallel streets (documented in the
master report). With AA as wall these remain **separate regions**; with core-only walls several
merge. AA-as-wall therefore *preserves* real topology.

## Do tiny gaps prevent closure?

No case was found where a genuine street line fails to enclose. The pin-hole survey from the
master stage (≈1 300 sub-4 px white specks inside strokes) does not affect closure — those are
enclosed *within* ink and become slivers absorbed during partitioning. Conversely, no spurious
merges between visually distinct blocks were observed when sampling the largest cells (the big
cells are the Seine segments, Tuileries, Père-Lachaise, rail yards — all legitimately large).

## Seamless partition

For mask generation, every ink pixel was assigned to its nearest cell by iterative label
propagation (70 iterations to full coverage). Result: a **complete partition of all
180 862 976 canvas pixels into 2 560 cells** — no gaps, no overlaps; each cell owns its open
space plus the surrounding stroke up to the wall centerline. Union of any cell set is therefore
a pixel-exact, seam-free mask. Adjacency (7 398 cell pairs, with shared-boundary length and
mean wall thickness) is in `meta/cells_L6.json`.

## A negative result worth recording

The plan to derive superblocks from **stroke thickness** (merge cells across thin walls, keep
thick boulevards as boundaries) **fails**: the map renders 75% of all streets at a nearly
uniform ~25 px (10.5 m) stroke; only the top ~10% are thicker. At any threshold the thin walls
percolate — one 20 km² component swallows the band. Major-artery structure in this artwork is
*not* encoded in line weight alone; it had to be brought in from geographic knowledge
(see Phase 3).
