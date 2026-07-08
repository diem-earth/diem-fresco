# Phase 3 — Multi-Scale Decomposition

Seven nested levels. Every level is expressed in the same currency — **sets of the 2 560 atomic
cells** — so all masks compose exactly, boundaries always follow real drawn streets, and any
region at any level is the pixel-exact union of its children.

| Level | Name | Regions | Construction |
|---|---|---|---|
| L0 | Canvas | 1 | the band itself |
| L1 | Macro geography | 9 | graph reachability after removing water+bridge cells → Rive Droite (2 212 cells), Rive Gauche (181), La Seine (57 segments), Île de la Cité (39), Île Saint-Louis (20), bridges (38), pockets (11), 2 exterior margins |
| L2 | Arrondissements | 16 | official Paris Open Data polygons projected through the georeference; each cell assigned by centroid → **cell-snapped** boundaries |
| L3 | Quartiers | 47 | same method, official 80-quartier layer |
| L4 | Semantic units | 28 | overlay layer: named OSM parks/cemeteries ≥1 ha (Tuileries, Père-Lachaise, Palais-Royal, Nelson-Mandela, Arsenal…), surface rail corridors (Gare de Lyon fan), 12 curated plazas (Étoile, Concorde, Vendôme, Bastille, Nation…), islands, the Seine, bridge decks |
| L5 | **Superblocks** | 81 | cell-adjacency graph **cut along OSM major roads** (motorway/trunk/primary/secondary, 4 015 ways, rasterized ±30 px corridors); islands kept separate; fragments < 2.5 ha absorbed into the neighbor with the longest shared boundary; water+bridges grouped as one *seine_corridor* unit |
| L6 | Atomic cells | 2 560 | enclosed street cells from Phase 2 |

## Why this construction

- **Cell-snapping (L2/L3)**: raw administrative polygons cut through the middle of blocks
  (georef tolerance ±16 m, plus boundaries legally run mid-street). Assigning whole cells by
  centroid makes every administrative mask follow the drawn street walls — no half-buildings,
  no seams through blocks. The exact projected polygons remain available in the georeference
  for semantic lookup.
- **Graph cuts instead of line thickness (L5)**: measured stroke width is uniform for 75% of
  streets (Phase 2), so the artwork itself does not encode road hierarchy — external knowledge
  (OSM road classes) supplies it. Cuts are applied to cell *adjacencies* whose shared wall lies
  ≥55% inside a major-road corridor, so superblock boundaries are exactly the major avenues as
  drawn in the raster.
- **Islands and Seine as first-class units**: they are the strongest visual identities of the
  band and must never be absorbed into a bank tile.
- **Bridge decks isolated**: without this, thin bridge parapets would merge the two banks into
  one region and destroy the macro structure.

## Size statistics (L5 superblocks, excluding corridor/exterior)

- count: 78 (68 bank + 10 island) · median 13.2 ha · p90 ≈ 60 ha · max 2.37 km²
- median superblock ≈ 800 × 800 px at full resolution — a comfortable single-generation tile.
- quartier purity (fraction of cells in the dominant quartier): recorded per superblock in
  metadata; median = 0.92 — superblocks inherit clean semantic identities.

## Deliverables map

- `masks/labelmaps/` — full-resolution label maps (L1, L2, L3, L4, L5 8/16-bit + L6 16-bit) with code tables
- `masks/L1_macro/ … L5_superblocks/` — 179 individual binary PNG masks (1-bit, full resolution)
- `masks/svg/` — polygonal outlines for L1/L2/L5 in master pixel coordinates (derived; raster canonical)
- `masks/ink_mask.png` — the linework itself, for clipping strokes to regions
- `meta/regions_L0_L5.json` — every region: id, level, type, name, area (px/m²), centroid
  (px + lon/lat), bbox, parent, neighbors with shared-boundary lengths
- `meta/cells_L6.json` — all 2 560 cells with the same fields plus per-cell L1–L5 identities
- `meta/georeference.json` — the lon/lat ↔ pixel transform
- `viz/` — annotated Phase-1 map, per-level colored maps with IDs, L5 adjacency graph, hierarchy diagram
