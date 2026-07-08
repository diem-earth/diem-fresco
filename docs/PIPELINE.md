# Diem Fresco — Pipeline Map

## Full fresco architecture (three panels, one canvas)

The fresco is a single 34 048 × 5 312 px canvas (300 dpi ≈ 2.88 × 0.45 m) composed of
three panels:

```
x: 0        5088                        28048        34048
   ┌─────────┬───────────────────────────┬────────────┐
   │  LEFT   ⟩   CENTER — Paris Centre   ⟨   RIGHT    │   height 5312
   │ regions ⟩   street network (1:5000) ⟨  regions   │
   └─────────┴───────────────────────────┴────────────┘
     extremities/        (this repo:         extremities/
     outputs/left     master + decomposition)   outputs/right
```

- **Center** — the Paris Centre street map (`diem_master_geometry_v1.tiff`) and its
  seven-level decomposition (`decomposition/`). Stages 1–2 below.
- **Extremities** (`extremities/`) — two convex partial-hexagon tilings representing the
  French regions around Paris: left panel 5 088 × 5 312 (Bretagne, Normandie,
  Pays de la Loire, Centre-Val de Loire, Nouvelle-Aquitaine, Occitanie), right panel
  6 000 × 5 312 (Hauts-de-France, Grand Est, Auvergne-Rhône-Alpes,
  Bourgogne-Franche-Comté, PACA, Corse). Each polygon's pixel area is proportional to
  the region's real-world surface (optimized to 0.00% error by `extremities/optimize.py`).

**Coordinate mapping.** Left panel: local == global pixels. Right panel:
`global_x = local_x + 28 048` (34 048 − 6 000). Heights match exactly.

**Zigzag interfaces.** Each panel's center-facing edge is a fixed zigzag polyline
(vertices in `extremities/outputs/*/final_positions.json`):
left `(4707,0)→(4078,1531)→(4118,2481)→(3741,3547)→(3408,5311)`;
right (global) `(28172,0)→(28235,458)→(28884,1523)→(28806,2358)→(29418,3674)→(29527,5311)`.
Measured against the master raster: only **0.12%** of map ink lies west of the left
zigzag (it hugs the périphérique), but **1.03% of map ink (~307 k px — the Porte de
Vincennes / eastern périphérique area) lies east of the right zigzag**.

> **⚠ Open compositing decision (unresolved by design):** how the right panel and the
> map's eastern overflow coexist — panel-over-map (streets hidden), map-over-panel
> (streets drawn across the region tiling), masking the map at the zigzag, or a blend.
> The left side is effectively conflict-free. Decide at the compositing stage and
> record the choice here.

## Center pipeline (stages 0–2)

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

## Extremities pipeline (`extremities/`)

Self-contained, fully reproducible optimization (imported 2026-07-08 from the
`fresco_building` project; layout preserved verbatim):

| Artifact | Meaning |
|---|---|
| `optimize.py` | multi-phase solver (L-BFGS-B ⇄ Nelder-Mead): 8 movable vertices/panel, convexity + ≤155° angle constraints, areas → real region proportions |
| `inputs/{left,right}/` | starting partition (`whole.png`), annotated vertex map, original region masks (incl. `07-Reste.png`, the leftover center-side zone of the starting partition) |
| `outputs/{left,right}/final_positions.json` | **canonical panel geometry**: all vertex coordinates, per-region fractions, angles |
| `outputs/{left,right}/masks/` | per-region masks in panel-local coordinates (binary + transparent RGBA) |
| `outputs/{left,right}/*.gif` | convergence animations (documentation, regenerable) |

Rebuild everything: `pip install -r extremities/requirements.txt && python extremities/optimize.py both`
(run from inside `extremities/` — the script uses relative `inputs/`/`outputs/` paths).

Consumers should treat `final_positions.json` as the geometric source of truth for the
panels and remap masks to global fresco coordinates via the offsets above.

## Data flow contracts

- The **raster master is the only geometric authority**. SVGs are derived conveniences.
- All decomposition levels are sets of the 2 560 atomic cells → masks compose pixel-exactly.
- Downstream stages should consume `decomposition/meta/*.json` + `decomposition/masks/`,
  never re-derive geometry from the TIFF ad hoc.
