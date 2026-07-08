# Diem — Multi-Scale Decomposition of the Master Geometry

Stage 2 of the pipeline. Input: `../diem_master_geometry_v1.tiff` (canonical, **not modified
by this stage** — verified). Output: a seven-level, cell-composable decomposition of the Paris
Centre band for constrained AI generation.

## TL;DR

- The map is a **1:5000, 20.3°-rotated band along the Grand Axis Étoile→Nation** (Phase 1 report).
- The network closes into **2 560 atomic cells** with zero repairs to the master (Phase 2).
- Seven levels, all defined as sets of atomic cells, so **every mask at every level composes
  pixel-exactly** (Phase 3).
- **Recommended driving hierarchy: generate at L5 superblocks (78 tiles bounded by real
  avenues), condition prompts from L2/L3/L4 identities, composite at L6 cells** (Phase 4).

## Layout

```
reports/   PHASE1_UNDERSTANDING.md   what the map is, landmarks, fidelity
           PHASE2_TOPOLOGY.md        closure, AA analysis, no-repair conventions
           PHASE3_DECOMPOSITION.md   the seven levels and how each was built
           PHASE4_ARTISTIC_EVALUATION.md  scoring + recommended hierarchy
meta/      regions_L0_L5.json        185 regions: geometry, names, parents, neighbors
           cells_L6.json             2 560 cells: geometry, L1–L5 identity, neighbors
           georeference.json         lon/lat <-> pixel transform (RMS 38 px)
masks/     labelmaps/                full-res label maps + code tables (L1–L6)
           L1_macro/ … L5_superblocks/   179 binary full-res PNG masks
           svg/                      L1/L2/L5 outlines (pixel coordinates)
           ink_mask.png              the linework, for clipping strokes
viz/       phase1_annotated_map.png  landmarks + arrondissement overlay
           L1…L5_map.png             colored level maps with region IDs
           L5_adjacency_graph.png    superblock neighbor graph
           hierarchy_diagram.svg     the seven-level pyramid
```

## Conventions

- Region ids: `L{level}_{name}` (e.g. `L2_arr04`, `L3_q13`, `L5_sb027`); cells are `L6_c0001`–`L6_c2560`.
- Label maps: PNG value = code; `*_codes.json` maps code → region id. 0 is unused/outside.
- All coordinates are master-raster pixels (34 048 × 5 312); lon/lat provided via the georeference.
- Areas: `area_px` = seamless-partition area (cell + owned half-walls); `open_area_px` = white
  space only (L6). 1 px = 0.4219 m.
- Sources: arrondissements & quartiers — opendata.paris.fr; major/secondary roads, parks,
  rail — OpenStreetMap (Overpass, 2026-07). The raster remains the only geometric authority.
```
