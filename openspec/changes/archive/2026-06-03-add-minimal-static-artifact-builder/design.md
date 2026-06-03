## Context

The current reset baseline validates `raya.yaml`, source Markdown, official learning objects, and artifact schemas, but it cannot yet produce an artifact. The foundation defines Glintstone as the static content engine and builder, and `docs/foundation/06_artifact_contract.md` defines the required artifact surface.

This change turns the validated source-course loop into the first build loop:

```text
source course
  |
  v
raya validate
  |
  v
raya build
  |
  v
artifact/
  site/
  manifest.json
  data/
  assets/
```

## Goals / Non-Goals

**Goals:**

- Add `packages/static` as the plain package path for Glintstone builder code.
- Add `raya build <course>` to validate a source course and generate the first portable artifact.
- Produce readable static HTML pages with simple navigation and internal links.
- Produce `manifest.json`, `data/pages.json`, `data/quanta.json`, `data/links.json`, and `data/official.json`.
- Copy local assets into the artifact when the course has an assets directory.
- Preserve official learning-object authority labels and learning-quantum scope in artifact data.
- Make generated artifact validation part of tests and documented commands.

**Non-Goals:**

- No rich renderer, JavaScript framework, CSS framework, search tool, graph UI, or TypeScript/web UI decision.
- No backend, database, identity provider, registration, sync, or deployment adapter.
- No personal review queues, spaced repetition history, confidence ratings, mastery maps, or private study state.
- No migration of legacy renderer stacks, old generated JSON shapes, old `glintstone.yaml`, or old `clase/` assumptions.

## Decisions

### Decision: `packages/static` owns Glintstone build behavior

Implement build behavior in a new Python workspace package at `packages/static`; keep `packages/cli` as orchestration and diagnostics.

Rationale: this follows the foundation package map and keeps the CLI from owning rendering internals. It also leaves room for later graph, study, web, and UI packages to grow around the artifact contract.

Alternative considered: put build code directly in `packages/cli`. That would be faster initially but would blur command orchestration and content-engine responsibility.

### Decision: HTML rendering is intentionally minimal

Render Markdown into simple static HTML using baseline Python code and escaping, with headings, paragraphs, lists, and links sufficient for the fixture course.

Rationale: the first artifact must be static-useful and contract-valid, not visually complete. Avoiding a renderer dependency prevents a CSS or JavaScript stack from becoming architecture too early.

Alternative considered: adopt a Markdown/static-site dependency immediately. That can be proposed later if the builder needs richer Markdown semantics, components, or extension points.

### Decision: Source remains canonical

The builder reads source course files, writes generated artifacts, and treats generated data as rebuildable output. The manifest is the entrypoint for downstream consumers.

Rationale: this preserves the source/artifact boundary from the foundation and prevents dynamic domains from scraping rendered HTML as authority.

### Decision: Build validates before writing

`raya build <course>` runs source validation before artifact generation and exits nonzero if validation fails.

Rationale: build output should not mask contract errors. It also keeps CLI behavior predictable for humans and coding agents.

### Decision: Generated indexes are small but stable

The first indexes include enough identity, path, title, link, authority, and scope information to support future Primeval Current and Rennala proposals without implementing those domains yet.

Rationale: stable minimal data lets graph and study features grow from artifacts while preserving static usefulness.

## Risks / Trade-offs

- Minimal Markdown rendering may omit authoring features professors expect -> keep the fixture simple and treat richer Markdown/components as future Glintstone work.
- The generated indexes may need additional fields later -> start with schema-valid fields and add future fields through specs.
- Build output can leave generated files in `examples/courses/minimal/_site` during tests -> tests should use temporary course copies or clean output directories.
- `raya build` may feel like a renderer decision -> document that it is a builder contract, not a frontend stack decision.

## Migration Plan

1. Add `packages/static` and workspace metadata.
2. Implement the minimal builder and data generation.
3. Wire `raya build <course>` to validate, build, and print files read/outputs written.
4. Add tests for artifact shape, manifest/index validation, HTML output, asset copy, CLI build success, and CLI build failure.
5. Update root guidance and smoke testing.

Rollback is simple during reset: remove `packages/static`, the CLI build command, tests, and docs before archive. No deployed services or production data are affected.

## Open Questions

- Should future rich Markdown support come from a Python Markdown dependency, a renderer package, or a separate web pipeline?
- Should artifact content hashes include only source course files or also normalized generated data?
- Should `raya build` later support machine-readable diagnostics in addition to human-readable output?
