# extremity_prompt_legacy/ — landing zone for historical regional prompts

**Status: NO source material has been imported yet.** This directory is
scaffolding only.

## What is expected here

Prior artistic prompt work exists for the 12 extremity regions, developed
before this repository. Per the project's description it includes:

- a **left panel blue series** and a **right panel red series**;
- abstract regional identity (not literal landscapes);
- dense **layered tapestry** logic;
- explicit avoidance of sparse "tourism-poster" scenes;
- continuity intentions between neighboring regions;
- **region-specific motif lists**.

This material is **not** in the `fresco_building` archive (verified
2026-07-10: the zip contains no prompt files) and has not yet been located or
integrated. Its source must be provided by the project owner.

## Hard rule for AI assistants

**Do not recreate, reconstruct, paraphrase or "restore" the historical
prompts from memory or from the summary above.** The bullet list describes
what the material is *about*; it is not the material. Only files actually
supplied by the project owner belong in `raw/`. Until then, the curated
prompt fields of `extremity_regions.json` stay empty or contain clearly *new*
authored work — never a from-memory reconstruction presented as legacy.

## Workflow

```
raw/          verbatim originals, exactly as supplied — never edited
normalized/   one JSON per region, extracted from raw/ (see below)
```

1. **Import**: drop original files into `raw/` unchanged (any format).
2. **Normalize**: for each region, produce
   `normalized/EXT_{L|R}_{slug}.json` mapping the raw content onto the
   curated fields of `extremity_regions.json`:
   `concept_prompt`, `identity_motifs`, `secondary_motifs`, `materials`,
   `atmosphere`, `color_direction`, `density`, `composition_notes`,
   `continuity_notes` (+ `render_prompt` only if the legacy text was
   model-specific — note which model).
3. **Integrate**: copy the normalized values into the matching record's
   `curated` block in `generation/prompt_tables/extremity_regions.json`
   (by hand or a small merge script), then rebuild the tables. The curated
   block survives rebuilds (proven by `test_curated_persistence.py`).

## Provenance — required in every normalized file

```json
{
  "provenance": {
    "original_filename": "…",        // or source description
    "source": "…",                   // where it came from
    "date": "…",                     // if known, else null
    "language": "fr|en|…",
    "version": "…",                  // if the legacy work was versioned
    "transformation_notes": "…"      // what was changed during normalization
  },
  "curated_fields": { … }
}
```

Raw files are never modified; every transformation is recorded in
`transformation_notes`.
