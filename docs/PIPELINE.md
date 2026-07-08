# Diem Fresco — Pipeline Map

```
official Paris map (1:5000)                        [upstream, not in repo]
        │  rotation (−20.3°, Grand Axis horizontal) + Canny extraction
        ▼
canny_final.tiff                                   STAGE 0 input  (repo root)
        │  stage 1: surgical artifact removal (24 components, 8 743 px)
        │  → qa/reproduce_master.py rebuilds this deterministically
        ▼
diem_master_geometry_v1.tiff  ◄── CANONICAL GEOMETRY (never modified again)
        │  stage 2: pipeline/stage2/s01…s07
        ▼
decomposition/                                     STAGE 2 output
   masks/  meta/  viz/  reports/                   (7 levels, L0–L6)
        │  stage 3+ (future): zone prompts → AI generation → compositing → print
        ▼
        …
```

## Stage 1 — Master geometry

- Input `canny_final.tiff`, output `diem_master_geometry_v1.tiff` + `.png`.
- Every changed pixel documented in `qa/removal_manifest.csv`; rebuild with
  `qa/reproduce_master.py` (self-verifying — aborts on any deviation).
- Full rationale: `MASTER_GEOMETRY_REPORT.md`.

## Stage 2 — Multi-scale decomposition

Run order (see `docs/REPRODUCIBILITY.md` for caveats):

| Script | Produces | Time* |
|---|---|---|
| `s01_partition.py` | seamless 2 560-cell partition (`work/partition_L6.npy`), cell properties | ~15 min |
| `s02_georef_fit.py` | lon/lat↔px similarity transform | seconds |
| `s03_adjacency.py` | cell adjacency graph + major-road cut corridor | ~5 min |
| `s04_levels.py` | special cells, L1 macro, L2/L3 admin, L4 units, L5 superblocks | ~10 min |
| `s05_assemble.py` | `decomposition/meta/*.json` (regions, cells, georeference) | ~2 min |
| `s06_masks.py` | label maps + 179 binary masks + ink mask | ~15 min |
| `s07_viz.py` | level maps, adjacency overlay, SVG outlines, hierarchy diagram | ~5 min |

\* on a 16 GB M-series laptop.

Environment: Python ≥ 3.12 with `numpy pillow opencv-python-headless scikit-image scipy shapely tifffile`.

Design decisions and results: `decomposition/reports/PHASE1…PHASE4*.md`.

## Data flow contracts

- The **raster master is the only geometric authority**. SVGs are derived conveniences.
- All decomposition levels are sets of the 2 560 atomic cells → masks compose pixel-exactly.
- Downstream stages should consume `decomposition/meta/*.json` + `decomposition/masks/`,
  never re-derive geometry from the TIFF ad hoc.
