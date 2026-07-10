# Stage 3 — Generation Plan (v1, refinement pass B — planning only)

*Status 2026-07-10: planning layer refined, **no artistic image generation has
started**. This document and `generation/` are intentionally uncommitted until
refinement is approved (commit sequence A–E in
[DELIVERABLES_ARCHITECTURE.md](DELIVERABLES_ARCHITECTURE.md); A is committed
as `f0b14cd` / tag `v0.3-deliverables-architecture`).*

## Purpose

Turn the validated stage-1/2 geometry into a structured, reviewable generation
plan: one metadata + prompt record per generation unit, a clean separation of
technical invariants from artistic hypotheses, and three pilot zones with
technical QA boards.

Generation units (93 total):

1. **78 L5 center superblocks** + the **Seine corridor** (79 records) —
   `generation/prompt_tables/center_superblocks.json`
2. **12 extremity regions** (6 left, 6 right) —
   `generation/prompt_tables/extremity_regions.json`
3. **2 seam ornaments** — laurel (left), oak (right) —
   `generation/prompt_tables/seam_ornaments.json`

Schemas: [generation/prompt_tables/SCHEMA.md](../generation/prompt_tables/SCHEMA.md)
(v0.2 — model-independent `concept_prompt` vs model-specific `render_prompt`;
all human-authored artistic data in rebuild-surviving `curated` blocks;
persistence proven by `generation/scripts/test_curated_persistence.py`).

## Invariant technical constraints

These are the **only** non-negotiable rules. They derive from the validated
geometry and the deliverables architecture, not from any artistic choice:

1. **Canonical geometry and masks are never altered.** The master raster,
   decomposition masks/meta and extremity geometry are read-only inputs.
2. **Generated content stays clipped to its assigned region.** Center units
   clip cell-exactly at L6 (no orphan pixels, neighbors untouched); extremity
   content stays inside its region polygon mask.
3. **The Paris street-network linework is recomposited above generated
   content.** Generation never draws, moves, erases or invents streets; any
   output whose recomposite would alter an ink pixel is rejected.
4. **No accidental text, labels or watermarks** in generated output.
   (Whether *deliberate* lettering ever appears anywhere in the fresco is a
   separate artistic decision, currently open.)
5. **Reproducibility and traceability.** Every generation must be traceable
   to its unit id, its prompt (`concept_prompt` / `render_prompt`), and its
   configuration (`model_config_ref`, `conditioning_assets`, effective
   margin). Accepted outputs are registered (see "Architecture alignment").

## Provisional artistic hypotheses (PROPOSED — none approved)

Working hypotheses, held in `style_pack_v0` and the tables' provisional
groupings. Each may be revised or discarded by artistic decision; **nothing
below is a constraint**:

- **PROPOSED — palette worlds.** The L1-derived grouping
  (`rive_droite` / `rive_gauche` / `seine` / panel worlds) as a way to make
  the fresco read from across the room. The grouping is computed and stored;
  what it *means* visually (if anything) is open.
- **PROPOSED — L4 set pieces as emphasis zones.** The ~28 parks / plazas /
  islands / cemetery / rail units may deserve dedicated treatment; how (in-tile
  emphasis vs separate overlay) is open.
- **PROPOSED — quiet exterior.** `L5_exterior_west/east` and blank margins
  minimally treated. Open.
- **PROPOSED — seam quiet zones.** Extremity regions touching the zigzag
  keep a calmer band near the seam edge for the future laurel/oak branches
  (whose own style is TBD).
- **PROPOSED — continuity mechanics.** Feathering budgets from
  `context.neighbors[].shared_px`; the corridor generated as one continuous
  unit or long overlapping strips; avenue-stroke recomposite bands over L5
  joins (the recomposite itself is invariant #3; using *dilated* bands as a
  stitching device is the hypothesis).

**Explicitly NOT constraints** (earlier drafts overstated these): strict
aerial/plan view; flat vector treatment; an "illuminated map" style; a
blanket prohibition of perspective fragments; any specific palette or
pictorial medium. The street network determines **spatial boundaries, not
pictorial perspective** — unit interiors may become dense, layered, symbolic,
surreal, multi-scale or multi-perspective compositions if the artistic
direction goes there.

## Open artistic decisions

1. **Pictorial medium / visual language** — completely open (fresco pigment,
   gouache, engraving, layered symbolic tapestry, mixed…).
2. **Palette** — open, including whether palette worlds are used at all.
3. **Perspective policy** — open: plan-view, mixed perspectives, multi-scale
   interiors, or per-unit freedom within continuity limits.
4. **Deliberate lettering** — open (accidental text remains banned).
5. **Generation model & tooling** — open; `render_prompt` and
   `model_config_ref` stay empty until chosen. **Concept prompts can and
   should be authored before this is decided.**
6. **L4 set-piece treatment** — in-tile emphasis vs overlay generation.
7. **Extremity content direction** — abstract regional identity per the
   legacy prompt series (import pending) vs a new direction; see
   `generation/references/extremity_prompt_legacy/`.
8. **Seam branch design** — style/scale/opacity/method (records
   `blocked_on_design`).
9. **Degenerate tiles** — 4 single-cell slivers ≤ 0.5 ha
   (`sb075/076/078/079`): merge into a neighbor's window or inherited fill.
10. **Corridor strategy** — single generation vs overlapping strips (model
    canvas limits will decide; the pilot strip tests blending).

## Architecture (generation mechanics — unchanged from PHASE4)

**Generate at L5 · condition from L1/L2/L3/L4 · composite at L6.**

- Units are generated in `geometry.gen_window_px_global` crops: tight bbox +
  **effective margin** (config default `default_generation_margin_px`,
  currently 64 px as an *unapproved working default*, overridable per record
  via `curated.generation_margin_override_px` — the right value depends on
  the model, resolution, conditioning method and continuity strategy).
- Conditioning facts (quartier, arrondissement, contained set pieces,
  neighbors, grain) are precomputed in `context`; `prompt_scaffold` is a
  factual, artistically neutral unit summary that seeds `concept_prompt`
  authoring.
- Output is clipped cell-exactly at L6 before compositing, so any tile can be
  re-generated later without touching neighbors.

## Alignment with the deliverables architecture

- **Accepted generation outputs are registered** in `registry/artifacts.yaml`
  (role provisional → canonical on acceptance). The storage path for
  generated tiles is **TBD until approved** (registry `generated_tiles.path:
  null`; a proposal exists but nothing is final).
- **Every accepted canvas-changing output emits a canonical full-canvas
  process-film preview** (film stage `s08_generation` capture rule,
  `process_film/README.md`), committed with the work.
- **Curated prompt content is private**: excluded from any public export
  (`public_export/manifests/exclude.txt` blocks `prompt_tables/*.json|csv`).
- **Schemas and the builder are public-safe export candidates**
  (`include_candidates.txt`), pending the export review gates.
- A unit reaches `status: composited` only when registered *and* film-captured.

## Pilot zones (3) — with technical QA boards

Deterministic QA boards (position, masks, windows, neighbors, metadata — not
artwork) live in `generation/qa/pilot_selection/` with a machine-readable
`pilot_summary.json`; regenerate with
`python3 generation/scripts/build_pilot_qa_boards.py`.

| Pilot | Unit | Why this one |
|---|---|---|
| Dense center tile | **`L5_sb034` — Arts-et-Métiers (3e, haut Marais)**, 15.8 ha ≈ median, 16 cells | purity 1.0 (clean single-quartier conditioning), 6 neighbors (max continuity testing), no L4 unit (tests the *plain fabric* case covering most of the 78) |
| Seine / water | **`L5_seine_corridor`**, piloted on the strip **x ∈ [13 500, 20 200]** (approved) | exercises water + both bank interfaces + both islands (fully contained) + bridge-deck overlays in one window; validates strip blending for the full 13.4 k px corridor |
| Extremity | **`EXT_L_bretagne`** (left panel, 9.5 %) | strong standalone identity; does **not** touch the zigzag seam, so decoupled from the unresolved branch design; borders 3 regions |

**Strip extent — APPROVED (2026-07-10): x ∈ [13 500, 20 200]** is the
canonical Stage 3 pilot strip. History: the initially proposed extent
x ∈ [13 500, 19 500] clipped Île Saint-Louis (footprint to x = 20 013) — a
QA-board finding — and was superseded on approval; both extents remain
recorded in `pilot_summary.json` for provenance.

Pilot success criteria:

1. Re-compositing the ink mask over the output leaves every street pixel
   identical to the master (invariant #3 holds).
2. Generating `L5_sb034` and one neighbor independently, then applying the
   avenue-stroke band, produces no visible seam at candidate print scale
   (effective print resolution TBD — see `production/specs/fresco.yaml`).
3. The corridor strip reads as continuous water past bridge and island
   overlays.
4. Bretagne reads as part of the same fresco as the center pilots (whatever
   style pack is finally approved holds across panel types).

Alternates if a pilot underperforms: `L5_sb022` (Bonne-Nouvelle/Sentier, 2e —
densest high-purity fabric, purity 0.807) for the center;
`EXT_R_bourgogne_franche_comte` (also seam-free) for the extremity.

## What was deliberately deferred

- Authoring `concept_prompt`s — next step after this refinement is approved
  (can proceed *without* a model decision).
- `render_prompt`s and `model_config_ref`s — blocked on model/tooling choice.
- Legacy regional prompt import — scaffolding exists
  (`generation/references/extremity_prompt_legacy/`), **no source material
  imported yet**; historical prompts must come from their original source,
  never reconstructed from memory.
- Seam branch design; any image generation; compositing code.
