## 1. Contract Tests

- [x] 1.1 Add or define a representative render fixture course/page with concise Raya Lucaria framework overview content, nested content, local assets, and explicit fixture labels.
- [x] 1.2 Add builder tests that a root page local asset link is rendered as a relative URL to `_raya/assets/`.
- [x] 1.3 Add builder tests that a nested page local asset link is rendered as a relative URL to `../_raya/assets/` or the correct nesting depth.
- [x] 1.4 Add builder tests that referenced source assets are copied under `site/_raya/assets/` with source asset relative paths preserved.
- [x] 1.5 Add builder tests that artifact-level `assets/` copying still works and artifact inspection still passes.
- [x] 1.6 Add builder tests that external URLs, `mailto:`, `tel:`, and fragment-only links are not rewritten as local assets.
- [x] 1.7 Add builder tests that rendered page and asset URLs avoid absolute deployment roots, configured hosts, backend routes, and CDNs.
- [x] 1.8 Add e2e/static-read-path tests that build the representative fixture and verify generated pages and local assets are reachable from `artifact/site/`.

## 2. Static Builder Resource Resolution

- [x] 2.1 Add constants or helpers for the browser resource namespace `site/_raya/assets/`.
- [x] 2.2 Extend build output creation and cleanup to include generated `site/_raya/assets/`.
- [x] 2.3 Copy source assets into `site/_raya/assets/` while preserving current artifact-level `assets/` output.
- [x] 2.4 Reuse source link classification so only validated local asset references are rewritten as browser asset URLs.
- [x] 2.5 Rewrite rendered local asset hrefs relative from each generated HTML page to `site/_raya/assets/`.
- [x] 2.6 Preserve existing relative page-to-page rendering for `.md` content links.
- [x] 2.7 Preserve external URL, `mailto:`, `tel:`, and fragment-only rendering behavior.

## 3. Artifact And Guidance Updates

- [x] 3.1 Update OpenSpec config guidance so rendered-output changes require e2e/static-read-path tests and representative fixture content.
- [x] 3.2 Update artifact/static guidance to distinguish artifact-level machine surfaces from browser-facing `site/_raya/` resources.
- [x] 3.3 Keep docs explicit that math rendering, graph UI, backlinks, wikilinks, heading-anchor validation, external link policy, and interactive components remain future work.
- [x] 3.4 Confirm no generated example artifact output is committed.

## 4. Verification

- [x] 4.1 Run local `raya validate`, `raya build`, `raya artifacts inspect`, `pytest -q`, and the e2e/static-read-path test command.
- [x] 4.2 Run Docker Compose `raya validate`, `raya build`, `raya artifacts inspect`, `pytest -q`, and the e2e/static-read-path test command.
- [x] 4.3 Run `./scripts/smoke-test.sh`.
- [x] 4.4 Run `openspec validate define-static-render-resource-resolution --strict`.
- [x] 4.5 Run `openspec validate --specs --strict`.
