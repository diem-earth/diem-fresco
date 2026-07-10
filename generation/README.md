# generation/ — Stage 3 planning layer (provisional, uncommitted)

Metadata and prompt scaffolding for AI generation of the fresco. **No images
are generated from here yet** — this layer prepares the structured inputs.
Status: refinement pass B in progress (see
`docs/DELIVERABLES_ARCHITECTURE.md`, commit sequence A–E).

```
generation/
  README.md                     this file
  generation_config.json        global config: default_generation_margin_px (working
                                default, NOT approved), canvas, panel offset
  prompt_tables/
    SCHEMA.md                   schema v0.2: derived vs curated, concept/render prompt model
    center_superblocks.json     79 records: 78 L5 superblocks + Seine corridor (canonical)
    center_superblocks.csv      derived review view — do not hand-edit
    extremity_regions.json      12 records: 6 left + 6 right panel regions (canonical)
    extremity_regions.csv       derived review view — do not hand-edit
    seam_ornaments.json         2 records: laurel (left seam), oak (right seam)
  references/
    extremity_prompt_legacy/    landing zone for historical regional prompt material
                                (nothing imported yet — see its README)
  qa/
    pilot_selection/            deterministic technical QA boards for the 3 pilot
                                candidates + machine-readable summary (not artwork)
  scripts/
    build_prompt_tables.py      deterministic builder (stage-2 meta → tables)
    test_curated_persistence.py automated proof that curated fields survive rebuilds
    build_pilot_qa_boards.py    renders the QA boards from existing geometry/masks only
```

Plan, constraints, hypotheses, pilots and open questions:
[docs/STAGE3_GENERATION_PLAN.md](../docs/STAGE3_GENERATION_PLAN.md).

## Rebuilding & testing

```bash
python3 generation/scripts/build_prompt_tables.py      # rebuild tables
python3 generation/scripts/test_curated_persistence.py # prove curated survives rebuilds
python3 generation/scripts/build_pilot_qa_boards.py    # re-render pilot QA boards
```

Derived fields are recomputed from `decomposition/meta/`,
`extremities/outputs/` and `generation_config.json`; every record's `curated`
block (prompts, motifs, direction, overrides) is **preserved by id**, so
rebuilding is always safe — and the persistence test proves it. The builder
self-checks (record counts, area fractions, mask resolution, curated-schema
drift, margin/window presence) and refuses to write silently wrong tables.

## Rules inherited from stages 1–2 and the architecture (invariant)

- The master raster is the only geometric authority. Generation fills content
  *inside* masks; the street linework is recomposited on top. Never let a
  model redraw, move, or invent streets.
- Generated content stays clipped to its assigned region (cell-exact at L6
  for center units).
- Consume `decomposition/meta/*.json` + `decomposition/masks/` — never
  re-derive geometry from the TIFF ad hoc.
- Extremity masks are panel-local; right panel `global_x = local_x + 28 048`.
- Curated prompt content is **private** (excluded from any public export);
  schemas and this builder are public-safe export candidates.
- Accepted outputs must be registered in `registry/artifacts.yaml` and emit a
  canonical full-canvas process-film preview (see `process_film/README.md`).
