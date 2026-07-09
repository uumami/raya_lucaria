# Task 3 Report

## Scope

- Updated `tests/e2e/test_preview_static_read_path.py` to assert approved browser geometry at `1440x900` and `894x670`.
- Updated `packages/static/src/raya_static/rendering.py` with a narrow `894px-1279px` reader-shell override so inline rails render at the approved screenshot-width viewport.

## TDD Evidence

1. Added the geometry assertions first.
2. Ran:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "reader_shell"
```

3. Observed the expected red failure:

```text
assert 188 <= map_box["width"] <= 290
E assert 188 <= 44
```

4. Applied the targeted CSS override in `rendering.py`.
5. Re-ran the same focused browser test and got green:

```text
2 passed, 108 deselected in 13.46s
```

## Implementation Notes

- The existing `640px-1279px` rules still collapsed both rails to icon trays by default.
- The new `894px-1279px` override restores a three-column inline shell for the approved viewport band and re-exposes the map list, search, and rail command tiles even when the legacy collapsed state is still present on the root.
- The change is scoped to the approved screenshot-width range and leaves mobile drawer behavior untouched.

## Validation

- `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "reader_shell"`

## Concerns

- `tests/e2e/test_preview_static_read_path.py` already had unrelated unstaged edits before this task. I kept them intact and only intend to stage the Task 3 hunk plus the report.
- I only ran the focused browser subset requested by the task, not the full host or Docker check stack.

## Review Findings Follow-up

- Restored the prior reader-shell collapse regression coverage at `1440x900` while keeping the Task 3 approved-viewport inline geometry checks for `1440x900` and `894x670`.
- Added a concrete `894x670` browser assertion that the first four `.raya-course-rail-command` controls render as a compact two-per-row grid.
- No `rendering.py` change was required; the approved layout already satisfied the strengthened browser assertions.

## Follow-up Validation

- `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "reader_shell"`

```text
2 passed, 108 deselected in 12.44s
```

## Re-review Fixes

- Removed the stale Task 3 `@media (min-width: 894px) and (max-width: 1279px)` renderer override from `packages/static/src/raya_static/rendering.py`.
- Re-ran the focused reader-shell browser subset after removing that block and confirmed the approved `894x670` geometry regressed (`map.width == 44`).
- Replaced the stale hunk with a smaller `894px-1279px` cleanup adjustment that only re-expands the collapsed side rails and shell padding needed for the approved viewport band.
- Kept the strengthened browser assertions unchanged; no additional test edits were required for this cleanup pass.

## Re-review Validation

- `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "reader_shell"`

```text
2 passed, 108 deselected in 10.09s
```

## Final Root Cause Fix

- Removed the remaining `894px-1279px` collapsed-state CSS mask from `packages/static/src/raya_static/rendering.py` so the renderer no longer re-expands rails while the root state still says `collapsed`.
- Corrected the root default-state path in `packages/static/src/raya_static/shell.py` by treating widths at or above the approved `894px` geometry breakpoint as expanded defaults for both the course map and learning rail.
- Updated the focused reader-shell e2e coverage so both approved viewports, including `894x670`, assert the initial course-map state is truthfully `expanded` while preserving the compact two-per-row rail-command check.

## Final Note

- The accepted end state for Task 3 does not depend on a renderer-side `894px-1279px` override. The remaining fix is in `packages/static/src/raya_static/shell.py`, where an `approvedRailGeometryQuery` change listener now reapplies the truthful expanded defaults when resizing across the `894px` breakpoint and re-syncs both drawer states.
- The focused reader-shell browser test now covers both truthful approved-viewport root state (`data-raya-course-map="expanded"` and `data-raya-learning-rail="expanded"`) and the `893px -> 894px` resize transition that previously left the shell stuck in the collapsed state.
