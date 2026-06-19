# Keyboard Page Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reset-native keyboard previous/next page navigation using existing generated sequence links.

**Architecture:** The builder marks generated sequence links with `data-raya-prev-page` and `data-raya-next-page`. The local shell script listens for keyboard shortcuts and navigates through those links only when the event did not originate in an editable control. Foundation docs describe the behavior as a static reader control, not progress or adaptive study state.

**Tech Stack:** Python static renderer, generated local JavaScript, pytest contract tests, Playwright e2e tests.

---

### Task 1: Failing Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add contract assertions**

In `test_static_builder_renders_collapsible_shell_controls_and_page_position`, assert:

```python
assert 'rel="next" data-raya-next-page href="unit/index.html"' in html
assert 'rel="prev" data-raya-prev-page href="../index.html"' in middle_html
assert 'rel="next" data-raya-next-page href="topic/index.html"' in middle_html
```

In `test_static_build_writes_local_shell_resource`, assert:

```python
assert "data-raya-prev-page" in script_text
assert "data-raya-next-page" in script_text
assert "ArrowLeft" in script_text
assert "ArrowRight" in script_text
assert "isEditableNavigationTarget" in script_text
assert "sessionStorage" not in script_text
```

- [x] **Step 2: Add browser navigation test**

Add `test_render_fixture_keyboard_shortcuts_move_between_sequence_pages` to `tests/e2e/test_preview_static_read_path.py`. Use `create_preview(...)`, open the render fixture root page, press `ArrowRight`, assert the URL ends with `/static-path/index.html`, inject and focus an input, press `ArrowRight`, assert URL is unchanged, blur the input, dispatch `Alt+ArrowRight` and assert it is not canceled and does not trigger Raya navigation, press `Alt+j`, assert URL ends with `/math-authoring/index.html`, then press `Alt+k` and assert it returns to `/static-path/index.html`.

- [x] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position \
  tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_keyboard_shortcuts_move_between_sequence_pages
```

Expected: fail because the data attributes and keyboard handler do not exist yet.

### Task 2: Mark Sequence Links

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Add data attributes to `_sequence_links(...)`**

Change previous and next link rendering to:

```python
links.append(
    f'<a rel="prev" data-raya-prev-page href="{html.escape(href)}">'
    f"Previous: {html.escape(previous.nav_title or previous.title)}</a>"
)
```

and:

```python
links.append(
    f'<a rel="next" data-raya-next-page href="{html.escape(href)}">'
    f"Next: {html.escape(next_page.nav_title or next_page.title)}</a>"
)
```

- [x] **Step 2: Run contract test for sequence markup**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position
```

Expected: the sequence markup assertions pass; shell-script assertions still fail until Task 3.

### Task 3: Shell Keyboard Handler

**Files:**
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `docs/foundation/20_learning_renderer_contract.md`

- [x] **Step 1: Add local keyboard navigation**

In `shell.py`, add:

```javascript
function isEditableNavigationTarget(target) {
  if (!(target instanceof Element)) return false;
  const tagName = target.tagName.toLowerCase();
  return (
    target.isContentEditable ||
    tagName === "input" ||
    tagName === "textarea" ||
    tagName === "select"
  );
}

function navigateToSequenceLink(selector) {
  const link = document.querySelector(selector);
  const href = link ? link.getAttribute("href") : "";
  if (!href) return false;
  window.location.href = href;
  return true;
}

function handleSequenceKeyboardNavigation(event) {
  if (isEditableNavigationTarget(event.target)) return false;
  if (event.ctrlKey || event.metaKey || event.shiftKey) return false;
  const previousRequested =
    (!event.altKey && event.key === "ArrowLeft") ||
    (event.altKey && event.key === "k");
  const nextRequested =
    (!event.altKey && event.key === "ArrowRight") ||
    (event.altKey && event.key === "j");
  if (!previousRequested && !nextRequested) return false;
  const selector = previousRequested ? "[data-raya-prev-page]" : "[data-raya-next-page]";
  if (navigateToSequenceLink(selector)) {
    event.preventDefault();
    return true;
  }
  return false;
}
```

Register it with the existing `document.addEventListener("keydown", ...)` path or a separate listener in the same shell closure.

- [x] **Step 2: Update foundation contract**

In `docs/foundation/20_learning_renderer_contract.md`, update reader-controls wording to include keyboard previous/next page navigation and preserve the no-backend/no-CDN/no-progress constraints.

- [x] **Step 3: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position \
  tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_keyboard_shortcuts_move_between_sequence_pages
```

Expected: focused tests pass.

### Task 4: Review And Verification

**Files:**
- All modified files from Tasks 1-3.

- [x] **Step 1: Run full relevant verification**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -q
./scripts/check-render-debug.sh
```

Expected: all commands exit 0.

- [x] **Step 2: Request code review**

Ask an independent reviewer to inspect keyboard behavior, shortcut conflicts, editable-control guards, static/local constraints, and test coverage.

- [x] **Step 3: Fix review findings**

Patch any Critical or Important findings and re-run focused tests plus any relevant full command.

- [x] **Step 4: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-06-19-keyboard-page-navigation-design.md \
  docs/superpowers/plans/2026-06-19-keyboard-page-navigation.md \
  docs/foundation/20_learning_renderer_contract.md \
  packages/static/src/raya_static/builder.py \
  packages/static/src/raya_static/shell.py \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Add keyboard page navigation"
```
