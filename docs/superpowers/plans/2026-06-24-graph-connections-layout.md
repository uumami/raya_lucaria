# Graph Connections Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic default `Connections` layout to the static Course graph while preserving existing `Map`, `Radial`, and `List` modes.

**Architecture:** Keep the current embedded graph payload and local SVG renderer. Add one layout option in the static builder, local JavaScript helpers for normalized layout edges and connection depths in `graph.py`, focused contract and browser tests, and role/foundation documentation updates. No schema, data-fetching, storage, or external graph library changes.

**Tech Stack:** Python static builder, local JavaScript string in `packages/static/src/raya_static/graph.py`, pytest contract tests, Playwright e2e tests, Markdown docs.

---

### Task 1: Contract Test

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write failing layout option assertions**

In `test_build_writes_local_visual_graph_surface`, near the existing graph HTML
assertions for layout/search controls, add:

```python
assert '<option value="connections" selected>Connections</option>' in graph_html
assert '<option value="map">Map</option>' in graph_html
assert '<option value="radial">Radial</option>' in graph_html
assert '<option value="list">List</option>' in graph_html
```

- [ ] **Step 2: Write failing graph script assertions**

In the same test, near the existing graph script assertions, add:

```python
assert "connectionDepthsFor" in graph_script
assert "layoutEdgesFor" in graph_script
assert 'mode === "connections"' in graph_script
assert "incomingByNode" in graph_script
assert "outgoingByNode" in graph_script
```

- [ ] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: FAIL because the `connections` option and script helper do not exist.

### Task 2: Browser Behavior Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write a helper to read SVG node coordinates**

Near the existing `_viewbox_width` helper functions, add:

```python
def _graph_node_translate(page, node_id: str) -> tuple[float, float]:
    transform = page.locator(
        f'#raya-graph-canvas [data-raya-graph-node="{node_id}"] g'
    ).get_attribute("transform")
    assert transform is not None
    match = re.search(r"translate\(([-0-9.]+)\s+([-0-9.]+)\)", transform)
    assert match is not None
    return float(match.group(1)), float(match.group(2))
```

This file already imports `re`; do not add a duplicate import.

- [ ] **Step 2: Write failing default layout assertions**

In `test_preview_serves_local_visual_graph_surface`, after the initial graph
page load and before changing layout controls, add:

```python
assert page.locator("#graph-layout").input_value() == "connections"
assert (
    page.locator("[data-raya-graph-page]").get_attribute(
        "data-raya-graph-layout"
    )
    == "connections"
)
root_x, _ = _graph_node_translate(page, "render-root")
static_x, _ = _graph_node_translate(page, "static-path")
matrix_x, _ = _graph_node_translate(page, "authoring-matrix")
assert root_x < static_x
assert root_x < matrix_x
```

- [ ] **Step 3: Update existing layout switch assertions**

Where the test currently switches from `radial` to `list` and then back to
`map`, keep those checks and add a `connections` check before `map`:

```python
page.select_option("#graph-layout", "connections")
assert (
    page.locator("[data-raya-graph-page]").get_attribute(
        "data-raya-graph-layout"
    )
    == "connections"
)
page.select_option("#graph-layout", "map")
```

- [ ] **Step 4: Update reset expectation**

Where the test asserts Reset returns `data-raya-graph-layout` to `"map"`, change
the expected value to `"connections"`:

```python
assert (
    page.locator("[data-raya-graph-page]").get_attribute(
        "data-raya-graph-layout"
    )
    == "connections"
)
```

- [ ] **Step 5: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: FAIL because the default layout is still `map` and the
`connections` option does not exist.

### Task 3: Static Builder Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add the layout option**

In `_render_graph_surface`, replace the current layout select options:

```html
<option value="map">Map</option>
<option value="radial">Radial</option>
<option value="list">List</option>
```

with:

```html
<option value="connections" selected>Connections</option>
<option value="map">Map</option>
<option value="radial">Radial</option>
<option value="list">List</option>
```

- [ ] **Step 2: Verify contract RED changes to script-only failure**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: FAIL only on missing graph script helper assertions.

### Task 4: Local Graph Layout Script

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [ ] **Step 1: Add stable node sorting helper**

Before `positionsFor(activeNodes, mode)`, add:

```javascript
function compareNodesByOrder(a, b) {
  const aOrder = Number(a.order || 0);
  const bOrder = Number(b.order || 0);
  return aOrder - bOrder ||
    String(a.title || a.nav_title || a.id).localeCompare(String(b.title || b.nav_title || b.id)) ||
    String(a.id).localeCompare(String(b.id));
}
```

- [ ] **Step 2: Add normalized layout-edge helper**

After `compareNodesByOrder`, add:

```javascript
function layoutEdgesFor(activeNodes) {
  const activeIds = new Set(activeNodes.map((node) => node.id));
  const seen = new Set();
  const layoutEdges = [];
  edges.forEach((edge) => {
    if (!activeIds.has(edge.from) || !activeIds.has(edge.to)) return;
    if (edge.kind === "parent") return;
    const fromNode = nodesById.get(edge.from);
    const toNode = nodesById.get(edge.to);
    const fromOrder = Number(fromNode ? fromNode.order || 0 : 0);
    const toOrder = Number(toNode ? toNode.order || 0 : 0);
    let from = edge.from;
    let to = edge.to;
    if (fromOrder > toOrder) {
      if (edge.kind !== "content" && edge.kind !== "prerequisite") return;
      from = edge.to;
      to = edge.from;
    }
    const key = `${from}\u0000${to}`;
    if (seen.has(key)) return;
    seen.add(key);
    layoutEdges.push({ from, to });
  });
  return layoutEdges;
}
```

- [ ] **Step 3: Add connection depth helper**

After `layoutEdgesFor`, add:

```javascript
function connectionDepthsFor(activeNodes) {
  const incomingByNode = new Map(activeNodes.map((node) => [node.id, []]));
  const outgoingByNode = new Map(activeNodes.map((node) => [node.id, []]));
  const layoutEdges = layoutEdgesFor(activeNodes);
  layoutEdges.forEach((edge) => {
    incomingByNode.get(edge.to).push(edge.from);
    outgoingByNode.get(edge.from).push(edge.to);
  });

  const orderedNodes = activeNodes.slice().sort(compareNodesByOrder);
  let roots = orderedNodes.filter((node) => (incomingByNode.get(node.id) || []).length === 0);
  if (roots.length === 0 && orderedNodes.length > 0) {
    roots = [orderedNodes[0]];
  }

  const depths = new Map();
  roots.forEach((node) => depths.set(node.id, 0));
  const queue = roots.map((node) => node.id);
  while (queue.length > 0) {
    const id = queue.shift();
    const baseDepth = depths.get(id) || 0;
    (outgoingByNode.get(id) || []).forEach((targetId) => {
      if (!depths.has(targetId)) {
        depths.set(targetId, baseDepth + 1);
        queue.push(targetId);
      }
    });
  }

  for (let pass = 0; pass < activeNodes.length; pass += 1) {
    let changed = false;
    layoutEdges.forEach((edge) => {
      if (!depths.has(edge.from)) return;
      const nextDepth = (depths.get(edge.from) || 0) + 1;
      const currentDepth = depths.has(edge.to) ? depths.get(edge.to) : -1;
      if (nextDepth > currentDepth && nextDepth <= activeNodes.length) {
        depths.set(edge.to, nextDepth);
        changed = true;
      }
    });
    if (!changed) break;
  }

  orderedNodes.forEach((node) => {
    if (depths.has(node.id)) return;
    const incomingDepths = (incomingByNode.get(node.id) || [])
      .filter((id) => depths.has(id))
      .map((id) => (depths.get(id) || 0) + 1);
    depths.set(node.id, incomingDepths.length ? Math.min(...incomingDepths) : 0);
  });

  return { depths, incomingByNode, outgoingByNode };
}
```

- [ ] **Step 4: Add connections branch to `positionsFor`**

At the start of `positionsFor(activeNodes, mode)`, after width/height/positions
are declared and before the radial branch, add:

```javascript
if (mode === "connections") {
  const { depths } = connectionDepthsFor(activeNodes);
  const byDepth = new Map();
  activeNodes.forEach((node) => {
    const depth = depths.get(node.id) || 0;
    if (!byDepth.has(depth)) byDepth.set(depth, []);
    byDepth.get(depth).push(node);
  });
  const orderedDepths = Array.from(byDepth.keys()).sort((a, b) => a - b);
  const columnWidth = width / Math.max(orderedDepths.length, 1);
  orderedDepths.forEach((depth, depthIndex) => {
    const columnNodes = (byDepth.get(depth) || []).slice().sort(compareNodesByOrder);
    const rowGap = Math.max(64, (height - 140) / Math.max(columnNodes.length, 1));
    columnNodes.forEach((node, nodeIndex) => {
      positions.set(node.id, {
        x: columnWidth * depthIndex + columnWidth / 2,
        y: 80 + nodeIndex * rowGap,
      });
    });
  });
  return { width, height, positions };
}
```

- [ ] **Step 5: Make reset return to connections**

In the reset handler, change:

```javascript
if (layout) layout.value = "map";
```

to:

```javascript
if (layout) layout.value = "connections";
```

- [ ] **Step 6: Verify focused tests pass**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: PASS.

### Task 5: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update the foundation contract**

In the static graph paragraph, mention `Connections` as the default
deterministic relationship layout and preserve the non-goal language:

```markdown
The default `Connections` layout may arrange visible pages by explicit graph
relationships and course order so students can read link flow, while `Map`,
`Radial`, and `List` remain alternate local views. Layout position is only a
readability cue over generated graph data, not recommendation rank, progress,
importance, mastery, or authority.
```

- [ ] **Step 2: Update English agent guidance**

In `docs/guides/en/agents/index.md`, extend the Course graph verification
paragraph to require checking the default `Connections` layout, the alternate
layout modes, and deterministic graph positions without external graph
libraries.

- [ ] **Step 3: Update Spanish agent guidance**

In `docs/guides/es/agentes/index.md`, add the same requirement in Spanish while
keeping technical labels such as `Connections`, `Map`, `Radial`, `List`, and
`viewBox` in backticks.

- [ ] **Step 4: Verify focused tests still pass**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: PASS.

### Task 6: Review And Full Verification

**Files:**
- Review all changed files from Tasks 1-5.

- [ ] **Step 1: Request independent code review**

Dispatch a reviewer with this scope:

```text
Review Graph Connections Layout. Check deterministic layout correctness,
static-renderer constraints, no fetch/storage/CDN/external graph library,
default/reset behavior, tests, and EN/ES docs.
```

- [ ] **Step 2: Apply valid review findings**

If review finds Critical or Important issues, fix them before continuing. If it
finds Low issues that improve test coverage or docs without scope creep, fix
them in the same loop.

- [ ] **Step 3: Run final verification**

Run:

```bash
git diff --check
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: all commands exit 0. `check.sh` and `check-docker.sh` must run
sequentially, not concurrently.

- [ ] **Step 4: Commit and push**

Run:

```bash
git add docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph connections layout"
git push origin new_rayalucaria
```
