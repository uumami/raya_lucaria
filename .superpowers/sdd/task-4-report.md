Status: complete

Summary:
- Added a focused reader-shell collapse regression at the approved `894px` viewport.
- Confirmed the red state first: collapse left 6 course-map links tabbable after transition.
- Fixed the structural course-map drawer sync to reapply collapse tab-order state after it re-enables the map container.

Evidence:
- Red: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "collapse and reader_shell"` failed with `activeHiddenLinks == 6`.
- Green: the same command passed after the shell fix.

Files changed:
- `tests/e2e/test_preview_static_read_path.py`
- `packages/static/src/raya_static/shell.py`
