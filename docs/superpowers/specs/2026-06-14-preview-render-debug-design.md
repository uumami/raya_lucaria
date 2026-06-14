# Preview Render Debug Design

Date: 2026-06-14
Status: approved direction, ready for implementation planning

## Context

Glintstone already pre-renders accepted MathJax math at build time, copies local
math support files under `artifact/site/_raya/render/math/`, and has browser
tests that can optionally capture renderer debug screenshots and `summary.json`
when `RAYA_RENDER_DEBUG_DIR` is set. That test-owned workflow proved useful, but
it is still hidden behind an internal pytest invocation.

The next quality pillar is to make the same visual debugging evidence available
through the local preview workflow that contributors and coding agents already
use. The command should expose a supported diagnostic path without changing
course source truth, artifact authority, or the no-browser-side-MathJax
contract.

This loop uses the Superpowers workflow only. It does not create or update an
OpenSpec change.

## Decision

Add a narrow renderer debug mode to `raya preview`:

```bash
raya preview <course> --render-debug <output-dir>
```

When the option is present, preview should validate and build the explicit
course, serve the generated `artifact/site/` files through the same local static
server used by normal preview, open representative pages in a Chromium-compatible
browser, and write screenshots plus a compact `summary.json` to the requested
output directory.

The debug output is evidence for humans and agents. It is not course source, not
declared artifact data, not machine authority, and not required for ordinary
preview. The command must continue to use the built static site as the source of
browser truth.

```text
source course
  |
  v
raya preview --render-debug
  |
  +-- validate
  +-- build
  +-- serve artifact/site/
  +-- browser inspects generated static pages
      |
      v
      external debug output directory
```

## Command Contract

The command shape is:

```bash
raya preview examples/courses/render-fixture --render-debug /tmp/raya-render-debug
```

Behavior:

- validate and build the course before browser inspection,
- serve `artifact/site/` with deployment-neutral local paths,
- capture desktop and mobile screenshots for the course root page,
- capture the nested `static-path/` page when it exists,
- write a `summary.json` array of capture records,
- print the student entrypoint, inspection URL when present, and render debug
  output directory,
- stop the preview server before the command exits.

The first implementation should keep the page set intentionally small:

| Page | Required when |
| --- | --- |
| `index` | always |
| `static-path` | when `artifact/site/static-path/index.html` exists |

The first implementation should use two viewports:

| Viewport | Dimensions |
| --- | --- |
| `desktop` | `1280x900` |
| `mobile` | `390x844` |

## Debug Output

The output directory should be created if it does not exist. Known debug files
from previous runs should be removed before new captures are written so agents
do not inspect stale screenshots.

Expected file names:

```text
<output-dir>/
  desktop-index.png
  mobile-index.png
  desktop-static-path.png      # when static-path exists
  mobile-static-path.png       # when static-path exists
  summary.json
```

Each `summary.json` record should include:

- page name,
- page URL,
- viewport name and dimensions,
- screenshot path,
- MathJax container count,
- visible raw TeX leakage flag,
- representative visible raw TeX markers,
- external request URLs observed during page load,
- horizontal overflow value.

This is a debugging aid, not a formal artifact schema. It should be stable
enough for agents to compare current evidence, but it should not become a
versioned course artifact contract.

## Diagnostics And Failure Behavior

If no Chromium-compatible browser is available, the command should fail with an
actionable diagnostic that names the missing requirement and suggests the
reference Docker path or `RAYA_TEST_BROWSER=/path/to/browser`.

If validation or build fails, render debug capture must not run. The command
should report the existing validation/build diagnostics.

If browser inspection finds visible raw TeX, external renderer/CDN requests, or
horizontal overflow, the summary should record the evidence. The command may
return a nonzero status for publication-blocking rendering failures once the
checks are implemented. The first implementation should at least fail on raw TeX
leakage and external requests because those violate the accepted rendering
baseline.

## Non-Goals

- No browser-side MathJax conversion.
- No external renderer, CDN, or network dependency.
- No course code, notebook, Docker execution, `uv` execution, package install,
  runtime profile use, or cache refresh.
- No generated debug files committed to the repository.
- No new top-level `raya render-debug` command in this loop.
- No pixel-perfect visual snapshot contract.
- No broad page crawler or visual diff engine.
- No promotion of screenshots or `summary.json` into `manifest.json` or
  `artifact/data/*.json`.

## Documentation

Update role guidance in both languages where the workflow matters:

- contributors/collaborators: how to run `raya preview --render-debug`, inspect
  screenshots, and use `summary.json` when renderer tests fail;
- agents: how to treat debug output as evidence while keeping source files,
  `manifest.json`, and `data/*.json` as authority.

Professors and students do not need new role guidance unless implementation
changes the authoring or reading contract. Technical identifiers, paths,
commands, and environment variables remain in English in both language trees.

## Verification

Required verification for this loop:

- a failing CLI or preview test before implementation,
- focused pass for the new debug preview behavior,
- existing browser math/static-read-path checks still pass,
- render fixture build,
- docs validate/build if role documentation changes,
- host archive gate before completion,
- Docker verification path when practical or an explicit note if not run,
- code review before final completion because this changes the public CLI path.
