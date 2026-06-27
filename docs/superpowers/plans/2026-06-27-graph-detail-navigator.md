# Graph Detail Navigator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact selected-page detail navigator to the generated Graph workspace so learners can jump to Summary, Relationships, Study, Sequence, and Links without losing the graph context.

**Architecture:** The static builder emits native button controls inside the existing selected-page detail panel. The local graph script enables/disables buttons and performs transient in-panel scroll/focus behavior based on already rendered selected-page sections. Renderer CSS styles the buttons with existing graph/detail tokens.

**Tech Stack:** Python 3.10, pytest, Playwright, static HTML/CSS/JavaScript in `packages/static`.

---

## Files

- Modify `packages/static/src/raya_static/builder.py`: emit the selected-page detail nav markup.
- Modify `packages/static/src/raya_static/graph.py`: initialize nav targets, enable/disable buttons in `renderDetail()`, and handle local jump/focus.
- Modify `packages/static/src/raya_static/rendering.py`: style nav controls and focus targets.
- Modify `tests/e2e/test_preview_static_read_path.py`: add generated-markup and browser behavior tests.

## Task 1: Generated Detail Navigator Markup

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Write the failing static markup test**

Add this test near existing graph generated HTML tests in `tests/e2e/test_preview_static_read_path.py`:

```python
def test_graph_workspace_renders_selected_detail_navigator(
    tmp_path: Path,
) -> None:
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        graph_html = _fetch_text(f"{handle.base_url}/_raya/graph/index.html")

        assert 'data-raya-graph-detail-nav' in graph_html
        for target, label in (
            ("summary", "Summary"),
            ("relationships", "Relationships"),
            ("study", "Study"),
            ("sequence", "Sequence"),
            ("links", "Links"),
        ):
            assert (
                '<button type="button" class="raya-graph-detail-nav-button" '
                f'data-raya-graph-detail-nav-target="{target}">{label}</button>'
            ) in graph_html
    finally:
        handle.close()
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_graph_workspace_renders_selected_detail_navigator -q
```

Expected: FAIL because `data-raya-graph-detail-nav` does not exist yet.

- [ ] **Step 3: Emit navigator markup**

In `packages/static/src/raya_static/builder.py`, immediately after `</div>` for `.raya-graph-detail-header`, add:

```python
            (
                '<nav class="raya-graph-detail-nav" data-raya-graph-detail-nav '
                'aria-label="Selected page detail sections" hidden>'
                '<button type="button" class="raya-graph-detail-nav-button" '
                'data-raya-graph-detail-nav-target="summary">Summary</button>'
                '<button type="button" class="raya-graph-detail-nav-button" '
                'data-raya-graph-detail-nav-target="relationships">Relationships</button>'
                '<button type="button" class="raya-graph-detail-nav-button" '
                'data-raya-graph-detail-nav-target="study">Study</button>'
                '<button type="button" class="raya-graph-detail-nav-button" '
                'data-raya-graph-detail-nav-target="sequence">Sequence</button>'
                '<button type="button" class="raya-graph-detail-nav-button" '
                'data-raya-graph-detail-nav-target="links">Links</button>'
                "</nav>"
            ),
```

- [ ] **Step 4: Run the test to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_graph_workspace_renders_selected_detail_navigator -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/e2e/test_preview_static_read_path.py packages/static/src/raya_static/builder.py
git commit -m "Add graph detail navigator markup"
```

## Task 2: Navigator Behavior and Styling

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Write the failing browser behavior test**

Add this test near existing graph selected-page detail tests:

```python
def test_graph_detail_navigator_jumps_without_state_or_storage(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        graph_js = _fetch_text(f"{handle.base_url}/_raya/render/graph.js")
        assert "fetch(" not in graph_js
        assert "XMLHttpRequest" not in graph_js
        assert "localStorage" not in graph_js
        assert "sessionStorage" not in graph_js

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 950})
                requests: list[str] = []
                page.on("request", lambda request: requests.append(request.url))
                try:
                    page.goto(
                        f"{handle.base_url}/_raya/graph/index.html?page=reader-ux",
                        wait_until="networkidle",
                    )
                    requests.clear()
                    detail_panel = page.locator("[data-raya-graph-detail-panel]")
                    page.wait_for_selector("[data-raya-graph-detail-panel]:not([hidden])")
                    nav = page.locator("[data-raya-graph-detail-nav]")
                    assert nav.is_visible()
                    buttons = nav.locator("[data-raya-graph-detail-nav-target]")
                    assert buttons.evaluate_all(
                        "nodes => nodes.map((node) => node.textContent.trim())"
                    ) == ["Summary", "Relationships", "Study", "Sequence", "Links"]
                    for target in ("summary", "relationships", "study", "sequence", "links"):
                        assert nav.locator(
                            f'[data-raya-graph-detail-nav-target="{target}"]'
                        ).is_enabled()

                    before_url = page.url
                    nav.locator('[data-raya-graph-detail-nav-target="relationships"]').click()
                    page.wait_for_function(
                        "() => document.activeElement?.matches('[data-raya-graph-detail-jump-target=\"relationships\"]')"
                    )
                    assert page.url == before_url
                    assert page.locator(
                        '[data-raya-graph-detail-jump-target="relationships"]'
                    ).is_visible()
                    assert page.evaluate("() => localStorage.length") == 0
                    assert page.evaluate("() => sessionStorage.length") == 0
                    assert requests == []

                    page.click('[data-raya-graph-toggle-panel="inspector"]')
                    assert (
                        page.locator("[data-raya-graph-page]").get_attribute(
                            "data-raya-graph-inspector-state"
                        )
                        == "collapsed"
                    )
                    assert (
                        nav.locator('[data-raya-graph-detail-nav-target="relationships"]')
                        .get_attribute("tabindex")
                        == "-1"
                    )
                    page.click('[data-raya-graph-toggle-panel="inspector"]')
                    assert (
                        nav.locator('[data-raya-graph-detail-nav-target="relationships"]')
                        .get_attribute("tabindex")
                        is None
                    )
                    assert detail_panel.is_visible()
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_graph_detail_navigator_jumps_without_state_or_storage -q
```

Expected: FAIL because the nav buttons do not yet update enabled state or jump/focus.

- [ ] **Step 3: Wire graph script controls**

In `packages/static/src/raya_static/graph.py`, add constants near the existing detail selectors:

```javascript
  const detailNav = document.querySelector("[data-raya-graph-detail-nav]");
  const detailNavButtons = Array.from(
    document.querySelectorAll("[data-raya-graph-detail-nav-target]")
  );
```

Add helper functions before `renderDetail()`:

```javascript
  function visibleDetailTarget(selector) {
    const element = document.querySelector(selector);
    if (!element || element.hidden) return null;
    return element;
  }

  function detailJumpTarget(target) {
    if (target === "relationships") {
      return visibleDetailTarget("[data-raya-graph-detail-relationship-overview]") ||
        visibleDetailTarget("[data-raya-graph-detail-relationship-chips]") ||
        visibleDetailTarget("[data-raya-graph-relationship-walkthrough]") ||
        visibleDetailTarget("[data-raya-graph-detail-neighborhood]");
    }
    if (target === "study") {
      return visibleDetailTarget("[data-raya-graph-detail-sections]") ||
        visibleDetailTarget("[data-raya-graph-detail-study-objects]") ||
        visibleDetailTarget("[data-raya-graph-detail-key-objects]");
    }
    if (target === "sequence") {
      return visibleDetailTarget("[data-raya-graph-detail-reading-path]");
    }
    if (target === "links") {
      return visibleDetailTarget(".raya-graph-detail-links");
    }
    return detailPanel;
  }

  function syncDetailNavigator() {
    if (!detailNav) return;
    const hasSelection = Boolean(selectedId && detailPanel && !detailPanel.hidden);
    detailNav.hidden = !hasSelection;
    detailNavButtons.forEach((button) => {
      const target = button.getAttribute("data-raya-graph-detail-nav-target") || "";
      const enabled = hasSelection && Boolean(detailJumpTarget(target));
      button.disabled = !enabled;
      button.setAttribute("aria-disabled", enabled ? "false" : "true");
    });
  }

  function jumpToDetailTarget(target) {
    const destination = detailJumpTarget(target);
    if (!destination) return;
    destination.setAttribute("data-raya-graph-detail-jump-target", target);
    if (!destination.hasAttribute("tabindex")) {
      destination.setAttribute("tabindex", "-1");
      destination.setAttribute("data-raya-graph-nav-temp-tabindex", "true");
    }
    destination.scrollIntoView({ block: "nearest", inline: "nearest" });
    destination.focus({ preventScroll: true });
  }
```

Call `syncDetailNavigator();` in both branches of `renderDetail()` after visible/hidden section updates. Add click listeners near other startup listeners:

```javascript
  detailNavButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (button.disabled) return;
      jumpToDetailTarget(button.getAttribute("data-raya-graph-detail-nav-target") || "summary");
    });
  });
```

- [ ] **Step 4: Add styles**

In `packages/static/src/raya_static/rendering.py`, near `.raya-graph-detail-header`, add:

```css
.raya-graph-detail-nav {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0.65rem 0 0.8rem;
}
.raya-graph-detail-nav-button {
  border-radius: 999px !important;
  font-size: 0.82rem !important;
  font-weight: 800;
  min-height: 1.9rem !important;
  padding: 0.25rem 0.6rem !important;
}
.raya-graph-detail-nav-button:disabled {
  color: var(--raya-color-muted);
  cursor: default;
  opacity: 0.56;
}
.raya-graph-detail-nav-button:focus-visible,
[data-raya-graph-detail-jump-target]:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
```

- [ ] **Step 5: Run behavior test to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_graph_detail_navigator_jumps_without_state_or_storage -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/e2e/test_preview_static_read_path.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py
git commit -m "Add graph detail navigator behavior"
```

## Task 3: Review and Verification

**Files:**
- No production edits expected unless review finds an issue.

- [ ] **Step 1: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py::test_graph_workspace_renders_selected_detail_navigator \
  tests/e2e/test_preview_static_read_path.py::test_graph_detail_navigator_jumps_without_state_or_storage \
  tests/e2e/test_preview_static_read_path.py::test_preview_static_graph_page_is_local_and_interactive \
  -q
./scripts/check-render-debug.sh
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 2: Request code review**

Use `superpowers:requesting-code-review` for the implementation range. Ask the reviewer to check:

- graph detail navigator matches the spec;
- inspector collapse still protects focus order;
- no storage, fetch, external renderer, or graph data contract change;
- no accessibility regressions.

- [ ] **Step 3: Fix review feedback with TDD if behavior changes**

For Critical or Important review issues, add or tighten a failing test first,
verify RED, implement the fix, then verify GREEN. Commit the review fix.

- [ ] **Step 4: Push and preview**

Run:

```bash
git status --short --branch
git push origin new_rayalucaria
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --port 0
```

Expected: branch is clean and synced after push, preview prints an entrypoint URL.

## Self-Review

- Spec coverage: tasks cover static markup, native buttons, visibility, local jump/focus, disabled state, collapse focus behavior, no storage/fetch, review, and preview.
- Placeholder scan: no unfinished implementation placeholders remain.
- Type consistency: every selector uses `data-raya-graph-detail-nav*` and `data-raya-graph-detail-jump-target` consistently.
