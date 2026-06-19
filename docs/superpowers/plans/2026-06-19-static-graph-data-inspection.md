# Static Graph Data And Inspection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a manifest-declared, schema-validated `data/graph.json` page graph and expose compact graph diagnostics on `_raya/inspect/index.html`.

**Architecture:** Build graph data from current generated page and link authority inside `packages/static/src/raya_static/builder.py`. Validate it through a new schema helper in `packages/schema`, declare it in `manifest.json`, and show only structural inspection diagnostics in the existing inspection surface.

**Tech Stack:** Python 3.10, pytest, JSON Schema validation, current Glintstone static builder, no browser-side graph library, no CDN, no generated outputs committed.

---

## File Structure

- `tests/contracts/test_static_builder.py`
  - Add graph index contract tests.
  - Add schema failure test for malformed graph indexes.
- `packages/schema/src/raya_schema/schemas/graph-index.schema.json`
  - Validate graph index shape.
- `packages/schema/src/raya_schema/artifacts.py`
  - Add `validate_graph_index`.
  - Validate manifest-declared graph data during artifact inspection.
- `packages/schema/src/raya_schema/__init__.py`
  - Export `validate_graph_index`.
- `packages/static/src/raya_static/builder.py`
  - Build graph index from current pages and links.
  - Write `data/graph.json`.
  - Declare graph in `manifest.json`.
  - Include graph summary in `_raya/inspect/index.html`.

---

### Task 1: Contract Test For Graph Index

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add imports**

Add `validate_graph_index` to the `from raya_schema import (...)` import list in `tests/contracts/test_static_builder.py`.

- [ ] **Step 2: Add failing test**

Add this test near the artifact contract tests:

```python
def test_build_writes_graph_index_from_current_navigation_and_links(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    root_page = course / "course" / "0_index.md"
    root_page.write_text(
        root_page.read_text(encoding="utf-8")
        + "\nRead the [topic](1_unit/1_topic/0_index.md).\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    artifact = course / "artifact"
    graph_path = artifact / "data" / "graph.json"
    assert graph_path.exists()
    manifest = json.loads((artifact / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["data"]["graph"] == "data/graph.json"
    graph_report = validate_graph_index(graph_path)
    assert graph_report.ok, [diagnostic.format() for diagnostic in graph_report.diagnostics]

    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    assert graph["version"] == 1
    assert graph["course_id"] == "minimal-course"
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    assert nodes_by_id["course-root"]["title"] == "Minimal Course"
    assert nodes_by_id["course-root"]["url"] == "index.html"
    assert nodes_by_id["first-unit"]["group"] == "first-unit"
    assert nodes_by_id["first-topic"]["group"] == "first-unit"
    assert nodes_by_id["first-topic"]["tags"] == []
    edges = {(edge["from"], edge["to"], edge["kind"]) for edge in graph["edges"]}
    assert ("course-root", "first-unit", "navigation") in edges
    assert ("first-unit", "first-topic", "navigation") in edges
    assert ("first-topic", "first-unit", "parent") in edges
    assert ("first-topic", "first-unit", "prerequisite") in edges
    assert ("course-root", "first-topic", "content") in edges
    backlinks = graph["backlinks"]["first-topic"]
    assert backlinks == [
        {
            "from": "course-root",
            "title": "Minimal Course",
            "url": "index.html",
            "kind": "content",
        }
    ]
    inspection_html = (
        artifact / "site" / "_raya" / "inspect" / "index.html"
    ).read_text(encoding="utf-8")
    assert "Course Graph" in inspection_html
    assert "3 page node(s)" in inspection_html
    assert "5 graph edge(s)" in inspection_html
    assert 'href="../../data/graph.json"' in inspection_html
    assert 'href="../../unit/topic/index.html"' in inspection_html
```

- [ ] **Step 3: Run test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_graph_index_from_current_navigation_and_links -q
```

Expected: import or assertion failure because `validate_graph_index` and `data/graph.json` do not exist yet.

---

### Task 2: Graph Schema And Validator

**Files:**
- Create: `packages/schema/src/raya_schema/schemas/graph-index.schema.json`
- Modify: `packages/schema/src/raya_schema/artifacts.py`
- Modify: `packages/schema/src/raya_schema/__init__.py`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add schema**

Create `packages/schema/src/raya_schema/schemas/graph-index.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://raya-lucaria.local/schemas/graph-index.schema.json",
  "title": "Raya Graph Index",
  "type": "object",
  "required": ["version", "course_id", "nodes", "edges", "groups", "backlinks"],
  "properties": {
    "version": {"type": "integer", "const": 1},
    "course_id": {"type": "string", "minLength": 1},
    "nodes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "title", "nav_title", "url", "group", "order", "status", "tags"],
        "properties": {
          "id": {"type": "string", "minLength": 1},
          "title": {"type": "string"},
          "nav_title": {"type": "string"},
          "url": {"type": "string", "minLength": 1},
          "group": {"type": "string"},
          "order": {"type": "integer", "minimum": 1},
          "status": {"type": "string"},
          "tags": {"type": "array", "items": {"type": "string"}}
        }
      }
    },
    "edges": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["from", "to", "kind", "source"],
        "properties": {
          "from": {"type": "string", "minLength": 1},
          "to": {"type": "string", "minLength": 1},
          "kind": {"type": "string", "minLength": 1},
          "source": {"type": "string", "const": "links"}
        }
      }
    },
    "groups": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "title", "order"],
        "properties": {
          "id": {"type": "string"},
          "title": {"type": "string"},
          "order": {"type": "integer", "minimum": 1}
        }
      }
    },
    "backlinks": {
      "type": "object",
      "additionalProperties": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["from", "title", "url", "kind"],
          "properties": {
            "from": {"type": "string", "minLength": 1},
            "title": {"type": "string"},
            "url": {"type": "string", "minLength": 1},
            "kind": {"type": "string", "enum": ["content", "prerequisite"]}
          }
        }
      }
    }
  }
}
```

- [ ] **Step 2: Wire validator**

In `packages/schema/src/raya_schema/artifacts.py`, add:

```python
def validate_graph_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "graph-index.schema.json")
```

Add `"graph": validate_graph_index` to the `validators` mapping in `inspect_artifact()`.

In `packages/schema/src/raya_schema/__init__.py`, import and export `validate_graph_index`.

- [ ] **Step 3: Add malformed schema test**

Add this contract test:

```python
def test_graph_index_schema_rejects_missing_nodes(tmp_path: Path) -> None:
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(
        json.dumps(
            {
                "version": 1,
                "course_id": "broken",
                "edges": [],
                "groups": [],
                "backlinks": {},
            }
        ),
        encoding="utf-8",
    )

    report = validate_graph_index(graph_path)

    assert not report.ok
    assert any("nodes" in diagnostic.format() for diagnostic in report.diagnostics)
```

- [ ] **Step 4: Run schema test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_graph_index_schema_rejects_missing_nodes -q
```

Expected: PASS after validator wiring.

---

### Task 3: Generate Graph Data And Inspection Summary

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Implement graph builder helper**

Add `_graph_index(course_id, content_model, links_index)` near `_links_index()`:

```python
def _graph_index(
    course_id: str,
    content_model: ContentModel,
    links_index: dict[str, Any],
) -> dict[str, Any]:
    group_by_page = _graph_group_by_page(content_model)
    nodes = [
        {
            "id": page.id,
            "title": page.title,
            "nav_title": page.nav_title,
            "url": page.output_path,
            "group": group_by_page.get(page.id, ""),
            "order": index,
            "status": page.status,
            "tags": list(page.tags),
        }
        for index, page in enumerate(content_model.pages, start=1)
    ]
    edges = [
        {
            "from": link["from"],
            "to": link["to"],
            "kind": link["kind"],
            "source": "links",
        }
        for link in links_index["links"]
    ]
    groups = [
        {
            "id": page.id,
            "title": page.nav_title or page.title,
            "order": index,
        }
        for index, page in enumerate(
            (
                content_model.pages_by_id[page_id]
                for page_id in content_model.children_by_parent.get(
                    content_model.root_id or "",
                    [],
                )
            ),
            start=1,
        )
    ]
    pages_by_id = content_model.pages_by_id
    backlinks: dict[str, list[dict[str, str]]] = {
        page.id: [] for page in content_model.pages
    }
    for edge in edges:
        if edge["kind"] not in {"content", "prerequisite"}:
            continue
        source = pages_by_id.get(edge["from"])
        target = pages_by_id.get(edge["to"])
        if source is None or target is None:
            continue
        backlinks[target.id].append(
            {
                "from": source.id,
                "title": source.title,
                "url": source.output_path,
                "kind": edge["kind"],
            }
        )
    return {
        "version": 1,
        "course_id": course_id,
        "nodes": nodes,
        "edges": edges,
        "groups": groups,
        "backlinks": backlinks,
    }
```

Add `_graph_group_by_page(content_model)`:

```python
def _graph_group_by_page(content_model: ContentModel) -> dict[str, str]:
    groups: dict[str, str] = {}
    root_id = content_model.root_id
    top_level = set(content_model.children_by_parent.get(root_id or "", []))
    for page in content_model.pages:
        if page.id in top_level:
            groups[page.id] = page.id
            continue
        ancestor = page.parent_id
        selected = ""
        while ancestor:
            if ancestor in top_level:
                selected = ancestor
                break
            ancestor_page = content_model.pages_by_id.get(ancestor)
            ancestor = ancestor_page.parent_id if ancestor_page is not None else None
        groups[page.id] = selected
    return groups
```

- [ ] **Step 2: Write graph JSON and manifest entry**

After `links_index = _links_index(...)`, set:

```python
graph_index = _graph_index(course_id, content_model, links_index)
```

After writing `links.json`, write:

```python
_write_json(data_dir / "graph.json", graph_index, report)
```

Add to manifest `data`:

```python
"graph": "data/graph.json",
```

- [ ] **Step 3: Pass graph data into inspection surface**

Add `graph_index` as a parameter to `_write_inspection_surface()` and `_render_inspection_surface()`.

In the inspection HTML, add a `Course Graph` section before `Pages` that renders:

```python
graph_href = _relative_href(STATIC_INSPECTION_PATH.as_posix(), "data/graph.json")
graph_page_links = []
for node in graph_index["nodes"]:
    href = _relative_href(STATIC_INSPECTION_PATH.as_posix(), node["url"])
    graph_page_links.append(
        f'<li><a href="{html.escape(href)}">{html.escape(node["title"])}</a></li>'
    )
```

Render counts and links:

```html
<h2>Course Graph</h2>
<p>3 page node(s), 5 graph edge(s).</p>
<p><a href="../../data/graph.json">Raw graph data</a></p>
<ul>...</ul>
```

- [ ] **Step 4: Run graph contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_graph_index_from_current_navigation_and_links -q
```

Expected: PASS.

---

### Task 4: Artifact Validation And Focused Gate

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add graph validation to generated artifact contract**

In `test_generated_artifact_contract_validates`, add:

```python
validate_graph_index(artifact / "data" / "graph.json"),
```

Also assert in `test_build_minimal_fixture_into_temporary_course`:

```python
assert (artifact / "data" / "graph.json").exists()
assert manifest["data"]["graph"] == "data/graph.json"
```

- [ ] **Step 2: Run focused contracts**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_minimal_fixture_into_temporary_course tests/contracts/test_static_builder.py::test_generated_artifact_contract_validates tests/contracts/test_static_builder.py::test_build_writes_graph_index_from_current_navigation_and_links tests/contracts/test_static_builder.py::test_graph_index_schema_rejects_missing_nodes -q
```

Expected: PASS.

- [ ] **Step 3: Run static read path smoke**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_default_and_inspection_pages_have_responsive_layout_regions -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add packages/schema/src/raya_schema packages/static/src/raya_static/builder.py tests/contracts/test_static_builder.py
git commit -m "Add static graph data inspection"
```

---

## Final Verification

Run:

```bash
./scripts/check-render-debug.sh
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
```

If those pass, request code review before continuing to the later visual graph page slice.
