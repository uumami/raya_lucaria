# Reader-Rail Correctness Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the reader rail's JS and CSS agree on band membership by construction, close the remaining breakpoint drift, repair the guardrail tests that were passing vacuously, and remove a latent full-height overlay defect.

**Architecture:** The rail's collapsed appearance is driven by two independent systems that must agree: CSS `@media` queries and a JS state derivation. Today the JS derives from `innerWidth` while CSS derives from `@media`, so any engine where those differ produces a **permanently** disagreeing rail — JS state says collapsed while CSS never hides the body. This plan replaces the `innerWidth` input with `matchMedia` evaluated against the *same* boundary strings.

**This is a tradeoff, not a free win — state it accurately.** It does **not** make disagreement "structurally impossible":

- `shell-prepaint.js` is injected as a blocking script in `<head>` **before** any stylesheet and before `<body>` (`builder.py:1023` vs `:1024-1027`, `:1029`). At that moment no scrollbar exists, so the media query returns the *no-scrollbar* answer — numerically identical to what `innerWidth` gave. The prepaint read is **provisional**.
- Agreement is reached **after** `shell.js` runs and the MQ `change` listeners fire (`shell.py:1529-1540`). The accurate claim is *eventually consistent once `shell.js` runs*, converging on the same answer CSS uses.
- Consequently this change can produce a **post-paint state flip** in the narrow scrollbar band, where the old code silently stayed permanently wrong instead. Converging visibly beats being invisibly broken, but the flip is real and Task 1 tests for it.

It then tokenizes the breakpoint literals that escaped the original single-sourcing, and repairs the guardrails so a future regression fails loudly.

**Tech Stack:** Python 3.10, uv workspace (`packages/schema`, `packages/cli`, `packages/static`), pytest, Playwright (Chromium required; Firefox/WebKit added by this plan), CSS and JS emitted as Python strings with `__RAYA_*__` placeholder tokens.

## Global Constraints

- CSS and JS are emitted from brace-dense Python raw strings. **Never** convert them to f-strings or `.format()` — substitution is done exclusively by `str.replace` via `apply_rail_geometry_tokens`.
- `RAIL_EFFECTIVE_DERIVATION_JS` must remain built from resolved Python ints, **not** from `__RAYA_*__` tokens, so it is already final text and stays byte-identical across both emitted scripts.
- Collapse state lives **only** on `document.documentElement.dataset.rayaCourseMap` / `.rayaLearningRail`. Never write a state mirror onto a rail element or `main`.
- Rail geometry constants live **only** in `packages/static/src/raya_static/shell_geometry.py`.
- Run every browser test in the **FOREGROUND**. Never background a test command and wait for a notification.
- Run focused tests while iterating; run the full suite once before the final commit of a task, not after every edit.
- Do not edit generated outputs: `_site/`, `artifact/`, `node_modules/`, `.pytest_cache/`.
- The label string `"OpenDyslexic"` must not change — it is asserted in `tests/contracts/test_documentation_surfaces.py:392,395` and `tests/contracts/test_static_builder.py:4948,4972` (EN + ES).
- Test commands use: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest <path> -v`

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `packages/static/src/raya_static/shell_geometry.py` | The single source of rail breakpoints and the shared JS derivation | Modify: add band-query helper, add compact/structural-minus tokens |
| `packages/static/src/raya_static/shell_prepaint.py` | Pre-paint state application (runs before first paint) | Modify: derive from bands, not `innerWidth` |
| `packages/static/src/raya_static/shell.py` | Runtime shell behaviour | Modify: derive from bands; dedupe default-state functions; tokenize compact query |
| `packages/static/src/raya_static/rendering.py` | CSS emission | Modify: tokenize 5 literal boundaries; prune 9 dead mirror selectors; fix ≥894 collapsing rule; add `<640` font-toggle rule |
| `tests/e2e/test_rail_collapse_contract.py` | Rail invariant guardrails | Modify: absence-assertions, tightened mirror check, real-click test, cross-engine test |
| `tests/e2e/test_preview_static_read_path.py` | Broad layout e2e | Modify: gutter floor, dedupe redundant keys |
| `docs/foundation/20_learning_renderer_contract.md` | Rail seed truth | Modify: codify the invariants |
| `docs/superpowers/specs/2026-07-19-deferred-debt.md` | Deferred work record | Create |

---

### Task 1: Derive rail state from matchMedia instead of innerWidth

Replaces the `width` input to the shared derivation with a band object read via `matchMedia`, using the *same* boundary strings CSS uses. This removes the entire class of JS/CSS disagreement (classic scrollbars, visual-viewport zoom) rather than patching one engine.

**Files:**
- Modify: `packages/static/src/raya_static/shell_geometry.py:21-40`
- Modify: `packages/static/src/raya_static/shell_prepaint.py:19,24`
- Modify: `packages/static/src/raya_static/shell.py:227`
- Test: `tests/e2e/test_rail_collapse_contract.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: JS functions `rayaRailBands()` returning `{ structural: boolean, approved: boolean }`, and `rayaEffectiveRailState(courseMap, learningRail, bands)` returning `{ courseMap, learningRail }`. Python constant `RAIL_EFFECTIVE_DERIVATION_JS` contains both. Later tasks rely on these exact names.

- [ ] **Step 1: Write the failing test**

Add to `tests/e2e/test_rail_collapse_contract.py`:

```python
def test_rail_state_derives_from_media_queries_not_inner_width():
    # JS must derive band membership from the SAME media queries CSS uses.
    # Deriving from innerWidth allows disagreement on engines where the
    # media-query width excludes a classic scrollbar: an innerWidth in
    # [640, 640+scrollbarWidth) puts JS in the structural band (state ->
    # collapsed) while CSS is still below it (body not hidden), which
    # renders a collapsed rail leaking its full body.
    runtime = shell_resources().javascript
    prepaint = shell_prepaint_javascript()
    for script, allowed_inner_width in ((runtime, 2), (prepaint, 0)):
        assert "function rayaRailBands()" in script
        assert "rayaRailBands())" in script
        # Substring assertions like `", innerWidth)" not in script` are a
        # false-pass hole: they do not match `, window.innerWidth)`, which is
        # the spelling used elsewhere in this file. Count instead. The only
        # permitted innerWidth reads are the two compact-preview geometry
        # calculations at shell.py:864,868 -- neither is a band decision.
        assert script.count("innerWidth") == allowed_inner_width, script
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_rail_state_derives_from_media_queries_not_inner_width -v`

Expected: FAIL — `assert "function rayaRailBands()" in script` fails (the function does not exist yet).

- [ ] **Step 3: Replace the derivation in `shell_geometry.py`**

Replace lines 21-32 (the whole `RAIL_EFFECTIVE_DERIVATION_JS` assignment) with:

```python
RAIL_EFFECTIVE_DERIVATION_JS = (
    "function rayaRailBands() {\n"
    "  var printing = matchMedia(\"print\").matches;\n"
    "  return {\n"
    "    structural: printing || matchMedia(\"(min-width: "
    + str(RAIL_STRUCTURAL_PX) + "px)\").matches,\n"
    "    approved: printing || matchMedia(\"(min-width: "
    + str(RAIL_APPROVED_PX) + "px)\").matches\n"
    "  };\n"
    "}\n"
    "function rayaEffectiveRailState(courseMap, learningRail, bands) {\n"
    "  if (!bands.structural) {\n"
    "    return { courseMap: \"expanded\", learningRail: \"expanded\" };\n"
    "  }\n"
    "  if (!bands.approved && courseMap === \"expanded\""
    " && learningRail === \"expanded\") {\n"
    "    return { courseMap: \"collapsed\", learningRail: \"collapsed\" };\n"
    "  }\n"
    "  return { courseMap: courseMap, learningRail: learningRail };\n"
    "}"
)
```

Also update the comment block above it (lines 7-20). Replace its first paragraph with:

```python
# The one definition of the effective-state rule, embedded verbatim in BOTH
# the prepaint and runtime scripts. Pure function of (preference, bands):
#   not structural   -> both expanded (left is presented as a drawer in CSS/JS)
#   approved         -> caller's preference (default expanded)
#   structural & !approved & both expanded -> collapse both (medium-band
#                                             mutual exclusion)
#
# Bands are read via matchMedia against the SAME boundary strings the CSS
# @media rules use, so JS and CSS converge on the same answer. Deriving from
# innerWidth instead allows a PERMANENT mismatch on engines where the
# media-query width excludes a classic scrollbar.
#
# The prepaint read is PROVISIONAL: shell-prepaint.js runs before any
# stylesheet and before <body>, so no scrollbar exists yet and the query
# returns the no-scrollbar answer. Agreement is reached once shell.js runs
# and the MQ change listeners fire.
#
# `printing` forces the widest band. During print, viewport media features
# resolve against the PAGE BOX (~700-760px at A4/Letter 96dpi), which would
# otherwise flip `approved` false and collapse BOTH rails in the printout for
# any user with an expanded/expanded preference. innerWidth was immune
# because it is not re-scoped to the page box.
```

- [ ] **Step 4: Update the prepaint script**

In `packages/static/src/raya_static/shell_prepaint.py`, replace lines 18-26
(both `applyEffective` and `applyDefaults`) so the bands are read **once** per
path rather than re-evaluated by each function:

```javascript
  const applyEffective = (courseMap, learningRail, bands) => {
    const result = rayaEffectiveRailState(courseMap, learningRail, bands || rayaRailBands());
    root.dataset.rayaCourseMap = result.courseMap;
    root.dataset.rayaLearningRail = result.learningRail;
  };
  const applyDefaults = () => {
    const bands = rayaRailBands();
    const expanded = !bands.structural || bands.approved;
    const state = expanded ? "expanded" : "collapsed";
    applyEffective(state, state, bands);
  };
```

- [ ] **Step 5: Update the runtime script**

In `packages/static/src/raya_static/shell.py`, replace line 227:

```javascript
    return rayaEffectiveRailState(next.courseMap, next.learningRail, rayaRailBands());
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py -v`

Expected: PASS — all tests in the file, including the pre-existing
`test_rail_geometry_is_single_sourced_across_scripts`.

If `test_rail_geometry_is_single_sourced_across_scripts` fails on its
`"894" in prepaint and "640" in prepaint` assertion, that is expected only if
you removed the numbers entirely — they are still present inside the
`matchMedia` strings, so it should pass. Do **not** weaken that test.

- [ ] **Step 7: Run the broader rail suite**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -v -k "rail or map or shell"`

Expected: PASS. This is a browser suite — run it in the FOREGROUND.

- [ ] **Step 7b: Prove the no-flash guarantee at the boundary**

The design required this gate and it must not be skipped: this change can
introduce a **post-paint rail flip**. Under the old code, when content loaded
and a scrollbar shrank the MQ width across 640 or 894, the MQ `change` event
fired but `innerWidth` had not changed, so the derived state was unchanged and
nothing moved. Now the same event re-derives from *changed* bands.

Add to `tests/e2e/test_rail_collapse_contract.py`:

```python
def test_rail_state_does_not_flip_after_first_paint(tmp_path):
    # Task 1 made band reads reactive to media queries. Verify that does not
    # produce a visible rail flip when content loads and a scrollbar appears.
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(_browser_executable()),
                                        headless=True, args=["--no-sandbox"])
            try:
                for width in (638, 640, 645, 648, 892, 894, 898):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    page.add_init_script("""
                      window.__rayaFlips = [];
                      document.addEventListener('DOMContentLoaded', () => {
                        const r = document.documentElement;
                        new MutationObserver(() => {
                          window.__rayaFlips.push(r.dataset.rayaCourseMap);
                        }).observe(r, { attributes: true,
                                        attributeFilter: ['data-raya-course-map'] });
                      });
                    """)
                    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                    page.wait_for_timeout(400)
                    flips = page.evaluate("() => window.__rayaFlips || []")
                    # Any change of VALUE after first paint is a visible flip.
                    assert len(set(flips)) <= 1, (width, flips)
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_rail_state_does_not_flip_after_first_paint -v`

Expected: PASS. **If it FAILS**, the flip is real at that width — do not
suppress it. Report status DONE_WITH_CONCERNS with the exact `(width, flips)`
so the tradeoff can be judged deliberately.

- [ ] **Step 8: Commit**

```bash
git add packages/static/src/raya_static/shell_geometry.py \
        packages/static/src/raya_static/shell_prepaint.py \
        packages/static/src/raya_static/shell.py \
        tests/e2e/test_rail_collapse_contract.py
git commit -m "Derive rail band membership from matchMedia instead of innerWidth

JS derived bands from innerWidth while CSS derived them from @media. On
engines where the media-query width excludes a classic scrollbar, an
innerWidth in [640, 640+scrollbarWidth) put JS in the structural band while
CSS was still below it, rendering a collapsed rail that leaked its body --
permanently, since innerWidth never changed to correct it.

Both scripts now read bands via matchMedia against the same boundary strings
the CSS uses, so the two converge. This is eventual, not structural: the
prepaint read precedes stylesheet application and content layout, so it is
provisional until shell.js runs and the MQ listeners fire. The tradeoff is a
possible post-paint flip in the scrollbar band instead of a permanent wrong
state; a regression test guards it.

rayaRailBands() forces the widest band while printing. Viewport media
features resolve against the page box (~700-760px), which would otherwise
collapse both rails in the printout for users with an expanded/expanded
preference. innerWidth was immune because it is not re-scoped to the page
box, so this guard preserves the old printed output."
```

---

### Task 2: Add Firefox and WebKit to the cross-engine boundary test

Task 1 removed the mismatch class; this task proves it on the engines that could expose it. Chromium was already verified to have exact `innerWidth`/media-query agreement, so Chromium alone cannot detect a regression here.

**Files:**
- Test: `tests/e2e/test_rail_collapse_contract.py`

**Interfaces:**
- Consumes: `rayaRailBands()` / `rayaEffectiveRailState(...)` from Task 1.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Install the browsers**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run playwright install firefox webkit
```

Expected: downloads complete. If the environment blocks downloads, report
this as a BLOCKED status rather than skipping the task silently.

- [ ] **Step 2: Write the failing test**

Add to `tests/e2e/test_rail_collapse_contract.py`:

```python
@pytest.mark.parametrize("engine", ["chromium", "firefox", "webkit"])
def test_js_and_css_agree_on_band_membership_across_engines(tmp_path, engine):
    # Across the structural boundary, the state JS derives must match the
    # appearance CSS applies. A disagreement here is the exact shape of the
    # reported bug: state says "collapsed" while the body stays visible.
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        with sync_playwright() as p:
            launcher = getattr(p, engine)
            if engine == "chromium":
                # Chromium must NEVER skip: a bare launcher.launch() finds no
                # Playwright-downloaded chromium in CI, so a blanket
                # try/except would make ALL THREE parametrizations skip and
                # the test would be green-by-skip from the day it lands.
                browser = launcher.launch(executable_path=str(_browser_executable()),
                                          headless=True, args=["--no-sandbox"])
            else:
                try:
                    browser = launcher.launch(headless=True)
                except Exception as exc:
                    if os.environ.get("RAYA_REQUIRE_ALL_ENGINES") == "1":
                        pytest.fail(f"{engine} required but unavailable: {exc}")
                    pytest.skip(f"{engine} unavailable: {exc}")
            try:
                for width in (636, 639, 640, 641, 645, 655, 660, 893, 894, 900):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                    page.wait_for_timeout(150)
                    result = page.evaluate("""() => {
                      const r = document.documentElement;
                      const body = document.querySelector('#raya-course-map-body');
                      return {
                        state: r.dataset.rayaCourseMap,
                        bodyShown: getComputedStyle(body).display !== 'none',
                        structuralMQ: matchMedia('(min-width: 640px)').matches,
                      };
                    }""")
                    # Collapsed state must always mean a hidden body inside the
                    # structural band. NOTE: only this half tests anything --
                    # the `not structuralMQ -> expanded` half is TAUTOLOGICAL
                    # after Task 1, because both sides now read the same
                    # matchMedia('(min-width: 640px)'). Do not over-trust it.
                    if result["structuralMQ"] and result["state"] == "collapsed":
                        assert result["bodyShown"] is False, (engine, width, result)
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 3: Run the test**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_js_and_css_agree_on_band_membership_across_engines -v`

Expected: PASS on all three engines (Task 1 fixed the cause).

**If Firefox or WebKit FAILS:** stop and report it. That is a genuine
engine-specific defect beyond the scrollbar band, and it must be diagnosed,
not worked around. Report status DONE_WITH_CONCERNS with the exact
`(engine, width, result)` tuple.

- [ ] **Step 4: Probe whether this environment can express the mismatch (no source edits)**

**Do not** attempt a RED proof by reverting source. After Task 1 the
derivation lives in `shell_geometry.py` and reads `bands.structural`, so
reverting `shell.py` alone passes a *number* where `.structural` is read →
`undefined` → falsy → the function returns "expanded" for every width and the
test passes trivially, proving nothing. Worse, `git checkout -- shell.py`
would not revert a shim in `shell_geometry.py`, leaving an uncommitted
mutation of the single source of rail geometry in the tree.

Instead, probe the premise directly. Add to the loop, before the assertions:

```python
                    probe = page.evaluate("""() => ({
                      mqStructural: matchMedia('(min-width: 640px)').matches,
                      iwStructural: innerWidth >= 640,
                    })""")
                    if probe["mqStructural"] != probe["iwStructural"]:
                        divergences.append((engine, width, probe))
```

with `divergences = []` before the loop, and after the loop:

```python
            print(f"[{engine}] innerWidth/media-query divergences: {divergences}")
```

Do **not** assert on it. If no divergence occurs on any engine at any probed
width, the engines available here use overlay scrollbars and **cannot express
the mismatch class**. Record that limitation in your report rather than
claiming this test proves the fix.

- [ ] **Step 5: Make the engines reachable in CI, or record the gap**

Measured: `~/.cache/ms-playwright` holds chromium only; `Dockerfile:13`
installs system chromium only; `scripts/check-python.sh:94-99` installs
chromium only and only when `RAYA_INSTALL_PLAYWRIGHT_CHROMIUM=1`, which
`host-check` never sets. So Firefox and WebKit skip in **both** CI jobs and
this test would guard nothing there.

Pick one and do it — do not land the test without either:
- Extend `scripts/check-python.sh:99` to install firefox and webkit behind a
  new `RAYA_INSTALL_PLAYWRIGHT_ENGINES` flag, and set it in
  `scripts/check-docker.sh:53`; or
- Add an entry to `docs/superpowers/specs/2026-07-19-deferred-debt.md` stating
  that the cross-engine test skips in CI and therefore guards nothing there.

- [ ] **Step 6: Commit**

```bash
git add tests/e2e/test_rail_collapse_contract.py
git commit -m "Add cross-engine band-agreement test over the structural boundary

Chromium has exact innerWidth/media-query agreement, so it cannot detect a
regression of the mismatch class Task 1 removed. Firefox and WebKit can."
```

---

### Task 3: Tokenize the five remaining hardcoded breakpoints

The boundary guardrail asserted only that tokens are *present*; it never asserted literals are *absent*, so five hardcoded boundaries survived. This task adds the absence-assertion (RED), then tokenizes (GREEN).

**Files:**
- Modify: `packages/static/src/raya_static/shell_geometry.py:3-5,34-40`
- Modify: `packages/static/src/raya_static/rendering.py:4100,5166,5261,6229,6863`
- Modify: `packages/static/src/raya_static/shell.py:54-56`
- Test: `tests/e2e/test_rail_collapse_contract.py`

**Interfaces:**
- Consumes: `apply_rail_geometry_tokens` from `shell_geometry.py`.
- Produces: new Python constant `RAIL_COMPACT_PX = 768`; new tokens
  `__RAYA_STRUCTURAL_MINUS_PX__` (639) and `__RAYA_COMPACT_MINUS_PX__` (767).

- [ ] **Step 1: Write the failing test**

Add to `tests/e2e/test_rail_collapse_contract.py`:

```python
# Exactly one media query in these files uses a rail-boundary number but is
# NOT a rail boundary: the discovery workspace shell. Its true partner is
# graph.py:1725 (`matchMedia("(max-width: 1279px)")`), which this test does
# not scan, so tokenizing it against a READER-rail constant would couple two
# unrelated subsystems and silently desync from graph.py. It is tracked as
# deferred debt item 5 instead. Allowlist entries must be exact full-line
# matches and must each reference a tracked debt item -- this is not a
# pattern-based skip, which is how the previous guardrail went vacuous.
_NON_RAIL_BOUNDARY_ALLOWLIST = {
    "rendering.py: @media (max-width: 1279px) {",  # debt item 5: discovery rail
}


def test_no_hardcoded_rail_boundaries_in_templates():
    # The presence-only boundary assertions let five literals survive the
    # single-sourcing refactor. Assert ABSENCE: every rail boundary in the
    # CSS/JS templates must be token-sourced, so changing a constant in
    # shell_geometry.py cannot leave a stale literal behind.
    import raya_static.shell as shell_module
    import raya_static.shell_prepaint as prepaint_module

    boundaries = ("640", "639", "894", "893", "1280", "1279", "768", "767")
    sources = {
        "rendering.py": Path(rendering_module.__file__).read_text(encoding="utf-8"),
        "shell.py": Path(shell_module.__file__).read_text(encoding="utf-8"),
        "shell_prepaint.py": Path(prepaint_module.__file__).read_text(encoding="utf-8"),
    }
    offenders = []
    for name, source in sources.items():
        for line in source.splitlines():
            if "min-width:" not in line and "max-width:" not in line:
                continue
            entry = f"{name}: {line.strip()}"
            if entry in _NON_RAIL_BOUNDARY_ALLOWLIST:
                continue
            for boundary in boundaries:
                if f"{boundary}px" in line:
                    offenders.append(entry)
    assert offenders == [], offenders
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_no_hardcoded_rail_boundaries_in_templates -v`

Expected: FAIL listing **exactly** these 6 offenders (the 7th real hit,
`rendering.py:6054 @media (max-width: 1279px)`, is the allowlisted discovery
boundary and must not appear):
- `rendering.py: @media (max-width: 639px) {` (×3 — lines 4100, 5261, 6229)
- `rendering.py: @media (min-width: 1280px) {` (line 5166)
- `rendering.py: @media (min-width: __RAYA_STRUCTURAL_PX__px) and (max-width: 767px) {` (line 6863)
- `shell.py: "(min-width: __RAYA_STRUCTURAL_PX__px) and (max-width: 767px)"` (line 55)

If the test reports **additional** offenders beyond these 6, tokenize them.
Add to `_NON_RAIL_BOUNDARY_ALLOWLIST` **only** if the offender provably
belongs to a non-rail subsystem, and only together with a new deferred-debt
entry — never as a pattern-based skip.

- [ ] **Step 2b: Capture the CSS baseline before any source edit**

Step 9 verifies the tokenization is a pure refactor. Capture the "before"
now, while the source is still unmodified — this avoids any `git stash`
round-trip that could strand your work if interrupted.

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run python -c "
from raya_static.rendering import rich_render_css
open('/tmp/css_before.txt','w').write(rich_render_css())" && echo "baseline captured"
```

Expected output: `baseline captured`

- [ ] **Step 3: Add the new constant and tokens**

In `packages/static/src/raya_static/shell_geometry.py`, after line 5 add:

```python
RAIL_COMPACT_PX = 768

# defaultRailExpanded() (shell.py) drops its isDesktopShell() term because
# desktop implies approved. That reduction is only valid while this holds,
# and nothing else enforces it -- make it structural, not coincidental.
assert RAIL_DESKTOP_PX > RAIL_APPROVED_PX > RAIL_STRUCTURAL_PX
```

Replace the `_TOKENS` dict (lines 34-40) with:

```python
_TOKENS = {
    "__RAYA_RAIL_DERIVATION__": RAIL_EFFECTIVE_DERIVATION_JS,
    "__RAYA_STRUCTURAL_PX__": str(RAIL_STRUCTURAL_PX),
    "__RAYA_APPROVED_PX__": str(RAIL_APPROVED_PX),
    "__RAYA_DESKTOP_PX__": str(RAIL_DESKTOP_PX),
    "__RAYA_STRUCTURAL_MINUS_PX__": str(RAIL_STRUCTURAL_PX - 1),
    "__RAYA_APPROVED_MINUS_PX__": str(RAIL_APPROVED_PX - 1),
    "__RAYA_COMPACT_MINUS_PX__": str(RAIL_COMPACT_PX - 1),
}
```

- [ ] **Step 4: Tokenize the CSS literals**

In `packages/static/src/raya_static/rendering.py`, make these four
replacements. Each `(max-width: 639px)` occurrence becomes
`(max-width: __RAYA_STRUCTURAL_MINUS_PX__px)`:

- Line 4100: `@media (max-width: 639px) {` → `@media (max-width: __RAYA_STRUCTURAL_MINUS_PX__px) {`
- Line 5261: same replacement
- Line 6229: same replacement
- Line 5166: `@media (min-width: 1280px) {` → `@media (min-width: __RAYA_DESKTOP_PX__px) {`
- Line 6863: `@media (min-width: __RAYA_STRUCTURAL_PX__px) and (max-width: 767px) {` → `@media (min-width: __RAYA_STRUCTURAL_PX__px) and (max-width: __RAYA_COMPACT_MINUS_PX__px) {`

Because there are three identical `(max-width: 639px)` lines, apply them by
line number, not with a global replace-all, and verify the count afterward:

```bash
grep -c "max-width: __RAYA_STRUCTURAL_MINUS_PX__px" packages/static/src/raya_static/rendering.py
```
Expected output: `3`

- [ ] **Step 5: Tokenize the JS literal**

In `packages/static/src/raya_static/shell.py`, replace lines 54-56:

```javascript
  const compactStructuralRailQuery = window.matchMedia(
    "(min-width: __RAYA_STRUCTURAL_PX__px) and (max-width: __RAYA_COMPACT_MINUS_PX__px)"
  );
```

- [ ] **Step 6: Dedupe the triplicated default-state rule**

`defaultCourseMapExpanded` and `defaultLearningRailExpanded`
(`shell.py:174-184`) are verbatim copies of each other, and both restate the
rule prepaint's `applyDefaults` implements — three copies that must stay
identical. Note `isDesktopShell()` is redundant in the expression: 1280 > 894,
so `approvedRailGeometryQuery.matches` is already true whenever
`isDesktopShell()` is.

Replace both functions (`shell.py:174-184`) with one:

```javascript
  function defaultRailExpanded() {
    return !isStructuralRailShell() || approvedRailGeometryQuery.matches;
  }
```

Then update the two call sites in `effectiveReaderShellState`
(`shell.py:224-225`):

```javascript
      courseMap: defaultRailExpanded() ? "expanded" : "collapsed",
      learningRail: defaultRailExpanded() ? "expanded" : "collapsed",
```

Verify no other callers remain:
```bash
grep -n "defaultCourseMapExpanded\|defaultLearningRailExpanded" packages/static/src/raya_static/shell.py
```
Expected: no output.

- [ ] **Step 7: Derive the boundary test's expectations from the constants**

`test_css_and_js_share_the_same_rail_boundaries` pins literal strings
(`"(min-width: 640px)"`, `"894"`). That means changing a constant fails on the
test's own literal, channelling a maintainer into editing the test rather than
fixing the drift. In `tests/e2e/test_rail_collapse_contract.py`, add the
imports:

```python
from raya_static.shell_geometry import (
    _TOKENS,
    RAIL_APPROVED_PX,
    RAIL_STRUCTURAL_PX,
    RAIL_EFFECTIVE_DERIVATION_JS,
)
```

and replace the pinned literals in that test with derived values:

```python
    assert f"(min-width: {RAIL_APPROVED_PX}px)" in css
    assert f"(max-width: {RAIL_APPROVED_PX - 1}px)" in css
    assert f"(min-width: {RAIL_STRUCTURAL_PX}px)" in css
```

Apply the same to `test_rail_geometry_is_single_sourced_across_scripts`:

```python
    assert f"(min-width: {RAIL_APPROVED_PX}px)" in runtime
    assert str(RAIL_APPROVED_PX) in prepaint and str(RAIL_STRUCTURAL_PX) in prepaint
    assert str(RAIL_STRUCTURAL_PX) in runtime
```

- [ ] **Step 8: Run the test to verify it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py -v`

Expected: PASS, all tests.

- [ ] **Step 9: Verify the emitted CSS is unchanged**

The tokenization must be a pure refactor — the resolved output must be
byte-identical to before.

Compare against the baseline captured in Step 2b. **Do not** use
`git stash` — an interruption between stash and pop strands every uncommitted
change of this task in a stash entry that no later step knows about.

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run python -c "
from raya_static.rendering import rich_render_css
open('/tmp/css_after.txt','w').write(rich_render_css())" \
  && diff /tmp/css_before.txt /tmp/css_after.txt && echo "IDENTICAL"
```

Expected output: `IDENTICAL`. If it differs, a token resolved to the wrong
number — fix before committing.

- [ ] **Step 10: Run the browser suite**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -v -k "rail or map or shell"`

Expected: PASS. FOREGROUND only. This covers the `defaultRailExpanded` dedupe,
which changes runtime behaviour paths even though it is logic-equivalent.

- [ ] **Step 11: Commit**

```bash
git add packages/static/src/raya_static/shell_geometry.py \
        packages/static/src/raya_static/rendering.py \
        packages/static/src/raya_static/shell.py \
        tests/e2e/test_rail_collapse_contract.py
git commit -m "Tokenize the five rail boundaries that escaped single-sourcing

Three (max-width: 639px), one (min-width: 1280px), and a (max-width: 767px)
duplicated across rendering.py and shell.py survived the original refactor
because the guardrail asserted only that tokens were present, never that
literals were absent. Adds that absence-assertion and tokenizes all five.

Also collapses defaultCourseMapExpanded/defaultLearningRailExpanded (verbatim
copies of each other, and of prepaint's applyDefaults rule) into one
defaultRailExpanded, and derives the boundary test's expectations from the
constants instead of pinning literals that channel maintainers into editing
the test rather than fixing drift.

Emitted CSS verified byte-identical."
```

---

### Task 4: Prune the nine dead mirror selectors and close the guardrail hole

`test_collapse_selectors_key_off_html_only` skips any line containing `-transition`, which exempts exactly the nine surviving element-mirror selectors. The exemption is unnecessary: the mirror regexes anchor on `data-raya-course-map=` / `data-raya-learning-rail=`, and a suffixed attribute (`...-transition=`) can never match them. Removing the exemption makes the test catch the nine, then we prune them.

**Files:**
- Modify: `tests/e2e/test_rail_collapse_contract.py:102-103`
- Modify: `packages/static/src/raya_static/rendering.py:4157,4161,4167,4182,4193,5358,5364,6574,6576`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: nothing consumed by later tasks.

**CRITICAL — only the second selector of each ruleset is dead.** The
ancestor-rooted first selector of every one of these rulesets is **LIVE**,
measured matching during the 240 ms transition window. Deleting a whole
ruleset causes a visible regression — removing `rendering.py:4166` alone makes
the rail render completely empty for the entire expand animation. Delete
**only** the listed lines.

- [ ] **Step 1: Make the guardrail catch the mirrors (RED)**

In `tests/e2e/test_rail_collapse_contract.py`, replace lines 102-103:

```python
        if "-drawer" in line or "-preference" in line:
            continue  # drawer/preference channels are genuine element attrs
```

That is, remove `"-transition" in line or ` from the condition. Update the
comment above the regexes (line 104) to:

```python
        # Element-mirror forms that go dead when the mirror write is removed.
        # NOTE: these regexes anchor on `data-raya-*=` immediately, so a
        # suffixed attribute (`data-raya-*-transition=`) never matches them.
        # The ancestor-rooted selectors that pair with each mirror are LIVE
        # during the 240ms transition window and are intentionally not caught.
```

Then broaden the detection so a mirror on **any** element is caught, not just
the three classes currently listed. Replace the four `re.search` calls
(lines 105-108) with this **structural** matcher — it splits the selector into
compounds and checks what each attribute is attached to, rather than using
lookbehinds:

```python
        # Any selector that reads collapse state off a non-root element is a
        # mirror. Enumerating element classes (as before) missed mirrors on
        # `body`, `main`, or the article element entirely. A lookbehind-based
        # matcher does NOT work here: `(?<!html)` guards only the FIRST
        # attribute, so a chain like `html[data-raya-course-map=...]
        # [data-raya-learning-rail=...]` false-positives on the second.
        for compound in re.split(r"[,\s>+~]+", line):
            if _MIRROR_ATTR.search(compound) and compound.split("[", 1)[0] not in ("", "html"):
                offenders.append(line.strip())
                break
```

and add this module-level constant near the top of the file:

```python
_MIRROR_ATTR = re.compile(r"\[data-raya-(?:course-map|learning-rail)=")
```

- [ ] **Step 2: Run the test to verify it fails with exactly nine offenders**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_collapse_selectors_key_off_html_only -v`

Expected: FAIL, listing exactly 9 offenders — the `.raya-learning-rail[...]`
and `.raya-course-map[...]` mirror selectors corresponding to
`rendering.py:4157, 4161, 4167, 4182, 4193, 5358, 5364, 6574, 6576`.

If the count is **11**, you used a lookbehind matcher instead of the
structural one — the two extra hits are the LIVE root-rooted chains at
`rendering.py:6566` and `:6879`
(`html[data-raya-course-map="collapsed"][data-raya-learning-rail="collapsed"] ...`).
Do not delete those. Use the structural matcher from Step 1.

If the count is anything else, stop and report.

- [ ] **Step 2b: Verify the CSS still parses after the edits**

Because the guardrail inspects selector text only, it cannot detect a dangling
comma. After Step 3, confirm no selector list was broken:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run python -c "
from raya_static.rendering import rich_render_css
bad = [l.strip() for l in rich_render_css().splitlines() if l.rstrip().endswith(', {')]
assert not bad, bad
print('no dangling selector lists')
"
```

Expected output: `no dangling selector lists`

- [ ] **Step 3: Remove the nine dead mirror selectors (8 are edits, not deletions)**

**This is NOT nine line-deletions.** At 8 of the 9 sites the preceding line
ends in a comma, so deleting the mirror line alone leaves `selector, {` — an
invalid selector list that browsers drop **entirely**, taking the live rule
with it. At `rendering.py:4156` and `4166` that produces exactly the "rail
renders empty mid-expand" regression this task exists to avoid. Worse, Step 4's
guardrail only inspects selector *text*, so a dangling-comma tree would pass
Step 4 and only fail later at Step 5.

Work bottom-up so earlier line numbers stay valid:

| Mirror line | Action |
|---|---|
| `6576` | delete, **and** change line `6575` to end ` {` |
| `6574` | **pure delete** (line 6575 is another selector — the only safe pure deletion) |
| `5364` | delete, **and** change line `5363` to end ` {` |
| `5358` | delete, **and** change line `5357` to end ` {` |
| `4193` | delete, **and** change line `4192` to end ` {` |
| `4182` | delete, **and** change line `4181` to end ` {` |
| `4167` | delete, **and** change line `4166` to end ` {` |
| `4161` | delete, **and** change line `4160` to end ` {` |
| `4157` | delete, **and** change line `4156` to end ` {` |

For example lines 4156-4159 become:

```css
[data-raya-learning-rail="expanded"] .raya-learning-rail[data-raya-learning-rail-transition="expanding"] .raya-learning-rail-header {
  display: none;
}
```

And lines 6573-6578 become:

```css
  html[data-raya-course-map="collapsed"] .raya-course-map[data-raya-course-map-transition="collapsing"] .raya-course-map-list,
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail[data-raya-learning-rail-transition="collapsing"] .raya-learning-rail-body {
    display: none;
  }
```

**Do not** use a regex sweep. `.raya-course-map[data-raya-course-map-root]`
and `[data-raya-course-map-storage-key]` (`builder.py:2199-2201`) are live
attributes with a confusingly similar prefix and must not be touched.

- [ ] **Step 4: Run the test to verify it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py -v`

Expected: PASS, all tests.

- [ ] **Step 5: Verify the live transition rules still apply**

Add this regression test to `tests/e2e/test_rail_collapse_contract.py` so a
future prune cannot remove a live ancestor selector:

```python
def test_transition_window_keeps_rail_chrome_painted(tmp_path):
    # The ancestor-rooted transition selectors are LIVE: they keep the expand
    # chip painted and the header/body hidden during the 240ms animation.
    # Without them the rail renders completely empty mid-expand.
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(_browser_executable()),
                                        headless=True, args=["--no-sandbox"])
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                # Collapse, settle, then start expanding and sample mid-flight.
                page.evaluate(
                    "() => { document.documentElement.dataset.rayaLearningRail = 'collapsed'; }")
                page.wait_for_timeout(320)
                page.click("[data-raya-learning-rail-expand]")
                page.wait_for_timeout(80)  # inside the 240ms window
                mid = page.evaluate("""() => {
                  const rail = document.querySelector('#raya-learning-rail');
                  const chip = rail.querySelector('.raya-learning-rail-expand');
                  const header = rail.querySelector('.raya-learning-rail-header');
                  return {
                    transition: rail.dataset.rayaLearningRailTransition || '',
                    chipShown: getComputedStyle(chip).display !== 'none',
                    headerShown: getComputedStyle(header).display !== 'none',
                  };
                }""")
                assert mid["transition"] == "expanding", mid
                assert mid["chipShown"] is True, mid
                assert mid["headerShown"] is False, mid
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_transition_window_keeps_rail_chrome_painted -v`

Expected: PASS. If it fails, you deleted a live ancestor selector — restore it.

- [ ] **Step 6: Commit**

```bash
git add packages/static/src/raya_static/rendering.py \
        tests/e2e/test_rail_collapse_contract.py
git commit -m "Prune nine dead element-mirror selectors and close guardrail hole

test_collapse_selectors_key_off_html_only skipped any line containing
-transition, which exempted exactly the nine surviving mirror selectors:
removing the skip yielded 9 offenders while the suite stayed green. The
exemption was unnecessary — the regexes anchor on data-raya-*= so a suffixed
attribute never matches.

Only the mirror-rooted second selector of each ruleset is dead. The
ancestor-rooted selectors are live during the 240ms transition window and
are retained, now covered by a regression test."
```

---

### Task 5: Fix the latent full-height overlay at ≥894px

At ≥894px the collapsing rule re-grants `display: block` to the rail body, overriding the collapse `display: none` (specificity 0,4,0 vs 0,2,1). Measured 100 ms after collapse: the right rail is **44 × 10,466 px**. Benign today only because `visibility: hidden` and `pointer-events: none` are also set — it is a latent full-page click-blocker.

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py:5357-5362` (line numbers shift after Task 4 — locate by content)
- Test: `tests/e2e/test_rail_collapse_contract.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Write the failing test**

Add to `tests/e2e/test_rail_collapse_contract.py`:

```python
def test_collapsed_rail_never_exceeds_viewport_height(tmp_path):
    # At >=894 the collapsing rule re-granted display:block to the rail body,
    # overriding the collapse display:none, making the collapsed rail a
    # 44 x 10466px fixed element -- a latent full-page click-blocker.
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(_browser_executable()),
                                        headless=True, args=["--no-sandbox"])
            try:
                for width in (894, 1000, 1280, 1440):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                    page.click("[data-raya-learning-rail-collapse]")
                    page.wait_for_timeout(100)  # mid-transition, the risky window
                    box = page.evaluate("""() => {
                      const r = document.querySelector('#raya-learning-rail');
                      const b = r.getBoundingClientRect();
                      return { w: Math.round(b.width), h: Math.round(b.height) };
                    }""")
                    assert box["h"] <= 900, (width, box)
                    page.wait_for_timeout(250)  # settled
                    settled = page.evaluate("""() => {
                      const r = document.querySelector('#raya-learning-rail');
                      const b = r.getBoundingClientRect();
                      return { w: Math.round(b.width), h: Math.round(b.height) };
                    }""")
                    assert settled["h"] <= 900, (width, settled)
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_collapsed_rail_never_exceeds_viewport_height -v`

Expected: FAIL at the mid-transition assertion with a height near 10466.

- [ ] **Step 3: Remove the `display: block` re-grant**

**There is no fade to preserve.** Verified: the only relevant `transition:` is
on the rail itself (`rendering.py:4032` — `border-color, box-shadow, opacity,
transform, width`), nothing on `.raya-learning-rail-body`, and the collapsed
appearance never animates `opacity`. The rule already sets
`visibility: hidden`, so the contents are invisible from frame 1 today.

**A `max-height: 100%` fix does not work** — measured as a total no-op
(10465.5 px unchanged at all four widths). The collapsed rail is
`position: fixed` with `top: 0.75rem`, `height: auto`, and `max-height: none`
(`rendering.py:6782-6800`), so a percentage `max-height` on its child resolves
against an auto-height containing block and computes to `none`.

In `packages/static/src/raya_static/rendering.py`, find the ruleset (inside
`@media (min-width: __RAYA_APPROVED_PX__px)`, decls at `:5359-5361`) whose
selector is:

```css
  [data-raya-learning-rail="collapsed"] .raya-learning-rail[data-raya-learning-rail-transition="collapsing"] .raya-learning-rail-body {
```

Replace its declaration block with:

```css
    display: none;
  }
```

Measured result: 44 × **40** px mid-transition at 894/1000/1280/1440 —
identical to the settled state. A full-page screenshot diff at 1280×900 at
100/180/300 ms after collapse shows **4 differing pixels** (a search-input
caret), so there is no visual regression.

This also restores the invariant the comment at `rendering.py:5355-5356`
already claims is true ("Collapsed header/body display:none lives in the
single ... region"), which the `max-height` patch would have left a lie.

- [ ] **Step 4: Run the test to verify it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py -v`

Expected: PASS, all tests.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/rendering.py \
        tests/e2e/test_rail_collapse_contract.py
git commit -m "Stop the collapsing rail from becoming a full-height overlay

At >=894 the collapsing rule re-granted display:block to the rail body,
overriding the collapse display:none (specificity 0,4,0 vs 0,2,1). Measured
100ms after collapse the rail was 44 x 10466px -- benign only because
visibility:hidden and pointer-events:none were also set, but a latent
full-page click-blocker.

Drops the display:block re-grant entirely. There is no fade to preserve --
nothing transitions on .raya-learning-rail-body and the rule already sets
visibility:hidden, so contents are invisible from frame 1. Measured 44x40
mid-transition at 894/1000/1280/1440, with a 4-pixel screenshot diff.

Also restores the invariant the adjacent comment already claimed."
```

---

### Task 6: Drive the collapse contract through real clicks

`test_collapsed_rails_are_single_clean_chips` writes `documentElement.dataset` directly, bypassing every toggle handler — so the real interaction path (drawer branch, medium-band mutual exclusion, focus target, persistence) is untested by the contract suite.

**Files:**
- Modify: `tests/e2e/test_rail_collapse_contract.py:166-213`

**Interfaces:**
- Consumes: `_collapsed_chip` helper (already defined at line 140).
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Add the click-driven variant**

Add to `tests/e2e/test_rail_collapse_contract.py` (keep the existing
dataset-driven test — it covers the CSS contract independent of JS):

```python
def test_collapse_via_real_clicks_produces_clean_chips(tmp_path):
    # The dataset-driven test bypasses every toggle handler. This drives the
    # real interaction path: handler -> state -> persistence -> appearance.
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(_browser_executable()),
                                        headless=True, args=["--no-sandbox"])
            try:
                for width in (894, 1280, 1440):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                    page.click("[data-raya-course-map-toggle]")
                    page.click("[data-raya-learning-rail-collapse]")
                    page.wait_for_timeout(320)  # past the 240ms transition
                    state = page.evaluate("""() => {
                      const r = document.documentElement;
                      return { map: r.dataset.rayaCourseMap,
                               rail: r.dataset.rayaLearningRail };
                    }""")
                    assert state == {"map": "collapsed", "rail": "collapsed"}, (width, state)
                    for sel in ("#raya-course-map", "#raya-learning-rail"):
                        side = _collapsed_chip(page, sel)
                        assert side["controlCount"] == 1, (width, sel, side)
                        assert side["headerShown"] is False, (width, sel, side)
                        assert side["bodyShown"] is False, (width, sel, side)
                    overflow = page.evaluate(
                        "() => Math.ceil(document.documentElement.scrollWidth - innerWidth)")
                    assert overflow <= 1, (width, overflow)
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run the test**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py::test_collapse_via_real_clicks_produces_clean_chips -v`

Expected: PASS. If the map toggle selector does not resolve, inspect the
emitted HTML for the correct attribute rather than weakening the assertions:
```bash
grep -o 'data-raya-course-map-toggle[^>]*' examples/courses/render-fixture/artifact/site/index.html | head -3
```

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/test_rail_collapse_contract.py
git commit -m "Drive the collapse contract through real clicks

The existing contract test writes documentElement.dataset directly, so the
toggle handlers, medium-band mutual exclusion, and persistence path were
never exercised. Adds a click-driven variant alongside it."
```

---

### Task 7: Two verified follow-ups (a third was measured and rejected)

Each was independently measured. No assumption is being carried forward from the original design.

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py:17090-17091,17095-17096,17327-17328` (gutter)
- Modify: `tests/e2e/test_preview_static_read_path.py:13829-13831,13929-13931,14006-14008,14287-14289,14335-14337,21353` (dedupe)
- (font-toggle label change CUT — see Step 4)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Restore the gutter floor to 24**

The gutter measured **exactly 24.0 px** at 1440/1280/1024/950/894, with
OpenDyslexic + x-large text, and at deviceScaleFactor 1.25 and 2. It is a
fixed `1.5rem` grid track (`rendering.py:5333-5344`), not a content-dependent
measurement, so there is no sub-pixel jitter. The pre-refactor contract was
`>= 24`; `>= 20` was a needless loosening.

Independently re-measured: **220 samples across widths 894-2560, DPR
1/1.25/1.5/2/2.625, with and without OpenDyslexic + x-large text — every
single one exactly `(24, 24)`.** No jitter, including across the 894/1280/1800
band boundaries.

In `tests/e2e/test_preview_static_read_path.py`, change `>= 20` to `>= 24` at
lines 17090-17091, 17095-17096, and 17327-17328, and add this comment above
each pair:

```python
        # 1.5rem grid track -> 24px at the stock 16px root font size. This
        # assertion therefore depends on the BROWSER's default font size, not
        # any in-page setting: a profile with a 15px default yields 22.5 and
        # fails. Relevant when running via RAYA_TEST_BROWSER against a
        # personal browser profile.
```

- [ ] **Step 2: Run the gutter tests**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -v -k "gutter or workspace or chrome"`

Expected: PASS.

- [ ] **Step 3: Dedupe the byte-identical assertion keys**

At `tests/e2e/test_preview_static_read_path.py:14287-14289` these three keys
are byte-identical JS expressions (before commit `e862dbb` they read three
different elements; the mirror-removal conversion collapsed them):

```js
rootState: root.dataset.rayaLearningRail,
shellState: document.documentElement.dataset.rayaLearningRail,
railState:  document.documentElement.dataset.rayaLearningRail,
```

Keep **one** key per group and update the matching assertions. Apply the same
at `:14335-14337` (learning rail) and `:13829-13831`, `:13929-13931`,
`:14006-14008` (course map, keys `state`/`shellState`/`mapState`). Assertions
to update are at `:14305-14307`, `:14357-14359`, `:13858`, `:13966`, `:14030`.

Note "byte-identical" is loose for the two learning-rail groups: they read
`root.` vs `document.documentElement.` with `const root =
document.documentElement` bound at `:14280`/`:14324`. Same DOM property, so
deduping is still safe.

**At `:14305-14307`, remove only `:14305-14306`.** Line `:14307` is
`bodyHidden`, not a state key — keep it. (The `:14357-14359` range is correct
as stated.)

Also fix the degenerate conditional — it is at **`:21364`**, NOT `:21353`:
```python
"mapHidden": "false" if not modal else "false"
```
becomes:
```python
"mapHidden": "false"
```
**Do not edit `:21353`** — that line is `"scrollLock": "true" if modal else
"false"`, a legitimate conditional; changing it would silently break the
scroll-lock assertion.

While here, remove the unreferenced `const shell =
document.querySelector('#raya-content');` at `:14281` and `:14325` — no
returned key uses it.

- [ ] **Step 4: Add the `<640` OpenDyslexic label rule**

At 390/375/320 px with the drawer open, the label renders 2 lines (28.8 px at
`line-height: 14.4px`), making the button 45.2 px vs 28 px for every sibling
in a 2-column grid. The ≥640 band already has the fix
(`rendering.py:6764-6766`); there is no `<640` counterpart.

**DECIDED 2026-07-19: leave it alone. This step is CUT — implement nothing
here.** Skip to Step 5. The rationale below is retained so the decision is not
silently revisited.

The obvious fix is **measured broken**. Copying the ≥640 rule to the base
block makes the word escape its button by **13 px** (painted right edge 141.2
vs button right 128.0 at 390 px), spilling into the adjacent grid cell.
Cause: the base label has `overflow-wrap: anywhere` **and** `min-width: 0`
(`rendering.py:4272-4279`); `anywhere` is what collapses the flex item's
min-content contribution to a 64 px box. Removing `anywhere` without also
handling `min-width` keeps the narrow box but forbids the break. The ≥640
version is safe only because it is paired with `flex-direction: column` and
`overflow: hidden` (`rendering.py:6750-6759`), which the base button block
(`rendering.py:4238-4250`) has neither of.

Measured options, all at 390/375/320 with and without OpenDyslexic:

| option | button height | spill past button | verdict |
|---|---|---|---|
| **do nothing** (current) | 45.2 (siblings 28) | 0 | ragged, but nothing escapes |
| naive copy of ≥640 rule | 31.4 | **13 px** | broken — rejected |
| `font-size: 0.6rem` alone | 39.4 | 0 | **still wraps** — doesn't fix it |
| ellipsis truncation | 31.4 | 0 | works, but renders `OpenDysle…` |
| `flex-direction: column` | **47.3** | 0 | worse than the defect |

The only measured non-overflowing fix truncates the visible label to
`OpenDysle…`. Since the entire motivation here is cosmetic, trading a
two-line wrap for a truncated word is a downgrade, not a fix — which is why
the decision was to leave it.

**Do not** attempt any of the rejected options, and do not shorten the label
text — it is asserted in four EN+ES test sites (see Global Constraints).

- [ ] **Step 5: Confirm the drawer is untouched**

Step 4 was cut, so this only confirms the dedupe and gutter edits did not
disturb the drawer. Run in the FOREGROUND:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -v -k "drawer or mobile or phone"
```

Expected: PASS.

- [ ] **Step 6: Run the full suite**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q`

Expected: PASS with pristine output (no warnings introduced by these changes).

- [ ] **Step 7: Commit**

```bash
git add tests/e2e/test_preview_static_read_path.py \
        packages/static/src/raya_static/rendering.py
git commit -m "Restore gutter floor to 24 and dedupe redundant assertion keys

Gutter re-measured across 220 samples (widths 894-2560, DPR 1-2.625, with
and without OpenDyslexic + x-large text): every sample exactly 24.0. The
>= 20 floor was a needless loosening of the pre-refactor >= 24 contract.
Comments record that 24 depends on the browser's stock 16px root font.

The rootState/shellState/railState keys read the same DOM property after the
mirror-read conversion; keeps one per group. Also fixes a degenerate
conditional that always yielded 'false'.

The phone-drawer OpenDyslexic label wrap was deliberately NOT fixed: every
measured fix was a downgrade. The naive rule overflows the button by 13px,
a smaller font still wraps, stacking makes the button taller than the
defect, and the only clean option truncates the label to 'OpenDysle...'.
Recorded rather than patched."
```

---

### Task 8: Document the invariants and record deferred debt

The documentation is what actually prevents the smearing from recurring — the original breakage happened because one visual state was expressible in many places with no written rule.

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Create: `docs/superpowers/specs/2026-07-19-deferred-debt.md`

**Interfaces:**
- Consumes: the invariants established by Tasks 1-6.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Read the existing contract doc**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run cat docs/foundation/20_learning_renderer_contract.md | head -60
```

Match its existing heading style and tone.

- [ ] **Step 2: Append the invariants section**

Add to `docs/foundation/20_learning_renderer_contract.md`:

```markdown
## Rail Collapse Invariants

These four rules exist because the collapsed rail broke repeatedly when one
visual state was expressible in many places. Each is enforced by a guardrail
in `tests/e2e/test_rail_collapse_contract.py`.

1. **Geometry is single-sourced.** Every rail breakpoint lives in
   `packages/static/src/raya_static/shell_geometry.py` and reaches CSS and JS
   only through `__RAYA_*__` tokens. A literal `px` boundary **outside**
   `shell_geometry.py` — in a rail `@media` rule or a `matchMedia` string — is
   a defect, not a shortcut. Inside `shell_geometry.py` the literals are the
   single source, built from the Python ints.

2. **JS and CSS derive band membership from the same source.** Both read
   `matchMedia` against identical boundary strings. Deriving band membership
   from `innerWidth` is forbidden: on engines where the media-query width
   excludes a classic scrollbar the two disagree **permanently**, producing a
   rail whose state says "collapsed" while its body stays visible.

   Two caveats, both deliberate. The **prepaint read is provisional**:
   `shell-prepaint.js` runs before any stylesheet and before `<body>`
   (`builder.py:1023` vs `:1024-1029`), so no scrollbar exists yet and the
   query returns the no-scrollbar answer. Agreement is reached once
   `shell.js` runs and the MQ `change` listeners fire — so the guarantee is
   *eventual consistency*, not structural impossibility. And `rayaRailBands()`
   **forces the widest band while printing**, because viewport media features
   resolve against the page box (~700-760px), which would otherwise collapse
   both rails in the printout.

3. **Collapse state lives only on the root element.** It is written to
   `document.documentElement.dataset.rayaCourseMap` / `.rayaLearningRail` and
   nowhere else. Never mirror it onto a rail element or `main`. CSS reads it
   only via `html[data-raya-...]`.

4. **Collapsed appearance is defined in one region.** The
   "rail collapse: appearance (single source)" region owns the collapsed
   header/body hiding and the chip. Band-scoped fragments elsewhere are how
   the original drift happened.

Note that the transition channel (`data-raya-*-transition`) is a genuine
element-level attribute and is not a state mirror. Its ancestor-rooted
selectors are live during the 240 ms animation window: they keep the expand
chip painted and the header hidden while the rail animates. Removing them
makes the rail render empty mid-animation.
```

- [ ] **Step 3: Write the deferred-debt record**

Create `docs/superpowers/specs/2026-07-19-deferred-debt.md`:

```markdown
# Deferred Debt — Reader Renderer

Recorded 2026-07-19 from the rail correctness cleanup. Each entry states a
prerequisite and a trigger so it is actionable rather than a vague "someday".

## 1. Asset cache-busting

**What:** Generated assets are referenced by stable, unversioned paths, so a
returning browser can serve a stale `rich.css`/`shell.js` after a deploy.

**Mechanism required: hashed paths, NOT query strings.** Measured against the
production edge three times with never-before-seen query strings: all returned
`x-cache: HIT` on first request, proving the GitHub Pages CDN cache key
ignores the query string. `?v=` would be actively worse than nothing — the
browser keys on the query string, fetches the "new" URL, receives stale bytes
from the query-insensitive edge, and re-pins them under a fresh TTL.

**Size:** ~14 generated assets across 7 emission surfaces (reader, inspection,
and 5 discovery surfaces), ~72 literal test assertion sites, plus hardcoded
paths in `packages/cli/src/raya_cli/render_debug_report.py:444,1061`.

**Build-order constraint:** pages render (`builder.py:350-406`) before assets
are written (`:424-431`), so hashes must come from generator output strings,
not from disk. Hashed *directories* additionally fix font URLs embedded inside
CSS bytes, which no call-site rewrite can reach.

**Prerequisite:** none technical — asset generation was verified deterministic
(two independent builds produced byte-identical assets).

**Trigger:** when stale assets cause a second reported incident, or when a
CDN with a longer TTL than the current `max-age=600` is introduced.

**Urgency:** modest for the deployed site (staleness self-heals in ten
minutes). The genuinely unbounded case is the local preview server, which
sends no cache headers at all (`packages/cli/src/raya_cli/preview.py:7,20`),
so browsers apply heuristic freshness.

## 2. Extract CSS from the rendering.py monolith

**What:** `packages/static/src/raya_static/rendering.py` is ~7,800 lines,
almost all of it CSS emitted as a Python string. This is the structural reason
rail state could smear across the file with related rules thousands of lines
apart.

**Prerequisite:** a visual-regression or byte-diff safety net must exist
first. Extracting this much CSS without one risks silent visual regressions
that no current test would catch.

**Trigger:** the next time rail CSS needs a structural change. Do not attempt
it as a rider on unrelated work — a half-extracted system (some rules in
modules, some in the string) is worse than a consistent monolith.

## 3. Right-rail dead drawer path

**What:** `openLearningRailDrawer` (`packages/static/src/raya_static/shell.py:1104-1122`)
is never called, yet `closeLearningRailDrawer`, `trapLearningRailDrawerFocus`
(`:352`), the scroll-lock write (`:1008`), the backdrop element
(`builder.py:2285`), and CSS at `rendering.py:6408`/`6443` all exist for a
state that cannot be entered.

**Decision needed:** remove the dead path, or wire it up if a right-rail
drawer is intended on phones. This is a product decision, not a cleanup.

**Trigger:** next time the right rail's phone behaviour is specified.

## 4. Missing width guard on the right expand handler

**What:** `shell.py:1668` guards `if (!isStructuralRailShell())`; its sibling
expand handler at `:1680` has no such guard. Currently masked because
`syncLearningRailDrawerState()` re-derives the correct value immediately
afterward.

**Trigger:** fold into the next change that touches the learning-rail toggle
handlers.

## 5. Discovery-rail boundary drift

**What:** `rendering.py:6054` (`@media (max-width: 1279px)`, styling
`.raya-discovery-workspace-shell` / `.raya-discovery-course-rail`) and its
partner `packages/static/src/raya_static/graph.py:1725`
(`matchMedia("(max-width: 1279px)")`) are the same boundary duplicated across
CSS and JS — the identical failure mode the reader rail just fixed.

It is deliberately **not** tokenized against `RAIL_DESKTOP_PX`: that would
couple discovery-rail geometry to a reader-rail constant, and would silently
desync from `graph.py`, which the reader-rail guardrail does not scan. It is
allowlisted in `test_no_hardcoded_rail_boundaries_in_templates` with a
pointer to this entry.

**Prerequisite:** none.

**Trigger:** next time discovery/graph rail geometry is touched. The fix is a
discovery-owned constant plus extending the guardrail's scanned sources to
include `discovery.py` and `graph.py`.

## 6. Cross-engine test does not run in CI

**What:** `test_js_and_css_agree_on_band_membership_across_engines` skips
Firefox and WebKit in both CI jobs. `~/.cache/ms-playwright` holds chromium
only, `Dockerfile:13` installs system chromium only, and
`scripts/check-python.sh:94-99` installs chromium only, gated on
`RAYA_INSTALL_PLAYWRIGHT_CHROMIUM=1` which `host-check` never sets.

Chromium has exact `innerWidth`/media-query agreement, so the engines that
could actually expose the mismatch class are exactly the ones not running.

**Trigger:** set `RAYA_REQUIRE_ALL_ENGINES=1` and install the engines in CI.

**Note:** delete this entry if Task 2 Step 5 was resolved by extending CI
rather than by recording the gap.
```

- [ ] **Step 4: Verify the reset checks still pass**

Run:
```bash
cd /home/uumami/itam/raya_lucaria
find docs/foundation -maxdepth 1 -type f | sort
rg -n "Eleventy|Tailwind|Pagefind" docs/foundation -g '!14_domain_language.md'
```

Expected: the foundation file list includes `20_learning_renderer_contract.md`;
the `rg` command returns no matches (exit 1 is correct).

- [ ] **Step 5: Run the documentation contract tests**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add docs/foundation/20_learning_renderer_contract.md \
        docs/superpowers/specs/2026-07-19-deferred-debt.md
git commit -m "Codify rail collapse invariants and record deferred debt

The original breakage happened because one visual state was expressible in
many places with no written rule. Documents the four invariants each
guardrail enforces, including that the transition channel is a genuine
element attribute whose ancestor selectors are live mid-animation.

Records four deferred items with prerequisites and triggers: asset
cache-busting (needs hashed paths -- query strings are provably ignored by
the CDN cache key), the rendering.py CSS extraction, the right-rail dead
drawer path, and a missing width guard."
```

---

## Final Verification

- [ ] **Run the full test suite in the FOREGROUND**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q
```

Expected: all pass, output pristine.

- [ ] **Verify the smoke test**

```bash
./scripts/smoke-test.sh
```

Expected: completes successfully.

- [ ] **Confirm no un-substituted tokens leak into output**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run python -c "
from raya_static.rendering import rich_render_css
from raya_static.shell import shell_resources
from raya_static.shell_prepaint import shell_prepaint_javascript
for name, text in (('css', rich_render_css()),
                   ('shell.js', shell_resources().javascript),
                   ('prepaint.js', shell_prepaint_javascript())):
    leaked = [t for t in ('__RAYA_STRUCTURAL_PX__', '__RAYA_APPROVED_PX__',
                          '__RAYA_DESKTOP_PX__',
                          '__RAYA_STRUCTURAL_MINUS_PX__', '__RAYA_APPROVED_MINUS_PX__',
                          '__RAYA_COMPACT_MINUS_PX__', '__RAYA_RAIL_DERIVATION__')
              if t in text]
    assert not leaked, (name, leaked)
print('no token leaks')
"
```

Expected output: `no token leaks`
