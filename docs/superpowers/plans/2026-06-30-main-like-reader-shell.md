# Main-Like Reader Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make generated reader pages use a main-like structural left course rail: desktop reflows article width on collapse/expand, mobile uses a modal drawer, and reader commands live in the left rail without a reader top bar.

**Architecture:** Keep the reset static builder. `builder.py` owns reader markup, `rendering.py` owns responsive layout and visual state, and `shell.py` owns volatile UI behavior, focus, resize normalization, and map orientation. Foundation and role docs move the reader-control contract from a top bar to the left rail.

**Tech Stack:** Python 3.10, generated static HTML/CSS/JS, Playwright e2e tests, string/regex HTML assertions already used in contract tests, existing `uv` and Raya CLI workflows.

---

## File Structure

- Modify `docs/foundation/20_learning_renderer_contract.md`: replace reader top-bar contract language with left-rail reader commands, while preserving discovery command bars and volatile shell-state rules.
- Modify `docs/guides/en/students/index.md` and `docs/guides/es/estudiantes/index.md`: describe the left course rail, collapsed Map tab, and mobile map drawer.
- Modify `docs/guides/en/agents/index.md` and `docs/guides/es/agentes/index.md`: remove stale top-bar assumptions for generated reader pages.
- Modify `packages/static/src/raya_static/builder.py`: keep reader top bar removed, dedupe workspace command surfaces in the course map, and ensure course tools are descendants of `#raya-course-map`.
- Modify `packages/static/src/raya_static/rendering.py`: implement desktop structural rail metrics, collapsed rail width, single scroll owner, no mobile drawer leakage, and reduced-motion-safe transitions.
- Modify `packages/static/src/raya_static/shell.py`: separate desktop structural map state from mobile drawer state, normalize state on resize, modalize mobile drawer interaction, and orient the current map link inside the real scrollport without browser storage.
- Modify `tests/contracts/test_static_builder.py`: assert semantic reader markup, no reader top bar, local links, accessible names, and no storage/fetch regressions.
- Modify `tests/e2e/test_preview_static_read_path.py`: add geometry, overflow, drawer modal, resize, scrolling, and volatile-state browser tests.

---

### Task 1: Contract And Role Docs

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Test: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write failing documentation contract checks**

Add this test near the existing learning renderer contract/documentation checks in `tests/contracts/test_static_builder.py`:

```python
def test_learning_renderer_contract_describes_left_rail_reader_commands() -> None:
    foundation = (
        ROOT
        / "docs"
        / "foundation"
        / "20_learning_renderer_contract.md"
    ).read_text(encoding="utf-8")
    assert "left course rail" in foundation
    assert "reader top bar" not in foundation.lower()
    assert "sticky command bar" not in foundation.lower()
    assert "Discovery workspace chrome" in foundation
    assert "non-persistent UI state" in foundation


def test_role_guides_describe_left_rail_reader_shell() -> None:
    guide_paths = [
        ROOT / "docs" / "guides" / "en" / "students" / "index.md",
        ROOT / "docs" / "guides" / "es" / "estudiantes" / "index.md",
        ROOT / "docs" / "guides" / "en" / "agents" / "index.md",
        ROOT / "docs" / "guides" / "es" / "agentes" / "index.md",
    ]
    for path in guide_paths:
        text = path.read_text(encoding="utf-8").lower()
        assert "top bar" not in text
        assert "left" in text or "izquier" in text
        assert "map" in text or "mapa" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_learning_renderer_contract_describes_left_rail_reader_commands \
  tests/contracts/test_static_builder.py::test_role_guides_describe_left_rail_reader_shell
```

Expected: both tests fail because the foundation still says sticky command bar or role docs still describe stale controls.

- [ ] **Step 3: Update foundation contract**

In `docs/foundation/20_learning_renderer_contract.md`, replace reader command-bar language with this contract language:

```markdown
The current reader shell uses an expanded course map rendered as a structural left course rail by default on desktop and browser load, keeps the article primary as the continuous reading surface, and supports mobile article-first layout. Reader commands such as static Search handoff, Graph, Practice, Tasks, Schedule, reader focus, right learning-rail context, local text size, and local OpenDyslexic controls live in the left course rail on reader pages. Discovery workspace pages may keep their own command bar because they do not render the reader course map. Article pages may show reader breadcrumbs with the course home, ancestor pages, and current page generated from navigation data. Breadcrumb links are deployment-neutral static links and must not expose authored source paths. The course map is generated from current navigation data, can be filtered locally by rendered page labels, may show generated structural sequence numbers, may include compact static workspace shortcuts to Search, Graph, Practice, Tasks, and Schedule, may include volatile section controls to expand the current path, expand all sections, or collapse back to the current path, and may auto-orient the current page into the visible map region after load. It does not collapse on hover; desktop readers can collapse it through an explicit click control, and keyboard users can close it with Escape. Collapsed desktop mode becomes an operable compact map rail with an intentional Map tab: visible rail items remain real navigation targets, not decorative markers. A desktop reader focus command may collapse the course map and right learning rail together as volatile display state. A desktop context command may collapse or restore only the right learning rail while leaving the course map available. When the right rail is collapsed on desktop, it becomes an operable Context tab and its body is removed from keyboard and assistive navigation until restored. The shell may use coordinated, reduced-motion-aware visual transitions for explicit map, context, and reader-focus state changes so the reader perceives one continuous workspace; these transitions are display state only and must not persist shell state, infer progress, or hide accessible content outside the documented collapsed desktop states. On tablet and mobile, a compact course-map control may open the course map as an intentional modal drawer containing a visible drawer header, structural page position when available, the same static map, workspace shortcuts, filter, and section controls; while open, background page scrolling is paused and background regions are unavailable to pointer, keyboard, and assistive navigation until the drawer closes through its close button, backdrop, or Escape. The closed drawer is non-persistent, inert, hidden from assistive navigation, and must not hide the article or right learning rail from normal reading. Course-map state, orientation, workspace links, shortcut badges, drawer state, drawer scroll lock, reader focus state, right-rail context state, section expansion, search text, and filter text are non-persistent UI state. The right learning rail collapse is a desktop-only affordance; tablet and mobile layouts keep the rail body visually and accessibly available when collapse controls are hidden, and Escape must not create an inert hidden rail state there. The shell may show structural page position such as `Page N of M`; this is course structure, not personal progress. The article may also end with larger Previous/Next sequence cards generated from the same ordered navigation data so students have a clear static reading path after finishing the page.
```

Also update the renderer contract table rows that mention command-bar search/context so they say “left course rail reader commands” for reader pages and “discovery command bar” for discovery workspaces.

- [ ] **Step 4: Update role guides**

Add concise reader-shell wording to the English student guide:

```markdown
Reader pages use a left course rail for navigation and reader tools. On desktop the rail takes real page space; collapsing the Map tab gives that space back to the article. On phones and narrow tablets, the course map opens as a temporary drawer and closes with its close button, backdrop, or Escape.
```

Add the Spanish equivalent to `docs/guides/es/estudiantes/index.md`:

```markdown
Las páginas de lectura usan un riel izquierdo del curso para navegación y herramientas del lector. En escritorio el riel ocupa espacio real de la página; al contraer la pestaña Mapa, ese espacio vuelve al artículo. En teléfonos y tabletas angostas, el mapa del curso se abre como un cajón temporal y se cierra con su botón de cierre, el fondo o Escape.
```

Add agent guidance in English:

```markdown
Generated reader pages do not use a reader top bar. Reader navigation and commands belong in the left course rail; discovery workspaces may keep their own command bar.
```

Add agent guidance in Spanish:

```markdown
Las páginas de lectura generadas no usan una barra superior del lector. La navegación y los comandos del lector pertenecen al riel izquierdo del curso; los espacios de descubrimiento pueden conservar su propia barra de comandos.
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_learning_renderer_contract_describes_left_rail_reader_commands \
  tests/contracts/test_static_builder.py::test_role_guides_describe_left_rail_reader_shell
```

Expected: both tests pass.

- [ ] **Step 6: Commit**

```bash
git add docs/foundation/20_learning_renderer_contract.md \
  docs/guides/en/students/index.md \
  docs/guides/es/estudiantes/index.md \
  docs/guides/en/agents/index.md \
  docs/guides/es/agentes/index.md \
  tests/contracts/test_static_builder.py
git commit -m "Document left rail reader shell contract"
```

---

### Task 2: Semantic Reader Markup And Tool Deduplication

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write failing semantic markup test**

Extend `test_render_fixture_uses_static_learning_shell` or add this focused test in `tests/contracts/test_static_builder.py`:

```python
def test_reader_tools_live_inside_course_map_without_top_bar(tmp_path: Path) -> None:
    course = _copy_render_fixture(tmp_path)
    report = build_course(course)
    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (
        course / "artifact" / "site" / "math-authoring" / "index.html"
    ).read_text(encoding="utf-8")

    assert '<header class="raya-top-command-bar" aria-label="Course tools">' not in html
    map_start = html.index('<nav id="raya-course-map"')
    map_end = html.index("</nav>", map_start)
    course_map_html = html[map_start:map_end]
    assert 'data-raya-course-map-tools' in course_map_html
    assert 'action="../_raya/search/index.html"' in course_map_html

    expected = {
        "Graph": "../_raya/graph/index.html?page=math-authoring",
        "Practice": "../_raya/practice/index.html?page=math-authoring",
        "Tasks": "../_raya/tasks/index.html?page=math-authoring",
        "Schedule": "../_raya/schedule/index.html?page=math-authoring",
    }
    for label, href in expected.items():
        assert f'href="{href}"' in course_map_html, label

    command_count = sum(
        course_map_html.count(command_class)
        for command_class in (
            "raya-command-graph",
            "raya-command-practice",
            "raya-command-tasks",
            "raya-command-schedule",
        )
    )
    assert command_count == 4
    assert course_map_html.count("data-raya-course-map-workspace-link") <= 4
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_reader_tools_live_inside_course_map_without_top_bar
```

Expected: fails if tools are duplicated, outside the map, missing accessible links, or stale top bar remains.

- [ ] **Step 3: Adjust reader markup in `builder.py`**

In `packages/static/src/raya_static/builder.py`:

1. Keep `_render_top_command_bar` available for discovery-only callers.
2. Keep reader page render from calling `_render_top_command_bar`.
3. Make `_render_course_map_tools(...)` return the single compact command surface for reader Search, Graph, Practice, Tasks, Schedule, Map, Focus, Context, Text size, and OpenDyslexic.
4. Make `_render_course_map_workspaces(...)` either omit duplicate workspace cards or render only compact badges/details that do not duplicate the same primary links already in `_render_course_map_tools(...)`.

Use this invariant in code:

```python
tools_html = _render_course_map_tools(
    course=course,
    page=page,
    pages=pages,
    relative_prefix=relative_prefix,
)
workspace_html = _render_course_map_workspaces(
    course=course,
    page=page,
    pages=pages,
    relative_prefix=relative_prefix,
    include_primary_workspace_links=False,
)
```

If `_render_course_map_workspaces` does not yet accept `include_primary_workspace_links`, add that keyword-only parameter and use it to suppress duplicate primary Search/Graph/Practice/Tasks/Schedule cards on reader pages.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_reader_tools_live_inside_course_map_without_top_bar
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/builder.py tests/contracts/test_static_builder.py
git commit -m "Place reader commands in course rail"
```

---

### Task 3: Desktop Structural Rail Geometry

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing desktop geometry test**

Add this test to `tests/e2e/test_preview_static_read_path.py`:

```python
def test_reader_left_rail_reallocates_article_width_like_main(tmp_path: Path) -> None:
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
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for width in (1280, 1366, 1440, 1920):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    try:
                        page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                        _assert_no_horizontal_overflow(page)
                        expanded = page.evaluate(
                            """() => {
                              const box = (selector) => {
                                const rect = document.querySelector(selector).getBoundingClientRect();
                                return { left: rect.left, right: rect.right, width: rect.width, top: rect.top, bottom: rect.bottom };
                              };
                              return {
                                map: box('#raya-course-map'),
                                article: box('#raya-article'),
                                rail: box('#raya-learning-rail'),
                                scrollWidth: document.documentElement.scrollWidth,
                                clientWidth: document.documentElement.clientWidth,
                              };
                            }"""
                        )
                        assert expanded["map"]["right"] <= expanded["article"]["left"]
                        assert expanded["article"]["right"] <= expanded["rail"]["left"]
                        assert 208 <= expanded["map"]["width"] <= 272
                        assert expanded["scrollWidth"] <= expanded["clientWidth"]

                        page.click("#raya-course-map .raya-course-map-toggle")
                        page.wait_for_function(
                            """() => document.documentElement.dataset.rayaCourseMap === 'collapsed'
                              && document.querySelector('#raya-course-map').getBoundingClientRect().width <= 88"""
                        )
                        collapsed = page.evaluate(
                            """() => {
                              const box = (selector) => {
                                const rect = document.querySelector(selector).getBoundingClientRect();
                                return { left: rect.left, right: rect.right, width: rect.width };
                              };
                              return {
                                map: box('#raya-course-map'),
                                article: box('#raya-article'),
                                rail: box('#raya-learning-rail'),
                                scrollWidth: document.documentElement.scrollWidth,
                                clientWidth: document.documentElement.clientWidth,
                              };
                            }"""
                        )
                        assert collapsed["map"]["width"] <= 88
                        assert collapsed["article"]["width"] >= expanded["article"]["width"] + 96
                        assert collapsed["map"]["right"] <= collapsed["article"]["left"]
                        assert collapsed["article"]["right"] <= collapsed["rail"]["left"]
                        assert collapsed["scrollWidth"] <= collapsed["clientWidth"]
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
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_reader_left_rail_reallocates_article_width_like_main
```

Expected: FAIL on current obscuring/width behavior.

- [ ] **Step 3: Implement desktop grid metrics in CSS**

In `packages/static/src/raya_static/rendering.py`, adjust the `@media (min-width: 1280px)` shell rules so desktop states use structural grid columns:

```css
@media (min-width: 1280px) {
  .raya-learning-shell {
    align-items: start;
    gap: 1rem;
    grid-template-columns: 15rem minmax(0, 1fr) 15rem;
  }

  html[data-raya-course-map="collapsed"] .raya-learning-shell,
  .raya-learning-shell[data-raya-course-map="collapsed"] {
    grid-template-columns: 5rem minmax(0, 1fr) 15rem;
  }

  html[data-raya-learning-rail="collapsed"] .raya-learning-shell,
  .raya-learning-shell[data-raya-learning-rail="collapsed"] {
    grid-template-columns: 15rem minmax(0, 1fr) 5rem;
  }

  html[data-raya-course-map="collapsed"][data-raya-learning-rail="collapsed"] .raya-learning-shell,
  .raya-learning-shell[data-raya-course-map="collapsed"][data-raya-learning-rail="collapsed"] {
    grid-template-columns: 5rem minmax(0, 1fr) 5rem;
  }

  .raya-course-map,
  .raya-learning-rail {
    max-height: calc(100vh - 2rem);
    overflow: auto;
    position: sticky;
    top: 1rem;
  }
}
```

Keep existing skin variables and borders. Remove any desktop rule that positions the course map over the article or gives the article a fixed `min-width` that creates document overflow at `1280px`.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_reader_left_rail_reallocates_article_width_like_main
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git commit -m "Reflow article with structural course rail"
```

---

### Task 4: Right Rail Independent Reallocation And Comfort Overflow

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing right-rail independence test**

Add this test:

```python
def test_reader_rails_reallocate_article_width_independently(tmp_path: Path) -> None:
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
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                try:
                    page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                    page.evaluate(
                        """() => {
                          document.documentElement.dataset.rayaReaderTextSize = 'large';
                          document.documentElement.classList.add('raya-open-dyslexic');
                        }"""
                    )
                    baseline = _bounding_box(page, "#raya-article")
                    page.click("[data-raya-learning-rail-collapse]")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaLearningRail === 'collapsed'"
                    )
                    right_collapsed = _bounding_box(page, "#raya-article")
                    assert right_collapsed["width"] >= baseline["width"] + 96

                    page.click("#raya-course-map .raya-course-map-toggle")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaCourseMap === 'collapsed'"
                    )
                    both_collapsed = _bounding_box(page, "#raya-article")
                    assert both_collapsed["width"] >= right_collapsed["width"] + 96
                    _assert_no_horizontal_overflow(page)
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
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_reader_rails_reallocate_article_width_independently
```

Expected: FAIL if right rail and left rail do not independently increase article width or if large text overflows.

- [ ] **Step 3: Tighten CSS overflow behavior**

In `rendering.py`, ensure:

```css
.raya-learning-shell,
.raya-main-article,
.raya-course-map,
.raya-learning-rail {
  min-width: 0;
}

.raya-course-map-tool-grid .raya-command,
.raya-course-map-workspace-link,
.raya-course-map a {
  max-width: 100%;
}

.raya-course-map-tool-grid .raya-command-label,
.raya-course-map-workspace-label,
.raya-course-map-workspace-detail {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

Keep existing current-page compact marker styles, but ensure collapsed-state hidden verbose controls are `display: none` and not positioned over the article.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_reader_rails_reallocate_article_width_independently
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git commit -m "Preserve independent reader rail reflow"
```

---

### Task 5: Mobile Drawer Modal State And Resize Normalization

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing mobile modal test**

Add this test:

```python
def test_mobile_course_map_drawer_is_modal_and_nonleaking(tmp_path: Path) -> None:
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
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for viewport in ({"width": 390, "height": 844}, {"width": 1180, "height": 900}):
                    page = browser.new_page(viewport=viewport)
                    try:
                        page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                        closed = page.evaluate(
                            """() => {
                              const map = document.querySelector('#raya-course-map');
                              const rect = map.getBoundingClientRect();
                              const focusable = Array.from(map.querySelectorAll('a, button, input'))
                                .filter((node) => node.getAttribute('tabindex') !== '-1');
                              const hit = document.elementFromPoint(20, 20);
                              return {
                                ariaHidden: map.getAttribute('aria-hidden'),
                                inert: map.inert,
                                intersects: rect.right > 0 && rect.bottom > 0 && rect.left < innerWidth && rect.top < innerHeight && rect.width > 4 && rect.height > 4,
                                focusableCount: focusable.length,
                                hitInsideMap: map.contains(hit),
                              };
                            }"""
                        )
                        assert closed == {
                            "ariaHidden": "true",
                            "inert": True,
                            "intersects": False,
                            "focusableCount": 0,
                            "hitInsideMap": False,
                        }

                        page.click(".raya-mobile-course-map-open")
                        page.wait_for_function(
                            "() => document.documentElement.dataset.rayaCourseMapDrawer === 'open'"
                        )
                        opened = page.evaluate(
                            """() => {
                              const map = document.querySelector('#raya-course-map');
                              const article = document.querySelector('#raya-article');
                              const rail = document.querySelector('#raya-learning-rail');
                              const backdrop = document.querySelector('[data-raya-course-map-drawer-backdrop]');
                              const rect = map.getBoundingClientRect();
                              return {
                                ariaHidden: map.getAttribute('aria-hidden'),
                                inert: map.inert,
                                intersects: rect.left < innerWidth && rect.right > 0 && rect.width >= 300,
                                backdropVisible: !!backdrop && !backdrop.hidden && getComputedStyle(backdrop).display !== 'none',
                                scrollLock: document.documentElement.dataset.rayaCourseMapScrollLock,
                                articleInert: article.inert,
                                railInert: rail.inert,
                              };
                            }"""
                        )
                        assert opened["ariaHidden"] == "false"
                        assert opened["inert"] is False
                        assert opened["intersects"] is True
                        assert opened["backdropVisible"] is True
                        assert opened["scrollLock"] == "true"
                        assert opened["articleInert"] is True
                        assert opened["railInert"] is True

                        for _ in range(8):
                            page.keyboard.press("Tab")
                            assert page.evaluate(
                                "() => document.querySelector('#raya-course-map').contains(document.activeElement)"
                            )

                        page.keyboard.press("Escape")
                        page.wait_for_function(
                            "() => document.documentElement.dataset.rayaCourseMapDrawer === 'closed'"
                        )
                        assert page.locator(".raya-mobile-course-map-open").is_focused()
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
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_mobile_course_map_drawer_is_modal_and_nonleaking
```

Expected: FAIL until background inertness, hit testing, and drawer leakage are corrected.

- [ ] **Step 3: Implement mobile CSS isolation**

In `rendering.py`, under `@media (max-width: 1279px)`, enforce:

```css
html[data-raya-course-map-drawer="closed"] .raya-course-map {
  height: 1px;
  left: -120vw;
  max-height: 1px;
  overflow: hidden;
  position: fixed;
  top: 0;
  width: 1px;
}

html[data-raya-course-map-drawer="closed"] .raya-course-map * {
  pointer-events: none;
}

html[data-raya-course-map-drawer="open"] .raya-course-map {
  bottom: 0;
  display: block;
  left: 0;
  max-height: 100vh;
  overflow: auto;
  position: fixed;
  top: 0;
  width: min(22rem, calc(100vw - 2.5rem));
  z-index: 20;
}

html[data-raya-course-map-drawer="open"] .raya-course-map-tools {
  display: grid;
}
```

Ensure closed mobile drawer descendants cannot appear at top-left through sticky positioning.

- [ ] **Step 4: Implement modal state in `shell.py`**

In `shell.py`, add:

```javascript
const article = document.querySelector("#raya-article");

function setBackgroundInertForCourseMapDrawer(inert) {
  [shell, article, learningRail].forEach((element) => {
    if (!element || element === map || map.contains(element)) {
      return;
    }
    if (inert) {
      element.setAttribute("inert", "");
    } else {
      element.removeAttribute("inert");
    }
    element.inert = inert;
  });
}
```

Call `setBackgroundInertForCourseMapDrawer(true)` from `openCourseMapDrawer` after setting drawer state. Call `setBackgroundInertForCourseMapDrawer(false)` from `closeCourseMapDrawer` and from the desktop branch of `syncCourseMapDrawerState`.

Do not call `setExpanded(true)` when opening the mobile drawer. Use the existing structural state for desktop and only open the drawer state for mobile.

- [ ] **Step 5: Run test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_mobile_course_map_drawer_is_modal_and_nonleaking
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/static/src/raya_static/rendering.py \
  packages/static/src/raya_static/shell.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Modalize mobile course map drawer"
```

---

### Task 6: Resize State Preservation

**Files:**
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing resize normalization test**

Add:

```python
def test_course_map_resize_preserves_desktop_state_without_stale_inertness(tmp_path: Path) -> None:
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
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                page.click("#raya-course-map .raya-course-map-toggle")
                page.wait_for_function(
                    "() => document.documentElement.dataset.rayaCourseMap === 'collapsed'"
                )
                page.set_viewport_size({"width": 390, "height": 844})
                page.click(".raya-mobile-course-map-open")
                page.wait_for_function(
                    "() => document.documentElement.dataset.rayaCourseMapDrawer === 'open'"
                )
                page.keyboard.press("Escape")
                page.wait_for_function(
                    "() => document.documentElement.dataset.rayaCourseMapDrawer === 'closed'"
                )
                page.set_viewport_size({"width": 1440, "height": 900})
                page.wait_for_function(
                    """() => document.documentElement.dataset.rayaCourseMap === 'collapsed'
                      && document.documentElement.dataset.rayaCourseMapDrawer === 'closed'
                      && document.documentElement.dataset.rayaCourseMapScrollLock === 'false'"""
                )
                state = page.evaluate(
                    """() => ({
                      mapInert: document.querySelector('#raya-course-map').inert,
                      articleInert: document.querySelector('#raya-article').inert,
                      railInert: document.querySelector('#raya-learning-rail').inert,
                      focusedVisible: document.activeElement
                        ? document.activeElement.getClientRects().length > 0
                        : true,
                      mapWidth: document.querySelector('#raya-course-map').getBoundingClientRect().width,
                    })"""
                )
                assert state["mapInert"] is False
                assert state["articleInert"] is False
                assert state["railInert"] is False
                assert state["focusedVisible"] is True
                assert state["mapWidth"] <= 88
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_course_map_resize_preserves_desktop_state_without_stale_inertness
```

Expected: FAIL until mobile drawer open/close stops mutating desktop collapse state and resize normalization clears inertness.

- [ ] **Step 3: Normalize state on breakpoint changes**

In `shell.py`, add a resize handler that calls this logic when `desktopMapQuery.matches` changes:

```javascript
function normalizeCourseMapForViewport() {
  if (isDesktopShell()) {
    root.dataset.rayaCourseMapDrawer = "closed";
    root.setAttribute("data-raya-course-map-scroll-lock", "false");
    setBackgroundInertForCourseMapDrawer(false);
    setElementInert(map, false);
    map.setAttribute("aria-hidden", "false");
    setFocusableDescendantsEnabled(map, true);
    if (document.activeElement && !document.activeElement.getClientRects().length) {
      const visibleToggle = map.querySelector(".raya-course-map-toggle");
      if (visibleToggle) {
        visibleToggle.focus();
      }
    }
    return;
  }
  syncCourseMapDrawerState();
}
```

Wire it to the media query:

```javascript
if (desktopMapQuery.addEventListener) {
  desktopMapQuery.addEventListener("change", normalizeCourseMapForViewport);
} else if (desktopMapQuery.addListener) {
  desktopMapQuery.addListener(normalizeCourseMapForViewport);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_course_map_resize_preserves_desktop_state_without_stale_inertness
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/shell.py tests/e2e/test_preview_static_read_path.py
git commit -m "Normalize course map state across breakpoints"
```

---

### Task 7: Scroll Ownership And Current-Page Orientation

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing orientation test**

Add:

```python
def test_course_map_orients_current_page_below_tools(tmp_path: Path) -> None:
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
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 520})
                page.goto(f"{handle.base_url}/authoring-matrix/index.html", wait_until="networkidle")
                visible = page.evaluate(
                    """() => {
                      window.rayaOrientCourseMapToCurrentPage();
                      const map = document.querySelector('#raya-course-map');
                      const tools = document.querySelector('[data-raya-course-map-tools]');
                      const current = map.querySelector('a[aria-current="page"]');
                      const mapBox = map.getBoundingClientRect();
                      const toolsBox = tools.getBoundingClientRect();
                      const currentBox = current.getBoundingClientRect();
                      return {
                        currentBelowTools: currentBox.top >= toolsBox.bottom - 1,
                        currentInsideMap: currentBox.top >= mapBox.top && currentBox.bottom <= mapBox.bottom,
                        scrollTop: map.scrollTop,
                        storageKeys: Object.keys(localStorage).concat(Object.keys(sessionStorage)),
                      };
                    }"""
                )
                assert visible["currentBelowTools"] is True
                assert visible["currentInsideMap"] is True
                assert visible["scrollTop"] >= 0
                assert visible["storageKeys"] == []

                page.click("#raya-course-map .raya-course-map-toggle")
                page.click("#raya-course-map .raya-course-map-toggle")
                page.wait_for_function(
                    "() => document.documentElement.dataset.rayaCourseMap === 'expanded'"
                )
                expanded = page.evaluate(
                    """() => {
                      window.rayaOrientCourseMapToCurrentPage();
                      const map = document.querySelector('#raya-course-map');
                      const tools = document.querySelector('[data-raya-course-map-tools]');
                      const current = map.querySelector('a[aria-current="page"]');
                      const toolsBox = tools.getBoundingClientRect();
                      const currentBox = current.getBoundingClientRect();
                      return currentBox.top >= toolsBox.bottom - 1;
                    }"""
                )
                assert expanded is True
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_course_map_orients_current_page_below_tools
```

Expected: FAIL if current link is hidden under sticky tools, scroll ownership is wrong, or storage keys are created.

- [ ] **Step 3: Implement one scroll owner and visible-region math**

In `rendering.py`, keep `.raya-course-map` as the single vertical scroll owner. Avoid `overflow: auto` on `.raya-course-map-list` or nested tool containers.

In `shell.py`, update `orientCourseMapToCurrentPage` so it computes a top obstruction:

```javascript
function courseMapVisibleTop(scrollContainer) {
  const containerRect = scrollContainer.getBoundingClientRect();
  const stickyChildren = Array.from(
    scrollContainer.querySelectorAll(".raya-course-map-tools, .raya-course-map-header")
  ).filter((element) => {
    const style = window.getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    return style.position === "sticky" && rect.bottom > containerRect.top;
  });
  return stickyChildren.reduce(
    (top, element) => Math.max(top, element.getBoundingClientRect().bottom),
    containerRect.top
  );
}
```

Use `visibleTop = courseMapVisibleTop(scrollContainer)` instead of `containerRect.top` for visibility and offset calculations:

```javascript
const visibleTop = courseMapVisibleTop(scrollContainer);
const isVisible =
  linkRect.top >= visibleTop && linkRect.bottom <= containerRect.bottom;
```

When not visible, scroll so the link top lands below `visibleTop + 8`.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_course_map_orients_current_page_below_tools
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/rendering.py \
  packages/static/src/raya_static/shell.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Orient course map below rail tools"
```

---

### Task 8: Volatile State And Storage Guard

**Files:**
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing storage guard test**

Add:

```python
def test_reader_shell_does_not_persist_map_or_drawer_state(tmp_path: Path) -> None:
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
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                page.fill("[data-raya-course-map-filter]", "matrix")
                page.click("#raya-course-map .raya-course-map-toggle")
                page.click("[data-raya-reader-focus-toggle]")
                keys = page.evaluate(
                    """() => ({
                      local: Object.keys(localStorage),
                      session: Object.keys(sessionStorage),
                    })"""
                )
                forbidden = ("map", "drawer", "focus", "rail", "filter", "search", "course")
                assert all(not any(word in key.lower() for word in forbidden) for key in keys["local"])
                assert all(not any(word in key.lower() for word in forbidden) for key in keys["session"])
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run test to verify it fails or passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_does_not_persist_map_or_drawer_state
```

Expected: PASS if no persistence exists; FAIL if shell code stores forbidden state.

- [ ] **Step 3: Remove forbidden storage writes if needed**

In `shell.py`, remove any `localStorage.setItem` or `sessionStorage.setItem` calls for map, drawer, rail, focus, filter, search, or course state. Keep comfort storage in the existing comfort scripts, not in `shell.py`.

The reader shell should only mutate DOM dataset state:

```javascript
root.dataset.rayaCourseMap = nextExpanded ? "expanded" : "collapsed";
root.dataset.rayaCourseMapDrawer = drawerOpen ? "open" : "closed";
root.dataset.rayaLearningRail = nextExpanded ? "expanded" : "collapsed";
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_does_not_persist_map_or_drawer_state
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/shell.py tests/e2e/test_preview_static_read_path.py
git commit -m "Keep reader shell state volatile"
```

---

### Task 9: Print And Discovery Regression

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write failing regression tests**

Add or update tests:

```python
def test_discovery_workspace_keeps_discovery_command_bar(tmp_path: Path) -> None:
    course = _copy_render_fixture(tmp_path)
    report = build_course(course)
    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    graph_html = (
        course / "artifact" / "site" / "_raya" / "graph" / "index.html"
    ).read_text(encoding="utf-8")
    assert 'class="raya-top-command-bar raya-discovery-command-bar"' in graph_html
    assert 'id="raya-course-map"' not in graph_html
```

Update print e2e assertions so they check no reader top bar and hidden rail surfaces:

```python
assert page.locator(".raya-top-command-bar").count() == 0
assert page.locator(".raya-mobile-course-map-open").evaluate(
    "node => getComputedStyle(node).display"
) == "none"
assert page.locator(".raya-course-map").evaluate(
    "node => getComputedStyle(node).display"
) == "none"
```

- [ ] **Step 2: Run tests to verify current state**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_discovery_workspace_keeps_discovery_command_bar \
  tests/e2e/test_preview_static_read_path.py::test_preview_reader_print_view_is_static_handout
```

Expected: FAIL if discovery command bars were removed or print CSS still assumes reader top bar exists.

- [ ] **Step 3: Fix print/discovery CSS**

In `rendering.py`, keep discovery command-bar CSS. In print rules, hide:

```css
@media print {
  .raya-mobile-course-map-open,
  .raya-course-map,
  .raya-learning-rail,
  .raya-discovery-command-bar,
  .raya-graph-canvas {
    display: none !important;
  }
}
```

Do not require `.raya-top-command-bar` to exist on reader pages.

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_discovery_workspace_keeps_discovery_command_bar \
  tests/e2e/test_preview_static_read_path.py::test_preview_reader_print_view_is_static_handout
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/rendering.py \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Preserve discovery chrome and print handouts"
```

---

### Task 10: Focused Regression Gate And Local Preview

**Files:**
- Modify only if tests expose a bug: `packages/static/src/raya_static/builder.py`, `packages/static/src/raya_static/rendering.py`, `packages/static/src/raya_static/shell.py`, `tests/contracts/test_static_builder.py`, `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Run focused contract and e2e suite**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell \
  tests/contracts/test_static_builder.py::test_reader_tools_live_inside_course_map_without_top_bar \
  tests/contracts/test_static_builder.py::test_discovery_workspace_keeps_discovery_command_bar \
  tests/e2e/test_preview_static_read_path.py::test_reader_left_rail_reallocates_article_width_like_main \
  tests/e2e/test_preview_static_read_path.py::test_reader_rails_reallocate_article_width_independently \
  tests/e2e/test_preview_static_read_path.py::test_mobile_course_map_drawer_is_modal_and_nonleaking \
  tests/e2e/test_preview_static_read_path.py::test_course_map_resize_preserves_desktop_state_without_stale_inertness \
  tests/e2e/test_preview_static_read_path.py::test_course_map_orients_current_page_below_tools \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_does_not_persist_map_or_drawer_state \
  tests/e2e/test_preview_static_read_path.py::test_preview_reader_print_view_is_static_handout
```

Expected: all selected tests pass.

- [ ] **Step 2: Run render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: exit code `0`, with no raw TeX leakage, no overflow, local MathJax resources present, and no external renderer requests.

- [ ] **Step 3: Run diff hygiene**

Run:

```bash
git diff --check
```

Expected: no output and exit code `0`.

- [ ] **Step 4: Restart local preview**

Stop any old preview:

```bash
pgrep -af "raya preview examples/courses/render-fixture" || true
```

Kill only the listed old preview PIDs, then run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --host 127.0.0.1 --port 4173
```

Expected output includes:

```text
preview:
- status=Static preview ready
- entrypoint=http://127.0.0.1:4173/index.html
```

- [ ] **Step 5: Smoke-check served page**

Run:

```bash
curl -I http://127.0.0.1:4173/index.html
curl -s http://127.0.0.1:4173/reader-ux/index.html | rg "raya-course-map-tools|raya-top-command-bar"
```

Expected: `HTTP/1.0 200 OK`; output includes `raya-course-map-tools` and does not include `raya-top-command-bar` for reader pages.

- [ ] **Step 6: Commit final fixes if any were needed**

If Task 10 required code or test edits, commit them:

```bash
git add packages/static/src/raya_static/builder.py \
  packages/static/src/raya_static/rendering.py \
  packages/static/src/raya_static/shell.py \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Verify main-like reader shell regression gate"
```

If Task 10 required no edits, do not create an empty commit.
