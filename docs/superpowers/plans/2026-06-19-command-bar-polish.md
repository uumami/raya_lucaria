# Command Bar Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the static course top command bar with dense, readable, icon-like controls adapted from old `main` without importing its stack or persistence.

**Architecture:** Reuse the current top command bar and shell script. Add semantic command classes in the renderer, polish CSS with existing skin tokens and generated CSS symbols, and verify behavior through contract and browser tests.

**Tech Stack:** Python 3.10 static builder, generated HTML/CSS/JS resources, pytest, Playwright, current Glintstone render fixture.

---

## File Structure

- Modify `packages/static/src/raya_static/builder.py`: refine `_render_top_command_bar(...)` control markup.
- Modify `packages/static/src/raya_static/rendering.py`: add command button/link CSS and responsive command bar layout.
- Modify `packages/static/src/raya_static/shell.py`: keep synchronized course-map toggle text compatible with the command-specific map button.
- Modify `tests/contracts/test_static_builder.py`: add/adjust command bar contract assertions.
- Modify `tests/e2e/test_preview_static_read_path.py`: add command bar desktop/mobile layout and interaction checks.

## Task 1: Contract Test Command Markup

- [ ] **Step 1: Write the failing contract test**

Add assertions to `test_render_fixture_builds_learning_shell` or a nearby focused test in `tests/contracts/test_static_builder.py`:

```python
assert '<a class="raya-command raya-command-graph"' in html
assert 'aria-label="Open course graph"' in html
assert '<button class="raya-command raya-command-map"' in html
assert 'aria-label="Collapse course map"' in html
assert '<button class="raya-command raya-command-font"' in html
assert 'aria-label="Toggle OpenDyslexic font"' in html
assert 'href="_raya/graph/index.html"' in html
```

- [ ] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_learning_shell -q
```

Expected: fail because the current command bar uses `raya-graph-link`, `raya-course-map-toggle`, and `raya-font-toggle` without the new `raya-command-*` classes.

- [ ] **Step 3: Implement markup**

In `_render_top_command_bar(...)`, render:

```python
f'<a class="raya-command raya-command-graph" href="{html.escape(graph_href)}" aria-label="Open course graph"><span class="raya-command-label">Graph</span></a>'
_render_course_map_toggle("Course map", class_name="raya-command raya-command-map")
'<button class="raya-command raya-command-font raya-font-toggle" type="button" aria-label="Toggle OpenDyslexic font" aria-pressed="false"><span class="raya-command-label">OpenDyslexic</span></button>'
```

Update `_render_course_map_toggle(...)` to accept `class_name: str = "raya-course-map-toggle"` and include both that class and `raya-course-map-toggle` when needed.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_learning_shell -q
```

Expected: pass.

## Task 2: CSS Contract For Compact Commands

- [ ] **Step 1: Write the failing CSS assertions**

In `test_rich_css_defines_learning_shell_regions`, add:

```python
assert ".raya-command {" in css
assert ".raya-command::before" in css
assert ".raya-command-graph::before" in css
assert ".raya-command-map::before" in css
assert ".raya-command-font::before" in css
assert "min-width: 2.75rem" in css
assert ".raya-command:focus-visible" in css
```

- [ ] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions -q
```

Expected: fail because `.raya-command` CSS does not exist.

- [ ] **Step 3: Implement CSS**

In `packages/static/src/raya_static/rendering.py`, replace the separate `.raya-font-toggle` and `.raya-graph-link` command styling with shared `.raya-command` styles. Keep `.raya-graph-back-link` for the graph page back link.

Use CSS generated symbols:

```css
.raya-command::before { ... }
.raya-command-graph::before { content: "G"; }
.raya-command-map::before { content: "M"; }
.raya-command-font::before { content: "Aa"; }
```

Keep text labels visible on desktop and compact them only under the existing small-screen media query if necessary.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions -q
```

Expected: pass.

## Task 3: Browser Layout And Interaction

- [ ] **Step 1: Write failing e2e checks**

Add a focused test in `tests/e2e/test_preview_static_read_path.py` that opens `index.html` at desktop and mobile widths and evaluates:

```javascript
const commands = Array.from(document.querySelectorAll('.raya-command'));
return {
  count: commands.length,
  minHeights: commands.map((item) => item.getBoundingClientRect().height),
  topBarWidth: document.querySelector('.raya-top-command-bar').scrollWidth,
  viewportWidth: document.documentElement.clientWidth,
  graphHref: document.querySelector('.raya-command-graph')?.getAttribute('href'),
  mapExpanded: document.querySelector('.raya-command-map')?.getAttribute('aria-expanded'),
  fontPressed: document.querySelector('.raya-command-font')?.getAttribute('aria-pressed'),
};
```

Assert:

```python
assert state["count"] == 3
assert all(height >= 36 for height in state["minHeights"])
assert state["topBarWidth"] <= state["viewportWidth"]
assert state["graphHref"] == "_raya/graph/index.html"
assert state["mapExpanded"] == "true"
assert state["fontPressed"] == "false"
```

Then click `.raya-command-map` and assert `aria-expanded == "false"`. Click `.raya-command-font` and assert `aria-pressed == "true"` and computed body font includes `OpenDyslexic`.

- [ ] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_command_bar_controls_are_dense_and_operable -q
```

Expected: fail before implementation.

- [ ] **Step 3: Adjust shell text synchronization if needed**

If the map command loses its label after shell initialization, update `setExpanded(...)` in `packages/static/src/raya_static/shell.py` so it changes text only for the inner map control or for buttons without `.raya-command-map`. The top command label should remain `Course map` while the `aria-label` changes between `Collapse course map` and `Expand course map`.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_command_bar_controls_are_dense_and_operable -q
```

Expected: pass.

## Task 4: Full Verification And Review

- [ ] **Step 1: Run focused checks**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_learning_shell tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions tests/e2e/test_preview_static_read_path.py::test_render_fixture_command_bar_controls_are_dense_and_operable -q
```

- [ ] **Step 2: Run full static renderer checks**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py -q
./scripts/check-render-debug.sh
```

- [ ] **Step 3: Request independent code review**

Ask a reviewer to inspect the diff against the plan and contract, with focus on local/static constraints, accessibility labels, command-bar layout, and not reintroducing persistent old-main behavior.

- [ ] **Step 4: Commit**

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py packages/static/src/raya_static/shell.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/superpowers/specs/2026-06-19-command-bar-polish-design.md docs/superpowers/plans/2026-06-19-command-bar-polish.md
git commit -m "Polish static command bar controls"
```

## Self-Review

- The plan covers markup, CSS, shell behavior, browser behavior, full verification, and review.
- No external assets or persistence are introduced.
- The plan preserves the current graph page, course map, and OpenDyslexic features.
- No source schema or artifact contract changes are required.
