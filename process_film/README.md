# process_film/ — Deliverable 3: the canonical process film

A film/GIF that builds the fresco from a blank white canvas through every
stage to the final artwork. **The film is compiled from
[manifest/stages.json](manifest/stages.json) by scripts — never assembled by
hand at the end.** Adding or reworking a stage means editing the manifest and
(re)rendering its previews; the film itself is always a derived artifact.

```
manifest/
  SCHEMA.md       stage record schema
  stages.json     the 12-stage manifest (canonical) — s00 blank … s11 final
previews/         canonical full-canvas stage previews (committed)   [empty for now]
scripts/          render/assemble tooling (future)                   [placeholder]
outputs/          rendered GIF/MP4 files — regenerable, gitignored
```

## Canonical full-canvas preview rules

1. **Every frame is the full canvas.** Each preview renders the complete
   34048 × 5312 composition (white where nothing exists yet), downsampled by
   one single global factor — proposed **1/8 → 4256 × 664** (TBD). Never a
   crop presented as the whole; never per-stage framing changes.
2. **Panel-local artifacts are composited at their global offsets first**
   (right panel `global_x = local_x + 28048`), then downsampled.
3. RGB PNG, white background. Static stages: one `sNN_<id>.png`. Animated
   stages: `sNN_<id>/frame_%04d.png`.
4. **No fabricated history.** A stage whose sources are missing
   (`blocked_missing_source`) gets a clearly-marked placeholder card in draft
   renders — never a fake reconstruction.
5. Previews are committed (they are the film's source material); `outputs/`
   renders are regenerable and gitignored.

## Source & output hierarchy

1. **Canonical stage previews** (`previews/`, committed) are the *visual
   source of truth* — every stage's imagery must exist as, or be regenerable
   into, full-canvas previews.
2. **`mp4_exhibition` is the primary moving-image output**; it is rendered at
   the highest quality the previews support.
3. **`gif_simple` and `gif_annotated` are derived distribution formats** —
   downsampled conveniences compiled from the same previews, never sources.
4. **No GIF may become the sole surviving source of a stage.** (The existing
   convergence GIFs are acceptable as historical documentation only because
   `optimize.py` can re-emit their frames; s06 still requires canonical
   full-canvas previews of its own.)

## Output formats (targets, parameters TBD)

| id | role | description |
|---|---|---|
| `mp4_exhibition` | **primary** | high-resolution, tuned timing, for exhibition/web (codec/size/audio TBD) |
| `gif_annotated` | derived | with stage titles/captions — naming mirrors `annotated_convergence.gif` |
| `gif_simple` | derived | small, no text, stage-per-beat — mirrors `simple_convergence.gif` |

## Reuse of existing artifacts (no re-shooting)

- `extremities/outputs/*/{simple,annotated}_convergence.gif` — stage s06
  (2 808 / 2 987 recorded optimizer steps). Panel-local → must be re-rendered
  onto the full canvas for canonical previews; `extremities/optimize.py` can
  re-emit frames if needed.
- `decomposition/viz/L*_map.png` — stage s07, already full-canvas.
- `qa/removal_manifest.csv` + `qa/before_after_*.png` — stage s04: the cleanup
  animation can be *replayed* exactly (8 743 documented pixels, 24 components).
- `canny_final.tiff`, `diem_master_geometry_v1.tiff` — stages s03/s04 end states.
- `extremities/inputs/*/whole.png` — stage s05 starting partitions.

## Stages needing reconstruction (explicit)

| Stage | Blocker |
|---|---|
| s01 source map | the original official Paris 1:5000 map is **not in the repo** (upstream, author Mathis Koroglu) — must be obtained before this stage can be rendered |
| s02 rotation | derivable only once s01's source exists (angle −20.3° is known) |
| s00, s03–s07 | reconstructable from repo artifacts by future scripts — no external blockers |
| s08–s11 | future stages — captured as they happen (see capture rule below) |

## Capture rule (from now on)

Every future stage that changes the canvas (pilot generations, compositing
steps, seam ornaments) must add/refresh its manifest entry and commit its
canonical preview **in the same commit** as the work itself. That is what
makes the film reproducible instead of an afterthought.
