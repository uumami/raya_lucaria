## Why

Raya Lucaria now has working static/artifact contracts, but documentation is not yet a first-class requirement for accepted changes. This leaves contributors, professors, students, and agents dependent on scattered guidance, examples, or specs, and it already allowed archived specs with `Purpose: TBD` placeholders.

Foundation files justify the change: `docs/foundation/13_truth_surfaces.md` separates authority surfaces, `docs/foundation/15_system_overview.md` names contributors/professors/students/agents as newcomer audiences, and `docs/foundation/12_legacy_salvage.md` preserves the principle that docs and code-agent guidance must be explicit.

## What Changes

- Define documentation as its own current truth surface, below foundation/specs and separate from examples, course content, and generated artifacts.
- Require future changes to identify documentation impact for contributors/collaborators, professors, students, and agents.
- Require role documentation for those audiences to exist as separate English and Spanish role directories with `index.md` pages, while code, paths, commands, schemas, and package names remain English.
- Require docs tasks when a change affects behavior, contracts, CLI commands, rendering, deployment, pedagogy, authority boundaries, or user-facing workflows.
- Add compact foundation guidance for documentation surfaces and keep `docs/foundation/00_index.md` accurate.
- Add OpenSpec config rules so proposals/specs/design/tasks include documentation coverage and documentation hygiene.
- Require archived/current specs to have meaningful `Purpose` sections, not `TBD` placeholders.
- Define a rendered documentation path as separate from class/course examples: docs remain readable as Markdown, and rendered docs or documentation fixtures may exercise Glintstone without becoming class canon or architecture by example.
- Salvage the legacy principle that role guides are useful, while rejecting old role guides, old renderer documentation, and old examples as current authority.

Minimum requirement: every relevant change states whether role documentation is needed, updates the smallest appropriate documentation surface with separate English and Spanish role directories when contributor/professor/student/agent docs are affected, and keeps examples/fixtures distinct from docs and course material.

Growth path: later proposals can add a richer docs site, role-specific guide structure, generated docs artifacts, documentation search, screenshots, math examples, and renderer capability showcases without changing the authority hierarchy.

## Capabilities

### New Capabilities

- `documentation-surface-baseline`: documentation authority, audience coverage, rendered-doc separation, and documentation hygiene requirements.

### Modified Capabilities

- `dev-workflow-baseline`: future changes must include documentation impact/tasks and documentation validation where appropriate.
- `static-render-resource-resolution`: rendered documentation or documentation fixtures that exercise Glintstone must use the static read path while remaining separate from course/class examples.

## Impact

- Updates `docs/foundation/13_truth_surfaces.md` and, if useful, adds a compact foundation documentation-surface file referenced by `docs/foundation/00_index.md`.
- Updates `openspec/config.yaml` proposal/spec/design/task rules for documentation coverage and documentation hygiene.
- Updates current root/package guidance where it affects contributor or agent workflows.
- Defines separate English and Spanish role-documentation directories for contributors/collaborators, professors, students, and agents.
- Adds or defines a small rendered documentation fixture only if needed to prove the separation between docs, examples, and course content; if added, it uses separate English and Spanish role directories.
- Adds OpenSpec spec deltas and focused tests/checks for docs hygiene, including no `Purpose: TBD` placeholders in current specs.
- Does not introduce a new renderer stack, web app, backend, identity system, or course pedagogy.
