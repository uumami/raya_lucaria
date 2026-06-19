# Local Visual Graph Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fully local static course graph page generated from the current graph index, with search, group filters, layout switching, fit/reset, and page navigation.

**Architecture:** The builder writes `artifact/site/_raya/graph/index.html` from the in-memory `graph_index` and embeds the graph payload in a JSON script tag. A new local `graph.js` resource under `_raya/render/` renders an SVG/list workspace from that embedded JSON. Artifact-root `data/graph.json` remains the manifest-declared authority.

**Tech Stack:** Python static builder, vanilla JavaScript, inline SVG, existing `rich.css` skin tokens, pytest, Playwright e2e preview checks.

---

## File Map

- Create `packages/static/src/raya_static/graph.py`
  - Owns `GRAPH_SCRIPT_NAME`, `GRAPH_RESOURCE_PATH`, and `graph_resources()`.
- Modify `packages/static/src/raya_static/builder.py`
  - Import graph resources.
  - Write `_raya/render/graph.js`.
  - Generate `_raya/graph/index.html`.
  - Add top-bar graph link to normal rendered pages.
- Modify `packages/static/src/raya_static/rendering.py`
  - Add graph workspace CSS using existing `--raya-*` tokens.
- Modify `tests/contracts/test_static_builder.py`
  - Add graph surface contract tests.
- Modify `tests/e2e/test_preview_static_read_path.py`
  - Add preview/static/browser graph page tests.

---

## Task 1: Contract Test For Generated Graph Surface

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write the failing test**

Add this test near `test_build_writes_graph_index_from_current_navigation_and_links`:

```python
def test_build_writes_local_visual_graph_surface(tmp_path: Path) -> None:
    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    site = course / "artifact" / "site"
    graph_page = site / "_raya" / "graph" / "index.html"
    graph_js = site / "_raya" / "render" / "graph.js"
    index_html = (site / "index.html").read_text(encoding="utf-8")
    graph_html = graph_page.read_text(encoding="utf-8")
    graph_script = graph_js.read_text(encoding="utf-8")

    assert graph_page.exists()
    assert graph_js.exists()
    assert 'href="_raya/graph/index.html"' in index_html
    assert 'data-raya-surface="graph"' in graph_html
    assert '<script type="application/json" id="raya-graph-data">' in graph_html
    assert 'src="../render/graph.js"' in graph_html
    assert 'href="../render/rich.css"' in graph_html
    assert 'href="../render/skin.css"' in graph_html
    assert 'href="../../data/graph.json"' not in graph_html
    assert "https://" not in graph_html
    assert "http://" not in graph_html
    assert "cytoscape" not in graph_html.lower()
    assert "graph-search" in graph_html
    assert "graph-layout" in graph_html
    assert "graph-fit" in graph_html
    assert "graph-reset" in graph_html
    assert "data-raya-graph-node" in graph_html
    assert "../index.html" in graph_html
    assert "data-raya-graph-layout" in graph_script
    assert "graph-search" in graph_script
    assert "graph-group-filter" in graph_script
    assert "graph-reset" in graph_script
    assert "window.location.href" in graph_script
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: fail because `_raya/graph/index.html` and `_raya/render/graph.js` do not exist.

---

## Task 2: Add Local Graph JavaScript Resource

**Files:**
- Create: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Create the graph resource module**

Create `packages/static/src/raya_static/graph.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


GRAPH_SCRIPT_NAME = "graph.js"
GRAPH_RESOURCE_PATH = "_raya/render"


@dataclass(frozen=True)
class GraphResources:
    javascript: str


def graph_resources() -> GraphResources:
    return GraphResources(javascript=_GRAPH_JAVASCRIPT)


_GRAPH_JAVASCRIPT = r"""
(() => {
  const root = document.querySelector("[data-raya-graph-page]");
  const dataEl = document.getElementById("raya-graph-data");
  const canvas = document.getElementById("raya-graph-canvas");
  const list = document.getElementById("raya-graph-list");
  const search = document.getElementById("graph-search");
  const layout = document.getElementById("graph-layout");
  const fit = document.getElementById("graph-fit");
  const reset = document.getElementById("graph-reset");
  const status = document.getElementById("graph-status");
  const groupFilters = Array.from(document.querySelectorAll("[data-raya-graph-group-filter]"));

  if (!root || !dataEl || !canvas || !list) {
    return;
  }

  let graph;
  try {
    graph = JSON.parse(dataEl.textContent || "{}");
  } catch {
    if (status) status.textContent = "Graph data could not be read.";
    return;
  }

  const nodes = Array.isArray(graph.nodes) ? graph.nodes : [];
  const edges = Array.isArray(graph.edges) ? graph.edges : [];
  const groups = Array.isArray(graph.groups) ? graph.groups : [];
  const hiddenGroups = new Set();
  let query = "";
  let selectedId = "";

  function normalize(value) {
    return String(value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }

  function matchesNode(node) {
    if (hiddenGroups.has(node.group || "")) return false;
    if (!query) return true;
    const haystack = normalize([node.title, node.nav_title, node.id].join(" "));
    return haystack.includes(query) || haystack.split(/\s+/).some((word) => word.startsWith(query));
  }

  function visibleNodes() {
    return nodes.filter(matchesNode);
  }

  function visibleEdges(visibleIds) {
    return edges.filter((edge) => visibleIds.has(edge.from) && visibleIds.has(edge.to));
  }

  function groupTitle(groupId) {
    const group = groups.find((item) => item.id === groupId);
    return group ? group.title : "Course";
  }

  function positionsFor(activeNodes, mode) {
    const width = 960;
    const height = 560;
    const positions = new Map();
    if (mode === "radial") {
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = Math.min(width, height) * 0.36;
      activeNodes.forEach((node, index) => {
        const angle = (Math.PI * 2 * index) / Math.max(activeNodes.length, 1) - Math.PI / 2;
        positions.set(node.id, {
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius,
        });
      });
      return { width, height, positions };
    }

    const byGroup = new Map();
    activeNodes.forEach((node) => {
      const group = node.group || "";
      if (!byGroup.has(group)) byGroup.set(group, []);
      byGroup.get(group).push(node);
    });
    const orderedGroups = Array.from(byGroup.keys()).sort((a, b) => {
      const aOrder = groups.find((group) => group.id === a)?.order || 0;
      const bOrder = groups.find((group) => group.id === b)?.order || 0;
      return aOrder - bOrder || groupTitle(a).localeCompare(groupTitle(b));
    });
    const columnWidth = width / Math.max(orderedGroups.length, 1);
    orderedGroups.forEach((groupId, groupIndex) => {
      const groupNodes = byGroup.get(groupId) || [];
      groupNodes.forEach((node, nodeIndex) => {
        positions.set(node.id, {
          x: columnWidth * groupIndex + columnWidth / 2,
          y: 80 + nodeIndex * Math.max(58, (height - 140) / Math.max(groupNodes.length, 1)),
        });
      });
    });
    return { width, height, positions };
  }

  function neighborsOf(nodeId) {
    const ids = new Set([nodeId]);
    edges.forEach((edge) => {
      if (edge.from === nodeId) ids.add(edge.to);
      if (edge.to === nodeId) ids.add(edge.from);
    });
    return ids;
  }

  function render() {
    const mode = layout ? layout.value : "map";
    root.dataset.rayaGraphLayout = mode;
    query = normalize(search ? search.value : "");
    const activeNodes = visibleNodes();
    const activeIds = new Set(activeNodes.map((node) => node.id));
    const activeEdges = visibleEdges(activeIds);
    const selectedNeighbors = selectedId ? neighborsOf(selectedId) : new Set();
    const geometry = positionsFor(activeNodes, mode);

    canvas.setAttribute("viewBox", `0 0 ${geometry.width} ${geometry.height}`);
    canvas.replaceChildren();

    activeEdges.forEach((edge) => {
      const from = geometry.positions.get(edge.from);
      const to = geometry.positions.get(edge.to);
      if (!from || !to) return;
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", String(from.x));
      line.setAttribute("y1", String(from.y));
      line.setAttribute("x2", String(to.x));
      line.setAttribute("y2", String(to.y));
      line.setAttribute("class", selectedId && (edge.from === selectedId || edge.to === selectedId) ? "raya-graph-edge is-active" : "raya-graph-edge");
      canvas.appendChild(line);
    });

    activeNodes.forEach((node) => {
      const point = geometry.positions.get(node.id);
      if (!point) return;
      const link = document.createElementNS("http://www.w3.org/2000/svg", "a");
      link.setAttribute("href", node.url);
      link.setAttribute("class", "raya-graph-node-link");
      link.dataset.rayaGraphNode = node.id;
      const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const active = !selectedId || selectedNeighbors.has(node.id);
      group.setAttribute("class", active ? "raya-graph-node" : "raya-graph-node is-muted");
      group.setAttribute("transform", `translate(${point.x} ${point.y})`);
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("r", node.id === selectedId ? "18" : "14");
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("y", "34");
      text.textContent = node.nav_title || node.title || node.id;
      group.append(circle, text);
      link.appendChild(group);
      link.addEventListener("mouseenter", () => {
        selectedId = node.id;
        render();
      });
      link.addEventListener("focus", () => {
        selectedId = node.id;
        render();
      });
      link.addEventListener("click", (event) => {
        event.preventDefault();
        window.location.href = node.url;
      });
      canvas.appendChild(link);
    });

    list.querySelectorAll("[data-raya-graph-node]").forEach((item) => {
      const id = item.getAttribute("data-raya-graph-node") || "";
      item.hidden = !activeIds.has(id);
      item.classList.toggle("is-active", id === selectedId);
    });

    if (status) {
      status.textContent = `${activeNodes.length} visible node(s), ${activeEdges.length} visible edge(s).`;
    }
  }

  if (search) search.addEventListener("input", render);
  if (layout) layout.addEventListener("change", render);
  if (fit) fit.addEventListener("click", render);
  if (reset) {
    reset.addEventListener("click", () => {
      if (search) search.value = "";
      if (layout) layout.value = "map";
      hiddenGroups.clear();
      selectedId = "";
      groupFilters.forEach((button) => {
        button.setAttribute("aria-pressed", "true");
      });
      render();
    });
  }
  groupFilters.forEach((button) => {
    button.addEventListener("click", () => {
      const group = button.getAttribute("data-raya-graph-group-filter") || "";
      if (hiddenGroups.has(group)) {
        hiddenGroups.delete(group);
        button.setAttribute("aria-pressed", "true");
      } else {
        hiddenGroups.add(group);
        button.setAttribute("aria-pressed", "false");
      }
      render();
    });
  });
  canvas.addEventListener("mouseleave", () => {
    selectedId = "";
    render();
  });

  render();
})();
"""
```

- [ ] **Step 2: Import and write the resource in builder**

In `packages/static/src/raya_static/builder.py`, add:

```python
from raya_static.graph import GRAPH_RESOURCE_PATH, GRAPH_SCRIPT_NAME, graph_resources
```

Add near `_write_shell_resources`:

```python
def _write_graph_resources(site_dir: Path, report: ValidationReport) -> None:
    resources = graph_resources()
    graph_dir = site_dir / GRAPH_RESOURCE_PATH
    graph_dir.mkdir(parents=True, exist_ok=True)
    report.wrote_output(graph_dir)
    graph_script = graph_dir / GRAPH_SCRIPT_NAME
    graph_script.write_text(resources.javascript, encoding="utf-8")
    report.wrote_output(graph_script)
```

Call it in `build_course` after `_write_shell_resources(site_dir, report)`:

```python
_write_graph_resources(site_dir, report)
```

- [ ] **Step 3: Run contract test again**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: still fail because graph page/top-bar link does not exist yet, but `graph.js` exists.

---

## Task 3: Generate Graph Page And Top-Bar Link

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add graph path constant**

Near `STATIC_INSPECTION_PATH`, add:

```python
STATIC_GRAPH_PATH = Path(STATIC_RESOURCE_DIR) / "graph" / "index.html"
```

- [ ] **Step 2: Add graph link to top command bar**

Change `_render_top_command_bar(course_title: str)` to accept `graph_href: str`, and add the link before the map toggle:

```python
def _render_top_command_bar(course_title: str, graph_href: str) -> str:
    return "\n".join(
        [
            '<header class="raya-top-command-bar" aria-label="Course tools">',
            '<div class="raya-top-command-bar-inner">',
            f'<p class="raya-course-title">{html.escape(course_title)}</p>',
            '<div class="raya-course-tools">',
            f'<a class="raya-graph-link" href="{html.escape(graph_href)}">Graph</a>',
            _render_course_map_toggle("Course map"),
            (
                '<button class="raya-font-toggle" type="button" '
                'aria-label="Toggle OpenDyslexic font" '
                'aria-pressed="false">OpenDyslexic</button>'
            ),
            "</div>",
            "</div>",
            "</header>",
        ]
    )
```

In `_render_page`, compute:

```python
graph_href = _relative_href(page.output_path, STATIC_GRAPH_PATH.as_posix())
```

and pass it to `_render_top_command_bar(course_title, graph_href)`.

- [ ] **Step 3: Add graph page writer**

Call this after `_write_inspection_surface(...)` in `build_course`:

```python
_write_graph_surface(
    site_dir=site_dir,
    content_model=content_model,
    course_title=str(config["title"]),
    language=str(config["language"]),
    graph_index=graph_index,
    skin_context=skin_context,
    report=report,
)
```

Add:

```python
def _write_graph_surface(
    *,
    site_dir: Path,
    content_model: ContentModel,
    course_title: str,
    language: str,
    graph_index: dict[str, Any],
    skin_context: SkinContext,
    report: ValidationReport,
) -> None:
    graph_path = site_dir / STATIC_GRAPH_PATH
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    report.wrote_output(graph_path.parent)
    graph_path.write_text(
        _render_graph_surface(
            content_model=content_model,
            course_title=course_title,
            language=language,
            graph_index=graph_index,
            skin_context=skin_context,
        ),
        encoding="utf-8",
    )
    report.wrote_output(graph_path)
```

- [ ] **Step 4: Add graph page renderer**

Add:

```python
def _render_graph_surface(
    *,
    content_model: ContentModel,
    course_title: str,
    language: str,
    graph_index: dict[str, Any],
    skin_context: SkinContext,
) -> str:
    stylesheet_href = _relative_href(STATIC_GRAPH_PATH.as_posix(), RENDER_STYLESHEET_PATH)
    skin_stylesheet_href = _relative_href(STATIC_GRAPH_PATH.as_posix(), SKIN_STYLESHEET_PATH)
    accessibility_css_href = _relative_href(
        STATIC_GRAPH_PATH.as_posix(),
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_CSS_NAME}",
    )
    accessibility_js_href = _relative_href(
        STATIC_GRAPH_PATH.as_posix(),
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_JS_NAME}",
    )
    graph_js_href = _relative_href(
        STATIC_GRAPH_PATH.as_posix(),
        Path(GRAPH_RESOURCE_PATH) / GRAPH_SCRIPT_NAME,
    )
    root_skin = skin_id_for_source_path(content_model.pages[0].source_path, skin_context)
    graph_payload = html.escape(json.dumps(graph_index, ensure_ascii=False), quote=False)
    group_buttons = []
    for group in graph_index["groups"]:
        group_buttons.append(
            '<button class="raya-graph-chip" type="button" '
            f'data-raya-graph-group-filter="{html.escape(group["id"], quote=True)}" '
            'aria-pressed="true">'
            f'{html.escape(group["title"])}'
            "</button>"
        )
    node_items = []
    for node in graph_index["nodes"]:
        href = _relative_href(STATIC_GRAPH_PATH.as_posix(), node["url"])
        node_items.append(
            '<li data-raya-graph-node="'
            f'{html.escape(node["id"], quote=True)}">'
            f'<a href="{html.escape(href)}">{html.escape(node["title"])}</a>'
            f'<span>{html.escape(node["status"])}</span>'
            "</li>"
        )
    return "\n".join(
        [
            "<!doctype html>",
            f'<html lang="{html.escape(language)}">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>Course Graph - {html.escape(course_title)}</title>",
            f'<link rel="stylesheet" href="{html.escape(stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(skin_stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(accessibility_css_href)}">',
            "</head>",
            f'<body data-raya-surface="graph" data-raya-skin="{html.escape(root_skin, quote=True)}">',
            '<a class="raya-skip-link" href="#raya-graph-main">Skip to graph</a>',
            '<main id="raya-graph-main" class="raya-graph-page" data-raya-graph-page>',
            '<header class="raya-graph-header">',
            f'<p class="raya-course-title">{html.escape(course_title)}</p>',
            '<a class="raya-graph-back-link" href="../../index.html">Back to course</a>',
            "<h1>Course Graph</h1>",
            "<p>Explore pages, unit groups, prerequisites, and content references generated from this course.</p>",
            "</header>",
            '<section class="raya-graph-controls" aria-label="Graph controls">',
            '<label for="graph-search">Search</label>',
            '<input id="graph-search" type="search" autocomplete="off">',
            '<label for="graph-layout">Layout</label>',
            '<select id="graph-layout"><option value="map">Map</option><option value="radial">Radial</option><option value="list">List</option></select>',
            '<button id="graph-fit" type="button">Fit</button>',
            '<button id="graph-reset" type="button">Reset</button>',
            "</section>",
            '<section class="raya-graph-groups" aria-label="Graph groups">',
            "\n".join(group_buttons),
            "</section>",
            '<p id="graph-status" class="raya-graph-status" aria-live="polite"></p>',
            '<svg id="raya-graph-canvas" class="raya-graph-canvas" role="img" aria-label="Course graph"></svg>',
            '<ol id="raya-graph-list" class="raya-graph-list">',
            "\n".join(node_items),
            "</ol>",
            '<script type="application/json" id="raya-graph-data">',
            graph_payload,
            "</script>",
            "</main>",
            f'<script src="{html.escape(accessibility_js_href)}" defer></script>',
            f'<script src="{html.escape(graph_js_href)}" defer></script>',
            "</body>",
            "</html>",
            "",
        ]
    )
```

- [ ] **Step 5: Run contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: pass after correcting any exact-string drift.

---

## Task 4: Add Graph Styling

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add CSS**

Append graph CSS near the inspection/main layout styles:

```css
.raya-graph-link,
.raya-graph-back-link {
  align-items: center;
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  display: inline-flex;
  font-weight: 700;
  min-height: 2.25rem;
  padding: 0.45rem 0.75rem;
  text-decoration: none;
}
.raya-graph-page {
  margin: 0 auto;
  max-width: 118rem;
  padding: var(--raya-space-page);
}
.raya-graph-header,
.raya-graph-controls,
.raya-graph-groups,
.raya-graph-status,
.raya-graph-canvas,
.raya-graph-list {
  margin-bottom: var(--raya-space-block);
}
.raya-graph-controls,
.raya-graph-groups {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.raya-graph-controls input,
.raya-graph-controls select,
.raya-graph-controls button,
.raya-graph-chip {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  font: inherit;
  min-height: 2.5rem;
  padding: 0.45rem 0.7rem;
}
.raya-graph-chip[aria-pressed="true"] {
  border-color: var(--raya-color-accent);
  box-shadow: inset 0 -0.2rem 0 var(--raya-color-accent);
}
.raya-graph-canvas {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  display: block;
  min-height: 34rem;
  width: 100%;
}
.raya-graph-edge {
  stroke: var(--raya-color-border);
  stroke-width: 2;
}
.raya-graph-edge.is-active {
  stroke: var(--raya-color-accent);
  stroke-width: 3;
}
.raya-graph-node circle {
  fill: var(--raya-color-accent-soft);
  stroke: var(--raya-color-accent);
  stroke-width: 2;
}
.raya-graph-node text {
  fill: var(--raya-color-text);
  font-size: 0.78rem;
  font-weight: 700;
  text-anchor: middle;
}
.raya-graph-node.is-muted {
  opacity: 0.28;
}
.raya-graph-list {
  columns: 2;
  padding-left: 1.25rem;
}
.raya-graph-list li[hidden] {
  display: none;
}
@media (max-width: 760px) {
  .raya-graph-page {
    padding: 1rem;
  }
  .raya-graph-canvas {
    min-height: 24rem;
  }
  .raya-graph-list {
    columns: 1;
  }
}
```

- [ ] **Step 2: Run contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: pass.

---

## Task 5: Add Preview Static Read Path And Browser Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing e2e test**

Add:

```python
def test_preview_serves_local_visual_graph_surface(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        base_url = handle.base_url
        assert base_url is not None
        graph_html = _fetch_text(f"{base_url}/_raya/graph/index.html")
        graph_js = _fetch_text(f"{base_url}/_raya/render/graph.js")

        assert 'data-raya-surface="graph"' in graph_html
        assert "raya-graph-data" in graph_html
        assert "https://" not in graph_html
        assert "http://" not in graph_html
        assert "cytoscape" not in graph_html.lower()
        assert "window.location.href" in graph_js

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
                        page.goto(f"{base_url}/_raya/graph/index.html", wait_until="networkidle")
                        _assert_no_horizontal_overflow(page)
                        assert page.locator("#raya-graph-canvas .raya-graph-node").count() > 0
                        before = page.locator("#raya-graph-list [data-raya-graph-node]:visible").count()
                        page.fill("#graph-search", "matrix")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-status')
                              ?.textContent
                              ?.includes('visible node')"""
                        )
                        after = page.locator("#raya-graph-list [data-raya-graph-node]:visible").count()
                        assert after <= before
                        page.select_option("#graph-layout", "radial")
                        assert page.locator("[data-raya-graph-page]").get_attribute("data-raya-graph-layout") == "radial"
                        page.click("#graph-reset")
                        assert page.locator("[data-raya-graph-page]").get_attribute("data-raya-graph-layout") == "map"
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run e2e test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: pass after implementation. If it fails, use `superpowers:systematic-debugging` before changing code.

---

## Task 6: Full Verification And Review

**Files:**
- No planned file edits.

- [ ] **Step 1: Run focused suites**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: both pass.

- [ ] **Step 2: Run broader renderer/debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: pass, no external requests, no horizontal overflow, static math still local.

- [ ] **Step 3: Request code review**

Use `superpowers:requesting-code-review` with:

- Description: Local visual graph page generated from `graph_index`.
- Requirements: this plan and `docs/superpowers/specs/2026-06-19-local-visual-graph-page-design.md`.
- Base SHA: commit before implementation.
- Head SHA: implementation commit candidate.

- [ ] **Step 4: Commit**

After addressing any Critical/Important review findings:

```bash
git add packages/static/src/raya_static/graph.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add local visual graph page"
```

---

## Self-Review

- Spec coverage: graph page, local resources, embedded graph payload, top-bar graph command, search/filter/layout/fit/reset/navigation, tests, and no-CDN invariants are covered.
- Placeholder scan: no placeholder tasks remain.
- Type consistency: graph data uses existing `nodes`, `edges`, `groups`, and `backlinks`; JavaScript uses `from`/`to` edge fields from current `graph_index`.
