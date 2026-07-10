# Reader Rail Session Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist explicit structural reader rail state per validated course across refresh and same-tab navigation without leaking state across courses, breaking responsive accessibility, or using durable storage.

**Architecture:** Render validated `course_id` and generated defaults on `<html>`, then load a synchronous, read-only shell prepaint resource before CSS. Store one versioned JSON rail pair and one versioned collapsed-branch array in `sessionStorage`; the deferred shell adopts the prepaint snapshot, writes only after explicit structural actions, and reconciles BFCache and responsive transitions without writes.

**Tech Stack:** Python 3.10 static renderer, generated JavaScript/CSS resources, pytest contract tests, Playwright Chromium e2e tests, Docker Compose reference gate.

## Global Constraints

- `docs/foundation/` remains highest truth; this loop changes the old no-shell-storage rule only for the versioned rail pair.
- Use validated `course_id` directly; never derive storage scope from root page ID, title, URL, deployment path, or lossy normalization.
- Use only `raya:reader-shell:v1:<course_id>` and `raya:course-map-branches:v1:<course_id>`.
- Rail state is exact JSON with only `courseMap` and `learningRail`, each `expanded` or `collapsed`.
- At `640px`-`893px`, at most one rail may be expanded; a restored both-expanded pair is effectively both-collapsed until an explicit action writes a valid pair.
- Phone course-map drawer and always-visible phone learning context remain non-persistent; do not add a phone learning-rail drawer.
- Prepaint is synchronous before CSS, read-only, exception-safe, and the only initialization storage read.
- No `localStorage`, cookies, fetch/XHR, backend, source-data, artifact-data, progress, mastery, recommendation, or personalization state.
- Ignore and never migrate or delete stale root-derived or origin-global keys.
- Preserve unrelated dirty work. Never stage `docs/superpowers/plans/2026-07-08-course-map-tiny-tray.md`.
- Run host, render-debug, smoke, and Docker checks sequentially.

---

## File Structure

- Create `packages/static/src/raya_static/shell_prepaint.py`: synchronous shell-state prepaint resource only.
- Modify `packages/static/src/raya_static/builder.py`: pass `course_id`, render root attributes, order prepaint, and write the resource.
- Modify `packages/static/src/raya_static/shell.py`: atomic explicit writes, responsive/BFCache reconciliation, and branch validation.
- Modify `packages/static/src/raya_static/rendering.py`: allow completed prepaint state to drive first paint.
- Modify `docs/foundation/20_learning_renderer_contract.md` and all EN/ES role guides: accept the bounded exception and remove contradictions.
- Modify `tests/contracts/test_static_builder.py`: generated resource, exact-key, and documentation contracts.
- Modify `tests/e2e/test_preview_static_read_path.py`: real browser persistence, isolation, first-paint, focus, BFCache, tab, and failure proofs.

---

### Task 1: Accept The Foundation And Role Contract

**Files:**
- Modify: `tests/contracts/test_static_builder.py:4873`
- Modify: `docs/foundation/20_learning_renderer_contract.md:23-36,189`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

**Interfaces:**
- Consumes: `docs/superpowers/specs/2026-07-09-reader-rail-session-persistence-design.md`.
- Produces: authoritative storage wording used by all later implementation tasks.

- [ ] **Step 1: Extend the documentation contract test so stale surfaces fail**

In `test_reader_shell_guidance_matches_left_rail_contract`, read all four roles in both languages:

```python
english_paths = tuple(ROOT / f"docs/guides/en/{role}/index.md" for role in (
    "contributors", "professors", "students", "agents"
))
spanish_paths = tuple(ROOT / f"docs/guides/es/{role}/index.md" for role in (
    "colaboradores", "profesores", "estudiantes", "agentes"
))
english_guides = tuple(" ".join(path.read_text(encoding="utf-8").split()) for path in english_paths)
spanish_guides = tuple(" ".join(path.read_text(encoding="utf-8").split()) for path in spanish_paths)

assert "raya:reader-shell:v1:<course_id>" in foundation
assert "raya:course-map-branches:v1:<course_id>" in foundation
assert "explicit structural rail display pair" in foundation.lower()
assert "course-map branch expansion is the only accepted same-tab exception" not in foundation.lower()
assert not ("browser storage must not store" in foundation.lower() and "shell collapse state" in foundation.lower())

for text in english_guides:
    lowered = text.lower()
    assert "course-scoped" in lowered
    assert "sessionstorage" in lowered
    assert "structural rail" in lowered
    assert "rail choice is non-persistent" not in lowered

for text in spanish_guides:
    lowered = text.lower()
    assert "con scope de curso" in lowered
    assert "sessionstorage" in lowered
    assert "rieles estructurales" in lowered
```

- [ ] **Step 2: Run the test and verify red**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_reader_shell_guidance_matches_left_rail_contract
```

Expected: FAIL because foundation still names branch state as the only exception and other role guides still call rail/shell state non-persistent.

- [ ] **Step 3: Update foundation and all role guides**

Use this English boundary, adapted per role:

```text
Same-tab sessionStorage may restore only course-scoped collapsed course-map branch identifiers and the explicit left/right structural rail display pair. Drawer, filter, focus, scroll, active-context, progress, mastery, recommendation, and personalization state remains non-persistent.
```

Use this Spanish equivalent:

```text
sessionStorage en la misma pestana puede restaurar solo identificadores de ramas plegadas con scope de curso y el par explicito de estado visual de los rieles estructurales izquierdo/derecho. El estado del drawer, filtro, foco, scroll, contexto activo, progreso, dominio, recomendacion y personalizacion sigue siendo no persistente.
```

Foundation must name both keys, `course_id` isolation, opener-copy semantics, and the prohibition on every other shell/learner storage category. Narrow `volatile right-rail Context` to active content context only.

- [ ] **Step 4: Run documentation tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_reader_shell_guidance_matches_left_rail_contract \
  tests/contracts/test_documentation_surfaces.py
```

Expected: PASS.

- [ ] **Step 5: Commit only the accepted contract**

```bash
git add docs/foundation/20_learning_renderer_contract.md \
  docs/guides/en/contributors/index.md docs/guides/en/professors/index.md \
  docs/guides/en/students/index.md docs/guides/en/agents/index.md \
  docs/guides/es/colaboradores/index.md docs/guides/es/profesores/index.md \
  docs/guides/es/estudiantes/index.md docs/guides/es/agentes/index.md \
  tests/contracts/test_static_builder.py
git diff --cached --check
git diff --cached --name-only
git commit -m "Accept reader rail session state"
```

Expected: only those ten paths; the Tiny Tray plan is absent.

---

### Task 2: Render Course Identity And Prepaint State

**Files:**
- Create: `packages/static/src/raya_static/shell_prepaint.py`
- Modify: `packages/static/src/raya_static/builder.py:146,373-397,848-870,997-1013,1912-1933,2094-2101,8250-8257`
- Modify: `packages/static/src/raya_static/rendering.py:6962-7067`
- Modify: `tests/contracts/test_static_builder.py:4946-5050`
- Modify: `tests/e2e/test_preview_static_read_path.py`

**Interfaces:**
- Produces: `SHELL_PREPAINT_SCRIPT_NAME = "shell-prepaint.js"` and `shell_prepaint_javascript() -> str`.
- Produces root attributes `data-raya-course-id`, `data-raya-shell-prepaint`, `data-raya-course-map-preference`, and `data-raya-learning-rail-preference`.
- Produces `data-raya-course-map-storage-key="raya:course-map-branches:v1:<course_id>"`.
- Task 3 consumes the prepaint DOM snapshot without an initialization read.

- [ ] **Step 1: Add failing generated-resource contract assertions**

Extend `test_reader_shell_uses_static_learning_shell`:

```python
assert '<html lang="en" data-raya-course-id="render-fixture"' in html
assert 'data-raya-shell-prepaint="pending"' in html
assert 'data-raya-learning-rail="expanded"' in html
assert 'data-raya-course-map-storage-key="raya:course-map-branches:v1:render-fixture"' in html
prepaint_tag = '<script src="../_raya/render/shell-prepaint.js"></script>'
stylesheet_tag = '<link rel="stylesheet" href="../_raya/render/rich.css">'
assert prepaint_tag in html
assert html.index(prepaint_tag) < html.index(stylesheet_tag)
assert "defer" not in prepaint_tag and "async" not in prepaint_tag

prepaint = (course / "artifact/site/_raya/render/shell-prepaint.js").read_text(encoding="utf-8")
assert "raya:reader-shell:v1:" in prepaint
assert "sessionStorage.getItem" in prepaint
assert "sessionStorage.setItem" not in prepaint
assert "localStorage" not in prepaint
assert "fetch(" not in prepaint
```

- [ ] **Step 2: Add a failing blocked-shell first-paint test**

Add `test_reader_shell_prepaint_restores_width_safe_state_before_deferred_shell`. Preload the record with `page.add_init_script`, abort `**/shell.js`, and assert:

```python
page.add_init_script("""() => sessionStorage.setItem(
  'raya:reader-shell:v1:render-fixture',
  JSON.stringify({courseMap: 'expanded', learningRail: 'collapsed'})
)""")
page.route("**/shell.js", lambda route: route.abort())
page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
state = page.evaluate("""() => ({
  prepaint: document.documentElement.dataset.rayaShellPrepaint,
  ready: document.documentElement.dataset.rayaShellReady || null,
  map: document.documentElement.dataset.rayaCourseMap,
  rail: document.documentElement.dataset.rayaLearningRail,
  mapPreference: document.documentElement.dataset.rayaCourseMapPreference,
  railPreference: document.documentElement.dataset.rayaLearningRailPreference,
  mapVisible: document.querySelector('#raya-course-map-list').checkVisibility(),
  railVisible: document.querySelector('#raya-learning-rail-body').checkVisibility(),
})""")
assert state == {
    "prepaint": "valid", "ready": None,
    "map": "expanded", "rail": "collapsed",
    "mapPreference": "expanded", "railPreference": "collapsed",
    "mapVisible": True, "railVisible": False,
}
```

Repeat at `800px` with both stored values expanded; both effective states must be collapsed while preference attributes remain expanded.

- [ ] **Step 3: Run both tests and verify red**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_reader_shell_uses_static_learning_shell \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_prepaint_restores_width_safe_state_before_deferred_shell
```

Expected: FAIL because course ID/prepaint resource and preference attributes do not exist.

- [ ] **Step 4: Create the focused prepaint resource**

Create `shell_prepaint.py`:

```python
from __future__ import annotations

SHELL_PREPAINT_SCRIPT_NAME = "shell-prepaint.js"

def shell_prepaint_javascript() -> str:
    return _SHELL_PREPAINT_JAVASCRIPT

_SHELL_PREPAINT_JAVASCRIPT = r"""
(() => {
  const root = document.documentElement;
  const courseId = root.dataset.rayaCourseId || "";
  const applyEffective = (courseMap, learningRail) => {
    let map = courseMap;
    let rail = learningRail;
    if (innerWidth < 640) {
      map = "expanded";
      rail = "expanded";
    } else if (innerWidth < 894 && map === "expanded" && rail === "expanded") {
      map = "collapsed";
      rail = "collapsed";
    }
    root.dataset.rayaCourseMap = map;
    root.dataset.rayaLearningRail = rail;
  };
  const applyDefaults = () => {
    const expanded = innerWidth < 640 || innerWidth >= 894;
    applyEffective(expanded ? "expanded" : "collapsed", expanded ? "expanded" : "collapsed");
  };
  if (!/^[a-z0-9][a-z0-9._-]*$/.test(courseId)) {
    applyDefaults();
    root.dataset.rayaShellPrepaint = "invalid";
    return;
  }
  let raw;
  try {
    raw = sessionStorage.getItem(`raya:reader-shell:v1:${courseId}`);
  } catch (_error) {
    applyDefaults();
    root.dataset.rayaShellPrepaint = "unavailable";
    return;
  }
  if (raw === null) {
    applyDefaults();
    root.dataset.rayaShellPrepaint = "missing";
    return;
  }
  try {
    const value = JSON.parse(raw);
    const keys = Object.keys(value || {}).sort();
    const valid = (state) => state === "expanded" || state === "collapsed";
    if (keys.length !== 2 || keys[0] !== "courseMap" || keys[1] !== "learningRail"
        || !valid(value.courseMap) || !valid(value.learningRail)) {
      applyDefaults();
      root.dataset.rayaShellPrepaint = "invalid";
      return;
    }
    root.dataset.rayaCourseMapPreference = value.courseMap;
    root.dataset.rayaLearningRailPreference = value.learningRail;
    applyEffective(value.courseMap, value.learningRail);
    root.dataset.rayaShellPrepaint = "valid";
  } catch (_error) {
    applyDefaults();
    root.dataset.rayaShellPrepaint = "invalid";
  }
})();
"""
```

- [ ] **Step 5: Thread `course_id`, write the resource, and order it before CSS**

Add `course_id: str` to `_render_page` and `_render_course_map`, pass `str(config["course_id"])`, render escaped `data-raya-course-id` plus `data-raya-shell-prepaint="pending"`, and set:

```python
storage_key = f"raya:course-map-branches:v1:{course_id}"
```

Write `shell-prepaint.js` beside `shell.js` and render its synchronous script before `rich.css`.

- [ ] **Step 6: Let completed prepaint state drive CSS**

Replace medium pre-ready selectors that begin:

```css
html:not([data-raya-shell-ready="true"])
```

with conservative pending-only selectors:

```css
html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"])
```

Normal state selectors must control `valid`, `missing`, `invalid`, and `unavailable` outcomes.

- [ ] **Step 7: Run the focused contract and first-paint tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_reader_shell_uses_static_learning_shell \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_prepaint_restores_width_safe_state_before_deferred_shell
```

Expected: PASS while `shell.js` is blocked at desktop and medium widths.

- [ ] **Step 8: Commit the prepaint boundary**

```bash
git add packages/static/src/raya_static/shell_prepaint.py \
  packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py \
  tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git diff --cached --check
git commit -m "Prepaint reader rail state"
```

---

### Task 3: Persist One Atomic Rail Pair

**Files:**
- Modify: `packages/static/src/raya_static/shell.py:145-209,433-478,1008-1049,1345-1414,1423-1437,1535-1630,1778-1787`
- Modify: `tests/e2e/test_preview_static_read_path.py:14741`

**Interfaces:**
- Consumes: Task 2 root preference/effective attributes.
- Produces: `readerShellStorageKey()`, `savedReaderShellPreference()`, and `saveReaderShellPreference()` inside generated JS.
- Produces exactly one `sessionStorage.setItem` per explicit structural action.

- [ ] **Step 1: Replace loose persistence assertions with exact reload/navigation coverage**

Rename the current test to `test_reader_rail_pair_survives_reload_and_same_tab_navigation` and assert:

```python
assert page.evaluate("Object.fromEntries(Object.entries(localStorage))") == {}
assert page.evaluate("Object.fromEntries(Object.entries(sessionStorage))") == {
    "raya:reader-shell:v1:render-fixture":
        '{"courseMap":"collapsed","learningRail":"collapsed"}',
}
page.reload(wait_until="networkidle")
assert page.locator("html").get_attribute("data-raya-course-map") == "collapsed"
assert page.locator("html").get_attribute("data-raya-learning-rail") == "collapsed"
page.goto(f"{handle.base_url}/static-path/index.html", wait_until="networkidle")
assert page.locator("html").get_attribute("data-raya-course-map") == "collapsed"
assert page.locator("html").get_attribute("data-raya-learning-rail") == "collapsed"
```

Assert structural Escape writes the resulting pair once; phone drawer Escape leaves it unchanged.

- [ ] **Step 2: Add same-origin cross-course isolation coverage**

Add `test_reader_rail_state_isolated_by_course_id`. Build two copied minimal courses under one served parent with the same root page ID and different `course_id` values. Collapse course A, open course B in the same page/session, and assert B keeps defaults while only A's exact key exists.

- [ ] **Step 3: Run both tests and verify red**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_reader_rail_pair_survives_reload_and_same_tab_navigation \
  tests/e2e/test_preview_static_read_path.py::test_reader_rail_state_isolated_by_course_id
```

Expected: FAIL because current shell writes two origin-global scalar keys.

- [ ] **Step 4: Replace scalar helpers with DOM-adopted pair helpers**

Delete `loadReaderShellState`, `preferredCourseMapExpanded`, and `preferredLearningRailExpanded`. Add:

```javascript
function validCourseId() {
  const value = root.dataset.rayaCourseId || "";
  return /^[a-z0-9][a-z0-9._-]*$/.test(value) ? value : "";
}
function readerShellStorageKey() {
  const courseId = validCourseId();
  return courseId ? `raya:reader-shell:v1:${courseId}` : "";
}
function savedReaderShellPreference() {
  const courseMap = root.dataset.rayaCourseMapPreference;
  const learningRail = root.dataset.rayaLearningRailPreference;
  const valid = (value) => value === "expanded" || value === "collapsed";
  return valid(courseMap) && valid(learningRail) ? { courseMap, learningRail } : null;
}
function saveReaderShellPreference() {
  const key = readerShellStorageKey();
  if (!key || !isStructuralRailShell()) return;
  const value = {
    courseMap: root.dataset.rayaCourseMap === "expanded" ? "expanded" : "collapsed",
    learningRail: root.dataset.rayaLearningRail === "expanded" ? "expanded" : "collapsed",
  };
  root.dataset.rayaCourseMapPreference = value.courseMap;
  root.dataset.rayaLearningRailPreference = value.learningRail;
  try { sessionStorage.setItem(key, JSON.stringify(value)); } catch (_error) { return; }
}
```

Initialization adopts root effective attributes with both setters using `{skipPersist: true}` and does not call `getItem`.

- [ ] **Step 5: Write once after every explicit structural action**

For Map, Context, collapse buttons, and structural Escape, apply the final pair with non-writing setters, then call `saveReaderShellPreference()` once. At medium width, collapse the counterpart first. Phone actions return before the save call.

- [ ] **Step 6: Run pair/isolation and existing collapse tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_reader_rail_pair_survives_reload_and_same_tab_navigation \
  tests/e2e/test_preview_static_read_path.py::test_reader_rail_state_isolated_by_course_id \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_focus_command_is_removed_and_rails_collapse_independently \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_rail_collapses_to_compact_context_tab
```

Expected: PASS with one exact versioned record.

- [ ] **Step 7: Commit atomic persistence**

```bash
git add packages/static/src/raya_static/shell.py tests/e2e/test_preview_static_read_path.py
git diff --cached --check
git commit -m "Persist reader rail pair"
```

---

### Task 4: Reconcile Responsive State And Focus Without Writes

**Files:**
- Modify: `packages/static/src/raya_static/shell.py:145-175,1345-1414`
- Modify: `tests/e2e/test_preview_static_read_path.py:16309,18329`

**Interfaces:**
- Consumes: Task 3 preference helpers and non-writing setters.
- Produces: `effectiveReaderShellState()` and one idempotent `reconcileReaderShellState({restoreFocus})`.

- [ ] **Step 1: Add a failing medium coordination/write-snapshot test**

Add `test_reader_shell_medium_actions_store_coordinated_pair`. Instrument `Storage.prototype.setItem`, seed both-expanded at `1000px`, resize to `800px`, and assert both effective states collapse without writes. Open Map then Context and assert exact coordinated pair writes. Cross `893/894` and `1279/1280`; viewport reconciliation must not write.

- [ ] **Step 2: Add failing focus assertions**

Add `test_reader_shell_breakpoint_reconciliation_preserves_visible_focus` covering focus inside either rail at `894 -> 893`, focused compact opener at `640 -> 639`, and drawer close control at `639 -> 640`:

```python
page.set_viewport_size({"width": 893, "height": 760})
page.wait_for_function("() => document.activeElement?.checkVisibility()")
assert page.evaluate("() => !document.querySelector('[inert]')?.contains(document.activeElement)") is True
```

- [ ] **Step 3: Run both tests and verify red**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_medium_actions_store_coordinated_pair \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_breakpoint_reconciliation_preserves_visible_focus
```

Expected: FAIL because current listeners restore independently and do not protect focus for every inert transition.

- [ ] **Step 4: Implement width-safe state calculation**

```javascript
function effectiveReaderShellState(preference = savedReaderShellPreference()) {
  if (!isStructuralRailShell()) return { courseMap: "expanded", learningRail: "expanded" };
  const next = preference || {
    courseMap: defaultCourseMapExpanded() ? "expanded" : "collapsed",
    learningRail: defaultLearningRailExpanded() ? "expanded" : "collapsed",
  };
  if (!approvedRailGeometryQuery.matches
      && next.courseMap === "expanded" && next.learningRail === "expanded") {
    return { courseMap: "collapsed", learningRail: "collapsed" };
  }
  return next;
}
```

- [ ] **Step 5: Route all media queries through one reconciliation function**

`reconcileReaderShellState` must capture active focus, compute the effective pair, move focus before hiding/inerting its owner, close drawers, apply both setters with `{skipPersist: true}`, synchronize modal/ARIA/tabindex/backdrop/scroll-lock state, and never call `saveReaderShellPreference`. Register it for structural, compact, approved-geometry, and desktop queries, including `addListener` fallbacks.

- [ ] **Step 6: Run responsive tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_medium_actions_store_coordinated_pair \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_breakpoint_reconciliation_preserves_visible_focus
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_medium_reader_rails_are_overlay_controls \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_drawer_boundary_switches_to_inline_rails \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_top_context_command_toggles_right_rail_only
```

Expected: PASS with no viewport-induced writes.

- [ ] **Step 7: Commit reconciliation**

```bash
git add packages/static/src/raya_static/shell.py tests/e2e/test_preview_static_read_path.py
git diff --cached --check
git commit -m "Reconcile reader rail breakpoints"
```

---

### Task 5: Re-Key And Validate Branch State

**Files:**
- Modify: `packages/static/src/raya_static/shell.py:506-555,1450-1495`
- Modify: `tests/e2e/test_preview_static_read_path.py:13220`

**Interfaces:**
- Consumes: exact Task 2 branch key attribute.
- Produces: `loadCollapsedMapNodeIds() -> Set<string> | null`; `null` means missing/invalid/unavailable, empty `Set` means valid all-expanded.

- [ ] **Step 1: Add failing branch payload cases**

Add `test_course_map_branch_state_uses_course_id_and_validates_payload` with:

```python
cases = (
    (None, "generated-defaults"),
    ("[]", "all-expanded"),
    ('["unit-node","unit-node","missing-node"]', "known-deduplicated"),
    ('{"bad":true}', "generated-defaults"),
    ('["unit-node",7]', "generated-defaults"),
    ('[""]', "generated-defaults"),
)
```

Assert valid `[]` keeps every branch expanded; duplicates/unknowns collapse only known IDs without a read-time rewrite; an explicit toggle writes one DOM-order array. Also prove two courses with identical roots use different branch keys.

- [ ] **Step 2: Run branch tests and verify red**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_branch_state_survives_refresh_and_page_navigation \
  tests/e2e/test_preview_static_read_path.py::test_course_map_branch_state_uses_course_id_and_validates_payload
```

Expected: FAIL because empty-array handling and payload validation do not match the spec.

- [ ] **Step 3: Implement nullable exact parsing**

```javascript
function loadCollapsedMapNodeIds() {
  const key = courseMapBranchStorageKey();
  if (!key) return null;
  let raw;
  try { raw = sessionStorage.getItem(key); } catch (_error) { return null; }
  if (raw === null) return null;
  try {
    const value = JSON.parse(raw);
    if (!Array.isArray(value)
        || value.some((item) => typeof item !== "string" || !item)) return null;
    const currentIds = new Set(mapNodeToggles.map((toggle) => toggle.dataset.rayaMapNodeToggle));
    return new Set(value.filter((item) => currentIds.has(item)));
  } catch (_error) { return null; }
}
```

Initialization must distinguish `null` from empty `Set`. Explicit writes iterate toggles in DOM order and include current collapsed IDs only.

- [ ] **Step 4: Remove URL fallback and legacy migration**

```javascript
function courseMapBranchStorageKey() {
  const courseId = validCourseId();
  const expected = courseId ? `raya:course-map-branches:v1:${courseId}` : "";
  return map.getAttribute("data-raya-course-map-storage-key") === expected ? expected : "";
}
```

Never enumerate, delete, or copy legacy keys.

- [ ] **Step 5: Run branch and contract subsets**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_branch_state_survives_refresh_and_page_navigation \
  tests/e2e/test_preview_static_read_path.py::test_course_map_branch_state_uses_course_id_and_validates_payload
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "reader_shell or course_map"
```

Expected: PASS.

- [ ] **Step 6: Commit branch isolation**

```bash
git add packages/static/src/raya_static/shell.py \
  tests/e2e/test_preview_static_read_path.py tests/contracts/test_static_builder.py
git diff --cached --check
git commit -m "Scope course map branch state"
```

---

### Task 6: Harden Failure, BFCache, And Tab Semantics

**Files:**
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `packages/static/src/raya_static/shell_prepaint.py`
- Modify: `tests/e2e/test_preview_static_read_path.py:14645-14836`

**Interfaces:**
- Consumes: Task 3 pair helpers and Task 4 reconciliation.
- Produces: `readReaderShellPreference()` for persisted `pageshow` only.
- Produces exception-safe accessor/read/write/quota/one-shot behavior.

- [ ] **Step 1: Parameterize the storage failure test against sessionStorage**

Replace its localStorage-only init script with accessor, read, write, and one-shot-read cases. For each, assert no page errors, shell ready, width-safe fallback, usable controls, correct ARIA/inertness, and visible focus. For write failure, assert UI changes while the old record remains unchanged.

```python
failure_scripts = {
    "accessor": "Object.defineProperty(window,'sessionStorage',{configurable:true,get(){throw new Error('accessor')}});",
    "read": "const g=Storage.prototype.getItem;Storage.prototype.getItem=function(k){if(k.startsWith('raya:'))throw new Error('read');return g.call(this,k)};",
    "write": "const s=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k.startsWith('raya:'))throw new Error('write');return s.call(this,k,v)};",
    "one-shot-read": "const g=Storage.prototype.getItem;let f=false;Storage.prototype.getItem=function(k){if(!f&&k.startsWith('raya:reader-shell:')){f=true;throw new Error('once')}return g.call(this,k)};",
}
```

- [ ] **Step 2: Add a failing BFCache test**

Add `test_reader_shell_bfcache_pageshow_reconciles_saved_state`: collapse on A, navigate to B, change state, `go_back`, assert cached A adopts current state without writes, then `go_forward` and repeat.

- [ ] **Step 3: Add a failing same-context tab test**

Add `test_reader_shell_tab_sessions_follow_browser_semantics`. Use separate top-level pages in one Playwright `BrowserContext` for independent state, create the opener case with `window.open`, assert its initial snapshot, then prove later writes diverge. Do not use separate contexts for the primary proof.

- [ ] **Step 4: Run hardening tests and verify red**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_works_without_storage \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_bfcache_pageshow_reconciles_saved_state \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_tab_sessions_follow_browser_semantics
```

Expected: FAIL because session failures and persisted `pageshow` are not handled fully.

- [ ] **Step 5: Add pageshow-only exact reading**

```javascript
function readReaderShellPreference() {
  const key = readerShellStorageKey();
  if (!key) return null;
  try {
    const raw = sessionStorage.getItem(key);
    if (raw === null) return null;
    const value = JSON.parse(raw);
    const keys = Object.keys(value || {}).sort();
    const valid = (state) => state === "expanded" || state === "collapsed";
    return keys.length === 2 && keys[0] === "courseMap" && keys[1] === "learningRail"
      && valid(value.courseMap) && valid(value.learningRail) ? value : null;
  } catch (_error) { return null; }
}
window.addEventListener("pageshow", (event) => {
  if (!event.persisted) return;
  const preference = readReaderShellPreference();
  if (preference) {
    root.dataset.rayaCourseMapPreference = preference.courseMap;
    root.dataset.rayaLearningRailPreference = preference.learningRail;
  } else {
    delete root.dataset.rayaCourseMapPreference;
    delete root.dataset.rayaLearningRailPreference;
  }
  reconcileReaderShellState({ restoreFocus: true });
});
```

Do not call this reader during normal deferred initialization. Keep catches narrow.

- [ ] **Step 6: Run hardening and focused reader subsets**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_works_without_storage \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_bfcache_pageshow_reconciles_saved_state \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_tab_sessions_follow_browser_semantics
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "reader_shell or course_map or rich_css"
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "reader_shell or reader_rail or course_map_branch_state or course_map_works_without_storage"
```

Expected: PASS.

- [ ] **Step 7: Commit hardening**

```bash
git add packages/static/src/raya_static/shell.py \
  packages/static/src/raya_static/shell_prepaint.py tests/e2e/test_preview_static_read_path.py
git diff --cached --check
git commit -m "Harden reader rail session state"
```

---

### Task 7: Final Verification And Commit Hygiene

**Files:**
- No production changes expected.
- Do not commit generated artifacts or the dirty Tiny Tray plan.

**Interfaces:**
- Consumes: approved Tasks 1-6.
- Produces: fresh focused, render-debug, host, smoke, Docker, review, and final-diff evidence.

- [ ] **Step 1: Run focused verification**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "reader_shell or course_map or rich_css"
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "reader_shell or reader_rail or course_map_branch_state or course_map_works_without_storage"
```

Expected: PASS.

- [ ] **Step 2: Run explicit render-debug evidence**

```bash
./scripts/check-render-debug.sh
```

Expected: PASS; generated reports remain ignored.

- [ ] **Step 3: Run the canonical host gate**

```bash
./scripts/check.sh
```

Expected: PASS, including full pytest, builds, inspections, docs, and internal render-debug.

- [ ] **Step 4: Run external-course smoke verification**

```bash
./scripts/smoke-test.sh
```

Expected: PASS for local and Docker validate/build/inspect/init paths.

- [ ] **Step 5: Run the reference Docker gate last**

```bash
./scripts/check-docker.sh
```

Expected: PASS.

- [ ] **Step 6: Audit final diff and staging**

```bash
git diff --check
git status --short
git diff --stat 29c6eeb..HEAD
git diff --name-only 29c6eeb..HEAD
git diff --cached --name-only
```

Expected paths from the design baseline are limited to:

```text
docs/foundation/20_learning_renderer_contract.md
docs/guides/en/contributors/index.md
docs/guides/en/professors/index.md
docs/guides/en/students/index.md
docs/guides/en/agents/index.md
docs/guides/es/colaboradores/index.md
docs/guides/es/profesores/index.md
docs/guides/es/estudiantes/index.md
docs/guides/es/agentes/index.md
docs/superpowers/plans/2026-07-10-reader-rail-session-persistence.md
packages/static/src/raya_static/builder.py
packages/static/src/raya_static/rendering.py
packages/static/src/raya_static/shell.py
packages/static/src/raya_static/shell_prepaint.py
tests/contracts/test_static_builder.py
tests/e2e/test_preview_static_read_path.py
```

The Tiny Tray plan must remain unstaged and outside every implementation commit.

- [ ] **Step 7: Request final code review**

Use `superpowers:requesting-code-review` over `29c6eeb..HEAD`. Fix each Critical or Important finding with a failing regression first, rerun the affected focused test, and repeat review until approved.

- [ ] **Step 8: Record completion**

Do not create an empty completion commit. Report exact commands, counts, commit SHAs, unrelated dirty paths, and residual risk.

---

## Self-Review Checklist

- Spec coverage: authority, course identity, atomic pair, branch payload, medium conflict, phone behavior, prepaint, BFCache, focus, failures, tabs, role parity, and gates map to tasks.
- Completeness scan: no deferred implementation or unnamed edge-case handling remains.
- Interface consistency: root attributes, versioned keys, preference helpers, and reconciliation names match across tasks.
- Commit hygiene: explicit pathspecs exclude the pre-existing Tiny Tray plan.
