## Context

The foundation requires a static course path that remains useful without accounts, dynamic services, provider-specific deployment, or JavaScript-heavy behavior. The current baseline already builds `artifact/site/`, `manifest.json`, `data/*.json`, and artifact-level `assets/`. It also validates local Markdown links and local asset references before build.

The remaining gap is browser-facing resource resolution. Page-to-page links are rewritten to relative HTML paths, but local asset links are currently left in the source shape. That can work in some local layouts, but it is not a stable artifact contract for static hosting, copied artifacts, subdirectory deployments, or future renderer capabilities such as math support.

This change belongs to Glintstone (`packages/static`) and artifact contracts in `packages/schema`. It does not introduce a web app, backend service, provider adapter, or dynamic study state.

## Goals / Non-Goals

**Goals:**

- Make `artifact/site/` self-contained for browser-facing local assets.
- Rewrite rendered local asset URLs to relative paths that target `site/_raya/assets/`.
- Preserve artifact-level `assets/` and `data/` as machine-readable and installation-readable artifact surfaces.
- Keep page-to-page content links relative and deployment-neutral.
- Add a representative render/e2e fixture course that exercises framework overview content, nested pages, local assets, and link examples.
- Add contract and e2e/static-read-path tests for nested pages, asset copying, artifact inspection, and static read-path portability.
- Establish `site/_raya/` as the reserved browser resource namespace for future Glintstone renderer assets.

**Non-Goals:**

- No math rendering yet.
- No graph UI, backlinks UI, wikilinks, or heading-anchor validation.
- No external URL checking or link crawling.
- No JavaScript framework, CSS framework, CDN, backend, identity, or deployment provider.
- No changes to official learning-object authority or personal study state.
- The representative e2e fixture is not official pedagogy, architecture truth, or product documentation; it is test content derived from the foundation for renderer coverage.

## Decisions

### Decision: use `site/_raya/` for browser-facing generated resources

Rendered browser assets SHALL live under `artifact/site/_raya/assets/`.

Rationale: `site/` is the static read path. If `site/` is served directly, browser resources must be reachable without depending on sibling directories such as `../assets`. The `_raya/` prefix also reserves a clear namespace for framework-generated resources without colliding with course content paths.

Alternative considered: keep browser assets only under artifact-level `assets/`. That keeps the tree smaller but makes `site/` dependent on a sibling path and weakens local file and static-host portability.

### Decision: preserve artifact-level `assets/`

The builder SHALL keep copying source assets to artifact-level `assets/` for the existing artifact contract while also copying browser-facing assets to `site/_raya/assets/`.

Rationale: `manifest.json`, artifact inspection, and future dynamic installations need stable artifact-root surfaces. Browser-facing static resources are a serving concern; artifact-level assets are an artifact data concern.

Alternative considered: move all assets into `site/_raya/assets/` and change manifest `assets`. That would be a sharper break and is not needed for this minimal contract.

### Decision: rewrite only validated local asset references

The renderer SHALL rewrite links classified as local asset references into relative URLs pointing at `site/_raya/assets/`. External URLs, `mailto:`, `tel:`, fragment-only links, and `.md` content links keep their existing handling.

Rationale: source validation already guarantees local asset existence. Reusing the same classification avoids rendering unvalidated paths and keeps this change scoped.

Alternative considered: rewrite all non-content links. That would blur local assets with external links and could damage valid URLs.

### Decision: keep URLs relative, never deployment-root based

Generated URLs SHALL be relative from each generated HTML page to the target generated page or browser resource.

Rationale: relative paths work when opened from local files, served from a subdirectory, hosted at a root domain, or served by a dynamic installation. Absolute `/...` paths assume a deployment root and should not be part of the baseline.

Alternative considered: add a configurable base URL. That can come later as deployment metadata, but it should not be required for the static baseline.

### Decision: reserve future renderer resources without implementing them

The design reserves `site/_raya/` as the browser resource namespace for future public browser data, math renderer assets, syntax-highlighting assets, and optional interactive components. This proposal implements only local asset copying and URL rewriting.

Rationale: math and richer components should not force another resource layout migration later, but they need their own proposal because they affect parsing, accessibility, and possibly dependencies.

### Decision: add a representative render/e2e fixture separate from the minimal fixture

This change SHALL add or define a fixture course/page for static rendering e2e tests. The fixture should include a concise Raya Lucaria framework overview, nested content, a local asset, a content link, a local asset link, and ignored link examples.

Rationale: the minimal fixture is intentionally tiny and should stay that way. A richer render fixture gives Glintstone stable content to build and serve without turning examples into pedagogy or architecture truth.

Alternative considered: keep adding content to `examples/courses/minimal`. That would weaken the "minimal fixture" boundary and make future tests harder to interpret.

### Decision: e2e tests should exercise the generated static read path

The e2e path SHOULD build the representative fixture, serve or open `artifact/site/`, and assert that generated pages and local assets are reachable through browser/static read-path URLs. If a browser runner is added, it should run through the Docker reference workflow and local `uv` workflow.

Rationale: unit tests can prove path strings, but they do not prove the generated static read path works as a user-facing site. E2E coverage protects local deployment, static hosting, and future renderer changes.

Alternative considered: rely only on generated HTML string assertions. Those remain useful contract tests but are not enough for deployment portability.

## Risks / Trade-offs

- [Duplicate copied assets] Copying to both `assets/` and `site/_raya/assets/` duplicates files. Mitigation: accept the small baseline cost now; future specs can consolidate if artifact-level and browser-facing asset contracts are unified.
- [Simple Markdown parser limitations] Current Markdown extraction is regex-based and may miss advanced syntax. Mitigation: keep tests scoped to current supported Markdown and propose a render-model/parser contract before richer Markdown or math.
- [Namespace collision] A course page path could theoretically use `_raya/`. Mitigation: reserve `site/_raya/` as generated output, not source truth; source content still lives under `content/`.
- [Future manifest evolution] Browser-facing resources may later need an index. Mitigation: keep this proposal layout-focused and leave `assets.json` or public browser data indexes to a later proposal.
- [E2E dependency weight] A browser runner can add setup cost. Mitigation: keep the fixture small, run it in Docker and local workflows, and document the exact command; if browser tooling proves too heavy, update this design before substituting a lighter static-server e2e path.
- [Fixture content becoming canonical] A framework overview fixture could be mistaken for foundation truth. Mitigation: label the fixture explicitly and keep `docs/foundation/` as the authority surface.

## Migration Plan

1. Add the representative render/e2e fixture and label it as fixture material.
2. Add focused contract tests that describe the expected `site/_raya/assets/` layout and relative href behavior.
3. Add e2e/static-read-path tests that build and exercise the generated fixture site.
4. Update the static builder to copy local source assets into `site/_raya/assets/` in addition to artifact-level `assets/`.
5. Update Markdown rendering so local asset links become page-relative URLs to `site/_raya/assets/`.
6. Keep existing manifest and artifact inspection contracts passing.
7. Run local and Docker CLI/test/smoke/e2e verification.

Rollback is straightforward during reset: remove the new copy target and href rewriting while preserving existing artifact-level asset copying.
