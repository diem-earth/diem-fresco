# Diem Fresco Project — Master Geometry v1.0
## Technical Report

**Date:** 2026-07-07
**Source:** `canny_final.tiff` (2025-11-19, author: Mathis Koroglu)
**Master:** `diem_master_geometry_v1.tiff` (+ `diem_master_geometry_v1.png`)

---

## 1. Source characterization

| Property | Value |
|---|---|
| Dimensions | 34 048 × 5 312 px (unchanged in master) |
| Physical size @ 300 dpi | 288.3 × 45.0 cm |
| Mode / depth | Grayscale, 8-bit, single channel |
| Compression | Adobe Deflate (preserved in master) |
| Pixel values | 9 levels: 0 (line core), 255 (background), 7 intermediate anti-aliasing levels (31–223) |
| Ink coverage | 29 790 629 px < 255 (16.5 % of canvas) |
| Map body extent | x ≈ 3 412 → 29 587 (large intentional white margins left and right) |

Structural findings that drove every decision:

- **The street network is a single connected component** holding 99.927 % of all ink
  (29 768 947 px). Topological continuity of the extraction is excellent — no stitching
  or gap-closing was needed anywhere.
- **99.97 % of intermediate gray pixels are directly adjacent to line cores**: they are
  legitimate anti-aliasing of the stroke rendering, uniformly distributed. The rendering
  is already internally consistent.
- Besides the main network, only **45 small components** existed (21 682 px total,
  0.073 % of ink). Each one was individually reviewed on a zoomed contact sheet and
  measured for distance to the main body before any decision.

## 2. Workflow chosen and why

**Direct, surgical raster editing — nothing else.** Alternatives were explicitly
evaluated and rejected:

| Workflow | Verdict | Reason |
|---|---|---|
| Vectorize (skeleton/centerline) → rebuild | ✗ Rejected | Re-rasterization resamples *every* line: global sub-pixel geometry drift, violates the preservation constraint |
| Contour tracing (potrace-style) → SVG → raster | ✗ Rejected | Curve fitting displaces edges up to ~1 px everywhere; creates a second, subtly different source of truth |
| Morphological cleanup (open/close/despeckle filters) | ✗ Rejected | Blind filters alter line ends, corners and junctions across the whole map |
| Binarization / AA removal | ✗ Rejected | The 7 AA levels are healthy and consistent; thresholding would jag every edge |
| **Component-level removal with per-component review** | ✓ Chosen | Only provably non-map pixels are touched; every other pixel stays byte-identical |

The master remains **grayscale** on purpose: the anti-aliasing carries genuine sub-pixel
position information. Downstream stages that need a binary mask should threshold at the
point of use (e.g. `ink = value < 128` or `< 255` depending on tolerance) rather than
baking that loss into the canonical asset.

## 3. Modifications performed

**Exactly 8 743 pixels changed (0.029 % of ink), all ink → white, in 24 isolated
components. Zero pixels were added. Zero pixels changed inside the map body.**
Full inventory with coordinates: `qa/removal_manifest.csv`. Groups:

| Group | Components | Pixels | Justification |
|---|---|---|---|
| Bottom-right severed stubs | 6 (L35–L40) | 7 450 | Thick diagonal dashes at the bottom edge, x = 31 082–33 533 — **1.5–4 k px beyond the map body's eastern end**, isolated in white space (> 600 px from any map ink). Leaked fragments of streets outside the intended Paris-Centre frame. This is the "bottom-right protrusion" flagged in the brief. |
| Right canvas-edge slivers | 3 (L19–L21) | 256 | 3–4 px wide bars ON the right canvas edge (x = 34 044+), 4.4 k px from the map. Rotation/crop border bleed. |
| Far-west isolated blob | 1 (L32) | 680 | Anti-aliased blob at (838, 3722), 2.6 k px west of the map body, floating in empty margin. Leaked content from beyond the périphérique. |
| Left canvas-edge bar | 1 (L34) | 256 | 10×28 px bar touching the left canvas edge at y = 5 244, in empty margin. Border bleed. |
| Western sub-threshold residue | 12 (L17, L18, L22–L31) | 95 | Specks of 1–29 px scattered 72–307 px west of the périphérique, outside the map boundary. Includes a faint gray dust chain (L24–L30) — remnant of a line the Canny threshold rejected; it renders no usable geometry. |
| Floating fleck | 1 (L33) | 6 | 5×2 px fleck in a white pocket near the SW interchange, 17 px from the nearest line, no continuation on either side. |

### Deliberately kept (reviewed, judged genuine)

- **All 14 top-edge components** (L1–L15 group, incl. 1–2 px dots): clipped tips of real
  streets that continue above the canvas — proper stroke width, correct style.
- **All 5 bottom-edge in-map components** (L42–L46): same situation at the bottom edge.
- **L41** (156 px, bottom edge at x = 29 609): nestled between the périphérique
  interchange curves, 49 px from the main body — plausibly genuine clipped geometry.
  Kept under "when in doubt, don't touch".
- **L16** (2 px at (4624, 31)): the anti-aliased continuation of a tapering street
  needle, 4 px from its tip. Genuine rendering residue of real geometry.

### Deliberately NOT done — important negative finding

The map contains ~1 300 tiny (≤ 4 px) white/gray "holes". Zoomed inspection showed these
are **not** noise: they are the surviving remnants of genuine narrow white channels
separating closely-spaced parallel streets (visible as dotted white lines inside
apparently-thick strokes, e.g. around x ≈ 18 100, y ≈ 65–101). **Filling them would
actively merge distinct parallel streets — a geometry modification — so no hole filling
was performed anywhere.** Downstream stages should be aware that some parallel-street
separations are only 1–2 px wide.

## 4. Validation (all hard-asserted in code)

| Check | Result |
|---|---|
| Output dimensions | 34 048 × 5 312, uint8 — **identical** ✓ |
| Changed pixels | exactly 8 743, every one inside the 24 documented artifact bboxes ✓ |
| Direction of change | 100 % ink → white; no pixel darkened, none added ✓ |
| Main street network | 29 768 947 px — **byte-identical** ✓ |
| Components | 46 → 22 (main + 21 kept genuine fragments) ✓ |
| Left/right canvas borders | 0 ink px after cleanup (was 26 / 76 artifact px) ✓ |
| Top/bottom borders | untouched (genuine clipped streets preserved) ✓ |
| TIFF/PNG roundtrip | re-read arrays equal in-memory result exactly ✓ |
| Metadata | 300 dpi preserved; Adobe Deflate preserved; provenance written into ImageDescription; original author kept in Artist tag |

QA assets in `qa/`: before/after comparisons of every removal zone (removed pixels
highlighted red), full master overview, machine-readable removal manifest, and
`reproduce_master.py` — a deterministic script that rebuilds the master from the source
and **aborts if any component signature differs**.

## 5. On the SVG deliverable

An SVG "master" was **intentionally not produced**. Any vectorization of this raster
(centerline or contour) is a lossy approximation: curve fitting displaces geometry at
sub-pixel to pixel scale, and dense 181-Mpx linework would yield an unwieldy multi-GB
path soup with degraded junctions. Publishing it as a "master" would create two
non-identical sources of truth — a real hazard for zone extraction and compositing.
**The raster IS the canonical geometry.** If later pipeline stages need vectors (laser,
CNC, plotting), vectorize per-zone from this master at that stage, with parameters tuned
to that use, and validate against the master raster.

## 6. Remaining known imperfections (documented, not defects introduced)

1. **Nearly-collapsed parallel-street channels** (see §3): separations of 1–2 px in a
   few dense corridors. Repairing them would require redrawing geometry from the source
   map — out of scope for this asset; possible future v2 if the upstream render can be
   regenerated at higher internal resolution.
2. **Anti-aliasing is quantized to 7 levels** (31…223) rather than continuous — an
   artifact of the upstream pipeline. Visually irrelevant at print scale; harmless to
   masking.
3. **Streets clipped at top/bottom canvas edges** end abruptly by design (the canvas is
   a band through Paris); their 1–5 px orphan residues at the very edge rows were kept
   as genuine geometry.
4. L41 could not be conclusively attributed (kept conservatively).

## 7. Deliverables

| File | Role |
|---|---|
| `diem_master_geometry_v1.tiff` | **Canonical master** — grayscale, 34 048 × 5 312, 300 dpi, Adobe Deflate |
| `diem_master_geometry_v1.png` | Lossless PNG equivalent (identical pixels, 300 dpi pHYs) |
| `MASTER_GEOMETRY_REPORT.md` | This report |
| `qa/removal_manifest.csv` | Every removed component: coordinates, size, distance to map, reason |
| `qa/before_after_*.png` | Visual proof of each removal (removed pixels in red) |
| `qa/master_overview.png` | Full-map overview of the master |
| `qa/reproduce_master.py` | Deterministic, self-verifying rebuild script |

`canny_final.tiff` is untouched and remains the raw upstream reference.
