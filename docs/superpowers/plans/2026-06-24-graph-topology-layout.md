# Graph Topology Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a static, deterministic `Topology` graph layout that clusters visible pages by explicit generated graph relationships.

**Architecture:** The graph builder adds a new layout option and help copy. The local graph script keeps layout computation client-side but deterministic over already embedded graph payload data and currently visible edges. Tests verify HTML/script contracts and browser behavior from the existing render fixture.

**Tech Stack:** Python static builder, embedded local JavaScript emitted by `packages/static/src/raya_static/graph.py`, pytest, Playwright e2e.

---

## File Map

- Modify `packages/static/src/raya_static/builder.py`: add the `Topology` selector option and help text.
- Modify `packages/static/src/raya_static/graph.py`: pass active edges into `positionsFor`, add the deterministic topology layout helpers and branch.
- Modify `packages/static/src/raya_static/rendering.py`: no required visual changes unless tests show the toolbar needs wrapping adjustments.
- Modify `tests/contracts/test_static_builder.py`: assert graph HTML/script contract for `Topology`.
- Modify `tests/e2e/test_preview_static_read_path.py`: assert topology behavior in the render fixture.
- Modify `docs/foundation/20_learning_renderer_contract.md`: document the current `Topology` layout boundary.
- Modify English and Spanish agent guide indexes: document the static graph layout cue for agents.

## Tasks

### Task 1: Contract Test For Topology Layout

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write the failing test assertions**

In `test_build_writes_local_visual_graph_surface`, add assertions near the
existing graph layout assertions:

```python
assert '<option value="topology">Topology</option>' in graph_html
assert "Topology groups visible pages by explicit graph relationships" in graph_html
assert "topologyPositionsFor" in graph_script
assert "topologyEdgesFor" in graph_script
assert "Math.random" not in graph_script
assert "requestAnimationFrame" not in graph_script
```

- [ ] **Step 2: Verify red**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: fail because the graph selector and script do not contain topology
layout support.

### Task 2: Browser Test For Topology Behavior

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add topology assertions**

Inside `test_preview_serves_local_visual_graph_surface`, after the existing
`Cluster` layout checks and before returning to `Map`, add:

```python
page.select_option("#graph-layout", "topology")
assert (
    page.locator("[data-raya-graph-page]").get_attribute("data-raya-graph-layout")
    == "topology"
)
topology_root = _graph_node_translate(page, "render-root")
topology_matrix = _graph_node_translate(page, "authoring-matrix")
topology_static = _graph_node_translate(page, "static-path")
topology_reader = _graph_node_translate(page, "reader-ux")
assert _point_distance(topology_root, topology_matrix) < _point_distance(
    topology_static, topology_reader
)
topology_viewbox = _viewbox_values(
    page.locator("#raya-graph-canvas").get_attribute("viewBox")
)
topology_positions = page.locator(
    "#raya-graph-canvas [data-raya-graph-node] g"
).evaluate_all(
    """nodes => nodes.map((node) => {
      const match = node
        .getAttribute('transform')
        .match(/translate\\(([-0-9.]+)\\s+([-0-9.]+)\\)/);
      return { x: Number(match[1]), y: Number(match[2]) };
    })"""
)
assert all(30 <= position["x"] <= topology_viewbox[2] - 30 for position in topology_positions)
assert all(30 <= position["y"] <= topology_viewbox[3] - 30 for position in topology_positions)
before_filter_position = _graph_node_translate(page, "authoring-matrix")
page.locator('[data-raya-graph-edge-kind-filter="content"]').click()
page.wait_for_function(
    """() => document
      .querySelector('[data-raya-graph-edge-kind-filter="content"]')
      ?.getAttribute('aria-pressed') === 'false'"""
)
after_filter_position = _graph_node_translate(page, "authoring-matrix")
assert after_filter_position != before_filter_position
page.locator('[data-raya-graph-edge-kind-filter="content"]').click()
```

- [ ] **Step 2: Verify red**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: fail because `#graph-layout` does not have a `topology` option.

### Task 3: Implement Topology Layout

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/graph.py`

- [ ] **Step 1: Add selector and help copy**

In `_render_graph_surface`, add:

```html
<option value="topology">Topology</option>
```

after the `Connections` option, and add help text saying:

```text
Topology groups visible pages by explicit graph relationships. It is a
structural readability cue only, not learner state or personal guidance.
```

- [ ] **Step 2: Add topology helpers**

In `graph.py`, add `topologyEdgesFor(activeNodes)` and
`topologyPositionsFor(activeNodes, activeEdges)` near the existing layout helper
functions. The implementation must use deterministic initial ring positions,
fixed iteration counts, bounded repulsion, edge attraction, center pull, and
safe clamping inside the `960 x 560` graph space.

- [ ] **Step 3: Pass active edges into layout**

Change the render path from:

```javascript
const geometry = positionsFor(activeNodes, mode);
```

to:

```javascript
const geometry = positionsFor(activeNodes, mode, activeEdges);
```

and change the `positionsFor` signature to accept the third parameter.

- [ ] **Step 4: Add the topology branch**

Inside `positionsFor`, before `cluster`, add:

```javascript
if (mode === "topology") {
  return topologyPositionsFor(activeNodes, activeEdges);
}
```

### Task 4: Documentation Updates

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update renderer contract**

In the static graph paragraph, add `Topology` to the list of deterministic
layouts and state that it places visible pages by explicit generated graph
relationships only.

- [ ] **Step 2: Update agent guides**

Add one short paragraph in each agent guide explaining that agents may inspect
the generated graph `Topology` layout as a static readability view over
explicit relationships, but must read artifact data for authority and must not
treat graph position as recommendation or learner state.

### Task 5: Verification, Review, Commit

**Files:**
- All files above

- [ ] **Step 1: Run focused tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: both pass.

- [ ] **Step 2: Request independent review**

Ask a read-only subagent to review the topology layout implementation for
static contract violations, deterministic behavior, UX regressions, and weak
tests.

- [ ] **Step 3: Run full verification**

```bash
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Run the host and Docker gates sequentially.

- [ ] **Step 4: Commit and push**

```bash
git add docs/superpowers/specs/2026-06-24-graph-topology-layout-design.md \
  docs/superpowers/plans/2026-06-24-graph-topology-layout.md \
  docs/foundation/20_learning_renderer_contract.md \
  docs/guides/en/agents/index.md \
  docs/guides/es/agentes/index.md \
  packages/static/src/raya_static/builder.py \
  packages/static/src/raya_static/graph.py \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph topology layout"
git push origin new_rayalucaria
```

## Self-Review

- Spec coverage: selector, deterministic local layout, edge-kind interaction,
  documentation, and verification are covered.
- Placeholder scan: no placeholder tasks remain.
- Type consistency: plan uses existing `activeNodes`, `activeEdges`,
  `positionsFor`, graph selector IDs, and fixture node IDs.
