# Render Debug Parity Gate Design

## Goal

Add a focused renderer parity gate that proves the accepted render fixture works through the same generated static files used by local preview and static deployment. The gate should be easy for contributors and agents to run directly, and it should also run through the existing host and Docker verification paths.

## Context

The current renderer baseline already pre-renders accepted MathJax during build, copies local MathJax CSS and fonts under `artifact/site/_raya/render/math/`, and exposes `raya preview <course> --render-debug <dir>` for browser screenshots and `summary.json` inspection. The remaining risk is drift between normal fixture builds, browser inspection, and the canonical host/Docker gates.

This loop should not add a new public CLI command. The current CLI surface is sufficient; the missing piece is a named verification recipe around it.

## Approach

Create `scripts/check-render-debug.sh` as the focused renderer parity gate.

The script will:

- use `UV_PROJECT_ENVIRONMENT=.venv-local` by default, matching `scripts/check-python.sh`;
- create a temporary debug output directory;
- run `uv run raya preview examples/courses/render-fixture --port 0 --render-debug <temp-dir>`;
- inspect the generated `summary.json`;
- verify expected desktop and mobile captures for the render fixture pages;
- verify screenshot files exist and are non-empty;
- fail on visible raw TeX, external requests, or horizontal overflow;
- inspect generated HTML under `examples/courses/render-fixture/artifact/site/` to ensure the static site does not load browser-side MathJax runtime scripts or external renderer/CDN resources;
- delete the temporary debug directory on exit unless the caller sets a keep-debug environment variable.

Wire `scripts/check-python.sh` to call this script after representative fixture build/inspect checks have made renderer dependencies and artifacts available. Because `scripts/check-docker.sh` runs `scripts/check-python.sh` inside the reference container, Docker parity is covered by the same path.

## Data Flow

```text
examples/courses/render-fixture
        |
        v
raya preview --render-debug
        |
        v
artifact/site/ served locally
        |
        v
temporary screenshots + summary.json
        |
        v
check-render-debug assertions
```

The debug output remains local evidence. It is not committed, not copied into the course artifact, and not treated as source or artifact authority.

## Failure Behavior

The gate should fail with direct messages that name the failed invariant and the relevant path:

- missing or malformed `summary.json`;
- missing expected capture record;
- missing or empty screenshot;
- visible raw TeX in any capture;
- external requests in any capture;
- horizontal overflow in any capture;
- browser-side MathJax runtime script or external renderer resource in generated HTML.

Browser setup failures should preserve the existing `raya preview --render-debug` diagnostics, which already point users toward the reference Docker workflow or `RAYA_TEST_BROWSER`.

## Tests

Use test-driven development:

- contract tests prove `scripts/check-render-debug.sh` exists, is documented, and is invoked by `scripts/check-python.sh`;
- focused script tests run the gate and verify it succeeds against `examples/courses/render-fixture`;
- negative tests use temporary copied fixture/debug data where practical to prove the summary inspector fails for raw TeX, external requests, missing screenshots, overflow, or browser-side MathJax runtime references.

Implementation may keep summary inspection in the shell script if it stays small, but a Python helper under `tests` or `packages/cli` is acceptable if that keeps parsing and diagnostics clearer. If a helper becomes reusable runtime behavior, it belongs under `packages/cli`; if it is only a gate implementation detail, it should stay script-local.

## Documentation

Update role docs in both languages:

- contributors/colaboradores: add the focused `scripts/check-render-debug.sh` command as the renderer parity gate before full host/Docker checks;
- agents/agentes: describe when to run the focused gate versus `raya preview --render-debug` directly;
- preserve the distinction between debug evidence and authority surfaces.

Do not update professor or student docs in this loop unless the implementation changes their authoring or reading workflow.

## Out Of Scope

- New public `raya` subcommands.
- Persisting screenshots or summaries in course artifacts.
- Browser-side MathJax conversion.
- External renderer or CDN requests.
- New math authoring examples beyond any minimal fixture content needed for parity assertions.
- OpenSpec changes.

## Acceptance Criteria

- `scripts/check-render-debug.sh` passes locally with `UV_PROJECT_ENVIRONMENT=.venv-local`.
- `scripts/check-python.sh` runs the render-debug parity gate.
- `scripts/check-docker.sh` covers the same gate through the reference container.
- The gate fails on raw visible TeX, external requests, missing screenshots, horizontal overflow, and browser-side MathJax runtime dependencies.
- Contributor and agent role docs in English and Spanish name the focused command and its relationship to `raya preview --render-debug`.
- `./scripts/check.sh` and `./scripts/check-docker.sh` pass before merging.

## Spec Self-Review

- Placeholder scan: no placeholders or TBDs remain.
- Consistency check: the design uses the existing preview render-debug CLI rather than adding a new public command.
- Scope check: the loop is limited to one script, tests, check wiring, and role docs.
- Ambiguity check: debug artifacts remain temporary evidence and are not artifact authority.
