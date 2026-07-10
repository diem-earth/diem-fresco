# process_film/scripts/ — render & assembly tooling (placeholder)

Planned (nothing implemented yet):

- `render_stage.py <stage_id>` — build one stage's canonical preview(s) from
  `../manifest/stages.json`, enforcing the full-canvas rules.
- `assemble.py --format gif_simple|gif_annotated|mp4_exhibition` — compile
  `../outputs/<format>.*` strictly from the manifest (order, durations,
  transitions). Must fail on any stage whose `status` isn't `preview_ready`,
  unless `--allow-placeholders` renders marked placeholder cards.

Rendered outputs land in `../outputs/` (gitignored — always regenerable).
