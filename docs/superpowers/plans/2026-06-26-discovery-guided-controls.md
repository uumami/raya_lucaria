# Discovery Guided Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add static quick-guide cards to Search, Practice, Tasks, and Schedule discovery workspaces.

**Architecture:** Reuse the existing static builder pattern by adding one shared HTML helper in `packages/static/src/raya_static/builder.py`, then insert it into the four generated workspace pages. Add shared CSS in `packages/static/src/raya_static/rendering.py` and focused contract/browser tests around generated HTML and layout.

**Tech Stack:** Python 3.10, Glintstone static builder, pytest, Playwright, local static assets only.

---

### Task 1: Contract Tests For Generated Guides

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write failing helper assertions**

Add a helper near the existing discovery assertion helpers:

```python
def _assert_discovery_quick_guide(
    html: str,
    *,
    kind: str,
    labels: tuple[str, ...],
    snippets: tuple[str, ...],
) -> None:
    assert (
        f'<section class="raya-discovery-quick-guide" '
        f'data-raya-discovery-guide="{kind}" '
    ) in html
    assert "<h2>Quick guide</h2>" in html
    for label in labels:
        assert f"<h3>{label}</h3>" in html
    for snippet in snippets:
        assert snippet in html
    guide_match = re.search(
        rf'<section class="raya-discovery-quick-guide" '
        rf'data-raya-discovery-guide="{re.escape(kind)}" '
        r'.*?</section>',
        html,
        re.DOTALL,
    )
    assert guide_match is not None
    guide_text = guide_match.group(0).lower()
    for forbidden in (
        "progress",
        "mastery",
        "recommend",
        "personal",
        "ranking",
        "adaptive",
        "grade",
        "score",
        "submit",
    ):
        assert forbidden not in guide_text
```

- [ ] **Step 2: Add failing workspace assertions**

In the existing Search, Practice, Tasks, and Schedule builder tests, call:

```python
_assert_discovery_quick_guide(
    search_html,
    kind="search",
    labels=("Find", "Inspect", "Open", "Reset"),
    snippets=(
        "Type public page, section, tag, or stable-ID text.",
        "Pointer, focus, or keyboard movement updates the context panel.",
        "Use result links to open the page, graph, or matching workspaces.",
        "Clear or Escape returns to all visible public pages.",
    ),
)
```

```python
_assert_discovery_quick_guide(
    practice_html,
    kind="practice",
    labels=("Find", "Inspect", "Open", "Reset"),
    snippets=(
        "Search accepted official objects and filter by type.",
        "Select visible objects to read public metadata.",
        "Return to the owning page or graph focus.",
        "Clear or Escape shows accepted objects again.",
    ),
)
```

```python
_assert_discovery_quick_guide(
    tasks_html,
    kind="tasks",
    labels=("Find", "Sort", "Inspect", "Open"),
    snippets=(
        "Filter accepted task-family objects by text and type.",
        "Switch course order, authored due date, or type.",
        "Select visible tasks to read public planning fields.",
        "Return to the owning page or graph focus.",
    ),
)
```

```python
_assert_discovery_quick_guide(
    schedule_html,
    kind="schedule",
    labels=("Find", "Scan dates", "Inspect", "Open"),
    snippets=(
        "Filter dated official work by text, date kind, and type.",
        "Read authored due and available dates as course metadata.",
        "Select visible dated items to read public planning fields.",
        "Return to the owning page or graph focus.",
    ),
)
```

- [ ] **Step 3: Add failing CSS selector assertions**

In the Search test where `rich_css` is already loaded, assert:

```python
assert ".raya-discovery-quick-guide" in rich_css
assert ".raya-discovery-guide-card" in rich_css
```

- [ ] **Step 4: Run RED tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_build_writes_static_search_page \
  tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace \
  tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace \
  tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace \
  -q
```

Expected: failures because `raya-discovery-quick-guide` is not rendered yet.

### Task 2: Browser Layout Test For Guides

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing browser test**

Add a focused Playwright test:

```python
def test_discovery_workspace_guides_are_visible_without_overflow(
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
                        for workspace_path, kind in (
                            ("_raya/search/index.html", "search"),
                            ("_raya/practice/index.html", "practice"),
                            ("_raya/tasks/index.html", "tasks"),
                            ("_raya/schedule/index.html", "schedule"),
                        ):
                            page.goto(
                                f"{base_url}/{workspace_path}",
                                wait_until="networkidle",
                            )
                            _assert_no_horizontal_overflow(page)
                            guide = page.locator(
                                f'[data-raya-discovery-guide="{kind}"]'
                            )
                            assert guide.is_visible()
                            box = guide.bounding_box()
                            assert box is not None
                            assert box["x"] >= 0
                            assert box["x"] + box["width"] <= viewport["width"] + 1
                            assert guide.locator(".raya-discovery-guide-card").count() == 4
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
  tests/e2e/test_preview_static_read_path.py::test_discovery_workspace_guides_are_visible_without_overflow \
  -q
```

Expected: fail because guide elements are absent.

### Task 3: Shared Builder Helper And Workspace Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add shared helper**

Add near `_render_discovery_overview`:

```python
def _render_discovery_quick_guide(
    *,
    kind: str,
    cards: list[tuple[str, str]],
) -> str:
    card_html = "\n".join(
        [
            (
                '<article class="raya-discovery-guide-card">'
                f"<h3>{html.escape(label)}</h3>"
                f"<p>{html.escape(text)}</p>"
                "</article>"
            )
            for label, text in cards
        ]
    )
    return "\n".join(
        [
            (
                '<section class="raya-discovery-quick-guide" '
                f'data-raya-discovery-guide="{html.escape(kind, quote=True)}" '
                'aria-label="Workspace quick guide">'
            ),
            "<h2>Quick guide</h2>",
            '<div class="raya-discovery-guide-cards">',
            card_html,
            "</div>",
            "</section>",
        ]
    )
```

- [ ] **Step 2: Insert guide in Search**

After `_render_discovery_overview(...)` in `_render_search_surface`, insert:

```python
_render_discovery_quick_guide(
    kind="search",
    cards=[
        ("Find", "Type public page, section, tag, or stable-ID text."),
        (
            "Inspect",
            "Pointer, focus, or keyboard movement updates the context panel.",
        ),
        (
            "Open",
            "Use result links to open the page, graph, or matching workspaces.",
        ),
        ("Reset", "Clear or Escape returns to all visible public pages."),
    ],
),
```

- [ ] **Step 3: Insert guide in Practice**

After `_render_discovery_overview(...)` in `_render_practice_surface`, insert:

```python
_render_discovery_quick_guide(
    kind="practice",
    cards=[
        ("Find", "Search accepted official objects and filter by type."),
        ("Inspect", "Select visible objects to read public metadata."),
        ("Open", "Return to the owning page or graph focus."),
        ("Reset", "Clear or Escape shows accepted objects again."),
    ],
),
```

- [ ] **Step 4: Insert guide in Tasks**

After `_render_discovery_overview(...)` in `_render_tasks_surface`, insert:

```python
_render_discovery_quick_guide(
    kind="tasks",
    cards=[
        ("Find", "Filter accepted task-family objects by text and type."),
        ("Sort", "Switch course order, authored due date, or type."),
        ("Inspect", "Select visible tasks to read public planning fields."),
        ("Open", "Return to the owning page or graph focus."),
    ],
),
```

- [ ] **Step 5: Insert guide in Schedule**

After `_render_discovery_overview(...)` in `_render_schedule_surface`, insert:

```python
_render_discovery_quick_guide(
    kind="schedule",
    cards=[
        ("Find", "Filter dated official work by text, date kind, and type."),
        ("Scan dates", "Read authored due and available dates as course metadata."),
        ("Inspect", "Select visible dated items to read public planning fields."),
        ("Open", "Return to the owning page or graph focus."),
    ],
),
```

### Task 4: Shared Discovery Guide CSS

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add CSS near discovery overview styles**

Add:

```css
.raya-discovery-quick-guide {
  background: color-mix(in srgb, var(--raya-color-surface) 90%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 82%, var(--raya-color-accent));
  border-radius: 0.5rem;
  display: grid;
  gap: 0.65rem;
  margin: 0 0 var(--raya-space-block);
  padding: 0.75rem;
}
.raya-discovery-quick-guide h2 {
  font-size: 1rem;
  margin: 0;
}
.raya-discovery-guide-cards {
  display: grid;
  gap: 0.65rem;
  grid-template-columns: repeat(auto-fit, minmax(min(12rem, 100%), 1fr));
}
.raya-discovery-guide-card {
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-page));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 84%, transparent);
  border-radius: 0.45rem;
  display: grid;
  gap: 0.2rem;
  min-width: 0;
  padding: 0.65rem;
}
.raya-discovery-guide-card h3 {
  color: var(--raya-color-text);
  font-size: 0.9rem;
  margin: 0;
}
.raya-discovery-guide-card p {
  color: var(--raya-color-muted);
  font-size: 0.86rem;
  line-height: 1.35;
  margin: 0;
  overflow-wrap: anywhere;
}
```

### Task 5: Verify And Commit

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run focused contract tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_build_writes_static_search_page \
  tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace \
  tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace \
  tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace \
  -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run focused browser test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py::test_discovery_workspace_guides_are_visible_without_overflow \
  -q
```

Expected: test passes.

- [ ] **Step 3: Run render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: all render-debug checks pass.

- [ ] **Step 4: Check formatting whitespace**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 5: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-discovery-guided-controls-design.md \
  docs/superpowers/plans/2026-06-26-discovery-guided-controls.md \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py \
  packages/static/src/raya_static/builder.py \
  packages/static/src/raya_static/rendering.py
git commit -m "Add discovery guided controls"
git push origin new_rayalucaria
```
