## Context

The current build loop can generate an artifact, and schema helpers can validate individual manifest and index files. What is missing is one artifact-level read-only inspection operation that follows the manifest and validates the artifact as a portable unit.

This matters because future dynamic domains should read artifacts through `manifest.json`, not by scraping HTML or assuming local source-course context.

## Goals / Non-Goals

**Goals:**

- Add `raya artifacts inspect <artifact>`.
- Accept an explicit artifact directory path and inspect `manifest.json`.
- Validate required artifact paths: `site/`, `data/`, `assets/`, and `manifest.json`.
- Validate `manifest.json` and the manifest-declared pages, quanta, links, and official indexes.
- Report files read, diagnostics, and stable zero/nonzero exits.
- Keep inspection read-only.

**Non-Goals:**

- No source-course rebuild.
- No deployment registration.
- No static link crawler, graph consistency engine, search validation, or browser rendering check.
- No machine-readable CLI output yet.
- No backend, identity, TypeScript/web UI, or provider adapter.

## Decisions

### Decision: inspection belongs in `packages/schema`

Add artifact-level inspection to the schema helpers because it validates contracts and manifest-declared data rather than rendering behavior.

Rationale: `packages/static` creates artifacts, while `packages/schema` validates contracts. The CLI should orchestrate both without owning the rules.

Alternative considered: put inspection in `packages/static`. That would tie artifact validation too closely to the first builder, while artifacts should remain readable by downstream services regardless of how they were produced.

### Decision: manifest-centered traversal

Inspection reads `manifest.json`, validates it, then follows `data.pages`, `data.quanta`, `data.links`, and `data.official` paths relative to the artifact root.

Rationale: this reinforces the artifact contract and keeps future services from scraping rendered HTML as authority.

### Decision: read-only command

`raya artifacts inspect <artifact>` does not write or repair files.

Rationale: inspection should be safe to run on generated artifacts, copied artifacts, mounted artifacts, or deployment outputs.

## Risks / Trade-offs

- Inspection is shallow and does not crawl every static link -> future proposals can add deeper static checks after the manifest contract is stable.
- The command validates schema shape, not pedagogical quality -> that remains a source-course and review concern.
- Nested CLI parsing adds a small amount of CLI complexity -> acceptable because artifact commands are a natural group.

## Migration Plan

1. Add artifact-level inspection helper.
2. Export the helper from `raya_schema`.
3. Add `raya artifacts inspect <artifact>`.
4. Add contract and CLI tests.
5. Update docs and smoke test.

Rollback is simple during reset: remove the helper, CLI command, tests, docs, and change specs before archive.
