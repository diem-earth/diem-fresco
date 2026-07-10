# public_export/ — Deliverable 2: the future public repository (planning layer)

**No public repo exists yet. Nothing here is published.** This layer defines
the boundary and the mechanism for eventually generating one.

## Purpose of the future public repo

Publish the **method**, not the workbench: enough for a reader to understand
and reproduce the pipeline — city map → canonical line-work master →
multi-scale decomposition → area-proportional region panels → mask-conditioned
generation → composited fresco — or to build a similar fresco for another city.
It is explicitly **not** a mirror of this private repository.

## Boundary model: allowlist, deny-wins — **inclusion list is PROVISIONAL**

- Nothing is exported unless it matches `manifests/include_candidates.txt`.
- `manifests/exclude.txt` holds **mandatory exclusions** and always wins.
- Anything matching neither list is private by default.

The boundary *model* is approved in principle; the exact inclusion list is
**not** — every include entry is a candidate pending the review gates below.
No export may run until each gate is explicitly cleared.

## Review gates (all open)

| Gate | Question | Known facts (docs/DATA_PROVENANCE.md) |
|---|---|---|
| Paris source-map rights | may derivatives of the upstream official plan be published? | recorded as *"check upstream map license before public release of derivatives"*; the raw map is not in the repo |
| OSM / ODbL | attribution + share-alike implications for the Overpass extracts and geometry derived from them | ODbL 1.0, attribution *© OpenStreetMap contributors* — recorded |
| Paris Open Data | attribution for arrondissements/quartiers geojsons | **Licence Ouverte v2 (Etalab)**, attribution *Ville de Paris* — recorded (not ODbL) |
| INSEE figures | region surface data used by the optimizer | recorded as factual data, no license constraint; attribute as courtesy |
| Decomposition metadata | is `decomposition/meta/*.json` appropriate to publish? its geometry (bboxes, centroids, cells) derives from the upstream map | tied to the source-map gate |
| Internal reports | do PHASE1–4 / MASTER_GEOMETRY_REPORT need rewriting before publication? | assess per file at export time |
| Prompt & artwork IP | curated prompts stay private (decided); what resolution of the artwork, if any, is published? | open artistic/commercial decision |

### Included (public)

- Method documentation: pipeline map, reproducibility notes, data provenance,
  the stage reports (rewritten/curated at export time where needed).
- The pipeline code: `qa/reproduce_master.py`, `pipeline/stage2/s01–s07`,
  `extremities/optimize.py`, `generation/scripts/build_prompt_tables.py`.
- Schemas (prompt tables, film manifest, fresco spec structure) — the *shape*
  of the data, without curated artistic content.
- Decomposition metadata (`decomposition/meta/*.json`) so the code runs.
- Selected visual assets: convergence GIFs, decomposition level maps,
  **downsampled** master-geometry and final-fresco previews (resolution TBD —
  artwork-rights decision), the process film outputs.

### Private (never exported)

- Full-resolution masters, print files, and generation outputs
  (the commercial artwork itself).
- Curated prompt text (`generation/prompt_tables/*.json|csv` — the artistic
  recipe; the schema and builder are public, the prompts are not).
- Internal state and process docs (`PROJECT_STATE.md`, `LLM_START_HERE.md`),
  rejected experiments, `imports/`, this `public_export/` layer itself.
- The workbench git history (contains experimentation and internal identities).
- Any personal data: emails, machine paths, git identities.

## Export mechanism (future script, not written yet)

1. `public_export/scripts/build_export.py` reads both manifests, copies
   include-matched files into a fresh directory, applies declared transforms
   (downsampling, README rewriting).
2. A **verifier pass** scans the result for excluded patterns, e-mail
   addresses, absolute paths, and prompt text before anything is published.
3. `git init` in the export directory — **fresh history, single snapshot
   commit**. The workbench history is never filtered, rewritten, or pushed.
4. Manual review, then push to the (future) public remote.

## Proposed public repo structure

```
README.md                 method overview, gallery, how-to-reproduce
LICENSE-CODE / LICENSE-ASSETS
docs/                     pipeline, reproducibility, provenance, stage reports
method/
  stage1_master/          reproduce_master.py + manifest + downsampled figures
  stage2_decomposition/   s01–s07 + meta JSONs + level maps
  extremities/            optimize.py + final_positions + convergence GIFs
  stage3_prompting/       SCHEMA.md + builder (no curated prompts)
gallery/                  downsampled fresco preview + process film (GIF/MP4)
```

## Licensing (known facts vs open decisions)

Known facts, recorded in `docs/DATA_PROVENANCE.md` and in-tree:

- `extremities/` code: **MIT (copyright 2025)** — license file at `extremities/LICENSE`.
- Paris Open Data geojsons: **Licence Ouverte v2**, attribution *Ville de Paris*.
- Overpass/OSM extracts: **ODbL 1.0**, attribution *© OpenStreetMap contributors*.
- INSEE region surfaces: factual data, no license constraint.

Open decisions (user's):

- License for this project's own code (proposed: MIT or Apache-2.0) — TBD.
- License for the public docs (proposed: CC BY 4.0) — TBD.
- Artwork / fresco imagery rights — TBD; likely all-rights-reserved with a
  limited-resolution preview.
- Upstream Paris plan rights — **must be verified** before any derivative
  (master geometry, decomposition, viz) is published; see review gates.
