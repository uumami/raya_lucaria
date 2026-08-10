# Persistent Workspace Course Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render the accepted Course map as the sole course navigation on every
generated workspace, with correct static links and no duplicate workspace rail.

**Architecture:** Extend the existing Course-map renderer with a workspace
mode that separates its link origin from an optional course-page context. Each
workspace uses the same map markup and local shell resources as a reader page,
but marks only its workspace destination current and omits reader-only
`Context`. Keep workspace tools and the main-content focused-page strip; remove
only duplicate discovery navigation chrome.

**Tech Stack:** Python 3.10, Raya Static builder, generated HTML/CSS/local
JavaScript, pytest, Playwright static-preview tests.

## Global Constraints

- Preserve static-only operation: no runtime fetches, external resources,
  accounts, or backend dependency.
- Do not add course source schema, learner state, analytics, progress,
  recommendations, or personalization.
- Generate every destination using `_relative_href(from_output_path, target)`;
  never introduce root-relative course links.
- On workspaces, exactly one Course map is rendered; `Context` is absent;
  the active workspace tile is the only `aria-current="page"` map link.
- A valid `?page=<page-id>` may orient a non-current map node and retain the
  existing main-content focused-page strip; it must not restore the legacy
  focused-page sidebar.
- Workspace map interactions are presentation-only: no source/artifact or
  learner-state writes, no unrelated preference writes, and no fetches.
- Run host and Docker archive checks sequentially, after focused tests pass.

---

## File Map

- `packages/static/src/raya_static/builder.py` — common Course-map renderer,
  workspace HTML call sites, local-resource references, and removal of duplicate
  workspace navigation renderers.
- `packages/static/src/raya_static/shell.py` — shared map initialization and
  safe workspace focus orientation when no reader learning rail exists.
- `packages/static/src/raya_static/shell_prepaint.py` — prepaint state that is
  valid for a map-only workspace shell.
- `packages/static/src/raya_static/rendering.py` — workspace placement rules
  for the shared map and removal of obsolete discovery-rail/command-bar rules.
- `packages/static/src/raya_static/discovery.py` — retain only workspace
  filtering/results/main-content focus behavior after rail-specific focus code
  moves to the shared shell.
- `docs/foundation/20_learning_renderer_contract.md` — replace the prohibition
  on Course-map shell behavior in discovery workspaces with the accepted shared
  map contract.
- `docs/guides/en/{students,contributors,agents,professors}/index.md` and
  `docs/guides/es/{estudiantes,colaboradores,agentes,profesores}/index.md` —
  explain stable workspace map navigation and remove claims about the separate
  discovery command bar or absent shell.
- `tests/contracts/test_static_builder.py` — generated-markup, resource,
  active-state, and relative-link assertions.
- `tests/contracts/test_documentation_surfaces.py` — required current
  documentation wording assertions.
- `tests/e2e/test_preview_static_read_path.py` — browser/static-path coverage
  for all five workspace pages.
- `tests/e2e/test_rail_collapse_contract.py` and
  `tests/e2e/test_rail_home_control.py` — extend existing map drawer/collapse
  contract coverage to a workspace fixture only where existing helpers apply.

### Task 1: Establish the renderer and documentation contract

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/{students,contributors,agents,professors}/index.md`
- Modify: `docs/guides/es/{estudiantes,colaboradores,agentes,profesores}/index.md`
- Modify: `tests/contracts/test_documentation_surfaces.py`

**Interfaces:**
- Consumes: the approved design at
  `docs/superpowers/specs/2026-08-09-persistent-workspace-course-map-design.md`.
- Produces: current truth stating that discovery workspaces use the persistent
  Course map and omit reader-only Context.

- [ ] **Step 1: Write failing documentation-contract assertions**

  Add a test named `test_workspace_course_map_contract_is_documented` that reads
  the foundation file and all eight role guides. Assert the foundation contains
  the exact phrases `persistent Course map`, `reader-only Context is absent`,
  and `must not fetch external resources`; assert each English guide contains
  `persistent Course map`; assert each Spanish guide contains `mapa de curso
  persistente`.

  ```python
  def test_workspace_course_map_contract_is_documented() -> None:
      foundation = (ROOT / "docs/foundation/20_learning_renderer_contract.md").read_text()
      assert "persistent Course map" in foundation
      assert "reader-only Context is absent" in foundation
      assert "must not fetch external resources" in foundation
  ```

- [ ] **Step 2: Run the documentation test and verify it fails**

  Run:

  ```bash
  UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_documentation_surfaces.py::test_workspace_course_map_contract_is_documented
  ```

  Expected: FAIL because the current foundation prohibits the Course map on
  discovery workspaces.

- [ ] **Step 3: Amend the smallest truth and guide surfaces**

  Replace the discovery-workspace paragraph in
  `20_learning_renderer_contract.md` with wording that permits one persistent
  Course map and its local shell resources on Search, Graph, Practice, Tasks,
  and Schedule. State that the map has correct generated relative links, one
  active workspace tile, no current tree link, no `Context`, volatile
  filtering/focus, no external fetch, and no learner/source/artifact state.

  Update the four English and four Spanish guide indexes to describe the same
  navigation. Remove statements that workspaces render
  `.raya-discovery-command-bar`, do not load `shell.js`, or expose all eight
  reader commands. Preserve documentation of workspace-local filters, results,
  and the main-content focused-page strip.

- [ ] **Step 4: Run the documentation test and affected current tests**

  Run:

  ```bash
  UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_documentation_surfaces.py
  ```

  Expected: PASS after updating any exact wording assertions affected by the
  old workspace-chrome contract.

- [ ] **Step 5: Commit the contract update**

  ```bash
  git add docs/foundation/20_learning_renderer_contract.md docs/guides tests/contracts/test_documentation_surfaces.py
  git commit -m "Document persistent workspace course map"
  ```

### Task 2: Make the Course-map renderer workspace-aware

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `tests/contracts/test_static_builder.py`

**Interfaces:**
- Consumes: `ContentModel`, `_relative_href`, map command renderers, and the
  `STATIC_*_PATH` constants.
- Produces: `_render_course_map(..., from_output_path: str,
  current_page: ContentPage | None, current_workspace: str | None = None)`
  whose links are always based on `from_output_path`.

- [ ] **Step 1: Write failing generated-HTML tests for a deep workspace**

  Add a focused test building `examples/courses/render-fixture` and loading
  `artifact/site/_raya/schedule/index.html`. Assert:

  ```python
  assert html.count('id="raya-course-map"') == 1
  assert 'class="raya-discovery-course-rail"' not in html
  assert 'class="raya-discovery-command-bar"' not in html
  assert 'href="../../index.html"' in html
  assert 'href="../search/index.html"' in html
  assert 'data-raya-current-workspace="schedule"' in html
  assert 'aria-current="page"' in _workspace_command_html(html, "schedule")
  assert 'raya-command-context' not in _element_html(html, '<nav id="raya-course-map"', '</nav>')
  ```

  Add the analogous parameterized assertions for Search, Graph, Practice, and
  Tasks, each with its own current workspace and expected relative home link.

- [ ] **Step 2: Run the focused static-builder test and verify it fails**

  Run:

  ```bash
  UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k workspace_course_map
  ```

  Expected: FAIL because workspace HTML currently contains the discovery rail
  and command bar, not `#raya-course-map`.

- [ ] **Step 3: Implement the smallest renderer signature change**

  Change `_render_course_map` so `from_output_path` determines all calls to
  `_relative_href`, while `current_page` is optional and only determines tree
  `aria-current`, breadcrumbs, direct-page counts, and current-path expansion.
  Add `current_workspace` to `_render_course_map_tools`; apply
  `aria-current="page"` and `data-raya-current-workspace` only to that compact
  workspace link. When `current_page is None`, render no current tree link and
  use global workspace destinations without a page query.

  Keep reader-page call sites passing their `page.output_path` and `page` so
  their output is unchanged. Use workspace call sites with
  `from_output_path=STATIC_<WORKSPACE>_PATH.as_posix()`,
  `current_page=None`, and the matching workspace name.

- [ ] **Step 4: Run static-builder tests and inspect generated paths**

  Run:

  ```bash
  UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "workspace_course_map or course_map"
  UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
  ```

  Expected: PASS; each `_raya/*/index.html` has exactly one Course map and all
  map destinations are relative to that workspace path.

- [ ] **Step 5: Commit the map-renderer change**

  ```bash
  git add packages/static/src/raya_static/builder.py tests/contracts/test_static_builder.py
  git commit -m "Reuse course map in workspaces"
  ```

### Task 3: Integrate the shared map shell and remove duplicate workspace chrome

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `packages/static/src/raya_static/shell_prepaint.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/discovery.py`
- Modify: `tests/contracts/test_static_builder.py`

**Interfaces:**
- Consumes: workspace-aware `_render_course_map`, `shell_resources()`, map
  prepaint resources, and existing discovery focus parsing.
- Produces: a map-only workspace shell that supports map drawer/collapse,
  filtering, focus orientation, and existing workspace controls without the
  legacy rail.

- [ ] **Step 1: Write failing resource and focus tests**

  Add tests asserting every workspace HTML includes local shell-prepaint,
  `shell.js`, and comfort-prepaint paths relative to its output path; its root
  document carries the map state and course-id data required by `shell.js`; and
  it includes the mobile Course-map opener. Add a `?page=reader-ux` fixture
  assertion that the tree contains a focused-node marker but no tree
  `aria-current` link and no `data-raya-discovery-rail-page-focus` element.

- [ ] **Step 2: Run the focused tests and verify they fail**

  Run:

  ```bash
  UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "workspace_course_map and (resources or focus)"
  ```

  Expected: FAIL because workspaces omit shell/prepaint assets and focus is
  currently owned by discovery-rail selectors.

- [ ] **Step 3: Implement a map-only workspace shell, not a second map**

  Add the existing local shell/prepaint/comfort assets and the minimal document
  data attributes required by the Course map to each workspace renderer.
  Make `shell.py` tolerate `#raya-course-map` without a learning rail or
  `#raya-article`: its map behavior remains active, but reader-only actions do
  nothing because they are not rendered. Move valid `?page=` parsing and map
  node orientation from discovery-rail-only selectors into the shared shell;
  keep main-content strip/result logic in `discovery.py`.

  Place the shared map in the workspace shell grid as the only course
  navigation. Remove `_render_discovery_course_rail` and
  `_render_discovery_command_bar` call sites, their obsolete DOM state, and CSS
  selectors that exclusively support those components. Do not remove workspace
  control/result/context panels or the focused-page strip.

- [ ] **Step 4: Run renderer tests for resource and shell parity**

  Run:

  ```bash
  UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k workspace_course_map
  UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_rail_collapse_contract.py tests/e2e/test_rail_home_control.py
  ```

  Expected: PASS; reader pages retain their existing rail behavior and each
  workspace has a functioning map-only shell with no duplicate IDs.

- [ ] **Step 5: Commit the workspace-shell integration**

  ```bash
  git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/shell.py packages/static/src/raya_static/shell_prepaint.py packages/static/src/raya_static/rendering.py packages/static/src/raya_static/discovery.py tests
  git commit -m "Integrate course map with workspaces"
  ```

### Task 4: Prove static-path, keyboard, drawer, and state safety across workspaces

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `tests/e2e/test_rail_collapse_contract.py`

**Interfaces:**
- Consumes: the rendered five workspace paths and the shared Course-map
  selectors from Tasks 2–3.
- Produces: browser evidence that the common map works from static deep paths
  without duplicate navigation or unintended state.

- [ ] **Step 1: Write a parameterized failing browser test**

  Parameterize over `search`, `graph`, `practice`, `tasks`, and `schedule`.
  For each `/_raya/<workspace>/index.html`, assert in Playwright that:

  ```python
  assert page.locator("#raya-course-map").count() == 1
  assert page.locator(".raya-discovery-course-rail").count() == 0
  assert page.locator(".raya-discovery-command-bar").count() == 0
  assert page.locator("[data-raya-current-workspace]").get_attribute("data-raya-current-workspace") == workspace
  assert page.locator("#raya-course-map a[aria-current='page']").count() == 1
  ```

  Resolve the clicked Home, Search, and a tree-link URLs against the current
  deep page and assert they remain inside the preview's mounted course prefix.
  At a phone viewport, open then close the map drawer with keyboard activation
  and assert focus returns to the opener. Assert a `?page=reader-ux` load keeps
  the map visible and the main-content focus strip visible. Record
  `localStorage`, `sessionStorage`, and resource requests before/after map
  interaction and assert no new storage key or network request is introduced.

- [ ] **Step 2: Run the browser test and verify it fails before the integration**

  Run:

  ```bash
  UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k workspace_course_map
  ```

  Expected: FAIL until the workspace integration satisfies the browser-level
  link, focus, drawer, and state assertions; static markup checks alone do not
  establish those behaviors.

- [ ] **Step 3: Make only test-driven fixes discovered by the browser**

  Correct relative paths, focus restoration, map-only shell guards, drawer
  inertness, or layout overflow only when a named assertion from Step 1 fails.
  Keep the fix in the shared renderer/shell; do not add course-specific or
  workspace-specific link patches.

- [ ] **Step 4: Run focused browser and render-debug verification**

  Run:

  ```bash
  UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k workspace_course_map
  ./scripts/check-render-debug.sh
  ```

  Expected: PASS, including no horizontal overflow and one usable map scroll
  region at the tested desktop and phone widths.

- [ ] **Step 5: Commit the browser coverage**

  ```bash
  git add tests/e2e/test_preview_static_read_path.py tests/e2e/test_rail_collapse_contract.py packages/static
  git commit -m "Verify workspace course map behavior"
  ```

### Task 5: Run repository gates and update IA O26 only after framework merge

**Files:**
- Modify after framework merge: `/home/uumami/itam/ia_o26/.github/workflows/pages.yml`

**Interfaces:**
- Consumes: the merged immutable framework commit and IA O26's existing pinned
  `framework_ref`/checkout revision.
- Produces: an IA O26 deployment rebuilt by the corrected shared renderer.

- [ ] **Step 1: Run host checks**

  Run:

  ```bash
  ./scripts/check.sh
  ```

  Expected: PASS.

- [ ] **Step 2: Run Docker checks after host checks finish**

  Run:

  ```bash
  ./scripts/check-docker.sh
  ```

  Expected: PASS.

- [ ] **Step 3: Merge the reviewed framework change and record its immutable SHA**

  Use the repository's normal reviewed merge flow. Verify the target branch
  contains the commits from Tasks 1–4 and record the resulting full commit SHA.

- [ ] **Step 4: Advance only the IA O26 pinned framework revision**

  In `/home/uumami/itam/ia_o26/.github/workflows/pages.yml`, replace the
  existing pinned framework revision with the full merged SHA. Do not change
  course source, deployment permissions, or DNS configuration.

- [ ] **Step 5: Verify the course deployment**

  Push the workflow-only course commit, wait for its `Verify and publish
  course` workflow to succeed, then fetch:

  ```bash
  curl --fail --silent --show-error --location https://rayalucaria.org/ia_o26/_raya/schedule/
  ```

  Confirm the response contains `id="raya-course-map"`, has no
  `raya-discovery-course-rail`, and that the generated home/link targets retain
  the `/ia_o26/` prefix when resolved in a browser.

- [ ] **Step 6: Commit the course revision separately**

  ```bash
  git -C /home/uumami/itam/ia_o26 add .github/workflows/pages.yml
  git -C /home/uumami/itam/ia_o26 commit -m "Update Raya framework revision"
  ```

## Plan Self-Review

- Spec coverage: Tasks 1–4 cover foundation truth, one shared map, workspace
  state, Context omission, shared shell, focus preservation, link correctness,
  duplicate-chrome removal, accessibility/state safety, and responsive browser
  evidence. Task 5 covers sequential gates and the downstream course update.
- No-placeholder scan: the plan has concrete files, test names, selectors,
  commands, expected failures, and commit boundaries; it contains none of the
  prohibited placeholder markers.
- Type consistency: `_render_course_map` receives `from_output_path`, optional
  `current_page`, and optional `current_workspace`; all later tasks use that
  same model. Browser assertions require one active workspace map link and no
  current course-tree link, as defined by the design.
