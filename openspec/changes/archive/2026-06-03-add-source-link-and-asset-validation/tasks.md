## 1. Source Validation

- [x] 1.1 Add Markdown link extraction helpers for content validation.
- [x] 1.2 Classify external URLs, fragment-only links, local `.md` content links, and local asset links.
- [x] 1.3 Validate local `.md` content links relative to the source Markdown file and configured content directory.
- [x] 1.4 Validate local asset links relative to the source Markdown file and configured/default assets directory.
- [x] 1.5 Report source file, link target field, and next action for broken links/assets.
- [x] 1.6 Keep external URLs, `mailto:`, `tel:`, and fragment-only links from failing local validation.

## 2. Builder Link Index

- [x] 2.1 Reuse or mirror link extraction in the static builder.
- [x] 2.2 Add valid Markdown content links to `data/links.json` with kind `content`.
- [x] 2.3 Keep existing navigation and parent link entries.
- [x] 2.4 Ensure build stops on broken links/assets through source validation.

## 3. Tests

- [x] 3.1 Add validation tests for valid local Markdown content links.
- [x] 3.2 Add validation tests for broken local Markdown content links.
- [x] 3.3 Add validation tests for valid local asset references.
- [x] 3.4 Add validation tests for missing local asset references.
- [x] 3.5 Add validation tests that external URLs and fragment-only links are ignored.
- [x] 3.6 Add builder tests that content links are exported to `data/links.json`.
- [x] 3.7 Add builder tests that broken source links stop artifact generation.

## 4. Documentation

- [x] 4.1 Update README/AGENTS/CLAUDE guidance to mention local link and asset validation.
- [x] 4.2 Keep docs explicit that graph UI, backlinks, wikilinks, heading anchors, and external link policies remain future work.

## 5. Verification

- [x] 5.1 Run local `raya validate`, `raya build`, `raya artifacts inspect`, and `pytest -q`.
- [x] 5.2 Run Docker Compose `raya validate`, `raya build`, `raya artifacts inspect`, and `pytest -q`.
- [x] 5.3 Run `./scripts/smoke-test.sh`.
- [x] 5.4 Run `openspec validate add-source-link-and-asset-validation --strict`.
- [x] 5.5 Run `openspec validate --specs --strict`.
