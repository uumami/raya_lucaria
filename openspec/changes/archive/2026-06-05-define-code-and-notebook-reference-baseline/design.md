## Context

Raya Lucaria now has a rich static Markdown baseline, but courses in data science, programming, mathematics, and computational subjects need authored scripts and notebooks to travel with static notes. Today, local Markdown links can target pages and `_assets/`, but there is no first-class distinction between an opaque asset, a script that may later be executed, and a notebook that may later need kernel, output, and trust metadata.

Phase 2 defines references only. It makes code and notebooks valid source support material, validates links to them, copies them into artifacts, and renders static links/previews. It intentionally stops before runtime profiles, caches, kernels, browser execution, or local `raya run`.

## Goals / Non-Goals

**Goals:**

- Define `code/` and `notebooks/` as authored source support directories owned by the nearest learning quantum.
- Keep code and notebooks out of rendered navigation while preserving their relationship to the page that references them.
- Validate supported `.py` and `.ipynb` references before build.
- Copy referenced code and notebook files into artifact-level and browser-facing generated outputs.
- Write manifest-declared reference data for future agents, launchers, graph tools, and execution managers.
- Render static reference links and compact source/outline previews without executing.
- Keep static read paths working when `artifact/site/` is served directly or opened locally.

**Non-Goals:**

- No `raya run` command.
- No execution policies beyond a clear no-execution marker for referenced files.
- No `uv` or Docker runtime profile selection.
- No notebook execution, kernel validation, output trust, output caching, or refresh.
- No Pyodide, JupyterLite, marimo, remote runners, or GPU services.
- No cross-course package manager or dependency resolver.
- No new official learning object family.

## Decisions

### Use `code/` and `notebooks/` as source support directories

`_assets/` remains for opaque files such as images, CSVs, PDFs, and other support material. `_official/` remains for official learning objects. Code and notebooks need semantic validation and future execution metadata, so they should live in visible `code/` and `notebooks/` directories colocated with the quantum they support.

Alternative considered: put scripts and notebooks under `_assets/`. Rejected because it hides behavior that future execution, cache, security, and agent workflows must understand.

### Validate ordinary Markdown links first

Authors should be able to write normal links such as `[cleaning script](code/clean_data.py)` and `[exploration notebook](notebooks/exploration.ipynb)`. Richer directives can be proposed later if preview options, captions, or execution controls need source syntax.

Alternative considered: require custom directives immediately. Rejected because the baseline should be easy to author and should not invent syntax before plain Markdown links fail.

### Own-or-ancestor support references are the safe default

Phase 2 should mirror current `_assets/` ergonomics: a page may reference code or notebooks in its own support directory or an ancestor support directory inside the authored source tree. Cross-quantum references should be invalid by default unless a future proposal explicitly defines ownership, export scope, and cache implications.

Alternative considered: allow any path under `course/`. Rejected because it makes ownership and future execution caches ambiguous.

### Copy referenced files to both artifact and static paths

Referenced code and notebooks should appear in `artifact/files/` for inspection/local tooling and in `artifact/site/_raya/files/` for browser download. Rendered HTML should point at `site/_raya/files/` using relative URLs.

Alternative considered: copy only to `site/_raya/files/`. Rejected because artifact inspection and future local execution should not scrape the static site.

### Add `references.json`

Machine-readable reference data should record page ID, source path, kind, language/format, hash, artifact path, browser path, and no-execution status. This gives future Sellen agents, launchers, graph tools, and execution managers a stable surface that is not rendered HTML.

Alternative considered: rely on `links.json`. Rejected because links describe graph relationships, while code/notebook references need file metadata and future execution fields.

### Render previews safely

Scripts may render a source excerpt; notebooks may render a static outline or cell-source preview from notebook JSON. Notebook outputs must not be trusted or executed in this phase. The builder may show that execution is deferred.

Alternative considered: render full notebook output. Rejected because output trust, kernel metadata, large outputs, and cache refresh belong to later phases.

## Risks / Trade-offs

- [Scope creep into execution] Reference metadata can look like runtime metadata. Mitigation: every artifact and rendered panel must mark references as not executed and defer policy/runtime fields.
- [Large notebooks or files] Static previews can become heavy. Mitigation: preview a compact excerpt/outline and always provide download links.
- [Cross-quantum reuse pressure] Authors may want shared code. Mitigation: allow own/ancestor references first and design explicit shared-source semantics later.
- [Notebook JSON variability] Notebook files can contain large outputs or unusual metadata. Mitigation: validate readable `.ipynb` JSON minimally and ignore outputs for Phase 2 preview.
- [Artifact path churn] New `files/` paths expand the artifact contract. Mitigation: manifest-declare `references.json` and test artifact inspection/static read paths.

## Migration Plan

1. Add the new `code-notebook-references` spec and delta specs for source, link validation, static builder, artifact, inspection, resource, and workflow behavior.
2. Add source-reference discovery and validation helpers in `packages/schema`.
3. Add artifact reference data schemas/validators if `references.json` is accepted.
4. Update Glintstone to copy referenced files to `artifact/files/` and `site/_raya/files/`, rewrite rendered links, and render compact reference panels/previews.
5. Add representative valid and invalid fixtures.
6. Add contract, artifact, e2e/static-read-path, and documentation tests.
7. Update foundation docs and separate English/Spanish role guides.

Rollback is straightforward because source files remain ordinary Markdown links plus ordinary source support files. Generated `files/`, `site/_raya/files/`, and `references.json` can be removed by rebuilding with a previous builder.

## Open Questions

- Should Phase 2 support only `.py` and `.ipynb`, or also `.sql`, `.r`, `.jl`, and `.sh` as display-only code references?
- Should unreferenced files under `code/` and `notebooks/` be copied, warned about, or ignored?
- Should notebook previews show only markdown/code cell headings or also small trusted-looking output metadata marked as ignored?
- Should ancestor `code/` and `notebooks/` be allowed immediately, or should Phase 2 require own-quantum support only?
