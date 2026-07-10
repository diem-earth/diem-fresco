# LLM START HERE — Diem Fresco

You are in the canonical repo of the **Diem fresco**: a monumental printed artwork
(physical dimensions TBD), one canvas of **34 048 × 5 312 px** (file metadata
300 dpi — a working assumption, not the print resolution), composed of three panels:

```
x: 0        5088                        28048        34048
   ┌─────────┬───────────────────────────┬────────────┐
   │  LEFT   ⟩   CENTER — Paris Centre   ⟨   RIGHT    │
   │ regions ⟩   street map (1:5000)     ⟨  regions   │
   └─────────┴───────────────────────────┴────────────┘
```

Center = Paris street network (Grand Axis Étoile→Nation horizontal).
Left/right = convex partial-hexagon tilings of the other French regions,
polygon areas proportional to real surfaces.

## Read in this order (≈3 min)

1. [PROJECT_STATE.md](PROJECT_STATE.md) — current status, open decisions, next tasks
2. [docs/PIPELINE.md](docs/PIPELINE.md) — full architecture + how panels join
3. Only when needed: `MASTER_GEOMETRY_REPORT.md`, `decomposition/reports/PHASE1–4*.md`,
   `extremities/README.md`, `docs/REPRODUCIBILITY.md`, `docs/DATA_PROVENANCE.md`

## The five hard rules

1. **Never modify `diem_master_geometry_v1.tiff`** (or `canny_final.tiff`). All geometry
   derives from the master. Never resize, crop, or re-render it.
2. **Never despeckle/fill the tiny white holes inside strokes** — they are collapsed
   1–2 px channels between parallel streets (real geometry, not noise).
3. **Masks compose from cells.** Every region at every level is a set of the 2 560
   atomic L6 cells; build new regions as cell unions, never by drawing polygons.
4. **Don't re-derive geometry ad hoc** — consume `decomposition/meta/*.json` and
   `decomposition/masks/`. For extremities, `extremities/outputs/*/final_positions.json`
   is the source of truth (right panel: `global_x = local_x + 28 048`).
5. **Never silently re-fetch external data** — `pipeline/sources/` is a frozen snapshot
   (OSM drifts). New snapshot = new dated files + deliberate rebuild.

## Instant orientation commands

```bash
git log --oneline            # project history (small, each commit = a stage)
cat PROJECT_STATE.md         # status snapshot

# load the decomposition metadata (plain python):
python3 -c "
import json
r = json.load(open('decomposition/meta/regions_L0_L5.json'))
sb = r['L5_sb001']
print(len(r), 'regions | L5_sb001:', sb['area_m2'], 'm2, parent', sb['parent'],
      '| neighbors:', len(sb['neighbors']))"
```

Git LFS is required (`git lfs install`) — all rasters/GIFs are LFS pointers.
