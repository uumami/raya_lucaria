# Navigation-First Course Rail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the crowded, multi-scroll course sidebar with one compact navigation-first rail that has deterministic 256px/48px geometry, one native scroller, the same semantic DOM in structural and drawer modes, and complete accessible behavior at every breakpoint.

**Architecture:** `builder.py` emits one course-map landmark with fixed header, central navigation, fixed footer, and a separate structural mini rail; the same landmark becomes the phone drawer through CSS and shell state rather than duplicated markup. `shell_geometry.py`, `shell_prepaint.py`, and `shell.py` share breakpoint/default rules, while `rendering.py` owns layout and native scrolling and `accessibility.py` limits Text size to the article. Foundation and role truth surfaces change before package behavior is claimed current.

**Tech Stack:** Python 3.10, generated static HTML/CSS/JavaScript, pytest, Playwright with Chromium, uv workspace, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-08-04-navigation-first-course-rail-design.md`, approved after adversarial review.

## Global Constraints

- Work on `feature/reader-rail-density`; do not rewrite or discard user changes.
- `docs/foundation/` remains the highest truth. Amend `20_learning_renderer_contract.md` before claiming renderer behavior current.
- Expanded width is 256px; structural mini width is 48px; structural begins at 640px; approved wide geometry begins at 894px.
- Header and footer are 48px. The central navigation is the only left-rail element with vertical scrolling.
- No `wheel` or `touchmove` forwarding, no JS-assigned scroll deltas, and no nested vertical scroll containers.
- Search, Graph, Practice, Tasks, Schedule, and Context remain operable; Text size and OpenDyslexic live in the footer and mini rail.
- Text size scales only `.raya-main-article`. OpenDyslexic may affect content and navigation.
- Five discovery workspaces remain renderer-owned build outputs; the root-page home link is the only optional header destination.
- Session storage remains limited to `raya:reader-shell:v1:<course_id>` and `raya:course-map-branches:v1:<course_id>`. Reader local storage remains limited to `raya:text-size` and `raya:open-dyslexic`.
- Fine-pointer rows target 27-30px for the tree and 30-32px for command/header controls. If `any-pointer: coarse` is true, every operable rail target and tree row is at least 44px with no overlap.
- Structural and drawer modes reuse the same course-map/tree DOM. Do not add a mobile copy.
- Use local assets only. Do not add dependencies, external requests, analytics, learner inference, progress, mastery, or recommendations.
- Do not edit generated artifacts, caches, debug reports, screenshots, or dependency lock data unless a required dependency change is separately approved.
- Run focused red-green tests in each task. Run host, smoke, and Docker gates sequentially in the final task.
- Browser tests use `RAYA_TEST_BROWSER=/usr/bin/google-chrome` when Chromium auto-detection is unavailable.

## File Structure

| File | Responsibility | Tasks |
| --- | --- | --- |
| `docs/foundation/20_learning_renderer_contract.md` | Current renderer contract | 1 |
| `docs/guides/{en,es}/{contributors,professors,students,agents}/index.md` | Role-facing rail behavior | 1, 12 |
| `packages/static/src/raya_static/builder.py` | One semantic rail DOM, six actions, footer, mini rail | 2, 5, 7, 9 |
| `packages/static/src/raya_static/shell_geometry.py` | Shared breakpoints and pure effective-state derivation | 3, 8 |
| `packages/static/src/raya_static/shell_prepaint.py` | No-focus state before CSS/first paint | 3, 8 |
| `packages/static/src/raya_static/shell.py` | Runtime state, focus, drawer, filter, orientation | 3, 6, 8, 9, 10 |
| `packages/static/src/raya_static/rendering.py` | Geometry, layout, density, scroll, responsive, print | 4-10 |
| `packages/static/src/raya_static/accessibility.py` | Article-only Text size and OpenDyslexic resources | 5 |
| `tests/contracts/test_static_builder.py` | Generated markup/CSS contracts and workspace hrefs | 1, 2, 5, 7, 12 |
| `tests/contracts/test_documentation_surfaces.py` | Foundation/role parity | 1, 12 |
| `tests/contracts/test_renderer_dependencies.py` | Packaged local resource guardrails | 11 |
| `tests/e2e/test_rail_collapse_contract.py` | Shared geometry, prepaint, state, mini rail | 3, 7, 8 |
| `tests/e2e/test_rail_home_control.py` | Header/home/drawer order and focus | 2, 7, 9 |
| `tests/e2e/test_rail_density.py` | Single scroll owner, density, labels, touch/wheel | 4, 6, 10, 12 |
| `tests/e2e/test_preview_static_read_path.py` | Full browser/static/storage/print parity | 5, 8, 9, 11, 12 |
| `examples/courses/rail-density-fixture/` | Existing deep/long-label acceptance fixture | 4, 6, 10 |

## Density-Branch Migration Matrix

Complete this classification before the first package edit. The task owner must verify each row with `git blame`, `git log -S`, and the named focused tests; the disposition is already decided by the approved design.

| Existing surface | Evidence | Disposition | Replacement |
| --- | --- | --- | --- |
| Deep/long-label fixture | `examples/courses/rail-density-fixture/` | Retain | Reuse for scroll, label, OpenDyslexic, and short-height tests |
| Current-row orientation coverage | `tests/e2e/test_rail_density.py` | Adapt | Point at the central navigation owner and prove one-shot release |
| 13px label and narrow indentation | `rendering.py`, commits `34d0834`, `a122121` | Adapt | Fine-pointer 12-13px rules; 44px coarse rows |
| Two-line clamp | commit `38952cc` | Adapt | Fine-pointer only; full in-flow labels for touch/hybrid |
| Current-only sequence badge | commit `c8ec639` | Retain | Re-measure and keep contained inside the new label grid |
| Four-column tiles and `Plan` caption | `builder.py`, `rendering.py`, density tests | Remove | Six two-column flat actions with `Schedule` |
| Inline course query form | `_render_command_search_form()` inside rail | Remove from reader rail | Search action opens Search workspace; Content filter stays local |
| Position only in Page brief | density test and builder | Remove assertion | Compact `N / M` returns to fixed footer with full accessible text |
| Outer/list competing scroll owners | `rendering.py` base and responsive rules | Remove | One `.raya-course-map-navigation` owner |
| `overscroll-behavior: contain` rail relief valves | base/drawer CSS comments | Remove | Native structural chaining; modal background lock only |
| Floating collapsed Map opener | collapse CSS/tests | Remove | Reserved 48px mini rail |
| Tile-specific OpenDyslexic overrides/comments | `accessibility.py:81+` | Remove/adapt | Generic comfort button styles and article-only Text size |
| Wheel test accepting list/frame/page movement | `test_rail_density.py::test_wheel_over_any_rail_region_moves_something` | Replace | Exact central-owner deltas plus boundary chaining |
| Eight-body-tile documentation assertions | foundation, guides, contract tests | Replace | Six course actions plus two comfort controls |

---

### Task 1: Amend Foundation And Role Contracts

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Test: `tests/contracts/test_documentation_surfaces.py`

**Interfaces:**
- Consumes: approved design `d981c9c`.
- Produces: current wording that Tasks 2-12 implement and contract phrases shared by EN/ES tests.

- [ ] **Step 1: Replace the documentation parity test with the new contract vocabulary**

In `test_reader_rail_visual_parity_truth_surfaces_agree`, assert the stable English and Spanish phrases without binding prose layout:

```python
for name in ("foundation", "student_en", "agent_en"):
    assert "Search, Graph, Practice, Tasks, Schedule, and Context" in text[name]
    assert "Text size and OpenDyslexic" in text[name]
for name in ("student_es", "agent_es"):
    assert "Search, Graph, Practice, Tasks, Schedule y Context" in text[name]
    assert "Text size y OpenDyslexic" in text[name]
for name in paths:
    assert "256px" in text[name]
    assert "48px" in text[name]
assert "exactly eight compact icon-labeled command tiles" not in text["foundation"]
assert "minimal floating Map edge opener" not in text["foundation"]
```

Add all eight role indexes to `paths`; contributors and professors must be checked for stale floating-opener and Text-size language even if they do not enumerate every action.

- [ ] **Step 2: Run the contract test and confirm red**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py::test_reader_rail_visual_parity_truth_surfaces_agree -v
```

Expected: FAIL because foundation and role guides still require eight body tiles and the floating opener.

- [ ] **Step 3: Amend the smallest foundation surface**

Rewrite only the course-map, right-rail interaction, reader-control, and verification paragraphs/rows in `20_learning_renderer_contract.md`. The amended text must explicitly contain:

```text
six two-column course actions for Search, Graph, Practice, Tasks, Schedule, and Context
two fixed-footer comfort controls for Text size and OpenDyslexic
one central native vertical scroll owner
256px expanded course rail and 48px structural mini rail
Text size applies only to the authored article
```

Preserve the existing storage keys, no-inference language, static workspace contracts, rootless-home omission, right-rail phone availability, and deployment-neutral link requirements. Do not modify `00_index.md`; its current inventory remains accurate.

- [ ] **Step 4: Update all eight role indexes**

Describe the same behaviors for each audience. English uses existing generated labels; Spanish explains them without changing the emitted labels. Remove claims about the inline query, eight body tiles, Page-brief-only position, and floating Map opener. Keep course Search distinct from the local Content filter.

- [ ] **Step 5: Run documentation contracts**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add docs/foundation/20_learning_renderer_contract.md docs/guides tests/contracts/test_documentation_surfaces.py
git commit -m "Amend navigation-first rail contract"
```

### Task 2: Emit One Semantic Navigation Rail

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Test: `tests/contracts/test_static_builder.py`
- Test: `tests/e2e/test_rail_home_control.py`

**Interfaces:**
- Consumes: `_render_command_link`, `_render_command_button`, `_command_icon`, `_page_position`, `_render_rail_home_link`.
- Produces: `.raya-course-map-header`, `.raya-course-map-navigation`, `.raya-course-actions`, `.raya-course-content`, `.raya-course-map-footer`, and `.raya-course-map-mini`; later CSS/JS tasks rely on these exact classes.

- [ ] **Step 1: Add failing semantic markup assertions**

Update the reader-shell builder test to parse generated HTML and assert:

```python
assert html.count('id="raya-course-map"') == 1
assert html.count('id="raya-course-map-list"') == 1
assert '<div class="raya-course-map-navigation" data-raya-course-map-navigation>' in html
assert '<section class="raya-course-actions" aria-labelledby="raya-course-actions-title">' in html
assert '<section class="raya-course-content" aria-labelledby="raya-course-content-title">' in html
assert '<footer class="raya-course-map-footer">' in html
assert '<div class="raya-course-map-mini" data-raya-course-map-mini' in html
assert 'class="raya-course-rail-search raya-command-search-form"' not in html
assert html.count('class="raya-course-action ') == 6
```

Assert the action labels in DOM order are exactly `Search`, `Graph`, `Practice`, `Tasks`, `Schedule`, `Context` and footer position exposes visually hidden `Page N of M` beside aria-hidden `N / M`.

- [ ] **Step 2: Run focused tests and confirm red**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -k "course_map or reader_command" -v
```

Expected: FAIL on missing semantic regions, old inline form, eight old tile classes, and absent footer/mini markup.

- [ ] **Step 3: Split `_render_course_map` into focused render helpers**

Add these private interfaces in `builder.py` (the following is the exact
signature contract; Step 4 defines their emitted structure):

```text
_render_course_actions(*, search_href: str, graph_href: str,
    practice_href: str, tasks_href: str, schedule_href: str,
    graph_label: str, practice_label: str, tasks_label: str,
    schedule_label: str) -> str
_render_course_map_footer(position: str) -> str
_render_course_map_mini(home_href: str | None) -> str
```

`_render_course_actions` emits five anchors and one Context button. Keep existing `aria-label` detail counts and deployment-neutral hrefs. Use visible `Schedule`, not the obsolete four-column `Plan` caption. `_render_course_map_footer` emits the two existing comfort buttons once inside the expanded footer and compact position markup. `_render_course_map_mini` emits independent Home/Expand/Text-size/OpenDyslexic controls for structural collapsed mode; omit Home when `home_href is None`.

- [ ] **Step 4: Assemble the single expanded DOM**

Make `_render_course_map` emit this ownership structure:

```html
<nav id="raya-course-map" class="raya-course-map" aria-label="Course map">
  <header class="raya-course-map-header"></header>
  <div id="raya-course-map-body" class="raya-course-map-body">
    <div class="raya-course-map-navigation" data-raya-course-map-navigation>
      <section class="raya-course-actions"></section>
      <section class="raya-course-content"></section>
    </div>
    <footer class="raya-course-map-footer"></footer>
  </div>
  <div class="raya-course-map-mini" data-raya-course-map-mini></div>
</nav>
```

The generated course title remains complete text in the DOM and is visually truncated later by CSS. Add a real tooltip node and `aria-describedby` for title and unfamiliar icon controls; do not rely on `title` or `data-raya-command-tooltip` alone.

- [ ] **Step 5: Preserve rootless and nested-home behavior**

Update `test_rail_home_control.py` so the nested fixture resolves the header and mini Home href to the generated root and the rootless fixture finds zero `.raya-course-map-home` elements in both regions.

- [ ] **Step 6: Run builder/home tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -k "course_map or reader_command" -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_home_control.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/static/src/raya_static/builder.py tests/contracts/test_static_builder.py tests/e2e/test_rail_home_control.py
git commit -m "Build semantic course navigation rail"
```

### Task 3: Make Geometry And Prepaint Deterministic

**Files:**
- Modify: `packages/static/src/raya_static/shell_geometry.py`
- Modify: `packages/static/src/raya_static/shell_prepaint.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Test: `tests/e2e/test_rail_collapse_contract.py`

**Interfaces:**
- Consumes: `RAIL_STRUCTURAL_PX = 640`, `RAIL_APPROVED_PX = 894`.
- Produces: `RAIL_EXPANDED_PX = 256`, `RAIL_MINI_PX = 48`, `rayaEffectiveRailState(courseMap, learningRail, bands)` with left-first no-focus fallback, and runtime-only `reconcileFocusedIntermediateState()`.

- [ ] **Step 1: Write failing token and state-table tests**

Add:

```python
def test_navigation_rail_geometry_tokens_are_single_sourced():
    assert RAIL_EXPANDED_PX == 256
    assert RAIL_MINI_PX == 48
    for resource in (rich_render_css(), shell_resources().javascript, shell_prepaint_javascript()):
        assert "__RAYA_RAIL_EXPANDED_PX__" not in resource
        assert "__RAYA_RAIL_MINI_PX__" not in resource

def _evaluate_intermediate_derivation(course_map: str, learning_rail: str):
    script = f"""
{RAIL_EFFECTIVE_DERIVATION_JS}
const result = rayaEffectiveRailState(
  {json.dumps(course_map)},
  {json.dumps(learning_rail)},
  {{structural: true, approved: false}}
);
process.stdout.write(JSON.stringify(result));
"""
    completed = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)

def test_intermediate_effective_state_prefers_left_without_focus():
    result = _evaluate_intermediate_derivation("expanded", "expanded")
    assert result == {"courseMap": "expanded", "learningRail": "collapsed"}
```

Add `import json` and `import subprocess` beside the existing test imports.

Extend the browser prepaint test across 894, 893, 640, and 639 with missing, `collapsed/collapsed`, one-expanded, and `expanded/expanded` saved pairs.

- [ ] **Step 2: Run focused state tests and confirm red**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py -k "geometry_tokens or intermediate_effective or prepaint" -v
```

Expected: FAIL because widths are not tokenized and intermediate `expanded/expanded` currently becomes `collapsed/collapsed`.

- [ ] **Step 3: Add geometry tokens and pure no-focus derivation**

In `shell_geometry.py` add:

```python
RAIL_EXPANDED_PX = 256
RAIL_MINI_PX = 48
```

Add both placeholders to `_TOKENS`. Change the intermediate branch of `rayaEffectiveRailState` to return left expanded/right collapsed only when both requested states are expanded. Preserve zero-expanded and one-expanded pairs verbatim. Phone still reports both expanded because CSS/JS presents the left as a drawer and keeps right context available.

- [ ] **Step 4: Align default state in prepaint and runtime**

In `shell_prepaint.py`, missing/invalid intermediate state calls `applyEffective("expanded", "collapsed", bands)`. In `shell.py`, `effectiveReaderShellState()` uses the same no-focus default and consumes the shared derivation. Do not inspect focus during prepaint.

- [ ] **Step 5: Add the runtime focus arbitration seam**

Add a helper with this behavior:

```javascript
function intermediateWinnerForTransition() {
  if (map.contains(document.activeElement)) return "courseMap";
  if (learningRail && learningRail.contains(document.activeElement)) return "learningRail";
  return "courseMap";
}
```

Use it only when an explicit resize/zoom/BFCache reconciliation encounters `expanded/expanded`. If focused content becomes inert, focus the winning rail's corresponding visible toggle after state and inertness are synchronized.

- [ ] **Step 6: Run state tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/static/src/raya_static/shell_geometry.py packages/static/src/raya_static/shell_prepaint.py packages/static/src/raya_static/shell.py tests/e2e/test_rail_collapse_contract.py
git commit -m "Define navigation rail state geometry"
```

### Task 4: Establish The One-Scroller Layout

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/e2e/test_rail_density.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

**Interfaces:**
- Consumes: `.raya-course-map-navigation`, `RAIL_EXPANDED_PX`, `RAIL_MINI_PX`.
- Produces: one declared vertical scroll owner and 256px expanded geometry in wide/intermediate modes.

- [ ] **Step 1: Replace the permissive scroll test with an exact owner test**

Add a helper that returns each candidate's computed `overflowY`, `clientHeight`, and `scrollHeight`:

```javascript
() => [
  '.raya-course-map',
  '.raya-course-map-body',
  '.raya-course-map-navigation',
  '.raya-course-actions',
  '.raya-course-content',
  '.raya-course-map-list'
].map(selector => {
  const node = document.querySelector(selector);
  return {
    selector,
    overflowY: getComputedStyle(node).overflowY,
    clientHeight: node.clientHeight,
    scrollHeight: node.scrollHeight
  };
})
```

For widths 1440, 894, 893, and 640 assert that only `.raya-course-map-navigation` has `overflowY` equal to `auto` or `scroll`. On the deep fixture also assert its `scrollHeight > clientHeight`.

- [ ] **Step 2: Run the owner test and confirm red**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py -k "single_scroll_owner" -v
```

Expected: FAIL showing the current outer rail and list as competing owners and no central navigation owner.

- [ ] **Step 3: Replace base layout rules**

In the base rail CSS emitted by `rendering.py`, implement the explicit grid:

```css
.raya-course-map {
  inline-size: calc(__RAYA_RAIL_EXPANDED_PX__ * 1px);
  max-block-size: calc(100dvh - var(--raya-shell-block-offset, 0px));
  overflow: clip;
}
.raya-course-map-body {
  display: grid;
  grid-template-rows: minmax(0, 1fr) 48px;
  min-block-size: 0;
  overflow: clip;
}
.raya-course-map-navigation {
  min-block-size: 0;
  overflow-x: clip;
  overflow-y: auto;
}
.raya-course-map-list,
.raya-course-actions,
.raya-course-content {
  max-block-size: none;
  overflow: visible;
}
```

Keep header outside `.raya-course-map-body` or make the outer grid `48px minmax(0,1fr)`; in either form, header/footer must be siblings of the central scroller. Delete every conflicting `overflow-y`, `max-height`, and `overscroll-behavior` declaration on the outer rail and tree in base, 640-893, >=894, and drawer rules.

- [ ] **Step 4: Assert header/footer stability by geometry**

In Playwright, record header/footer rects, set the central owner to half its maximum scroll, and record rects again:

```python
assert after["header"] == before["header"]
assert after["footer"] == before["footer"]
assert after["navigationScrollTop"] > before["navigationScrollTop"]
```

Do not assert `position: sticky`; the behavioral rect contract is authoritative.

- [ ] **Step 5: Run focused layout tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py -k "single_scroll_owner or header_footer" -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "reader_shell_geometry" -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/static/src/raya_static/rendering.py tests/e2e/test_rail_density.py tests/e2e/test_preview_static_read_path.py
git commit -m "Give course navigation one scroll owner"
```

### Task 5: Compact Actions, Footer, Text Size, And Tooltips

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/accessibility.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

**Interfaces:**
- Consumes: semantic regions from Task 2.
- Produces: two-column flat action grid, fixed footer controls, article-only `--raya-reader-text-scale`, and reusable `.raya-tooltip` behavior.

- [ ] **Step 1: Write failing action/footer geometry tests**

At widths 1440, 894, 893, and open 390 drawer, collect action rows and assert:

```python
assert labels == ["Search", "Graph", "Practice", "Tasks", "Schedule", "Context"]
assert columns == [0, 1, 0, 1, 0, 1]
assert all(30 <= item["height"] <= 32 for item in actions)  # fine pointer
assert all(not item["borderedCard"] for item in actions)
assert footer["height"] == 48
assert footer["positionAccessibleName"] == f"Page {page_number} of {page_count}"
```

Generate a coarse-pointer context and assert every action and footer button is at least 44px with pairwise non-intersecting rects.

- [ ] **Step 2: Write the failing Text-size scope test**

Measure computed font sizes and rects before and after two clicks on `.raya-text-size-toggle`:

```python
assert after["articleFont"] > before["articleFont"]
for key in ("map", "rightRail", "action", "filter", "tree", "footer", "mini"):
    assert after[key] == before[key]
```

Expected red: the right learning rail currently consumes `--raya-reader-text-scale`.

- [ ] **Step 3: Style flat two-column actions and footer**

Use:

```css
.raya-course-actions-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.raya-course-action {
  min-inline-size: 0;
  min-block-size: 30px;
  border: 0;
  border-radius: 4px;
  font-size: 0.8125rem;
}
.raya-course-map-footer {
  block-size: 48px;
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  align-items: center;
  overflow: clip;
}
```

Use subtle background only for hover, focus-visible, current, or pressed state. Remove legacy card borders, four-column rules, search-form rules, and `Plan`-specific comments.

- [ ] **Step 4: Scope Text size to the article**

Keep `--raya-reader-text-scale` on root for persistence compatibility, but consume it only here:

```css
.raya-main-article {
  font-size: calc(1rem * var(--raya-reader-text-scale, 1));
}
```

Remove its use from `.raya-learning-rail`. Delete tile-specific `.raya-font-toggle:not(.raya-course-rail-command)` compensations that no longer match the new markup; keep generic standalone/discovery styles intact.

- [ ] **Step 5: Implement dismissible hover/focus tooltips**

Use one delegated Escape handler in `shell.py` to mark the active tooltip hidden without changing focus. CSS must keep a tooltip visible while its trigger has hover/focus or the tooltip itself is hovered. Each trigger retains its own `aria-label`; `aria-describedby` points to tooltip content and never supplies the only name.

- [ ] **Step 6: Run focused tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -k "course_map or accessibility" -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "course_action or text_size or tooltip" -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/static/src/raya_static/rendering.py packages/static/src/raya_static/accessibility.py packages/static/src/raya_static/shell.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Compact course rail controls"
```

### Task 6: Make The Tree Dense And Fully Readable

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `tests/e2e/test_rail_density.py`

**Interfaces:**
- Consumes: `.raya-course-map-navigation` and existing complete link text/data labels.
- Produces: fine-pointer clamp/reveal, full hybrid/touch labels, and one-shot orientation against the central owner.

- [ ] **Step 1: Replace density assertions with pointer-specific tests**

For a fine-pointer context assert non-current labels use 12-13px type, rows are 27-30px when one line, labels clamp to at most two lines, and focused/current rows reveal in normal flow. For a context with `has_touch=True` and CSS media emulation confirming `any-pointer: coarse`, assert all labels expose their full rendered height and each row is at least 44px.

Use the fixture's unbroken identifier to assert:

```python
assert row["right"] <= scrollport["right"] + 1
assert row["scrollWidth"] <= scrollport["clientWidth"] + 1
assert row["writingMode"] == "horizontal-tb"
```

- [ ] **Step 2: Run label tests and confirm red**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py -k "long_labels or coarse_pointer_labels" -v
```

Expected: FAIL because coarse/hybrid rules do not exist and current selectors target the old list scroller.

- [ ] **Step 3: Implement pointer-specific row rules**

Fine-pointer base:

```css
.raya-course-map-node-row {
  min-block-size: 27px;
  grid-template-columns: 24px 24px minmax(0, 1fr);
}
.raya-course-map-node-row a {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  overflow-wrap: anywhere;
}
.raya-course-map-node-row:is(:hover, :focus-within) a,
.raya-course-map-node-row a[aria-current="page"] {
  display: block;
  overflow: visible;
}
```

For `@media (any-pointer: coarse), (hover: none)`, set each row/link/disclosure to a non-overlapping 44px minimum and remove the clamp. Preserve a single subtle hierarchy guide per level and the current-only sequence badge if it remains contained.

- [ ] **Step 4: Repoint orientation to the central owner**

Replace `.raya-course-map-list` as orientation viewport with `[data-raya-course-map-navigation]`. Use `element.scrollIntoView({block: "nearest"})` only during initial/current-path reconciliation. After a manual scroll, resize/observer callbacks must not restore the old position.

- [ ] **Step 5: Verify reveal and orientation behavior**

Focus a long link near the bottom, assert its full rect remains between header/footer, manually change central `scrollTop`, trigger resize and any registered observer inputs, then assert the manual value is unchanged within one pixel.

- [ ] **Step 6: Run tree tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py -k "label or sequence or orientation" -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/static/src/raya_static/rendering.py packages/static/src/raya_static/shell.py tests/e2e/test_rail_density.py
git commit -m "Refine course tree density"
```

### Task 7: Replace The Floating Opener With A 48px Mini Rail

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `tests/e2e/test_rail_collapse_contract.py`
- Modify: `tests/e2e/test_rail_home_control.py`
- Modify: `tests/contracts/test_static_builder.py`

**Interfaces:**
- Consumes: `.raya-course-map-mini` markup and `RAIL_MINI_PX`.
- Produces: reserved structural mini geometry with Home, Expand, Text size, OpenDyslexic and fully inert expanded content.

- [ ] **Step 1: Rewrite collapsed-state tests**

Replace assertions for one floating chip with:

```python
assert 47 <= state["railWidth"] <= 49
assert state["miniVisible"] is True
assert state["miniLabels"] == ["Back to course", "Expand course map", "Text size: normal", "Toggle OpenDyslexic font"]
assert state["bodyHidden"] == "true"
assert state["bodyInert"] is True
assert state["bodyTabbables"] == 0
assert state["articleDoesNotIntersectMini"] is True
```

For a rootless fixture omit only `Back to course`. Include an accessibility-tree snapshot proving body descendants are absent while mini controls remain present.

- [ ] **Step 2: Run collapse tests and confirm red**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py tests/e2e/test_rail_home_control.py -k "collapsed or mini or rootless" -v
```

Expected: FAIL because the current state exposes one floating opener and reserves no 48px column.

- [ ] **Step 3: Implement mini geometry and visibility**

At `min-width: 640px`, collapsed state sets the left shell track to `48px`, hides/inerts `.raya-course-map-body` and expanded header content, and shows `.raya-course-map-mini` as a 48px vertical rail. Expanded state uses 256px and hides/inerts the mini controls. Below 640px, the mini rail leaves layout entirely.

- [ ] **Step 4: Synchronize comfort controls**

The existing delegated comfort code already updates every `.raya-text-size-toggle` and `.raya-font-toggle`; retain that fan-out. Assert footer and mini `aria-pressed`/`aria-label` values change together and localStorage contains only the two accepted comfort keys.

- [ ] **Step 5: Run collapse and builder tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py tests/e2e/test_rail_home_control.py -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -k "course_map" -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/static/src/raya_static/rendering.py packages/static/src/raya_static/shell.py tests/e2e/test_rail_collapse_contract.py tests/e2e/test_rail_home_control.py tests/contracts/test_static_builder.py
git commit -m "Add structural course mini rail"
```

### Task 8: Implement Intermediate Rail Handoff

**Files:**
- Modify: `packages/static/src/raya_static/shell_geometry.py`
- Modify: `packages/static/src/raya_static/shell_prepaint.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/e2e/test_rail_collapse_contract.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

**Interfaces:**
- Consumes: state derivation from Task 3 and mini rail from Task 7.
- Produces: deterministic 640-893 left/right exclusivity, focus transfer, and session persistence.

- [ ] **Step 1: Add the complete intermediate transition table**

Test 893px and 640px for these inputs:

```text
missing state                 -> left expanded, right collapsed
collapsed/collapsed           -> both mini/collapsed
expanded/collapsed            -> left expanded, right collapsed
collapsed/expanded            -> left mini, right expanded
expanded/expanded, no focus   -> left expanded, right collapsed
expanded/expanded, left focus -> left expanded, right collapsed
expanded/expanded, right focus-> left mini, right expanded
```

For each result assert shell tracks do not intersect the article and at most one full rail exists.

- [ ] **Step 2: Run the transition table and confirm red**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py -k "intermediate_handoff" -v
```

Expected: FAIL on the new defaults, 48px mini geometry, and focus-aware winner.

- [ ] **Step 3: Centralize atomic pair application**

In `shell.py` add one function that sets both root data attributes, both bodies' inert/hidden state, both toggle states, shell grid state, and storage only after the pair is valid:

```javascript
function applyStructuralRailPair(courseMapState, learningRailState, options = {}) {
  const next = reconcileRailPair(courseMapState, learningRailState, options);
  root.dataset.rayaCourseMap = next.courseMap;
  root.dataset.rayaLearningRail = next.learningRail;
  syncCourseMapState(next.courseMap);
  syncLearningRailState(next.learningRail);
  if (options.persist !== false) saveReaderShellPreference();
  restoreValidFocus(options.previousFocus);
}
```

Do not expose intermediate DOM states where both full rails are interactive in 640-893.

- [ ] **Step 4: Wire explicit handoffs**

In the intermediate band, activating Context applies left collapsed/right expanded. Expanding the left rail applies left expanded/right collapsed. Explicitly collapsing either rail may leave both collapsed. At >=894 each rail retains independent controls; below 640 the left becomes a drawer and the right stays expanded.

- [ ] **Step 5: Test resize, zoom/reflow, and BFCache**

Exercise `894 -> 893 -> 894` and `640 -> 639 -> 640` with focus in left, right, and article. Dispatch `pageshow` with `persisted: true`. Assert no focused descendant is inside an inert/hidden rail and prepaint/runtime settle without a second visible transition.

- [ ] **Step 6: Run state/browser tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "reader_shell_prepaint or boundary_switches or rail_state" -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/static/src/raya_static/shell_geometry.py packages/static/src/raya_static/shell_prepaint.py packages/static/src/raya_static/shell.py packages/static/src/raya_static/rendering.py tests/e2e/test_rail_collapse_contract.py tests/e2e/test_preview_static_read_path.py
git commit -m "Coordinate intermediate reader rails"
```

### Task 9: Make The Phone Drawer Reuse The Rail Correctly

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `tests/e2e/test_rail_home_control.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

**Interfaces:**
- Consumes: one rail DOM, central scroller, atomic state helpers.
- Produces: sub-640 modal drawer with dynamic viewport/safe-area handling and mobile Context focus handoff.

- [ ] **Step 1: Add drawer identity and geometry tests**

Capture `window.__courseMapIdentity = document.querySelector('#raya-course-map')`, resize `640 -> 639`, open/close, resize back, then assert:

```javascript
({
  sameMap: window.__courseMapIdentity === document.querySelector('#raya-course-map'),
  maps: document.querySelectorAll('#raya-course-map').length,
  trees: document.querySelectorAll('#raya-course-map-list').length,
  duplicateIds: Array.from(document.querySelectorAll('[id]'))
    .map(node => node.id)
    .filter((id, index, ids) => ids.indexOf(id) !== index)
})
```

Expected values: `sameMap=True`, `maps=1`, `trees=1`, `duplicateIds=[]`.

- [ ] **Step 2: Add narrow/safe-area/short-height red tests**

At 639x480, 390x844, and 240x320 assert drawer width equals `min(256, viewport width)`, header/footer remain fully inside the viewport, central navigation overflows when needed, document horizontal overflow is <=1px, and no controls overlap. Separately assert the generated CSS contains `env(safe-area-inset-left)` and `env(safe-area-inset-bottom)` on the open drawer; Chromium's headless viewport does not synthesize non-zero device cutout insets.

- [ ] **Step 3: Run drawer tests and confirm red**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "mobile_course_map_drawer" -v
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_home_control.py -k "drawer" -v
```

Expected: FAIL because current drawer has separate chrome behavior, nested scroll rules, hidden filter/Context, and no fixed footer.

- [ ] **Step 4: Implement modal layout without duplicated content**

Below 640px set the same `#raya-course-map` to fixed dialog geometry:

```css
html[data-raya-course-map-drawer="open"] .raya-course-map {
  inline-size: min(256px, 100vw);
  block-size: 100vh;
  block-size: 100dvh;
  padding-inline-start: env(safe-area-inset-left);
  padding-block-end: env(safe-area-inset-bottom);
  overflow: clip;
}
```

Keep the header and footer fixed in the rail grid and the central navigation as the sole drawer scroller. Remove drawer-only copies, old grip/title/position duplication, hidden filter rules, 18rem list caps, and nested containment.

- [ ] **Step 5: Complete modal semantics and Context handoff**

On open: set dialog name/`aria-modal`, inert the article/right rail/launcher, lock background, focus course Home when it exists and otherwise focus Close, and trap Tab. On close/Escape/backdrop: remove inertness/lock and restore launcher focus. On mobile Context: close the drawer first, restore the right rail, `scrollIntoView({block: "start"})`, then focus `#raya-learning-rail` with `tabindex="-1"`; do not collapse it.

- [ ] **Step 6: Verify six actions and focus lifecycle**

Assert Search/Graph/Practice/Tasks/Schedule hrefs remain operable in the drawer, Context reaches the right rail, Escape restores the launcher, and resizing while open cannot leave article/right rail inert.

- [ ] **Step 7: Run drawer tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "mobile_course_map_drawer or drawer_boundary" -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_home_control.py -k "drawer" -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py packages/static/src/raya_static/shell.py tests/e2e/test_rail_home_control.py tests/e2e/test_preview_static_read_path.py
git commit -m "Unify mobile course drawer"
```

### Task 10: Prove Native Wheel And Touch Scrolling

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `tests/e2e/test_rail_density.py`

**Interfaces:**
- Consumes: single central owner and modal background lock.
- Produces: exact wheel/touch liveness, structural boundary chaining, and source guardrails against forwarding.

- [ ] **Step 1: Add the source-level forwarding guardrail**

Read `shell_resources().javascript` and assert:

```python
for forbidden in (
    'addEventListener("wheel"',
    "addEventListener('wheel'",
    'addEventListener("touchmove"',
    "addEventListener('touchmove'",
    ".onwheel =",
    ".ontouchmove =",
):
    assert forbidden not in javascript
```

Also assert the stylesheet contains no `overscroll-behavior: contain` selector that applies to `.raya-course-map`, `.raya-course-map-navigation`, or `.raya-course-map-list` in structural mode.

- [ ] **Step 2: Add exact wheel tests for every zone and band**

With the deep fixture at 1440, 894, 893, 640, open 639 drawer, and open 390 drawer, reset central scroll to zero, wheel over the center of actions, filter, and tree, then assert only central `scrollTop` increases while it has remaining range. Do not accept outer rail or page movement as a substitute.

- [ ] **Step 3: Add structural boundary chaining tests**

At structural widths, set central scroll exactly to its bottom, make the document scrollable, wheel down over the central owner, and assert page `scrollY` increases. Repeat at the top with an upward wheel. In modal drawer mode, assert the document remains locked at the same boundaries.

- [ ] **Step 4: Add real touchscreen swipes**

Create Playwright contexts with `has_touch=True` and a mobile/tablet device scale. In one structural 640 case and one open 390 drawer, perform a real touchscreen swipe whose start point lies over each of actions, filter, and tree:

```python
session = context.new_cdp_session(page)
session.send("Input.dispatchTouchEvent", {
    "type": "touchStart",
    "touchPoints": [{"x": x, "y": y}],
})
for delta in (20, 40, 60, 80, 100):
    session.send("Input.dispatchTouchEvent", {
        "type": "touchMove",
        "touchPoints": [{"x": x, "y": y - delta}],
    })
session.send("Input.dispatchTouchEvent", {
    "type": "touchEnd",
    "touchPoints": [],
})
assert page.locator("[data-raya-course-map-navigation]").evaluate(
    "node => node.scrollTop"
) > before_scroll_top
```

The implementation task must use CDP touch events rather than calling `element.scrollTop` in the test; direct assignment would not prove native touch handling.

- [ ] **Step 5: Run red tests before CSS cleanup**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py -k "native_wheel or native_touch or forwarding" -v
```

Expected: FAIL until all obsolete outer/list overflow and containment rules are removed.

- [ ] **Step 6: Remove remaining scroll interception**

Delete all course-rail wheel/touch handlers if present and remove every competing scroll/containment declaration found by the tests. Preserve modal document scroll lock, which is stateful background behavior rather than event forwarding.

- [ ] **Step 7: Run scroll tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py -k "scroll or wheel or touch or orientation" -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add packages/static/src/raya_static/rendering.py packages/static/src/raya_static/shell.py tests/e2e/test_rail_density.py
git commit -m "Verify native course rail scrolling"
```

### Task 11: Preserve Storage, Accessibility, Print, And Static Parity

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `packages/static/src/raya_static/accessibility.py`
- Modify: `tests/contracts/test_renderer_dependencies.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

**Interfaces:**
- Consumes: final markup/state/layout behavior.
- Produces: storage isolation, accessibility-tree correctness, reduced motion, print exclusion, local resource parity, and resolved workspace links.

- [ ] **Step 1: Extend storage tests**

Preserve existing opener-copy/tab-divergence and course-isolation cases. After exercising rail collapse, branch collapse, drawer, filter, scroll, focus, Context, Text size, and OpenDyslexic, assert:

```python
assert sorted(session_keys) == [
    f"raya:course-map-branches:v1:{course_id}",
    f"raya:reader-shell:v1:{course_id}",
]
assert sorted(local_keys) == ["raya:open-dyslexic", "raya:text-size"]
assert "filter" not in serialized_storage
assert "scroll" not in serialized_storage
assert "focus" not in serialized_storage
assert "drawer" not in serialized_storage
```

- [ ] **Step 2: Add hidden-state accessibility snapshots**

For expanded, mini, drawer closed, and drawer open states, use Playwright locator ARIA snapshots. Assert hidden expanded content is absent in mini mode; the mini rail is absent while expanded; closed drawer content is absent below 640; and inert article/right rail content is absent only while the modal is open.

- [ ] **Step 3: Add reduced-motion and print tests**

With reduced motion, assert state, focus, inertness, and geometry settle without transition timing. In print media, assert course map, mini rail, launcher, backdrop, and right learning rail are hidden while `.raya-main-article` remains visible and readable.

- [ ] **Step 4: Resolve all generated workspace destinations**

Build the fixture, parse the five action hrefs from a nested reader page, strip query/fragment, resolve them relative to that page, and assert each target exists under `artifact/site`. Assert no href is absolute, external, source-private, or under `data/`.

- [ ] **Step 5: Run the expanded static-read-path tests and confirm any red cases**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "storage or accessibility or reduced_motion or print or workspace" -v
```

Expected before final fixes: any remaining stale storage, inertness, print, or path assertion fails with the specific state mismatch.

- [ ] **Step 6: Make the minimal resource/state fixes**

Keep comfort resource filenames and packaged OpenDyslexic font unchanged. Update only selectors and state reconciliation required by failing tests. Do not introduce storage migration keys, network fallback, or duplicated scripts.

- [ ] **Step 7: Run focused parity tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_renderer_dependencies.py -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "storage or accessibility or reduced_motion or print or workspace" -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add packages/static/src/raya_static/rendering.py packages/static/src/raya_static/shell.py packages/static/src/raya_static/accessibility.py tests/contracts/test_renderer_dependencies.py tests/e2e/test_preview_static_read_path.py
git commit -m "Preserve reader rail accessibility contracts"
```

### Task 12: Remove Obsolete Density Contracts And Run The Visual Matrix

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/accessibility.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/contracts/test_documentation_surfaces.py`
- Modify: `tests/e2e/test_rail_density.py`
- Modify: `tests/e2e/test_rail_collapse_contract.py`
- Modify: `tests/e2e/test_rail_home_control.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

**Interfaces:**
- Consumes: Tasks 1-11.
- Produces: no obsolete CSS/markup/test contract and retained screenshot evidence outside source truth.

- [ ] **Step 1: Scan for obsolete architecture**

Run:

```bash
rg -n "four-column|four per row|Plan tile|eight body|eight compact|floating Map|raya-course-rail-search|raya-command-search-form|raya-course-map-compact-preview|overscroll-behavior: contain" packages/static tests docs/foundation docs/guides
```

Classify every match. Discovery-workspace search forms are valid; reader-rail instances are not. Graph/canvas `overscroll-behavior` may be valid; left course-rail instances are not.

- [ ] **Step 2: Delete obsolete compensations and assertions**

Remove old four-column CSS, `Plan` label comments, tile-specific accessibility overrides, compact preview markup/JS/CSS, Page-brief-only position assertions, permissive wheel tests, floating opener tests, and comments that describe removed ownership. Do not weaken unrelated discovery, right-rail, or graph tests.

- [ ] **Step 3: Run the focused rail suite**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py \
  tests/contracts/test_documentation_surfaces.py \
  tests/e2e/test_rail_density.py \
  tests/e2e/test_rail_collapse_contract.py \
  tests/e2e/test_rail_home_control.py -q
```

Expected: PASS.

- [ ] **Step 4: Capture the required visual matrix**

Use the browser fixture at 1440, 1024, 894, 893, 640, 639, and 390px, with normal and short heights. Capture expanded/mini or closed/open drawer as applicable, plus article-large-text, OpenDyslexic, reduced-motion, long-label, and print states. Keep evidence under a temporary/debug directory, never as source truth.

For each capture assert before screenshot:

```javascript
({
  horizontalOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  maps: document.querySelectorAll('#raya-course-map').length,
  owner: getComputedStyle(document.querySelector('[data-raya-course-map-navigation]')).overflowY,
  externalResources: performance.getEntriesByType('resource')
    .map(entry => new URL(entry.name))
    .filter(url => url.origin !== location.origin).length
})
```

Require overflow <=1, maps=1, owner=`auto`, externalResources=0.

- [ ] **Step 5: Inspect screenshots manually**

Reject any clipped controls, character-by-character labels, nested scrollbar, card-like action tile, overlap, missing footer/header, obscured safe area, unreadable long label, or article/rail collision. Record the retained debug report path in the task report, not in committed docs.

- [ ] **Step 6: Commit cleanup**

```bash
git add packages/static tests docs/foundation docs/guides
git commit -m "Remove obsolete rail density contracts"
```

### Task 13: Full Gates, Adversarial Review, Local Deployment, And Handoff

**Files:**
- No file changes are planned. A gate or review failure returns to the task that owns the behavior and uses that task's file list and focused test.

**Interfaces:**
- Consumes: complete implementation.
- Produces: verified branch, local browser URL, and evidence suitable for PR/deployment review.

- [ ] **Step 1: Run the full local Python suite**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q
```

Expected: PASS with zero failures.

- [ ] **Step 2: Run the focused render-debug gate**

```bash
RAYA_RENDER_DEBUG_KEEP=1 ./scripts/check-render-debug.sh
```

Expected: `check-render-debug: passed`; retain the printed report path for review.

- [ ] **Step 3: Run canonical host checks**

```bash
./scripts/check.sh
```

Expected: `check: passed`.

- [ ] **Step 4: Run the smoke test**

```bash
./scripts/smoke-test.sh
```

Expected: successful validate/build/inspection of temporary external courses.

- [ ] **Step 5: Run Docker checks after host checks**

```bash
./scripts/check-docker.sh
```

Expected: `check-docker: passed`.

- [ ] **Step 6: Request adversarial reviews**

Dispatch independent reviewers for:

```text
1. Foundation/role/contract agreement and storage/no-inference boundaries.
2. Responsive UX, native scroll, touch targets, focus/inertness, and visual matrix.
3. Builder/shell/prepaint technical correctness, migration cleanup, and test quality.
```

Resolve every verified Critical or Important finding with a focused red-green test and a separate fix commit. Push back with repository evidence when a suggestion contradicts the approved design.

- [ ] **Step 7: Re-run all gates after review fixes**

Repeat Steps 1-5 in this task. Previous green output is not evidence after a fix.

- [ ] **Step 8: Start a local preview for user comparison**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --host 0.0.0.0 --port 0
```

Keep the process running, report the emitted browser URL, and verify the URL with Chromium at 1440 and 390 before handoff. `uv run raya preview --help` was checked while writing this plan and confirms both `--host` and `--port`.

- [ ] **Step 9: Verify repository state and commit final fixes**

```bash
git diff --check
git status --short --branch
git log --oneline -15
```

Every Step 6 review fix must already have its own focused commit. At this point
`git status --short` must be empty; if it is not, identify the owning task and
finish its red-green-commit cycle before handoff.

- [ ] **Step 10: Prepare the handoff**

Report the local URL, commits, exact gate results, render-debug report path, screenshots reviewed, and any residual risk. Do not push, merge, create a PR, or publish to GitHub Pages unless the user explicitly requests that external action.

## Self-Review

### Spec Coverage

- Information architecture/header/actions/filter/tree/footer: Tasks 2, 4-6.
- One native scroll owner and gesture behavior: Tasks 4 and 10.
- 256px/48px geometry and all breakpoints: Tasks 3, 4, 7-9.
- Same semantic DOM and mobile Context: Tasks 2 and 9.
- State, prepaint, BFCache, storage, focus, inertness: Tasks 3, 7-9, 11.
- Fine/coarse density, hybrid touch, tooltips, Text size, OpenDyslexic: Tasks 5-6, 11.
- Workspace href integrity, rootless home, static/privacy/no-inference: Tasks 1-2, 11.
- Foundation and eight role surfaces: Tasks 1 and 12.
- Density migration cleanup: migration matrix and Task 12.
- Structural/visual matrix, full gates, adversarial review, preview URL: Tasks 12-13.

### Type And Selector Consistency

- Geometry constants: `RAIL_EXPANDED_PX`, `RAIL_MINI_PX`.
- Central owner: `.raya-course-map-navigation` and `[data-raya-course-map-navigation]`.
- Expanded regions: `.raya-course-actions`, `.raya-course-content`, `.raya-course-map-footer`.
- Structural collapsed region: `.raya-course-map-mini` and `[data-raya-course-map-mini]`.
- State records remain `{courseMap, learningRail}` under the existing versioned keys.
- No task introduces a second `#raya-course-map` or `#raya-course-map-list`.
