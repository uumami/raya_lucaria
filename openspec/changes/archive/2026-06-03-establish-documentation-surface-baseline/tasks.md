## 1. Contract And Hygiene Tests

- [x] 1.1 Add a focused documentation-hygiene test that current specs under `openspec/specs/` do not contain `Purpose: TBD` placeholders.
- [x] 1.2 Add a focused test or check that `openspec/config.yaml` requires role-documentation impact and documentation tasks for relevant changes.
- [x] 1.3 Add a focused test or check that role documentation uses separate English and Spanish role directories instead of mixed-language pages.
- [x] 1.4 Add fixture/check coverage that rendered documentation fixtures remain labeled and separate from class/course examples.
- [x] 1.5 Add e2e/static-read-path coverage for the rendered documentation fixture if the implementation adds one.

## 2. Foundation And OpenSpec Guidance

- [x] 2.1 Update `docs/foundation/13_truth_surfaces.md` so documentation is a distinct current truth surface below foundation/specs and separate from examples.
- [x] 2.2 Add compact foundation documentation-surface guidance, or update the smallest existing foundation file, to define contributor/collaborator, professor, student, and agent documentation responsibilities and separate English/Spanish role-directory expectations.
- [x] 2.3 Keep `docs/foundation/00_index.md` and `docs/foundation/15_system_overview.md` accurate after the documentation-surface update.
- [x] 2.4 Update `openspec/config.yaml` proposal/spec/design/task rules to require role-documentation impact, separate English/Spanish role directories, docs tasks when needed, rendered-doc separation, and spec purpose hygiene.

## 3. Documentation Surfaces

- [x] 3.1 Add compact role-oriented documentation entrypoints for contributors/collaborators, professors, students, and agents.
- [x] 3.2 Keep role docs readable as plain Markdown with separate English and Spanish role directories, without requiring a rendered site, backend, hosted service, or frontend build.
- [x] 3.3 Update root and agent guidance to point at the new documentation surface without making it outrank foundation docs or accepted specs.
- [x] 3.4 Fix current `openspec/specs/*/spec.md` `Purpose: TBD` placeholders with concise capability purpose text.
- [x] 3.5 Backfill current role-documentation entrypoints with separate English and Spanish role directories where needed.

## 4. Rendered Documentation Boundary

- [x] 4.1 Add a small documentation fixture or rendered-doc source separate from `examples/courses/minimal` and class/course examples.
- [x] 4.2 Label the rendered documentation fixture as documentation/fixture material and point it back to `docs/foundation/` and role docs as authority surfaces.
- [x] 4.3 Build the rendered documentation fixture through the current Glintstone static path and verify its local assets and links remain deployment-neutral.
- [x] 4.4 Confirm the rendered documentation fixture keeps English and Spanish role guidance in separate role directories.
- [x] 4.5 Confirm the rendered documentation fixture does not introduce a new renderer stack, web UI, backend, identity provider, or course pedagogy.

## 5. Verification

- [x] 5.1 Run local focused docs-hygiene/role-language-page tests and any added e2e/static-read-path tests.
- [x] 5.2 Run local `pytest -q`.
- [x] 5.3 Run Docker Compose `uv run pytest -q`.
- [x] 5.4 Run `openspec validate establish-documentation-surface-baseline --strict`.
- [x] 5.5 Run `openspec validate --specs --strict`.
- [x] 5.6 Confirm no generated documentation or example artifact output is committed.
