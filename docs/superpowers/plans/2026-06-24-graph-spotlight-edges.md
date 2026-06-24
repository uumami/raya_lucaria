# Graph Spotlight Edges Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add source-group edge color and transient hover/focus spotlighting to the static Course Graph.

**Architecture:** Keep the existing embedded JSON payload and SVG graph renderer. Derive all new visual state in `packages/static/src/raya_static/graph.py` from existing node/edge/group data, style it in `rendering.py`, expose static legend/help copy in `builder.py`, and verify with focused contract and Playwright tests.

**Tech Stack:** Python static builder, local JavaScript string, CSS in Python renderer resource, pytest, Playwright.

---

## File Structure

- `packages/static/src/raya_static/graph.py`: local graph script helpers, edge color custom property, and `is-dimmed` class toggles.
- `packages/static/src/raya_static/rendering.py`: CSS for colored edges, inspected edges, and dimmed graph elements.
- `packages/static/src/raya_static/builder.py`: graph legend and help copy.
- `docs/foundation/20_learning_renderer_contract.md`: contract language for edge colors and spotlight dimming.
- `docs/guides/en/agents/index.md`: English verification guidance.
- `docs/guides/es/agentes/index.md`: Spanish verification guidance.
- `tests/contracts/test_static_builder.py`: static HTML/script/CSS assertions.
- `tests/e2e/test_preview_static_read_path.py`: browser behavior assertions.

## Task 1: Contract And Browser RED Tests

- [ ] **Step 1: Add static contract assertions**

In `tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface`, add assertions near the existing graph legend checks:

```python
assert 'data-raya-graph-legend="edge-color"' in graph_html
assert "Edge color follows the source page group" in graph_html
assert "source-group edge colors" in graph_html
```

Add script assertions near existing graph script checks:

```python
assert "edgeColorFor" in graph_script
assert "--raya-graph-edge-color" in graph_script
assert "is-dimmed" in graph_script
```

- [ ] **Step 2: Add browser spotlight assertions**

In `tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface`, after the existing hover/focus inspection assertions around `authoring-matrix`, add:

```python
edge_color = page.locator("#raya-graph-canvas .raya-graph-edge").first.evaluate(
    "node => node.style.getPropertyValue('--raya-graph-edge-color')"
)
assert edge_color.startswith("var(--raya-graph-group-")
page.locator(
    '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
).hover()
page.wait_for_function(
    """() => document
      .querySelector('#raya-graph-canvas .raya-graph-edge.is-inspected') !== null"""
)
assert page.locator("#raya-graph-canvas .raya-graph-edge.is-dimmed").count() > 0
assert page.locator("#raya-graph-canvas .raya-graph-node.is-dimmed").count() > 0
page.locator('#raya-graph-list [data-raya-graph-node="static-path"] a').focus()
page.wait_for_function(
    """() => document
      .querySelector('[data-raya-graph-hover-status]')
      ?.textContent.includes('Static Path')"""
)
assert page.locator("#raya-graph-canvas .raya-graph-node.is-dimmed").count() > 0
```

- [ ] **Step 3: Run RED tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: FAIL because `edgeColorFor`, the edge-color legend, and `is-dimmed`
behavior do not exist yet.

## Task 2: Implement Static Graph Spotlight

- [ ] **Step 1: Add edge color helper**

In `packages/static/src/raya_static/graph.py`, after `groupColorIndex`, add:

```js
  function edgeColorFor(edge) {
    const source = nodesById.get(edge.from);
    if (!source) return "var(--raya-color-border)";
    return `var(--raya-graph-group-${groupColorIndex(source.group || "")})`;
  }
```

- [ ] **Step 2: Extend inspection DOM updates**

In `updateInspectionDom`, compute the spotlight set:

```js
    const inspectedSpotlightIds = inspectedId
      ? new Set([inspectedId, ...inspectedConnectedIds])
      : new Set();
```

Then add `is-dimmed` toggles for SVG node groups and edges:

```js
      nodeGroup.classList.toggle(
        "is-dimmed",
        Boolean(inspectedId) && !inspectedSpotlightIds.has(id)
      );
```

```js
      edge.classList.toggle(
        "is-dimmed",
        Boolean(inspectedId) && !(from === inspectedId || to === inspectedId)
      );
```

- [ ] **Step 3: Set edge color on rendered lines**

In the `activeEdges.forEach` render block, after setting edge data attributes,
add:

```js
      line.style.setProperty("--raya-graph-edge-color", edgeColorFor(edge));
```

Include `is-dimmed` in the rendered class list when inspection is already active:

```js
          inspectedId && !(edge.from === inspectedId || edge.to === inspectedId)
            ? "is-dimmed"
            : "",
```

- [ ] **Step 4: Include node dimming in initial render classes**

In the node group class list, add:

```js
          inspectedId && !new Set([inspectedId, ...inspectedConnectedIds]).has(node.id)
            ? "is-dimmed"
            : "",
```

If this inline set reads poorly, create a local `inspectedSpotlightIds` const in
`render()` next to `inspectedConnectedIds` and use it in both edge and node class
lists.

## Task 3: Style And Static Copy

- [ ] **Step 1: Style colored and dimmed edges**

In `packages/static/src/raya_static/rendering.py`, change `.raya-graph-edge` to:

```css
.raya-graph-edge {
  stroke: var(--raya-graph-edge-color, var(--raya-color-border));
  stroke-opacity: 0.58;
  stroke-width: 2;
}
```

Add:

```css
.raya-graph-edge.is-dimmed {
  stroke-opacity: 0.14;
}
.raya-graph-node.is-dimmed {
  opacity: 0.16;
}
```

- [ ] **Step 2: Preserve inspected edge visibility**

Keep `.raya-graph-edge.is-active` and `.raya-graph-edge.is-inspected`, but ensure
they set stronger opacity:

```css
.raya-graph-edge.is-active {
  stroke: var(--raya-color-accent);
  stroke-opacity: 0.86;
  stroke-width: 3;
}
.raya-graph-edge.is-inspected {
  stroke: var(--raya-graph-edge-color, var(--raya-color-success));
  stroke-opacity: 0.94;
  stroke-width: 3;
}
```

- [ ] **Step 3: Add legend/help copy**

In `packages/static/src/raya_static/builder.py`, add an edge-color legend item
before the existing explicit-link legend:

```python
(
    '<span class="raya-graph-legend-item" data-raya-graph-legend="edge-color">'
    '<span class="raya-graph-legend-line raya-graph-legend-edge-color"></span>'
    "Source group edge"
    "</span>"
),
```

Add a help paragraph:

```python
(
    "<p>Hover and keyboard focus spotlight the inspected page and its directly "
    "connected pages. Other graph marks dim temporarily; this is only a "
    "readability cue.</p>"
),
(
    "<p>Edge color follows the source page group so explicit links are easier "
    "to trace across the course.</p>"
),
```

## Task 4: Documentation

- [ ] **Step 1: Update foundation contract**

In `docs/foundation/20_learning_renderer_contract.md`, update the static graph
paragraph to include:

```markdown
source-group edge colors, transient hover/focus spotlight dimming,
```

- [ ] **Step 2: Update English agent guide**

In `docs/guides/en/agents/index.md`, update the graph verification guidance to
mention source-group edge colors and transient spotlight behavior.

- [ ] **Step 3: Update Spanish agent guide**

In `docs/guides/es/agentes/index.md`, update the matching graph verification
guidance in Spanish, keeping technical identifiers such as `Graph`, `Search`,
and `Practice` unchanged where the page labels use them.

## Task 5: GREEN Verification And Review

- [ ] **Step 1: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: PASS.

- [ ] **Step 2: Run render debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: `check-render-debug: passed`.

- [ ] **Step 3: Request code review**

Dispatch a reviewer with the base commit before implementation and the current
HEAD. Ask it to check static renderer constraints, spotlight behavior,
accessibility parity, no external dependencies, and test coverage.

- [ ] **Step 4: Run archive gates**

Run sequentially:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both pass.

- [ ] **Step 5: Commit and push**

Run:

```bash
git add docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph spotlight edge cues"
git push origin new_rayalucaria
```

## Self-Review

- Spec coverage: edge colors, spotlight dimming, legend/help copy, docs, tests,
  and static constraints are covered.
- Placeholder scan: no TODO/TBD placeholders remain.
- Type consistency: all identifiers match existing graph script and DOM naming.
