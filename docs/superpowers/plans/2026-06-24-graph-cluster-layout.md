# Graph Cluster Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic `Cluster` layout to the static Course graph so pages in the same generated course group sit near each other without external graph libraries or persistent state.

**Architecture:** Keep the current embedded graph payload and local SVG renderer. Add one static layout option in the builder, helper functions and a `cluster` branch in `packages/static/src/raya_static/graph.py`, focused contract and Playwright assertions, and foundation/role documentation updates.

**Tech Stack:** Python static builder, local JavaScript string in `packages/static/src/raya_static/graph.py`, pytest contract tests, Playwright e2e tests, Markdown docs.

---

### Task 1: Contract Test

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write failing layout option assertion**

In `test_build_writes_local_visual_graph_surface`, near the existing layout
option assertions, add:

```python
assert '<option value="cluster">Cluster</option>' in graph_html
```

- [ ] **Step 2: Write failing graph help assertion**

Near the existing graph help assertions, add:

```python
assert "Cluster groups visible pages by generated course group" in graph_html
```

- [ ] **Step 3: Write failing graph script assertions**

Near the existing `connectionDepthsFor` and `layoutEdgesFor` graph script
assertions, add:

```python
assert "sortedGroupIdsFor" in graph_script
assert 'mode === "cluster"' in graph_script
assert "clusterRingRadius" in graph_script
```

- [ ] **Step 4: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: FAIL because `Cluster` markup and script helpers do not exist yet.

### Task 2: Browser Behavior Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add distance helper**

Near `_graph_node_translate`, add:

```python
def _point_distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
```

- [ ] **Step 2: Write failing Cluster layout assertions**

In `test_preview_serves_local_visual_graph_surface`, after the existing `List`
layout assertions and before switching back to `Connections` or `Map`, add:

```python
page.select_option("#graph-layout", "cluster")
assert (
    page.locator("[data-raya-graph-page]").get_attribute(
        "data-raya-graph-layout"
    )
    == "cluster"
)
cluster_root = _graph_node_translate(page, "render-root")
cluster_static = _graph_node_translate(page, "static-path")
cluster_math = _graph_node_translate(page, "math-authoring")
cluster_numbered = _graph_node_translate(page, "numbered-objects")
assert _point_distance(cluster_math, cluster_numbered) < _point_distance(
    cluster_root, cluster_static
)
```

This checks that pages in the same generated group sit closer together than
pages in different generated groups.

- [ ] **Step 3: Reuse bounds checks after Cluster render**

Immediately after the cluster distance assertions, read all graph node
positions the same way the existing bounds check does and assert:

```python
assert all(
    30 <= position["x"] <= canvas_width - 30
    for position in graph_node_positions
)
assert all(
    30 <= position["y"] <= canvas_height - 30
    for position in graph_node_positions
)
```

Use fresh `graph_node_positions`, `canvas_width`, and `canvas_height` values
after selecting `Cluster`.

- [ ] **Step 4: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: FAIL because the `cluster` option does not exist yet.

### Task 3: Builder Markup and Help

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add Cluster option**

In `_render_graph_surface`, update the layout select from:

```html
<option value="connections" selected>Connections</option>
<option value="map">Map</option>
```

to:

```html
<option value="connections" selected>Connections</option>
<option value="cluster">Cluster</option>
<option value="map">Map</option>
```

- [ ] **Step 2: Add neutral help text**

In the graph help details, after the Connections paragraph, add:

```html
<p>Cluster groups visible pages by generated course group so nearby pages can be scanned together.</p>
```

Do not use visible words forbidden by
`test_render_fixture_search_graph_course_map_visible_text_avoids_learner_state_language`.

- [ ] **Step 3: Verify contract test still fails only on script assertions**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: FAIL on missing `sortedGroupIdsFor`, `mode === "cluster"`, and
`clusterRingRadius`.

### Task 4: Local Cluster Layout

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [ ] **Step 1: Add group sorting helper**

After `layoutEdgesFor(activeNodes)`, add:

```javascript
function sortedGroupIdsFor(activeNodes) {
  const activeGroupIds = Array.from(new Set(activeNodes.map((node) => node.group || "")));
  return activeGroupIds.sort((a, b) => {
    const aGroup = groups.find((group) => group.id === a);
    const bGroup = groups.find((group) => group.id === b);
    const aOrder = Number(aGroup ? aGroup.order || 0 : 0);
    const bOrder = Number(bGroup ? bGroup.order || 0 : 0);
    return aOrder - bOrder || groupTitle(a).localeCompare(groupTitle(b)) || a.localeCompare(b);
  });
}
```

- [ ] **Step 2: Add cluster branch to `positionsFor`**

In `positionsFor(activeNodes, mode)`, after the `connections` branch and before
the `radial` branch, add:

```javascript
if (mode === "cluster") {
  const centerX = width / 2;
  const centerY = height / 2;
  const sidePadding = 92;
  const topPadding = 88;
  const availableWidth = Math.max(1, width - sidePadding * 2);
  const availableHeight = Math.max(1, height - topPadding * 2);
  const centerRingRadius = Math.min(availableWidth, availableHeight) * 0.38;
  const groupIds = sortedGroupIdsFor(activeNodes);
  const nodesByGroup = new Map(groupIds.map((groupId) => [groupId, []]));
  activeNodes.forEach((node) => {
    const groupId = node.group || "";
    if (!nodesByGroup.has(groupId)) nodesByGroup.set(groupId, []);
    nodesByGroup.get(groupId).push(node);
  });
  groupIds.forEach((groupId, groupIndex) => {
    const angle = groupIds.length <= 1
      ? -Math.PI / 2
      : (Math.PI * 2 * groupIndex) / groupIds.length - Math.PI / 2;
    const groupCenter = {
      x: groupIds.length <= 1 ? centerX : centerX + Math.cos(angle) * centerRingRadius,
      y: groupIds.length <= 1 ? centerY : centerY + Math.sin(angle) * centerRingRadius,
    };
    const groupNodes = (nodesByGroup.get(groupId) || []).slice().sort(compareNodesByOrder);
    const maxRadiusX = Math.max(0, Math.min(groupCenter.x - 44, width - groupCenter.x - 44));
    const maxRadiusY = Math.max(0, Math.min(groupCenter.y - 44, height - groupCenter.y - 44));
    const clusterRingRadius = groupNodes.length <= 1
      ? 0
      : Math.min(74, Math.max(32, Math.min(maxRadiusX, maxRadiusY)));
    groupNodes.forEach((node, nodeIndex) => {
      if (clusterRingRadius === 0) {
        positions.set(node.id, groupCenter);
        return;
      }
      const nodeAngle = (Math.PI * 2 * nodeIndex) / groupNodes.length - Math.PI / 2;
      positions.set(node.id, {
        x: groupCenter.x + Math.cos(nodeAngle) * clusterRingRadius,
        y: groupCenter.y + Math.sin(nodeAngle) * clusterRingRadius,
      });
    });
  });
  return { width, height, positions };
}
```

- [ ] **Step 3: Verify focused tests pass**

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

- [ ] **Step 1: Update foundation contract**

In the graph layout paragraph, add `Cluster` as a deterministic generated-group
layout alongside `Connections`, `Map`, `Radial`, and `List`. Keep the statement
that layout positions are only structural reading cues over generated graph
data.

- [ ] **Step 2: Update English agent guide**

In the Graph section, mention `Cluster` as an alternate generated-group layout.
Avoid forbidden learner-state words in rendered student-facing UI guidance.

- [ ] **Step 3: Update Spanish agent guide**

In the matching Spanish Graph section, mention `Cluster` as an alternate
generated-group layout. Keep technical labels in backticks.

- [ ] **Step 4: Verify docs and rendered language tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_search_graph_course_map_visible_text_avoids_learner_state_language tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: PASS.

### Task 6: Final Focused Verification

**Files:**
- No edits.

- [ ] **Step 1: Run focused graph/browser tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/contracts/test_static_builder.py::test_render_fixture_search_graph_course_map_visible_text_avoids_learner_state_language tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: PASS.

- [ ] **Step 2: Run render debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS with no external renderer requests, no raw visible TeX leakage,
and static/site parity checks passing.

- [ ] **Step 3: Run archive gates**

Run sequentially:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both pass.

- [ ] **Step 4: Commit implementation**

Run:

```bash
git add docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph cluster layout"
```
