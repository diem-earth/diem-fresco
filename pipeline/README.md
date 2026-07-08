# pipeline/

Everything needed to regenerate the derived artifacts of this repository.

- `sources/` — **frozen snapshots** of external data (Paris Open Data arrondissements &
  quartiers; OSM roads/parks/rail via Overpass, extracted 2026-07-08). Committed because
  live re-fetches drift over time. Never overwrite silently — add a new dated snapshot
  and rebuild deliberately.
- `stage2/` — the decomposition pipeline, run in order `s01 → s07`
  (`python s01_partition.py` etc., from inside this directory).
  - `checkpoints/` — small committed JSON records of every decision and derived table
    (georeference, special cells, level assignments, superblocks, adjacency).
    Steps s05–s07 rebuild all of `decomposition/` from these alone.
  - `work/` — heavy regenerable intermediates (`partition_L6.npy`, cut masks).
    Gitignored; recreated by s01/s03/s04 in ~30 min total.

Stage-1 (master geometry) reproduction lives in `../qa/reproduce_master.py`.

See `../docs/REPRODUCIBILITY.md` for verification status and caveats.
