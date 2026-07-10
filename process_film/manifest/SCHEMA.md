# Process-film stage manifest — schema (v0.2)

`stages.json` is the canonical, machine-readable description of the film.
Renderers consume it; humans edit it.

**Narrative vs chronology.** The film's playback order is *dramaturgical* — it
may differ from actual project history (e.g. the extremity optimization
predates the center decomposition, but plays after it). Both are preserved:
`order` is the narrative playback order; `chronology_note` records what
actually happened when. Renderers use `order`; historians use
`chronology_note`. The file-level `order_semantics` field restates this.

One record per stage:

| Field | Type | Meaning |
|---|---|---|
| `id` | str | `sNN_slug`, stable forever (renderers key on it) |
| `order` | int | **narrative** playback order (== NN; kept explicit for reordering safety) |
| `chronology_note` | str | project-history record: when the underlying work actually happened, and where narrative deliberately diverges |
| `title` | str | caption used by `gif_annotated` / `mp4_exhibition` |
| `status` | str | `reconstructable` — inputs in repo, preview not yet rendered · `blocked_missing_source` — needs an artifact the repo doesn't have · `future` — the stage itself hasn't happened yet · `preview_ready` — canonical preview exists at `preview` |
| `source_artifacts` | list[str] | repo-relative paths this stage renders from (`[]` + note if missing) |
| `generator` | str\|null | command/script that (re)builds the preview; null until scripts exist |
| `git_ref` | str\|null | commit/tag where the underlying work landed; null for future stages |
| `preview` | str | canonical preview path under `previews/` (placeholder until `preview_ready`) |
| `duration_s` | number | proposed on-screen duration (all values draft until a full-cut review) |
| `transition` | str | transition *into* this stage: `cut` \| `crossfade` \| `progressive_reveal` (content draws itself in) |
| `notes` | str | reuse pointers, blockers, reconstruction hints |

File header: `schema_version`, `canvas` (px + proposed preview downsample),
`formats` (the three output targets). Status moves
`blocked_missing_source|reconstructable → preview_ready` only when the file at
`preview` exists and follows the full-canvas rules in `../README.md`.
