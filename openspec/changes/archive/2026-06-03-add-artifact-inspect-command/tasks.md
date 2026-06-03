## 1. Artifact Inspection Helper

- [x] 1.1 Add artifact-level inspection helper in `packages/schema`.
- [x] 1.2 Validate artifact root, `manifest.json`, `site/`, `data/`, and `assets/` paths.
- [x] 1.3 Load and validate `manifest.json`.
- [x] 1.4 Follow manifest-declared data index paths and validate pages, quanta, links, and official indexes.
- [x] 1.5 Keep inspection read-only and report files read without outputs written.
- [x] 1.6 Export the inspection helper from `raya_schema`.

## 2. CLI Command

- [x] 2.1 Add nested `raya artifacts inspect <artifact>` parsing to CLI help.
- [x] 2.2 Wire the command to artifact inspection.
- [x] 2.3 Ensure successful inspection exits zero and reports files read.
- [x] 2.4 Ensure failed inspection exits nonzero and reports actionable diagnostics.
- [x] 2.5 Update `raya doctor` next actions to mention artifact inspection after build.

## 3. Tests

- [x] 3.1 Add direct tests that inspect a built temporary artifact successfully.
- [x] 3.2 Add tests that inspection fails for missing required artifact paths.
- [x] 3.3 Add tests that inspection fails for missing manifest-declared data indexes.
- [x] 3.4 Add tests that inspection is read-only and reports no outputs written.
- [x] 3.5 Add CLI tests for artifacts help, inspect success, and inspect failure.

## 4. Documentation And Smoke Workflow

- [x] 4.1 Update README with Docker and local artifact inspect commands.
- [x] 4.2 Update AGENTS and CLAUDE guidance with artifact inspect commands.
- [x] 4.3 Update the external-course smoke test to inspect the temporary external artifact locally and through Docker.
- [x] 4.4 Keep docs explicit that inspection is manifest-centered and read-only.

## 5. Verification

- [x] 5.1 Run local `raya --help`, `raya artifacts --help`, build, inspect, and `pytest -q`.
- [x] 5.2 Run Docker Compose `raya --help`, `raya artifacts --help`, build, inspect, and `pytest -q`.
- [x] 5.3 Run `./scripts/smoke-test.sh`.
- [x] 5.4 Run `openspec validate add-artifact-inspect-command --strict`.
- [x] 5.5 Run `openspec validate --specs --strict`.
