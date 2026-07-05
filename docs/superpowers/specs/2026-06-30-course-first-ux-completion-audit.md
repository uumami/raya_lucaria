# Course-First UX Completion Audit

Date: 2026-06-30

## Question

Has the active Course-First UX Goal reached a defensible stopping point without
another conservative renderer loop?

## Authority Checked

- `docs/foundation/13_truth_surfaces.md`
- `docs/foundation/15_system_overview.md`
- `docs/foundation/19_learning_science_principles.md`
- `docs/foundation/20_learning_renderer_contract.md`
- `docs/superpowers/course-first-ux-goal.md`

## Audit Result

The goal is complete for the current static-renderer baseline. The five
suggested loops in `docs/superpowers/course-first-ux-goal.md` have implementation
and verification evidence, and no additional course-first UX loop is required
before handing the work back.

This does not mean future renderer work is finished. It means the active goal's
mental model is now represented in current guidance, static shell behavior,
generated workspaces, skin authority, density behavior, role documentation, and
test coverage.

## Requirement Evidence

### Static Authority And Contract Boundaries

Evidence:

- Root guidance now treats local Search and Graph as current Glintstone static
  renderer behavior while keeping backend, TypeScript UI, dynamic graph state,
  and cross-course graph features out of the current baseline.
- `docs/foundation/06_artifact_contract.md` and
  `docs/foundation/18_known_missing_work.md` describe the accepted static
  surfaces without reinstating legacy renderer architecture.
- `scripts/check-hygiene.sh` rejects stale graph/search guidance drift.

Verification:

- `./scripts/check-hygiene.sh`
- `tests/contracts/test_hygiene_scripts.py`

### Course-First Reader Shell

Evidence:

- Reader pages expose course position, hierarchy, previous/next sequence,
  course workspaces, article-first layout, page brief, page support, graph
  context, and responsive shell controls.
- Collapsed course-map and learning-rail behavior uses compact readable tabs,
  returns article width, avoids focus leaks, and remains desktop-scoped where
  the contract requires it.

Verification:

- `tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell`
- `tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position`
- `tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_shell_layout_and_accessibility`
- `tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_navigation_spine_is_coherent`
- `tests/e2e/test_preview_static_read_path.py::test_render_fixture_collapsed_reader_rails_expand_article_width_independently`
- `tests/e2e/test_preview_static_read_path.py::test_render_fixture_collapsed_reader_rails_use_compact_horizontal_tabs`
- `tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading`

### Generated Workspaces As Course Tools

Evidence:

- Search, Graph, Practice, Tasks, and Schedule share course identity, current
  workspace marking, related workspace links, a course rail, and page-focus
  handoff paths back to reading.
- Workspace pages keep local static behavior and reject storage or network
  dependencies outside the documented static path.

Verification:

- `tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface`
- `tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface`
- `tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace`
- `tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace`
- `tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace`
- `tests/e2e/test_preview_static_read_path.py::test_discovery_workspaces_show_shared_page_focus_strip`
- `tests/e2e/test_preview_static_read_path.py::test_discovery_workspaces_render_static_course_rail_without_storage`
- `tests/e2e/test_preview_static_read_path.py::test_discovery_command_bar_marks_current_workspace_without_overflow`
- `tests/e2e/test_preview_static_read_path.py::test_graph_page_focus_exposes_return_to_reading_path`

### Skin Authority And Density

Evidence:

- Source-selected course and section skins remain the only browser-facing skin
  authority for default student pages.
- Default student pages no longer emit browser skin override scripts, toolbar
  commands, storage keys, or override attributes.
- Skin density tokens drive repeated workspace cards, action links, control
  height, control padding, control gaps, and discovery spacing without shrinking
  article text.

Verification:

- `tests/contracts/test_static_skins.py::test_render_skin_css_maps_density_to_spacing_variables`
- `tests/contracts/test_static_skins.py::test_rich_render_css_consumes_font_and_density_tokens`
- `tests/contracts/test_static_builder.py::test_build_applies_course_skin_to_pages_and_writes_skin_css`
- `tests/e2e/test_preview_static_read_path.py::test_render_fixture_uses_authored_skin_without_browser_override`
- `tests/e2e/test_preview_static_read_path.py::test_compact_skin_makes_discovery_cards_dense_without_shrinking_article_text`
- `tests/e2e/test_preview_static_read_path.py::test_render_fixture_command_bar_controls_are_dense_and_operable`

### Learner-State And Privacy Language

Evidence:

- Static reader and workspace pages avoid progress, mastery, recommendation,
  ranking, scoring, submission, grading, and personalization claims.
- Browser storage remains limited to documented comfort preferences.
- Browser-facing workspace/search/graph payloads are scanned for private support
  paths and stale generated internals by the existing static-read-path gates.

Verification:

- `tests/contracts/test_static_builder.py::test_render_fixture_search_graph_course_map_visible_text_avoids_learner_state_language`
- `tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_works_without_storage`
- `tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_ignores_saved_expanded_state_on_load`
- `tests/e2e/test_preview_static_read_path.py::test_render_fixture_math_renders_in_browser_without_external_requests`
- `./scripts/check-render-debug.sh`

### Role Documentation And Tutorial Impact

Evidence:

- English and Spanish role docs for students, professors, contributors, and
  agents describe the current course-first shell, static workspaces, graph/search
  reality, source-selected skins, comfort preferences, and no browser override
  contract.
- Root `README.md` and `AGENTS.md` agree with the same source-layout and current
  renderer guidance.

Verification:

- `docs/guides/en/students/index.md`
- `docs/guides/en/professors/index.md`
- `docs/guides/en/contributors/index.md`
- `docs/guides/en/agents/index.md`
- `docs/guides/es/estudiantes/index.md`
- `docs/guides/es/profesores/index.md`
- `docs/guides/es/colaboradores/index.md`
- `docs/guides/es/agentes/index.md`
- `README.md`
- `AGENTS.md`

## Final Gate Evidence

The final implementation loop passed these gates sequentially after the last
renderer and role-doc changes:

- `git diff --check`
- `./scripts/check-hygiene.sh`
- `./scripts/check-render-debug.sh`
- `./scripts/check.sh`
- `./scripts/check-docker.sh`

Recorded results:

- Host pytest: `555 passed in 1049.20s (0:17:29)`
- Docker pytest: `555 passed in 1135.87s (0:18:55)`
- Render-debug: `129 check(s)` passed in explicit host runs and inside host and
  Docker gates.

The completion audit itself changes only Superpowers documentation. It requires
`git diff --check` and `./scripts/check-hygiene.sh` before final completion, not
a full renderer rebuild.

## Decision

No next loop is selected. The active Course-First UX Goal can be marked complete
after the audit documentation passes the lightweight final gates above.
