# Phase 4 — Artistic Relevance & Recommended Hierarchy

Scoring: ● strong ◐ mixed ○ weak

| Level | Semantic coherence | Visual coherence | AI-generation suitability | Prompt consistency | Neighbor continuity |
|---|---|---|---|---|---|
| L1 macro (9) | ● iconic (banks/Seine/islands) | ● | ○ regions far too large to generate whole | ● trivial ("Right Bank Paris…") | ● few, natural water boundaries |
| L2 arrondissements (16) | ● strong cultural identity | ◐ big, heterogeneous | ○ 1–6 km² each — beyond tile budgets | ● excellent (each arr. has a style prior) | ◐ long straight admin joins |
| L3 quartiers (47) | ● precise, nameable (Marais → *Archives*, *Saint-Merri*…) | ◐ | ◐ 0.2–1.5 km², borderline | ● very good | ◐ |
| L4 semantic units (28) | ● highest (Tuileries, Étoile, Seine…) | ● self-contained set pieces | ● ideal as *special-treatment* zones | ● unique prompts per unit | ● isolated by design |
| **L5 superblocks (78+corridor)** | ◐→● inherits quartier identity (median purity 0.92) | ● bounded by real avenues on all sides | ● median 11 ha ≈ 800×800 px — single-pass scale | ● prompt = quartier name + L4 content + boulevard frame | ● boundaries are *streets*, the natural seam of a map fresco |
| L6 cells (2 560) | ○ individually anonymous | ● atomic | ○ far too small/many for generation | ○ | ● perfect (walls are shared strokes) |

## Recommendation — a three-tier driving hierarchy

**Generate at L5, condition from L1/L2/L3/L4, composite at L6.**

1. **L1 + L4 set the global score.** Use L1 to define the band's three tonal worlds (Rive
   Droite / Seine corridor / Rive Gauche) and L4 to reserve the ~28 set pieces (Étoile,
   Concorde, Tuileries, the islands, Père-Lachaise…) for dedicated treatment. This guarantees
   the fresco reads correctly from across the room.

2. **L5 superblocks are the generation unit.** Each of the 78 tiles is bounded by major
   avenues — the most defensible seam in a street-map artwork, because a seam *on* a wide
   drawn street is visually absorbed by the stroke itself. Median tile ≈ 800×800 px at full
   resolution fits current image-model canvases without tiling artifacts. Prompt template:
   *quartier name (L3 parent) + arrondissement character (L2) + contained L4 units + the
   bounding boulevards* — all available directly from the metadata. Purity ≈ 0.9 means one
   prompt per tile stays truthful.

3. **L6 cells are the compositing currency.** Every L5 mask is an exact union of L6 cells, so
   blending, inpainting fixes, and later re-generation of any sub-area can be clipped
   cell-exactly without touching neighbors. The seamless partition guarantees no orphan pixels
   between adjacent generations.

Administrative levels L2/L3 should **not** drive generation directly (too large, and their
straight boundary joins are the worst possible seams) — their role is semantic conditioning
and human navigation of the project ("show me the Marais").

## Continuity strategy between neighboring L5 tiles

- The adjacency graph (`meta/regions_L0_L5.json`, `viz/L5_adjacency_graph.png`) lists every
  neighbor pair with shared-boundary length — the exact edge budget for overlap/feathering.
- Because seams lie on major avenues, a thin dilated band of the avenue stroke (from
  `ink_mask.png`) can be re-composited *over* both tiles after generation, visually stitching
  any residual tone mismatch under black linework.
- The Seine corridor is one continuous unit spanning the whole band — generate it once (or in
  long overlapping strips) so the river never changes character mid-stream; bridge decks are
  separate masks that overlay both river and banks cleanly.

## Known limitations (documented, acceptable)

- Georef tolerance ≈ 16 m RMS: cell-snapped admin boundaries can differ from legal boundaries
  by up to ~1 block where the boundary runs mid-block; irrelevant artistically.
- 11 "pocket" cells (enclaves like Vert-Galant) are attached to the Seine corridor or kept as
  single-cell units — check them if they ever appear as visible artifacts.
- L4 park list is OSM-name-dependent: a few unnamed green spaces (Esplanade des Invalides,
  Jardin des Champs-Élysées segments) are not auto-captured; they can be added by the same
  polygon → cells mechanism at any time.
- The 12e figure includes no Bois de Vincennes content: the drawn map correctly stops at the
  périphérique; the blank far-east canvas is `exterior`.
