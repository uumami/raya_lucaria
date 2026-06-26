# Graph Relationship Comprehension Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make selected-page graph relationships easier to inspect by coordinating relationship chips, walkthrough cards, detail lists, SVG edge emphasis, and global relationship filters.

**Architecture:** Reuse the existing embedded Graph payload and `relationshipFocus` state in `graph.js`. Add generated static markup for a relationship focus bar, local JavaScript synchronization, CSS emphasis classes, and focused contract/browser tests. Do not change graph data schemas, generated graph JSON, URL parameters, storage, or external dependencies.

**Tech Stack:** Python static builder, generated HTML/CSS/JS, local SVG graph, pytest, Playwright.

---

## File Structure

- `packages/static/src/raya_static/builder.py` owns the generated Graph HTML. It will add the relationship focus bar and reset button inside the selected-page relationship chip section.
- `packages/static/src/raya_static/graph.py` owns local Graph workspace behavior. It will coordinate `relationshipFocus` with chip state, walkthrough cards, outgoing/incoming detail lists, SVG edge classes, and global edge-kind filters.
- `packages/static/src/raya_static/rendering.py` owns visual styling. It will style the focus bar, reset button, globally hidden chips, focused relationship edges, and muted selected-page edges.
- `tests/contracts/test_static_builder.py` owns static Graph HTML contract checks.
- `tests/e2e/test_preview_static_read_path.py` owns browser behavior checks over the render fixture.
- `docs/foundation/20_learning_renderer_contract.md`, `docs/guides/en/students/index.md`, and `docs/guides/es/estudiantes/index.md` own structural language and role-facing documentation.

## Task 1: Static Markup Contract

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Write the failing contract assertions**

In `tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface`, after the existing assertions for `data-raya-graph-detail-relationship-chip-list`, add:

```python
assert "data-raya-graph-relationship-focus-bar" in graph_html
assert "data-raya-graph-relationship-focus-summary" in graph_html
assert "data-raya-graph-relationship-focus-reset" in graph_html
assert (
    '<button type="button" class="raya-graph-relationship-focus-reset" '
    'data-raya-graph-relationship-focus-reset hidden>'
    "Show all relationships</button>"
) in graph_html
```

- [ ] **Step 2: Run the focused contract test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: fail because the generated Graph HTML does not yet include the relationship focus bar.

- [ ] **Step 3: Add generated relationship focus markup**

In `packages/static/src/raya_static/builder.py`, inside the selected-page relationship chips section immediately before `data-raya-graph-detail-relationship-chip-list`, generate:

```python
(
    '<div class="raya-graph-relationship-focus-bar" '
    "data-raya-graph-relationship-focus-bar>"
)
'<p data-raya-graph-relationship-focus-summary>'
"All selected-page relationships are visible.</p>"
(
    '<button type="button" class="raya-graph-relationship-focus-reset" '
    "data-raya-graph-relationship-focus-reset hidden>"
    "Show all relationships</button>"
)
"</div>"
```

Keep the existing chip list and `data-raya-graph-detail-relationship-chips` wrapper.

- [ ] **Step 4: Run the focused contract test and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: pass.

## Task 2: Relationship Focus Behavior

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/graph.py`

- [ ] **Step 1: Write failing browser assertions**

In `tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface`, extend the existing `authoring-matrix` relationship-chip block after `content_out_chip.click()` with:

```python
focus_summary = page.locator("[data-raya-graph-relationship-focus-summary]")
focus_reset = page.locator("[data-raya-graph-relationship-focus-reset]")
assert focus_reset.is_visible()
assert "Showing Content out relationships." in focus_summary.inner_text()
assert (
    page.locator("[data-raya-graph-detail-outgoing] li").evaluate_all(
        "items => items.filter((item) => !item.hidden).map((item) => item.textContent)"
    )
    == page.locator("[data-raya-graph-detail-outgoing] li").evaluate_all(
        "items => items.filter((item) => !item.hidden && item.textContent.includes('Content')).map((item) => item.textContent)"
    )
)
assert page.locator("[data-raya-graph-detail-incoming] li").evaluate_all(
    "items => items.every((item) => item.hidden)"
) is True
focused_edges = page.locator("#raya-graph-canvas [data-raya-graph-edge].is-relationship-focus")
muted_edges = page.locator("#raya-graph-canvas [data-raya-graph-edge].is-relationship-muted")
assert focused_edges.count() >= 1
assert muted_edges.count() >= 1
```

After the existing second click that clears `content_out_chip`, add:

```python
assert focus_reset.is_hidden()
assert "All selected-page relationships are visible." in focus_summary.inner_text()
assert focused_edges.count() == 0
assert muted_edges.count() == 0
assert page.locator("[data-raya-graph-detail-incoming] li").evaluate_all(
    "items => items.some((item) => !item.hidden)"
) is True
```

- [ ] **Step 2: Run the focused browser test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: fail because the relationship focus bar, filtered detail lists, and SVG focus edge classes are not implemented.

- [ ] **Step 3: Add relationship focus DOM references**

In `packages/static/src/raya_static/graph.py`, near the existing `relationshipFocusStatus` query, add:

```javascript
  const relationshipFocusSummary = document.querySelector(
    "[data-raya-graph-relationship-focus-summary]"
  );
  const relationshipFocusReset = document.querySelector(
    "[data-raya-graph-relationship-focus-reset]"
  );
```

Add a click listener after helper definitions are available:

```javascript
  if (relationshipFocusReset) {
    relationshipFocusReset.addEventListener("click", () => clearRelationshipFocus());
  }
```

- [ ] **Step 4: Update relationship focus synchronization**

In `syncRelationshipFocusDom()`, after computing `hasFocus`, add:

```javascript
    if (relationshipFocusSummary) {
      relationshipFocusSummary.textContent = hasFocus
        ? `Showing ${relationshipChipLabel(kind, direction)} relationships.`
        : "All selected-page relationships are visible.";
    }
    if (relationshipFocusReset) {
      relationshipFocusReset.hidden = !hasFocus;
    }
```

Keep the existing `relationshipFocusStatus` behavior for screen-reader live status.

- [ ] **Step 5: Filter selected-page detail lists by relationship focus**

Modify `explicitRelationshipsFor(nodeId, direction)` so each returned item has a normalized `kind` field and each list item gets data attributes in `renderDetailList`.

Use this returned item shape:

```javascript
        return {
          id: otherId,
          title: target.title || otherId,
          url: target.url || "#",
          kind: edgeKind(edge),
          kindLabel: edgeLabel(edge),
        };
```

In `renderDetailList(container, items, emptyText)`, set:

```javascript
        if (item.kind) li.setAttribute("data-raya-graph-detail-relationship-kind", item.kind);
        if (item.direction) li.setAttribute("data-raya-graph-detail-relationship-direction", item.direction);
```

When creating outgoing and incoming arrays in `renderDetail()`, add `direction` to each item:

```javascript
    const outgoing = explicitRelationshipsFor(node.id, "out").map((item) => ({
      ...item,
      direction: "out",
    }));
    const incoming = explicitRelationshipsFor(node.id, "in").map((item) => ({
      ...item,
      direction: "in",
    }));
```

Then hide nonmatching detail list items in `syncRelationshipFocusDom()`:

```javascript
    document.querySelectorAll("[data-raya-graph-detail-relationship-kind]").forEach((item) => {
      const itemKind = item.getAttribute("data-raya-graph-detail-relationship-kind") || "";
      const itemDirection = item.getAttribute("data-raya-graph-detail-relationship-direction") || "";
      item.hidden = hasFocus && (itemKind !== kind || itemDirection !== direction);
    });
```

- [ ] **Step 6: Add SVG edge relationship focus classes**

In the SVG edge render path that creates elements with `data-raya-graph-edge`, add class synchronization based on `relationshipFocus`, `selectedId`, and edge kind/direction:

```javascript
      const edgeDirection = edge.from === selectedId ? "out" : (edge.to === selectedId ? "in" : "");
      const selectedPageEdge = Boolean(selectedId && edgeDirection);
      const focusMatches = Boolean(
        relationshipFocus &&
        selectedPageEdge &&
        edgeKind(edge) === relationshipFocus.kind &&
        edgeDirection === relationshipFocus.direction
      );
      edgeElement.classList.toggle("is-relationship-focus", focusMatches);
      edgeElement.classList.toggle(
        "is-relationship-muted",
        Boolean(relationshipFocus && selectedPageEdge && !focusMatches)
      );
```

Use the local edge element variable name already used by the renderer.

- [ ] **Step 7: Run the focused browser test and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: pass.

## Task 3: Global Relationship Filter Coordination

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Write failing browser assertions for globally hidden kinds**

In the same graph e2e block, after reselecting `authoring-matrix`, click the global `content` relationship filter off and assert chip state:

```python
page.locator('[data-raya-graph-edge-kind-filter="content"]').click()
assert content_out_chip.get_attribute("data-raya-graph-relationship-hidden-by-filter") == "true"
assert "Content relationships are hidden by Relationship filters." in focus_summary.inner_text()
page.locator('[data-raya-graph-edge-kind-filter="content"]').click()
assert content_out_chip.get_attribute("data-raya-graph-relationship-hidden-by-filter") == "false"
assert "All selected-page relationships are visible." in focus_summary.inner_text()
```

- [ ] **Step 2: Run the focused browser test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: fail because relationship chips are not yet annotated when the global relationship kind is hidden.

- [ ] **Step 3: Mark chips hidden by global relationship filters**

In `syncRelationshipFocusDom()`, while iterating relationship chips, add:

```javascript
          const hiddenByFilter = hiddenEdgeKinds.has(chipKind);
          chip.setAttribute(
            "data-raya-graph-relationship-hidden-by-filter",
            hiddenByFilter ? "true" : "false"
          );
          chip.classList.toggle("is-hidden-by-filter", hiddenByFilter);
```

When there is no active relationship focus but at least one selected-page chip kind is hidden by global filters, set `relationshipFocusSummary.textContent` to:

```javascript
`${relationshipKindLabel(firstHiddenKind)} relationships are hidden by Relationship filters.`
```

Add a small helper:

```javascript
  function relationshipKindLabel(kind) {
    const labels = {
      navigation: "Navigation",
      content: "Content",
      prerequisite: "Prerequisite",
      parent: "Parent",
    };
    return labels[edgeKind({ kind })] || "Relationship";
  }
```

- [ ] **Step 4: Add CSS for focused and hidden states**

In `packages/static/src/raya_static/rendering.py`, add:

```css
.raya-graph-relationship-focus-bar {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: space-between;
}
.raya-graph-relationship-focus-bar p {
  margin: 0;
}
.raya-graph-relationship-focus-reset {
  white-space: nowrap;
}
.raya-graph-detail-relationship-chip.is-hidden-by-filter {
  opacity: 0.58;
}
.raya-graph-edge.is-relationship-focus {
  opacity: 1;
  stroke-width: 3;
}
.raya-graph-edge.is-relationship-muted {
  opacity: 0.22;
}
```

Use selectors that match the existing SVG edge classes if the renderer uses a child path instead of the edge wrapper.

- [ ] **Step 5: Run the focused browser test and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: pass.

## Task 4: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`

- [ ] **Step 1: Update foundation contract**

In `docs/foundation/20_learning_renderer_contract.md`, extend the selected-page relationship chip sentence to say chips may focus walkthrough cards, selected-page incoming/outgoing lists, and visible selected-page graph edges, while global relationship filters may mark chip kinds as hidden.

- [ ] **Step 2: Update English student guide**

In `docs/guides/en/students/index.md`, update the relationship walkthrough paragraph to mention `Show all relationships` and that Relationship filters may hide a kind globally without storing state.

- [ ] **Step 3: Update Spanish student guide**

In `docs/guides/es/estudiantes/index.md`, mirror the English student-guide update in Spanish while keeping technical labels such as `Relationship filters` and `Show all relationships` in English.

- [ ] **Step 4: Run focused docs/build verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
./scripts/check-render-debug.sh
```

Expected: all pass.

## Task 5: Review, Commit, Push

**Files:**
- All files changed by Tasks 1-4.

- [ ] **Step 1: Request code review**

Use `superpowers:requesting-code-review` and dispatch at least one independent reviewer focused on graph state/static invariants.

- [ ] **Step 2: Address review feedback**

Fix Critical and Important findings. Re-run the focused verification commands from Task 4.

- [ ] **Step 3: Run archive gates**

Run sequentially:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both pass.

- [ ] **Step 4: Commit and push**

Run:

```bash
git status --short --branch
git add docs/superpowers/specs/2026-06-26-graph-relationship-comprehension-design.md docs/superpowers/plans/2026-06-26-graph-relationship-comprehension.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/es/estudiantes/index.md
git commit -m "Clarify graph relationship focus"
git push origin new_rayalucaria
```

Expected: branch is clean and `origin/new_rayalucaria` contains the new commit.
