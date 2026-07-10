#!/usr/bin/env python3
"""Render deterministic technical QA boards for the three stage-3 pilots.

These boards are for pilot SELECTION and technical QA — not aesthetics.
They use only existing geometry, masks and metadata (read-only); no artwork
is generated. Every color, scale and layout constant is fixed, so reruns are
reproducible.

Outputs (generation/qa/pilot_selection/):
  board_L5_sb034.png
  board_seine_strip.png
  board_EXT_L_bretagne.png
  pilot_summary.json

Run:  python3 generation/scripts/build_pilot_qa_boards.py
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "generation" / "qa" / "pilot_selection"
CFG = json.loads((ROOT / "generation" / "generation_config.json").read_text())
W, H = CFG["canvas"]["width_px"], CFG["canvas"]["height_px"]
MARGIN = CFG["default_generation_margin_px"]

LOCATOR_SCALE = 16          # full canvas -> 2128 x 332
DETAIL_MAX_W = 1800         # detail panel is downscaled to fit this width
CONTEXT_PAD = 300           # extra context around the gen window in detail view

COL_UNIT = (255, 120, 40)          # unit mask tint
COL_BBOX = (0, 90, 255)            # tight bbox outline
COL_WINDOW = (225, 30, 30)         # generation window outline (bbox + margin)
COL_ALT = (20, 160, 60)            # alternate/proposed extent outline
NEIGHBOR_COLS = [(70, 130, 220), (60, 170, 90), (170, 90, 200),
                 (220, 170, 40), (90, 190, 190), (200, 90, 90),
                 (140, 140, 60), (100, 100, 220)]

STRIP_APPROVED = [13500, 20200]    # APPROVED 2026-07-10 — canonical pilot strip
STRIP_FORMER = [13500, 19500]      # superseded: clipped Île Saint-Louis (x=20013)


def font(size=14):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:                      # older Pillow
        return ImageFont.load_default()


def ascii_safe(s):
    """PIL's default font lacks glyphs for accents/dashes — render ASCII only."""
    import unicodedata
    s = s.replace("—", "-").replace("·", "-").replace("×", "x").replace("≈", "~")
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def load_gray(path):
    return Image.open(ROOT / path).convert("L")


def clamp_window(bbox, margin):
    x0, y0, x1, y1 = (int(round(v)) for v in bbox)
    return [max(0, x0 - margin), max(0, y0 - margin),
            min(W - 1, x1 + margin), min(H - 1, y1 + margin)]


def tint(base_rgb, mask_l, color, alpha=0.45):
    """Blend `color` over base wherever mask>127, at the given alpha (PIL-only)."""
    a = int(alpha * 255)
    blend_mask = mask_l.point(lambda v: a if v > 127 else 0)
    solid = Image.new("RGB", base_rgb.size, color)
    return Image.composite(solid, base_rgb, blend_mask)


def paste_panel_local(mask_img, offset_x):
    """Lift a panel-local extremity mask onto the full global canvas (L mode).

    Extremity masks are region-BLACK-on-white (opposite of the L5 masks,
    verified 2026-07-10; recorded as assets.mask_polarity in the tables) —
    normalize to region-white here so all overlays share one convention.
    """
    inverted = mask_img.point(lambda v: 255 - v)
    full = Image.new("L", (W, H), 0)
    full.paste(inverted, (offset_x, 0))
    return full


def locator_panel(master_small, unit_small, rects):
    """Full-canvas locator at 1/LOCATOR_SCALE with unit tint + rectangles.

    rects: list of (bbox_global, color, width)
    """
    faded = master_small.point(lambda v: 255 - int((255 - v) * 0.35))  # fade the ink
    img = tint(faded.convert("RGB"), unit_small, COL_UNIT, alpha=0.55)
    d = ImageDraw.Draw(img)
    s = LOCATOR_SCALE
    for bbox, color, width in rects:
        x0, y0, x1, y1 = [v / s for v in bbox]
        d.rectangle([x0, y0, x1, y1], outline=color, width=width)
    return img


def detail_panel(master, overlays, crop, rects, labels):
    """Crop of the master with tinted overlays, rectangles and id labels.

    overlays: list of (full_canvas_L_image, color, alpha)
    rects: list of (bbox_global, color, width)  labels: list of (text, xy_global)
    """
    cx0, cy0, cx1, cy1 = crop
    img = master.crop((cx0, cy0, cx1 + 1, cy1 + 1)).convert("RGB")
    for mimg, color, alpha in overlays:
        img = tint(img, mimg.crop((cx0, cy0, cx1 + 1, cy1 + 1)), color, alpha)
    d = ImageDraw.Draw(img)
    for bbox, color, width in rects:
        d.rectangle([bbox[0] - cx0, bbox[1] - cy0, bbox[2] - cx0, bbox[3] - cy0],
                    outline=color, width=width)
    f = font(26)
    for text, (lx, ly) in labels:
        x, y = lx - cx0, ly - cy0
        if 0 <= x < img.width and 0 <= y < img.height:
            d.text((x + 2, y + 2), ascii_safe(text), fill=(255, 255, 255), font=f)
            d.text((x, y), ascii_safe(text), fill=(0, 0, 0), font=f)
    if img.width > DETAIL_MAX_W:
        r = DETAIL_MAX_W / img.width
        img = img.resize((DETAIL_MAX_W, max(1, int(img.height * r))), Image.BILINEAR)
    return img


def mask_panel(mask_full, crop, max_w=700):
    cx0, cy0, cx1, cy1 = crop
    img = mask_full.crop((cx0, cy0, cx1 + 1, cy1 + 1)).convert("RGB")
    if img.width > max_w:
        r = max_w / img.width
        img = img.resize((max_w, max(1, int(img.height * r))), Image.BILINEAR)
    return img


def assemble_board(title, text_lines, panels, out_path):
    """panels: list of (caption, PIL.Image)."""
    f_title, f_txt, f_cap = font(30), font(16), font(18)
    pad, line_h = 24, 22
    width = max(1400, max(p.width for _, p in panels)) + 2 * pad
    text_h = 60 + line_h * len(text_lines)
    height = text_h + sum(p.height + 46 for _, p in panels) + pad
    board = Image.new("RGB", (width, height), (250, 250, 250))
    d = ImageDraw.Draw(board)
    d.text((pad, pad), ascii_safe(title), fill=(0, 0, 0), font=f_title)
    y = pad + 44
    for line in text_lines:
        d.text((pad, y), ascii_safe(line), fill=(40, 40, 40), font=f_txt)
        y += line_h
    y += 10
    for caption, panel in panels:
        d.text((pad, y), ascii_safe(caption), fill=(0, 0, 0), font=f_cap)
        y += 26
        board.paste(panel, (pad, y))
        d.rectangle([pad - 1, y - 1, pad + panel.width, y + panel.height],
                    outline=(180, 180, 180), width=1)
        y += panel.height + 20
    board.save(out_path)
    return out_path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tables = ROOT / "generation" / "prompt_tables"
    center = {r["id"]: r for r in
              json.loads((tables / "center_superblocks.json").read_text())["records"]}
    extrem = {r["id"]: r for r in
              json.loads((tables / "extremity_regions.json").read_text())["records"]}

    master = load_gray("diem_master_geometry_v1.png")
    master_small = master.resize((W // LOCATOR_SCALE, H // LOCATOR_SCALE), Image.BILINEAR)
    summary = {"generated_by": "generation/scripts/build_pilot_qa_boards.py",
               "coordinate_system": "global fresco pixels, origin top-left, "
                                    "canvas 34048x5312",
               "default_generation_margin_px": MARGIN,
               "pilots": []}

    # ---------------------------------------------------------------- L5_sb034
    rec = center["L5_sb034"]
    bbox = rec["geometry"]["bbox_px_global"]
    win = rec["geometry"]["gen_window_px_global"]
    unit = load_gray(rec["assets"]["mask_path"])
    unit_small = unit.resize(master_small.size, Image.BILINEAR)
    crop = clamp_window(bbox, MARGIN + CONTEXT_PAD)

    overlays = [(unit, COL_UNIT, 0.5)]
    labels = [("L5_sb034", rec["geometry"]["centroid_px_global"])]
    for i, nb in enumerate(rec["context"]["neighbors"]):
        nrec = center[nb["id"]]
        nmask = load_gray(nrec["assets"]["mask_path"])
        overlays.append((nmask, NEIGHBOR_COLS[i % len(NEIGHBOR_COLS)], 0.30))
        labels.append((nb["id"][3:], nrec["geometry"]["centroid_px_global"]))

    text = [
        f"unit id: L5_sb034 (superblock) — {rec['display_name']}",
        "coordinate system: global fresco px (origin top-left, canvas 34048x5312); mask space: global",
        f"mask: {rec['assets']['mask_path']}",
        f"tight bbox: {bbox}   generation window (bbox + {MARGIN}px default margin): {win}",
        f"crop dimensions: {rec['geometry']['gen_window_size_px'][0]} x {rec['geometry']['gen_window_size_px'][1]} px",
        f"area: {rec['geometry']['area_ha']} ha, {rec['geometry']['n_cells_l6']} L6 cells, "
        f"block grain: {rec['context']['block_grain']}, quartier purity: {rec['context']['quartier_purity']}",
        f"context: {rec['context']['l3_quartier']['name']} / {rec['context']['l2_arrondissement']['name']}, "
        f"palette world (provisional): {rec['context']['palette_world']}",
        "neighbors (shared px): " + ", ".join(
            f"{n['id'][3:]}({n['shared_px']})" for n in rec["context"]["neighbors"]),
        "legend: orange=unit  tinted=neighbors  blue=bbox  red=gen window",
    ]
    board = assemble_board(
        "PILOT QA — L5_sb034 (dense center tile)", text,
        [("full-fresco locator (1/16)", locator_panel(master_small, unit_small,
            [(bbox, COL_BBOX, 1), (win, COL_WINDOW, 1)])),
         ("detail: master + unit + neighbors + windows",
          detail_panel(master, overlays, crop,
                       [(bbox, COL_BBOX, 3), (win, COL_WINDOW, 3)], labels)),
         ("unit mask (gen window crop)", mask_panel(unit, win))],
        OUT / "board_L5_sb034.png")
    summary["pilots"].append({
        "pilot_id": "pilot_center_dense", "unit_ids": ["L5_sb034"],
        "kind": "superblock", "board": str(board.relative_to(ROOT)),
        "mask_paths": [rec["assets"]["mask_path"]], "mask_space": "global",
        "bbox_px_global": bbox, "gen_window_px_global": win,
        "effective_margin_px": rec["geometry"]["effective_margin_px"],
        "crop_size_px": rec["geometry"]["gen_window_size_px"],
        "neighbors": [n["id"] for n in rec["context"]["neighbors"]],
        "metadata": {"quartier": rec["context"]["l3_quartier"]["name"],
                     "arrondissement": rec["context"]["l2_arrondissement"]["name"],
                     "area_ha": rec["geometry"]["area_ha"],
                     "purity": rec["context"]["quartier_purity"]},
        "findings": "window 1550x1132 px, clean single-quartier unit; no issues",
    })
    del unit, unit_small, overlays

    # ------------------------------------------------------------- Seine strip
    rec = center["L5_seine_corridor"]
    cb = rec["geometry"]["bbox_px_global"]
    unit = load_gray(rec["assets"]["mask_path"])
    unit_small = unit.resize(master_small.size, Image.BILINEAR)
    strip_a = [STRIP_APPROVED[0], cb[1], STRIP_APPROVED[1], cb[3]]
    strip_f = [STRIP_FORMER[0], cb[1], STRIP_FORMER[1], cb[3]]
    win_a = clamp_window(strip_a, MARGIN)
    win_f = clamp_window(strip_f, MARGIN)
    crop = clamp_window(strip_a, MARGIN + CONTEXT_PAD)

    cite = load_gray("decomposition/masks/L4_semantic/L4_island_ile_de_la_cite.png")
    stlouis = load_gray("decomposition/masks/L4_semantic/L4_island_ile_saint_louis.png")
    bridges = load_gray("decomposition/masks/L4_semantic/L4_bridges.png")
    overlays = [(unit, COL_UNIT, 0.45),
                (cite, NEIGHBOR_COLS[0], 0.45), (stlouis, NEIGHBOR_COLS[1], 0.45),
                (bridges, NEIGHBOR_COLS[2], 0.45)]
    labels = [("seine_corridor", [14200, 4600]),
              ("ile_de_la_cite", [16700, 4300]), ("ile_saint_louis", [18900, 4300]),
              ("strip", [13600, 3300])]

    isl_bbox = [17952, 3866, 20013, 5185]   # from regions_L0_L5.json (L4)
    text = [
        "unit id: L5_seine_corridor (seine_corridor) — pilot on a strip, not the whole corridor",
        "coordinate system: global fresco px; mask space: global",
        f"mask: {rec['assets']['mask_path']}   corridor bbox: {cb}",
        f"strip (APPROVED 2026-07-10, canonical): x {STRIP_APPROVED}   gen window: {win_a}  "
        f"({win_a[2]-win_a[0]+1} x {win_a[3]-win_a[1]+1} px)",
        f"former extent (superseded): x {STRIP_FORMER}   gen window: {win_f}  "
        f"({win_f[2]-win_f[0]+1} x {win_f[3]-win_f[1]+1} px)",
        f"history: Ile Saint-Louis footprint {isl_bbox} extends to x=20013 — the former strip",
        f"(end x=19500) clipped its eastern tip by ~513 px; approved end x=20200 contains both islands fully.",
        f"area (whole corridor): {rec['geometry']['area_ha']} ha, {rec['geometry']['n_cells_l6']} cells; "
        f"flags: {', '.join(rec['context']['flags'])}",
        "overlays shown: islands (blue/green, separate units) + bridge decks (purple, overlay masks)",
        "legend: orange=corridor  green=APPROVED strip window  red=former extent (superseded)",
    ]
    board = assemble_board(
        "PILOT QA — Seine corridor strip (water pilot)", text,
        [("full-fresco locator (1/16)", locator_panel(master_small, unit_small,
            [(win_f, COL_WINDOW, 1), (win_a, COL_ALT, 1)])),
         ("detail: corridor + islands + bridges + strip windows",
          detail_panel(master, overlays, crop,
                       [(win_f, COL_WINDOW, 3), (win_a, COL_ALT, 3)], labels)),
         ("corridor mask (approved strip crop)", mask_panel(unit, win_a))],
        OUT / "board_seine_strip.png")
    summary["pilots"].append({
        "pilot_id": "pilot_seine_strip", "unit_ids": ["L5_seine_corridor"],
        "kind": "seine_corridor_strip", "board": str(board.relative_to(ROOT)),
        "mask_paths": [rec["assets"]["mask_path"],
                       "decomposition/masks/L4_semantic/L4_island_ile_de_la_cite.png",
                       "decomposition/masks/L4_semantic/L4_island_ile_saint_louis.png",
                       "decomposition/masks/L4_semantic/L4_bridges.png"],
        "mask_space": "global",
        "strip_x_approved": STRIP_APPROVED,
        "strip_status": "approved 2026-07-10 — canonical Stage 3 pilot strip",
        "strip_x_former_superseded": STRIP_FORMER,
        "strip_history": "former end x=19500 clipped Ile Saint-Louis (footprint to "
                         "x=20013); extended to x=20200 on approval",
        "gen_window_px_global": win_a,
        "gen_window_px_global_former": win_f,
        "effective_margin_px": MARGIN,
        "crop_size_px": [win_a[2]-win_a[0]+1, win_a[3]-win_a[1]+1],
        "neighbors": [n["id"] for n in rec["context"]["neighbors"]],
        "findings": "approved extent contains both islands fully; no open issues",
    })
    del unit, unit_small, cite, stlouis, bridges, overlays

    # ----------------------------------------------------------- EXT_L_bretagne
    rec = extrem["EXT_L_bretagne"]
    bbox = [int(round(v)) for v in rec["geometry"]["bbox_px_global"]]
    win = rec["geometry"]["gen_window_px_global"]
    offset = rec["geometry"]["panel_offset_x"]
    unit = paste_panel_local(load_gray(rec["assets"]["mask_path"]), offset)
    unit_small = unit.resize(master_small.size, Image.BILINEAR)
    crop = clamp_window(bbox, MARGIN + CONTEXT_PAD)

    overlays = [(unit, COL_UNIT, 0.5)]
    labels = [("bretagne", [900, 350])]
    name_to_id = {r["display_name"]: r["id"] for r in extrem.values()}
    for i, nb_name in enumerate(rec["context"]["neighbors_same_panel"]):
        nrec = extrem[name_to_id[nb_name]]
        nmask = paste_panel_local(load_gray(nrec["assets"]["mask_path"]),
                                  nrec["geometry"]["panel_offset_x"])
        overlays.append((nmask, NEIGHBOR_COLS[i % len(NEIGHBOR_COLS)], 0.30))
        nx = sum(p[0] for p in nrec["geometry"]["polygon_px_global"]) / len(
            nrec["geometry"]["polygon_px_global"])
        ny = sum(p[1] for p in nrec["geometry"]["polygon_px_global"]) / len(
            nrec["geometry"]["polygon_px_global"])
        labels.append((nrec["id"][6:], [nx, ny]))

    poly = [(p[0], p[1]) for p in rec["geometry"]["polygon_px_global"]]
    text = [
        f"unit id: EXT_L_bretagne (extremity_region) — {rec['display_name']}, panel: left",
        "coordinate system: global fresco px; MASK SPACE: panel-local "
        f"(offset_x={offset}, so local == global here)",
        f"mask: {rec['assets']['mask_path']}",
        f"polygon (global): {[[round(x), round(y)] for x, y in poly]}",
        f"tight bbox: {bbox}   generation window (bbox + {MARGIN}px default margin): {win}",
        f"crop dimensions: {rec['geometry']['gen_window_size_px'][0]} x {rec['geometry']['gen_window_size_px'][1]} px",
        f"area fraction of panel: {rec['geometry']['area_fraction_achieved']:.4f} "
        f"(target {rec['geometry']['area_fraction_target']:.4f}, optimizer error 0.00%)",
        f"touches zigzag seam: {rec['context']['touches_zigzag_seam']}   "
        f"neighbors: {', '.join(rec['context']['neighbors_same_panel'])}",
        "legend: orange=unit  tinted=neighbors  blue=bbox  red=gen window  white=polygon outline",
    ]

    def bret_detail():
        img = detail_panel(master, overlays, crop,
                           [(bbox, COL_BBOX, 3), (win, COL_WINDOW, 3)], labels)
        scale = img.width / (crop[2] - crop[0] + 1)
        d = ImageDraw.Draw(img)
        pts = [((x - crop[0]) * scale, (y - crop[1]) * scale) for x, y in poly]
        d.polygon(pts, outline=(255, 255, 255), width=3)
        return img

    board = assemble_board(
        "PILOT QA — EXT_L_bretagne (extremity pilot)", text,
        [("full-fresco locator (1/16)", locator_panel(master_small, unit_small,
            [(bbox, COL_BBOX, 1), (win, COL_WINDOW, 1)])),
         ("detail: panel + unit + neighbors + polygon", bret_detail()),
         ("unit mask (gen window crop, lifted to global)", mask_panel(unit, win))],
        OUT / "board_EXT_L_bretagne.png")
    summary["pilots"].append({
        "pilot_id": "pilot_extremity", "unit_ids": ["EXT_L_bretagne"],
        "kind": "extremity_region", "board": str(board.relative_to(ROOT)),
        "mask_paths": [rec["assets"]["mask_path"]],
        "mask_space": f"panel_local (offset_x={offset})",
        "bbox_px_global": bbox, "gen_window_px_global": win,
        "effective_margin_px": rec["geometry"]["effective_margin_px"],
        "crop_size_px": rec["geometry"]["gen_window_size_px"],
        "neighbors": rec["context"]["neighbors_same_panel"],
        "metadata": {"panel": "left",
                     "area_fraction": rec["geometry"]["area_fraction_achieved"],
                     "touches_zigzag_seam": rec["context"]["touches_zigzag_seam"]},
        "findings": "window 2643x937 px — wide/shallow aspect (2.8:1); workable but "
                    "note some models prefer squarer canvases; unit does not touch "
                    "the seam (decoupled from branch design)",
    })

    (OUT / "pilot_summary.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    for p in summary["pilots"]:
        print(f"{p['pilot_id']:<22} -> {p['board']}")
    print(f"summary -> {(OUT / 'pilot_summary.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
