#!/usr/bin/env python3
"""Build the stage-3 prompt tables from stage-2 metadata.  (schema v0.2)

Deterministic: derived fields come only from
  decomposition/meta/regions_L0_L5.json
  decomposition/meta/cells_L6.json
  extremities/outputs/{left,right}/final_positions.json
  generation/generation_config.json   (default generation margin, canvas)

Curated fields (everything under each record's "curated" key) are preserved
across rebuilds: if an output JSON already exists, its curated blocks are
merged back in by record id — only keys belonging to the current curated
schema are accepted; legacy v0.1 keys are migrated (see MIGRATIONS) and any
dropped non-empty value is reported loudly.

Generation windows are DERIVED: bbox + effective margin, where the effective
margin is curated.generation_margin_override_px if set, else the global
default from generation_config.json. Changing an override requires a rebuild.

CSV files are derived, read-only views of the JSON — never hand-edit the CSVs.

Run from anywhere:  python3 generation/scripts/build_prompt_tables.py
"""

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
META = ROOT / "decomposition" / "meta"
OUT = ROOT / "generation" / "prompt_tables"
CONFIG_PATH = ROOT / "generation" / "generation_config.json"

SCHEMA_VERSION = "0.2"

# Documented in docs/PIPELINE.md (measured against the master raster).
SEAM_INK_OVERLAP = {
    "left": {"pct_of_map_ink": 0.12, "px": None},
    "right": {"pct_of_map_ink": 1.03, "px": 307000},
}

PALETTE_WORLD = {  # L1 macro id -> tonal world (a PROVISIONAL artistic grouping)
    "L1_right_bank": "rive_droite",
    "L1_left_bank": "rive_gauche",
    "L1_seine": "seine",
    "L1_ile_de_la_cite": "seine",
    "L1_ile_saint_louis": "seine",
    "L1_bridge": "seine",
    "L1_pocket": "seine",
    "L1_exterior_west": "exterior",
    "L1_exterior_east": "exterior",
}

PILOTS = {"L5_sb034", "L5_seine_corridor", "EXT_L_bretagne"}

# --------------------------------------------------------------------- curated

# Canonical curated schema — ALL human-authored artistic/editorial data lives
# here and survives rebuilds. Derived data must never be written into curated.
ARTISTIC_CURATED = {
    "status": "todo",          # todo|pilot|drafted|approved|generated|composited
    "pilot": False,
    "style_pack": "style_pack_v0",   # provisional hypotheses container (see plan)
    # -- prompt model: model-independent first --
    "concept_prompt": "",      # durable artistic/narrative intent, independent
                               # of any generation model or tool
    "render_prompt": "",       # operational prompt adapted to a specific model
    "negative_prompt": "",
    "model_config_ref": "",    # pointer to a model/tool config (none exist yet)
    "conditioning_assets": [], # repo-relative paths of conditioning inputs
    "generation_notes": "",
    # -- artistic direction (authored, not derived) --
    "identity_motifs": [],
    "secondary_motifs": [],
    "materials": "",
    "atmosphere": "",
    "color_direction": "",
    "density": "",
    "composition_notes": "",
    "continuity_notes": "",
    # -- technical override --
    "generation_margin_override_px": None,   # None -> config default
    "notes": "",
}

SEAM_CURATED = {
    "status": "blocked_on_design",
    "pilot": False,
    "style_pack": "style_pack_v0",
    "concept_prompt": "",
    "render_prompt": "",
    "negative_prompt": "",
    "model_config_ref": "",
    "conditioning_assets": [],
    "generation_notes": "",
    "branch_style": "",        # TBD — open decision (PROJECT_STATE.md)
    "band_width_px": None,     # TBD (right side must absorb ~307k px of ink)
    "opacity": None,           # TBD
    "generation_method": "",   # TBD: raster AI vs vector illustration
    "notes": "",
}

# v0.1 -> v0.2 key migrations (old_key -> new_key); applied only when the old
# value is non-empty. Unmapped legacy keys are dropped with a warning.
MIGRATIONS = {
    "prompt_final": "render_prompt",
}

_migration_log = []


def default_curated(kind, status="todo", pilot=False):
    base = SEAM_CURATED if kind == "seam_ornament" else ARTISTIC_CURATED
    c = json.loads(json.dumps(base))  # deep copy
    c["status"] = status
    c["pilot"] = pilot
    return c


def merge_curated(records, out_path):
    """Carry curated blocks over from an existing output file, by id.

    Only keys in the current curated schema are accepted; legacy keys are
    migrated via MIGRATIONS; dropped non-empty values are logged.
    Legacy context.iconography (v0.1, extremities) migrates to
    curated.identity_motifs.
    """
    if not out_path.exists():
        return
    old_records = json.loads(out_path.read_text())["records"]
    old = {r["id"]: r for r in old_records}
    for r in records:
        prev = old.get(r["id"])
        if not prev:
            continue
        cur = r["curated"]
        for k, v in prev.get("curated", {}).items():
            if k in cur:
                cur[k] = v
            elif k in MIGRATIONS:
                if v not in ("", None, []):
                    cur[MIGRATIONS[k]] = v
                    _migration_log.append(f"{r['id']}: {k} -> {MIGRATIONS[k]}")
            elif v not in ("", None, []):
                _migration_log.append(f"{r['id']}: DROPPED legacy curated.{k}={v!r}")
        legacy_icono = prev.get("context", {}).get("iconography")
        if legacy_icono and not cur.get("identity_motifs"):
            cur["identity_motifs"] = legacy_icono
            _migration_log.append(f"{r['id']}: context.iconography -> curated.identity_motifs")


def sha256_short(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def slugify(name):
    import unicodedata
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return "".join(ch if ch.isalnum() else "_" for ch in ascii_name.lower()).strip("_")


def block_grain(n_cells, area_ha):
    density = n_cells / area_ha if area_ha > 0 else float("inf")
    if density >= 1.2:
        return "fine"
    if density >= 0.5:
        return "medium"
    return "coarse"


def apply_gen_windows(records, cfg):
    """Derive effective margin + generation window AFTER curated merge."""
    default = cfg["default_generation_margin_px"]
    W, H = cfg["canvas"]["width_px"], cfg["canvas"]["height_px"]
    for r in records:
        g = r.get("geometry", {})
        if "bbox_px_global" not in g:
            continue
        override = r["curated"].get("generation_margin_override_px")
        margin = default if override is None else int(override)
        x0, y0, x1, y1 = (int(round(v)) for v in g["bbox_px_global"])
        win = [max(0, x0 - margin), max(0, y0 - margin),
               min(W - 1, x1 + margin), min(H - 1, y1 + margin)]
        g["effective_margin_px"] = margin
        g["margin_source"] = "default" if override is None else "curated_override"
        g["gen_window_px_global"] = win
        g["gen_window_size_px"] = [win[2] - win[0] + 1, win[3] - win[1] + 1]


# --------------------------------------------------------------------------- center

def build_center(regions, cells):
    l3_name = {k: v["name"] for k, v in regions.items() if k.startswith("L3_")}
    l2_name = {k: v["name"] for k, v in regions.items() if k.startswith("L2_")}
    l4_cells = {k: set(v.get("cells", [])) for k, v in regions.items() if k.startswith("L4_")}
    cell_by_idx = {}
    for c in cells.values():
        cell_by_idx[int(c["id"][len("L6_c"):])] = c

    records = []
    ids = sorted(k for k, v in regions.items()
                 if v.get("level") == 5 and v["type"] in ("superblock", "seine_corridor"))
    for rid in ids:
        r = regions[rid]
        own = set(r["cells"])
        area_ha = r["area_m2"] / 1e4

        world_area = {}
        l3_area = {}
        for i in own:
            c = cell_by_idx[i]
            world = PALETTE_WORLD.get(c["l1"], "exterior")
            world_area[world] = world_area.get(world, 0) + c["area_px"]
            l3_area[c["l3"]] = l3_area.get(c["l3"], 0) + c["area_px"]
        palette_world = "seine" if r["type"] == "seine_corridor" else \
            max(world_area, key=world_area.get)

        total = sum(l3_area.values())
        primary_q = r["parent"] if r["parent"].startswith("L3_") else None
        secondary = [{"id": q, "name": l3_name.get(q, q), "area_share": round(a / total, 3)}
                     for q, a in sorted(l3_area.items(), key=lambda kv: -kv[1])
                     if q != primary_q and q != "L3_outside" and a / total >= 0.05]

        overlays = []
        for uid, ucells in sorted(l4_cells.items()):
            if not ucells:
                continue
            frac = len(ucells & own) / len(ucells)
            if frac > 0:
                overlays.append({"id": uid, "name": regions[uid]["name"],
                                 "type": regions[uid]["type"],
                                 "frac_of_unit": round(frac, 3),
                                 "contained": frac >= 0.95})

        flags = []
        if r["n_cells"] == 1:
            flags.append("degenerate_single_cell")
        if r.get("quartier_purity", 1.0) < 0.7:
            flags.append("multi_quartier")
        if any(o["type"] == "island" and o["frac_of_unit"] > 0.3 for o in overlays):
            flags.append("island")
        if any(o["type"] == "rail" and o["frac_of_unit"] > 0.3 for o in overlays):
            flags.append("rail")
        if r["type"] == "seine_corridor":
            flags.append("continuous_band")

        neighbors = [{"id": n, "shared_px": px}
                     for n, px in sorted(r.get("neighbors", {}).items(), key=lambda kv: -kv[1])]
        grain = block_grain(r["n_cells"], area_ha)
        x0, y0, x1, y1 = r["bbox_px"]

        qname = l3_name.get(primary_q, "")
        aname = l2_name.get(regions.get(primary_q, {}).get("parent", ""), "")
        set_pieces = [o["name"] for o in overlays if o["contained"]]

        # Factual unit summary ONLY — no artistic direction (view, medium,
        # palette are open decisions; authored intent goes to curated fields).
        scaffold = (
            f"Unit facts: avenue-bounded block group, {qname} quartier"
            f"{' (' + aname + ')' if aname else ''}, Paris; {grain}-grain street mesh; "
            f"{r['n_cells']} L6 cells, {area_ha:.1f} ha"
            + (f"; contains {', '.join(set_pieces)}" if set_pieces else "")
            + f"; {len(neighbors)} neighboring units. Generated content fills only this "
              "unit's mask; the street linework is recomposited above it."
        ) if r["type"] == "superblock" else (
            "Unit facts: the Seine corridor — one continuous river band (quays included); "
            "islands and bridge decks are separate overlay masks. Continuity requirement: "
            "the water must not change character mid-stream, so generate as one unit or in "
            "long overlapping strips. Generated content fills only this unit's mask; the "
            "street linework is recomposited above it."
        )

        records.append({
            "id": rid,
            "kind": r["type"],
            "display_name": (f"{qname} · {rid[3:]}" if r["type"] == "superblock"
                             else "Seine corridor"),
            "geometry": {
                "bbox_px_global": r["bbox_px"],
                # effective_margin_px / gen_window_* are filled by
                # apply_gen_windows() after the curated merge
                "centroid_px_global": r["centroid_px"],
                "centroid_lonlat": r["centroid_lonlat"],
                "area_px": r["area_px"],
                "area_ha": round(area_ha, 2),
                "n_cells_l6": r["n_cells"],
            },
            "assets": {
                "mask_path": f"decomposition/masks/L5_superblocks/{rid}.png",
                "mask_coordinate_space": "global",
                "mask_polarity": "region_white_on_black",
                "cells_ref": "decomposition/meta/regions_L0_L5.json#" + rid,
            },
            "context": {
                "palette_world": palette_world,
                "l2_arrondissement": {"id": regions.get(primary_q, {}).get("parent"),
                                      "name": aname} if primary_q else None,
                "l3_quartier": {"id": primary_q, "name": qname} if primary_q else None,
                "quartier_purity": r.get("quartier_purity"),
                "secondary_quartiers": secondary,
                "l4_overlays": overlays,
                "block_grain": grain,
                "neighbors": neighbors,
                "touches_seine_corridor": any(n["id"] == "L5_seine_corridor" for n in neighbors)
                                          or r["type"] == "seine_corridor",
                "touches_canvas_edge": x0 <= 0 or y0 <= 0 or x1 >= 34048 - 1 or y1 >= 5312 - 1,
                "flags": flags,
            },
            "prompt_scaffold": scaffold,
            "curated": default_curated(
                r["type"], status="pilot" if rid in PILOTS else "todo",
                pilot=rid in PILOTS),
        })
    return records


# ----------------------------------------------------------------------- extremities

def build_extremities(left, right, cfg):
    offset_right = cfg["right_panel_offset_x"]
    records = []
    for side, data, offset in (("left", left, 0), ("right", right, offset_right)):
        verts = {**data["fixed_vertices"], **data["optimized_vertices"],
                 **data["implicit_corners"]}
        seam_names = set(data["fixed_vertices"])
        mask_dir = ROOT / "extremities" / "outputs" / side / "masks"
        mask_files = sorted(mask_dir.glob("mask_*.png")) if mask_dir.exists() else []

        region_verts = {r["name"]: set(r["vertices"]) for r in data["regions"]}
        for r in data["regions"]:
            slug = slugify(r["name"])
            rid = f"EXT_{side[0].upper()}_{slug}"
            poly_local = [[round(float(verts[v][0]), 1), round(float(verts[v][1]), 1)]
                          for v in r["vertices"]]
            poly_global = [[round(x + offset, 1), y] for x, y in poly_local]
            xs = [p[0] for p in poly_global]
            ys = [p[1] for p in poly_global]
            bbox = [min(xs), min(ys), max(xs), max(ys)]

            binary = next((m for m in mask_files
                           if slug in m.name and "transparent" not in m.name), None)
            rgba = next((m for m in mask_files
                         if slug in m.name and "transparent" in m.name), None)

            neighbors = sorted(n for n, vs in region_verts.items()
                               if n != r["name"] and len(vs & set(r["vertices"])) >= 2)
            touches_seam = bool(set(r["vertices"]) & seam_names)

            records.append({
                "id": rid,
                "kind": "extremity_region",
                "display_name": r["name"],
                "panel": side,
                "geometry": {
                    "polygon_px_local": poly_local,
                    "polygon_px_global": poly_global,
                    "bbox_px_global": bbox,
                    "area_px": r["pixel_area"],
                    "area_fraction_target": r["target_fraction"],
                    "area_fraction_achieved": r["achieved_fraction"],
                    "max_interior_angle_deg": r["max_angle_deg"],
                    "panel_offset_x": offset,
                },
                "assets": {
                    "mask_path": str(binary.relative_to(ROOT)) if binary else None,
                    "mask_rgba_path": str(rgba.relative_to(ROOT)) if rgba else None,
                    "mask_coordinate_space": "panel_local",
                    # NB: opposite polarity to the L5 masks (verified 2026-07-10)
                    "mask_polarity": "region_black_on_white",
                },
                "context": {
                    "palette_world": f"panel_{side}",
                    "neighbors_same_panel": neighbors,
                    "touches_zigzag_seam": touches_seam,
                    "seam_ornament": ("seam_left_laurel" if side == "left"
                                      else "seam_right_oak") if touches_seam else None,
                },
                "prompt_scaffold": (
                    f"Unit facts: {r['name']} — convex polygonal facet of the {side} panel, "
                    f"{r['achieved_fraction']:.1%} of panel area"
                    + (f"; borders {', '.join(neighbors)}" if neighbors else "")
                    + ("; touches the zigzag seam (ornament band reserved)" if touches_seam else "")
                    + ". Generated content fills only this region's mask. Identity, motifs "
                      "and treatment are authored in curated fields (legacy prompt import "
                      "pending — see generation/references/extremity_prompt_legacy/)."
                ),
                "curated": default_curated(
                    "extremity_region", status="pilot" if rid in PILOTS else "todo",
                    pilot=rid in PILOTS),
            })
    return records


# --------------------------------------------------------------------- seam ornaments

def build_seams(left, right, cfg):
    def polyline(data, offset):
        pts = sorted(data["fixed_vertices"].values(), key=lambda p: p[1])
        return [[p[0] + offset, p[1]] for p in pts]

    specs = [
        ("seam_left_laurel", "laurel", "left", polyline(left, 0)),
        ("seam_right_oak", "oak", "right", polyline(right, cfg["right_panel_offset_x"])),
    ]
    records = []
    for rid, motif, side, pts in specs:
        records.append({
            "id": rid,
            "kind": "seam_ornament",
            "display_name": f"{motif.capitalize()} branch — {side} seam",
            "motif": motif,
            "symbolism": "Paris coat of arms (laurel + oak wreath)",
            "panel_side": side,
            "geometry": {
                "zigzag_polyline_px_global": pts,
                "spans_full_height": True,
                "ink_overlap": SEAM_INK_OVERLAP[side] | {
                    "meaning": "map ink lying on the extremity side of the zigzag; the "
                               "branch must be wide enough to absorb it",
                    "source": "docs/PIPELINE.md (measured 2026-07-09)"},
            },
            "curated": default_curated("seam_ornament", status="blocked_on_design"),
        })
    return records


# ----------------------------------------------------------------------------- CSVs

def write_center_csv(records, path):
    cols = ["id", "kind", "display_name", "arrondissement", "quartier", "palette_world",
            "area_ha", "n_cells_l6", "block_grain", "quartier_purity", "l4_units",
            "n_neighbors", "touches_seine", "flags", "effective_margin_px", "pilot",
            "status", "concept_prompt", "render_prompt", "notes"]
    with path.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for r in records:
            c, g, cu = r["context"], r["geometry"], r["curated"]
            w.writerow([
                r["id"], r["kind"], r["display_name"],
                (c["l2_arrondissement"] or {}).get("name", ""),
                (c["l3_quartier"] or {}).get("name", ""),
                c["palette_world"], g["area_ha"], g["n_cells_l6"], c["block_grain"],
                c["quartier_purity"],
                "; ".join(o["name"] for o in c["l4_overlays"] if o["contained"]),
                len(c["neighbors"]), c["touches_seine_corridor"],
                "; ".join(c["flags"]), g["effective_margin_px"], cu["pilot"],
                cu["status"], cu["concept_prompt"], cu["render_prompt"], cu["notes"],
            ])


def write_extremity_csv(records, path):
    cols = ["id", "panel", "region", "area_fraction", "area_px", "touches_zigzag_seam",
            "neighbors_same_panel", "identity_motifs", "effective_margin_px", "pilot",
            "status", "concept_prompt", "render_prompt", "notes"]
    with path.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for r in records:
            g, c, cu = r["geometry"], r["context"], r["curated"]
            w.writerow([
                r["id"], r["panel"], r["display_name"], g["area_fraction_achieved"],
                g["area_px"], c["touches_zigzag_seam"],
                "; ".join(c["neighbors_same_panel"]),
                "; ".join(cu["identity_motifs"]), g["effective_margin_px"],
                cu["pilot"], cu["status"], cu["concept_prompt"], cu["render_prompt"],
                cu["notes"],
            ])


# ----------------------------------------------------------------------------- main

def main():
    regions_path = META / "regions_L0_L5.json"
    cells_path = META / "cells_L6.json"
    left_path = ROOT / "extremities" / "outputs" / "left" / "final_positions.json"
    right_path = ROOT / "extremities" / "outputs" / "right" / "final_positions.json"

    cfg = json.loads(CONFIG_PATH.read_text())
    regions = json.loads(regions_path.read_text())
    cells = json.loads(cells_path.read_text())
    left = json.loads(left_path.read_text())
    right = json.loads(right_path.read_text())

    OUT.mkdir(parents=True, exist_ok=True)
    provenance = {
        "schema_version": SCHEMA_VERSION,
        "sources": {
            "regions_L0_L5.json": sha256_short(regions_path),
            "cells_L6.json": sha256_short(cells_path),
            "left/final_positions.json": sha256_short(left_path),
            "right/final_positions.json": sha256_short(right_path),
            "generation_config.json": sha256_short(CONFIG_PATH),
        },
        "default_generation_margin_px": cfg["default_generation_margin_px"],
        "builder": "generation/scripts/build_prompt_tables.py",
    }

    tables = [
        ("center_superblocks.json", build_center(regions, cells)),
        ("extremity_regions.json", build_extremities(left, right, cfg)),
        ("seam_ornaments.json", build_seams(left, right, cfg)),
    ]
    for fname, records in tables:
        out_path = OUT / fname
        merge_curated(records, out_path)
        apply_gen_windows(records, cfg)   # after merge: overrides live in curated
        out_path.write_text(json.dumps(
            {"provenance": provenance, "n_records": len(records), "records": records},
            indent=1, ensure_ascii=False) + "\n")

    center, extrem, seams = (t[1] for t in tables)
    write_center_csv(center, OUT / "center_superblocks.csv")
    write_extremity_csv(extrem, OUT / "extremity_regions.csv")

    # sanity checks
    n_sb = sum(1 for r in center if r["kind"] == "superblock")
    assert n_sb == 78, f"expected 78 superblocks, got {n_sb}"
    assert sum(1 for r in center if r["kind"] == "seine_corridor") == 1
    assert len(extrem) == 12, f"expected 12 extremity regions, got {len(extrem)}"
    assert len(seams) == 2
    for panel in ("left", "right"):
        frac = sum(r["geometry"]["area_fraction_achieved"]
                   for r in extrem if r["panel"] == panel)
        assert abs(frac - 1.0) < 1e-3, f"{panel} fractions sum to {frac}"
    missing_masks = [r["id"] for r in extrem if not r["assets"]["mask_path"]]
    assert not missing_masks, f"unresolved extremity masks: {missing_masks}"
    for r in center + extrem:
        schema = SEAM_CURATED if r["kind"] == "seam_ornament" else ARTISTIC_CURATED
        assert set(r["curated"]) == set(schema), f"curated drift in {r['id']}"
        assert r["geometry"]["effective_margin_px"] >= 0
        assert "gen_window_px_global" in r["geometry"], f"no gen window: {r['id']}"
    for r in seams:
        assert set(r["curated"]) == set(SEAM_CURATED), f"curated drift in {r['id']}"

    pilots = [r["id"] for t in (center, extrem) for r in t if r["curated"]["pilot"]]
    print(f"OK  center={len(center)} (78 sb + corridor)  extremities={len(extrem)}  "
          f"seams={len(seams)}  margin_default={cfg['default_generation_margin_px']}px")
    print(f"    pilots: {', '.join(pilots)}")
    if _migration_log:
        print("    migrations/drops:")
        for line in _migration_log:
            print("      -", line)


if __name__ == "__main__":
    main()
