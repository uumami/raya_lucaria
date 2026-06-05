## Why

Glintstone currently renders only a minimal Markdown subset, but Raya Lucaria needs serious static course notes before executable code, notebooks, or browser runtimes can land cleanly. This phase defines the rich static rendering baseline from `docs/foundation/17_rendering_execution_plan.md` while preserving static portability and keeping execution explicitly out of scope.

## What Changes

- Define a Raya-owned rich static rendering contract for Markdown pages under the ordered `course/` source tree.
- Add support expectations for headings, paragraphs, lists, links, code blocks, math, tables, callouts/admonitions, footnotes or citations if accepted in design, heading anchors, and generated page table of contents.
- Preserve deployment-neutral URLs, static-file usefulness, artifact inspection, generated navigation/index data, and `site/_raya/` as the browser-facing generated resource namespace.
- Add representative course and documentation fixture content that demonstrates rich rendering without becoming canonical pedagogy.
- Add contract and e2e/static-read-path coverage for the richer rendered HTML surface.
- Update foundation guidance, English and Spanish role guides, rendered documentation content, and OpenSpec guidance as needed.
- Defer executable code execution, notebooks, runtime profiles, cache metadata, Pyodide/JupyterLite, and local `raya run` behavior to later phases.

## Capabilities

### New Capabilities

- `rich-static-rendering`: Defines the static rendering baseline for rich course pages, including supported Markdown structures, math, code display, callouts, anchors, page table of contents, and accessibility expectations.

### Modified Capabilities

- `minimal-static-builder`: Render the richer static page surface while preserving generated navigation, indexes, official study counts, stable links, and static-file behavior.
- `static-render-resource-resolution`: Reserve and use generated browser-facing resources under `site/_raya/` for rendering assets such as math, syntax highlighting, or future component support.
- `artifact-contract-baseline`: Expose any new render-support data or generated browser resources through the manifest-centered artifact contract without making rendered HTML authority.
- `dev-workflow-baseline`: Require representative examples, contract tests, e2e/static-read-path tests, role docs, and rendered-doc updates when rich rendering changes.

## Impact

- Affected packages: `packages/static` renderer internals, schema/artifact validators if render-support data is added, and CLI build validation only as needed.
- Affected artifacts: generated HTML under `artifact/site/`, possible `site/_raya/` generated resources, and manifest-declared data if the design accepts render-support indexes.
- Affected fixtures: course render fixture, documentation fixture, live docs render tree, and invalid fixtures for unsupported or unsafe render constructs.
- Affected documentation: `docs/foundation/17_rendering_execution_plan.md`, course/artifact docs if required, English and Spanish role guides, README/AGENTS only if operational commands change.
- No runtime execution dependency is introduced in this change; `uv`, Docker execution, notebook execution, cache policies, and browser execution remain future adapters.
