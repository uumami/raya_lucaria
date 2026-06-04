## 1. Source Model And Validation

- [x] 1.1 Implement ordered-entry parsing for numeric prefixes, padded equivalents, appendix prefixes, natural sorting, duplicate normalized order detection, and mixed main prefix-style diagnostics.
- [x] 1.2 Implement rendered/private/draft source classification for ordered Markdown files, section directories, leading-underscore paths, `_partials/`, `_drafts/`, `drafts/`, and unordered published files.
- [x] 1.3 Enforce rendered directory landing pages through normalized zero index files and use landing-page metadata as the directory quantum source.
- [x] 1.4 Extend Markdown frontmatter parsing and validation for `id`, `title`, `nav_title`, `summary`, `status`, `estimated_time`, `tags`, `prerequisites`, and `aliases`.
- [x] 1.5 Add course-wide stable ID and alias registry validation, including duplicate ID, duplicate alias, and published-page missing-ID failures.
- [x] 1.6 Add optional `raya.yaml` hierarchy label parsing with conservative defaults when labels are absent.
- [x] 1.7 Add `raya:` stable link validation and non-failing guidance for fragile Markdown path links that target rendered pages with stable IDs.

## 2. Fixtures And Course Init

- [x] 2.1 Update course init output to create the canonical ordered root scaffold with `content/0_index.md`, minimal metadata, replaceable prose, and existing `assets/` and `official/` directories.
- [x] 2.2 Update the minimal fixture only as much as needed to satisfy the ordered source and metadata contract without turning fixture content into canonical pedagogy.
- [x] 2.3 Add a representative ordered-content fixture with main sections, nested pages, an appendix, manual index prose, `<!-- raya:index -->`, summaries, aliases, prerequisites, and official study objects.
- [x] 2.4 Add negative fixtures for duplicate normalized order, mixed prefix widths, missing section landing pages, unordered published files, duplicate stable IDs, duplicate aliases, duplicate clean slugs, and broken `raya:` links.

## 3. Artifact Data And Inspection

- [x] 3.1 Add schema and generation support for `data/navigation.json` with resolved order, labels, URLs, parent/child relationships, breadcrumbs, previous links, and next links.
- [x] 3.2 Add schema and generation support for `data/indices.json` with local indexes, master index entries, appendix entries, summaries, and official study-object counts.
- [x] 3.3 Update `manifest.json` schema and generation to declare navigation and generated-index data locations.
- [x] 3.4 Extend `pages.json`, `quanta.json`, and `links.json` generation to preserve stable IDs, aliases, metadata, hierarchy labels, and resolved `raya:` links.
- [x] 3.5 Update artifact inspection to validate manifest-declared navigation and generated-index data in copied artifacts without requiring source files.

## 4. Static Builder Rendering

- [x] 4.1 Render clean static URLs from stripped ordered path segments while keeping diagnostics tied to original source paths.
- [x] 4.2 Render breadcrumbs, parent/child navigation, previous/next links, hierarchy labels, and appendix labels from resolved navigation data.
- [x] 4.3 Render generated local index sections at `<!-- raya:index -->` markers and use the documented append fallback when markers are absent.
- [x] 4.4 Render the root master index from resolved main sections and appendices.
- [x] 4.5 Render generated study counts from official learning objects without personal review state.
- [x] 4.6 Resolve validated `raya:` links and aliases to deployment-neutral relative static URLs.

## 5. Documentation And Foundation

- [x] 5.1 Update `docs/foundation/05_course_contract.md`, `docs/foundation/06_artifact_contract.md`, and `docs/foundation/15_system_overview.md` with ordered source, stable ID, generated index, and artifact data rules.
- [x] 5.2 Update `openspec/config.yaml` so future proposals preserve convention-first ordering, generated artifact indexes, stable IDs, and role-documentation expectations.
- [x] 5.3 Update English and Spanish professor guides with the source-tree authoring model, metadata examples, generated index behavior, and stable link guidance.
- [x] 5.4 Update English and Spanish student guides with the rendered navigation model, generated indexes, summaries, prerequisites, and study-count expectations.
- [x] 5.5 Update English and Spanish contributor/collaborator and agent guides with validation rules, artifact data surfaces, and source-versus-rendered authority boundaries.

## 6. Tests And Verification

- [x] 6.1 Add contract tests for ordered-entry parsing, rendered/private classification, metadata parsing, hierarchy labels, duplicate diagnostics, and stable ID/alias validation.
- [x] 6.2 Add source-link tests for valid `raya:` links, valid alias links, broken stable references, normal Markdown links, and fragile-link guidance.
- [x] 6.3 Add artifact schema tests for `manifest.json`, `navigation.json`, `indices.json`, `pages.json`, `quanta.json`, and `links.json`.
- [x] 6.4 Add static-read-path e2e tests that build the representative ordered-content fixture and assert generated local indexes, master index, clean URLs, breadcrumbs, previous/next links, appendix rendering, study counts, and `raya:` links.
- [x] 6.5 Run `openspec validate define-content-order-index-baseline --strict` and `openspec validate --specs --strict`.
- [x] 6.6 Run local tests with `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q`.
- [x] 6.7 Run Docker tests with `docker compose run --rm dev uv run pytest -q`.
- [x] 6.8 Run `git diff --check` and verify current specs do not contain `Purpose: TBD` placeholders before archive.

## 7. Live Documentation Render Surface

- [x] 7.1 Add a renderable `docs/raya.yaml` docs course and ordered `docs/render-content/` source that covers current foundation and role documentation.
- [x] 7.2 Add compact frontmatter metadata to current foundation and role documentation pages so they can feed navigation, indexes, stable links, and artifact data.
- [x] 7.3 Update source-link validation so fenced Markdown examples and symlink-backed render sources do not produce false broken-link diagnostics.
- [x] 7.4 Add contract and e2e tests that build the live `docs/` course and serve current foundation, English role, and Spanish role pages through the static read path.
- [x] 7.5 Run focused validation for live docs rendering and keep generated `docs/artifact/` output ignored and out of source control.
