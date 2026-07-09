Status: DONE

Summary:
- Updated `docs/foundation/20_learning_renderer_contract.md` to match the rebuilt reader shell: left rail search plus compact two-per-row command tiles, default expanded rail behavior at the approved `894px+` breakpoint, and stronger inertness wording for collapsed or hidden rail content.
- Updated `docs/guides/en/students/index.md` with the same reader-shell guidance in student-facing language.
- Updated `docs/guides/es/estudiantes/index.md` with the same reader-shell guidance in Spanish while preserving English technical identifiers.

Checks:
- Task 5 stale-guidance `rg` check: found stale wording in the foundation contract and both student guides.
- Doc hygiene `rg` check: no stale `reader top bar`, `top command bar`, `raya-course-map-tool-grid`, or `Course Workspaces` guidance remains in the checked surfaces.

Concerns:
- `docs/guides/en/agents/index.md` and `docs/guides/es/agentes/index.md` still mention `Course Tools`, but they were outside Task 5 ownership and were not changed here.
