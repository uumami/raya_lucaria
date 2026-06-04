## 1. Configuration And Source Resolution

- [x] 1.1 Add `source` to the course configuration schema as the canonical authored source root.
- [x] 1.2 Implement source-root resolution from `source` only.
- [x] 1.3 Update validation diagnostics for missing source directories and unsupported `content` / root `assets` fields.
- [x] 1.4 Update internal naming where needed so implementation code distinguishes authored source roots from rendered page content.

## 2. Ordered Source Tree And Support Paths

- [x] 2.1 Extend ordered source scanning to run under the resolved authored source root.
- [x] 2.2 Treat `_official/`, `_assets/`, `_drafts/`, `drafts/`, `_partials/`, and other leading-underscore support paths as private and unrendered.
- [x] 2.3 Enforce that a learning quantum with `_official/` or `_assets/` support material uses a directory page with `0_index.md`.
- [x] 2.4 Preserve valid rendered file pages such as `1_topic.md` when they do not own child support directories.

## 3. Official Learning Object Colocation

- [x] 3.1 Discover official object families under source-root and quantum-colocated `_official/<family>/` directories.
- [x] 3.2 Validate ordered filenames for colocated official object files and fail unordered or duplicate normalized order values within a family.
- [x] 3.3 Infer `scope.quantum` for colocated official objects from the nearest rendered directory landing page when scope is omitted.
- [x] 3.4 Require explicit colocated scopes to match the nearest quantum and require explicit scope for source-root `_official/`.
- [x] 3.5 Detect duplicate official object IDs across source-root and quantum-colocated official-object locations.
- [x] 3.6 Export official objects with stable IDs, authority labels, source paths, object payloads, resolved scope, and study counts without exposing filename prefixes as identity.

## 4. Colocated Assets

- [x] 4.1 Validate Markdown asset links against the page's own `_assets/` and ancestor `_assets/` locations.
- [x] 4.2 Reject links from rendered pages into `_official/`, `_drafts/`, `_partials/`, or other non-asset support paths.
- [x] 4.3 Copy referenced colocated assets into artifact-level assets and browser-facing static assets using collision-safe deployment-neutral paths.
- [x] 4.4 Reject root authored `assets` configuration and keep generated artifact `assets/` output.

## 5. Builder, Course Init, And Fixtures

- [x] 5.1 Update the minimal static builder to build from the resolved authored source root and keep support directories out of rendered navigation, local indexes, and master indexes.
- [x] 5.2 Update `data/official.json`, `indices.json`, navigation data, and manifest output to include colocated official objects and source paths where required.
- [x] 5.3 Update `raya course init` to scaffold `raya.yaml` with `source: course`, `course/0_index.md`, private support directories, and generated `artifact/` output.
- [x] 5.4 Migrate canonical fixtures and examples to `course/` and remove root-authored source alternatives.
- [x] 5.5 Add invalid fixtures for unsupported source fields, missing source root, unordered official object files, scope mismatches, duplicate official IDs, invalid support links, and missing colocated assets.

## 6. Documentation And Guidance

- [x] 6.1 Update `docs/foundation/05_course_contract.md`, `docs/foundation/15_system_overview.md`, `docs/foundation/16_documentation_surfaces.md`, and related foundation references for the unified source tree.
- [x] 6.2 Update `openspec/config.yaml` guidance so future changes preserve `source: course`, ordered quanta, colocated `_official/`, colocated `_assets/`, and support-directory privacy.
- [x] 6.3 Update separate English and Spanish role guide directories for contributors/collaborators, professors, students, and agents.
- [x] 6.4 Update rendered documentation fixtures and live documentation examples so they demonstrate the canonical unified source tree without mixing class/course examples into documentation source.

## 7. Verification

- [x] 7.1 Add or update contract tests for configuration resolution, ordered source scanning, support path privacy, official object colocation, scope inference, study counts, and colocated asset validation.
- [x] 7.2 Add or update static read-path e2e tests that build a representative unified source fixture and verify rendered pages, generated indexes, official export data, and colocated asset URLs.
- [x] 7.3 Run host verification with the relevant `uv` or direct Python test commands for schema, CLI, builder, docs, and e2e coverage.
- [x] 7.4 Run the Docker Compose reference workflow for the same representative validation and e2e path or document any Docker workflow gap.
- [x] 7.5 Run `openspec validate unify-ordered-course-source-tree --strict` and the current spec hygiene checks before implementation is considered complete.
