# Course Map Keyboard Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local keyboard movement and branch expand/collapse behavior to the rendered course map.

**Architecture:** Keep the existing static course-map DOM and shell script. Add a single keydown handler plus small helper functions in `packages/static/src/raya_static/shell.py`, and cover it with contract and Playwright e2e tests.

**Tech Stack:** Python 3.10, generated static HTML/CSS/JS, pytest, Playwright/Chromium.

**Status: implemented.** This checklist is a historical execution record. Current
source support lives in course-map keyboard helpers in
`packages/static/src/raya_static/shell.py` and focused contract/browser tests.

---

### Task 1: Contract Test for Shell Resource

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write the failing test assertions**

In `test_static_build_writes_local_shell_resource`, add assertions after the existing course-map scan assertions:

```python
    assert "function visibleCourseMapLinks" in script_text
    assert "function handleCourseMapKeyboardNavigation" in script_text
    assert 'map.addEventListener("keydown", handleCourseMapKeyboardNavigation)' in script_text
```

- [ ] **Step 2: Run the contract test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource -q
```

Expected: FAIL because the shell script does not yet contain `visibleCourseMapLinks`.

### Task 2: Browser Test for Keyboard Movement

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add browser assertions to the existing nested course-map test**

In `test_minimal_course_map_nested_sections_are_expanded_and_collapsible`, after the `scan_sibling_collapse` assertion and before exiting scan mode with expand-all, add:

```python
                    page.focus('[data-raya-map-node="map-branch-b"] > .raya-course-map-node-row a')
                    page.keyboard.press("ArrowRight")
                    keyboard_branch_child = page.evaluate(
                        """() => ({
                          activeNode: document.activeElement
                            ?.closest("[data-raya-map-node]")
                            ?.getAttribute("data-raya-map-node"),
                          branchBExpanded: document
                            .querySelector('[data-raya-map-node="map-branch-b"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                        })"""
                    )
                    assert keyboard_branch_child == {
                        "activeNode": "map-branch-b-child",
                        "branchBExpanded": "true",
                    }

                    page.keyboard.press("ArrowLeft")
                    keyboard_parent_focus = page.evaluate(
                        """() => ({
                          activeNode: document.activeElement
                            ?.closest("[data-raya-map-node]")
                            ?.getAttribute("data-raya-map-node"),
                          branchBExpanded: document
                            .querySelector('[data-raya-map-node="map-branch-b"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                        })"""
                    )
                    assert keyboard_parent_focus == {
                        "activeNode": "map-branch-b",
                        "branchBExpanded": "true",
                    }

                    page.keyboard.press("ArrowLeft")
                    keyboard_parent_collapse = page.evaluate(
                        """() => ({
                          activeNode: document.activeElement
                            ?.closest("[data-raya-map-node]")
                            ?.getAttribute("data-raya-map-node"),
                          branchBExpanded: document
                            .querySelector('[data-raya-map-node="map-branch-b"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                          branchBChildVisible: !!document
                            .querySelector('[data-raya-map-node="map-branch-b-child"]')
                            ?.checkVisibility(),
                        })"""
                    )
                    assert keyboard_parent_collapse == {
                        "activeNode": "map-branch-b",
                        "branchBExpanded": "false",
                        "branchBChildVisible": False,
                    }

                    page.keyboard.press("ArrowUp")
                    keyboard_previous_visible = page.evaluate(
                        """() => document.activeElement
                          ?.closest("[data-raya-map-node]")
                          ?.getAttribute("data-raya-map-node")"""
                    )
                    assert keyboard_previous_visible == "first-topic"

                    page.keyboard.press("ArrowDown")
                    keyboard_next_visible = page.evaluate(
                        """() => document.activeElement
                          ?.closest("[data-raya-map-node]")
                          ?.getAttribute("data-raya-map-node")"""
                    )
                    assert keyboard_next_visible == "map-branch-b"

                    page.keyboard.press("Home")
                    keyboard_first_visible = page.evaluate(
                        """() => document.activeElement
                          ?.closest("[data-raya-map-node]")
                          ?.getAttribute("data-raya-map-node")"""
                    )
                    assert keyboard_first_visible == "course-root"

                    page.keyboard.press("End")
                    keyboard_last_visible = page.evaluate(
                        """() => document.activeElement
                          ?.closest("[data-raya-map-node]")
                          ?.getAttribute("data-raya-map-node")"""
                    )
                    assert keyboard_last_visible == "map-branch-b"
```

- [ ] **Step 2: Run the e2e test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_minimal_course_map_nested_sections_are_expanded_and_collapsible -q
```

Expected: FAIL because arrow keys do not yet move focus inside the course map.

### Task 3: Implement Shell Keyboard Navigation

**Files:**
- Modify: `packages/static/src/raya_static/shell.py`

- [ ] **Step 1: Add helper functions near existing course-map helpers**

Add functions for visible link detection, focused node lookup, parent link lookup, first child link lookup, and focus movement.

- [ ] **Step 2: Add `handleCourseMapKeyboardNavigation`**

The handler must:

- ignore editable targets and modifier-key chords.
- ignore focus outside `#raya-course-map-list`.
- use visible map links for `ArrowDown`, `ArrowUp`, `Home`, and `End`.
- use `setMapNodeExpanded` for `ArrowRight` and `ArrowLeft`.
- preserve scan-mode sibling collapse through the existing `setMapNodeExpanded` path.

- [ ] **Step 3: Attach the handler**

Add:

```javascript
  map.addEventListener("keydown", handleCourseMapKeyboardNavigation);
```

near the other course-map event listeners.

- [ ] **Step 4: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource tests/e2e/test_preview_static_read_path.py::test_minimal_course_map_nested_sections_are_expanded_and_collapsible -q
```

Expected: PASS.

### Task 4: Verification and Review

**Files:**
- Check: `packages/static/src/raya_static/shell.py`
- Check: `tests/contracts/test_static_builder.py`
- Check: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Run render debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS with no raw TeX, no external renderer requests, no overflow regressions, and static parity checks passing.

- [ ] **Step 2: Run diff checks**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors; only intended docs, shell, and test files changed.

- [ ] **Step 3: Request independent review**

Ask reviewers to inspect keyboard behavior, storage/fetch constraints, and interaction with scan/filter/collapsed-map states.

- [ ] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-course-map-keyboard-navigation-design.md docs/superpowers/plans/2026-06-26-course-map-keyboard-navigation.md packages/static/src/raya_static/shell.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add course map keyboard navigation"
git push origin new_rayalucaria
```
