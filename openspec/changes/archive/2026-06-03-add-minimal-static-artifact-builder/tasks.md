## 1. Workspace And Package Setup

- [x] 1.1 Add `packages/static` as the Glintstone builder package.
- [x] 1.2 Add static package metadata and wire it into the root `uv` workspace.
- [x] 1.3 Add static package README with its boundary and non-goals.
- [x] 1.4 Ensure `uv sync --all-packages --dev` installs the CLI, schema package, and static builder package.

## 2. Builder Data Model And Discovery

- [x] 2.1 Add builder result/report types that reuse CLI-friendly diagnostics.
- [x] 2.2 Load and schema-validate `raya.yaml` before build output is produced.
- [x] 2.3 Discover Markdown content files and parse supported frontmatter.
- [x] 2.4 Derive stable page, quanta, and output path metadata from content paths.
- [x] 2.5 Discover supported official learning-object files and preserve authority/scope/content payloads.
- [x] 2.6 Discover and copy source assets when an assets directory exists.

## 3. Artifact Generation

- [x] 3.1 Replace stale generated output for `site/`, `data/`, `assets/`, and `manifest.json`.
- [x] 3.2 Render Markdown content into escaped, readable static HTML.
- [x] 3.3 Generate static navigation links across rendered pages.
- [x] 3.4 Generate `data/pages.json`.
- [x] 3.5 Generate `data/quanta.json`.
- [x] 3.6 Generate `data/links.json`.
- [x] 3.7 Generate `data/official.json`.
- [x] 3.8 Generate `manifest.json` with schema-valid artifact metadata and index paths.
- [x] 3.9 Record files read and outputs written in build diagnostics.

## 4. CLI Build Command

- [x] 4.1 Add `raya build <course>` to CLI help.
- [x] 4.2 Wire `raya build <course>` to run source validation before artifact generation.
- [x] 4.3 Ensure build success exits zero and reports generated outputs.
- [x] 4.4 Ensure build failures exit nonzero and report source or artifact diagnostics.
- [x] 4.5 Update `raya doctor` next actions to include the build command once appropriate.

## 5. Contract And Integration Tests

- [x] 5.1 Add tests that build the minimal fixture into a temporary artifact directory.
- [x] 5.2 Add tests that generated artifact directories and files exist.
- [x] 5.3 Add tests that generated manifest and data indexes pass schema validators.
- [x] 5.4 Add tests that generated HTML contains escaped readable content and static links.
- [x] 5.5 Add tests that official learning objects export as official study seed data without personal state.
- [x] 5.6 Add tests that source assets are copied when present.
- [x] 5.7 Add tests that stale artifact output is replaced on rebuild.
- [x] 5.8 Add CLI tests for build help, build success, and build failure behavior.

## 6. Documentation And Smoke Workflow

- [x] 6.1 Update README with Docker and local `raya build` commands.
- [x] 6.2 Update AGENTS and CLAUDE guidance with build commands and artifact expectations.
- [x] 6.3 Update the external-course smoke test to validate and build the temporary external course locally and through Docker.
- [x] 6.4 Keep docs explicit that renderer, TypeScript/web UI, backend, identity, and personal study state remain out of scope.

## 7. Verification

- [x] 7.1 Run `UV_PROJECT_ENVIRONMENT=.venv-local uv sync --python 3.10 --all-packages --dev`.
- [x] 7.2 Run local `raya --help`, `raya doctor`, `raya validate examples/courses/minimal`, `raya build examples/courses/minimal`, and `pytest -q`.
- [x] 7.3 Run Docker Compose `raya --help`, `raya doctor`, `raya validate examples/courses/minimal`, `raya build examples/courses/minimal`, and `pytest -q`.
- [x] 7.4 Run `./scripts/smoke-test.sh`.
- [x] 7.5 Run `openspec validate add-minimal-static-artifact-builder --strict`.
- [x] 7.6 Run `openspec validate --specs --strict`.
