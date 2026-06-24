# Graph Study Objects Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show public official study objects for the selected graph page so students can move from structural context to useful work without leaking private support data.

**Architecture:** Enrich only the browser graph payload with compact public study-object summaries. Keep `data/graph.json` as the current page-node/link-edge contract, and render the summaries in the local `graph.js` inspector.

**Tech Stack:** Python static builder, embedded vanilla JavaScript graph workspace, CSS in `rich.css`, pytest, Playwright.

---

### Task 1: Contract Test For Public Graph Study Objects

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add failing assertions to `test_build_writes_local_visual_graph_surface`**

Extend the existing graph test after the `allowed_graph_node_keys` set is defined:

```python
allowed_graph_node_keys = {
    "graph_url",
    "group",
    "hierarchy_label",
    "id",
    "link_counts",
    "nav_title",
    "next_url",
    "order",
    "practice_url",
    "previous_url",
    "schedule_url",
    "search_url",
    "stable_id",
    "status",
    "study_counts",
    "study_objects",
    "summary",
    "tags",
    "tasks_url",
    "title",
    "url",
}
```

Then add assertions near the existing `authoring_node` checks:

```python
assert "data-raya-graph-detail-study-objects" in graph_html
study_objects = authoring_node["study_objects"]
assert [item["id"] for item in study_objects] == [
    "matrix-prompt",
    "matrix-assignment",
]
assert study_objects[0]["type"] == "prompt"
assert study_objects[0]["type_label"] == "Prompt"
assert study_objects[0]["title"] == "Prompt"
assert "identity matrix preserves vector norms" in study_objects[0]["preview"]
assert study_objects[0]["url"].endswith(
    "../../5_authoring_matrix/index.html#raya-official-matrix-prompt"
)
assert study_objects[1]["type"] == "assignment"
assert study_objects[1]["type_label"] == "Assignment"
assert study_objects[1]["title"] == "Matrix graph check"
assert study_objects[1]["preview"] == "Trace the graph context for matrix notation."
assert study_objects[1]["due"] == "2026-11-03"
assert study_objects[1]["url"].endswith(
    "../../5_authoring_matrix/index.html#raya-official-matrix-assignment"
)
private_graph_payload_text = json.dumps(graph_payload, sort_keys=True)
for private_token in (
    "_official",
    "source_path",
    "answer",
    "solution",
    "correct",
    "\"back\"",
):
    assert private_token not in private_graph_payload_text
```

- [ ] **Step 2: Run the focused contract test and verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: FAIL because graph nodes do not yet include `study_objects` and graph HTML lacks `data-raya-graph-detail-study-objects`.

### Task 2: Builder Payload And Inspector Placeholder

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add a public study-object summary helper**

Create a helper near `_browser_tasks_payload()` and `_official_public_task_summary()`:

```python
def _browser_graph_study_objects(
    page: Page,
    page_objects: list[dict[str, Any]],
) -> list[dict[str, str]]:
    objects: list[dict[str, str]] = []
    for item in sorted(
        page_objects,
        key=lambda item: (
            item.get("source_order")
            if isinstance(item.get("source_order"), int)
            else 0,
            str(item.get("id") or ""),
        ),
    ):
        if not isinstance(item, dict):
            continue
        object_id = str(item.get("id") or "").strip()
        object_type = str(item.get("type") or "practice").strip() or "practice"
        if not object_id:
            continue
        task_summary = _official_public_task_summary(item)
        if task_summary is not None:
            title = task_summary["title"]
            preview = task_summary["preview"]
            content_map = task_summary["content"]
        else:
            title = _official_type_label(object_type)
            preview = _official_preview_text(item)
        if not title and preview:
            title = preview
        if not preview:
            preview = title
        if not title and not preview:
            continue
        anchor = f"raya-official-{_safe_map_fragment_id(object_id)}"
        payload = {
            "id": object_id,
            "preview": preview,
            "title": title,
            "type": object_type,
            "type_label": _official_type_label(object_type),
            "url": _relative_href(STATIC_GRAPH_PATH.as_posix(), page.output_path)
            + f"#{anchor}",
        }
        if task_summary is not None:
            available = _official_public_text(content_map, ("available",))
            due = _official_public_text(content_map, ("due",))
            if available:
                payload["available"] = available
            if due:
                payload["due"] = due
        objects.append(payload)
    return objects
```

- [ ] **Step 2: Attach summaries to browser graph nodes**

In `_browser_graph_payload()`, add `"study_objects": _browser_graph_study_objects(page, page_objects),` to each node object.

- [ ] **Step 3: Add the inspector placeholder**

In `_write_graph_surface()`, below the study counts paragraph, add:

```python
(
    '<section class="raya-graph-detail-study-objects" '
    "data-raya-graph-detail-study-objects hidden>"
    "<h3>Study objects</h3>"
    "<ul data-raya-graph-detail-study-object-list></ul>"
    "</section>"
),
```

- [ ] **Step 4: Run the focused contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: PASS for payload and markup assertions.

### Task 3: Graph Inspector Rendering

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Wire DOM elements and search text**

In `graph.py`, add selectors:

```javascript
const detailStudyObjects = document.querySelector("[data-raya-graph-detail-study-objects]");
const detailStudyObjectList = document.querySelector("[data-raya-graph-detail-study-object-list]");
```

In `nodeSearchText(node)`, include public study-object text:

```javascript
Array.isArray(node.study_objects)
  ? node.study_objects.map((item) => [
      item.type_label,
      item.title,
      item.preview,
      item.due,
      item.available,
    ].join(" ")).join(" ")
  : "",
```

- [ ] **Step 2: Add renderer helper**

Add:

```javascript
function renderDetailStudyObjects(node) {
  if (!detailStudyObjects || !detailStudyObjectList) return;
  detailStudyObjectList.replaceChildren();
  const objects = Array.isArray(node && node.study_objects) ? node.study_objects : [];
  if (!objects.length) {
    detailStudyObjects.hidden = true;
    return;
  }
  objects.forEach((item) => {
    const li = document.createElement("li");
    const link = document.createElement("a");
    link.href = item.url || node.url || "#";
    link.textContent = item.title || item.preview || item.id || item.type_label || "Study object";
    const meta = document.createElement("span");
    meta.className = "raya-graph-detail-study-object-meta";
    const dateText = item.due
      ? `Due ${item.due}`
      : (item.available ? `Available ${item.available}` : "");
    meta.textContent = [item.type_label || item.type || "Study object", dateText]
      .filter(Boolean)
      .join(" · ");
    li.appendChild(link);
    li.appendChild(meta);
    if (item.preview && item.preview !== link.textContent) {
      const preview = document.createElement("span");
      preview.className = "raya-graph-detail-study-object-preview";
      preview.textContent = item.preview;
      li.appendChild(preview);
    }
    detailStudyObjectList.appendChild(li);
  });
  detailStudyObjects.hidden = false;
}
```

Call `renderDetailStudyObjects(null);` in the no-selection branch and `renderDetailStudyObjects(node);` in the selected-node branch.

- [ ] **Step 3: Style compact rows**

In `rendering.py`, near `.raya-graph-detail-study-counts`, add CSS for:

```css
.raya-graph-detail-study-objects {
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  margin: 0.75rem 0;
  padding: 0.65rem;
}
.raya-graph-detail-study-objects h3 {
  font-size: 0.95rem;
  margin: 0 0 0.45rem;
}
.raya-graph-detail-study-objects ul {
  display: grid;
  gap: 0.55rem;
  list-style: none;
  margin: 0;
  padding: 0;
}
.raya-graph-detail-study-objects li {
  border-left: 0.2rem solid var(--raya-color-accent);
  display: grid;
  gap: 0.18rem;
  padding-left: 0.55rem;
}
.raya-graph-detail-study-object-meta,
.raya-graph-detail-study-object-preview {
  color: var(--raya-color-muted);
  font-size: 0.85rem;
}
```

- [ ] **Step 4: Run focused contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: PASS.

### Task 4: Browser Behavior Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add e2e assertions**

Inside `test_preview_serves_local_visual_graph_surface`, after the selected-page detail assertions for `authoring-matrix`, assert:

```python
study_objects = page.locator("[data-raya-graph-detail-study-objects]")
assert study_objects.is_visible()
assert study_objects.locator("a", has_text="Matrix graph check").is_visible()
assert study_objects.locator("text=Assignment · Due 2026-11-03").is_visible()
assert study_objects.locator(
    "text=Trace the graph context for matrix notation."
).is_visible()
assert study_objects.locator("a", has_text="Matrix graph check").evaluate(
    "node => node.href"
).endswith("/5_authoring_matrix/index.html#raya-official-matrix-assignment")
page.fill("#graph-search", "matrix graph check")
assert page.locator("#raya-graph-list [data-raya-graph-node='authoring-matrix']").is_visible()
```

- [ ] **Step 2: Run focused e2e test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: PASS.

### Task 5: Verification And Review

**Files:**
- No new source files.

- [ ] **Step 1: Run focused contract and e2e tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: both tests PASS.

- [ ] **Step 2: Run render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS.

- [ ] **Step 3: Request code review**

Use `superpowers:requesting-code-review` with one reviewer focused on private data leaks and static contract, and one reviewer focused on browser UX/accessibility.

- [ ] **Step 4: Run archive gate**

Run:

```bash
./scripts/check.sh
```

Expected: PASS.

- [ ] **Step 5: Commit and push**

Run:

```bash
git status --short
git add docs/superpowers/specs/2026-06-24-graph-study-objects-design.md docs/superpowers/plans/2026-06-24-graph-study-objects.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Expose graph study objects"
git push origin new_rayalucaria
```

Expected: commit succeeds and branch pushes.

## Self-Review

- Spec coverage: public graph inspector objects, no schema change, no private leaks, local-only behavior, and focused verification are covered.
- Placeholder scan: no TODO/TBD placeholders.
- Type consistency: the payload uses `study_objects`, `type_label`, `title`, `preview`, `url`, `due`, and `available` consistently across builder, JS, and tests.
