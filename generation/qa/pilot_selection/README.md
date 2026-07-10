# pilot_selection/ — technical QA boards for the stage-3 pilots

Deterministic technical boards for pilot **selection and QA — not
aesthetics**. Built exclusively from existing geometry, masks and metadata
(read-only); regenerate any time with:

```bash
python3 generation/scripts/build_pilot_qa_boards.py
```

| File | Pilot |
|---|---|
| `board_L5_sb034.png` | dense center tile — Arts-et-Métiers (3e) |
| `board_seine_strip.png` | Seine corridor strip (v0 extent + proposed revision) |
| `board_EXT_L_bretagne.png` | extremity region — Bretagne (left panel) |
| `pilot_summary.json` | machine-readable summary of all three (windows, margins, masks, findings) |

Each board shows: full-fresco locator (1/16), detail view (master + unit +
neighbor masks + tight bbox + generation window at the default margin), the
raw unit mask crop, and the unit's ids/dimensions/coordinate-space/context
metadata.

## Findings (2026-07-10)

- **Seine strip**: **x ∈ [13 500, 20 200] APPROVED (2026-07-10)** as the
  canonical Stage 3 pilot strip. History: the initial extent
  x ∈ [13 500, 19 500] clipped Île Saint-Louis (footprint reaches
  x = 20 013) and was superseded on approval; both extents remain in the
  board and summary for provenance.
- **Mask polarity**: extremity masks are region-black-on-white — the
  opposite of the L5 masks. Recorded as `assets.mask_polarity` in the prompt
  tables; consumers must normalize.
- `EXT_L_bretagne` window is wide/shallow (2643 × 937, ~2.8:1); workable,
  noted for model selection.
- `L5_sb034` is clean (single quartier, 6 neighbors, 1550 × 1132 window) —
  no issues.
