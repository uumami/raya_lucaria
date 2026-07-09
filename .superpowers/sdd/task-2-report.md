Status: complete

Scope:
- Updated `packages/static/src/raya_static/rendering.py` to replace the old reader-rail tool CSS with the new `raya-course-rail-*` visual system.
- Updated `tests/contracts/test_static_builder.py` to add Task 2 CSS contract coverage in the focused `rich_css` slice.

TDD record:
1. Added the new CSS assertions first.
2. Ran `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "rich_css or reader_shell or course_map"`.
3. Captured the red result: `test_rich_css_defines_learning_shell_regions` failed because `.raya-course-rail-tools` was missing from generated `rich.css`.
4. Replaced the old `.raya-course-map-tool-grid` rail styling with the new rail selectors, compact two-per-row command tiles, and medium-width fixed-rail rules.
5. Re-ran the same focused command and got green: `5 passed, 104 deselected`.

Implementation notes:
- Removed legacy rail CSS selectors such as `.raya-course-map-tool-grid` and `.raya-course-map-tools-label` from the reader rail styling path.
- Added compact rail tile styling for `raya-course-rail-command-list` with `grid-template-columns: repeat(2, minmax(0, 1fr))`.
- Kept the right rail aligned with the left rail in medium-width fixed positioning by using matching `height: calc(100vh - 1.5rem)` and `width: min(16rem, calc(100vw - 3rem))`.
- Preserved existing collapsed-content hiding selectors while updating them to target `raya-course-rail-tools`.
- Used distinct semantic command colors instead of a single-hue rail palette.

Validation:
- `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "rich_css or reader_shell or course_map"` -> `5 passed, 104 deselected`

Concerns:
- `packages/static/src/raya_static/rendering.py` already contained unrelated user changes before this task; this work was patched around them and did not revert them.
