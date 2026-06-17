# Science-Backed Course Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the learning-science documentation foundation and a static Glintstone course shell with named desktop/mobile regions, current-data-only learning context, and render-debug/browser verification.

**Architecture:** Keep `docs/foundation/` as the authority layer and use the committed Superpowers design as this loop's planning source. Refactor the static renderer around small HTML helper functions in `packages/static/src/raya_static/builder.py`, keep CSS in `packages/static/src/raya_static/rendering.py`, and reuse current artifact data instead of adding schema state unless a task explicitly tests it. The shell uses static navigation, heading, normalized page metadata, stable-ID prerequisites, local assets, build-time MathJax, and existing skin/OpenDyslexic resources.

**Tech Stack:** Python 3.10, `uv`, pytest, Playwright/Chromium, MarkdownIt, build-time MathJax, static HTML/CSS, Raya Glintstone packages.

---

## Source Design

Implement against `docs/superpowers/specs/2026-06-17-science-backed-course-shell-design.md`.

Do not create OpenSpec artifacts in this loop unless the user explicitly switches workflow. This plan must update foundation and guidance text so that the Superpowers exception is explicit and does not compete with `docs/foundation/`.

## File Map

Documentation authority and guidance:

- Modify: `docs/foundation/00_index.md`
- Modify: `docs/foundation/13_truth_surfaces.md`
- Modify: `docs/foundation/16_documentation_surfaces.md`
- Modify: `docs/foundation/17_rendering_execution_plan.md`
- Create: `docs/foundation/19_learning_science_principles.md`
- Create: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/render-content/1_foundation/`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `openspec/config.yaml`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

Renderer:

- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

Fixture:

- Modify: `examples/courses/render-fixture/course/0_index.md`
- Modify: `examples/courses/render-fixture/course/4_reader_ux/0_index.md`

Tests:

- Modify: `tests/contracts/test_documentation_surfaces.py`
- Modify: `tests/contracts/test_renderer_dependencies.py`
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `tests/e2e/test_render_debug_report.py`
- Modify if needed: `tests/e2e/test_render_debug_parity_gate.py`

## Implementation Notes

- Current `ContentPage.summary` and `ContentPage.status` are normalized in `packages/schema/src/raya_schema/content.py`; do not write tests that require raw frontmatter presence for those fields.
- Prerequisite rail entries must render only when `page.prerequisites` values resolve to stable page IDs in `content_model.pages_by_id`. Use the resolved page `nav_title` or `title`, and link to the resolved page output path.
- Do not infer goals, related practice, progress, or assignments from prose, tags, headings, or numbered objects.
- Do not add browser-side MathJax, CDN URLs, external fonts, external CSS, or runtime fetches.
- Keep English and Spanish role docs separate. Keep technical identifiers in English.

---

### Task 1: Documentation Workflow Authority

**Files:**
- Modify: `tests/contracts/test_documentation_surfaces.py`
- Modify: `docs/foundation/13_truth_surfaces.md`
- Modify: `docs/foundation/16_documentation_surfaces.md`
- Modify: `docs/foundation/17_rendering_execution_plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `openspec/config.yaml`
- Modify: English and Spanish role docs listed in the file map

- [ ] **Step 1: Write failing documentation-surface test**

Add this test to `tests/contracts/test_documentation_surfaces.py` after `test_role_documentation_uses_separate_english_and_spanish_pages()`:

```python
def test_guidance_surfaces_allow_user_selected_superpowers_renderer_loops() -> None:
    required = {
        "docs/foundation/13_truth_surfaces.md": [
            "Superpowers design and plan documents",
            "user explicitly selects that workflow",
            "OpenSpec remains an accepted workflow",
        ],
        "docs/foundation/16_documentation_surfaces.md": [
            "Superpowers design and plan documents",
            "OpenSpec remains an accepted workflow",
        ],
        "docs/foundation/17_rendering_execution_plan.md": [
            "Superpowers",
            "science-backed course shell",
            "OpenSpec remains available",
        ],
        "README.md": [
            "Superpowers",
            "OpenSpec remains available",
            "docs/foundation/",
        ],
        "AGENTS.md": [
            "Superpowers",
            "OpenSpec remains available",
            "docs/foundation/",
        ],
        "openspec/config.yaml": [
            "Superpowers",
            "OpenSpec remains available",
            "docs/foundation/",
        ],
        "docs/guides/en/contributors/index.md": ["Superpowers", "OpenSpec remains available"],
        "docs/guides/en/agents/index.md": ["Superpowers", "OpenSpec remains available"],
        "docs/guides/es/colaboradores/index.md": ["Superpowers", "OpenSpec remains available"],
        "docs/guides/es/agentes/index.md": ["Superpowers", "OpenSpec remains available"],
    }
    for relative_path, needles in required.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{relative_path} must mention {needle}"
```

- [ ] **Step 2: Run failing test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py::test_guidance_surfaces_allow_user_selected_superpowers_renderer_loops -q
```

Expected: fail because current guidance still presents OpenSpec as the only renderer-change workflow.

- [ ] **Step 3: Update foundation authority wording**

Edit `docs/foundation/13_truth_surfaces.md`. Keep the existing hierarchy, but add this paragraph after the numbered hierarchy:

```markdown
When the user explicitly selects a Superpowers development loop, committed Superpowers design and plan documents may drive implementation for that loop. They do not outrank `docs/foundation/`; they are temporary planning surfaces that must update foundation docs, role docs, tests, and accepted contracts as needed. OpenSpec remains an accepted workflow for future contract changes and can mine the Superpowers design later if the user switches back.
```

Edit `docs/foundation/16_documentation_surfaces.md`. Add this paragraph under the opening authority paragraph:

```markdown
Some implementation loops may be planned through committed Superpowers design and plan documents when the user explicitly selects that workflow. Those documents explain the active work, but they do not replace foundation decisions or accepted specs. OpenSpec remains an accepted workflow, and documentation must say which workflow is active when guidance would otherwise be ambiguous.
```

Edit `docs/foundation/17_rendering_execution_plan.md`. Add a short status note near the current renderer/debugging status section:

```markdown
Current renderer-learning-shell work is being planned through a Superpowers design and implementation plan because the user selected that workflow for this loop. OpenSpec remains available for future renderer contract changes. This loop must still update `docs/foundation/`, role docs, tests, and artifact/static-renderer contracts before claiming new behavior is current.
```

- [ ] **Step 4: Update lower guidance surfaces**

In `README.md`, `AGENTS.md`, and `openspec/config.yaml`, add a concise note with this meaning:

```markdown
OpenSpec remains available for future contract changes. When a user explicitly selects a Superpowers workflow, committed Superpowers design and plan documents may drive that loop, but `docs/foundation/` remains the highest source of seed truth and implementation must update the affected foundation, role, test, and contract surfaces.
```

In `docs/guides/en/contributors/index.md` and `docs/guides/en/agents/index.md`, add a short workflow paragraph using the same terms. In Spanish pages, use:

```markdown
OpenSpec sigue disponible para cambios futuros de contrato. Cuando la persona usuaria selecciona explicitamente un flujo Superpowers, los documentos de diseno y plan de Superpowers confirmados pueden guiar ese ciclo, pero `docs/foundation/` sigue siendo la fuente superior de verdad inicial.
```

- [ ] **Step 5: Run test until it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py::test_guidance_surfaces_allow_user_selected_superpowers_renderer_loops -q
```

Expected: pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add tests/contracts/test_documentation_surfaces.py docs/foundation/13_truth_surfaces.md docs/foundation/16_documentation_surfaces.md docs/foundation/17_rendering_execution_plan.md README.md AGENTS.md openspec/config.yaml docs/guides/en/contributors/index.md docs/guides/en/agents/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md
git commit -m "Clarify Superpowers renderer workflow authority"
```

---

### Task 2: Learning-Science Foundation Docs

**Files:**
- Modify: `tests/contracts/test_documentation_surfaces.py`
- Modify: `tests/contracts/test_renderer_dependencies.py`
- Create: `docs/foundation/19_learning_science_principles.md`
- Create: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/foundation/00_index.md`
- Add symlinks: `docs/render-content/1_foundation/19_learning_science_principles.md`
- Add symlinks: `docs/render-content/1_foundation/20_learning_renderer_contract.md`

- [ ] **Step 1: Write failing foundation/render-content tests**

Add this test to `tests/contracts/test_documentation_surfaces.py` after `test_current_documentation_render_content_points_to_real_docs()`:

```python
def test_learning_science_foundation_pages_are_rendered() -> None:
    learning = DOCS_ROOT / "foundation" / "19_learning_science_principles.md"
    contract = DOCS_ROOT / "foundation" / "20_learning_renderer_contract.md"
    assert learning.exists()
    assert contract.exists()

    learning_text = learning.read_text(encoding="utf-8")
    contract_text = contract.read_text(encoding="utf-8")
    for needle in (
        "cognitive load",
        "retrieval practice",
        "spaced practice",
        "self-explanation",
        "universal design",
    ):
        assert needle in learning_text
    for needle in (
        "`current`",
        "`planned`",
        "`future`",
        "course shell",
        "right learning rail",
        "no personal progress",
        "no browser-side MathJax",
    ):
        assert needle in contract_text

    index = (DOCS_ROOT / "foundation" / "00_index.md").read_text(encoding="utf-8")
    assert "19_learning_science_principles.md" in index
    assert "20_learning_renderer_contract.md" in index

    render_content = DOCS_ROOT / "render-content" / "1_foundation"
    assert (render_content / "19_learning_science_principles.md").resolve() == learning.resolve()
    assert (render_content / "20_learning_renderer_contract.md").resolve() == contract.resolve()
```

Add this test to `tests/contracts/test_renderer_dependencies.py` after `test_role_docs_cover_skin_profiles_and_style_guide()`:

```python
def test_role_docs_cover_learning_science_course_shell() -> None:
    required = {
        "docs/guides/en/professors/index.md": [
            "learning-science",
            "course shell",
            "retrieval practice",
            "prerequisites",
        ],
        "docs/guides/en/contributors/index.md": [
            "learning renderer contract",
            "current",
            "planned",
            "future",
            "no browser-side MathJax",
        ],
        "docs/guides/en/students/index.md": [
            "course map",
            "learning rail",
            "OpenDyslexic",
            "personal progress",
        ],
        "docs/guides/en/agents/index.md": [
            "course shell",
            "right learning rail",
            "no inferred goals",
            "render-debug",
        ],
        "docs/guides/es/profesores/index.md": [
            "ciencia del aprendizaje",
            "estructura del curso",
            "practica de recuperacion",
            "prerrequisitos",
        ],
        "docs/guides/es/colaboradores/index.md": [
            "contrato del renderizador de aprendizaje",
            "current",
            "planned",
            "future",
            "MathJax",
        ],
        "docs/guides/es/estudiantes/index.md": [
            "mapa del curso",
            "riel de aprendizaje",
            "OpenDyslexic",
            "progreso personal",
        ],
        "docs/guides/es/agentes/index.md": [
            "estructura del curso",
            "riel derecho",
            "metas inferidas",
            "render-debug",
        ],
    }
    for relative_path, needles in required.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{relative_path} must mention {needle}"
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py::test_learning_science_foundation_pages_are_rendered tests/contracts/test_renderer_dependencies.py::test_role_docs_cover_learning_science_course_shell -q
```

Expected: fail because the new pages and role-doc coverage do not exist yet.

- [ ] **Step 3: Create learning-science principles page**

Create `docs/foundation/19_learning_science_principles.md` with frontmatter:

```markdown
---
id: docs-learning-science-principles
title: Learning Science Principles
summary: Evidence-backed learning principles used to shape Raya static and future study experiences.
status: ready
---
```

Then include sections for:

- cognitive load management;
- coherence, signaling, and segmenting;
- retrieval practice;
- spaced practice and interleaving;
- worked examples and fading;
- self-explanation;
- metacognition/calibration;
- motivation, autonomy, relevance, and belonging;
- universal design and accessibility;
- what static HTML can and cannot honestly provide.

Use concise prose. Cite sources by name in prose without external links if necessary, for example Mayer, Sweller, Roediger and Karpicke, Dunlosky, Chi, Bjork, CAST UDL, and WCAG. Do not add external renderer dependencies.

- [ ] **Step 4: Create learning renderer contract page**

Create `docs/foundation/20_learning_renderer_contract.md` with frontmatter:

```markdown
---
id: docs-learning-renderer-contract
title: Learning Renderer Contract
summary: Current, planned, and future renderer behavior derived from learning science.
status: ready
---
```

Include a status table with these rows:

```markdown
| Capability | Status | Static renderer behavior |
| --- | --- | --- |
| Course map | `current` | Render from current navigation data. |
| Main article | `current` | Render authored content, build-time MathJax, numbered objects, static environments, callouts, tables, code, and local assets. |
| Right learning rail | `current` | Render page contents, normalized summary/status, optional estimated time/tags, stable-ID prerequisites, and previous/next links from current artifact data. |
| Reader controls | `current` | Use local OpenDyslexic resources and keyboard-reachable controls. |
| Checkpoints and goals as metadata | `planned` | Require a future source-contract change; do not infer from prose. |
| Related practice index | `planned` | Requires accepted source/artifact data. |
| Personal progress, analytics, adaptive review, spaced queues | `future` | Requires dynamic study state outside the static renderer. |
```

Include explicit non-goals:

```markdown
- no personal progress claims in static HTML;
- no inferred goals or related practice;
- no browser-side MathJax conversion;
- no external CSS, font, script, renderer, or CDN requests;
- no hidden schema change to distinguish raw `summary` or `status` presence in this loop.
```

- [ ] **Step 5: Update foundation index and render-content**

Add both new pages to `docs/foundation/00_index.md`.

Create symlinks:

```bash
ln -s ../../foundation/19_learning_science_principles.md docs/render-content/1_foundation/19_learning_science_principles.md
ln -s ../../foundation/20_learning_renderer_contract.md docs/render-content/1_foundation/20_learning_renderer_contract.md
```

- [ ] **Step 6: Update role docs**

Add concise role-specific paragraphs:

- professors: how to author page summaries, prerequisites, checkpoints as content, and practice prompts without expecting fake progress;
- contributors: current/planned/future renderer categories and no browser-side MathJax or external assets;
- students: how course map, main article, learning rail, OpenDyslexic, and static next links help reading;
- agents: exact source constraints, no inferred goals, no fake related practice, render-debug checks.

Mirror the same ideas in Spanish role pages with technical identifiers unchanged.

- [ ] **Step 7: Run tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py::test_learning_science_foundation_pages_are_rendered tests/contracts/test_renderer_dependencies.py::test_role_docs_cover_learning_science_course_shell tests/contracts/test_documentation_surfaces.py::test_current_documentation_tree_is_a_renderable_docs_course -q
```

Expected: pass.

- [ ] **Step 8: Commit**

Run:

```bash
git add tests/contracts/test_documentation_surfaces.py tests/contracts/test_renderer_dependencies.py docs/foundation/00_index.md docs/foundation/19_learning_science_principles.md docs/foundation/20_learning_renderer_contract.md docs/render-content/1_foundation/19_learning_science_principles.md docs/render-content/1_foundation/20_learning_renderer_contract.md docs/guides/en/professors/index.md docs/guides/en/contributors/index.md docs/guides/en/students/index.md docs/guides/en/agents/index.md docs/guides/es/profesores/index.md docs/guides/es/colaboradores/index.md docs/guides/es/estudiantes/index.md docs/guides/es/agentes/index.md
git commit -m "Document learning science renderer contract"
```

---

### Task 3: Static Course Shell HTML

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Write failing shell contract test**

Add this test to `tests/contracts/test_static_builder.py` near the render-fixture rich rendering test:

```python
def test_render_fixture_uses_static_learning_shell(tmp_path: Path) -> None:
    course = _copy_render_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "reader-ux" / "index.html").read_text(
        encoding="utf-8"
    )
    assert '<header class="raya-top-command-bar"' in html
    assert 'aria-label="Course tools"' in html
    assert '<nav class="raya-course-map" aria-label="Course map">' in html
    assert '<main id="raya-content" class="raya-learning-shell">' in html
    assert '<article class="raya-main-article"' in html
    assert '<aside class="raya-learning-rail" aria-label="Learning context">' in html
    assert '<section class="raya-rail-panel raya-page-summary"' in html
    assert '<section class="raya-rail-panel raya-page-status"' in html
    assert '<section class="raya-rail-panel raya-page-prerequisites"' in html
    assert "Prerequisites" in html
    assert "Raya Lucaria Render Fixture" in html
    assert 'href="../index.html"' in html
    assert "related practice" not in _visible_text(html).lower()
    assert "personal progress" not in _visible_text(html).lower()
```

- [ ] **Step 2: Write failing unresolved-prerequisite omission test**

Add this test to `tests/contracts/test_static_builder.py`:

```python
def test_learning_rail_omits_unresolved_prerequisites_without_browser_warning(
    tmp_path: Path,
) -> None:
    course = _copy_render_fixture(tmp_path)
    reader = course / "course" / "4_reader_ux" / "0_index.md"
    reader.write_text(
        reader.read_text(encoding="utf-8").replace(
            "prerequisites:\n  - render-fixture-root\n",
            "prerequisites:\n  - render-fixture-root\n  - missing-page-id\n",
        ),
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "reader-ux" / "index.html").read_text(
        encoding="utf-8"
    )
    assert "Raya Lucaria Render Fixture" in html
    assert "missing-page-id" not in html
    assert "unresolved prerequisite" not in _visible_text(html).lower()
```

If `examples/courses/render-fixture/course/4_reader_ux/0_index.md` does not already have the prerequisite frontmatter shown above, add it in Task 5 before expecting this exact replacement to work.

- [ ] **Step 3: Run failing tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell tests/contracts/test_static_builder.py::test_learning_rail_omits_unresolved_prerequisites_without_browser_warning -q
```

Expected: fail because current HTML uses `raya-site-header`, `raya-main`, `raya-article`, and `raya-support-stack` rather than the new shell regions.

- [ ] **Step 4: Refactor `_render_page()` to use shell helpers**

In `packages/static/src/raya_static/builder.py`, add helper functions below `_render_page()` or immediately above it:

```python
def _render_top_command_bar(
    *,
    course_title: str,
    accessibility_js_href: str,
) -> str:
    del accessibility_js_href
    return "\n".join(
        [
            '<header class="raya-top-command-bar" aria-label="Course tools">',
            '<div class="raya-top-command-bar-inner">',
            f'<p class="raya-course-title">{html.escape(course_title)}</p>',
            (
                '<button class="raya-font-toggle" type="button" '
                'aria-pressed="false" aria-label="Toggle OpenDyslexic font">'
                "OpenDyslexic</button>"
            ),
            "</div>",
            "</header>",
        ]
    )
```

```python
def _render_course_map(page: ContentPage, content_model: ContentModel) -> str:
    parts = ['<nav class="raya-course-map" aria-label="Course map">']
    parts.append('<p class="raya-region-title">Course Map</p>')
    parts.append("<ol>")
    for target in content_model.pages:
        href = _relative_href(page.output_path, target.output_path)
        label = html.escape(_navigation_label(target))
        current = ' aria-current="page"' if target.output_path == page.output_path else ""
        parts.append(
            f'<li><a href="{html.escape(href)}"{current}>{label}</a></li>'
        )
    parts.append("</ol>")
    parts.append("</nav>")
    return "\n".join(parts)
```

```python
def _render_learning_rail(
    *,
    page: ContentPage,
    rendered_article_html: str,
    content_model: ContentModel,
    support_panels: str,
) -> str:
    panels = [
        _render_page_contents_rail(rendered_article_html),
        _render_page_summary_rail(page),
        _render_page_status_rail(page),
        _render_estimated_time_rail(page),
        _render_tags_rail(page),
        _render_prerequisites_rail(page, content_model),
        _render_sequence_rail(page, content_model),
        support_panels,
    ]
    body = "\n".join(panel for panel in panels if panel)
    if not body:
        return ""
    return (
        '<aside class="raya-learning-rail" aria-label="Learning context">\n'
        f"{body}\n"
        "</aside>"
    )
```

```python
def _render_rail_panel(class_name: str, title: str, body: str) -> str:
    return "\n".join(
        [
            f'<section class="raya-rail-panel {html.escape(class_name)}">',
            f'<h2 class="raya-rail-title">{html.escape(title)}</h2>',
            body,
            "</section>",
        ]
    )
```

```python
def _render_page_contents_rail(rendered_article_html: str) -> str:
    match = re.search(
        r'<nav class="raya-page-toc" aria-label="Page contents">.*?</nav>',
        rendered_article_html,
        flags=re.DOTALL,
    )
    if match is None:
        return ""
    return _render_rail_panel("raya-page-contents", "On This Page", match.group(0))
```

```python
def _render_page_summary_rail(page: ContentPage) -> str:
    if not page.summary:
        return ""
    return _render_rail_panel(
        "raya-page-summary",
        "Summary",
        f"<p>{html.escape(page.summary)}</p>",
    )
```

```python
def _render_page_status_rail(page: ContentPage) -> str:
    if not page.status:
        return ""
    return _render_rail_panel(
        "raya-page-status",
        "Status",
        f'<p><span class="raya-status-chip">{html.escape(page.status)}</span></p>',
    )
```

```python
def _render_estimated_time_rail(page: ContentPage) -> str:
    if not page.estimated_time:
        return ""
    return _render_rail_panel(
        "raya-page-estimated-time",
        "Estimated Time",
        f"<p>{html.escape(page.estimated_time)}</p>",
    )
```

```python
def _render_tags_rail(page: ContentPage) -> str:
    if not page.tags:
        return ""
    tags = "".join(f"<li>{html.escape(tag)}</li>" for tag in page.tags)
    return _render_rail_panel("raya-page-tags", "Tags", f"<ul>{tags}</ul>")
```

```python
def _render_prerequisites_rail(
    page: ContentPage,
    content_model: ContentModel,
) -> str:
    items: list[str] = []
    for prerequisite_id in page.prerequisites:
        target = content_model.pages_by_id.get(prerequisite_id)
        if target is None:
            continue
        href = _relative_href(page.output_path, target.output_path)
        label = target.nav_title or target.title
        items.append(
            f'<li><a href="{html.escape(href)}">{html.escape(label)}</a></li>'
        )
    if not items:
        return ""
    return _render_rail_panel(
        "raya-page-prerequisites",
        "Prerequisites",
        "<ul>" + "".join(items) + "</ul>",
    )
```

```python
def _render_sequence_rail(page: ContentPage, content_model: ContentModel) -> str:
    sequence_nav = _render_sequence_nav(page, content_model)
    if not sequence_nav:
        return ""
    return _render_rail_panel("raya-page-next", "Next", sequence_nav)
```

Then update `_render_page()`:

- remove the top-level `nav_items` loop;
- render article HTML once into `article_html`;
- call `_render_top_command_bar()`, `_render_course_map()`, and `_render_learning_rail()`;
- wrap output with:

```python
'<main id="raya-content" class="raya-learning-shell">',
_render_course_map(page, content_model),
'<article class="raya-main-article">',
article_html,
"</article>",
learning_rail,
"</main>",
```

Keep `breadcrumbs` either inside the article above `article_html` or inside the course map. Do not remove skip link or OpenDyslexic script.

- [ ] **Step 5: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell tests/contracts/test_static_builder.py::test_learning_rail_omits_unresolved_prerequisites_without_browser_warning tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages -q
```

Expected: pass after implementation. If `test_render_fixture_builds_rich_static_pages` still expects the old TOC location, update it to assert the TOC exists in `raya-learning-rail`.

- [ ] **Step 6: Commit**

Run:

```bash
git add packages/static/src/raya_static/builder.py tests/contracts/test_static_builder.py
git commit -m "Render static learning shell regions"
```

---

### Task 4: Shell CSS, Accessibility, And Responsive Layout

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Write failing browser layout/accessibility test**

Add this test to `tests/e2e/test_preview_static_read_path.py` near the existing render-fixture browser tests:

```python
def test_render_fixture_learning_shell_layout_and_accessibility(
    tmp_path: Path,
) -> None:
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
                for viewport in ({"width": 1280, "height": 900}, {"width": 390, "height": 844}):
                    page = browser.new_page(viewport=viewport)
                    try:
                        page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                        _assert_no_horizontal_overflow(page)
                        assert page.locator("header.raya-top-command-bar").bounding_box()
                        assert page.locator("nav.raya-course-map").bounding_box()
                        assert page.locator("article.raya-main-article").bounding_box()
                        assert page.locator("aside.raya-learning-rail").bounding_box()
                        assert page.locator("button.raya-font-toggle").get_attribute("aria-label") == "Toggle OpenDyslexic font"
                        page.keyboard.press("Tab")
                        focused = page.evaluate("() => document.activeElement && document.activeElement.className")
                        assert "raya-skip-link" in focused or "raya-font-toggle" in focused
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Write failing CSS contract test**

Add assertions to `tests/contracts/test_static_builder.py` in the rich CSS test section or create a new test:

```python
def test_rich_css_defines_learning_shell_regions(tmp_path: Path) -> None:
    course = _copy_render_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    css = (
        course / "artifact" / "site" / "_raya" / "render" / "rich.css"
    ).read_text(encoding="utf-8")
    for selector in (
        ".raya-top-command-bar",
        ".raya-learning-shell",
        ".raya-course-map",
        ".raya-main-article",
        ".raya-learning-rail",
        ".raya-rail-panel",
        ".raya-status-chip",
        ".raya-font-toggle:focus-visible",
    ):
        assert selector in css
    assert "grid-template-columns: minmax(14rem, 18rem) minmax(0, 1fr) minmax(16rem, 22rem);" in css
    assert "@media (max-width: 900px)" in css
```

- [ ] **Step 3: Run failing tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_shell_layout_and_accessibility -q
```

Expected: fail before CSS is updated.

- [ ] **Step 4: Update `rich_render_css()`**

In `packages/static/src/raya_static/rendering.py`, replace old `.raya-site-header`, `.raya-main`, `.raya-article`, `.raya-support-stack`, and mobile rules with new shell rules. Keep existing numbered-object, math, code, callout, reference, inspection, and proof rules.

Add these CSS blocks inside the `base` string:

```css
:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-top-command-bar {
  background: var(--raya-color-surface);
  border-bottom: 1px solid var(--raya-color-border);
  position: sticky;
  top: 0;
  z-index: 5;
}
.raya-top-command-bar-inner,
.raya-learning-shell,
.raya-page-footer,
.raya-inspection-main {
  margin: 0 auto;
  max-width: 110rem;
  padding: var(--raya-space-page);
}
.raya-top-command-bar-inner {
  align-items: center;
  display: flex;
  gap: 1rem;
  justify-content: space-between;
}
.raya-font-toggle {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-accent);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  cursor: pointer;
  font: inherit;
  font-weight: 700;
  padding: 0.5rem 0.75rem;
}
.raya-learning-shell {
  align-items: start;
  display: grid;
  gap: calc(var(--raya-space-block) * 1.25);
  grid-template-columns: minmax(14rem, 18rem) minmax(0, 1fr) minmax(16rem, 22rem);
}
.raya-course-map,
.raya-main-article,
.raya-learning-rail,
.raya-inspection-main {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  min-width: 0;
}
.raya-course-map,
.raya-learning-rail {
  position: sticky;
  top: 5rem;
}
.raya-course-map,
.raya-main-article,
.raya-learning-rail,
.raya-inspection-main {
  padding: var(--raya-space-panel);
}
.raya-region-title,
.raya-rail-title {
  font-family: var(--raya-font-heading), var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.875rem;
  font-weight: 700;
  margin: 0 0 0.75rem;
}
.raya-course-map ol,
.raya-learning-rail ul {
  margin: 0;
  padding-left: 1.25rem;
}
.raya-course-map a {
  border-left: 3px solid transparent;
  display: block;
  padding: 0.25rem 0 0.25rem 0.5rem;
  text-decoration: none;
}
.raya-course-map a[aria-current="page"] {
  border-left-color: var(--raya-color-success);
  color: var(--raya-color-success);
  font-weight: 700;
}
.raya-main-article > :first-child,
.raya-inspection-main > :first-child {
  margin-top: 0;
}
.raya-learning-rail {
  display: grid;
  gap: var(--raya-space-block);
}
.raya-rail-panel {
  border-bottom: 1px solid var(--raya-color-border);
  padding-bottom: var(--raya-space-block);
}
.raya-rail-panel:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}
.raya-status-chip {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  display: inline-block;
  font-size: 0.8125rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
}
```

Add responsive rules:

```css
@media (max-width: 900px) {
  .raya-learning-shell {
    display: block;
  }
  .raya-course-map,
  .raya-learning-rail {
    margin-bottom: 1rem;
    position: static;
  }
  .raya-learning-rail {
    margin-top: 1rem;
  }
}
@media (max-width: 520px) {
  .raya-top-command-bar-inner,
  .raya-learning-shell,
  .raya-page-footer,
  .raya-inspection-main {
    padding: 0.75rem;
  }
  .raya-top-command-bar-inner {
    align-items: stretch;
    display: grid;
  }
}
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_shell_layout_and_accessibility tests/e2e/test_preview_static_read_path.py::test_rendered_surfaces_have_no_obvious_layout_overlap_at_viewports -q
```

Expected: pass. If the reference-fixture overlap test still checks old selectors `article.raya-article` and `aside.raya-support-stack`, update it to check `article.raya-main-article` and `aside.raya-learning-rail`.

- [ ] **Step 6: Commit**

Run:

```bash
git add packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Style responsive learning shell"
```

---

### Task 5: Render Fixture Learning Context

**Files:**
- Modify: `examples/courses/render-fixture/course/0_index.md`
- Modify: `examples/courses/render-fixture/course/4_reader_ux/0_index.md`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write failing fixture metadata test**

Add this test to `tests/contracts/test_static_builder.py`:

```python
def test_render_fixture_reader_page_exercises_learning_rail_metadata(
    tmp_path: Path,
) -> None:
    course = _copy_render_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    pages = json.loads((course / "artifact" / "data" / "pages.json").read_text(encoding="utf-8"))
    reader = next(
        page for page in pages["pages"] if page["quantum_id"] == "render-fixture-reader-ux"
    )
    assert reader["estimated_time"] == "15 minutes"
    assert reader["tags"] == ["reading", "navigation", "accessibility"]
    assert reader["prerequisites"] == ["render-fixture-root"]

    html = (course / "artifact" / "site" / "reader-ux" / "index.html").read_text(
        encoding="utf-8"
    )
    assert "15 minutes" in html
    assert "reading" in html
    assert "navigation" in html
    assert "accessibility" in html
```

- [ ] **Step 2: Run failing test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_reader_page_exercises_learning_rail_metadata -q
```

Expected: fail if the fixture page lacks these metadata fields or the rail does not display them.

- [ ] **Step 3: Update fixture frontmatter**

In `examples/courses/render-fixture/course/0_index.md`, ensure the root page has:

```yaml
id: render-fixture-root
```

In `examples/courses/render-fixture/course/4_reader_ux/0_index.md`, ensure frontmatter includes:

```yaml
id: render-fixture-reader-ux
summary: Reader UX fixture for course-shell navigation, learning rail context, static environments, and accessibility checks.
estimated_time: 15 minutes
tags:
  - reading
  - navigation
  - accessibility
prerequisites:
  - render-fixture-root
```

Do not add goals, progress, or related-practice metadata.

- [ ] **Step 4: Add authored examples inside the reader page**

In `examples/courses/render-fixture/course/4_reader_ux/0_index.md`, add concise authored sections using existing syntax:

```markdown
## Orientation Checkpoint

> [!TIP]
> Before reading, identify the current page in the course map and the immediate next page link.

## Static Practice Prompt

:::problem{id="reader-map-practice" title="Find the next page"}
Use the course map and learning rail to identify the next page after this reader UX fixture.
:::

:::hint{of="reader-map-practice"}
Look for the static previous/next links. No personal progress is stored.
:::

:::answer{of="reader-map-practice"}
The next page is determined by the generated course order.
:::
```

If the exact `:::problem` syntax conflicts with the current numbered-object parser, use the existing fenced numbered-object syntax already present in `3_numbered_objects/0_index.md`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_reader_page_exercises_learning_rail_metadata tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell -q
```

Expected: pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add examples/courses/render-fixture/course/0_index.md examples/courses/render-fixture/course/4_reader_ux/0_index.md tests/contracts/test_static_builder.py
git commit -m "Exercise learning rail fixture metadata"
```

---

### Task 6: Render-Debug Evidence For Course Shell

**Files:**
- Modify: `packages/cli/src/raya_cli/render_debug_report.py`
- Modify: `tests/e2e/test_render_debug_report.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify if needed: `tests/e2e/test_render_debug_parity_gate.py`

- [ ] **Step 1: Write failing render-debug report test**

Add this test to `tests/e2e/test_render_debug_report.py` near reader UX report tests:

```python
def test_render_debug_report_fails_when_learning_shell_regions_are_missing(
    tmp_path: Path,
) -> None:
    site = tmp_path / "site"
    debug = tmp_path / "debug"
    _write_basic_site(
        site,
        index_html="""
          <!doctype html>
          <html><head><link rel="stylesheet" href="_raya/render/skin.css"></head>
          <body data-raya-skin="warm-academic">
            <main><article>Missing learning shell.</article></main>
          </body></html>
        """,
        skin="warm-academic",
    )
    _write_summary(
        debug,
        pages=("index",),
        viewports=("desktop", "mobile"),
        skin="warm-academic",
    )

    report = inspect_render_debug(site_dir=site, debug_dir=debug)

    checks = {check["id"]: check for check in report["checks"]}
    assert checks["site:learning-shell:index"]["status"] == "fail"
    assert "raya-course-map" in checks["site:learning-shell:index"]["message"]
    assert "raya-learning-rail" in checks["site:learning-shell:index"]["message"]
```

- [ ] **Step 2: Write passing render-debug report test**

Add:

```python
def test_render_debug_report_passes_when_learning_shell_regions_exist(
    tmp_path: Path,
) -> None:
    site = tmp_path / "site"
    debug = tmp_path / "debug"
    _write_basic_site(
        site,
        index_html="""
          <!doctype html>
          <html><head><link rel="stylesheet" href="_raya/render/skin.css"></head>
          <body data-raya-skin="warm-academic">
            <header class="raya-top-command-bar" aria-label="Course tools"></header>
            <main id="raya-content" class="raya-learning-shell">
              <nav class="raya-course-map" aria-label="Course map"></nav>
              <article class="raya-main-article"></article>
              <aside class="raya-learning-rail" aria-label="Learning context"></aside>
            </main>
          </body></html>
        """,
        skin="warm-academic",
    )
    _write_summary(
        debug,
        pages=("index",),
        viewports=("desktop", "mobile"),
        skin="warm-academic",
    )

    report = inspect_render_debug(site_dir=site, debug_dir=debug)

    checks = {check["id"]: check for check in report["checks"]}
    assert checks["site:learning-shell:index"]["status"] == "pass"
```

- [ ] **Step 3: Run failing tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_render_debug_report.py::test_render_debug_report_fails_when_learning_shell_regions_are_missing tests/e2e/test_render_debug_report.py::test_render_debug_report_passes_when_learning_shell_regions_exist -q
```

Expected: fail because report inspection does not check shell regions yet.

- [ ] **Step 4: Implement report inspection**

In `packages/cli/src/raya_cli/render_debug_report.py`, add a helper:

```python
def _inspect_learning_shell(site_dir: Path, report: dict[str, Any], *, context: str) -> None:
    for html_path in sorted(path for path in site_dir.rglob("*.html") if "_raya" not in path.parts):
        page_name = _page_name_for_html(site_dir, html_path)
        text = html_path.read_text(encoding="utf-8")
        missing = [
            selector
            for selector in (
                "raya-top-command-bar",
                "raya-learning-shell",
                "raya-course-map",
                "raya-main-article",
                "raya-learning-rail",
            )
            if selector not in text
        ]
        _add_check(
            report,
            check_id=f"{context}:learning-shell:{page_name}",
            status="fail" if missing else "pass",
            message=(
                "missing learning shell regions: " + ", ".join(missing)
                if missing
                else f"learning shell regions present for {page_name}"
            ),
            path=str(html_path),
            next_action=(
                "Rebuild the course with the static learning shell renderer."
                if missing
                else None
            ),
        )
```

Call it from `inspect_render_debug()` after site CSS/resource checks:

```python
_inspect_learning_shell(site_dir, report, context="site")
```

Use the existing `_add_check` and page-name helper patterns in the file. If no `_page_name_for_html()` exists, add:

```python
def _page_name_for_html(site_dir: Path, html_path: Path) -> str:
    relative = html_path.relative_to(site_dir)
    if relative.name == "index.html":
        if len(relative.parts) == 1:
            return "index"
        return relative.parts[-2]
    return relative.with_suffix("").as_posix().replace("/", "-")
```

- [ ] **Step 5: Update screenshot expectations if page list changed**

If Task 5 causes `authoring-matrix` to be included by `_available_page_names()`, update expected screenshot sets in `tests/e2e/test_preview_static_read_path.py`. Do not remove current math/static parity checks.

- [ ] **Step 6: Run focused render-debug tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_render_debug_report.py::test_render_debug_report_fails_when_learning_shell_regions_are_missing tests/e2e/test_render_debug_report.py::test_render_debug_report_passes_when_learning_shell_regions_exist tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary -q
```

Expected: pass.

- [ ] **Step 7: Commit**

Run:

```bash
git add packages/cli/src/raya_cli/render_debug_report.py tests/e2e/test_render_debug_report.py tests/e2e/test_preview_static_read_path.py tests/e2e/test_render_debug_parity_gate.py
git commit -m "Inspect learning shell in render debug"
```

If `tests/e2e/test_render_debug_parity_gate.py` was not modified, omit it from `git add`.

---

### Task 7: Full Verification And Code Review

**Files:**
- Modify: this plan only if execution status needs to be recorded

- [ ] **Step 1: Run focused contract tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py tests/contracts/test_renderer_dependencies.py tests/contracts/test_static_builder.py -q
```

Expected: pass.

- [ ] **Step 2: Run focused e2e tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py tests/e2e/test_render_debug_report.py tests/e2e/test_render_debug_parity_gate.py -q
```

Expected: pass. If local Chromium is unavailable, run the Docker command in Step 4 and record the local browser limitation.

- [ ] **Step 3: Build docs and render fixture locally**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate docs
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build docs
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya artifacts inspect docs/artifact
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate examples/courses/render-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya artifacts inspect examples/courses/render-fixture/artifact
```

Expected: all commands exit 0.

- [ ] **Step 4: Run canonical gates**

Run:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both exit 0. Run sequentially because both may prepare local Node/MathJax dependencies.

- [ ] **Step 5: Manual preview with render debug**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --render-debug /tmp/raya-learning-shell-debug
```

Expected:

- CLI prints a local preview URL and render debug output path.
- Open `index.html`, `reader-ux/index.html`, and `/tmp/raya-learning-shell-debug/index.html`.
- Desktop view shows top command bar, left course map, main article, and right learning rail without horizontal overflow.
- Mobile/narrow view stacks regions without horizontal overflow.
- OpenDyslexic button changes computed body font.
- Debug report shows no external requests and no raw TeX leakage.

- [ ] **Step 6: Request code review**

Use `superpowers:requesting-code-review` with:

```text
Review commits after 698e21d.

Focus areas:
- Superpowers/OpenSpec workflow authority wording does not weaken docs/foundation authority.
- Learning-science docs separate current, planned, and future behavior honestly.
- Static shell uses current artifact data only and does not infer goals, related practice, assignments, or personal progress.
- Prerequisite rail entries render only stable page IDs resolved through the artifact page index.
- No browser-side MathJax, CDN, external fonts, external CSS, or runtime fetches were introduced.
- Desktop 1280x900 and mobile 390x844 layout/accessibility checks are meaningful.
- English and Spanish role docs are separate and consistent.
```

- [ ] **Step 7: Receive review and patch only verified issues**

If review feedback arrives, use `superpowers:receiving-code-review`. Verify each finding against the codebase before patching. Commit each focused fix.

- [ ] **Step 8: Final status**

Run:

```bash
git status --short --branch
git log --oneline -8
```

Expected: clean working tree on `new_rayalucaria`, with implementation commits ahead of `origin/new_rayalucaria`.

After review and verification, use `superpowers:finishing-a-development-branch` before merge/push decisions unless the user explicitly gives a different integration command.

---

## Self-Review Checklist

- Spec coverage: Tasks 1-2 cover foundation/guidance docs; Tasks 3-4 cover shell regions, current-data-only right rail, accessibility, and responsive layout; Task 5 covers fixture examples; Task 6 covers render-debug evidence; Task 7 covers verification and review.
- Current/planned/future boundary: The plan does not implement goals metadata, related-practice indexes, personal progress, analytics, adaptive review, or spaced queues.
- Static parity: The plan keeps local CSS/JS/font/MathJax resources and adds render-debug checks without external requests.
- Metadata contract: The plan uses normalized `summary/status`, optional `estimated_time/tags`, and stable-ID-only `prerequisites`.
- Placeholder scan: No task depends on an unspecified implementation step; any conditional branch names the exact fallback.
