# Reader-Rail Collapse Single Source of Truth — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate the two reader side-rails' chronically-breaking collapse behavior into one source of truth per concern (state, appearance, reflow) while preserving every entangled subsystem, so the collapsed rail is a clean single chevron chip and stops drifting.

**Architecture:** Surgical consolidation, not a rewrite. (1) State: one *effective* `data-raya-*` attribute per rail on `<html>` (mirror writes deleted), a retained *preference* channel, and a single code-generated breakpoint+derivation shared by prepaint JS, runtime JS, and CSS. (2) Appearance: one co-located CSS region that hides header **and** body and shows only the chip, width-invariant ≥640. (3) Reflow: a single 894 in-flow-grid boundary with a `minmax(0,1fr)` article floor below 1280, token-driven columns, and the medium-band mutual-exclusion rule. Five entangled subsystems (transition animator, medium-band coordinator, map-drawer modal inerting, learning-rail drawer, focus/reconciliation engine) are preserved and re-asserted.

**Tech Stack:** Python 3.10 (uv workspace, `raya_static` package: `builder.py`, `rendering.py`, `shell.py`, `shell_prepaint.py`), CSS-as-Python-string (`rich_render_css`), vanilla JS emitted verbatim from raw strings, Playwright/Chromium e2e, pytest.

## Global Constraints

- Seed truth is `docs/foundation/20_learning_renderer_contract.md`; it outranks this plan. Design spec: `docs/superpowers/specs/2026-07-17-rail-collapse-single-source-of-truth-design.md`.
- Left rail keeps **exactly eight** command tiles two-per-row when expanded (Search, Graph, Practice, Tasks, Schedule, Context, Text size, OpenDyslexic); header shows `Course map` + `Hide map`; **no Map control duplicated in the body**.
- Accessible opener names verbatim: left `Expand course map`; right Context edge opener.
- Collapsed content must be `display:none` + inert + `aria-hidden` + removed from tab order.
- Phone (`<640`): left = modal drawer; right rail = inline-expanded by its own state, never own-state-inert, **but** modal-background-inert (`aria-hidden`+`inert`) while the map drawer is open.
- Single reflow/collapse boundary = **894px**. The `1280px` `isDesktopShell` query survives only for non-collapse concerns (tooltip enable, tab-order) and the ≥1280 comfortable-article layer.
- SessionStorage keys unchanged: `raya:reader-shell:v1:<course_id>`, `raya:course-map-branches:v1:<course_id>`. Comfort keys `raya:open-dyslexic`/`raya:text-size` unchanged. No new storage/network/cross-tab state.
- Branch: `rail-collapse-single-source-of-truth` (already created off `new_rayalucaria`). Commit frequently. Do not edit `artifact/` trees.
- Browser tests need Chromium: image ships `chromium`; locally `google-chrome-stable` or `RAYA_TEST_BROWSER`.
- Gates before "done": `./scripts/check.sh` and `./scripts/check-render-debug.sh` (run sequentially, never concurrently).
- Test-rewrite rule: existing behaviors are **converted** to the new contract, **never silently deleted**. Every named preserved subsystem must have a green re-asserted test.

---

## File structure

- `packages/static/src/raya_static/shell_geometry.py` — **new**. Single source of the breakpoint constants (`RAIL_STRUCTURAL_PX=640`, `RAIL_APPROVED_PX=894`, `RAIL_DESKTOP_PX=1280`) and the shared effective-state derivation JS snippet. Consumed by `shell.py`, `shell_prepaint.py`, and `rendering.py` via token replacement.
- `packages/static/src/raya_static/shell_prepaint.py` — modify: replace hardcoded `640`/`894` with tokens.
- `packages/static/src/raya_static/shell.py` — modify: token breakpoints; delete mirror writes; inert = `f(state,width,side)`; re-derive inert on resize; re-point focus handoff to re-emitted chrome buttons.
- `packages/static/src/raya_static/rendering.py` — modify: single collapsed-appearance region; token-driven 894-boundary reflow; class-ify `#id` collapse selectors; token `@media` boundaries; keep transition/print CSS.
- `packages/static/src/raya_static/builder.py` — modify: `_render_rail_chrome` helper; remove SSR mirror attributes; both rails call chrome + own body.
- `tests/e2e/test_rail_collapse_contract.py` — **new**. Single-contract acceptance + guardrail tests.
- `tests/e2e/test_preview_static_read_path.py`, `tests/contracts/test_static_builder.py`, `tests/e2e/test_render_debug_parity_gate.py`, `tests/e2e/test_render_debug_report.py` — modify: convert blast-radius assertions.

---

## Task 0: Setup — reconcile stash, baseline, branch

**Files:**
- Modify: none (environment only)

- [ ] **Step 1: Confirm branch**

Run: `git -C /home/uumami/itam/raya_lucaria branch --show-current`
Expected: `rail-collapse-single-source-of-truth`

- [ ] **Step 2: Inspect and drop the stale stash (already superseded by upstream)**

Run: `git stash show -p 'stash@{0}' --stat`
Expected: shows `stale-local-rail-session-2026-07-17` touching `rendering.py`/tests. Confirm it is the discarded pre-sync work, then drop so it cannot collide:
Run: `git stash drop 'stash@{0}'`
Expected: `Dropped stash@{0} (...)`

- [ ] **Step 3: Establish the green baseline for the reader-rail suite**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py tests/contracts/test_static_builder.py -q`
Expected: PASS (record the count; this is the pre-change baseline the conversions must return to green).

- [ ] **Step 4: Commit a marker (empty) to anchor the branch**

```bash
git commit --allow-empty -m "chore: begin rail-collapse consolidation"
```

---

## Task 1: Single-source breakpoints + derivation (codegen into JS)

**Goal:** One Python source of the `640`/`894` boundaries and the effective-state derivation, token-substituted into both scripts. Kills the "three independent 894 literals" drift.

**Files:**
- Create: `packages/static/src/raya_static/shell_geometry.py`
- Modify: `packages/static/src/raya_static/shell.py` (return value of `shell_resources`), `packages/static/src/raya_static/shell_prepaint.py` (return value of `shell_prepaint_javascript`)
- Test: `tests/e2e/test_rail_collapse_contract.py`

**Interfaces:**
- Produces: `raya_static.shell_geometry.RAIL_STRUCTURAL_PX: int = 640`, `RAIL_APPROVED_PX: int = 894`, `RAIL_DESKTOP_PX: int = 1280`; `RAIL_EFFECTIVE_DERIVATION_JS: str` (the shared derivation function text, embedded via the `__RAYA_RAIL_DERIVATION__` token); and `apply_rail_geometry_tokens(text: str) -> str` replacing `__RAYA_STRUCTURAL_PX__` / `__RAYA_APPROVED_PX__` / `__RAYA_DESKTOP_PX__` / `__RAYA_RAIL_DERIVATION__` with their values.
- Consumes (later tasks): the same numeric token names inside CSS (Task 2).

**Why the derivation, not just the literals:** the pairwise medium-band rule ("below 894, both-expanded → collapse both") lives independently in prepaint (`applyEffective`, `shell_prepaint.py:15-27`) and runtime (`effectiveReaderShellState`, `shell.py:212-228`). Tokenizing only the numbers still lets the *rule* drift between the two. The single source must emit the whole rule once.

- [ ] **Step 1: Write the failing guardrail test (literals + shared derivation)**

In `tests/e2e/test_rail_collapse_contract.py`:

```python
from raya_static.shell import shell_resources
from raya_static.shell_prepaint import shell_prepaint_javascript
from raya_static.shell_geometry import RAIL_EFFECTIVE_DERIVATION_JS


def test_rail_geometry_is_single_sourced_across_scripts():
    runtime = shell_resources().javascript
    prepaint = shell_prepaint_javascript()
    # No un-substituted tokens leak into emitted scripts.
    for token in ("__RAYA_STRUCTURAL_PX__", "__RAYA_APPROVED_PX__",
                  "__RAYA_DESKTOP_PX__", "__RAYA_RAIL_DERIVATION__"):
        assert token not in runtime, token
        assert token not in prepaint, token
    # Boundaries agree across scripts.
    assert "(min-width: 894px)" in runtime
    assert "894" in prepaint and "640" in prepaint and "640" in runtime
    # The pairwise derivation is byte-identical in both scripts (no rule drift).
    assert RAIL_EFFECTIVE_DERIVATION_JS in runtime
    assert RAIL_EFFECTIVE_DERIVATION_JS in prepaint
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_rail_geometry_is_single_sourced_across_scripts -v`
Expected: FAIL — `RAIL_EFFECTIVE_DERIVATION_JS` does not exist / snippet not embedded in both scripts.

- [ ] **Step 3: Create the geometry module with the shared derivation**

`packages/static/src/raya_static/shell_geometry.py`:

```python
from __future__ import annotations

RAIL_STRUCTURAL_PX = 640
RAIL_APPROVED_PX = 894
RAIL_DESKTOP_PX = 1280

# The one definition of the effective-state rule, embedded verbatim in BOTH
# the prepaint and runtime scripts. Pure function of (preference, width):
#   < 640            -> both expanded (left is presented as a drawer in CSS/JS)
#   >= 894           -> caller's preference (default expanded)
#   640..893, both expanded -> collapse both (medium-band mutual exclusion)
RAIL_EFFECTIVE_DERIVATION_JS = (
    "function rayaEffectiveRailState(courseMap, learningRail, width) {\n"
    "  if (width < __RAYA_STRUCTURAL_PX__) {\n"
    "    return { courseMap: \"expanded\", learningRail: \"expanded\" };\n"
    "  }\n"
    "  if (width < __RAYA_APPROVED_PX__ && courseMap === \"expanded\""
    " && learningRail === \"expanded\") {\n"
    "    return { courseMap: \"collapsed\", learningRail: \"collapsed\" };\n"
    "  }\n"
    "  return { courseMap: courseMap, learningRail: learningRail };\n"
    "}"
)

_TOKENS = {
    "__RAYA_RAIL_DERIVATION__": RAIL_EFFECTIVE_DERIVATION_JS,
    "__RAYA_STRUCTURAL_PX__": str(RAIL_STRUCTURAL_PX),
    "__RAYA_APPROVED_PX__": str(RAIL_APPROVED_PX),
    "__RAYA_DESKTOP_PX__": str(RAIL_DESKTOP_PX),
}


def apply_rail_geometry_tokens(text: str) -> str:
    """Substitute rail-geometry placeholder tokens.

    Placeholder tokens (not f-strings/.format) are required because the JS/CSS
    bodies are dense with braces. The derivation token is expanded first, then
    the numeric tokens inside it are resolved.
    """
    for token, value in _TOKENS.items():
        text = text.replace(token, str(value))
    return text
```

Note: because `_TOKENS` is ordered with `__RAYA_RAIL_DERIVATION__` first, the derivation snippet is inserted before the numeric tokens it contains are substituted, so both the standalone numeric tokens and those inside the derivation resolve in one pass.

- [ ] **Step 4: Embed the shared derivation + tokenize both scripts**

In `shell_prepaint.py`: add `__RAYA_RAIL_DERIVATION__` near the top of the IIFE and rewrite `applyEffective` to call `rayaEffectiveRailState(courseMap, learningRail, innerWidth)` then write the result to `root.dataset`. Change the accessor:

```python
from raya_static.shell_geometry import apply_rail_geometry_tokens


def shell_prepaint_javascript() -> str:
    return apply_rail_geometry_tokens(_SHELL_PREPAINT_JAVASCRIPT)
```

In `shell.py`: add `__RAYA_RAIL_DERIVATION__` near the top of the IIFE; rewrite `effectiveReaderShellState` to delegate its pairwise clause to `rayaEffectiveRailState(next.courseMap, next.learningRail, innerWidth)` (keeping the `!isStructuralRailShell()` early return). Replace the media-query literals (`640`/`894`/`1280`, and the `640..767` compact lower bound) with the numeric tokens. Change the accessor:

```python
from raya_static.shell_geometry import apply_rail_geometry_tokens


def shell_resources() -> ShellResources:
    return ShellResources(javascript=apply_rail_geometry_tokens(_SHELL_JAVASCRIPT))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_rail_geometry_is_single_sourced_across_scripts -v`
Expected: PASS.

- [ ] **Step 6: Run the JS-touching e2e smoke to confirm no behavior change**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -q -k "reader_shell or course_map or learning_rail"`
Expected: PASS (the derivation reproduces the prior three-clause behavior exactly).

- [ ] **Step 7: Commit**

```bash
git add packages/static/src/raya_static/shell_geometry.py packages/static/src/raya_static/shell.py packages/static/src/raya_static/shell_prepaint.py tests/e2e/test_rail_collapse_contract.py
git commit -m "feat: single-source rail breakpoints and effective-state derivation"
```

---

## Task 2: Extend the single source into CSS `@media` boundaries

**Goal:** CSS boundaries are emitted from the same tokens, and a guardrail test asserts JS↔CSS parity. Closes root-cause #3's CSS drift.

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py` (the `894`/`893`/`640` collapse `@media` literals at 4077/4110/6446/6702/6830/6839/6848/6862; the `1280` grid at 5306), `packages/static/src/raya_static/builder.py:8237` (CSS emit)
- Test: `tests/e2e/test_rail_collapse_contract.py`

**Interfaces:**
- Consumes: `apply_rail_geometry_tokens` from Task 1.

- [ ] **Step 1: Write the failing parity test**

Add to `tests/e2e/test_rail_collapse_contract.py`:

```python
from raya_static.rendering import rich_render_css


def test_css_and_js_share_the_same_rail_boundaries():
    css = rich_render_css()
    for token in ("__RAYA_STRUCTURAL_PX__", "__RAYA_APPROVED_PX__",
                  "__RAYA_DESKTOP_PX__", "__RAYA_APPROVED_MINUS_PX__"):
        assert token not in css, token
    # The approved-geometry boundary appears in CSS exactly as in JS.
    assert "(min-width: 894px)" in css
    # Its complement is emitted from the same source (guards the sub-pixel gap).
    assert "(max-width: 893px)" in css
    # The structural boundary is shared too.
    assert "(min-width: 640px)" in css
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_css_and_js_share_the_same_rail_boundaries -v`
Expected: FAIL (tokens not yet used in CSS / boundary not yet unified — becomes meaningful after Step 3–4 and Task 6).

- [ ] **Step 3: Tokenize the collapse `@media` boundaries in `rich_render_css`**

In `rendering.py`, replace the collapse/reflow breakpoint literals with tokens: `(min-width: 640px)` → `(min-width: __RAYA_STRUCTURAL_PX__px)` and `(min-width: 894px)` → `(min-width: __RAYA_APPROVED_PX__px)` and `(max-width: 893px)` → `(max-width: __RAYA_APPROVED_MINUS_PX__px)` in the rail-collapse blocks only (do **not** touch unrelated component media queries). Add `__RAYA_APPROVED_MINUS_PX__ = RAIL_APPROVED_PX - 1` to `shell_geometry._TOKENS`.

- [ ] **Step 4: Substitute tokens at CSS emit**

In `builder.py:8237`, wrap the CSS write:

```python
stylesheet.write_text(apply_rail_geometry_tokens(rich_render_css()), encoding="utf-8")
```

And make `rich_render_css()` callers in tests see substituted output by substituting inside `rich_render_css` return, OR expose the substitution in the function. Choose: substitute inside `rich_render_css`'s return statement so all consumers (tests + build) get final CSS:

```python
from raya_static.shell_geometry import apply_rail_geometry_tokens
# ... at the end of rich_render_css:
return apply_rail_geometry_tokens(_assembled_css)
```

(Then revert the builder.py:8237 double-substitution to a plain write to avoid double work.)

- [ ] **Step 5: Run test to verify it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_css_and_js_share_the_same_rail_boundaries -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/static/src/raya_static/rendering.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/shell_geometry.py tests/e2e/test_rail_collapse_contract.py
git commit -m "feat: single-source rail breakpoints into CSS"
```

---

## Task 3: Effective state on `<html>` only (delete mirror writes; audit reads)

**Goal:** Remove the `main`/element state mirrors, keep the preference channel, and add the guardrail test forbidding mirror-read selectors.

**Files:**
- Modify: `packages/static/src/raya_static/shell.py` (mirror writes ~492-494, ~1086-1088), `packages/static/src/raya_static/builder.py` (SSR `data-raya-course-map="expanded"` on `main` id `raya-content` and on the rail elements), `packages/static/src/raya_static/rendering.py` (convert element/`.raya-learning-shell`-mirror collapse selectors to `html[...]` form at 4083-4084, 5321-5350, 6529-6547)
- Test: `tests/e2e/test_rail_collapse_contract.py`, `tests/contracts/test_static_builder.py` (convert the literal `main ... data-raya-course-map="expanded"` asserts at ~5133/5584/5589 and the doubled-selector asserts at ~4853)

**Interfaces:**
- Consumes: nothing new.
- Produces: state read exclusively from `root.dataset.rayaCourseMap` / `rayaLearningRail` on `<html>`; preference from `root.dataset.rayaCourseMapPreference` / `rayaLearningRailPreference`.

- [ ] **Step 1: Write the failing guardrail test (no mirror-read collapse selectors)**

Add to `tests/e2e/test_rail_collapse_contract.py`:

```python
import re
from raya_static.rendering import rich_render_css


def test_collapse_selectors_key_off_html_only():
    css = rich_render_css()
    offenders = []
    for line in css.splitlines():
        if "data-raya-course-map=" not in line and "data-raya-learning-rail=" not in line:
            continue
        if "-transition" in line or "-drawer" in line or "-preference" in line:
            continue  # animation/drawer/preference channels are exempt element attrs
        # Element-mirror forms that go dead when the mirror write is removed:
        if re.search(r"\.raya-course-map\[data-raya-course-map=", line) \
           or re.search(r"\.raya-learning-rail\[data-raya-learning-rail=", line) \
           or re.search(r"\.raya-learning-shell\[data-raya-course-map=", line) \
           or re.search(r"\.raya-learning-shell\[data-raya-learning-rail=", line):
            offenders.append(line.strip())
    assert offenders == [], offenders
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_collapse_selectors_key_off_html_only -v`
Expected: FAIL — lists the element/shell-mirror collapse selectors.

- [ ] **Step 3: Convert mirror-read selectors to `html[...]` form**

In `rendering.py`, for each offender the test reports, rewrite the selector to the `html[...]` ancestor form. Example transformation:
`.raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-expand` → `html[data-raya-course-map="collapsed"] .raya-course-map-expand`; `.raya-learning-shell[data-raya-course-map="collapsed"]` (the `main`) → `html[data-raya-course-map="collapsed"] .raya-learning-shell`. Keep transition/drawer element selectors untouched.

- [ ] **Step 4: Delete the mirror writes in `shell.py`**

Remove the `shell.dataset.rayaCourseMap = ...` / rail-element `dataset.rayaLearningRail = ...` mirror writes (~492-494 for map, ~1086-1088 for rail) so only `root.dataset.*` (html) is written. Leave the `root.dataset.*Preference` writes intact.

- [ ] **Step 5: Remove SSR mirror attributes in `builder.py`**

Delete `data-raya-course-map="expanded"` from `<main id="raya-content" class="raya-learning-shell">` and the initial `data-raya-course-map`/`data-raya-learning-rail` on the `nav`/`aside` elements (keep them on `<html>`). Update `tests/contracts/test_static_builder.py` literal expectations accordingly (the `<main ...>` string and doubled-selector substrings).

- [ ] **Step 6: Run the guardrail + contract tests**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_collapse_selectors_key_off_html_only tests/contracts/test_static_builder.py -q`
Expected: PASS (contract asserts updated to html-only forms).

- [ ] **Step 7: Commit**

```bash
git add packages/static/src/raya_static/shell.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/e2e/test_rail_collapse_contract.py tests/contracts/test_static_builder.py
git commit -m "refactor: collapse state on html root only"
```

---

## Task 4: One collapsed-appearance region (hide header + body, show chip)

**Goal:** Collapsed = narrow strip with header **and** body `display:none`, single chevron chip, width-invariant ≥640. The single acceptance test proves it for both rails at four widths.

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py` — consolidate the scattered collapsed-appearance rules (4070-4098, 6702-6829 chip geometry, and the per-band chip offsets 6830-6847) into one contiguous, commented `@media (min-width: __RAYA_STRUCTURAL_PX__px)` region; ensure it hides `.raya-course-map-header`/`.raya-learning-rail-header` as well as the bodies (mirror today's 4081-4084 which hides both).
- Test: `tests/e2e/test_rail_collapse_contract.py`

**Interfaces:**
- Consumes: html-only state (Task 3), single boundary (Task 2).

- [ ] **Step 1: Write the failing acceptance test**

Add to `tests/e2e/test_rail_collapse_contract.py` (mirror the helper pattern already in `tests/e2e/test_preview_static_read_path.py` for `create_preview` + Playwright; reuse its `_browser_executable`/`create_preview` imports):

```python
import shutil
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
RENDER_FIXTURE = ROOT / "examples" / "courses" / "render-fixture"


def _collapsed_chip(page, rail_sel):
    return page.evaluate(
        """(sel) => {
          const rail = document.querySelector(sel);
          const controls = Array.from(rail.querySelectorAll('a,button')).filter((el) => {
            const b = el.getBoundingClientRect();
            return b.width > 1 && b.height > 1 && getComputedStyle(el).visibility !== 'hidden';
          });
          const chip = controls[0];
          const cb = chip ? chip.getBoundingClientRect() : null;
          const header = rail.querySelector('.raya-course-map-header,.raya-learning-rail-header');
          const body = rail.querySelector('#raya-course-map-body,#raya-learning-rail-body');
          const shown = (el) => el && getComputedStyle(el).display !== 'none';
          return {
            controlCount: controls.length,
            w: cb ? Math.round(cb.width) : null,
            h: cb ? Math.round(cb.height) : null,
            headerShown: shown(header),
            bodyShown: shown(body),
          };
        }""",
        rail_sel,
    )


def test_collapsed_rails_are_single_clean_chips(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview
    from tests.e2e.test_preview_static_read_path import _browser_executable  # reuse

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(_browser_executable()),
                                        headless=True, args=["--no-sandbox"])
            try:
                for width in (768, 894, 1280, 1440):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                    # Drive both rails collapsed via their html state.
                    page.evaluate("""() => {
                      const r = document.documentElement;
                      r.dataset.rayaCourseMap = 'collapsed';
                      r.dataset.rayaLearningRail = 'collapsed';
                    }""")
                    page.wait_for_timeout(320)
                    left = _collapsed_chip(page, "#raya-course-map")
                    right = _collapsed_chip(page, "#raya-learning-rail")
                    for side in (left, right):
                        assert side["controlCount"] == 1, (width, side)
                        assert 36 <= side["w"] <= 48 and 36 <= side["h"] <= 48, (width, side)
                        assert side["headerShown"] is False, (width, side)
                        assert side["bodyShown"] is False, (width, side)
                    assert left["w"] == right["w"] and left["h"] == right["h"], (width, left, right)
                    overflow = page.evaluate(
                        "() => Math.ceil(document.documentElement.scrollWidth - innerWidth)")
                    assert overflow <= 1, (width, overflow)
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_collapsed_rails_are_single_clean_chips -v`
Expected: FAIL — header shown / multiple controls / per-band geometry differences at some widths.

- [ ] **Step 3: Consolidate the collapsed-appearance region**

In `rendering.py`, create one commented block `/* --- rail collapse: appearance (single source) --- */` inside `@media (min-width: __RAYA_STRUCTURAL_PX__px)` that, for both `html[data-raya-course-map="collapsed"] #raya-course-map` and `html[data-raya-learning-rail="collapsed"] #raya-learning-rail`:
  - sets the container to the fixed 2.75rem chip strip (move the rules from 6765-6792 here);
  - `display:none` on **both** `.raya-*-header` and `#raya-*-body` (extend the 4081-4084 pattern to cover the header explicitly for both rails);
  - shows the expand control as the 2.5rem chevron chip with `::after` `>`/`<` and the opener names;
  - removes the now-redundant per-band chip offset blocks (6830-6847) so the chip is width-invariant (choose one vertical placement — e.g. `top: 0.75rem` — for all ≥640).
Delete the superseded scattered collapsed-appearance fragments as you fold them in (leave transition-state and drawer CSS alone).

- [ ] **Step 4: Run the acceptance test until green**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_collapsed_rails_are_single_clean_chips -v`
Expected: PASS at all four widths.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/rendering.py tests/e2e/test_rail_collapse_contract.py
git commit -m "feat: single collapsed-appearance region hides header and body"
```

---

## Task 5: Class-ify `#id` collapse selectors + guardrail

**Goal:** Remove the `#id` specificity cliff so the single appearance block reliably wins; forbid future `#id` collapse selectors outside the prepaint skeleton.

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py` — non-skeleton `#raya-course-map` collapse hover rules at 6557-6558, and the skeleton set at 6661/6662/6686/6687/6689/6690
- Test: `tests/e2e/test_rail_collapse_contract.py`

- [ ] **Step 1: Write the failing guardrail test**

```python
def test_no_id_selectors_reference_collapse_state():
    css = rich_render_css()
    offenders = []
    for line in css.splitlines():
        if "#raya-course-map" not in line and "#raya-learning-rail" not in line:
            continue
        if "data-raya-course-map=" in line or "data-raya-learning-rail=" in line:
            offenders.append(line.strip())
    assert offenders == [], offenders
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_no_id_selectors_reference_collapse_state -v`
Expected: FAIL — lists 6557-6558 and skeleton lines.

- [ ] **Step 3: Convert `#id` to class selectors**

Replace `#raya-course-map` → `.raya-course-map` and `#raya-learning-rail` → `.raya-learning-rail` in every collapse-state rule the test reports (skeleton pending block + the 6557-6558 hover rules). The prepaint pending temporal guard (`html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"])`) is unchanged; the class form still outranks competing collapse rules (verified: specificity 0,4,1 > 0,2,1).

- [ ] **Step 4: Run test + the appearance acceptance test**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py -q`
Expected: PASS (all contract tests, including Task 4's).

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/rendering.py tests/e2e/test_rail_collapse_contract.py
git commit -m "refactor: class-ify collapse selectors, drop id specificity cliff"
```

---

## Task 6: Reflow — single 894 in-flow boundary without overflow

**Goal:** Move the in-flow grid to 894 with a `minmax(0,1fr)` article floor below 1280 (comfort floors only ≥1280), token-driven columns, and no phantom gap — proven by a no-overflow test where both rails are expanded across 894–1279.

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py` — the grid at 5306-5333 (currently `@media (min-width:1280px)`), the 640-1279 overlay blocks (6446-6489), and add the 894-1279 in-flow layer
- Test: `tests/e2e/test_rail_collapse_contract.py`

- [ ] **Step 1: Write the failing no-overflow test**

```python
def test_expanded_rails_do_not_overflow_at_894_band(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview
    from tests.e2e.test_preview_static_read_path import _browser_executable

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(_browser_executable()),
                                        headless=True, args=["--no-sandbox"])
            try:
                for width in (894, 1000, 1152, 1279):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                    page.evaluate("""() => {
                      const r = document.documentElement;
                      r.dataset.rayaCourseMap = 'expanded';
                      r.dataset.rayaLearningRail = 'expanded';
                    }""")
                    page.wait_for_timeout(120)
                    overflow = page.evaluate(
                        "() => Math.ceil(document.documentElement.scrollWidth - innerWidth)")
                    assert overflow <= 1, (width, overflow)
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_expanded_rails_do_not_overflow_at_894_band -v`
Expected: FAIL at 894/1000/1152 (article floor 42rem overflows).

- [ ] **Step 3: Add the 894-1279 in-flow layer with `minmax(0,1fr)`**

In `rendering.py`, introduce `@media (min-width: __RAYA_APPROVED_PX__px)` grid rules using CSS custom properties for the rail tracks:
```
html[data-raya-course-map="expanded"] { --raya-map-col: 15rem; }
html[data-raya-course-map="collapsed"] { --raya-map-col: 0; }
html[data-raya-learning-rail="expanded"] { --raya-rail-col: 15rem; }
html[data-raya-learning-rail="collapsed"] { --raya-rail-col: 0; }
.raya-learning-shell { grid-template-columns: var(--raya-map-col) minmax(0, 1fr) var(--raya-rail-col); column-gap: 1.5rem; }
```
Zero the column-gap adjacent to a collapsed side (e.g. via `grid-template-columns` with `0` track and reduced gap, or set `column-gap: 0` when both rails collapsed and handle single-collapse with `gap` on the article edge). Reintroduce the comfort article floor **only** at `@media (min-width: __RAYA_DESKTOP_PX__px)`:
```
.raya-learning-shell { grid-template-columns: var(--raya-map-col) minmax(42rem, 1fr) var(--raya-rail-col); }
```
Remove the old 640-1279 `position:fixed` overlay for the ≥894 band (overlay stays only for 640-893 — Task 7).

- [ ] **Step 4: Run the no-overflow test + appearance test**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_expanded_rails_do_not_overflow_at_894_band tests/e2e/test_rail_collapse_contract.py::test_collapsed_rails_are_single_clean_chips -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/rendering.py tests/e2e/test_rail_collapse_contract.py
git commit -m "feat: unify in-flow grid at 894 without overflow"
```

---

## Task 7: Medium-band (640–893) mutual-exclusion coordination

**Goal:** Below 894 at most one rail expanded; expanding one collapses the other; an expanded rail overlays (no reserved column). Re-assert the coordination tests against the new model.

**Files:**
- Modify: `packages/static/src/raya_static/shell.py` — confirm `isMediumStructuralShell` guards at ~1691-1693 / ~1711-1712 and `effectiveReaderShellState` pairwise clause (220-226) still fire after the html-only refactor; `rendering.py` — 640-893 overlay geometry (6848) keyed on `html[...]`
- Test: convert `tests/e2e/test_preview_static_read_path.py::test_reader_shell_open_actions_coordinate_only_below_approved_geometry` and `::test_reader_shell_medium_actions_store_coordinated_pair` to html-only reads

- [ ] **Step 1: Run the existing coordination tests to see current failures**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -q -k "coordinate_only_below_approved_geometry or medium_actions_store_coordinated_pair"`
Expected: FAIL where they read the deleted `main`/element mirror (`#raya-content`.dataset...).

- [ ] **Step 2: Convert the assertions to html-only reads**

In those tests, replace `document.querySelector('#raya-content')?.dataset.rayaCourseMap` and element-mirror reads with `document.documentElement.dataset.rayaCourseMap` / `rayaLearningRail`. Keep the stored-pair sessionStorage assertions (`{"courseMap":...,"learningRail":...}`) unchanged — they already assert the coordination outcome at 893 vs 894.

- [ ] **Step 3: Ensure overlay geometry at 640-893 keys off html**

In `rendering.py` 6848 block, confirm the expanded-rail overlay (`position:fixed`, no reserved column) selectors are `html[data-raya-...="expanded"]` forms; convert any element-mirror ones (already guarded by Task 3's test).

- [ ] **Step 4: Run the coordination tests**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -q -k "coordinate_only_below_approved_geometry or medium_actions_store_coordinated_pair"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/shell.py packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git commit -m "refactor: keep medium-band rail coordination on html state"
```

---

## Task 8: Inert = f(state, width, side); fix latent bug; modal-background exception

**Goal:** Both rail bodies derive own-state inert as `isStructuralRailShell() && collapsed` (adopting the map's width gate), the learning-rail unconditional-inert bug is fixed, inert re-derives on width change, phone right rail is never own-state-inert, and the map-drawer modal-background inerting is preserved.

**Files:**
- Modify: `packages/static/src/raya_static/shell.py` — the learning-rail inert path (~1088-1092), add a shared `applyRailBodyInert(body, collapsed)` used by both rails; ensure resize/reconciliation calls it; keep `syncCourseMapModalBackground` (286-290) untouched
- Test: convert `tests/e2e/test_preview_static_read_path.py::test_mobile_course_map_drawer_is_modal_and_volatile` (html-only reads) and add an inert re-derivation assertion

**Interfaces:**
- Produces: `applyRailBodyInert(body, collapsed)` — sets `aria-hidden`+inert+focusable-descendants using `isStructuralRailShell() && collapsed`.

- [ ] **Step 1: Write the failing phone-parity + resize test**

Add to `tests/e2e/test_rail_collapse_contract.py`:

```python
def test_phone_right_rail_never_own_state_inert(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview
    from tests.e2e.test_preview_static_read_path import _browser_executable

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(_browser_executable()),
                                        headless=True, args=["--no-sandbox"])
            try:
                page = browser.new_page(viewport={"width": 390, "height": 780})
                page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                page.wait_for_timeout(120)
                state = page.evaluate("""() => {
                  const body = document.querySelector('#raya-learning-rail-body');
                  return { ariaHidden: body.getAttribute('aria-hidden'),
                           inert: body.hasAttribute('inert') };
                }""")
                # Phone: right rail body is reachable (not own-state inert), drawer closed.
                assert state["ariaHidden"] != "true", state
                assert state["inert"] is False, state
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_phone_right_rail_never_own_state_inert -v`
Expected: FAIL (learning-rail inert applied without width gate at 1090).

- [ ] **Step 3: Introduce the shared width-gated inert function**

In `shell.py`, add near `updateMapLinkTabOrder`:

```javascript
function applyRailBodyInert(body, collapsed) {
  const hide = isStructuralRailShell() && collapsed;
  body.setAttribute("aria-hidden", hide ? "true" : "false");
  setElementInert(body, hide);
  setFocusableDescendantsEnabled(body, !hide);
}
```

Replace the learning-rail inert application (~1088-1092) with `applyRailBodyInert(learningRailBody, !nextExpanded)`, and have `updateMapLinkTabOrder` call `applyRailBodyInert(mapBody, !nextExpanded)` for the body portion (keep the map `tabindex` logic). Ensure the resize/reconciliation path (`reconcileReaderShellState`) re-invokes both, so a width change re-derives inert.

- [ ] **Step 4: Convert the modal-background test to html-only and run both**

In `test_mobile_course_map_drawer_is_modal_and_volatile`, keep the assertion that with the **drawer open** at 390px the rail is `{ariaHidden:"true", inert:True}` (modal-background inerting via `syncCourseMapModalBackground`, unchanged), switching any mirror reads to `document.documentElement`.

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_phone_right_rail_never_own_state_inert "tests/e2e/test_preview_static_read_path.py::test_mobile_course_map_drawer_is_modal_and_volatile" -v`
Expected: PASS (own-state non-inert at phone; modal-background inert only while drawer open).

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/shell.py tests/e2e/test_rail_collapse_contract.py tests/e2e/test_preview_static_read_path.py
git commit -m "fix: width-gated rail inert, phone right-rail parity preserved"
```

---

## Task 9: Shared `_render_rail_chrome`; re-point focus handoff

**Goal:** Extract only the recurring collapse chrome into one builder helper (no duplicate Map control), each rail keeps its own body, and the focus-handoff/reconciliation wiring points at the re-emitted buttons.

**Files:**
- Modify: `packages/static/src/raya_static/builder.py` — add `_render_rail_chrome(...)`, refactor `_render_course_map` (2113-2176) and `_render_learning_rail` (2179-2236) to call it; `shell.py` — verify `courseMapFocusTarget`, `learningRailExpand.focus()`, `readerShellReconciliationFocusTarget` still resolve the re-emitted buttons
- Test: convert `tests/e2e/test_preview_static_read_path.py::test_reader_shell_breakpoint_reconciliation_preserves_visible_focus` and `::test_reader_rail_escape_is_focus_scoped_and_persists_only_changes` to html-only; keep focus-target assertions

**Interfaces:**
- Produces: `_render_rail_chrome(*, landmark, rail_id, region_title, collapse_button_html, expand_button_html, body_html, backdrop_html)` → str.

- [ ] **Step 1: Run the focus tests to capture current green, then the structure test**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -q -k "reconciliation_preserves_visible_focus or escape_is_focus_scoped" tests/contracts/test_static_builder.py -q`
Expected: some FAIL where they read deleted mirrors; note the focus-target expectations.

- [ ] **Step 2: Add `_render_rail_chrome` and refactor both rails**

Extract the shared wrapper (landmark open/close, header with region title + collapse button, expand chip/edge opener, backdrop) into `_render_rail_chrome`. `_render_course_map` passes its own body (search + 8 tiles + filter + tree + compact-preview) and `data-raya-course-map-*` attrs; `_render_learning_rail` passes its own body (section-context-first panels + context-chip). Assert in code review: the left rail emits exactly the header `Hide map` + floating `Expand course map` — **no** third Map control in the body.

- [ ] **Step 3: Update `test_static_builder.py` structure expectations**

Adjust the exact-substring assertions to the chrome-refactored output (same controls, same order, html-only state).

- [ ] **Step 4: Convert and run the focus/reconciliation tests**

Switch mirror reads to `document.documentElement`; keep the focus-target assertions (collapse→chip, expand→collapse control, reconciliation mapping).

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -q -k "reconciliation_preserves_visible_focus or escape_is_focus_scoped" tests/contracts/test_static_builder.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/shell.py tests/e2e/test_preview_static_read_path.py tests/contracts/test_static_builder.py
git commit -m "refactor: shared rail chrome, focus handoff preserved"
```

---

## Task 10: Preserve entangled subsystems (transition, tooltip, print, branches)

**Goal:** Resolve the `::after` collision, keep the reduced-motion transition animator, keep the compact-preview tooltip interactive under the hidden body with a correct chip anchor, and confirm print + branch-disclosure survive.

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py` (transition CSS 4149-4192; ensure the new chevron `::after` and the transient `content:"Context"` at 4187 are state-scoped so exactly one applies), `packages/static/src/raya_static/shell.py` (compact-preview positioning 850-916 anchors to the chip)
- Test: re-assert transition, reduced-motion, tooltip, print tests

- [ ] **Step 1: Run the preserved-subsystem tests to see breakage**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -q -k "transition_end or expansion_keeps_body_accessible or respects_reduced_motion or collapses_and_expands_on_click_only or print_view_is_static_handout"`
Expected: some FAIL (chevron/transient `::after` collision; tooltip anchor; mirror reads).

- [ ] **Step 2: State-scope the `::after` so chevron vs transient content never overlap**

In `rendering.py`, gate the transient `content:"Context"` (4187) strictly to `[data-raya-learning-rail-transition="expanding"]` and the chevron `::after` (`>`/`<`) strictly to the collapsed non-transition state, so at most one resolves. Keep the transition body `visibility:hidden` rules.

- [ ] **Step 3: Keep the collapsed tree links tooltip-interactive**

Ensure the collapsed map keeps the compact-preview hover/focus sources usable: the body is visually hidden but the tooltip's `positionCourseMapCompactPreview` still receives a live `link.getBoundingClientRect()`; anchor horizontally to the chip's `map.right` and vertically to the chip box (not the removed per-band offsets). If `display:none` on the body kills the tooltip, reproduce today's interplay (`updateMapLinkTabOrder`/`setFocusableDescendantsEnabled`) rather than dropping it.

- [ ] **Step 4: Convert mirror reads and confirm print/branch survival**

Switch any mirror reads in these tests to `document.documentElement`. Confirm print rules still hide rails and force `.raya-learning-shell{display:block}` (they key on classes, unaffected by the token grid). Confirm a collapse→expand cycle preserves `raya:course-map-branches` (add a short assertion if absent).

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -q -k "transition_end or expansion_keeps_body_accessible or respects_reduced_motion or collapses_and_expands_on_click_only or print_view_is_static_handout"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/rendering.py packages/static/src/raya_static/shell.py tests/e2e/test_preview_static_read_path.py
git commit -m "fix: preserve transition, tooltip, print, branch subsystems"
```

---

## Task 11: Convert remaining blast-radius tests + full validation

**Goal:** Convert every remaining assertion that encoded the old fragmented behavior, then pass the full suite, the canonical gates, and adversarial browser validation.

**Files:**
- Modify: remaining assertions in `tests/e2e/test_preview_static_read_path.py`, `tests/e2e/test_render_debug_parity_gate.py`, `tests/e2e/test_render_debug_report.py`, `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Run the full reader-rail suites and list every failure**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py tests/contracts/test_static_builder.py tests/e2e/test_render_debug_report.py tests/e2e/test_render_debug_parity_gate.py -q`
Expected: a finite list of failures, each an old-contract assertion (per-width chip offset, element mirror, doubled selector, four-breakpoint geometry, two-column tiles).

- [ ] **Step 2: Convert each failure to the new contract**

For each: replace mirror reads with `document.documentElement`; replace per-width chip-offset expectations with the width-invariant chip; replace the ≥1280-only in-flow expectation with the ≥894 in-flow band; keep every behavioral assertion (coordination, inert, transition, focus). Convert — never delete — the behavior; if an assertion has no home in the new model, move its intent into `test_rail_collapse_contract.py`.

- [ ] **Step 3: Run the full suite green**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py tests/contracts/test_static_builder.py tests/e2e/test_render_debug_report.py tests/e2e/test_render_debug_parity_gate.py tests/e2e/test_rail_collapse_contract.py -q`
Expected: PASS.

- [ ] **Step 4: Canonical gates (sequential)**

Run: `./scripts/check.sh`
Expected: `check: passed` (exit 0).
Run: `./scripts/check-render-debug.sh`
Expected: pass; do not commit render-debug output.

- [ ] **Step 5: Adversarial browser validation**

Dispatch an independent Chromium validation subagent to load the built reader page at 640/768/894/1000/1280/1440, collapse each rail, and confirm by screenshot: single clean chevron chip both sides, no header/body leak, no two-button, no overflow, right rail inline-expanded at <640, drawer modal-inerts the right rail when open. Attach screenshots per repo convention.

- [ ] **Step 6: Final commit**

```bash
git add tests/
git commit -m "test: convert reader-rail suite to single-source collapse contract"
```

---

## Self-review notes (author)

- **Spec coverage:** state single-source (T1–T3), appearance one-block header+body hide (T4), `#id` cliff (T5), 894 reflow no-overflow (T6), medium-band coordination (T7), inert f(state,width,side) + phone parity + modal exception (T8), shared chrome + focus (T9), five entangled subsystems (T7 coordination, T8 modal, T10 transition/tooltip/print/branches, T9 focus/reconciliation), codegen JS+CSS + guardrails (T1–T3, T5), blast-radius conversion (T11). Foundation invariants asserted across T4/T7/T8/T9.
- **Preference channel:** retained (never deleted) — T3 removes only the *effective* mirror writes, leaving `*Preference` writes and `savedReaderShellPreference` intact.
- **Learning-rail drawer:** default-preserve (spec §Entangled #4); no task modifies it; T9 chrome extraction must not orphan its backdrop (`builder.py:2232`).
- **1280 survivor:** `isDesktopShell` kept for tooltip-enable/tab-order and the ≥1280 comfort article floor (T6) — not a collapse boundary.
