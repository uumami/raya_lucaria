# Mobile Reader Chrome Compaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the mobile reader first viewport show learning content sooner while preserving every current static reader command.

**Architecture:** Keep generated HTML, URLs, data indexes, drawers, and scripts unchanged. Tighten only the small-screen reader command-bar CSS in `rendering.py`, with Playwright coverage proving the bar is shorter, the lesson title starts earlier, controls remain reachable, and no static-renderer boundaries are weakened.

**Tech Stack:** Python static renderer, generated CSS, Playwright e2e tests, local `uv` verification.

---

## File Structure

- Modify `tests/e2e/test_preview_static_read_path.py`: strengthen the existing mobile reader-shell test around first-viewport layout and command reachability.
- Modify `packages/static/src/raya_static/rendering.py`: adjust `@media (max-width: 520px)` reader command-bar spacing, search sizing, and compact context display.
- Modify `docs/superpowers/plans/2026-06-27-mobile-reader-chrome-compaction.md`: track evidence as steps complete.

No docs update is required for this slice because it changes presentation density only; it does not change reader commands, authoring syntax, static contracts, or role workflows.

## Task 1: Failing Mobile First-Viewport Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Strengthen the existing mobile reader test**

In `test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading`, replace the loose thresholds:

```python
assert topbar["height"] <= 180
assert first_heading["y"] <= 360
```

with:

```python
assert topbar["height"] <= 150
assert first_heading["y"] <= 320
```

Then add command reachability assertions after `_assert_no_horizontal_overflow(page)`:

```python
visible_controls = page.locator(
    ".raya-top-command-bar button:visible, "
    ".raya-top-command-bar a:visible, "
    ".raya-top-command-bar input:visible"
)
control_boxes = visible_controls.evaluate_all(
    """controls => controls.map((control) => {
      const rect = control.getBoundingClientRect();
      return {
        label: control.getAttribute('aria-label') || control.textContent.trim(),
        width: rect.width,
        height: rect.height,
      };
    })"""
)
assert control_boxes
assert all(box["height"] >= 36 for box in control_boxes)
command_state = page.evaluate(
    """() => ({
      searchInput: !!document.querySelector('.raya-command-search-input')
        ?.getClientRects().length,
      searchSubmit: !!document.querySelector('.raya-command-search-submit')
        ?.getClientRects().length,
      graphLink: !!document.querySelector('.raya-command-graph')
        ?.getClientRects().length,
      practiceLink: !!document.querySelector('.raya-command-practice')
        ?.getClientRects().length,
      tasksLink: !!document.querySelector('.raya-command-tasks')
        ?.getClientRects().length,
      scheduleLink: !!document.querySelector('.raya-command-schedule')
        ?.getClientRects().length,
      mapButton: !!document.querySelector('.raya-command-map')
        ?.getClientRects().length,
      textSizeButton: !!document.querySelector('.raya-text-size-toggle')
        ?.getClientRects().length,
      fontButton: !!document.querySelector('.raya-font-toggle')
        ?.getClientRects().length,
      skinButton: !!document.querySelector('[data-raya-skin-toggle]')
        ?.getClientRects().length,
    })"""
)
assert command_state == {
    "searchInput": True,
    "searchSubmit": True,
    "graphLink": True,
    "practiceLink": True,
    "tasksLink": True,
    "scheduleLink": True,
    "mapButton": True,
    "textSizeButton": True,
    "fontButton": True,
    "skinButton": True,
}
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading
```

Expected: FAIL because the current mobile top command bar is about `178px` high and the first `h1` starts around `355px`.

Fresh evidence: failed as expected with `assert 177.96875 <= 150`.

## Task 2: Compact Mobile Reader Chrome CSS

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Tighten the reader-only mobile command bar**

Inside the existing `@media (max-width: 520px)` block, update only the non-discovery reader command-bar rules:

```css
.raya-top-command-bar-inner {
  gap: 0.35rem;
  padding: 0.3rem 0.65rem;
}
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context {
  gap: 0.2rem 0.35rem;
  min-width: 0;
}
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-course,
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-page {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-course {
  max-width: 8.5rem;
}
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-page {
  max-width: 10.5rem;
}
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-position,
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-section {
  display: none;
}
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-course-tools {
  gap: 0.25rem;
}
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-group {
  gap: 0.2rem;
  padding: 0.1rem;
}
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-group-discovery {
  display: grid;
  grid-template-columns: minmax(8.5rem, 1fr) repeat(5, minmax(2.25rem, auto));
}
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-search-form {
  flex: none;
  min-width: 0;
  width: 100%;
}
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command {
  min-height: 2.25rem;
  min-width: 2.25rem;
  padding: 0.35rem;
}
```

Keep the existing `.raya-command-label` clipping so accessible labels remain the control names.

- [x] **Step 2: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading
```

Expected: PASS.

Fresh evidence: `1 passed in 5.79s`.

## Task 3: Broader Verification, Review, Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-27-mobile-reader-chrome-compaction.md`

- [x] **Step 1: Run focused reader-shell and mobile chrome tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_keyboard_shortcuts_move_between_sequence_pages
```

Expected: both tests pass.

Fresh evidence after the review fix: mobile reader, keyboard sequence, and
discovery command-bar regression tests passed with `3 passed in 21.31s`.

- [x] **Step 2: Run render debug**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: `check-render-debug: passed`.

Fresh evidence after the review fix: `render-debug-report: passed (129 check(s), report=/tmp/raya-render-debug.ICel06/index.html)` and `check-render-debug: passed`.

- [x] **Step 3: Run diff hygiene**

Run:

```bash
git diff --check
```

Expected: no output, exit code 0.

Fresh evidence after the review fix: no output, exit code 0.

- [x] **Step 4: Request independent code review**

Use `superpowers:requesting-code-review`. Ask the reviewer to inspect:

- mobile command reachability and touch target sizes;
- no regression in course-map drawer behavior;
- no new storage, fetch, external request, or browser-side MathJax dependency;
- no unintended changes to discovery workspace chrome.

Fresh evidence: review found one Important issue where shared mobile padding
also affected discovery command bars. The CSS now restores shared padding and
applies compact padding only to non-discovery reader command bars.

- [x] **Step 5: Commit**

Run:

```bash
git add packages/static/src/raya_static/rendering.py \
  tests/e2e/test_preview_static_read_path.py \
  docs/superpowers/plans/2026-06-27-mobile-reader-chrome-compaction.md
git commit -m "Compact mobile reader chrome"
```

Expected: commit succeeds.

Fresh evidence: commit `7e4a852` created with subject `Compact mobile reader chrome`.
