Status: DONE
Commits created: `7cedf29` Lock rail markup contract
Test summary: RED `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "reader_shell or course_map"` -> 1 failed, 3 passed; GREEN same command -> 4 passed, 105 deselected
Concerns: Existing unrelated working tree changes were left unstaged and untouched.
Report file path: `/home/uumami/itam/raya_lucaria/.superpowers/sdd/task-1-report.md`

Fix review findings:
- Updated `packages/static/src/raya_static/builder.py` so `_render_course_map_tools()` applies `raya-course-rail-search` directly to the search form and removed the stray extra `</div>` from the returned markup.
- Updated `tests/contracts/test_static_builder.py` to require `<form class="raya-course-rail-search raya-command-search-form"...>` and to reject the obsolete wrapper `<div class="raya-course-rail-search">`.
- Verification:
  - RED `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "reader_shell or course_map"` -> `1 failed, 3 passed`
  - GREEN `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "reader_shell or course_map"` -> `4 passed, 105 deselected in 5.51s`

Appendix:
- Added a contract assertion that the reader-shell course tools section carries the stable `data-raya-course-map-tools` hook alongside `class="raya-course-rail-tools"`.
- Verification: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "reader_shell or course_map"` -> `4 passed, 105 deselected in 7.08s`
