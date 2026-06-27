# Graph Page Sections Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show public rendered page-section jump links inside the Graph selected-page detail panel.

**Architecture:** Reuse the existing public section records produced for Search, copy a bounded public subset into each graph node payload during static build, and render those links locally in `graph.js` with no fetch, storage, or source-path exposure.

**Tech Stack:** Python static builder, generated local JavaScript, pytest contract tests, Playwright e2e tests.

---

### Task 1: Failing Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add graph payload contract assertions**

In `tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface`, add `sections` to the allowed graph node keys. Assert `authoring_node["sections"]` contains a section titled `Matrix norm fixture` with:

```python
{
    "id": "authoring-matrix:raya-object-authoring-theorem",
    "anchor": "raya-object-authoring-theorem",
    "kind": "numbered-object",
    "title": "Matrix norm fixture",
    "url": "../../authoring-matrix/index.html#raya-object-authoring-theorem",
}
```

Also assert every section item has only `id`, `anchor`, `kind`, `title`, and `url`; every URL starts with the selected node rendered `url` plus `#`; and no section item contains `search_text`, `search_snippet`, `source_path`, `_official`, `_reviewed`, `_assets`, `artifact`, `cache_key`, raw TeX, or MathJax internals.

- [x] **Step 2: Add graph detail hook assertions**

In the same contract test, assert generated graph HTML contains:

```html
data-raya-graph-detail-sections
data-raya-graph-detail-section-list
<h3>Page sections</h3>
```

Assert generated graph JavaScript contains `renderDetailSections`.

- [x] **Step 3: Add browser behavior test**

In `tests/e2e/test_preview_static_read_path.py`, add `test_render_fixture_graph_detail_shows_public_section_jumps`. The test opens `_raya/graph/index.html?page=authoring-matrix`, waits for the selected detail panel, asserts:

- the `Page sections` block is visible;
- at least one link text contains `Matrix norm fixture`;
- the link href ends with `/authoring-matrix/index.html#raya-object-authoring-theorem`;
- the selected graph detail title remains `Authoring Matrix Fixture`;
- the current URL still contains `page=authoring-matrix`;
- `localStorage` and `sessionStorage` keys are empty;
- the rendered detail HTML does not contain `_official`, `_reviewed`, `_assets`, `source_path`, `artifact`, `mjx-container`, `\\begin`, `progress`, `recommend`, or `mastery`.

- [x] **Step 4: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_detail_shows_public_section_jumps
```

Expected: fail because graph nodes do not yet include `sections` and the graph detail panel has no `Page sections` hooks.

### Task 2: Static Builder Payload

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add graph detail markup**

In `_render_graph_surface`, add this hidden block after the selected-page metadata and before `Study objects`:

```html
<section class="raya-graph-detail-sections" data-raya-graph-detail-sections hidden>
<h3>Page sections</h3>
<ol data-raya-graph-detail-section-list></ol>
</section>
```

- [x] **Step 2: Copy public sections into graph nodes**

In `_browser_graph_payload`, for each current graph page node, read `search_records[page.id]["sections"]`, and copy each section into a new `sections` list containing exactly `id`, `anchor`, `kind`, `title`, and `url`. Build `url` by combining the graph node rendered page URL with `#` plus the section anchor. Preserve page order.

- [x] **Step 3: Keep RED active until client rendering**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: the original RED pair remains the implementation target until
`graph.js` renders the section links.

### Task 3: Graph Client Rendering

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [x] **Step 1: Select the section detail nodes**

Add constants for:

```js
const detailSections = document.querySelector("[data-raya-graph-detail-sections]");
const detailSectionList = document.querySelector("[data-raya-graph-detail-section-list]");
```

- [x] **Step 2: Render public section links**

Add `renderDetailSections(node)` that:

- empties `detailSectionList`;
- reads `node.sections` only when it is an array;
- hides the block when no sections exist;
- creates one `<li><a></a></li>` per section;
- sets `a.href` to `section.url || node.url || "#"`;
- sets text to `section.title || section.anchor || "Page section"`;
- appends a small kind label only for `heading`, `numbered-object`, or `proof`.

- [x] **Step 3: Integrate with selected detail rendering**

Call `renderDetailSections(node)` inside `renderDetail()` next to `renderDetailStudyObjects(node)` and `renderDetailKeyObjects(node)`. Ensure empty selections hide the section block.

- [x] **Step 4: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_detail_shows_public_section_jumps
```

Expected: pass.

### Task 4: Focused Verification

**Files:**
- Inspect only unless failures require fixes.

- [x] **Step 1: Run focused graph and search regression tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_detail_shows_public_section_jumps \
  tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_orientation_fit_selection_frames_context
```

Expected: pass.

- [x] **Step 2: Run render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: pass with no external renderer requests, no raw TeX leakage, no private path leakage, and no overflow regression.

### Task 5: Review, Commit, Push

**Files:**
- Inspect diff and review output.

- [x] **Step 1: Request independent review**

Ask a fresh reviewer to inspect the diff for private data leakage, overbroad graph payload fields, URL/static parity regressions, storage/fetch violations, and missing tests.

- [x] **Step 2: Fix confirmed issues with TDD**

For each confirmed issue, add or update a failing test first, verify RED, implement the smallest fix, and rerun focused verification.

- [x] **Step 3: Final local checks**

Run:

```bash
git diff --check
git status --short --branch
```

Expected: no whitespace errors and only intentional tracked changes.

- [x] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-27-graph-page-sections-design.md \
  docs/superpowers/plans/2026-06-27-graph-page-sections.md \
  packages/static/src/raya_static/builder.py \
  packages/static/src/raya_static/graph.py \
  packages/static/src/raya_static/rendering.py \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph detail section jumps"
git push origin new_rayalucaria
```
