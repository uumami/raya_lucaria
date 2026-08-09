# Gate graph layout repair report

## Scope

Repaired only the four graph workspace regressions identified by the Task 5
host-gate report:

- desktop instruction height,
- mobile selected-edge initial visibility,
- compact mobile toolbar/content-filter geometry, and
- off-viewport mobile list-panel and inspector toggles.

The persistent Course map and single-navigation contract remain unchanged.
Stale command-bar, title, and storage assertions were not part of this repair.

## Root cause

The persistent workspace shell introduced a real grid-item sizing omission.
At a `390x844` viewport the shell's responsive grid track correctly measured
`366px`, but `.raya-workspace-main` combined its inherited `margin: 0 auto`
with intrinsic graph content and expanded to `1835.453125px`. Its toolbar,
canvas, list panel, and inspector panel inherited that width. Consequently:

- the toolbar client width was `1794px`, so the Content filter appeared at
  `702.390625px` instead of after the compact visible strip;
- the canvas extended to `1822.453125px`, leaving the selected active edge
  outside the physical phone viewport; and
- normal Playwright clicks could not scroll the list and inspector toggles
  into the viewport.

The desktop instruction regression was separate width pressure from the same
persistent rail. The narrower main region wrapped the helper copy onto two
lines, and its `1.35` line height produced a `38.875px` block against the
existing `36px` compact bound.

## TDD evidence

The five existing browser regressions were used as behavior-first tests. The
initial focused run reproduced all five failures:

```text
5 failed in 85.10s
```

The mobile failure values and both 30-second user-like click timeouts matched
the Task 5 report exactly.

The minimal grid-item fix adds `width: 100%` to `.raya-workspace-main`, matching
the explicit stretch contract already used by reader main content. After that
single production change, the selected-edge, compact-toolbar, compact-panels,
and return-to-reading-path checks passed:

```text
4 passed in 26.35s
```

The instruction fix changes only `.raya-graph-instructions` line height from
`1.35` to `1.25`, keeping both wrapped lines visible instead of clipping copy.
The desktop first-viewport check and the mobile first-viewport companion then
passed:

```text
2 passed in 9.65s
```

## Files changed

- `packages/static/src/raya_static/rendering.py`
  - constrain the workspace main grid item to its assigned track;
  - keep two-line graph instructions inside the compact height contract.
- `.superpowers/sdd/2026-08-09-persistent-workspace-course-map/gate-graph-layout-report.md`
  - record diagnosis, TDD evidence, and verification.

## Verification

Fresh combined browser run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q --tb=short \
  tests/e2e/test_preview_static_read_path.py \
  -k 'workspace_course_map or preview_graph_workspace_starts_in_first_desktop_viewport or preview_graph_deeplink_keeps_orientation_controls_in_initial_viewport or preview_graph_mobile_toolbar_uses_compact_command_strip or preview_graph_mobile_defaults_to_compact_panels or graph_page_focus_exposes_return_to_reading_path'
```

Result:

```text
11 passed, 122 deselected in 90.53s (0:01:30)
```

This includes all five original graph regressions and the six-test persistent
workspace Course-map matrix.

Additional contract verification:

```text
tests/contracts/test_static_builder.py: 118 passed in 92.95s (0:01:32)
git diff --check: passed
```
