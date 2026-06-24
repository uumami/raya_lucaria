# Graph Edge Readability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make graph relationship kinds visually scannable without changing artifact schema or static-resource boundaries.

**Architecture:** Reuse existing `edge.kind` values already embedded in the graph payload. Add SVG data/class markers in local `graph.js`, add CSS stroke patterns in `rich.css`, and explain the patterns in graph legend/help copy.

**Tech Stack:** Python static builder, local vanilla JavaScript SVG graph renderer, renderer CSS, pytest, Playwright.

---

### Task 1: Failing Edge-Kind Coverage

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] Add contract assertions that graph HTML contains legend entries:
  `data-raya-graph-legend="edge-navigation"`,
  `data-raya-graph-legend="edge-content"`,
  `data-raya-graph-legend="edge-prerequisite"`, and
  `data-raya-graph-legend="edge-parent"`.
- [x] Add contract assertions that graph help text includes relationship-kind
  wording and keeps the existing structural readability framing.
- [x] Add contract assertions that `graph.js` contains
  `data-raya-graph-kind` and `raya-graph-edge-kind-`.
- [x] Add contract assertions that `rich.css` contains selectors for
  `.raya-graph-edge-kind-navigation`,
  `.raya-graph-edge-kind-content`,
  `.raya-graph-edge-kind-prerequisite`, and
  `.raya-graph-edge-kind-parent`.
- [x] Add browser assertions in the graph fixture that known rendered edges
  expose expected `data-raya-graph-kind` values and kind classes:
  `render-root -> static-path` as `navigation`,
  `static-path -> render-root` as `parent`,
  `render-root -> authoring-matrix` as `content`, and
  `authoring-matrix -> math-authoring` as `prerequisite` when visible.
- [x] Run the focused graph tests and confirm they fail because the new
  legend, CSS, and SVG edge-kind markers do not exist yet.

### Task 2: Edge Markup And Styling

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] Add an `edgeKindClass(edge)` helper that accepts the generated `kind`
  string, normalizes it to lowercase ASCII letters/numbers/hyphens, and returns
  `raya-graph-edge-kind-link` when missing.
- [x] In SVG edge rendering, set `data-raya-graph-kind` to the normalized kind
  and append the kind class to the existing state classes.
- [x] Add CSS selectors for navigation, content, prerequisite, and parent
  edges. Preserve source-group color while using stroke dash arrays, opacity,
  and width to distinguish kinds.
- [x] Ensure active/inspected/search state selectors remain stronger than base
  kind styling.
- [x] Run the focused graph tests and keep implementation minimal until they
  pass.

### Task 3: Legend, Help, And Contract

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `docs/foundation/20_learning_renderer_contract.md`

- [x] Add four relationship-kind legend entries with line samples that reuse
  the CSS classes from Task 2.
- [x] Replace the generic explicit source-link legend wording with clearer
  relationship-kind wording.
- [x] Update graph help text to explain source-group edge color and
  relationship-kind line patterns as structural readability cues only.
- [x] Update the foundation renderer contract to permit generated
  relationship-kind edge patterns while preserving the non-goal wording.
- [x] Run focused contract and browser tests.

### Task 4: Review And Verification

**Files:**
- Modify this plan as statuses change.

- [x] Request independent code review focused on static-resource boundaries,
  graph semantics, accessibility/readability, and learner-state wording.
- [x] Fix accepted review findings with tests first where behavior changes.
- [x] Run `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q`.
- [x] Run `./scripts/check-render-debug.sh`.
- [x] Run `./scripts/check.sh`.
- [ ] Commit and push to `origin/new_rayalucaria`.
