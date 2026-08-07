# Course Rail Readable Width Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give deep desktop course maps more readable title space without reducing the established article or phone-drawer geometry.

**Architecture:** Keep the current 256px structural rail and phone drawer as separate explicit geometry values. Add a 288px structural-only wide-desktop value at 1312px, and reduce each tree-child content offset to 12px through an 8px guide margin plus 4px child padding. The renderer continues to substitute all geometry constants into its CSS; no runtime interaction code changes.

**Tech Stack:** Python 3.10, generated static CSS in `raya_static.rendering`, Playwright/Chromium e2e tests, pytest.

## Global Constraints

- Use 288px only at viewport widths of 1312px and above; use 256px from 640px through 1311px.
- Keep the phone drawer at 256px at 639px and 390px.
- Keep the 48px mini rail, 640px structural boundary, 894px approved boundary, interaction model, and no-script fallback unchanged.
- Set the effective child title offset to exactly 12px: 8px guide margin plus 4px child padding.
- Preserve existing reader-width floors at 894px and 1280px and document horizontal-overflow protections.

---

### Task 1: Separate Structural-Wide Geometry From Drawer Geometry

**Files:**
- Modify: `packages/static/src/raya_static/shell_geometry.py:3-76`
- Modify: `packages/static/src/raya_static/rendering.py:3980-4000,5175-5185,5480-5535,6415-6445`
- Test: `tests/e2e/test_rail_density.py:641-705,1460-1530`
- Test: `tests/e2e/test_preview_static_read_path.py:18100-18130,19370-19410`

**Interfaces:**
- Consumes: `RAIL_STRUCTURAL_PX`, `RAIL_APPROVED_PX`, `RAIL_DESKTOP_PX`, `RAIL_EXPANDED_PX`, and `apply_rail_geometry_tokens(text)`.
- Produces: `RAIL_WIDE_PX = 1312`, `RAIL_WIDE_EXPANDED_PX = 288`, and `RAIL_DRAWER_PX = 256`, with corresponding `__RAYA_*_PX__` CSS tokens.

- [ ] **Step 1: Write the failing geometry and indentation tests**

```python
expected_widths = {
    640: 256, 894: 256, 1280: 256, 1311: 256,
    1312: 288, 1440: 288,
}
for width, expected in expected_widths.items():
    assert abs(geometry["mapWidth"] - expected) <= 1

assert state["groupMargin"] == "8px"
assert state["groupPadding"] == "4px"
assert state["titleOffset"] == 12
```

Add a phone assertion at 639px and 390px that the opened map drawer width is
`min(256, viewport width)`, and retain the coarse 44px control assertion.
At 894px and 1280px retain the existing article-width floor assertions and
assert zero document horizontal overflow.

- [ ] **Step 2: Run the targeted tests and verify RED**

Run:
```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local \
uv run pytest tests/e2e/test_rail_density.py \
tests/e2e/test_preview_static_read_path.py -k \
'course_map_uses_256px_expanded_geometry or hierarchy or mobile_course_map_drawer or article_width' -q
```

Expected: failures because no 1312px wide structural value exists and child
geometry remains `16px` plus `8px`.

- [ ] **Step 3: Implement the isolated geometry values and CSS bands**

```python
RAIL_EXPANDED_PX = 256
RAIL_DRAWER_PX = 256
RAIL_WIDE_PX = 1312
RAIL_WIDE_EXPANDED_PX = 288
```

Add tokens for the new wide boundary, its `-1` boundary, wide structural
width, and drawer width. In CSS, keep the 256px value at normal structural
widths, override only expanded structural map column/inline size at
`@media (min-width: __RAYA_WIDE_PX__px)`, and use only
`__RAYA_RAIL_DRAWER_PX__` for drawer geometry. Replace the child group values
with `margin-inline-start: 8px` and `padding-inline-start: 4px`.

- [ ] **Step 4: Run the targeted tests and verify GREEN**

Run the Step 2 command plus:
```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local \
uv run pytest tests/e2e/test_rail_collapse_contract.py -q
```

Expected: all selected tests pass, including 1311/1312 and phone drawer
boundaries.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/shell_geometry.py \
  packages/static/src/raya_static/rendering.py \
  tests/e2e/test_rail_density.py \
  tests/e2e/test_preview_static_read_path.py \
  tests/e2e/test_rail_collapse_contract.py
git commit -m "Widen course rail on wide desktops"
```

### Task 2: Align Renderer Truth Surfaces With Responsive Geometry

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md:23-31`
- Modify: `docs/guides/en/{agents,contributors,professors,students}/index.md`
- Modify: `docs/guides/es/{agentes,colaboradores,estudiantes,profesores}/index.md`
- Modify: `tests/contracts/test_renderer_dependencies.py:389-456`

**Interfaces:**
- Consumes: the responsive geometry terms produced by Task 1: 256px through
 1311px, 288px from 1312px, 48px mini rail, and 256px phone drawer.
- Produces: foundation and role guidance that accurately describes reader
 geometry without changing source or runtime contracts.

- [ ] **Step 1: Write failing documentation-contract assertions**

```python
required = {
    "docs/foundation/20_learning_renderer_contract.md": [
        "256px through 1311px", "288px from 1312px", "48px", "256px phone drawer",
    ],
}
```

Apply the same responsive wording expectations to the eight role guides that
currently require only `256px`.

- [ ] **Step 2: Run the documentation contract and verify RED**

Run:
```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
tests/contracts/test_renderer_dependencies.py -k rail -q
```

Expected: failure because documents still describe a single unconditional
256px expanded rail.

- [ ] **Step 3: Update the foundation and role guidance**

Replace unconditional structural-rail claims with: 256px through 1311px,
288px from 1312px, a fixed 48px collapsed rail, and a 256px phone drawer.
Keep existing wording about one central native vertical scroll owner,
non-persistent state, static links, and no-script behavior.

- [ ] **Step 4: Run documentation tests and verify GREEN**

Run:
```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
tests/contracts/test_renderer_dependencies.py -k rail -q
```

Expected: all selected documentation contracts pass.

- [ ] **Step 5: Commit**

```bash
git add docs/foundation/20_learning_renderer_contract.md \
  docs/guides/en docs/guides/es tests/contracts/test_renderer_dependencies.py
git commit -m "Document responsive course rail width"
```

### Task 3: Capture Boundary Evidence And Final Regression Coverage

**Files:**
- Modify: `tests/e2e/test_render_debug_parity_gate.py`
- Modify: `tests/e2e/test_render_debug_report.py`
- Test: `tests/e2e/test_rail_density.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

**Interfaces:**
- Consumes: the 1312px structural-wide rail and 12px child offset from Task 1.
- Produces: retained render-debug evidence for a deep long-label course map at
 256px and 288px structural widths.

- [ ] **Step 1: Write failing boundary evidence assertions**

```python
assert scenario["viewport"]["width"] == 1312
assert scenario["rail_rect"]["width"] == 288
assert scenario["article_rect"]["width"] >= 672
assert scenario["document_overflow"] <= 1
```

Keep an adjacent 1280px scenario expecting a 256px rail and its existing
reader floor. Include the long-label current-path state in both scenarios.

- [ ] **Step 2: Run render-debug tests and verify RED**

Run:
```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local \
uv run pytest tests/e2e/test_render_debug_parity_gate.py \
tests/e2e/test_render_debug_report.py -q
```

Expected: failure because the 1312px responsive structural scenario is absent.

- [ ] **Step 3: Add the two deterministic render-debug scenarios**

Add a 1280px preserved-width and 1312px wide-rail deep-label scenario to the
existing course-tree scenario capture/report pipeline. Record rail width,
article width, title containment, and document overflow in the report.

- [ ] **Step 4: Run focused and final verification**

Run:
```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local \
uv run pytest tests/e2e/test_rail_density.py \
tests/e2e/test_rail_collapse_contract.py \
tests/e2e/test_preview_static_read_path.py \
tests/e2e/test_render_debug_parity_gate.py \
tests/e2e/test_render_debug_report.py -q
RAYA_TEST_BROWSER=/usr/bin/google-chrome ./scripts/check-render-debug.sh
```

Expected: all focused suites and render-debug evidence pass; retained
screenshots visibly show the wider 1312px rail, unchanged 1280px rail, readable
deep labels, and no overlap.

- [ ] **Step 5: Commit**

```bash
git add tests/e2e/test_render_debug_parity_gate.py \
  tests/e2e/test_render_debug_report.py
git commit -m "Verify responsive course rail width"
```
