#!/usr/bin/env python3
"""Automated test: curated fields survive prompt-table rebuilds exactly.

Procedure (self-cleaning — never leaves dummy data in the tables):
  1. byte-backup the three table JSONs;
  2. inject recognizable sentinel values into the curated blocks of one
     representative center, extremity and seam record (including a
     generation-margin override, to prove derived windows react);
  3. run the builder;
  4. assert every sentinel survived exactly and the overridden margin
     produced the expected derived generation window;
  5. in a finally-block, restore the original bytes and verify the restored
     tables contain no sentinel.

Exit code 0 + "PASS" on success; any assertion failure restores the originals
before propagating.

Run:  python3 generation/scripts/test_curated_persistence.py
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "generation" / "prompt_tables"
BUILDER = ROOT / "generation" / "scripts" / "build_prompt_tables.py"
CONFIG = json.loads((ROOT / "generation" / "generation_config.json").read_text())

FILES = ["center_superblocks.json", "extremity_regions.json", "seam_ornaments.json"]
SENTINEL = "__CURATED_PERSISTENCE_TEST_7f3a9c__"
MARGIN_OVERRIDE = 123

INJECTIONS = {
    "center_superblocks.json": ("L5_sb001", {
        "concept_prompt": SENTINEL + "_concept",
        "render_prompt": SENTINEL + "_render",
        "identity_motifs": [SENTINEL + "_motif_a", SENTINEL + "_motif_b"],
        "materials": SENTINEL + "_materials",
        "generation_margin_override_px": MARGIN_OVERRIDE,
        "notes": SENTINEL + "_note",
    }),
    "extremity_regions.json": ("EXT_R_corse", {
        "concept_prompt": SENTINEL + "_concept",
        "atmosphere": SENTINEL + "_atmosphere",
        "identity_motifs": [SENTINEL + "_motif"],
        "continuity_notes": SENTINEL + "_continuity",
    }),
    "seam_ornaments.json": ("seam_left_laurel", {
        "branch_style": SENTINEL + "_style",
        "band_width_px": 777,
        "concept_prompt": SENTINEL + "_concept",
    }),
}


def load(fname):
    return json.loads((TABLES_DIR / fname).read_text())


def record(data, rid):
    return next(r for r in data["records"] if r["id"] == rid)


def run_builder():
    res = subprocess.run([sys.executable, str(BUILDER)], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"builder failed:\n{res.stdout}\n{res.stderr}")
    return res.stdout


def main():
    backups = {f: (TABLES_DIR / f).read_bytes() for f in FILES}
    try:
        # 1-2. inject sentinels into the current tables
        for fname, (rid, values) in INJECTIONS.items():
            data = load(fname)
            rec = record(data, rid)
            for k, v in values.items():
                assert k in rec["curated"], f"{fname}:{rid} curated has no key {k!r}"
                rec["curated"][k] = v
            (TABLES_DIR / fname).write_text(
                json.dumps(data, indent=1, ensure_ascii=False) + "\n")

        # 3. rebuild
        run_builder()

        # 4. verify survival
        for fname, (rid, values) in INJECTIONS.items():
            rec = record(load(fname), rid)
            for k, v in values.items():
                got = rec["curated"][k]
                assert got == v, f"{fname}:{rid}.curated.{k}: {got!r} != {v!r}"

        # margin override must drive the derived window
        rec = record(load("center_superblocks.json"), "L5_sb001")
        g = rec["geometry"]
        assert g["effective_margin_px"] == MARGIN_OVERRIDE, g["effective_margin_px"]
        assert g["margin_source"] == "curated_override", g["margin_source"]
        x0, y0, x1, y1 = g["bbox_px_global"]
        W = CONFIG["canvas"]["width_px"]; H = CONFIG["canvas"]["height_px"]
        expected = [max(0, x0 - MARGIN_OVERRIDE), max(0, y0 - MARGIN_OVERRIDE),
                    min(W - 1, x1 + MARGIN_OVERRIDE), min(H - 1, y1 + MARGIN_OVERRIDE)]
        assert g["gen_window_px_global"] == expected, \
            f"window {g['gen_window_px_global']} != {expected}"

        # sentinel must survive into the derived CSV view too
        csv_text = (TABLES_DIR / "center_superblocks.csv").read_text()
        assert SENTINEL + "_concept" in csv_text, "sentinel missing from center CSV"

        print("PASS  curated persistence: all sentinels survived the rebuild; "
              f"margin override {MARGIN_OVERRIDE}px drove the derived window")
    finally:
        # 5. restore originals byte-exactly and rebuild the derived CSVs to match
        for f, data in backups.items():
            (TABLES_DIR / f).write_bytes(data)
        run_builder()
        for f in FILES + ["center_superblocks.csv", "extremity_regions.csv"]:
            assert SENTINEL not in (TABLES_DIR / f).read_text(), \
                f"sentinel leaked into restored {f}"
        print("CLEAN  originals restored; no sentinel remains in any table or CSV")


if __name__ == "__main__":
    main()
