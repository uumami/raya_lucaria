# Graph Key Objects Inspector Design

## Goal

Make the static Graph workspace more useful as a learning map by showing the selected page's public key objects in the graph inspector.

## Background

The reader right rail already exposes public key objects from the rendered article, and Search already indexes public section/object anchors. The Graph inspector shows page metadata, relationships, reading path, and official study objects, but it does not yet answer the learner's immediate question: "what important content is inside this selected lesson?"

Legacy `main` branch graph work has useful UX intent, but its implementation relies on older renderer assumptions and does not fit the current reset. The current branch must stay local, static, deterministic, and aligned with the foundation renderer contract.

## Design

The Graph selected-page inspector will include a compact `Key objects` section when the selected page has public numbered objects or proofs. The section will contain local links back to the selected page's exact rendered anchors, such as definitions, propositions, equations, figures, tables, problems, homework, and proofs.

The data source is the existing public search-section extraction that is already produced during page rendering. The graph browser payload will embed a sanitized `key_objects` list per page node. This is browser-facing convenience data only; it does not change `data/graph.json`, does not introduce object nodes, and does not infer recommendations or progress.

The Graph page HTML will include an initially hidden inspector placeholder with `data-raya-graph-detail-key-objects`. The local graph script will reveal it only for selected nodes with key objects, render links with `textContent`, and hide it when the graph selection clears.

## Constraints

- No browser-side MathJax conversion.
- No CDN, external renderer, fetch, XHR, or graph library dependency.
- No localStorage/sessionStorage for graph state.
- No object-level graph semantics, graph edges, ranking, recommendation, mastery, progress, or authority claims.
- No private source paths, `_official/` paths, cache keys, source hashes, or answer/support leakage.
- URLs must remain deployment-neutral static links.

## Files

- `docs/foundation/20_learning_renderer_contract.md`: clarify that selected Graph details may include public section/object anchor jump links.
- `packages/static/src/raya_static/builder.py`: pass search records to graph rendering and embed sanitized key-object payloads per graph node.
- `packages/static/src/raya_static/graph.py`: render selected-node key-object links in the inspector.
- `packages/static/src/raya_static/rendering.py`: add compact styles for the graph key-object list.
- `tests/contracts/test_static_builder.py`: assert the static graph shell and embedded payload expose key objects without private data.
- `tests/e2e/test_preview_static_read_path.py`: assert focused graph pages show visible key-object links on desktop/mobile without overflow or storage.

## Testing

Use TDD:

1. Add focused failing tests for graph payload and graph inspector behavior.
2. Implement the smallest payload, HTML, JS, and CSS changes to pass.
3. Run focused contract/e2e tests.
4. Run `UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture`.
5. Run `./scripts/check-render-debug.sh`.

## Review Notes

The feature must reuse public article/search anchors. It must not read from `numbered-objects.json` directly in the browser or expose source paths. It must keep graph selection and inspector rendering as transient local UI state.
