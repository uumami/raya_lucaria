# Reader Location Breadcrumbs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace minimal article breadcrumbs with a polished static location strip that shows course home, ancestors, and current page.

**Architecture:** Update the existing `_render_breadcrumbs()` helper in `packages/static/src/raya_static/builder.py` to emit semantic classed markup from current `ContentModel` navigation data. Add responsive CSS in `packages/static/src/raya_static/rendering.py`, then cover the output with contract and browser static-read-path tests.

**Tech Stack:** Python static builder, generated HTML/CSS, pytest contract tests, Playwright-backed e2e tests.

---

### Task 1: Contract Test For Breadcrumb Markup

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Test: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add failing contract assertions**

Add a contract test that builds `examples/courses/minimal` and reads `artifact/site/unit/topic/index.html`:

```python
def test_build_renders_polished_reader_breadcrumbs(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "unit" / "topic" / "index.html").read_text(
        encoding="utf-8"
    )
    assert 'class="raya-breadcrumbs"' in html
    assert 'aria-label="Breadcrumbs"' in html
    assert 'class="raya-breadcrumbs-list"' in html
    assert 'class="raya-breadcrumb-home"' in html
    assert 'href="../../index.html"' in html
    assert 'class="raya-breadcrumb-link"' in html
    assert 'href="../index.html"' in html
    assert 'class="raya-breadcrumb-current"' in html
    assert 'aria-current="page"' in html
    assert 'class="raya-breadcrumb-separator" aria-hidden="true"' in html
    assert "course/" not in html
```

- [ ] **Step 2: Run test and confirm RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_renders_polished_reader_breadcrumbs
```

Expected: FAIL because current breadcrumbs have no `raya-breadcrumbs` classes, no home crumb, and no current-page crumb.

### Task 2: Browser Test For Navigation And No Overflow

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add failing e2e test**

Add a browser test using the minimal fixture preview:

```python
def test_preview_reader_breadcrumbs_are_static_location_links(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "minimal"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))
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
                    {"width": 1280, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    try:
                        requests: list[str] = []
                        page.on("request", lambda request: requests.append(request.url))
                        page.goto(
                            f"{base_url}/unit/topic/index.html",
                            wait_until="networkidle",
                        )
                        assert requests
                        assert all(url.startswith(f"{base_url}/") for url in requests)
                        _assert_no_horizontal_overflow(page)
                        breadcrumbs = page.locator(".raya-breadcrumbs")
                        assert breadcrumbs.is_visible()
                        assert breadcrumbs.locator(".raya-breadcrumb-current").get_attribute(
                            "aria-current"
                        ) == "page"
                        assert "Topic" in breadcrumbs.inner_text()
                        home_href = breadcrumbs.locator(".raya-breadcrumb-home").evaluate(
                            "node => node.href"
                        )
                        with page.expect_navigation():
                            breadcrumbs.locator(".raya-breadcrumb-home").click()
                        assert page.url == home_href
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run test and confirm RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_reader_breadcrumbs_are_static_location_links
```

Expected: FAIL because `.raya-breadcrumbs` does not exist.

### Task 3: Implement Breadcrumb HTML

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Test: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Replace `_render_breadcrumbs()` markup**

Change `_render_breadcrumbs()` to:

```python
def _render_breadcrumbs(page: ContentPage, content_model: ContentModel) -> str:
    breadcrumbs = _breadcrumb_pages(page, content_model)
    if not breadcrumbs:
        return ""
    crumbs: list[tuple[str, str | None, str]] = [
        ("Course home", _relative_href(page.output_path, content_model.pages[0].output_path), "raya-breadcrumb-home")
    ]
    crumbs.extend(
        (
            crumb.nav_title,
            _relative_href(page.output_path, crumb.output_path),
            "raya-breadcrumb-link",
        )
        for crumb in breadcrumbs
    )
    crumbs.append((page.nav_title, None, "raya-breadcrumb-current"))

    items = []
    for index, (label, href, class_name) in enumerate(crumbs):
        if index > 0:
            items.append(
                '<li class="raya-breadcrumb-separator" aria-hidden="true">›</li>'
            )
        escaped_label = html.escape(label)
        if href is None:
            items.append(
                '<li><span class="raya-breadcrumb-current" aria-current="page">'
                f"{escaped_label}</span></li>"
            )
        else:
            items.append(
                f'<li><a class="{class_name}" href="{html.escape(href)}">'
                f"{escaped_label}</a></li>"
            )
    return (
        '<nav class="raya-breadcrumbs" aria-label="Breadcrumbs">'
        '<ol class="raya-breadcrumbs-list">'
        + "".join(items)
        + "</ol></nav>"
    )
```

- [ ] **Step 2: Run contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_renders_polished_reader_breadcrumbs
```

Expected: PASS.

### Task 4: Add Responsive Breadcrumb Styling

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Replace generic breadcrumb CSS**

Replace the generic `nav[aria-label="Breadcrumbs"]` block with:

```css
.raya-breadcrumbs {
  color: var(--raya-color-muted);
  font-size: 0.875rem;
  margin-bottom: 0.85rem;
  max-width: 100%;
}
.raya-breadcrumbs-list {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  list-style: none;
  margin: 0;
  min-width: 0;
  padding: 0;
}
.raya-breadcrumbs li {
  min-width: 0;
}
.raya-breadcrumb-home,
.raya-breadcrumb-link,
.raya-breadcrumb-current {
  border-radius: 0.25rem;
  display: inline-block;
  max-width: min(18rem, 70vw);
  overflow: hidden;
  padding: 0.1rem 0.2rem;
  text-overflow: ellipsis;
  vertical-align: bottom;
  white-space: nowrap;
}
.raya-breadcrumb-home,
.raya-breadcrumb-link {
  color: var(--raya-color-link);
  font-weight: 700;
  text-decoration-thickness: 0.08em;
}
.raya-breadcrumb-home:hover,
.raya-breadcrumb-link:hover {
  color: var(--raya-color-success);
}
.raya-breadcrumb-current {
  color: var(--raya-color-text);
  font-weight: 800;
}
.raya-breadcrumb-separator {
  color: var(--raya-color-muted);
  font-weight: 800;
}
```

- [ ] **Step 2: Run browser test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_reader_breadcrumbs_are_static_location_links
```

Expected: PASS.

### Task 5: Foundation And Role Docs

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update renderer contract**

Add that article breadcrumbs are current static location cues with course-home, ancestor, and current-page crumbs, generated from navigation data and not progress.

- [ ] **Step 2: Update agent docs**

Mention breadcrumb checks when changing the shell: classed breadcrumb markup, home/ancestor/current semantics, deployment-neutral links, no source paths, and no overflow.

- [ ] **Step 3: Run docs grep**

Run:

```bash
rg -n "breadcrumb|Breadcrumb|miga|raya-breadcrumb" docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md
```

Expected: new guidance appears in the three files.

### Task 6: Review, Verify, Commit, Push

**Files:**
- Review all changed files.

- [ ] **Step 1: Run focused tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_renders_polished_reader_breadcrumbs
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_reader_breadcrumbs_are_static_location_links
```

- [ ] **Step 2: Run render-debug gate**

```bash
./scripts/check-render-debug.sh
```

- [ ] **Step 3: Request focused code review**

Use `superpowers:requesting-code-review` to review breadcrumb semantics, static boundary, accessibility, and tests.

- [ ] **Step 4: Run full gates**

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

- [ ] **Step 5: Commit and push**

```bash
git add docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/superpowers/plans/2026-06-24-reader-location-breadcrumbs.md
git commit -m "Polish reader location breadcrumbs"
git push origin new_rayalucaria
```

---

## Plan Self-Review

- Spec coverage: home crumb, ancestor links, current crumb, styling, docs, and tests are covered.
- Placeholder scan: no incomplete placeholders remain.
- Type consistency: class names match the design and test assertions.
