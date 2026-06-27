# Graph Key Objects Inspector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Show selected-page public key objects in the static Graph inspector with local anchor links back to the owning lesson.

**Architecture:** Reuse existing public search-section data generated during build. Embed sanitized `key_objects` in the graph browser payload only, render the inspector section with local JavaScript, and style it as a compact graph detail block.

**Tech Stack:** Python static builder, generated HTML/CSS, local vanilla JavaScript, pytest, Playwright.

---

### Task 1: Contract and Static Payload Tests

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Clarify the foundation contract**

Add one sentence to the paragraph that begins `Generated Search and Graph cards/details may show public page metadata`:

```markdown
Graph selected-page details may also show generated public section/object anchor jump links for the selected page, including numbered objects and proofs, when those anchors already exist in the rendered public article/search surface.
```

- [x] **Step 2: Write failing contract assertions**

In `test_build_writes_local_visual_graph_surface`, assert that graph HTML contains the key-object placeholder and that the embedded `raya-graph-data` payload gives `reader-ux` key objects with local anchor URLs and no private fields.

Expected assertions:

```python
assert "data-raya-graph-detail-key-objects" in graph_html
assert "data-raya-graph-detail-key-object-list" in graph_html
assert "Key objects" in graph_html
payload = _json_from_script(graph_html, "raya-graph-data")
reader_node = next(node for node in payload["nodes"] if node["id"] == "reader-ux")
key_objects = reader_node["key_objects"]
assert key_objects
assert any(item["title"].startswith("Definition 4.1") for item in key_objects)
assert any(item["kind"] == "proof" for item in key_objects)
assert all(item["url"].startswith("../../reader-ux/index.html#") for item in key_objects)
assert all("source_path" not in item for item in key_objects)
assert "GRAPH_SECRET_ANSWER" not in json.dumps(payload)
```

- [x] **Step 3: Run RED contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: FAIL because the placeholder and `key_objects` payload do not exist yet.

### Task 2: Browser Inspector Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Extend focused graph e2e test**

In `test_graph_page_focus_exposes_return_to_reading_path`, capture the selected inspector `Key objects` section on desktop and mobile.

Expected desktop probe fields:

```javascript
const keyObjects = document.querySelector('[data-raya-graph-detail-key-objects]');
const keyObjectLinks = Array.from(
  keyObjects?.querySelectorAll('[data-raya-graph-detail-key-object-list] a') || []
).map((link) => ({
  text: link.textContent.trim(),
  href: link.getAttribute('href'),
  width: link.getBoundingClientRect().width,
}));
```

Expected Python assertions:

```python
assert desktop_state["keyObjects"] is not None
assert "Key objects" in desktop_state["keyObjectsText"]
assert any(link["text"].startswith("Definition 4.1") for link in desktop_state["keyObjectLinks"])
assert any("Proof" in link["text"] for link in desktop_state["keyObjectLinks"])
assert all(link["href"].startswith("../../reader-ux/index.html#") for link in desktop_state["keyObjectLinks"])
assert all(link["width"] <= 360 for link in desktop_state["keyObjectLinks"])
assert mobile_state["keyObjects"] is not None
assert mobile_state["keyObjects"]["width"] <= 390
assert "Key objects" in mobile_state["text"]
```

- [x] **Step 2: Run RED e2e test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_graph_page_focus_exposes_return_to_reading_path
```

Expected: FAIL because the graph inspector does not render key objects yet.

### Task 3: Builder Payload and Inspector Placeholder

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Pass search records into graph rendering**

Thread `search_records` from the build flow into `_write_graph_surface`, `_render_graph_surface`, and `_browser_graph_payload`.

- [x] **Step 2: Add graph key-object payload helper**

Add a helper that filters public sections by `kind in {"numbered-object", "proof"}` and returns sanitized dictionaries:

```python
{
    "id": section_id,
    "anchor": anchor,
    "title": title,
    "kind": kind,
    "reference": reference,
    "url": f"{page_url}#{quote(anchor)}",
}
```

- [x] **Step 3: Add the inspector placeholder**

Inside the graph detail panel after official study objects and before relationship context, add:

```html
<section class="raya-graph-detail-key-objects" data-raya-graph-detail-key-objects hidden>
  <h3>Key objects</h3>
  <ol data-raya-graph-detail-key-object-list></ol>
</section>
```

- [x] **Step 4: Run contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: PASS for static HTML/payload assertions.

### Task 4: Graph Script Rendering and Styles

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Bind graph inspector elements**

Add selectors near the other detail selectors:

```javascript
const detailKeyObjects = document.querySelector("[data-raya-graph-detail-key-objects]");
const detailKeyObjectList = document.querySelector("[data-raya-graph-detail-key-object-list]");
```

- [x] **Step 2: Render selected-node key objects**

Add `renderDetailKeyObjects(node)` that clears the list, hides the section for no objects, and appends safe anchor rows using `textContent` and `href`.

- [x] **Step 3: Call the renderer**

Call `renderDetailKeyObjects(null)` in the empty branch of `renderDetail()`, and `renderDetailKeyObjects(node)` in the selected-node branch.

- [x] **Step 4: Style compact object links**

Add `.raya-graph-detail-key-objects`, `.raya-graph-detail-key-object-list`, and link styles that wrap long labels, preserve touch targets, and stay compact in the inspector.

- [x] **Step 5: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_graph_page_focus_exposes_return_to_reading_path
```

Expected: PASS.

### Task 5: Verification, Review, Commit, Push

**Files:**
- No additional source files expected.

- [x] **Step 1: Run static build**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
```

Expected: exit 0.

- [x] **Step 2: Run render debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: exit 0 with no overflow, no raw visible TeX leakage, no external renderer requests, and static parity checks passing.

- [x] **Step 3: Request independent code review**

Dispatch a reviewer with the diff and the design/plan paths. Fix Critical and Important findings before committing.

- [x] **Step 4: Commit**

Run:

```bash
git add docs/foundation/20_learning_renderer_contract.md docs/superpowers/specs/2026-06-27-graph-key-objects-design.md docs/superpowers/plans/2026-06-27-graph-key-objects.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph inspector key objects"
```

- [x] **Step 5: Push and refresh preview**

Run:

```bash
git push origin new_rayalucaria
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
```

Serve the refreshed `artifact/site` on the existing local static preview port or a new stable local port.
