# Discovery Workspace Switcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the discovery command bar a stable workspace switcher with visible current-workspace state.

**Architecture:** Extend the existing command-link helper to accept optional attributes, extend `_render_discovery_command_bar` with `current_workspace`, and pass self-links from each generated discovery page. Style the active command in shared CSS and cover the behavior with focused contract and Playwright checks.

**Tech Stack:** Python 3.10, generated static HTML/CSS, pytest, Playwright/Chromium.

**Status: implemented.** This checklist is a historical execution record. Current
source support lives in `_render_discovery_command_bar`, active discovery command
CSS, contract tests, and browser no-overflow checks.

---

### Task 1: Contract Tests For Current Workspace State

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add helper assertions**

Add near the existing discovery helpers:

```python
def _assert_discovery_workspace_switcher(
    html: str,
    *,
    current: str,
) -> None:
    for label in ("Search", "Graph", "Practice", "Tasks", "Schedule"):
        assert f'<span class="raya-command-label">{label}</span>' in html
    assert html.count('aria-current="page"') == 1
    assert f'data-raya-current-workspace="{current}"' in html
    assert "https://" not in html
    assert "http://" not in html
```

- [ ] **Step 2: Assert switcher on generated pages**

In `test_build_writes_local_visual_graph_surface`, call:

```python
_assert_discovery_workspace_switcher(graph_html, current="graph")
```

In `test_build_writes_local_course_search_surface`, call:

```python
_assert_discovery_workspace_switcher(search_html, current="search")
```

In `test_build_writes_static_official_practice_workspace`, call:

```python
_assert_discovery_workspace_switcher(practice_html, current="practice")
```

In `test_build_writes_static_official_tasks_workspace`, call:

```python
_assert_discovery_workspace_switcher(tasks_html, current="tasks")
```

In `test_build_writes_static_schedule_workspace`, call:

```python
_assert_discovery_workspace_switcher(schedule_html, current="schedule")
```

- [ ] **Step 3: Assert active CSS exists**

Where `rich_css` is already loaded in the Search contract test, add:

```python
assert '.raya-discovery-command-bar .raya-command[aria-current="page"]' in rich_css
assert "data-raya-current-workspace" in search_html
```

- [ ] **Step 4: Run RED contract tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface \
  tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface \
  tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace \
  tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace \
  tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace \
  -q
```

Expected: failures because current workspace commands are not yet rendered.

### Task 2: Browser Test For Active Workspace Switcher

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add focused browser test**

Add:

```python
def test_discovery_command_bar_marks_current_workspace_without_overflow(
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
        base_url = handle.base_url
        assert base_url is not None

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for viewport in (
                    {"width": 1366, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    try:
                        for workspace_path, kind, label in (
                            ("_raya/search/index.html", "search", "Search"),
                            ("_raya/graph/index.html", "graph", "Graph"),
                            ("_raya/practice/index.html", "practice", "Practice"),
                            ("_raya/tasks/index.html", "tasks", "Tasks"),
                            ("_raya/schedule/index.html", "schedule", "Schedule"),
                        ):
                            page.goto(
                                f"{base_url}/{workspace_path}",
                                wait_until="networkidle",
                            )
                            _assert_no_horizontal_overflow(page)
                            current = page.locator(
                                '.raya-discovery-command-bar '
                                '.raya-command[aria-current="page"]'
                            )
                            assert current.count() == 1
                            assert (
                                current.get_attribute("data-raya-current-workspace")
                                == kind
                            )
                            assert label in current.inner_text()
                            box = current.bounding_box()
                            assert box is not None
                            assert box["width"] > 0
                            assert box["x"] >= 0
                            assert box["x"] + box["width"] <= viewport["width"] + 1
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run RED browser test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py::test_discovery_command_bar_marks_current_workspace_without_overflow \
  -q
```

Expected: fail because no command has `aria-current="page"`.

### Task 3: Static Builder Implementation

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Extend `_render_command_link`**

Change the signature to:

```python
def _render_command_link(
    *,
    class_name: str,
    href: str,
    aria_label: str,
    icon: str,
    label: str,
    extra_attrs: str = "",
) -> str:
```

Change the opening anchor to include `extra_attrs`:

```python
    return (
        f'<a class="{html.escape(class_name, quote=True)}" '
        f'href="{html.escape(href)}" '
        f'aria-label="{html.escape(aria_label, quote=True)}"{extra_attrs}>'
```

- [ ] **Step 2: Add a command helper inside `_render_discovery_command_bar`**

Add `current_workspace: str` to `_render_discovery_command_bar`. Inside it,
create:

```python
    def workspace_command(
        *,
        kind: str,
        href: str,
        aria_label: str,
        icon: str,
        label: str,
    ) -> str:
        extra_attrs = (
            f' aria-current="page" data-raya-current-workspace="{kind}"'
            if current_workspace == kind
            else ""
        )
        return _render_command_link(
            class_name=f"raya-command raya-command-{kind}",
            href=href,
            aria_label=aria_label,
            icon=icon,
            label=label,
            extra_attrs=extra_attrs,
        )
```

Use it for Search, Graph, Practice, Tasks, and Schedule.

- [ ] **Step 3: Pass self-links and current workspace values**

Update each call:

```python
current_workspace="graph"
graph_href="index.html"
```

```python
current_workspace="search"
search_href="index.html"
```

```python
current_workspace="practice"
practice_href="index.html"
```

```python
current_workspace="tasks"
tasks_href="index.html"
```

```python
current_workspace="schedule"
schedule_href="index.html"
```

Keep other workspace hrefs unchanged.

### Task 4: Active Workspace CSS

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add scoped active command style**

Add near the discovery command bar rules:

```css
.raya-discovery-command-bar .raya-command[aria-current="page"] {
  background: color-mix(in srgb, var(--raya-color-surface) 24%, var(--raya-color-accent));
  border-color: var(--raya-color-accent);
  box-shadow: inset 0 -0.18rem 0 var(--raya-color-accent);
  color: var(--raya-color-surface);
}
.raya-discovery-command-bar .raya-command[aria-current="page"] .raya-command-icon {
  color: inherit;
}
```

### Task 5: Verify, Review, Commit, Push

**Files:**
- Check all changed files.

- [ ] **Step 1: Run focused contract tests**

Run the command from Task 1 Step 4.

Expected: all selected tests pass.

- [ ] **Step 2: Run focused browser test**

Run the command from Task 2 Step 2.

Expected: test passes.

- [ ] **Step 3: Run render-debug regression gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: render-debug passes.

- [ ] **Step 4: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 5: Request independent review**

Ask reviewers to check:

- static renderer contract compliance;
- UX/accessibility of `aria-current` and active styling;
- test coverage and brittleness.

- [ ] **Step 6: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-discovery-workspace-switcher-design.md \
  docs/superpowers/plans/2026-06-26-discovery-workspace-switcher.md \
  packages/static/src/raya_static/builder.py \
  packages/static/src/raya_static/rendering.py \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Mark current discovery workspace"
git push origin new_rayalucaria
```
