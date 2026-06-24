# Graph Keyboard Result Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let learners move through graph search results from the search field with keyboard controls while keeping the list, SVG map, and inspector synchronized.

**Architecture:** Reuse the existing graph script and visible list DOM. Add transient `activeResultId` state, helpers for visible result IDs, and keyboard handling on the graph search input. Style and document the active result as a local structural navigation cue.

**Tech Stack:** Python 3.10 package resources that emit static HTML/CSS/JS, pytest, Playwright e2e static preview tests.

---

## File Structure

- `packages/static/src/raya_static/graph.py`: owns graph interaction behavior and active-result synchronization.
- `packages/static/src/raya_static/rendering.py`: owns generated graph active-result styles.
- `packages/static/src/raya_static/builder.py`: owns generated graph help copy.
- `docs/foundation/20_learning_renderer_contract.md`: authoritative renderer contract wording.
- `docs/guides/en/agents/index.md`: English agent verification guidance.
- `docs/guides/es/agentes/index.md`: Spanish agent verification guidance.
- `tests/contracts/test_static_builder.py`: generated graph script/CSS assertions.
- `tests/e2e/test_preview_static_read_path.py`: browser assertions for graph keyboard result flow.

## Task 1: Failing Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add contract assertions**

In `test_build_writes_local_visual_graph_surface`, assert:

```python
assert "activeResultId" in graph_script
assert "setActiveResult" in graph_script
assert "moveActiveResult" in graph_script
assert "is-active-result" in graph_script
assert ".raya-graph-list li.is-active-result a" in stylesheet
```

- [ ] **Step 2: Add browser keyboard flow assertions**

In `test_preview_serves_local_visual_graph_surface`, after the graph search field is known visible, add a block that:

```python
page.fill("#graph-search", "matrix")
page.press("#graph-search", "ArrowDown")
page.wait_for_function(
    """() => document
      .querySelector('#raya-graph-list [data-raya-graph-node].is-active-result')
      ?.getAttribute('data-raya-graph-node')"""
)
first_active = page.locator(
    "#raya-graph-list [data-raya-graph-node].is-active-result"
).get_attribute("data-raya-graph-node")
assert first_active
assert page.locator(
    f'#raya-graph-list [data-raya-graph-node="{first_active}"] a'
).get_attribute("aria-current") == "true"
assert page.locator("[data-raya-graph-detail-panel]").is_visible()
assert page.locator(
    f'#raya-graph-canvas [data-raya-graph-node="{first_active}"] g'
).evaluate("node => node.classList.contains('is-inspected')")

page.press("#graph-search", "ArrowDown")
second_active = page.locator(
    "#raya-graph-list [data-raya-graph-node].is-active-result"
).get_attribute("data-raya-graph-node")
assert second_active
assert second_active != first_active

page.press("#graph-search", "ArrowUp")
assert (
    page.locator("#raya-graph-list [data-raya-graph-node].is-active-result")
    .get_attribute("data-raya-graph-node")
    == first_active
)

page.fill("#graph-search", "zz-no-result")
before_url = page.url
page.press("#graph-search", "Enter")
assert page.url == before_url
```

Then use a fresh graph page to verify Enter navigation:

```python
page.goto(f"{base_url}/_raya/graph/index.html", wait_until="networkidle")
page.fill("#graph-search", "matrix")
page.press("#graph-search", "ArrowDown")
target_href = page.locator(
    "#raya-graph-list [data-raya-graph-node].is-active-result a"
).evaluate("node => node.href")
page.press("#graph-search", "Enter")
page.wait_for_url(target_href)
```

- [ ] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: FAIL because active-result helpers/classes do not exist.

## Task 2: Graph Script And CSS Implementation

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add active result state**

In `packages/static/src/raya_static/graph.py`, near `selectedId`, add:

```javascript
  let activeResultId = "";
```

- [ ] **Step 2: Add visible result helpers**

Add helpers near `renderList(activeIds)`:

```javascript
  function currentVisibleListIds() {
    return Array.from(list.querySelectorAll("[data-raya-graph-node]"))
      .filter((item) => !item.hidden)
      .map((item) => item.getAttribute("data-raya-graph-node") || "")
      .filter(Boolean);
  }

  function activeResultUrl() {
    if (!activeResultId) return "";
    const link = list.querySelector(
      `[data-raya-graph-node="${window.CSS && CSS.escape ? CSS.escape(activeResultId) : activeResultId}"] a`
    );
    return link ? link.href : "";
  }
```

When implementing, avoid relying on `CSS.escape` for selector construction by using a small DOM scan if needed.

- [ ] **Step 3: Add active result setter**

Add:

```javascript
  function setActiveResult(nodeId, options = {}) {
    const visibleIds = currentVisibleListIds();
    activeResultId = visibleIds.includes(nodeId) ? nodeId : "";
    list.querySelectorAll("[data-raya-graph-node]").forEach((item) => {
      const id = item.getAttribute("data-raya-graph-node") || "";
      const active = id === activeResultId;
      item.classList.toggle("is-active-result", active);
      const link = item.querySelector("a");
      if (link) {
        if (active) link.setAttribute("aria-current", "true");
        else link.removeAttribute("aria-current");
      }
      if (active && options.scroll !== false) {
        item.scrollIntoView({ block: "nearest" });
      }
    });
    if (activeResultId) {
      selectedId = activeResultId;
      inspectedId = activeResultId;
      renderDetail();
      updateInspectionDom();
    } else {
      clearGraphInspection();
    }
  }
```

- [ ] **Step 4: Add active result movement**

Add:

```javascript
  function moveActiveResult(delta) {
    const visibleIds = currentVisibleListIds();
    if (visibleIds.length === 0) {
      setActiveResult("");
      return;
    }
    const currentIndex = activeResultId ? visibleIds.indexOf(activeResultId) : -1;
    const baseIndex = currentIndex >= 0 ? currentIndex : (delta > 0 ? -1 : 0);
    const nextIndex = (baseIndex + delta + visibleIds.length) % visibleIds.length;
    setActiveResult(visibleIds[nextIndex]);
  }
```

- [ ] **Step 5: Wire search rendering**

After `renderList(listIds)` in `render()`, keep active state valid:

```javascript
    if (activeResultId && !listIds.has(activeResultId)) {
      activeResultId = "";
    }
```

At the end of `render()`, call `setActiveResult(activeResultId, { scroll: false })` when `activeResultId` exists so rebuilt SVG/list DOM keeps synchronized classes.

In the search input `input` handler, reset and activate first visible result:

```javascript
      activeResultId = "";
      graphViewBox = null;
      render();
      const visibleIds = currentVisibleListIds();
      if (query && visibleIds.length > 0) {
        setActiveResult(visibleIds[0], { scroll: false });
      }
```

- [ ] **Step 6: Wire keyboard controls**

Add a `keydown` listener on `search`:

```javascript
    search.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        moveActiveResult(1);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        moveActiveResult(-1);
      } else if (event.key === "Enter") {
        const href = activeResultUrl();
        if (href) {
          event.preventDefault();
          window.location.href = href;
        }
      }
    });
```

- [ ] **Step 7: Add CSS**

In `packages/static/src/raya_static/rendering.py`, near graph list active styles, add:

```css
.raya-graph-list li.is-active-result a {
  outline: 2px solid var(--raya-color-accent);
  outline-offset: 2px;
  background: color-mix(in srgb, var(--raya-color-accent) 12%, transparent);
}
```

- [ ] **Step 8: Add help copy**

In graph help copy in `packages/static/src/raya_static/builder.py`, add a short sentence:

```html
<p>When search is focused, Arrow keys move through visible page results and Enter opens the active result.</p>
```

- [ ] **Step 9: Verify GREEN**

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

Add that the static graph page may provide keyboard result movement from search to visible results, with synchronized list/map/detail context.

- [ ] **Step 2: Update English agent guidance**

Add that agents should verify graph search keyboard result movement is transient, local, and not described as progress/ranking/recommendation.

- [ ] **Step 3: Update Spanish agent guidance**

Add equivalent Spanish guidance while keeping technical identifiers like `ArrowDown`, `ArrowUp`, and `Enter` in English.

- [ ] **Step 4: Verify focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/contracts/test_static_builder.py::test_render_fixture_search_graph_course_map_visible_text_avoids_learner_state_language tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: PASS.

## Task 4: Review And Gates

**Files:**
- No direct edits unless review finds issues.

- [ ] **Step 1: Request independent code review**

Ask a subagent to review current working tree for Critical/Important issues in graph keyboard result flow, static constraints, and accessibility.

- [ ] **Step 2: Fix valid Critical/Important findings**

Use TDD for any behavior change found by review.

- [ ] **Step 3: Run verification**

Run:

```bash
git diff --check
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: all pass. Run `check.sh` and `check-docker.sh` sequentially, not concurrently.

- [ ] **Step 4: Commit and push**

Commit the implementation and push:

```bash
git add docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph keyboard result flow"
git push origin new_rayalucaria
```

## Self-Review

- The plan covers every design goal.
- The task list starts with failing tests before implementation.
- No placeholders remain.
- The plan keeps graph state transient and avoids external resources/storage.
