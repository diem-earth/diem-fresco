# Diem — Deliverables Architecture

*Established 2026-07-10, after tag `v0.2-global-fresco-structure`. This repo
remains the **private canonical workbench**; the project has three distinct
final deliverables, each owned by a dedicated layer.*

## The three deliverables and their layers

| # | Deliverable | Layer | Nature |
|---|---|---|---|
| 1 | Final production fresco (monumental, print-ready) | `production/` | consumes canonical artifacts, owns spec + masters + print + validation |
| 2 | Future public GitHub repo (method, not workbench) | `public_export/` | planning + manifests; generated later as a fresh-history snapshot |
| 3 | Canonical process film (blank canvas → fresco) | `process_film/` | manifest-driven; previews captured as work happens, film always compiled |

Cross-cutting: `registry/artifacts.yaml` — the single index of every artifact
family with a role (**canonical / derived / provisional / archived**) and
status (**present / planned / missing_upstream**). Deliverable layers
reference artifacts through the registry's roles; none of them redefines
geometry.

## How the deliverables stay separated

- **Workbench vs production**: `production/` holds only spec, previews,
  masters, print files and validation records. Working material (masks, meta,
  prompt tables, pipeline) stays where stages 1–3 put it; the spec
  (`production/specs/fresco.yaml`) *points* at those canonical layers.
- **Private vs public**: allowlist model. Nothing leaves the workbench unless
  matched by `public_export/manifests/include.txt`; `exclude.txt` always wins;
  unmatched = private. The public repo is generated as a **fresh-history
  snapshot** — the workbench history, experimentation, prompts, full-res
  artwork and identities never leave.
- **Work vs film**: the film is compiled from
  `process_film/manifest/stages.json`; stage previews are committed source
  material, rendered outputs are gitignored derivatives. Missing history is
  flagged (`blocked_missing_source`), never fabricated.

## Format conventions

- **YAML** for human-first specifications (`production/specs/fresco.yaml`,
  `registry/artifacts.yaml`) — comments carry rationale.
- **JSON** for machine-consumed tables (`process_film/manifest/stages.json`,
  `generation/prompt_tables/*.json`) — stdlib-parseable, diff-friendly.
- TBD is a real value: code must refuse to proceed on a TBD it depends on.

## Stage 3 integration (currently uncommitted work)

The `generation/` layer created 2026-07-10 (prompt tables, schema, builder,
pilot selection, `docs/STAGE3_GENERATION_PLAN.md`) **stays exactly where it
is on disk but remains UNCOMMITTED** — it is the workbench's
generation-planning layer, not a deliverable, and it still needs the
artistic/schema refinement pass before it is commit-worthy. The architecture
references it strictly as a **provisional/planned layer**: nothing in
`production/`, `public_export/`, `process_film/` or `registry/` requires the
current prompt tables to be committed first.

- `registry/artifacts.yaml` lists the prompt tables as **provisional,
  uncommitted, pending refinement**; they become canonical when prompts are
  approved and committed.
- `production/specs/fresco.yaml#source_layers` references them as a
  compositing input; `generated_tiles` remains TBD until pilots run.
- `process_film` stage `s08_generation` will accumulate its frames from the
  pilots onward (capture rule in `process_film/README.md`).
- `public_export` publishes the prompt **schema and builder**, never the
  curated prompt text.

## Recommended commit sequence

**A. Architecture layer first** *(after the 2026-07-10 correction pass)* —
commit `production/`, `public_export/`, `process_film/`, `registry/`, this
doc, and the `PROJECT_STATE.md` update. `generation/` and
`docs/STAGE3_GENERATION_PLAN.md` stay uncommitted.

**B. Stage 3 refinement** *(working tree, no commit)* — the deferred
artistic/schema refinement pass:
   - distinguish invariant geometry constraints from provisional artistic
     direction;
   - separate `concept_prompt` (model-agnostic intent) from model-specific
     `render_prompt`;
   - move all human-authored artistic data into curated fields;
   - make the 64 px generation margin a configurable default;
   - add legacy regional-prompt import placeholders;
   - create technical QA boards for the three pilot choices.

**C. Refined Stage 3 commit** — `generation/` + `docs/STAGE3_GENERATION_PLAN.md`
land only in their refined form.

**D. Legacy regional-prompt import** — bring prior regional prompt material
into `extremity_regions.json` curated fields. ⚠ The `fresco_building` archive
contains **no prompt files** (verified 2026-07-10) — the source location of
these legacy prompts must be provided first (open decision).

**E. Pilot generation** — the three pilots (`L5_sb034`, Seine-corridor strip,
`EXT_L_bretagne`) against the success criteria in
`docs/STAGE3_GENERATION_PLAN.md`; validate against
`production/specs/fresco.yaml`; capture `s08` film frames from the first
accepted tile onward, then keep the ongoing capture rule: every
canvas-changing stage updates the film manifest and commits its canonical
preview in the same commit as the work.

## What was deliberately NOT done in this pass

- No files moved or deleted — all validated stage-1/2 artifacts remain at
  their canonical paths (`decomposition/`, `extremities/`, `qa/`, roots).
- No images generated, no film frames rendered, no export executed.
- Frozen historical reports (`MASTER_GEOMETRY_REPORT.md`,
  `decomposition/reports/`) untouched — they describe file metadata at the
  time (e.g. "physical size @ 300 dpi") and are records, not living claims.
- Unresolved specifications marked TBD, never guessed (physical print
  dimensions, effective print dpi, color profiles, print process, film
  downsample factor, licenses, generated-tile storage path).
