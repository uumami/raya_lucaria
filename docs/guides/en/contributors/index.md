---
id: docs-guides-en-contributors
title: Contributors And Collaborators
nav_title: Contributors
summary: Workflow guidance for changing code, specs, docs, tests, and contracts safely.
status: ready
---
# Contributors And Collaborators

Start with `docs/foundation/15_system_overview.md`, then `docs/foundation/13_truth_surfaces.md`, then the accepted OpenSpec specs for the capability you are changing.

Use the Docker Compose and `uv` commands from `README.md` and `AGENTS.md` when changing code, contracts, docs, or tests. Keep package paths, commands, schema fields, and stable IDs in English.

When changing course validation or rendering, preserve the convention-first source model: `source: course` points at the ordered `course/` tree, ordered filenames define authoring order, frontmatter `id` defines stable identity, colocated `_official/` and `_assets/` stay private, and `navigation.json` plus `indices.json` are generated artifact data. Tests should cover source diagnostics, official object export, asset copying, artifact schemas, and static-read-path rendering.

Current documentation is also a renderable docs course. Edit the readable pages under `docs/foundation/` and `docs/guides/`, keep `docs/render-content/` aligned for rendered order, and treat `docs/artifact/` as ignored generated output. Use `raya validate docs`, `raya build docs`, and static-read-path tests when changing documentation rendering behavior.

For substantial changes, state the documentation impact for contributors/collaborators, professors, students, and agents. If role documentation changes, keep the English and Spanish pages separate.
