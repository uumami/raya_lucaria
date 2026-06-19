# Collapsible Learning Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Supersession note, current as of the balanced learning workspace update:**
> this historical plan's collapsed-by-default and course-map `localStorage`
> decisions are superseded. Current behavior is expanded by default,
> non-persistent, and collapsible by explicit click to a compact map rail. Do
> not implement `raya.courseMapExpanded` or persisted course-map state from this
> plan.

**Goal:** Build a click-only collapsible course shell that gives rendered Raya pages more reading space, stronger static page tracking, and verified desktop/mobile behavior.

**Architecture:** Keep the current semantic shell order in `builder.py`: top command bar, course map, article, learning rail. Add a small local shell resource beside the existing rich CSS, skin CSS, MathJax CSS, and OpenDyslexic assets; use document data attributes and CSS grid states for collapsed/expanded layout instead of changing DOM order. Extend existing contract/e2e/render-debug tests so static preview, copied site output, and browser inspection all verify the same shell behavior.

**Tech Stack:** Python 3.10, `uv`, pytest, Playwright/Chromium, static HTML/CSS/JS, Raya Glintstone packages, build-time MathJax, local renderer resources only.

---

## Source Design

Implement against [2026-06-18-collapsible-learning-shell-design.md](/home/uumami/itam/raya_lucaria/docs/superpowers/specs/2026-06-18-collapsible-learning-shell-design.md).

Do not create OpenSpec artifacts in this loop unless the user explicitly switches workflow. The implementation must update affected foundation docs, English and Spanish role docs, tests, render-debug checks, and fixture evidence.

## File Map

Renderer:

- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Create: `packages/static/src/raya_static/shell.py`

Render-debug:

- Modify: `packages/cli/src/raya_cli/render_debug.py`
- Modify: `packages/cli/src/raya_cli/render_debug_report.py`

Tests:

- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/contracts/test_renderer_dependencies.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `tests/e2e/test_render_debug_report.py`
- Modify: `tests/e2e/test_render_debug_parity_gate.py`

Docs and fixture:

- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Modify: `examples/courses/render-fixture/course/4_reader_ux/0_index.md`

Verification:

- Run focused contract/e2e tests during tasks.
- Run `./scripts/check-render-debug.sh`.
- Run `./scripts/check.sh`.
- Run `./scripts/check-docker.sh` after local gates pass.

## Implementation Notes

- The current branch already has a semantic shell with `nav.raya-course-map`, `article#raya-article.raya-main-article`, and `aside.raya-learning-rail`.
- Preserve DOM order as `nav -> article -> aside`; desktop visual order may change only through CSS.
- Superseded: this historical plan originally defaulted the shell to collapsed.
  Current shell state is expanded on desktop and mobile when JavaScript runs.
- No hover expansion. CSS may style hover/focus for the button, but hover must not open the map.
- Superseded: the JavaScript must not use `localStorage` for course-map state
  and must not use the historical `raya.courseMapExpanded` key.
- Do not fetch JSON or external resources from the shell script.
- If JavaScript is disabled, the static course map remains visible and usable.
  JavaScript preserves the expanded default until an explicit click collapses
  the map to the compact rail.
- Page-position wording must be structural: use `Page N of M`. Never use completion, progress percent, mastered, score, or finished.
- Active section tracking uses existing heading anchors and links in the generated page contents. It is a reader aid, not personal progress.

---

### Task 1: Local Shell Resource Plumbing

**Files:**
- Create: `packages/static/src/raya_static/shell.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write failing contract test for shell resource output**

Add this test near the existing OpenDyslexic resource tests in `tests/contracts/test_static_builder.py`:

```python
def test_static_build_writes_local_shell_resource(tmp_path: Path) -> None:
    from raya_static.builder import build_course

    course = _minimal_course(tmp_path)
    report = build_course(course)
    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]

    site = course / "artifact" / "site"
    shell_js = site / "_raya" / "render" / "shell.js"
    index_html = (site / "index.html").read_text(encoding="utf-8")
    script_text = shell_js.read_text(encoding="utf-8")

    assert shell_js.exists()
    assert '<script src="_raya/render/shell.js" defer></script>' in index_html
    assert "raya.courseMapExpanded" not in script_text
    assert "localStorage" not in script_text
    assert "setExpanded(true)" in script_text
    assert "fetch(" not in script_text
    assert "XMLHttpRequest" not in script_text
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource -q
```

Expected: fail because `_raya/render/shell.js` is not generated or linked yet.

- [ ] **Step 3: Add shell resource module**

Create `packages/static/src/raya_static/shell.py`. Historical note: the
original sample below used persisted course-map state; that storage behavior is
superseded. Implement the current non-persistent expanded default instead:

```python
from __future__ import annotations

from dataclasses import dataclass


SHELL_SCRIPT_NAME = "shell.js"
SHELL_RESOURCE_PATH = "_raya/render"


@dataclass(frozen=True)
class ShellResources:
    javascript: str


def shell_resources() -> ShellResources:
    return ShellResources(javascript=_SHELL_JAVASCRIPT)


_SHELL_JAVASCRIPT = r"""
(() => {
  const root = document.documentElement;
  const shell = document.querySelector(".raya-learning-shell");
  const map = document.querySelector("#raya-course-map");
  const toggleButtons = Array.from(document.querySelectorAll("[data-raya-course-map-toggle]"));
  const tocLinks = Array.from(document.querySelectorAll(".raya-page-toc a[href^='#']"));
  const headings = tocLinks
    .map((link) => {
      const target = document.querySelector(link.getAttribute("href"));
      return target ? { link, target } : null;
    })
    .filter(Boolean);

  if (!shell || !map || toggleButtons.length === 0) {
    return;
  }

  function setExpanded(nextExpanded) {
    root.dataset.rayaCourseMap = nextExpanded ? "expanded" : "collapsed";
    shell.dataset.rayaCourseMap = nextExpanded ? "expanded" : "collapsed";
    map.dataset.rayaCourseMap = nextExpanded ? "expanded" : "collapsed";
    toggleButtons.forEach((button) => {
      button.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
    });
  }

  toggleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setExpanded(root.dataset.rayaCourseMap !== "expanded");
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && root.dataset.rayaCourseMap === "expanded") {
      setExpanded(false);
    }
  });

  if ("IntersectionObserver" in window && headings.length > 0) {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((left, right) => left.boundingClientRect.top - right.boundingClientRect.top)[0];
        if (!visible) {
          return;
        }
        tocLinks.forEach((link) => link.removeAttribute("aria-current"));
        const active = headings.find((item) => item.target === visible.target);
        if (active) {
          active.link.setAttribute("aria-current", "location");
        }
      },
      { rootMargin: "-20% 0px -65% 0px", threshold: [0, 1] }
    );
    headings.forEach((item) => observer.observe(item.target));
  }

  setExpanded(true);
})();
"""
```

- [ ] **Step 4: Write shell resource during build**

In `packages/static/src/raya_static/builder.py`, import the module:

```python
from raya_static.shell import SHELL_RESOURCE_PATH, SHELL_SCRIPT_NAME, shell_resources
```

Add this helper near `_write_rich_render_resources`:

```python
def _write_shell_resources(site_dir: Path, report: ValidationReport) -> None:
    resources = shell_resources()
    shell_dir = site_dir / SHELL_RESOURCE_PATH
    shell_dir.mkdir(parents=True, exist_ok=True)
    report.wrote_output(shell_dir)
    script_path = shell_dir / SHELL_SCRIPT_NAME
    script_path.write_text(resources.javascript, encoding="utf-8")
    report.wrote_output(script_path)
```

Call it in `build_course()` immediately after `_write_rich_render_resources(...)`:

```python
    _write_rich_render_resources(site_dir, report, skin_context=skin_context)
    _write_shell_resources(site_dir, report)
```

In `_render_page()`, add the shell script tag after the existing OpenDyslexic script tag:

```python
            f'<script src="{html.escape(shell_js_href)}" defer></script>',
```

Compute `shell_js_href` beside the existing resource hrefs:

```python
    shell_js_href = _relative_href(
        page.output_path,
        Path(SHELL_RESOURCE_PATH) / SHELL_SCRIPT_NAME,
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource -q
```

Expected: pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add packages/static/src/raya_static/shell.py packages/static/src/raya_static/builder.py tests/contracts/test_static_builder.py
git commit -m "Add local learning shell resource"
```

---

### Task 2: Shell Markup And Structural Page Tracking

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write failing contract test for shell controls and page position**

Add this test near `test_static_builder_renders_learning_shell_regions()` in `tests/contracts/test_static_builder.py`:

```python
def test_static_builder_renders_collapsible_shell_controls_and_page_position(tmp_path: Path) -> None:
    from raya_static.builder import build_course

    course = _minimal_course(tmp_path)
    report = build_course(course)
    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]

    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")

    assert '<nav id="raya-course-map" class="raya-course-map"' in html
    assert '<button class="raya-course-map-toggle"' in html
    assert 'data-raya-course-map-toggle' in html
    assert 'aria-controls="raya-course-map"' in html
    assert 'aria-expanded="false"' in html
    assert '<p class="raya-page-position">Page 1 of 3</p>' in html
    assert '<nav class="raya-article-sequence raya-article-sequence-top"' in html
    assert 'aria-label="Previous and next pages"' in html
    assert html.index('<nav id="raya-course-map"') < html.index('<article id="raya-article"') < html.index('<aside class="raya-learning-rail"')
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position -q
```

Expected: fail because the course map has no stable ID, no toggle, no page position, and no top article sequence nav.

- [ ] **Step 3: Add page position and shell control helpers**

In `packages/static/src/raya_static/builder.py`, add helpers near `_render_top_command_bar`:

```python
def _page_position(page: ContentPage, content_model: ContentModel) -> str:
    for index, target in enumerate(content_model.pages, start=1):
        if target.id == page.id:
            return f"Page {index} of {len(content_model.pages)}"
    return ""


def _render_course_map_toggle(label: str = "Course map") -> str:
    return (
        '<button class="raya-course-map-toggle" type="button" '
        'data-raya-course-map-toggle '
        'aria-controls="raya-course-map" '
        'aria-expanded="false">'
        f"{html.escape(label)}"
        "</button>"
    )
```

Change `_render_top_command_bar(course_title: str)` to include the toggle before the OpenDyslexic button:

```python
            '<div class="raya-course-tools">',
            _render_course_map_toggle("Course map"),
            (
                '<button class="raya-font-toggle" type="button" '
                'aria-label="Toggle OpenDyslexic font" '
                'aria-pressed="false">OpenDyslexic</button>'
            ),
```

Change `_render_course_map(...)` so the nav has a stable ID and a compact header:

```python
def _render_course_map(page: ContentPage, content_model: ContentModel) -> str:
    nav_items = []
    for target in content_model.pages:
        href = _relative_href(page.output_path, target.output_path)
        label = html.escape(_navigation_label(target))
        current = ' aria-current="page"' if target.output_path == page.output_path else ""
        nav_items.append(f'<a href="{html.escape(href)}"{current}>{label}</a>')
    position = html.escape(_page_position(page, content_model))
    return "\n".join(
        [
            '<nav id="raya-course-map" class="raya-course-map" aria-label="Course map" data-raya-course-map="expanded">',
            '<div class="raya-course-map-header">',
            '<p class="raya-region-title">Course map</p>',
            f'<p class="raya-page-position">{position}</p>' if position else "",
            _render_course_map_toggle("Toggle map"),
            "</div>",
            '<div class="raya-course-map-list" id="raya-course-map-list">',
            "\n".join(nav_items),
            "</div>",
            "</nav>",
        ]
    )
```

Add a top article sequence helper:

```python
def _render_article_sequence_nav(page: ContentPage, content_model: ContentModel) -> str:
    sequence = _sequence_links(page, content_model)
    if not sequence:
        return ""
    return (
        '<nav class="raya-article-sequence raya-article-sequence-top" '
        'aria-label="Previous and next pages">'
        + sequence
        + "</nav>"
    )
```

If `_sequence_links` does not exist yet, extract the link-building portion from `_render_sequence_nav()` into:

```python
def _sequence_links(page: ContentPage, content_model: ContentModel) -> str:
    pages = content_model.pages
    current_index = next(
        (index for index, target in enumerate(pages) if target.output_path == page.output_path),
        None,
    )
    if current_index is None:
        return ""
    links = []
    if current_index > 0:
        previous = pages[current_index - 1]
        href = _relative_href(page.output_path, previous.output_path)
        links.append(f'<a href="{html.escape(href)}">Previous: {html.escape(previous.nav_title or previous.title)}</a>')
    if current_index + 1 < len(pages):
        next_page = pages[current_index + 1]
        href = _relative_href(page.output_path, next_page.output_path)
        links.append(f'<a href="{html.escape(href)}">Next: {html.escape(next_page.nav_title or next_page.title)}</a>')
    return "\n".join(links)
```

Use `_sequence_links()` from the existing `_render_sequence_nav()` so top and rail sequence links cannot drift.

In `_render_page()`, insert article sequence before `breadcrumbs`:

```python
            _render_article_sequence_nav(page, content_model),
            breadcrumbs,
            article_html,
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position -q
```

Expected: pass.

- [ ] **Step 5: Run existing static builder shell tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
```

Expected: pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add packages/static/src/raya_static/builder.py tests/contracts/test_static_builder.py
git commit -m "Render collapsible shell controls"
```

---

### Task 3: Desktop Collapsed Layout And Click Behavior

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing browser test for desktop default and toggle behavior**

Add this test after `test_render_fixture_learning_shell_layout_and_accessibility()` in `tests/e2e/test_preview_static_read_path.py`:

```python
def test_render_fixture_course_map_collapses_and_expands_on_click_only(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        assert handle.base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 950})
                try:
                    page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                    _assert_no_horizontal_overflow(page)
                    collapsed = page.evaluate(
                        """() => ({
                          state: document.documentElement.dataset.rayaCourseMap,
                          expanded: document.querySelector('.raya-course-map-toggle')?.getAttribute('aria-expanded'),
                          mapWidth: document.querySelector('#raya-course-map')?.getBoundingClientRect().width,
                          articleWidth: document.querySelector('#raya-article')?.getBoundingClientRect().width,
                        })"""
                    )
                    assert collapsed["state"] == "collapsed"
                    assert collapsed["expanded"] == "false"
                    assert collapsed["mapWidth"] < 130
                    assert collapsed["articleWidth"] > 760

                    page.hover("#raya-course-map")
                    after_hover = page.evaluate("() => document.documentElement.dataset.rayaCourseMap")
                    assert after_hover == "collapsed"

                    page.click(".raya-course-map-toggle")
                    expanded = page.evaluate(
                        """() => ({
                          state: document.documentElement.dataset.rayaCourseMap,
                          expanded: document.querySelector('.raya-course-map-toggle')?.getAttribute('aria-expanded'),
                          mapWidth: document.querySelector('#raya-course-map')?.getBoundingClientRect().width,
                        })"""
                    )
                    assert expanded["state"] == "expanded"
                    assert expanded["expanded"] == "true"
                    assert expanded["mapWidth"] > 220

                    page.keyboard.press("Escape")
                    assert page.evaluate("() => document.documentElement.dataset.rayaCourseMap") == "collapsed"
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_collapses_and_expands_on_click_only -q
```

Expected: fail because CSS does not collapse the map yet.

- [ ] **Step 3: Add collapsed/expanded CSS states**

In `packages/static/src/raya_static/rendering.py`, update the shell CSS around `.raya-learning-shell`:

```css
.raya-learning-shell {
  display: grid;
  gap: calc(var(--raya-space-block) * 1.1);
  grid-template-areas: "course-map main-article learning-rail";
  grid-template-columns: minmax(4.5rem, 5.5rem) minmax(44rem, 1fr) minmax(15rem, 20rem);
}
[data-raya-course-map="expanded"] .raya-learning-shell,
.raya-learning-shell[data-raya-course-map="expanded"] {
  grid-template-columns: minmax(16rem, 20rem) minmax(38rem, 1fr) minmax(14rem, 18rem);
}
.raya-course-map {
  grid-area: course-map;
  overflow: hidden;
}
.raya-course-map-header {
  display: grid;
  gap: 0.5rem;
}
.raya-course-map-list {
  display: grid;
  gap: 0.15rem;
}
[data-raya-course-map="collapsed"] .raya-course-map-list,
.raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-list {
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  height: 1px;
  overflow: hidden;
  position: absolute;
  white-space: nowrap;
  width: 1px;
}
.raya-course-map-toggle {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  cursor: pointer;
  font: inherit;
  font-weight: 700;
  padding: 0.45rem 0.65rem;
}
.raya-course-map-toggle:focus-visible {
  outline: 3px solid var(--raya-color-focus);
  outline-offset: 2px;
}
.raya-article-sequence {
  border-bottom: 1px solid var(--raya-color-border);
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: space-between;
  margin: 0 0 1rem;
  padding: 0 0 0.75rem;
}
```

Keep existing region rules for `.raya-main-article` and `.raya-learning-rail`. Adjust the existing `@media (max-width: 900px)` in Task 4 instead of mixing mobile behavior here.

- [ ] **Step 4: Run desktop behavior test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_collapses_and_expands_on_click_only -q
```

Expected: pass.

- [ ] **Step 5: Run focused existing layout tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_static_read_path_uses_local_resources tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_shell_layout_and_accessibility -q
```

Expected: pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git commit -m "Collapse course map on desktop"
```

---

### Task 4: Mobile Reading Priority And Active Heading Tracking

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing browser test for mobile article priority and active heading**

Add this test after the desktop collapse test:

```python
def test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        assert handle.base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 390, "height": 844})
                try:
                    page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                    _assert_no_horizontal_overflow(page)
                    article = _bounding_box(page, "article.raya-main-article")
                    course_map = _bounding_box(page, "nav.raya-course-map")
                    rail = _bounding_box(page, "aside.raya-learning-rail")
                    assert article["y"] < course_map["y"] < rail["y"]
                    assert page.locator(".raya-course-map-toggle").first.get_attribute("aria-expanded") == "false"

                    page.click(".raya-course-map-toggle")
                    assert page.locator(".raya-course-map-toggle").first.get_attribute("aria-expanded") == "true"
                    _assert_no_horizontal_overflow(page)

                    page.locator("#worked-example").scroll_into_view_if_needed()
                    page.wait_for_timeout(250)
                    active = page.evaluate(
                        """() => document.querySelector('.raya-page-toc a[aria-current="location"]')?.getAttribute('href')"""
                    )
                    assert active == "#worked-example"
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Add stable heading to fixture if missing**

In `examples/courses/render-fixture/course/4_reader_ux/0_index.md`, ensure there is a second-level heading:

```markdown
## Worked Example
```

The generated heading ID should be `worked-example`.

- [ ] **Step 3: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
```

Expected: fail because mobile currently places course map before article and active heading tracking is not verified.

- [ ] **Step 4: Update mobile CSS**

In `packages/static/src/raya_static/rendering.py`, replace the current `@media (max-width: 900px)` shell ordering with:

```css
@media (max-width: 900px) {
  .raya-learning-shell {
    grid-template-areas:
      "main-article"
      "course-map"
      "learning-rail";
    grid-template-columns: minmax(0, 1fr);
  }
  .raya-course-map,
  .raya-learning-rail {
    margin-bottom: 1rem;
    max-height: 16rem;
    overflow: auto;
    position: static;
  }
  [data-raya-course-map="collapsed"] .raya-course-map {
    max-height: 5.5rem;
  }
  [data-raya-course-map="expanded"] .raya-course-map {
    max-height: 70vh;
  }
  .raya-learning-rail {
    margin-top: 1rem;
  }
}
.raya-page-toc a[aria-current="location"] {
  color: var(--raya-color-success);
  font-weight: 700;
}
```

- [ ] **Step 5: Verify shell script active-heading selector**

In `packages/static/src/raya_static/shell.py`, confirm `_SHELL_JAVASCRIPT` selects `.raya-page-toc a[href^='#']` and writes `aria-current="location"` on the active link. If the selector differs from Task 1, change it to:

```javascript
const tocLinks = Array.from(document.querySelectorAll(".raya-page-toc a[href^='#']"));
```

- [ ] **Step 6: Run mobile behavior test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
```

Expected: pass.

- [ ] **Step 7: Run combined browser layout tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_shell_layout_and_accessibility tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_collapses_and_expands_on_click_only tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
```

Expected: pass.

- [ ] **Step 8: Commit**

Run:

```bash
git add packages/static/src/raya_static/rendering.py packages/static/src/raya_static/shell.py examples/courses/render-fixture/course/4_reader_ux/0_index.md tests/e2e/test_preview_static_read_path.py
git commit -m "Prioritize article in mobile shell"
```

---

### Task 5: Render-Debug Shell Inspection And Screenshots

**Files:**
- Modify: `packages/cli/src/raya_cli/render_debug.py`
- Modify: `packages/cli/src/raya_cli/render_debug_report.py`
- Modify: `tests/e2e/test_render_debug_report.py`
- Modify: `tests/e2e/test_render_debug_parity_gate.py`

- [ ] **Step 1: Write failing report parser test for new shell selectors**

In `tests/e2e/test_render_debug_report.py`, extend the malformed shell test or add:

```python
def test_render_debug_report_requires_collapsible_shell_controls(tmp_path: Path) -> None:
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text(
        """<!doctype html>
        <html><body>
          <header class="raya-top-command-bar" aria-label="Course tools"></header>
          <main id="raya-content" class="raya-learning-shell">
            <nav id="raya-course-map" class="raya-course-map" aria-label="Course map"></nav>
            <article id="raya-article" class="raya-main-article"></article>
            <aside class="raya-learning-rail" aria-label="Learning context"></aside>
          </main>
        </body></html>""",
        encoding="utf-8",
    )

    report = inspect_render_debug_site(site)

    assert not report.ok
    assert "button.raya-course-map-toggle" in report.learning_shell["missing_selectors"]
    assert "[data-raya-course-map-toggle]" in report.learning_shell["missing_selectors"]
```

Use the actual helper/import name already present in this test file. Keep the assertion shape aligned with current `learning_shell` report data.

- [ ] **Step 2: Run report test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_render_debug_report.py::test_render_debug_report_requires_collapsible_shell_controls -q
```

Expected: fail because render-debug does not yet require collapsible controls.

- [ ] **Step 3: Extend shell selector inspection**

In `packages/cli/src/raya_cli/render_debug_report.py`, add these selectors to `LEARNING_SHELL_SELECTORS`:

```python
"nav#raya-course-map.raya-course-map",
"button.raya-course-map-toggle",
"[data-raya-course-map-toggle]",
```

If the current parser cannot recognize bare attribute selectors, extend `_ElementMarkerParser` so each start tag adds attribute markers:

```python
attrs_by_name = {name: value for name, value in attrs}
for name in attrs_by_name:
    self.selectors.add(f"[{name}]")
```

For `data-raya-course-map-toggle`, this must produce `[data-raya-course-map-toggle]`.

- [ ] **Step 4: Run report test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_render_debug_report.py::test_render_debug_report_requires_collapsible_shell_controls -q
```

Expected: pass.

- [ ] **Step 5: Add collapsed/expanded screenshots to render debug**

In `packages/cli/src/raya_cli/render_debug.py`, after normal desktop screenshot capture, add a click-state screenshot for pages with `.raya-course-map-toggle`:

```python
toggle = page.locator(".raya-course-map-toggle").first
if toggle.count() > 0:
    page.screenshot(path=str(page_output_dir / "desktop-collapsed.png"), full_page=False)
    toggle.click()
    page.wait_for_timeout(100)
    page.screenshot(path=str(page_output_dir / "desktop-expanded.png"), full_page=False)
```

Record these paths in the existing screenshot manifest/report structure using names `desktop-collapsed` and `desktop-expanded`. Follow the existing report data shape; do not invent a second report format.

- [ ] **Step 6: Extend parity gate test**

In `tests/e2e/test_render_debug_parity_gate.py`, add assertions to the render-debug gate output test:

```python
assert (debug_dir / "screenshots" / "index" / "desktop-collapsed.png").exists()
assert (debug_dir / "screenshots" / "index" / "desktop-expanded.png").exists()
```

Use the actual debug output path variable and page slug shape used in the existing test.

- [ ] **Step 7: Run render-debug focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_render_debug_report.py tests/e2e/test_render_debug_parity_gate.py -q
```

Expected: pass.

- [ ] **Step 8: Commit**

Run:

```bash
git add packages/cli/src/raya_cli/render_debug.py packages/cli/src/raya_cli/render_debug_report.py tests/e2e/test_render_debug_report.py tests/e2e/test_render_debug_parity_gate.py
git commit -m "Inspect collapsible learning shell"
```

---

### Task 6: Foundation And Role Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Modify: `tests/contracts/test_renderer_dependencies.py`

- [ ] **Step 1: Write failing docs coverage test**

Add this test to `tests/contracts/test_renderer_dependencies.py`:

```python
def test_docs_cover_collapsible_learning_shell() -> None:
    required = {
        "docs/foundation/20_learning_renderer_contract.md": [
            "collapsed course map",
            "click-only",
            "Page N of M",
            "no personal progress",
        ],
        "docs/guides/en/professors/index.md": [
            "collapsed course map",
            "Page N of M",
            "not personal progress",
        ],
        "docs/guides/en/contributors/index.md": [
            "click-only",
            "aria-expanded",
            "local renderer resources",
        ],
        "docs/guides/en/students/index.md": [
            "Course map",
            "Previous",
            "Next",
            "OpenDyslexic",
        ],
        "docs/guides/en/agents/index.md": [
            "expanded course map",
            "non-persistent",
            "no external requests",
            "render-debug",
        ],
        "docs/guides/es/profesores/index.md": [
            "mapa del curso colapsado",
            "Page N of M",
            "no es progreso personal",
        ],
        "docs/guides/es/colaboradores/index.md": [
            "click-only",
            "aria-expanded",
            "recursos locales del renderer",
        ],
        "docs/guides/es/estudiantes/index.md": [
            "mapa del curso",
            "Anterior",
            "Siguiente",
            "OpenDyslexic",
        ],
        "docs/guides/es/agentes/index.md": [
            "mapa del curso expandido",
            "no persistente",
            "sin solicitudes externas",
            "render-debug",
        ],
    }
    for relative_path, needles in required.items():
        text = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{relative_path} must mention {needle}"
```

Use the repository root constant already present in the test file. If its name differs, use the existing root constant from that file.

- [ ] **Step 2: Run docs test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_renderer_dependencies.py::test_docs_cover_collapsible_learning_shell -q
```

Expected: fail because docs do not yet mention the new shell behavior.

- [ ] **Step 3: Update foundation contract**

In `docs/foundation/20_learning_renderer_contract.md`, update the Course Shell and Static Renderer Status sections with:

```markdown
The current shell uses an expanded course map by default, mobile-first article priority, and an explicit click-only control that collapses the map to a compact rail. The shell may show structural page position such as `Page N of M`; this is course structure, not personal progress.
```

Add under Non-Goals:

```markdown
- no hover-first navigation expansion that moves the reading layout without intent;
- no wording that turns structural page position into personal progress.
```

- [ ] **Step 4: Update English role docs**

Add concise role-specific paragraphs:

Professors:

```markdown
Rendered pages now use an expanded course map by default and let students collapse it to a compact rail for more reading space. The shell may show structure such as `Page N of M`; treat that as course position, not personal progress or completion.
```

Contributors:

```markdown
Review shell controls as accessibility surfaces. The course-map behavior is click-only, uses `aria-expanded`, and must be served from local renderer resources rather than external scripts or styles.
```

Students:

```markdown
Use the Course map button to open the course navigation when you need orientation. Use Previous and Next to move through the ordered material, and use OpenDyslexic when that font is more comfortable.
```

Agents:

```markdown
When changing the shell, verify the expanded course map default, compact rail metadata, render-debug output, mobile no-overflow behavior, and no external requests. The course map state is non-persistent UI state.
```

- [ ] **Step 5: Update Spanish role docs**

Add concise role-specific paragraphs:

Profesores:

```markdown
Las paginas renderizadas usan un mapa del curso expandido por defecto y permiten colapsarlo a un riel compacto para dar mas espacio de lectura. La shell puede mostrar estructura como `Page N of M`; eso es posicion dentro del curso y no es progreso personal ni finalizacion.
```

Colaboradores:

```markdown
Revisa los controles de la shell como superficies de accesibilidad. El mapa del curso es click-only, usa `aria-expanded`, y debe servirse desde recursos locales del renderer sin scripts ni estilos externos.
```

Estudiantes:

```markdown
Usa el boton del mapa del curso para abrir la navegacion cuando necesites orientarte. Usa Anterior y Siguiente para moverte por el material ordenado, y usa OpenDyslexic cuando esa fuente sea mas comoda.
```

Agentes:

```markdown
Al cambiar la shell, verifica el mapa del curso expandido por defecto, la metadata del riel compacto, la salida de render-debug, el comportamiento movil sin overflow y sin solicitudes externas. El estado del mapa del curso es UI no persistente.
```

- [ ] **Step 6: Run docs test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_renderer_dependencies.py::test_docs_cover_collapsible_learning_shell -q
```

Expected: pass.

- [ ] **Step 7: Commit**

Run:

```bash
git add docs/foundation/20_learning_renderer_contract.md docs/guides/en/professors/index.md docs/guides/en/contributors/index.md docs/guides/en/students/index.md docs/guides/en/agents/index.md docs/guides/es/profesores/index.md docs/guides/es/colaboradores/index.md docs/guides/es/estudiantes/index.md docs/guides/es/agentes/index.md tests/contracts/test_renderer_dependencies.py
git commit -m "Document collapsible learning shell"
```

---

### Task 7: Final Verification, Preview, And Review

**Files:**
- No planned source edits unless verification finds a defect.

- [ ] **Step 1: Run focused contract tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py tests/contracts/test_renderer_dependencies.py -q
```

Expected: pass.

- [ ] **Step 2: Run focused browser and render-debug tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py tests/e2e/test_render_debug_report.py tests/e2e/test_render_debug_parity_gate.py -q
```

Expected: pass.

- [ ] **Step 3: Run render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: pass and write local debug artifacts outside tracked source.

- [ ] **Step 4: Run host archive gate**

Run:

```bash
./scripts/check.sh
```

Expected: pass.

- [ ] **Step 5: Run Docker gate**

Run only after `./scripts/check.sh` completes:

```bash
./scripts/check-docker.sh
```

Expected: pass.

- [ ] **Step 6: Start local preview for human inspection**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --port 8018
```

Expected output includes:

```text
entrypoint=http://127.0.0.1:8018/index.html
inspection=http://127.0.0.1:8018/_raya/inspect/index.html
```

If port `8018` is occupied by a stale preview, stop the old preview process and rerun the same command.

- [ ] **Step 7: Request final code review**

Use `superpowers:requesting-code-review`. Review the full implementation range from the plan commit to current `HEAD`. Ask the reviewer to check:

- click-only course-map expansion;
- desktop expanded default, compact collapsed rail, and article width;
- mobile article priority and no overflow;
- active heading behavior;
- no personal-progress wording;
- no external requests;
- static preview/copied-site parity;
- English and Spanish role docs;
- test coverage.

- [ ] **Step 8: Fix review findings**

For every Critical or Important finding:

1. use `superpowers:receiving-code-review`;
2. verify the finding against the code;
3. write or update a focused failing test;
4. implement the fix;
5. rerun the focused test;
6. commit with a short imperative subject.

- [ ] **Step 9: Final status**

Run:

```bash
git status --short --branch
git log --oneline --decorate -5
```

Expected: clean working tree on `new_rayalucaria`, with the implementation commits ahead of `origin/new_rayalucaria`.

Report:

- verification commands and pass/fail results;
- local preview URL;
- review result;
- branch ahead count;
- whether the branch has been pushed.
