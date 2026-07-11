# Course Map Tiny Tray Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the medium-width course-map tools into a small, intentional Tiny Tray under the map header, with stable DOM order and browser verification.

**Architecture:** Use a small renderer markup move so visual order and DOM/focus order match: header, tools tray, page position, map list. Scope CSS to medium fixed rails so the mobile drawer keeps its existing chrome. Extend Playwright e2e checks so a bottom strip, duplicate strip, weak icon rhythm, or mobile regression cannot pass.

**Tech Stack:** Python static renderer, generated HTML strings, CSS in `packages/static/src/raya_static/rendering.py`, Playwright-based pytest e2e tests.

---

### Task 1: Reorder Course Map Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing structural assertion**

In `test_render_fixture_tablet_course_map_uses_compact_tool_strip`, extend the evaluated state with box order and exact visible command count:

```python
# inside page.evaluate return object
headerBottom: Math.round(
  document.querySelector('.raya-course-map-header').getBoundingClientRect().bottom
),
toolsTop: Math.round(toolsBox.top),
toolsBottom: Math.round(toolsBox.bottom),
positionTop: Math.round(
  document.querySelector('#raya-course-map > .raya-page-position').getBoundingClientRect().top
),
positionBottom: Math.round(
  document.querySelector('#raya-course-map > .raya-page-position').getBoundingClientRect().bottom
),
listTop: Math.round(
  document.querySelector('#raya-course-map-list').getBoundingClientRect().top
),
visibleCommandCount: visibleCommands.length,
```

Then assert:

```python
assert state["headerBottom"] <= state["toolsTop"]
assert state["toolsBottom"] <= state["positionTop"]
assert state["positionBottom"] <= state["listTop"]
assert state["visibleCommandCount"] == 7
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_tablet_course_map_uses_compact_tool_strip
```

Expected: fail because `.raya-page-position` is currently inside `.raya-course-map-header` and tools render after the map list.

- [ ] **Step 3: Move page position and tools in the renderer markup**

In `packages/static/src/raya_static/builder.py`, change the generated course-map structure from:

```python
'<p class="raya-region-title">Course map</p>',
f'<p class="raya-page-position">{position}</p>' if position else "",
...
"</div>",
...
'<div class="raya-course-map-list" id="raya-course-map-list" aria-hidden="false">',
...
"</div>",
tools_html,
```

to:

```python
'<p class="raya-region-title">Course map</p>',
...
"</div>",
tools_html,
f'<p class="raya-page-position">{position}</p>' if position else "",
...
'<div class="raya-course-map-list" id="raya-course-map-list" aria-hidden="false">',
...
"</div>",
```

Keep the drawer-only position inside `.raya-course-map-drawer-chrome`.

- [ ] **Step 4: Run the focused test and verify the structural assertion can pass after CSS is updated**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_tablet_course_map_uses_compact_tool_strip
```

Expected: the original bottom-strip styling may still fail later visual assertions, but the DOM order selectors should now resolve.

### Task 2: Style the Medium Tiny Tray

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Update the focused test with Tiny Tray visual requirements**

In `test_render_fixture_tablet_course_map_uses_compact_tool_strip`, add measured values for tray and commands:

```python
const titleBox = document.querySelector('.raya-course-map-header .raya-region-title')
  .getBoundingClientRect();
const commandsUnion = visibleCommands.reduce((box, command) => {
  const rect = command.getBoundingClientRect();
  return {
    left: Math.min(box.left, rect.left),
    right: Math.max(box.right, rect.right),
    top: Math.min(box.top, rect.top),
    bottom: Math.max(box.bottom, rect.bottom),
  };
}, {left: Infinity, right: -Infinity, top: Infinity, bottom: -Infinity});
```

Return and assert:

```python
assert state["toolsTop"] < state["mapBottom"] - 120
assert state["toolsLeft"] <= state["titleLeft"] + 8
assert state["toolsWidth"] < state["mapWidth"] * 0.9
assert state["toolsWidth"] <= state["commandsUnionWidth"] + 24
assert state["toolsHeight"] <= 44
assert state["toolsBorderTopWidth"] == "0px"
assert state["toolsBackground"] != "rgba(0, 0, 0, 0)"
assert state["toolsBoxShadow"] == "none"
assert state["toolsBorderRadiusPx"] >= 12
assert [group["kind"] for group in state["visibleGroups"]] == ["discovery", "comfort"]
assert state["groupGap"] >= 4
assert all(32 <= command["width"] <= 38 and 32 <= command["height"] <= 38 for command in state["visibleCommands"])
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_tablet_course_map_uses_compact_tool_strip
```

Expected: fail because current commands are 28px and the tools container is transparent.

- [ ] **Step 3: Implement scoped medium tray CSS**

In `packages/static/src/raya_static/rendering.py`, inside the `@media (min-width: 640px) and (max-width: 1279px)` block:

```css
.raya-course-map-tools {
  align-self: flex-start;
  background: color-mix(in srgb, var(--raya-color-surface) 92%, var(--raya-color-border));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 76%, var(--raya-color-surface));
  border-radius: 999px;
  box-shadow: none;
  display: inline-grid;
  gap: 0;
  margin: 0.45rem 0 0.3rem;
  max-width: max-content;
  padding: 0.15rem 0.22rem;
  width: fit-content;
}
.raya-course-map-tool-grid {
  align-items: center;
  display: inline-flex;
  flex-wrap: nowrap;
  gap: 0.16rem;
}
.raya-course-map-tool-grid .raya-command-group {
  gap: 0.04rem;
}
.raya-course-map-tool-grid .raya-command-group-comfort {
  border-left: 1px solid color-mix(in srgb, var(--raya-color-border) 82%, transparent);
  margin-left: 0.18rem;
  padding-left: 0.28rem;
}
.raya-course-map-tool-grid .raya-command {
  height: 2rem;
  min-height: 2rem;
  min-width: 2rem;
  width: 2rem;
}
.raya-course-map-tool-grid .raya-command[aria-pressed="true"] {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 64%, transparent);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--raya-color-accent) 30%, transparent);
  color: var(--raya-color-text);
}
```

- [ ] **Step 4: Neutralize the 640-767 override**

In the `@media (min-width: 640px) and (max-width: 767px)` block, remove or override values that re-expand tray spacing:

```css
.raya-course-map-tools {
  margin: 0.4rem 0 0.28rem;
  padding: 0.14rem 0.2rem;
}
.raya-course-map-tool-grid {
  gap: 0.14rem;
}
.raya-course-map-tool-grid .raya-command {
  min-height: 2rem;
  height: 2rem;
  min-width: 2rem;
  width: 2rem;
  padding: 0;
}
```

- [ ] **Step 5: Run the focused test and verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_tablet_course_map_uses_compact_tool_strip
```

Expected: pass.

### Task 3: Add Breakpoint and Regression Coverage

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add a reusable browser measurement helper inside the test**

Inside `test_render_fixture_tablet_course_map_uses_compact_tool_strip`, add a local JavaScript helper string that opens the map and measures the tray. Reuse it for widths `640`, `767`, `768`, `912`, and `1279`.

The helper should return:

```javascript
{
  width: window.innerWidth,
  mapWidth,
  mapHeight,
  headerBottom,
  toolsTop,
  toolsBottom,
  positionTop,
  positionBottom,
  listTop,
  toolsWidth,
  toolsHeight,
  visibleCommandTexts,
  groupKinds,
  commandSizes,
  toolsBackground,
  toolsBorderTopWidth,
  toolsBoxShadow,
}
```

- [ ] **Step 2: Assert each medium breakpoint**

For each width in `[640, 767, 768, 912, 1279]`, assert:

```python
assert 244 <= state["mapWidth"] <= 264
assert state["mapHeight"] >= state["viewportHeight"] - 32
assert state["headerBottom"] <= state["toolsTop"]
assert state["toolsBottom"] <= state["positionTop"]
assert state["positionBottom"] <= state["listTop"]
assert state["visibleCommandTexts"] == [
    "Search",
    "Graph",
    "Practice",
    "Tasks",
    "Schedule",
    "Text size",
    "OpenDyslexic",
]
assert state["groupKinds"] == ["discovery", "comfort"]
assert state["toolsBackground"] != "rgba(0, 0, 0, 0)"
assert state["toolsBorderTopWidth"] == "0px"
assert state["toolsBoxShadow"] == "none"
```

- [ ] **Step 3: Keep mobile drawer regression targeted**

Run the existing mobile drawer test:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_course_map_drawer_has_comfort_chrome
```

Expected: pass; if it fails, scope medium tray selectors so drawer geometry is unchanged.

- [ ] **Step 4: Run broader focused browser subset**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "medium_reader_rails_are_overlay_controls or tablet_course_map_uses_compact_tool_strip or tablet_keeps_course_map_and_learning_rail_inline or mobile_course_map_drawer_has_comfort_chrome or command_bar_controls_are_dense_and_operable"
```

Expected: all selected tests pass.

### Task 4: Local Preview, Visual Inspection, and Deployment

**Files:**
- Modify: `docs/superpowers/plans/2026-07-08-course-map-tiny-tray.md` only for checkbox updates if executing this plan.

- [ ] **Step 1: Run full local host gate**

Run:

```bash
./scripts/check.sh
```

Expected: `check: passed`.

- [ ] **Step 2: Run full Docker gate**

Run:

```bash
./scripts/check-docker.sh
```

Expected: `check-docker: passed`.

- [ ] **Step 3: Start a local preview for user inspection**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview docs --host 127.0.0.1 --port 50759
```

Expected: command reports `http://127.0.0.1:50759/` or `http://localhost:50759/` as the local entrypoint URL. If port `50759` is occupied, stop the stale local preview process that owns that port and rerun this command.

- [ ] **Step 4: Verify with Chromium**

Use Playwright at the local preview URL with viewport `913x945`:

```python
page.click("#raya-course-map .raya-course-map-toggle")
page.screenshot(path="/tmp/raya-local-tiny-tray-map.png", full_page=False)
```

Confirm:

- tray is under the header;
- no bottom row remains;
- tools are readable, grouped, and compact;
- content is not occluded.

- [ ] **Step 5: Commit implementation**

Commit the implementation and tests:

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py docs/superpowers/plans/2026-07-08-course-map-tiny-tray.md
git commit -m "Move course map tools into tiny tray"
```

- [ ] **Step 6: Push, deploy, and live-verify**

Run:

```bash
git push origin new_rayalucaria
HEAD_SHA="$(git rev-parse HEAD)"
CHECK_RUN_ID="$(gh run list --limit 30 --json databaseId,headSha,name,event --jq '.[] | select(.name == "Checks" and .headSha == "'"$HEAD_SHA"'") | .databaseId' | head -n 1)"
test -n "$CHECK_RUN_ID"
gh run watch "$CHECK_RUN_ID" --exit-status
gh workflow run "Deploy Docs to GitHub Pages" --ref new_rayalucaria
sleep 5
DEPLOY_RUN_ID="$(gh run list --limit 30 --json databaseId,headSha,name,event --jq '.[] | select(.name == "Deploy Docs to GitHub Pages" and .headSha == "'"$HEAD_SHA"'" and .event == "workflow_dispatch") | .databaseId' | head -n 1)"
test -n "$DEPLOY_RUN_ID"
gh run watch "$DEPLOY_RUN_ID" --exit-status
```

Then verify the live URL with Chromium using a cache-busting query:

```bash
LIVE_URL="https://uumami.wiki/raya_lucaria/?v=$(git rev-parse --short HEAD)"
```

Expected: live map panel at `$LIVE_URL` matches the local Tiny Tray screenshot.
