## 1. Course Init Helper

- [x] 1.1 Add course init helper in `packages/cli`.
- [x] 1.2 Generate `raya.yaml` with course ID, title, description, language, content directory, and artifact directory.
- [x] 1.3 Generate minimal `content/00_index.md` with explicit replaceable scaffold language and stable quantum metadata.
- [x] 1.4 Create `assets/`, `official/cards/`, `official/quizzes/`, and `official/prompts/`.
- [x] 1.5 Refuse to initialize non-empty target directories.
- [x] 1.6 Report outputs written and actionable diagnostics.

## 2. CLI Command

- [x] 2.1 Add nested `raya course init <path>` parsing to CLI help.
- [x] 2.2 Add optional metadata flags for course ID, title, description, and language.
- [x] 2.3 Wire the command to the init helper.
- [x] 2.4 Ensure init success exits zero and reports generated files/directories.
- [x] 2.5 Ensure init failure exits nonzero.
- [x] 2.6 Update `raya doctor` next actions for unknown context to mention course init.

## 3. Tests

- [x] 3.1 Add direct tests that course init creates the expected source tree.
- [x] 3.2 Add tests that initialized courses validate successfully.
- [x] 3.3 Add tests that initialized courses build and inspect successfully.
- [x] 3.4 Add tests that non-empty target directories are refused.
- [x] 3.5 Add CLI tests for course help, init success, init validation/build/inspect compatibility, and init failure.

## 4. Documentation And Smoke Workflow

- [x] 4.1 Update README with Docker and local `raya course init` examples.
- [x] 4.2 Update AGENTS and CLAUDE guidance with course init behavior and overwrite safety.
- [x] 4.3 Update the external smoke test to initialize a separate temporary course and run validate/build/inspect on it.
- [x] 4.4 Keep docs explicit that generated starter content is replaceable scaffold.

## 5. Verification

- [x] 5.1 Run local `raya --help`, `raya course --help`, init, validate, build, inspect, and `pytest -q`.
- [x] 5.2 Run Docker Compose `raya --help`, `raya course --help`, init, validate, build, inspect, and `pytest -q`.
- [x] 5.3 Run `./scripts/smoke-test.sh`.
- [x] 5.4 Run `openspec validate add-course-init-command --strict`.
- [x] 5.5 Run `openspec validate --specs --strict`.
