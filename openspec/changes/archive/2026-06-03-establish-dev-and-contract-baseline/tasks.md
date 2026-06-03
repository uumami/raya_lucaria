## 1. Development Workflow

- [x] 1.1 Add root Python/uv project metadata for the baseline workspace and choose the baseline Python version.
- [x] 1.2 Add a root Dockerfile or development image definition that installs `uv` and can run the CLI/test workflow.
- [x] 1.3 Add root `docker-compose.yaml` service definitions for running `raya` commands and tests from the repository root.
- [x] 1.4 Document the Docker Compose reference workflow and the local `uv` escape hatch in root guidance.
- [x] 1.5 Add baseline command documentation for foundation checks, dependency sync, CLI help, CLI doctor, CLI validate, and tests.
- [x] 1.6 Add an external-course smoke-test script that copies the minimal fixture into a temporary directory, validates it locally, validates it through Docker with an explicit mount, and cleans up afterward.

## 2. Package Scaffolding

- [x] 2.1 Create `packages/schema` for portable contract schemas and Python validation helpers.
- [x] 2.2 Create `packages/cli` for the Python `raya` command entrypoint.
- [x] 2.3 Wire package metadata so `uv` can install and run the CLI in Docker and locally.
- [x] 2.4 Keep package names plain while documenting their domain mapping to Glintstone and contract surfaces.

## 3. Contract Schemas

- [x] 3.1 Add the initial `raya.yaml` schema with required course identity, metadata, content directory, and artifact output directory fields.
- [x] 3.2 Add artifact `manifest.json` schema with artifact version, course ID, course version/content hash, timestamp, source schema version, static site root, and data index locations.
- [x] 3.3 Add baseline page/quanta index schema definitions.
- [x] 3.4 Add baseline official learning-object schema definitions for cards, quizzes, prompts, examples, assignments, exams, projects, and tasks.
- [x] 3.5 Add official learning-object authority and learning-quantum scope fields to the relevant schemas.

## 4. Validation Helpers

- [x] 4.1 Implement source course discovery for explicit course paths.
- [x] 4.2 Implement `raya.yaml` loading and schema validation.
- [x] 4.3 Implement content directory existence and readable Markdown/frontmatter checks.
- [x] 4.4 Implement path-derived learning-quanta identity and duplicate stable ID checks.
- [x] 4.5 Implement official learning-object validation, duplicate object ID checks, and invalid/unscoped object diagnostics.
- [x] 4.6 Implement artifact manifest and generated-index schema validation helpers.
- [x] 4.7 Ensure validation diagnostics identify concrete files, fields, and next actions.

## 5. CLI Baseline

- [x] 5.1 Implement `raya --help` with discoverable baseline commands.
- [x] 5.2 Implement `raya doctor` with framework/course/installation/unknown context detection.
- [x] 5.3 Implement `raya validate <course>` using the schema and validation helpers.
- [x] 5.4 Ensure CLI commands return zero on success and nonzero on validation or setup failures.
- [x] 5.5 Ensure CLI diagnostics report detected context, files read, and outputs written when applicable.
- [x] 5.6 Ensure validation does not depend on hidden global state.

## 6. Minimal Fixture Course

- [x] 6.1 Add `examples/courses/minimal/raya.yaml`.
- [x] 6.2 Add minimal `content/` Markdown files with the smallest useful course structure.
- [x] 6.3 Add minimal `official/` learning-object fixtures for cards, quizzes, and prompts.
- [x] 6.4 Label fixture examples as fixture data rather than required pedagogy or architecture.
- [x] 6.5 Ensure `raya validate examples/courses/minimal` succeeds.

## 7. Contract Tests

- [x] 7.1 Add tests for valid and invalid `raya.yaml` files.
- [x] 7.2 Add tests for missing content directories and unreadable frontmatter.
- [x] 7.3 Add tests for duplicate quanta IDs and duplicate official object IDs.
- [x] 7.4 Add tests for official learning-object authority labels and scope requirements.
- [x] 7.5 Add tests for artifact manifest schema validation.
- [x] 7.6 Add tests for CLI help, doctor, validate success, and validate failure exit behavior.
- [x] 7.7 Add Docker Compose test execution to verify the reference workflow.
- [x] 7.8 Add local `uv` test execution with `UV_PROJECT_ENVIRONMENT=.venv-local` to verify the non-Docker escape hatch.

## 8. Documentation And Guardrails

- [x] 8.1 Update root README with Docker-first and local `uv` workflows.
- [x] 8.2 Update AGENTS/CLAUDE guidance with the implementation commands once they exist.
- [x] 8.3 Document that renderer, TypeScript/web UI, backend, and identity choices remain out of scope for this change.
- [x] 8.4 Document that old renderer assumptions, old `glintstone.yaml`, old `clase/`, and old generated JSON shapes remain historical.
- [x] 8.5 Document the external-course smoke-test command in root and agent guidance.

## 9. Verification

- [x] 9.1 Run `find docs/foundation -maxdepth 1 -type f | sort`.
- [x] 9.2 Run `rg -n "Eleventy|Tailwind|Pagefind" docs/foundation -g '!14_domain_language.md'`.
- [x] 9.3 Run Docker Compose CLI help, doctor, validate, and tests.
- [x] 9.4 Run local `uv` CLI help, doctor, validate, and tests with `UV_PROJECT_ENVIRONMENT=.venv-local`.
- [x] 9.5 Run `openspec validate establish-dev-and-contract-baseline --strict`.
- [x] 9.6 Run `./scripts/smoke-test.sh`.
