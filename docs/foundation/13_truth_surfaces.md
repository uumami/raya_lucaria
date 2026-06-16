---
id: docs-truth-surfaces
title: Truth Surfaces
summary: Authority hierarchy for foundation docs, specs, documentation, examples, and history.
status: ready
---
# Truth Surfaces

Raya Lucaria must keep current truth separate from implementation, examples, tooling, and history.

## Authority Hierarchy

After the reset:

1. `docs/foundation/` is the seed truth.
2. Future OpenSpec specs are generated from foundation decisions.
3. Current documentation explains accepted behavior and role workflows.
4. Root guidance explains how to work in the current repository.
5. Package READMEs describe implemented package boundaries.
6. Examples are fixtures only.
7. Git history and old branches are historical reference.

If any lower surface conflicts with foundation docs, the lower surface is wrong until a new decision updates the foundation.

## Surface Classes

| Class | Role |
| --- | --- |
| Foundation | current architecture, pedagogy, ownership, portability, and iteration truth |
| Decision records | explicit accepted choices and rejected alternatives |
| Specs | testable requirements generated from current foundation |
| Documentation | explanatory guidance for contributors/collaborators, professors, students, and agents |
| Package docs | status and ownership of implemented packages |
| Examples | minimal fixtures, never pedagogy by accident |
| Rendered docs | generated documentation artifacts or fixtures, not source authority |
| Tooling adapters | workflow support for agents/editors |
| History | inspiration and recovery, not current authority |

## Reset Discipline

Do not preserve stale material in the current tree just because it exists. If old code or docs contain a useful idea, copy the principle into a current proposal and rebuild it under current contracts.

## Documentation Discipline

Documentation explains current accepted behavior and points back to the relevant foundation or spec authority. It must not override foundation docs or accepted specs, and it must stay separate from examples, course/class material, generated artifacts, and history.

Role documentation for contributors/collaborators, professors, students, and agents uses separate English and Spanish role directories with index pages. Code identifiers, package names, commands, schema fields, file paths, domain names, and stable IDs remain in English.

Documentation should remain readable as plain files. Rendered documentation can exercise Glintstone, but rendered output is a generated artifact and not a higher authority surface.

For numbered objects, authored fenced directives and `raya.yaml`
`render.numbered_objects` configuration are source authoring truth. Rendered
pages are reader-facing views that show labels, numbers, anchors, and static
cross-reference links. Manifest-declared `data/numbered-objects.json` is the
machine-readable artifact truth for object IDs, numbers, source paths, output
paths, anchors, hrefs, and reference text.

## What May Be Deleted

On a from-zero reset, it is acceptable to delete:

- legacy implementation packages,
- legacy examples,
- generated artifacts,
- archived specs,
- old role guides,
- old renderer documentation,
- stale workflows.

The foundation docs are the surviving memory.
