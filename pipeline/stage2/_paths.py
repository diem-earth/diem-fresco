"""Shared repo-relative paths for the stage-2 decomposition pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # repo root
MASTER = ROOT / 'diem_master_geometry_v1.tiff'      # canonical raster (never modified)
SOURCES = ROOT / 'pipeline' / 'sources'             # frozen external data snapshots
CKPT = ROOT / 'pipeline' / 'stage2' / 'checkpoints' # small committed decision/derived JSONs
WORK = ROOT / 'pipeline' / 'stage2' / 'work'        # heavy regenerable intermediates (gitignored)
OUT = ROOT / 'decomposition'                        # stage-2 deliverables

WORK.mkdir(parents=True, exist_ok=True)

M_PER_PX = 0.4219   # from georeference (1:5000 at 300 dpi)
CANVAS = (34048, 5312)
