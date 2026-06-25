# Command Bar Iconography Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace letter-like command badges with local semantic glyphs across reader and discovery command bars.

**Architecture:** Keep existing generated HTML, command classes, links, labels, and scripts. Change only scoped CSS in `rendering.py` and add browser assertions in `test_preview_static_read_path.py` so the glyph vocabulary is verified from computed styles.

**Tech Stack:** Python static builder CSS string, Playwright e2e tests, pytest, Superpowers workflow.

---

## File Structure

- Modify `packages/static/src/raya_static/rendering.py` for command pseudo-element glyph content.
- Modify `tests/e2e/test_preview_static_read_path.py` for failing command-glyph assertions.

## Task 1: Add Failing Command Glyph Tests

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add a helper to read command pseudo content**

Add near existing browser helper functions:

```python
def _command_badge_content(page, selector: str) -> str:
    return page.locator(selector).evaluate(
        "node => getComputedStyle(node, '::before').content"
    )
```

- [ ] **Step 2: Add reader command assertions**

Inside `test_render_fixture_desktop_shell_has_modern_workspace_chrome`, after
the `chrome` evaluation and before collapsing controls, collect command badge
content:

```python
badges = page.evaluate(
    """() => Object.fromEntries(
      Array.from(document.querySelectorAll('.raya-top-command-bar .raya-command'))
        .map((node) => [
          Array.from(node.classList).find((name) => name.startsWith('raya-command-')),
          getComputedStyle(node, '::before').content
        ])
    )"""
)
```

Then assert after the browser closes:

```python
assert badges["raya-command-map"] == '"◇"'
assert badges["raya-command-search"] == '"⌕"'
assert badges["raya-command-graph"] == '"⌘"'
assert badges["raya-command-practice"] == '"✓"'
assert badges["raya-command-tasks"] == '"☑"'
assert badges["raya-command-schedule"] == '"◷"'
assert badges["raya-command-size"] == '"A+"'
assert badges["raya-command-font"] == '"Aa"'
```

- [ ] **Step 3: Add discovery command assertions**

Inside `test_preview_serves_local_visual_graph_surface`, after confirming the
discovery command bar is visible, evaluate:

```python
graph_badges = page.evaluate(
    """() => Object.fromEntries(
      Array.from(document.querySelectorAll('.raya-discovery-command-bar .raya-command'))
        .map((node) => [
          Array.from(node.classList).find((name) => name.startsWith('raya-command-')),
          getComputedStyle(node, '::before').content
        ])
    )"""
)
assert graph_badges["raya-command-home"] == '"⌂"'
assert graph_badges["raya-command-search"] == '"⌕"'
assert graph_badges["raya-command-practice"] == '"✓"'
assert graph_badges["raya-command-tasks"] == '"☑"'
assert graph_badges["raya-command-schedule"] == '"◷"'
assert graph_badges["raya-command-size"] == '"A+"'
assert graph_badges["raya-command-font"] == '"Aa"'
```

- [ ] **Step 4: Run RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_shell_has_modern_workspace_chrome -q
```

Expected: fail because current command badges compute as the old letter content
instead of the exact semantic glyph vocabulary.

## Task 2: Implement Local Semantic Command Glyphs

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Replace command pseudo-element content**

In `rendering.py`, replace the current `.raya-command-*-::before` content
rules with semantic glyphs:

```css
.raya-command-search::before {
  content: "⌕";
}
.raya-command-home::before {
  content: "⌂";
}
.raya-command-graph::before {
  content: "⌘";
}
.raya-command-practice::before {
  content: "✓";
}
.raya-command-tasks::before {
  content: "☑";
}
.raya-command-schedule::before {
  content: "◷";
}
.raya-command-map::before {
  content: "◇";
}
.raya-command-size::before {
  content: "A+";
}
.raya-command-font::before {
  content: "Aa";
}
```

Keep `.raya-command-label` text and all generated `aria-label`s unchanged.

- [ ] **Step 2: Run GREEN focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_shell_has_modern_workspace_chrome -q
```

Expected: pass.

## Task 3: Verify No Layout Or Static Boundary Regression

**Files:**
- Test only.

- [ ] **Step 1: Run broad workspace overflow check**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_rendered_surfaces_have_no_obvious_layout_overlap_at_viewports -q
```

Expected: pass with no reader, inspect, gallery, or workspace horizontal overflow.

- [ ] **Step 2: Run render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: pass with no external renderer requests, no raw visible TeX leakage,
no overflow, and static copied-site parity.

## Task 4: Review, Commit, Push, Preview

**Files:**
- Review: full git diff.

- [ ] **Step 1: Request independent review**

Ask reviewers to check that command glyphs improve UX without breaking current
static renderer boundaries, accessibility labels, mobile layout, or tests.

- [ ] **Step 2: Run host gate**

Run:

```bash
./scripts/check.sh
```

Expected: pass.

- [ ] **Step 3: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-25-command-bar-iconography-design.md docs/superpowers/plans/2026-06-25-command-bar-iconography.md packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git commit -m "Polish command bar iconography"
git push origin new_rayalucaria
```

- [ ] **Step 4: Restart local preview**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --host 127.0.0.1 --port 0
```

Report the root and graph workspace URLs.

## Self-Review

- Spec coverage: command bar glyph, static boundary, mobile no-overflow, focused
  tests, render-debug, commit, push, and preview are covered.
- Placeholder scan: no placeholders remain.
- Type consistency: selectors and file paths match the current renderer and e2e
  test names.
