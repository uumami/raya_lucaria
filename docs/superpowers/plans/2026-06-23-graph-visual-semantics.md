# Graph Visual Semantics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve Course graph readability with group color, bounded degree sizing, and transient hover/focus inspection.

**Architecture:** Keep the current static graph page and embedded payload. Add stable graph affordance markup in the Python builder, compute visual semantics in the existing local graph script, and style the new states in `rich.css` without changing artifact schemas or loading external graph libraries.

**Tech Stack:** Python static builder, embedded local JavaScript in `packages/static/src/raya_static/graph.py`, static CSS in `packages/static/src/raya_static/rendering.py`, pytest contract tests, Playwright e2e tests.

---

### Task 1: Contract Surface

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Write failing graph markup/script assertions**

In `test_build_writes_local_visual_graph_surface`, add assertions:

```python
assert "raya-graph-instructions" in graph_html
assert "Hover or focus a page" in graph_html
assert "data-raya-graph-hover-status" in graph_html
assert "style=\"--raya-graph-group-color:" in graph_html
assert "raya-graph-group-swatch" in graph_html
assert "degreeRadiusFor" in graph_script
assert "inspectGraphNode" in graph_script
assert "is-inspected" in graph_script
assert "is-inspected-neighbor" in graph_script
assert "cytoscape" not in graph_script.lower()
assert "fetch(" not in graph_script
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: FAIL because instruction text, hover status, group swatches, and inspected-node behavior do not exist yet.

### Task 2: Browser Behavior

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Write failing browser assertions**

In `test_preview_serves_local_visual_graph_surface`, after the initial graph load and before navigation assertions, hover/focus a known graph node and assert:

```python
page.locator('#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]').hover()
page.wait_for_function(
    """() => document
      .querySelector('[data-raya-graph-hover-status]')
      ?.textContent
      ?.includes('Inspecting Authoring Matrix Fixture')"""
)
assert page.locator(
    '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"] g'
).evaluate("node => node.classList.contains('is-inspected')")
for node_id in ("render-root", "math-authoring", "numbered-objects", "reader-ux"):
    assert page.locator(
        f'#raya-graph-canvas [data-raya-graph-node="{node_id}"] g'
    ).evaluate("node => node.classList.contains('is-inspected-neighbor')")

page.locator('#raya-graph-list [data-raya-graph-node="authoring-matrix"] a').focus()
page.wait_for_function(
    """() => document
      .querySelector('[data-raya-graph-hover-status]')
      ?.textContent
      ?.includes('Inspecting Authoring Matrix Fixture')"""
)
assert requested_urls == []
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: FAIL because hover/focus inspection status and classes do not exist yet.

### Task 3: Builder Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Add deterministic group colors**

Near the graph surface builder, define a small palette tuple:

```python
GRAPH_GROUP_COLORS = (
    "var(--raya-graph-group-1)",
    "var(--raya-graph-group-2)",
    "var(--raya-graph-group-3)",
    "var(--raya-graph-group-4)",
    "var(--raya-graph-group-5)",
    "var(--raya-graph-group-6)",
    "var(--raya-graph-group-7)",
    "var(--raya-graph-group-8)",
)
```

When rendering `group_buttons`, add a swatch and style:

```python
group_color = GRAPH_GROUP_COLORS[index % len(GRAPH_GROUP_COLORS)]
(
    '<button class="raya-graph-chip" type="button" '
    f'style="--raya-graph-group-color: {group_color}" '
    f'data-raya-graph-group-filter="{html.escape(group["id"], quote=True)}" '
    'aria-pressed="true">'
    '<span class="raya-graph-group-swatch" aria-hidden="true"></span>'
    f'{html.escape(group["title"])}'
    "</button>"
)
```

- [x] **Step 2: Add instruction and hover status placeholders**

In `_render_graph_surface`, add an instruction paragraph near the controls:

```html
<p class="raya-graph-instructions">Hover or focus a page to inspect nearby structure. Click to select it; double-click a graph node or open the detail link to navigate.</p>
```

Add a hover status line after the existing graph status:

```html
<p class="raya-graph-hover-status" data-raya-graph-hover-status aria-live="polite"></p>
```

- [x] **Step 3: Verify contract GREEN for markup only**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: still FAIL on script tokens, but no longer fail on new HTML/CSS placeholder tokens.

### Task 4: Graph Script Behavior

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [x] **Step 1: Add derived semantics helpers**

Add `hoverStatus`, `inspectedId`, `degreeFor(nodeId)`, `degreeRadiusFor(nodeId, selected)`, `groupColorIndex(groupId)`, and `inspectionTextFor(nodeId)` helpers. Use current `edges`, `groups`, and `nodesById`.

- [x] **Step 2: Add inspection state**

Add:

```javascript
function inspectGraphNode(nodeId) {
  inspectedId = nodesById.has(nodeId) ? nodeId : "";
  if (hoverStatus) hoverStatus.textContent = inspectedId ? inspectionTextFor(inspectedId) : "";
  render();
}
```

Add `clearGraphInspection()` for `mouseout` and `blur`, but keep selected detail state intact.

- [x] **Step 3: Mark inspected SVG nodes and edges**

In `render()`, compute `inspectedConnectedIds`. Add `is-inspected` to the inspected node and `is-inspected-neighbor` to connected nodes. Add `is-inspected` to edges touching the inspected node.

- [x] **Step 4: Add SVG/list focus and hover handlers**

For SVG links, add `mouseenter`, `mouseleave`, `focus`, and `blur`. For list links, add delegated listeners or per-link listeners in `renderList(activeIds)`.

- [x] **Step 5: Use bounded degree radius and group colors**

Set circle radius with `degreeRadiusFor(node.id, node.id === selectedId)`. Set a group custom property or data attribute so CSS can use the deterministic group color.

- [x] **Step 6: Verify focused GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: PASS.

### Task 5: CSS And Docs

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Style visual semantics**

Add styles for:

```css
.raya-graph-instructions,
.raya-graph-hover-status
.raya-graph-group-swatch
.raya-graph-node.is-inspected
.raya-graph-node.is-inspected-neighbor
.raya-graph-edge.is-inspected
.raya-graph-list li.is-inspected
.raya-graph-list li.is-inspected-neighbor
```

Use existing skin tokens and new graph group CSS variables. Do not introduce external colors outside the token system.

- [x] **Step 2: Document graph visual semantics**

Document that graph colors, node size, and hover/focus inspection are structural readability cues from generated graph data, not progress, recommendations, authority, or mastery.

- [x] **Step 3: Verify docs/focused gates**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_renderer_dependencies.py::test_docs_cover_collapsible_learning_shell tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
./scripts/check-render-debug.sh
```

Expected: all commands exit 0.

### Task 6: Review, Full Gates, Commit, Push

**Files:**
- All files changed in this plan.

- [x] **Step 1: Request independent review**

Dispatch a read-only reviewer focused on static graph boundaries, no external dependency regression, keyboard parity for hover inspection, no progress/recommendation wording, and mobile/static read-path safety.

- [x] **Step 2: Full verification**

Run sequentially:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both commands exit 0.

- [x] **Step 3: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-23-graph-visual-semantics-design.md \
  docs/superpowers/plans/2026-06-23-graph-visual-semantics.md \
  docs/foundation/20_learning_renderer_contract.md \
  docs/guides/en/students/index.md docs/guides/en/agents/index.md \
  docs/guides/es/estudiantes/index.md docs/guides/es/agentes/index.md \
  packages/static/src/raya_static/builder.py \
  packages/static/src/raya_static/graph.py \
  packages/static/src/raya_static/rendering.py \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph visual semantics"
git push origin new_rayalucaria
```

Expected: branch `new_rayalucaria` advances on GitHub.
