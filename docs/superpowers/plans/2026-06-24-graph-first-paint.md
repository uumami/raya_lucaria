# Graph First-Paint Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the graph workspace so page-focused graph handoffs show visible graph content immediately on desktop and remain usable on mobile.

**Architecture:** Keep the existing static SVG graph and local graph script. Change only the graph workspace layout CSS and add browser tests that assert selected graph content intersects the visible canvas area on first paint.

**Tech Stack:** Python static renderer, generated CSS in `packages/static/src/raya_static/rendering.py`, Playwright e2e tests in `tests/e2e/test_preview_static_read_path.py`.

---

### Task 1: Add A Failing Graph First-Paint Browser Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing test**

Add a browser assertion in the existing local visual graph test after opening `_raya/graph/index.html?page=reader-ux`. The assertion should compute the canvas, selected node, and visible edge bounding boxes in browser coordinates and require that the selected node and at least one edge intersect the canvas box.

- [ ] **Step 2: Run the focused test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: FAIL because the selected `reader-ux` node or graph edges are rendered outside the visible first-paint canvas area.

### Task 2: Bound Graph Workspace Canvas Height

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Implement minimal layout fix**

Change the graph workspace from stretched columns to start-aligned panels. Give `.raya-graph-canvas` a bounded height such as `height: clamp(28rem, 56vh, 40rem)`, keep `width: 100%`, and remove the flex growth that lets the canvas match side-panel height.

- [ ] **Step 2: Preserve expanded graph mode**

Keep expanded mode larger but bounded, for example `height: clamp(34rem, 72vh, 48rem)`.

- [ ] **Step 3: Run the focused test to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: PASS.

### Task 3: Contract And Regression Coverage

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Add contract assertions**

Assert `rich.css` contains bounded graph canvas height and graph workspace start alignment.

- [ ] **Step 2: Document the renderer invariant**

Update the graph contract to say page-focused graph handoffs must first-paint visible selected graph content and must keep graph canvas height bounded.

- [ ] **Step 3: Update agent guide notes**

Tell agents to verify graph handoffs by checking first-paint selected-node visibility, not only the presence of SVG nodes in the DOM.

### Task 4: Review, Verify, Commit, Push, Preview

- [ ] **Step 1: Request independent code review**

Use `superpowers:requesting-code-review` with at least one subagent focused on current renderer invariants and one focused on browser UX.

- [ ] **Step 2: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions -q
```

- [ ] **Step 3: Run full verification gates sequentially**

Run:

```bash
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

- [ ] **Step 4: Commit and push**

Commit with:

```bash
git add docs/superpowers/specs/2026-06-24-graph-first-paint-design.md docs/superpowers/plans/2026-06-24-graph-first-paint.md docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Fix graph first-paint visibility"
git push origin new_rayalucaria
```

- [ ] **Step 5: Start local preview**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --port 0
```

Report the local URL.
