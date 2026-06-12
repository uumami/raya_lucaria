# Renderer Debug Artifacts Design

Date: 2026-06-12
Status: approved direction, ready for implementation planning

## Context

Glintstone now pre-renders MathJax math during build, serves local math support
resources from `artifact/site/_raya/render/math/`, and has Playwright checks for
visible math, local assets, no external renderer requests, and desktop/mobile
overflow. The remaining problem is diagnostic workflow quality: when a rendered
fixture regresses, agents and contributors need concrete browser evidence that
is easy to inspect without turning screenshots into source truth or expanding
the public CLI surface.

The next loop uses the Superpowers workflow only. It does not create or update
OpenSpec changes.

## Decision

Add a test-owned renderer debug artifact workflow.

Browser-driven e2e tests should be able to write deterministic debug output
under a temporary pytest directory when requested by environment variable. The
debug output should include screenshots and compact HTML/text inspection
snapshots for the render fixture at representative desktop and mobile viewports.

The static course artifact remains the authority surface:

```text
source course
  |
  v
raya build / raya preview
  |
  v
artifact/site/
  |
  +-- test browser opens generated static pages
      |
      v
      optional pytest debug output
```

Debug artifacts are evidence for humans and agents. They are not checked in, not
declared in `manifest.json`, not course source, and not machine authority.

## Non-Goals

- No new public `raya` CLI command or option in this loop.
- No OpenSpec proposal, task file, or spec delta.
- No browser-side MathJax conversion.
- No external renderer, CDN, or network dependency.
- No generated artifacts committed to the repository.
- No pixel-perfect visual snapshot contract.
- No course code, notebook, Docker execution, `uv` execution, package install, or
  cache refresh from preview or build.

## Debug Artifact Contract

When debug capture is enabled for e2e tests, the browser check should write
files under pytest's temporary output area, for example:

```text
tmp/
  renderer-debug/
    desktop-index.png
    desktop-static-path.png
    mobile-index.png
    mobile-static-path.png
    summary.json
```

The exact temporary root can be selected by the test implementation, but it must
be outside source fixtures and generated course artifacts. File names should be
stable enough that failure output can point an agent to the relevant screenshot.

The summary should record:

- page URL,
- viewport name and dimensions,
- screenshot path,
- MathJax container count,
- whether visible raw TeX leakage was found,
- external request list,
- horizontal overflow value.

This is a debugging aid, not a formal artifact schema.

## Fixture Scope

Use `examples/courses/render-fixture` as the representative surface. Strengthen
it only where needed to make math authoring examples explicit:

- page-local `\newcommand` and `\renewcommand`,
- vectors and matrices,
- aligned equations,
- cases,
- derivatives and integrals,
- probability/statistics notation,
- optimization notation,
- escaped dollar signs,
- code blocks beside math.

The fixture remains labeled as fixture material and must not become pedagogy or
architecture canon.

## Browser Checks

Extend the existing Playwright coverage rather than adding a separate tool.
Checks should keep proving:

- generated MathJax output is visible on desktop and mobile,
- raw TeX is not visible in body text when rendering succeeds,
- no external renderer or CDN requests occur,
- local math CSS and fonts resolve from `artifact/site/`,
- layout has no horizontal overflow,
- local preview and static serving use the same generated files.

The new debug path should run only when enabled, so normal local and Docker
verification stay clean and do not write persistent screenshots.

## Documentation

Update role guidance in both languages:

- professors: how to author inline/display math, page-local macros, matrices,
  vectors, and common notation, and where diagnostics appear;
- students: math should already be typeset in static pages and does not require
  a CDN, account, backend, or browser-side MathJax;
- contributors/collaborators: how to enable and inspect browser debug artifacts
  when renderer tests fail;
- agents: how to use the screenshots/summary as evidence while treating
  `manifest.json`, `data/*.json`, and source files as authority.

Keep English and Spanish role pages separate. Technical identifiers, paths,
commands, and environment variables remain in English.

## Verification

Required verification for this loop:

- a focused failing e2e test before implementation,
- focused e2e pass after implementation,
- render fixture build,
- docs validate/build if role documentation changes,
- host archive gate if the final change touches shared docs/tests,
- Docker verification path when practical or a clear note if it is not run.

For substantial code changes, request code review before final completion.
