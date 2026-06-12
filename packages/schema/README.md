# raya-schema

Portable contracts and Python validation helpers for the reset baseline.

This package owns:

- `raya.yaml` schema,
- artifact manifest schema,
- page, quanta, links, navigation, index, official object, reference, runtime, execution-plan, cache, execution-results, and reviewed-output schemas,
- source course validators,
- artifact validators.

Reviewed-output validators parse colocated `_reviewed/execution/<target>/reviewed.yaml`, check source/runtime/input/review/file hashes, require current reviewed output for `policy: frozen`, and validate manifest-declared `data/reviewed-outputs.json` plus copied files.

It supports Glintstone and future domains without making renderer choices canonical.
