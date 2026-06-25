# Graph Relationship Chips Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add compact relationship-kind chips to the graph inspector so selected pages explain their direct graph context at a glance.

**Architecture:** Reuse the embedded graph JSON and existing selected-page render path in `graph.js`. Add one static inspector container in `builder.py`, fill it from local JS, and style it with existing token-based CSS in `rendering.py`.

**Tech Stack:** Python 3.10 static builder, local vanilla JavaScript graph resource, token CSS, pytest/Playwright.

---

### Task 1: Add Failing Relationship Chip Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add contract assertions**

In `test_build_writes_local_visual_graph_surface`, assert the graph HTML includes:

```python
assert "raya-graph-detail-relationship-chips" in graph_html
assert "data-raya-graph-detail-relationship-chips" in graph_html
assert "Relationship types" in graph_html
```

Also assert the graph script and stylesheet include the renderer/styling hooks:

```python
assert "renderRelationshipChips" in graph_script
assert "relationshipChipCountsFor" in graph_script
assert ".raya-graph-detail-relationship-chip" in stylesheet
```

- [x] **Step 2: Add browser behavior assertions**

In `test_preview_serves_local_visual_graph_surface`, after selecting or loading `authoring-matrix`, assert the chip section is visible and contains expected text:

```python
relationship_chips = page.locator("[data-raya-graph-detail-relationship-chips]")
assert relationship_chips.is_visible()
chip_texts = relationship_chips.locator(
    ".raya-graph-detail-relationship-chip"
).evaluate_all("nodes => nodes.map((node) => node.textContent.trim())")
assert "Content out 3" in chip_texts
assert "Content in 1" in chip_texts
assert "Navigation in 1" in chip_texts
assert "Parent out 1" in chip_texts
assert len(chip_texts) == 4
assert sum(int(text.split().pop()) for text in chip_texts) == 6
```

After `#graph-reset`, assert:

```python
assert page.locator("[data-raya-graph-detail-relationship-chips]").is_hidden()
```

- [x] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: FAIL because the chip container, JS renderer, and CSS class do not exist yet.

### Task 2: Add Inspector Markup and Styles

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add the static chip container**

In the graph detail panel after `data-raya-graph-detail-neighborhood`, add:

```html
<section class="raya-graph-detail-relationship-chips" data-raya-graph-detail-relationship-chips hidden>
  <h3>Relationship types</h3>
  <div class="raya-graph-detail-relationship-chip-list" data-raya-graph-detail-relationship-chip-list></div>
</section>
```

- [x] **Step 2: Add token-based CSS**

Add CSS in `packages/static/src/raya_static/rendering.py` near the existing graph detail styles:

```css
.raya-graph-detail-relationship-chips {
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  margin: 0.75rem 0;
  padding: 0.65rem;
}
.raya-graph-detail-relationship-chips h3 {
  font-size: 0.95rem;
  margin: 0 0 0.45rem;
}
.raya-graph-detail-relationship-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.raya-graph-detail-relationship-chip {
  align-items: center;
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  color: var(--raya-color-text);
  display: inline-flex;
  font-size: 0.82rem;
  font-weight: 700;
  gap: 0.35rem;
  line-height: 1.2;
  min-height: 1.8rem;
  padding: 0.25rem 0.55rem;
}
```

### Task 3: Render Relationship Chips in Local Graph JS

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [x] **Step 1: Capture chip DOM nodes**

Add selectors near the other detail selectors:

```javascript
const detailRelationshipChips = document.querySelector("[data-raya-graph-detail-relationship-chips]");
const detailRelationshipChipList = document.querySelector("[data-raya-graph-detail-relationship-chip-list]");
```

- [x] **Step 2: Add relationship counting helpers**

Add:

```javascript
function relationshipChipLabel(kind, direction) {
  const kindLabel = edgeKindLabel(kind);
  return `${kindLabel} ${direction}`;
}

function relationshipChipCountsFor(nodeId) {
  const counts = new Map();
  edges.forEach((edge) => {
    const kind = edgeKind(edge);
    if (edge.from === nodeId) {
      const key = `${kind}:out`;
      counts.set(key, {
        kind,
        direction: "out",
        count: (counts.get(key)?.count || 0) + 1,
      });
    }
    if (edge.to === nodeId) {
      const key = `${kind}:in`;
      counts.set(key, {
        kind,
        direction: "in",
        count: (counts.get(key)?.count || 0) + 1,
      });
    }
  });
  const order = ["navigation", "content", "prerequisite", "parent"];
  return Array.from(counts.values()).sort((left, right) => {
    const kindDelta = order.indexOf(left.kind) - order.indexOf(right.kind);
    if (kindDelta !== 0) return kindDelta;
    return left.direction.localeCompare(right.direction);
  });
}
```

- [x] **Step 3: Render and clear chips**

Add:

```javascript
function renderRelationshipChips(nodeId) {
  if (!detailRelationshipChips || !detailRelationshipChipList) return;
  detailRelationshipChipList.replaceChildren();
  if (!nodeId) {
    detailRelationshipChips.hidden = true;
    return;
  }
  const chips = relationshipChipCountsFor(nodeId);
  if (!chips.length) {
    detailRelationshipChips.hidden = true;
    return;
  }
  chips.forEach((chip) => {
    const item = document.createElement("span");
    item.className = "raya-graph-detail-relationship-chip";
    item.setAttribute("data-raya-graph-relationship-kind", chip.kind);
    item.setAttribute("data-raya-graph-relationship-direction", chip.direction);
    item.textContent = `${relationshipChipLabel(chip.kind, chip.direction)} ${chip.count}`;
    detailRelationshipChipList.appendChild(item);
  });
  detailRelationshipChips.hidden = false;
}
```

Call `renderRelationshipChips("")` in the no-selection branch and `renderRelationshipChips(node.id)` in the selected-page branch.

- [x] **Step 4: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: PASS.

### Task 4: Review, Gates, Commit, Preview

**Files:**
- No additional production files expected.

- [x] **Step 1: Request independent review**

Ask a reviewer to inspect the uncommitted diff for static boundary violations, graph state regressions, visual accessibility issues, and test coverage gaps.

- [x] **Step 2: Run render debug**

```bash
./scripts/check-render-debug.sh
```

Expected: PASS.

- [x] **Step 3: Run full gates sequentially**

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: PASS.

- [ ] **Step 4: Commit, push, preview**

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py tests/contracts/test_static_builder.py docs/superpowers/specs/2026-06-25-graph-relationship-chips-design.md docs/superpowers/plans/2026-06-25-graph-relationship-chips.md
git commit -m "Explain graph relationships with chips"
git push origin new_rayalucaria
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --host 127.0.0.1 --port 0
```

Report the local preview URL and graph URL.
