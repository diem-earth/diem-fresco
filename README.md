# Diem Fresco — Paris Centre

> New AI session? Start with [LLM_START_HERE.md](LLM_START_HERE.md).

Canonical repository for the **Diem fresco**: a 2.88 m × 0.45 m printed artwork
(34 048 × 5 312 px, 300 dpi) composed of **three panels** — the street network of central
Paris (1:5000, rotated so the Grand Axis **Étoile → Concorde → Louvre → Bastille → Nation**
runs horizontally) flanked by two convex partial-hexagon tilings of the surrounding
French regions, their areas proportional to real surfaces (left 5 088 px: western
regions; right 6 000 px: eastern regions; zigzag interfaces hugging the périphérique).
The two zigzag seams will be sublimated by ornamental branches — laurel (left) and
oak (right) — echoing the Paris coat of arms (see [docs/PIPELINE.md](docs/PIPELINE.md)).

Pipeline: `master geometry → multi-scale decomposition → AI generation → compositing → print`
for the center; the extremity panels are finished geometry
(see [docs/PIPELINE.md](docs/PIPELINE.md) for the full architecture and how panels join).

## The two ground truths

| File | Role |
|---|---|
| [`diem_master_geometry_v1.tiff`](diem_master_geometry_v1.tiff) | **Canonical geometry.** Black linework on white, 9 gray levels (7 anti-aliasing). Never modify; every later stage derives from it. |
| [`decomposition/`](decomposition/) | **Canonical segmentation.** Seven nested levels (L0 canvas → L6 atomic cells), 179 pixel-exact masks, full metadata + adjacency + georeference. |

Recommended generation hierarchy (from
[PHASE4_ARTISTIC_EVALUATION](decomposition/reports/PHASE4_ARTISTIC_EVALUATION.md)):
**generate at L5 superblocks (78 avenue-bounded tiles), condition prompts from
L2 arrondissements / L3 quartiers / L4 landmarks, composite at L6 cells.**

## Repository layout

```
canny_final.tiff                 stage-0 input (rotated Canny extraction, 2025-11-19)
diem_master_geometry_v1.tiff     stage-1 canonical master  (+ .png twin)
MASTER_GEOMETRY_REPORT.md        stage-1 report (what was cleaned and why)
qa/                              stage-1 proof: removal manifest, before/after, reproduce_master.py
decomposition/                   stage-2 deliverables: masks/ meta/ viz/ reports/
extremities/                     left/right region panels: optimize.py, inputs/, outputs/
                                 (final_positions.json = canonical panel geometry)
pipeline/
  sources/                       frozen external data (Paris Open Data, OSM 2026-07)
  stage2/                        s01…s07 pipeline scripts + checkpoints/ (decision records)
docs/                            PIPELINE.md · REPRODUCIBILITY.md · DATA_PROVENANCE.md
```

## Working rules

1. **Never edit the master TIFF or the mask label maps by hand.** Rebuild via the
   pipeline; every derived artifact must stay regenerable.
2. Geometry traps documented in the reports — read before touching anything:
   the tiny white holes inside strokes are collapsed parallel-street channels
   (never despeckle/fill); bridge decks must stay isolated from bank regions.
3. External data is snapshot-committed; never silently re-fetch
   (see [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md)).
4. Binary rasters are tracked with **Git LFS** — run `git lfs install` once before cloning.

## Quick start

```bash
git lfs install
git clone git@github-diem:diem-earth/diem-fresco.git
cd diem-fresco
python -m venv .venv && source .venv/bin/activate
pip install numpy pillow opencv-python-headless scikit-image scipy shapely tifffile
python qa/reproduce_master.py          # verify the master rebuilds bit-exact
```
