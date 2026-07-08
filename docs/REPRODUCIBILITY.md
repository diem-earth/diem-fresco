# Reproducibility

## What is bit-reproducible today

| Artifact | How to rebuild | Status |
|---|---|---|
| `diem_master_geometry_v1.tiff` | `python qa/reproduce_master.py` (needs `canny_final.tiff`) | **verified** — script self-checks every removed component and was re-run against the shipped master |
| `decomposition/meta/*` and `decomposition/masks/*` | `pipeline/stage2/s05…s07` from committed checkpoints | **verified as-run** — these three scripts are the exact session scripts (paths adapted) |
| checkpoints themselves | `pipeline/stage2/s01…s04` | **consolidated** — see caveat below |

## The honest caveat on s01–s04

Steps 01–04 originally ran as interactive session code on 2026-07-08. The committed
scripts are a faithful consolidation of that code (same algorithms, same parameters,
same constants), but they were not themselves executed end-to-end after consolidation.
The authoritative record of what those steps produced is the **committed checkpoints**
(`pipeline/stage2/checkpoints/*.json`) — later steps run from these, so full
deliverable regeneration does not depend on s01–s04 at all.

If you re-run s01–s04, compare the regenerated checkpoints against the committed ones
(`git diff`); expected differences are none, but OpenCV version changes could permute
connected-component label order (cell *numbering*, not geometry).

## Frozen external data

`pipeline/sources/` snapshots everything fetched from the network (2026-07-08):

- `arrondissements.geojson`, `quartiers.geojson` — opendata.paris.fr exports
- `major_roads.json`, `secondary_roads.json`, `parks.json`, `rail.json` — Overpass API
  extracts (bbox 48.828–48.895 N, 2.270–2.425 E)

These are committed precisely because live re-fetches drift: OSM edits change road
classifications weekly. **Never re-fetch and silently overwrite** — if an update is
needed, commit it as a new dated snapshot and rebuild the decomposition deliberately.

(Operational note: the Overpass API rejected POST from this network; use GET with an
explicit User-Agent.)

## Hardcoded knowledge in the pipeline (by design)

- Georef anchor plazas and their lon/lat (s02) — from public knowledge, ±10–20 m.
- Seine/Arsenal centerline waypoints, island footprint hulls, curated plaza list (s04).
- Thresholds: ink `<255`, cell min 50 px, water vote ≥3, bridge area <80 000 px,
  cut fraction >0.55, crumb absorption <2.5 ha.

Changing any of these is a *design change*, not a rebuild — document it in the phase
reports if you do.

## Environment

- Python 3.12.13 via `uv venv`; packages: numpy 2.x, opencv-python-headless 4.x,
  pillow 11.x, scikit-image 0.26, scipy 1.18, shapely 2.1.2, tifffile 2026.6.1.
- 16 GB RAM is sufficient (the partition step peaks ≈ 3 GB).
- No GPU required.
