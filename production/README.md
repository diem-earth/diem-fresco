# production/ — Deliverable 1: the final fresco

Everything required to go from validated generation output to the printed,
monumental artwork. This layer **consumes** canonical artifacts (see
[registry/artifacts.yaml](../registry/artifacts.yaml)) — it never redefines
geometry.

```
specs/fresco.yaml    canonical machine-readable production spec (draft v0 — TBDs are real open decisions)
previews/            composition previews (downsampled assemblies for review)     [empty]
masters/             full-resolution archival masters                             [empty]
print/               print-ready deliverables                                     [empty]
validation/          validation records (ink-integrity checks, dimension proofs)  [empty]
```

Rules:

- `specs/fresco.yaml` must reach `status: approved` before any compositing
  code is written against it. Code must fail loudly on any `TBD` it needs.
- Masters and print files are heavy binaries → Git LFS (already covered by
  `.gitattributes` patterns).
- Every file in `masters/` or `print/` must have a matching record in
  `validation/` before it is treated as deliverable.
