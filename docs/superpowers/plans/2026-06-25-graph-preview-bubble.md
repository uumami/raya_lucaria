# Graph Preview Bubble Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded, transient graph preview bubble that adapts the old branch's pointer-local graph feedback to the current static SVG graph.

**Architecture:** The builder emits one hidden bubble surface in the graph map panel. The existing graph JavaScript populates and positions it from already loaded graph payload data when the existing inspection state changes. The renderer stylesheet provides bounded visual styling, responsive suppression, and reduced-motion-safe transitions.

**Tech Stack:** Python static builder, embedded local JavaScript in `packages/static/src/raya_static/graph.py`, CSS in `packages/static/src/raya_static/rendering.py`, pytest and Playwright e2e tests.

---

## File Map

- Modify `tests/contracts/test_static_builder.py` to assert graph HTML/CSS/JS contract markers for the bubble.
- Modify `tests/e2e/test_preview_static_read_path.py` to verify hover/focus bubble behavior and overflow safety in a real browser.
- Modify `packages/static/src/raya_static/builder.py` to render the hidden bubble markup.
- Modify `packages/static/src/raya_static/graph.py` to populate, position, and hide the bubble through existing inspection events.
- Modify `packages/static/src/raya_static/rendering.py` to style and responsively suppress the bubble.
- Modify `docs/foundation/20_learning_renderer_contract.md` and student guides in `docs/guides/en/students/index.md` and `docs/guides/es/estudiantes/index.md`.

## Task 1: Contract Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write failing contract assertions**

Add assertions to the existing graph/static-builder test that already reads generated graph HTML, CSS, and JS. Assert these tokens:

```python
assert 'class="raya-graph-preview-bubble"' in graph_html
assert "data-raya-graph-preview-bubble hidden" in graph_html
assert "data-raya-graph-preview-title" in graph_html
assert "data-raya-graph-preview-summary" in graph_html
assert "data-raya-graph-preview-counts" in graph_html
assert ".raya-graph-preview-bubble" in css
assert "@media (max-width: 720px)" in css
assert "data-raya-graph-preview-bubble" in graph_js
assert "showGraphPreviewBubble" in graph_js
assert "hideGraphPreviewBubble" in graph_js
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
```

Expected: fails because the graph preview bubble markup and JavaScript markers do not exist yet.

- [ ] **Step 3: Stop after RED**

Do not modify production code until the failure is confirmed.

## Task 2: Browser Behavior Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing Playwright test**

Add a focused test near the existing graph e2e tests:

```python
def test_preview_graph_node_preview_bubble_tracks_hover_and_focus(tmp_path: Path) -> None:
    from playwright.sync_api import expect, sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        base_url = handle.base_url
        assert base_url is not None

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 960})
                try:
                    page.goto(f"{base_url}/_raya/graph/index.html", wait_until="networkidle")
                    bubble = page.locator("[data-raya-graph-preview-bubble]")
                    expect(bubble).to_be_hidden()

                    node = page.locator(
                        '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                    )
                    node.hover()
                    expect(bubble).to_be_visible()
                    expect(page.locator("[data-raya-graph-preview-title]")).to_contain_text(
                        "Authoring Matrix Fixture"
                    )
                    expect(page.locator("[data-raya-graph-preview-counts]")).to_contain_text(
                        "connected"
                    )

                    bounds = bubble.bounding_box()
                    assert bounds is not None
                    assert bounds["x"] >= 0
                    assert bounds["x"] + bounds["width"] <= 1440

                    page.keyboard.press("Escape")
                    expect(bubble).to_be_hidden()

                    node.focus()
                    expect(bubble).to_be_visible()
                    _assert_no_horizontal_overflow(page)
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_graph_node_preview_bubble_tracks_hover_and_focus -q
```

Expected: fails because the bubble surface does not exist.

## Task 3: Builder Markup And CSS

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add hidden bubble markup**

Insert this section in the graph map panel after the SVG canvas and before the existing in-flow inspection preview:

```html
<section class="raya-graph-preview-bubble" data-raya-graph-preview-bubble hidden aria-hidden="true">
  <p class="raya-graph-preview-kicker" data-raya-graph-preview-meta></p>
  <h2 data-raya-graph-preview-title>Graph page</h2>
  <p data-raya-graph-preview-summary></p>
  <p class="raya-graph-preview-counts" data-raya-graph-preview-counts></p>
</section>
```

- [ ] **Step 2: Add CSS**

Add `.raya-graph-map-panel { position: relative; }` if not already present, then add:

```css
.raya-graph-preview-bubble {
  background: color-mix(in srgb, var(--raya-color-surface) 94%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-accent);
  border-radius: 0.5rem;
  box-shadow: 0 1rem 2rem color-mix(in srgb, var(--raya-color-text) 18%, transparent);
  color: var(--raya-color-text);
  inline-size: min(19rem, calc(100% - 2rem));
  left: 1rem;
  padding: 0.85rem 0.95rem;
  pointer-events: none;
  position: absolute;
  top: 1rem;
  transform: translate(var(--raya-graph-preview-x, 0), var(--raya-graph-preview-y, 0));
  z-index: 4;
}

.raya-graph-preview-bubble[hidden] {
  display: none;
}

.raya-graph-preview-bubble h2,
.raya-graph-preview-bubble p {
  margin: 0;
}

.raya-graph-preview-bubble h2 {
  font-size: 1rem;
  line-height: 1.25;
}

.raya-graph-preview-kicker,
.raya-graph-preview-counts {
  color: var(--raya-color-muted);
  font-size: 0.78rem;
}

.raya-graph-preview-bubble h2 + p,
.raya-graph-preview-bubble p + p {
  margin-top: 0.35rem;
}

@media (max-width: 720px) {
  .raya-graph-preview-bubble {
    display: none;
  }
}
```

- [ ] **Step 3: Run contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
```

Expected: CSS/markup assertions pass except JavaScript marker assertions until Task 4.

## Task 4: JavaScript Behavior

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [ ] **Step 1: Wire bubble elements**

Add DOM lookups near the existing inspection preview lookups:

```javascript
const graphPreviewBubble = document.querySelector("[data-raya-graph-preview-bubble]");
const graphPreviewMeta = document.querySelector("[data-raya-graph-preview-meta]");
const graphPreviewTitle = document.querySelector("[data-raya-graph-preview-title]");
const graphPreviewSummary = document.querySelector("[data-raya-graph-preview-summary]");
const graphPreviewCounts = document.querySelector("[data-raya-graph-preview-counts]");
```

- [ ] **Step 2: Add helpers**

Add helpers near `renderInspectionPreview()`:

```javascript
function hideGraphPreviewBubble() {
  if (!graphPreviewBubble) return;
  graphPreviewBubble.hidden = true;
  graphPreviewBubble.setAttribute("aria-hidden", "true");
}

function graphPointToPanelOffset(point) {
  if (!point || !canvas || !graphViewBox) return null;
  const canvasBox = canvas.getBoundingClientRect();
  const panelBox = canvas.parentElement
    ? canvas.parentElement.getBoundingClientRect()
    : canvasBox;
  const scaleX = canvasBox.width / graphViewBox.width;
  const scaleY = canvasBox.height / graphViewBox.height;
  return {
    x: canvasBox.left - panelBox.left + (point.x - graphViewBox.x) * scaleX,
    y: canvasBox.top - panelBox.top + (point.y - graphViewBox.y) * scaleY,
    panelWidth: panelBox.width,
    panelHeight: panelBox.height,
  };
}

function showGraphPreviewBubble(nodeId) {
  if (!graphPreviewBubble) return;
  const node = nodesById.get(nodeId);
  const point = latestRenderedPositions.get(nodeId);
  const offset = graphPointToPanelOffset(point);
  if (!node || !offset) {
    hideGraphPreviewBubble();
    return;
  }
  if (graphPreviewTitle) graphPreviewTitle.textContent = node.title || node.nav_title || node.id;
  if (graphPreviewMeta) graphPreviewMeta.textContent = inspectionPreviewTextFor(node);
  if (graphPreviewSummary) graphPreviewSummary.textContent = node.summary || "No summary available.";
  if (graphPreviewCounts) graphPreviewCounts.textContent = inspectionPreviewCountTextFor(node.id);

  graphPreviewBubble.hidden = false;
  graphPreviewBubble.setAttribute("aria-hidden", "false");
  const bubbleBox = graphPreviewBubble.getBoundingClientRect();
  const margin = 16;
  const targetX = offset.x + 22;
  const targetY = offset.y - Math.min(64, bubbleBox.height / 2);
  const maxX = Math.max(margin, offset.panelWidth - bubbleBox.width - margin);
  const maxY = Math.max(margin, offset.panelHeight - bubbleBox.height - margin);
  const x = Math.min(Math.max(margin, targetX), maxX);
  const y = Math.min(Math.max(margin, targetY), maxY);
  graphPreviewBubble.style.setProperty("--raya-graph-preview-x", `${x - margin}px`);
  graphPreviewBubble.style.setProperty("--raya-graph-preview-y", `${y - margin}px`);
}
```

- [ ] **Step 3: Connect helpers to existing inspection lifecycle**

Call `showGraphPreviewBubble(inspectedId)` after `renderInspectionPreview(inspectedId)` when `inspectedId` is valid. Call `hideGraphPreviewBubble()` in all paths that clear `inspectedId`, enter list layout, reset graph, or leave the canvas.

- [ ] **Step 4: Run RED tests again and make them GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_graph_node_preview_bubble_tracks_hover_and_focus -q
```

Expected: both pass.

## Task 5: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`

- [ ] **Step 1: Update foundation contract**

Add the graph preview bubble to the static graph paragraph as transient hover/focus context over public generated graph data. State that it is not progress, ranking, mastery, recommendation, personalization, or authority.

- [ ] **Step 2: Update student docs**

English: explain that hovering or focusing graph nodes can show a small local preview, while the inspector remains the stable detail surface.

Spanish: explain the same in Spanish without mixing languages except technical labels and paths.

- [ ] **Step 3: Run docs-related focused checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
```

Expected: pass.

## Task 6: Verification And Review

**Files:**
- No direct edits expected unless review finds issues.

- [ ] **Step 1: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_graph_node_preview_bubble_tracks_hover_and_focus -q
./scripts/check-render-debug.sh
```

Expected: all pass.

- [ ] **Step 2: Request independent code review**

Ask one independent reviewer to inspect the implementation for current-branch contract alignment, accessibility, static constraints, and layout risks.

- [ ] **Step 3: Address review feedback with tests first when behavior changes**

If the reviewer finds a behavior bug, add or tighten a failing test before changing production code.

- [ ] **Step 4: Run archive gates if review is clean**

Run sequentially:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both pass.

- [ ] **Step 5: Commit and push**

Commit the implementation and docs, then push `new_rayalucaria` to `origin/new_rayalucaria`.

