# Graph Search Spotlight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make graph search visually spotlight matched pages and their explicit one-hop context without changing static data contracts.

**Architecture:** Reuse the current graph script's local fuzzy search and `matchIds` state. Add derived search spotlight classes during graph render, style those classes in the static renderer CSS, and document them as non-persistent structural readability cues.

**Tech Stack:** Python 3.10 package resources that emit static HTML/CSS/JS, pytest, Playwright e2e static preview tests.

---

## File Structure

- `packages/static/src/raya_static/graph.py`: owns local graph interaction behavior and SVG/list class application.
- `packages/static/src/raya_static/rendering.py`: owns graph visual classes in the generated local stylesheet.
- `packages/static/src/raya_static/builder.py`: owns generated graph help/legend copy.
- `docs/foundation/20_learning_renderer_contract.md`: authoritative renderer contract wording.
- `docs/guides/en/agents/index.md`: English agent verification guidance.
- `docs/guides/es/agentes/index.md`: Spanish agent verification guidance.
- `tests/contracts/test_static_builder.py`: generated HTML/CSS/JS contract assertions.
- `tests/e2e/test_preview_static_read_path.py`: browser behavior assertions for graph search spotlight.

## Task 1: Failing Contract And Browser Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add contract assertions**

In `test_build_writes_local_visual_graph_surface`, assert the generated graph help and script expose search spotlight behavior:

```python
assert "Search spotlight" in graph_html
assert "search spotlight is a structural readability cue" in graph_html
assert "searchSpotlightIds" in graph_script
assert "searchContextNodeIds" in graph_script
assert "is-search-context" in graph_script
assert "is-search-dimmed" in graph_script
```

- [ ] **Step 2: Add browser assertions**

In `test_preview_serves_local_visual_graph_surface`, after the existing `page.fill("#graph-search", "nested")` search block or in a nearby search block where enough nodes remain visible, assert search spotlight classes:

```python
page.fill("#graph-search", "matrix")
page.wait_for_function(
    """() => document
      .querySelector('#raya-graph-canvas [data-raya-graph-node="authoring-matrix"] g')
      ?.classList
      ?.contains('is-match')"""
)
assert page.locator(
    '#raya-graph-canvas [data-raya-graph-node="render-root"] g'
).evaluate("node => node.classList.contains('is-search-context')")
assert page.locator(
    '#raya-graph-canvas [data-raya-graph-node="static-path"] g'
).evaluate("node => node.classList.contains('is-search-dimmed')")
assert page.locator(
    '#raya-graph-canvas .raya-graph-edge[data-raya-graph-from="render-root"][data-raya-graph-to="authoring-matrix"]'
).evaluate("edge => edge.classList.contains('is-search-context')")
assert page.locator(
    '#raya-graph-canvas .raya-graph-edge.is-search-dimmed'
).count() > 0
page.click("#graph-reset")
assert (
    page.locator("#raya-graph-canvas .raya-graph-node.is-search-dimmed").count()
    == 0
)
assert (
    page.locator("#raya-graph-canvas .raya-graph-edge.is-search-dimmed").count()
    == 0
)
```

- [ ] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: FAIL because `Search spotlight`, `searchSpotlightIds`, and search spotlight classes are not implemented yet.

## Task 2: Graph Script And CSS Implementation

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add derived search spotlight helpers**

In `packages/static/src/raya_static/graph.py`, near `visibleNodes()`, add helpers that derive spotlight sets from the current `query` and `matchIds`:

```javascript
  function searchSpotlightIds() {
    if (!query || matchIds.size === 0) return new Set();
    const ids = new Set(matchIds);
    matchIds.forEach((id) => {
      neighborsOf(id).forEach((neighborId) => {
        const neighbor = nodesById.get(neighborId);
        if (neighbor && !hiddenGroups.has(neighbor.group || "")) {
          ids.add(neighborId);
        }
      });
    });
    return ids;
  }

  function searchContextNodeIds() {
    if (!query || matchIds.size === 0) return new Set();
    const ids = searchSpotlightIds();
    matchIds.forEach((id) => ids.delete(id));
    return ids;
  }
```

- [ ] **Step 2: Apply classes during render**

In `render()`, after computing `activeIds`, derive:

```javascript
    const searchSpotlight = searchSpotlightIds();
    const searchContext = searchContextNodeIds();
```

Use those sets when rendering edges and nodes:

```javascript
          query && (matchIds.has(edge.from) || matchIds.has(edge.to))
            ? "is-search-context"
            : "",
          query && !(matchIds.has(edge.from) || matchIds.has(edge.to))
            ? "is-search-dimmed"
            : "",
```

and:

```javascript
          searchContext.has(node.id) ? "is-search-context" : "",
          query && !searchSpotlight.has(node.id) ? "is-search-dimmed" : "",
```

- [ ] **Step 3: Preserve classes during inspection DOM updates**

In `updateInspectionDom()`, derive the same sets and toggle `is-search-context` / `is-search-dimmed` on existing SVG nodes and edges. This keeps classes correct after hover/focus changes without requiring a full render.

- [ ] **Step 4: Add CSS**

In `packages/static/src/raya_static/rendering.py`, near existing graph edge/node states, add:

```css
.raya-graph-edge.is-search-context {
  opacity: 0.82;
}

.raya-graph-edge.is-search-dimmed {
  opacity: 0.12;
}

.raya-graph-node.is-search-context circle {
  fill: color-mix(in srgb, var(--raya-graph-node-color, var(--raya-color-accent)) 34%, var(--raya-color-surface));
}

.raya-graph-node.is-search-dimmed {
  opacity: 0.18;
}
```

- [ ] **Step 5: Add graph help copy**

In `_render_graph_surface()` in `packages/static/src/raya_static/builder.py`, add help text:

```html
<p>Search spotlight keeps matching pages visually primary, keeps directly connected pages visible as context, and dims unrelated visible graph structure. The search spotlight is a structural readability cue only, not learner state or personal guidance.</p>
```

- [ ] **Step 6: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: PASS.

## Task 3: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update foundation wording**

In the static graph page paragraph, include:

```markdown
transient search spotlighting over matched pages and directly connected context
```

Keep the surrounding sentence explicit that these are readability cues only.

- [ ] **Step 2: Update English agent guide**

Add graph verification wording that agents should confirm search spotlight classes are transient, local, and not described as ranking/progress/recommendations.

- [ ] **Step 3: Update Spanish agent guide**

Add the matching Spanish guidance in `docs/guides/es/agentes/index.md`, keeping technical identifiers in English.

- [ ] **Step 4: Verify docs and focused visible-language guard**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_search_graph_course_map_visible_text_avoids_learner_state_language
```

Expected: PASS.

## Task 4: Final Verification And Review

**Files:**
- Review all changed files.

- [ ] **Step 1: Run focused tests**

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

Expected: PASS and no external renderer requests.

- [ ] **Step 3: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 4: Request code review**

Dispatch a reviewer with the design, plan, base SHA, head SHA/diff, and focused verification output. Fix Critical or Important findings before commit.

- [ ] **Step 5: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-06-24-graph-search-spotlight-design.md docs/superpowers/plans/2026-06-24-graph-search-spotlight.md docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph search spotlighting"
```

Expected: commit succeeds.

## Self-Review

- Every design requirement has a corresponding test or implementation step.
- No placeholders or deferred implementation steps remain.
- The plan does not add external dependencies, runtime fetching, storage, or schema changes.
- The plan keeps search spotlighting framed as structural readability, not learner guidance.
