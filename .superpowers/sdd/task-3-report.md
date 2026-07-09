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
