# Discovery Workspace Course Rail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a shared static course-orientation rail to generated Search, Graph, Practice, Tasks, and Schedule workspaces.

**Architecture:** Build the rail server-side from current public course/navigation/workspace data in `builder.py`, style it through existing render CSS tokens in `rendering.py`, and add only local volatile collapse behavior in `discovery.py`. Tests verify generated static HTML and browser behavior across all discovery workspaces.

**Tech Stack:** Python 3.10 static builder, generated HTML/CSS/vanilla JS, Playwright e2e tests, local `uv` verification.

---

## File Structure

- Modify `packages/static/src/raya_static/builder.py`: add shared discovery rail render helpers and insert the rail into generated Search/Graph/Practice/Tasks/Schedule pages.
- Modify `packages/static/src/raya_static/rendering.py`: add layout and collapse styles for `.raya-discovery-workspace-shell` and `.raya-discovery-course-rail`.
- Modify `packages/static/src/raya_static/discovery.py`: add local non-persistent course-rail collapse/accessibility behavior.
- Modify `tests/e2e/test_preview_static_read_path.py`: add one focused browser test for rail presence, current workspace, collapse, mobile flow, no overflow, and no storage/fetch.
- Modify `docs/superpowers/plans/2026-06-27-discovery-workspace-course-rail.md`: check off steps as they complete.

## Task 1: Failing Discovery Rail Browser Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing test**

Add a test near existing discovery workspace tests:

```python
def test_discovery_workspaces_render_static_course_rail_without_storage(
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
                    requested_urls: list[str] = []
                    page.on("request", lambda request: requested_urls.append(request.url))
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
                            assert not any(
                                url.startswith("http://") or url.startswith("https://")
                                for url in requested_urls
                                if not url.startswith(base_url)
                            )
                            rail = page.locator("[data-raya-discovery-course-rail]")
                            assert rail.is_visible()
                            current = rail.locator('[aria-current="page"]')
                            assert current.count() == 1
                            assert current.get_attribute("data-raya-workspace-link") == kind
                            assert label in current.inner_text()
                            assert rail.locator(".raya-discovery-course-page-link").count() >= 5
                            hrefs = rail.locator("a[href]").evaluate_all(
                                "links => links.map(link => link.getAttribute('href'))"
                            )
                            assert all(href and not href.startswith("/") for href in hrefs)
                            assert all("_official/" not in href for href in hrefs)
                            assert all("_drafts/" not in href for href in hrefs)
                            assert all("_partials/" not in href for href in hrefs)
                            assert page.evaluate("() => localStorage.length") == 0
                            assert page.evaluate("() => sessionStorage.length") == 0
                            if viewport["width"] >= 1000:
                                toggle = page.locator("[data-raya-discovery-toggle-rail]")
                                assert toggle.is_visible()
                                toggle.click()
                                page.wait_for_function(
                                    """() => document.querySelector('[data-raya-discovery-page]')
                                      ?.getAttribute('data-raya-discovery-rail-state') === 'collapsed'"""
                                )
                                assert rail.locator(
                                    "[data-raya-discovery-course-rail-body]"
                                ).get_attribute("aria-hidden") == "true"
                                assert rail.locator(".raya-discovery-course-tab").is_visible()
                                assert page.evaluate("() => localStorage.length") == 0
                                assert page.evaluate("() => sessionStorage.length") == 0
                                toggle.click()
                                page.wait_for_function(
                                    """() => document.querySelector('[data-raya-discovery-page]')
                                      ?.getAttribute('data-raya-discovery-rail-state') === 'expanded'"""
                                )
                                assert rail.locator(
                                    "[data-raya-discovery-course-rail-body]"
                                ).get_attribute("aria-hidden") == "false"
                            else:
                                assert page.locator(
                                    "[data-raya-discovery-toggle-rail]"
                                ).is_visible() is False
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_discovery_workspaces_render_static_course_rail_without_storage
```

Expected: FAIL because `[data-raya-discovery-course-rail]` does not exist.

## Task 2: Shared Static Rail Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add helper functions in `builder.py`**

Add helpers near `_render_discovery_command_bar`:

```python
def _discovery_workspace_entries(current_workspace: str) -> list[dict[str, str]]:
    entries = [
        ("search", "Search", "../search/index.html", "Course"),
        ("graph", "Graph", "../graph/index.html", "Graph"),
        ("practice", "Practice", "../practice/index.html", "Practice"),
        ("tasks", "Tasks", "../tasks/index.html", "Tasks"),
        ("schedule", "Schedule", "../schedule/index.html", "Schedule"),
    ]
    return [
        {"kind": kind, "label": label, "href": href, "badge": badge}
        for kind, label, href, badge in entries
    ]


def _render_discovery_course_rail(
    *,
    content_model: ContentModel,
    course_title: str,
    current_workspace: str,
    from_path: str,
) -> str:
    pages = content_model.pages[:18]
    page_links = "\n".join(
        (
            '<li>'
            f'<a class="raya-discovery-course-page-link" '
            f'href="{html.escape(_relative_href(from_path, page.output_path), quote=True)}">'
            f'<span>{html.escape(page.display_label or "")}</span>'
            f'<strong>{html.escape(page.title)}</strong>'
            "</a>"
            "</li>"
        )
        for page in pages
    )
    workspace_links = "\n".join(
        (
            f'<a class="raya-discovery-workspace-link" '
            f'data-raya-workspace-link="{html.escape(entry["kind"], quote=True)}" '
            f'href="{html.escape(_relative_href(from_path, entry["href"]), quote=True)}"'
            + (' aria-current="page"' if current_workspace == entry["kind"] else "")
            + ">"
            f'<span>{html.escape(entry["label"])}</span>'
            f'<em>{html.escape(entry["badge"])}</em>'
            "</a>"
        )
        for entry in _discovery_workspace_entries(current_workspace)
    )
    return "\n".join(
        [
            '<aside class="raya-discovery-course-rail" data-raya-discovery-course-rail aria-label="Course workspace">',
            '<button class="raya-discovery-course-tab" type="button" data-raya-discovery-toggle-rail aria-controls="raya-discovery-course-rail-body" aria-expanded="true" aria-label="Collapse course workspace">Course</button>',
            '<div id="raya-discovery-course-rail-body" class="raya-discovery-course-rail-body" data-raya-discovery-course-rail-body aria-hidden="false">',
            '<div class="raya-discovery-course-identity">',
            f"<h2>{html.escape(course_title)}</h2>",
            f'<a href="{html.escape(_relative_href(from_path, "index.html"), quote=True)}">Back to course</a>',
            "</div>",
            '<nav class="raya-discovery-workspace-links" aria-label="Discovery workspaces">',
            workspace_links,
            "</nav>",
            '<nav class="raya-discovery-course-pages" aria-label="Course pages">',
            "<h3>Course pages</h3>",
            f"<ol>{page_links}</ol>",
            "</nav>",
            "</div>",
            "</aside>",
        ]
    )
```

- [ ] **Step 2: Insert the rail into every discovery workspace**

Wrap existing workspace sections with a shell:

```python
'<section class="raya-discovery-workspace-shell" aria-label="Course discovery workspace">',
_render_discovery_course_rail(
    content_model=content_model,
    course_title=course_title,
    current_workspace="search",
    from_path=STATIC_SEARCH_PATH.as_posix(),
),
'<section class="raya-search-workspace" aria-label="Search workspace">',
...
"</section>",
"</section>",
```

Repeat with `current_workspace` and `from_path` for Graph, Practice, Tasks, and
Schedule.

- [ ] **Step 3: Run the focused test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_discovery_workspaces_render_static_course_rail_without_storage
```

Expected: still FAIL until CSS/JS collapse behavior exists.

## Task 3: CSS Layout

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add styles near discovery workspace CSS**

Add CSS for:

```css
.raya-discovery-workspace-shell {
  align-items: start;
  display: grid;
  gap: 0.75rem;
  grid-template-columns: minmax(13rem, 16rem) minmax(0, 1fr);
}
.raya-discovery-course-rail {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  min-width: 0;
  padding: 0.75rem;
  position: sticky;
  top: calc(var(--raya-topbar-height, 4rem) + 1rem);
}
.raya-discovery-course-tab {
  display: none;
}
[data-raya-discovery-rail-state="collapsed"] .raya-discovery-workspace-shell {
  grid-template-columns: minmax(4.5rem, 5.25rem) minmax(0, 1fr);
}
[data-raya-discovery-rail-state="collapsed"] .raya-discovery-course-rail-body {
  display: none;
}
[data-raya-discovery-rail-state="collapsed"] .raya-discovery-course-tab {
  display: inline-flex;
  writing-mode: vertical-rl;
}
@media (max-width: 999px) {
  .raya-discovery-workspace-shell {
    grid-template-columns: minmax(0, 1fr);
  }
  .raya-discovery-course-rail {
    position: static;
  }
  .raya-discovery-course-tab {
    display: none;
  }
}
```

Include final polished rules for workspace links, page links, active states,
focus-visible outlines, no overflow, and compact mobile spacing.

- [ ] **Step 2: Run the focused test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_discovery_workspaces_render_static_course_rail_without_storage
```

Expected: FAIL only on collapse/accessibility behavior until JS is added.

## Task 4: Volatile Rail Collapse JavaScript

**Files:**
- Modify: `packages/static/src/raya_static/discovery.py`

- [ ] **Step 1: Extend `discovery.js`**

Inside the existing `roots.forEach`, add local rail setup:

```javascript
const railBody = root.querySelector("[data-raya-discovery-course-rail-body]");
const railToggle = root.querySelector("[data-raya-discovery-toggle-rail]");
function setRailExpanded(expanded) {
  root.setAttribute("data-raya-discovery-rail-state", expanded ? "expanded" : "collapsed");
  if (railBody) {
    railBody.setAttribute("aria-hidden", expanded ? "false" : "true");
    setPanelFocusable(railBody, expanded);
  }
  if (railToggle) {
    railToggle.setAttribute("aria-expanded", expanded ? "true" : "false");
    railToggle.setAttribute(
      "aria-label",
      expanded ? "Collapse course workspace" : "Expand course workspace"
    );
  }
}
if (railBody && railToggle) {
  setRailExpanded(true);
  railToggle.addEventListener("click", () => {
    setRailExpanded(root.getAttribute("data-raya-discovery-rail-state") === "collapsed");
  });
}
```

Do not add `localStorage`, `sessionStorage`, URL mutation, fetch, XHR, or
external scripts.

- [ ] **Step 2: Run the focused test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_discovery_workspaces_render_static_course_rail_without_storage
```

Expected: PASS.

## Task 5: Broader Verification and Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-27-discovery-workspace-course-rail.md`

- [ ] **Step 1: Run focused discovery tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_discovery_workspaces_render_static_course_rail_without_storage \
  tests/e2e/test_preview_static_read_path.py::test_discovery_workspace_guides_are_visible_without_overflow \
  tests/e2e/test_preview_static_read_path.py::test_discovery_command_bar_marks_current_workspace_without_overflow
```

Expected: all selected tests pass.

- [ ] **Step 2: Run render debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: `check-render-debug: passed`.

- [ ] **Step 3: Run diff hygiene**

Run:

```bash
git diff --check
```

Expected: no output, exit code 0.

- [ ] **Step 4: Commit**

Run:

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py packages/static/src/raya_static/discovery.py tests/e2e/test_preview_static_read_path.py docs/superpowers/plans/2026-06-27-discovery-workspace-course-rail.md
git commit -m "Add discovery workspace course rail"
```

Expected: commit succeeds.

- [ ] **Step 5: Request review**

Use `superpowers:requesting-code-review` with the design and plan as
requirements. Fix Critical and Important findings before pushing.
