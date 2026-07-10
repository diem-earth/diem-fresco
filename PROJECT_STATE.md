# PROJECT_STATE — Diem Fresco

*Snapshot: 2026-07-10 · repo `diem-earth/diem-fresco` · main @ `2855a4e` ·
tags `v0.1-master-geometry-decomposition` @ `0646dac`,
`v0.2-global-fresco-structure` @ `2855a4e`*

New session? Read [LLM_START_HERE.md](LLM_START_HERE.md) first.

## What the project is

A monumental printed fresco (canonical canvas 34 048 × 5 312 px; **physical
dimensions TBD** — historically discussed around 7 × 1.8 m, must be validated
with the print fabricator; the file's 300 dpi tag is a working assumption, not
an approved print resolution — see `production/specs/fresco.yaml`): the Paris
Centre street network (source map 1:5000, rotated 20.3° so the Grand Axis
Étoile→Concorde→Louvre→Bastille→Nation runs horizontally), flanked by two
panels tiling the remaining French regions as convex partial hexagons with
areas proportional to their real surfaces. Target pipeline:
`master geometry → decomposition → AI generation per region → compositing → print`.

## Repo structure

```
LLM_START_HERE.md · PROJECT_STATE.md      entry points (this file)
README.md                                  human overview
canny_final.tiff                           stage-0 input (rotated Canny extraction)
diem_master_geometry_v1.tiff / .png        CANONICAL center geometry — never modify
MASTER_GEOMETRY_REPORT.md · qa/            stage-1 report + proof + reproduce script
decomposition/                             stage-2: masks/ meta/ viz/ reports/
extremities/                               left/right region panels (self-contained)
pipeline/  sources/ (frozen external data) stage2/ (s01–s07 scripts + checkpoints/)
docs/      PIPELINE · REPRODUCIBILITY · DATA_PROVENANCE
imports/   (gitignored) original zip archives already integrated
```

## Validated artifacts (trust these)

| Artifact | Validation |
|---|---|
| `diem_master_geometry_v1.tiff` | byte-reproducible from `canny_final.tiff` via `qa/reproduce_master.py` (self-verifying, re-run 2026-07-07); only 8 743 artifact px differ from raw; street geometry untouched |
| `decomposition/masks/*` + `meta/*` | L1/L2/L3/L5 label maps each tile the canvas **pixel-exactly** (sums asserted = 180 862 976); L6 = 2 560-cell seamless partition; georef RMS 38 px ≈ 16 m verified against drawn avenues |
| `extremities/outputs/*/final_positions.json` | optimizer converged to 0.00% area error, all 12 regions, convexity + ≤155° angles hold; panel dims verified: 5 088 + 22 960 + 6 000 = 34 048 |

## Center pipeline status

- **Stage 0–1 DONE** — master geometry v1 (34 048 × 5 312, grayscale: black lines,
  7 AA levels). 24 artifact components removed, everything else byte-identical.
- **Stage 2 DONE** — seven-level decomposition:
  L0 canvas → L1 macro (banks/Seine/islands/bridges, 9) → L2 arrondissements (16) →
  L3 quartiers (47) → L4 semantic units (28: parks/plazas/rail/water) →
  L5 superblocks (78 avenue-bounded tiles + seine corridor) → L6 atomic cells (2 560).
  **Recommended generation hierarchy: generate at L5, condition prompts from L2/L3/L4,
  composite at L6** (rationale: `decomposition/reports/PHASE4_ARTISTIC_EVALUATION.md`).
- **Stage 3 planning EXISTS but is PROVISIONAL and UNCOMMITTED** (2026-07-10):
  `generation/prompt_tables/` (93 unit records: 78 superblocks + Seine corridor
  + 12 extremity regions + 2 seam ornaments), builder script, and
  `docs/STAGE3_GENERATION_PLAN.md` with 3 pilot zones. It still needs the
  artistic/schema refinement pass (see `docs/DELIVERABLES_ARCHITECTURE.md`,
  step B) before being committed. **No artistic image generation has started.**

## Extremities pipeline status

- **DONE (geometry).** Left panel 5 088 × 5 312: Bretagne, Normandie, Pays de la Loire,
  Centre-Val de Loire, Nouvelle-Aquitaine, Occitanie. Right panel 6 000 × 5 312:
  Hauts-de-France, Grand Est, AURA, Bourgogne-Franche-Comté, PACA, Corse.
  Masks (binary + RGBA) in `extremities/outputs/*/masks/`, panel-local coordinates.
- No artistic treatment of the region polygons exists yet (only geometry + masks).

## Deliverables architecture (2026-07-10 — prepared, UNCOMMITTED)

Three final deliverables, each with a dedicated layer (umbrella doc:
`docs/DELIVERABLES_ARCHITECTURE.md`):

1. **`production/`** — the final fresco: `specs/fresco.yaml` (draft v0;
   **physical print dimensions, effective dpi, substrate, profiles all TBD** —
   fabricator validation required) + previews/masters/print/validation
   placeholders.
2. **`public_export/`** — future public repo (planning only): allowlist model,
   `manifests/include_candidates.txt` (all entries provisional pending rights/
   privacy/IP review gates) + mandatory `exclude.txt`; fresh-history snapshot,
   never a filtered workbench history.
3. **`process_film/`** — manifest-driven process film:
   `manifest/stages.json` (12 stages, narrative order + chronology notes);
   MP4 is the primary output, GIFs derived. **The original pre-rotation Paris
   source map is still missing from the repo** — film stages s01–s02 are
   blocked on it, and its license gates all public derivatives.

Cross-cutting: `registry/artifacts.yaml` (roles canonical/derived/provisional/
archived). Everything above exists in the working tree only — commit sequence
A–E in `docs/DELIVERABLES_ARCHITECTURE.md`.

## Resolved decisions

- **Zigzag seam strategy (artistic, 2026-07-09)** — the center/extremity seams are
  *intentional ornamental transitions*, not a technical layering rule. Panels are
  generated inside their own masks, the fresco is composited from the parts, and the
  two zigzag seams are covered/sublimated with **ornamental branches: laurel (left
  seam), oak (right seam)** — a direct reference to the **Paris coat of arms**, turning
  each seam into a symbolic civic motif. Details in `docs/PIPELINE.md`. Branch artwork
  does not exist yet; masks and geometry unchanged.

## Open decisions

1. **Seam branches — implementation** (smaller, follows the resolved strategy above):
   exact branch style, scale, opacity, and generation method TBD. Sizing fact: the
   right branch must absorb ≈ 307 k px of map ink east of the right zigzag
   (left side nearly conflict-free, 0.12%).
2. **Stage-3 design** — prompt schema per L5 tile (metadata exists: quartier name,
   arrondissement, contained L4 landmarks, bounding avenues); generation model/tooling
   not chosen; inner-seam strategy sketched in PHASE4 (re-composite avenue strokes
   over joins between L5 tiles).
3. Minor: a few unnamed green spaces (Esplanade des Invalides, Champs-Élysées gardens)
   absent from L4 (OSM name-dependent); 11 "pocket" cells attached to the Seine corridor.

## Next recommended tasks

Follow the commit sequence in `docs/DELIVERABLES_ARCHITECTURE.md`:

1. **A** — commit the architecture layer (`production/`, `public_export/`,
   `process_film/`, `registry/`, docs, this file).
2. **B/C** — stage-3 artistic/schema refinement pass, then commit the refined
   `generation/` layer.
3. **D** — legacy regional-prompt import (⚠ source location unknown — the
   `fresco_building` archive contains no prompt files).
4. **E** — pilot generation (`L5_sb034`, Seine-corridor strip,
   `EXT_L_bretagne`) with film capture from the first accepted tile.
5. In parallel: resolve physical print dimensions with the fabricator; obtain
   the original pre-rotation Paris source map (and verify its license).

## Commands to inspect / reproduce

```bash
git lfs install                                  # required before clone/checkout
pip install numpy pillow opencv-python-headless scikit-image scipy shapely tifffile imageio

python qa/reproduce_master.py                    # rebuild master, self-verifies (needs canny_final.tiff)
cd pipeline/stage2 && python s05_assemble.py && python s06_masks.py && python s07_viz.py
                                                 # regenerate all decomposition deliverables from checkpoints
cd extremities && python optimize.py both        # re-run extremity optimization (must cd first)
```

Heavy intermediates (`pipeline/stage2/work/*.npy`) are gitignored; rebuild with
`s01_partition.py` (~15 min) → `s02` → `s03` → `s04` if you need them.
Reproducibility status per artifact: `docs/REPRODUCIBILITY.md`.

## Warnings / pitfalls (learned the hard way)

- **Tiny white holes inside strokes are geometry** (collapsed parallel-street channels).
  Never fill, despeckle, or morphologically close anything on the master.
- **Anti-aliasing is signal**: segment with ink = `value < 255`; the AA halo keeps
  near-touching parallel streets separated. Don't binarize the master.
- **Stroke thickness does not encode road hierarchy** — 75% of streets are drawn at a
  uniform ~25 px; thickness-based merging percolates into one 20 km² blob. Superblocks
  come from OSM major-road graph cuts instead.
- **Bridge decks must stay isolated** or the two Seine banks merge through parapets.
  Narrow island cells touch both Seine arms — classify islands by footprint polygon,
  not by water adjacency.
- `extremities/optimize.py` hardcodes relative `inputs/`/`outputs/` — run from inside
  `extremities/`.
- Right panel local→global: `global_x = local_x + 28 048`. Heights already match.
- Overpass API from this machine: **GET + explicit User-Agent** (POST returns 406).
  And never re-fetch over `pipeline/sources/` — snapshot new files instead.
- Label maps: L6 is 16-bit PNG (values 1–2 560); codes → region ids live in the
  adjacent `*_codes.json`. Areas in metadata: 1 px = 0.4219 m (1:5000 @ 300 dpi).
- OpenCV version changes may permute connected-component *numbering* (not geometry)
  if you re-run s01 — compare against committed checkpoints before trusting.
