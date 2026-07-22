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

**What:** `openLearningRailDrawer` (`packages/static/src/raya_static/shell.py:1096`)
is never called, yet `closeLearningRailDrawer`, `trapLearningRailDrawerFocus`
(`:341`), the scroll-lock write (`:1001`, reset at `:1026`), the backdrop element
(`builder.py:2285`), and CSS at `rendering.py:4317`/`6403`/`6412-6414` all exist for a
state that cannot be entered.

**Decision needed:** remove the dead path, or wire it up if a right-rail
drawer is intended on phones. This is a product decision, not a cleanup.

**Trigger:** next time the right rail's phone behaviour is specified.

## 4. Missing width guard on the right expand handler

**What:** `shell.py:1659` guards `if (!isStructuralRailShell())`; its sibling
expand handler at `:1671-1682` has no such guard. Currently masked because
`syncLearningRailDrawerState()` re-derives the correct value immediately
afterward.

**Trigger:** fold into the next change that touches the learning-rail toggle
handlers.

## 5. Discovery-rail boundary drift

**What:** `rendering.py:6045` (`@media (max-width: 1279px)`, styling
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

**What:** `test_js_and_css_agree_on_band_membership_across_engines`
(`tests/e2e/test_rail_collapse_contract.py`) parametrizes over
chromium/firefox/webkit, but CI currently only provisions Chromium:
`Dockerfile:13` installs system chromium only, and `scripts/check-python.sh`
only installs Playwright Chromium (`RAYA_INSTALL_PLAYWRIGHT_CHROMIUM=1`,
never set by `host-check`). Firefox and WebKit therefore skip in both the
local `check-python.sh` path and the Docker `check-docker.sh` path, and this
test guards nothing on those two engines in CI today.

This is not hypothetical slack — Task 2's own run of this test in the current
sandbox surfaced both halves of the gap directly:

- **Firefox ran and told us nothing new.** Firefox is installed
  (`firefox-1522` under `~/.cache/ms-playwright`) and the test executed for
  real, not as a skip. But the Step 4 diagnostic probe
  (`innerWidth` vs `matchMedia('(min-width: 640px)')`, sampled across 10
  widths including the 640px/894px boundaries) found **zero divergences** on
  either Chromium or Firefox in this environment. Both apparently use
  overlay-style scrollbars (or headless layout that never reserves scrollbar
  width) here, so neither engine can exhibit the classic-scrollbar mismatch
  class that Task 1 actually fixed. A green run on these two engines proves
  the code paths agree wherever engine geometry happens to agree — it does
  not prove the fix defends against the mismatch it was written for.
- **WebKit could not launch at all, for a reason distinct from "not
  installed in CI".** `playwright install webkit` downloaded WebKit 26.4
  (v2287) successfully — the binary is present. It fails at *launch* time
  because the host is missing the shared library `libavif13` (and possibly
  other `playwright install-deps` targets), and this sandbox has no
  passwordless sudo to install it. The test's own `try/except` +
  `pytest.skip` absorbed this correctly (`SKIPPED`, not `FAILED`), but it
  means WebKit — the engine most likely to actually have non-overlay
  scrollbar behavior and thus be able to exercise the divergence class — has
  never run this assertion in this environment at all, download success
  notwithstanding.

So the gap has two independent parts that both need fixing before this test
is doing its intended job anywhere: (a) CI does not install/run firefox or
webkit at all, and (b) even where an engine is available to install, WebKit
additionally needs its host shared-library dependency (`libavif13` via
`sudo playwright install-deps` or `sudo apt-get install libavif13`) or it
downloads but cannot launch — a launch-time failure mode, not an install-time
one, so simply adding a Playwright browser install step is not sufficient by
itself for WebKit specifically.

**Fix:** extend `scripts/check-python.sh` to install firefox/webkit behind a
new `RAYA_INSTALL_PLAYWRIGHT_ENGINES` flag and set it in
`scripts/check-docker.sh:51`, or provision system firefox/webkit in the
Docker image directly; additionally ensure the CI image installs WebKit's
host dependencies (`libavif13` at minimum) so the download that already
succeeds can also launch.

**Trigger:** set `RAYA_REQUIRE_ALL_ENGINES=1` and install the engines (with
WebKit's host dependencies) in CI. Re-run the Step 4 probe once WebKit is
launchable — its non-overlay scrollbar behavior is the strongest remaining
candidate to actually exercise the divergence class this test exists to
catch.
