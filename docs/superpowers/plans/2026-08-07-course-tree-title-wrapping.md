# Course Tree Title Wrapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let ordinary course-map titles wrap naturally over multiple full lines while retaining emergency containment for unbroken identifiers.

**Architecture:** Preserve the existing chevron/spacer row and flex number/title link. Make the title's own final cascade declaration use normal word breaking and `break-word`; the number remains intrinsic and nonwrapping. Browser evidence inspects Range fragments rather than relying on document overflow, which is clipped by the rail.

**Tech Stack:** Python 3.10, generated CSS in `raya_static.rendering`, Playwright/Chromium, pytest.

## Global Constraints

- Do not change markup, runtime behavior, rail widths, indentation, drawer width, or mini rail.
- Keep the link `display:flex`; number is intrinsic/nonwrapping and title remains `min-width:0`.
- Ordinary titles use `word-break:normal` and `overflow-wrap:break-word`; unbroken identifiers may emergency-wrap.
- Cover expanded 1280px and 1312px rails, a 390px coarse drawer, and JS-disabled fallback.

---

### Task 1: Make Title Wrapping Natural And Prove It At Every Surface

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py:5280-5308`
- Modify: `docs/foundation/20_learning_renderer_contract.md:220-235`
- Modify: `tests/e2e/test_rail_density.py:850-925,1360-1450`
- Modify: `tests/e2e/test_preview_static_read_path.py:19155-19410`

**Interfaces:**
- Consumes: existing `.raya-course-map-list a`, `.raya-course-map-node-number`, and `.raya-course-map-node-title` markup.
- Produces: a final title cascade with natural multiword wrapping, plus Range-based containment/wrap tests.

- [ ] **Step 1: Add failing browser assertions**

```python
assert state["ordinary"]["wordBreak"] == "normal"
assert state["ordinary"]["overflowWrap"] == "break-word"
assert state["ordinary"]["lineTops"] >= 2
assert state["ordinary"]["eachWordHasOneRect"] is True
assert state["identifier"]["fragments"] >= 2
assert state["allFragmentsContained"] is True
```

Use the unnumbered root, `Detailed Requirements And Registration Constraints`,
and the existing unbroken identifier. Run this evidence at 1280px and 1312px,
in the open 390px coarse drawer, and in JS-disabled static flow; assert a
wrapped focusable title stays the active element and ArrowDown reaches the
next visible link.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:
```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local \
uv run pytest tests/e2e/test_rail_density.py \
tests/e2e/test_preview_static_read_path.py -k 'long_labels or no_script or mobile_course_map_drawer' -q
```

Expected: assertions fail because the title's winning declaration is
`overflow-wrap:anywhere`.

- [ ] **Step 3: Apply the CSS-only correction and foundation sentence**

```css
.raya-course-map-node-title {
  min-width: 0;
  overflow-wrap: break-word;
  word-break: normal;
}
```

Keep the surrounding link as `display:flex` and number as `flex:0 0 auto`.
Add one foundation-contract sentence requiring fully readable natural title
wrapping without truncation in expanded, drawer, and no-script layouts.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the Step 2 command plus:
```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local \
uv run pytest tests/e2e/test_rail_collapse_contract.py -q
```

Expected: all selected tests pass; ordinary titles use full-word line breaks,
the identifier remains contained, and interaction/geometry contracts remain
unchanged.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/rendering.py \
  docs/foundation/20_learning_renderer_contract.md \
  tests/e2e/test_rail_density.py tests/e2e/test_preview_static_read_path.py \
  tests/e2e/test_rail_collapse_contract.py
git commit -m "Wrap course tree titles naturally"
```
