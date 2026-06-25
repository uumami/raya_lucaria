# Graph Focus Orientation Band Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact student-facing graph orientation band and make selected-page relationship lists match explicit graph relationships.

**Architecture:** Reuse the existing static graph page and local `graph.js` state. The builder emits inert orientation scaffolding, the local graph script updates it from current visible nodes/edges and selected-page state, and docs describe it as structural graph context.

**Tech Stack:** Python static builder, embedded vanilla JavaScript graph renderer, Playwright e2e tests, Markdown foundation and role docs.

---

## File Structure

- Modify `tests/contracts/test_static_builder.py`: add graph HTML/script/CSS assertions to the existing local graph surface test.
- Modify `tests/e2e/test_preview_static_read_path.py`: add a browser regression for orientation updates and relationship-list consistency.
- Modify `packages/static/src/raya_static/builder.py`: render the orientation band in `_render_graph_surface`.
- Modify `packages/static/src/raya_static/graph.py`: select orientation elements, update them during `render()`, wire action controls, and derive incoming detail relationships from explicit edges.
- Modify `packages/static/src/raya_static/rendering.py`: add compact responsive graph orientation styles.
- Modify `docs/foundation/20_learning_renderer_contract.md`: record the graph orientation band and relationship-list consistency.
- Modify `docs/guides/en/students/index.md`, `docs/guides/es/estudiantes/index.md`, `docs/guides/en/agents/index.md`, and `docs/guides/es/agentes/index.md`: document how students and agents should read/verify the band.

## Task 1: Contract Test For Orientation Scaffolding

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add failing contract assertions**

In `test_build_writes_local_visual_graph_surface`, after the existing `assert "data-raya-graph-hover-status" in graph_html`, add:

```python
    assert "raya-graph-orientation" in graph_html
    assert "data-raya-graph-orientation" in graph_html
    assert "data-raya-graph-orientation-counts" in graph_html
    assert "data-raya-graph-orientation-layout" in graph_html
    assert "data-raya-graph-orientation-selected" in graph_html
    assert "data-raya-graph-orientation-page-focus" in graph_html
    assert "data-raya-graph-orientation-query" in graph_html
    assert "data-raya-graph-orientation-filters" in graph_html
    assert "data-raya-graph-orientation-neighborhood" in graph_html
    assert "data-raya-graph-orientation-open" in graph_html
    assert "data-raya-graph-orientation-neighborhood-toggle" in graph_html
    assert "data-raya-graph-orientation-clear" in graph_html
    assert "updateGraphOrientation" in graph_script
    assert "explicitRelationshipsFor" in graph_script
    assert ".raya-graph-orientation" in stylesheet
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: FAIL because `raya-graph-orientation` is not present.

## Task 2: Browser Test For Orientation Behavior

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add failing browser assertions**

Extend `test_render_fixture_graph_url_state_and_debug_readout` after the initial graph page load assertions:

```python
                    orientation = page.locator("[data-raya-graph-orientation]")
                    assert orientation.is_visible()
                    assert "visible node" in page.locator(
                        "[data-raya-graph-orientation-counts]"
                    ).inner_text()
                    assert "Connections" in page.locator(
                        "[data-raya-graph-orientation-layout]"
                    ).inner_text()
                    assert "Projection Residuals" in page.locator(
                        "[data-raya-graph-orientation-selected]"
                    ).inner_text()
                    assert "Projection Residuals" in page.locator(
                        "[data-raya-graph-orientation-page-focus]"
                    ).inner_text()
                    assert "projection" in page.locator(
                        "[data-raya-graph-orientation-query]"
                    ).inner_text()
                    assert "All groups and relationships visible" in page.locator(
                        "[data-raya-graph-orientation-filters]"
                    ).inner_text()
                    open_from_orientation = page.locator(
                        "[data-raya-graph-orientation-open]"
                    )
                    assert open_from_orientation.is_visible()
                    assert open_from_orientation.get_attribute("href").endswith(
                        "/4_reader_ux/index.html"
                    )
                    orientation_focus = page.locator(
                        "[data-raya-graph-orientation-neighborhood-toggle]"
                    )
                    assert orientation_focus.is_visible()
                    orientation_focus.click()
                    page.wait_for_function(
                        "() => document.querySelector('[data-raya-graph-orientation-neighborhood]').textContent.includes('On')"
                    )
                    assert "neighborhood=1" in page.url
                    orientation_focus.click()
                    page.wait_for_function(
                        "() => document.querySelector('[data-raya-graph-orientation-neighborhood]').textContent.includes('Off')"
                    )
                    assert "neighborhood=1" not in page.url
```

After the existing parent-edge filter assertion, add:

```python
                    assert "Parent" in page.locator(
                        "[data-raya-graph-orientation-filters]"
                    ).inner_text()
```

After the existing group filter assertion, add:

```python
                    assert "hidden group" in page.locator(
                        "[data-raya-graph-orientation-filters]"
                    ).inner_text().lower()
```

Near the relationship chip assertions, add:

```python
                        incoming_text = page.locator(
                            "[data-raya-graph-detail-incoming]"
                        ).inner_text()
                        walkthrough_text = relationship_walkthrough.inner_text()
                        assert "Content" in incoming_text
                        assert "Content in" in walkthrough_text
```

- [ ] **Step 2: Run the browser test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_url_state_and_debug_readout -q
```

Expected: FAIL because the orientation selectors are missing.

## Task 3: Render Orientation Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add orientation scaffolding after `graph-status`**

In `_render_graph_surface`, immediately after:

```python
            '<p id="graph-status" class="raya-graph-status" aria-live="polite"></p>',
```

insert:

```python
            (
                '<section class="raya-graph-orientation" '
                'data-raya-graph-orientation aria-label="Graph orientation">'
                '<div class="raya-graph-orientation-main">'
                '<p class="raya-graph-orientation-counts" '
                'data-raya-graph-orientation-counts>'
                '0 visible node(s), 0 visible edge(s)</p>'
                '<p class="raya-graph-orientation-selection">'
                '<span>Selected</span> '
                '<strong data-raya-graph-orientation-selected>None</strong>'
                '</p>'
                '</div>'
                '<dl class="raya-graph-orientation-meta">'
                '<div><dt>Layout</dt><dd data-raya-graph-orientation-layout>'
                'Connections</dd></div>'
                '<div><dt>Page focus</dt><dd data-raya-graph-orientation-page-focus>'
                'None</dd></div>'
                '<div><dt>Search</dt><dd data-raya-graph-orientation-query>'
                'None</dd></div>'
                '<div><dt>Filters</dt><dd data-raya-graph-orientation-filters>'
                'All groups and relationships visible</dd></div>'
                '<div><dt>Neighborhood</dt>'
                '<dd data-raya-graph-orientation-neighborhood>Off</dd></div>'
                '</dl>'
                '<p class="raya-graph-orientation-actions">'
                '<a data-raya-graph-orientation-open href="../../index.html" hidden>'
                'Open page</a>'
                '<button type="button" data-raya-graph-orientation-neighborhood-toggle '
                'hidden>Focus neighborhood</button>'
                '<button type="button" data-raya-graph-orientation-clear hidden>'
                'Clear selection</button>'
                '</p>'
                '</section>'
            ),
```

- [ ] **Step 2: Run the contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: still FAIL because `graph.py` and CSS hooks are missing.

## Task 4: Update Graph Script State And Relationship Lists

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [ ] **Step 1: Add element selectors near existing state selectors**

Add constants after `copyStatus`:

```javascript
  const orientation = document.querySelector("[data-raya-graph-orientation]");
  const orientationCounts = document.querySelector("[data-raya-graph-orientation-counts]");
  const orientationLayout = document.querySelector("[data-raya-graph-orientation-layout]");
  const orientationSelected = document.querySelector("[data-raya-graph-orientation-selected]");
  const orientationPageFocus = document.querySelector("[data-raya-graph-orientation-page-focus]");
  const orientationQuery = document.querySelector("[data-raya-graph-orientation-query]");
  const orientationFilters = document.querySelector("[data-raya-graph-orientation-filters]");
  const orientationNeighborhood = document.querySelector("[data-raya-graph-orientation-neighborhood]");
  const orientationOpen = document.querySelector("[data-raya-graph-orientation-open]");
  const orientationNeighborhoodToggle = document.querySelector("[data-raya-graph-orientation-neighborhood-toggle]");
  const orientationClear = document.querySelector("[data-raya-graph-orientation-clear]");
```

- [ ] **Step 2: Add helper functions before `renderDetail()`**

Add:

```javascript
  function layoutLabel(value) {
    const labels = {
      connections: "Connections",
      topology: "Topology",
      cluster: "Cluster",
      map: "Map",
      radial: "Radial",
      list: "List",
    };
    return labels[value] || value || "Connections";
  }

  function explicitRelationshipsFor(nodeId, direction) {
    return edges
      .filter((edge) => (direction === "out" ? edge.from === nodeId : edge.to === nodeId))
      .map((edge) => {
        const otherId = direction === "out" ? edge.to : edge.from;
        const target = nodesById.get(otherId) || {};
        return {
          id: otherId,
          title: target.title || otherId,
          url: target.url || "#",
          kind: edgeLabel(edge),
        };
      });
  }

  function updateGraphOrientation(activeNodes, activeEdges) {
    if (!orientation) return;
    const selected = selectedId ? nodesById.get(selectedId) : null;
    const focused = pageFocusId ? nodesById.get(pageFocusId) : null;
    if (orientationCounts) {
      orientationCounts.textContent = `${activeNodes.length} visible node(s), ${activeEdges.length} visible edge(s)`;
    }
    if (orientationLayout) orientationLayout.textContent = layoutLabel(layout ? layout.value : "connections");
    if (orientationSelected) {
      orientationSelected.textContent = selected ? selected.title || selected.nav_title || selected.id : "None";
    }
    if (orientationPageFocus) {
      orientationPageFocus.textContent = focused ? focused.title || focused.nav_title || focused.id : "None";
    }
    if (orientationQuery) orientationQuery.textContent = query || "None";
    if (orientationFilters) {
      const pieces = [];
      const groupText = hiddenGroupStatusText();
      const edgeText = hiddenEdgeKindStatusText();
      if (groupText) pieces.push(groupText);
      if (edgeText) pieces.push(edgeText);
      orientationFilters.textContent = pieces.length ? pieces.join(" ") : "All groups and relationships visible";
    }
    if (orientationNeighborhood) {
      orientationNeighborhood.textContent = neighborhoodFocus ? "On" : "Off";
    }
    if (orientationOpen) {
      if (selected && selected.url) {
        orientationOpen.href = selected.url;
        orientationOpen.hidden = false;
      } else {
        orientationOpen.hidden = true;
      }
    }
    if (orientationNeighborhoodToggle) {
      orientationNeighborhoodToggle.hidden = !selected;
      orientationNeighborhoodToggle.textContent = neighborhoodFocus ? "Show full graph" : "Focus neighborhood";
    }
    if (orientationClear) orientationClear.hidden = !selected;
  }
```

- [ ] **Step 3: Replace selected detail incoming/outgoing derivation**

In `renderDetail()`, replace the current `outgoing` and `incoming` constants with:

```javascript
    const outgoing = explicitRelationshipsFor(node.id, "out");
    const incoming = explicitRelationshipsFor(node.id, "in");
```

- [ ] **Step 4: Call orientation updater during render**

After `lastActiveEdges = activeEdges;`, add:

```javascript
    updateGraphOrientation(activeNodes, activeEdges);
```

- [ ] **Step 5: Wire action controls near other event listeners**

Add:

```javascript
  if (orientationNeighborhoodToggle) {
    orientationNeighborhoodToggle.addEventListener("click", () => {
      if (!selectedId) return;
      neighborhoodFocus = !neighborhoodFocus;
      if (neighborhoodFocus) pageFocusId = "";
      render();
    });
  }

  if (orientationClear) {
    orientationClear.addEventListener("click", clearGraphSelection);
  }
```

- [ ] **Step 6: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_url_state_and_debug_readout -q
```

Expected: contract may still FAIL until CSS is added; browser behavior should no longer fail on missing selectors.

## Task 5: Style The Orientation Band

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add CSS near graph status styles**

Add:

```css
.raya-graph-orientation {
  display: grid;
  gap: 0.75rem;
  padding: 0.85rem;
  border: 1px solid var(--raya-border);
  background: color-mix(in srgb, var(--raya-surface) 88%, var(--raya-accent) 12%);
}

.raya-graph-orientation-main {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
  align-items: baseline;
  justify-content: space-between;
}

.raya-graph-orientation-counts,
.raya-graph-orientation-selection {
  margin: 0;
}

.raya-graph-orientation-meta {
  display: grid;
  gap: 0.5rem;
  grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr));
  margin: 0;
}

.raya-graph-orientation-meta div {
  min-width: 0;
}

.raya-graph-orientation-meta dt {
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
}

.raya-graph-orientation-meta dd {
  margin: 0.1rem 0 0;
  overflow-wrap: anywhere;
}

.raya-graph-orientation-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0;
}
```

- [ ] **Step 2: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_url_state_and_debug_readout -q
```

Expected: PASS.

## Task 6: Update Foundation And Role Docs

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update foundation graph paragraph**

Add the orientation band to the existing graph affordance list with language equivalent to:

```markdown
The graph may show a compact student-facing orientation band with visible page
and relationship counts, layout, selected page, URL page focus, search, filters,
and selected-neighborhood focus state, plus local actions for the selected page.
That band is structural graph context only and must not be progress, mastery,
ranking, recommendation, or personalization.
```

Also add that selected-page incoming/outgoing lists must use the same explicit
generated edge kinds as relationship chips and walkthroughs.

- [ ] **Step 2: Update role docs**

Add one short paragraph in each student guide explaining that the graph
orientation band tells what static graph view is visible and how to return from
neighborhood focus.

Add one short paragraph in each agent guide explaining that agents should verify
the orientation band from generated local graph state and should not treat it as
learner state.

- [ ] **Step 3: Run docs grep**

Run:

```bash
rg -n "orientation band|banda de orientaci|progress|recommendation|mastery|ranking|personal" docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/es/estudiantes/index.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md
```

Expected: orientation text appears; forbidden learner-state words only appear in boundary warnings.

## Task 7: Full Verification And Commit

**Files:**
- All files changed above.

- [ ] **Step 1: Run focused graph checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_url_state_and_debug_readout -q
```

Expected: PASS.

- [ ] **Step 2: Run render debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS with no raw visible TeX, no overflow, no external renderer requests.

- [ ] **Step 3: Run host gate**

Run:

```bash
./scripts/check.sh
```

Expected: PASS.

- [ ] **Step 4: Run Docker gate**

Run:

```bash
./scripts/check-docker.sh
```

Expected: PASS.

- [ ] **Step 5: Commit implementation**

Run:

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/es/estudiantes/index.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md
git commit -m "Add graph focus orientation band"
```

Expected: one implementation commit after passing verification.

## Self-Review

- Spec coverage: tasks cover orientation scaffolding, graph behavior, relationship-list consistency, styles, docs, and verification.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: all proposed selectors use the `data-raya-graph-orientation-*` prefix from the design.
