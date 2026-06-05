## Context

Glintstone can already validate ordered source pages and produce a portable static artifact, but its renderer is intentionally minimal. It escapes text, handles a few Markdown shapes, rewrites local links/assets, renders generated indexes, and emits basic navigation. That is enough to prove the artifact contract, but not enough for serious course notes.

The foundation plan separates rich static rendering from executable code and notebooks. This change is Phase 1: define and implement a richer static page surface while keeping execution, runtime profiles, cache metadata, and browser Python out of scope.

## Goals / Non-Goals

**Goals:**

- Render serious static notes from the existing `course/` source tree.
- Keep Glintstone and Raya artifact contracts authoritative; do not make Quarto or another site generator core.
- Use proven parser/highlighter/math-support libraries internally where useful.
- Support common authoring constructs: headings, paragraphs, lists, links, blockquotes, code blocks, math, tables, callouts, footnotes, heading anchors, and page table of contents.
- Preserve stable `raya:<id>` links, generated navigation, generated indexes, official study counts, deployment-neutral URLs, and static-file usefulness.
- Add representative examples, invalid fixtures where useful, contract tests, e2e/static-read-path tests, live rendered docs coverage, and English/Spanish role guidance.

**Non-Goals:**

- No code execution.
- No notebook execution or notebook rendering.
- No runtime profiles, cache metadata, `raya run`, Pyodide, JupyterLite, marimo, remote runners, or GPU execution.
- No Quarto compatibility layer.
- No bibliography/citation system beyond simple footnotes in this phase.
- No frontend application shell, theme system, search, graph UI, accounts, or backend service.

## Decisions

### Keep Glintstone as the renderer boundary

Glintstone should own source-to-artifact behavior. The implementation can use a Markdown parser, syntax highlighter, math helper, and small post-processing utilities, but those libraries must remain implementation details behind the Raya source and artifact contracts.

Alternative considered: use Quarto directly. Rejected for core because Quarto would want to own book configuration, navigation, execution, output layout, and publishing assumptions. Raya already owns ordered quanta, generated indexes, official study objects, role docs, and manifest-centered artifacts.

### Parse Markdown into a controlled render pipeline

The builder should move from ad hoc line parsing toward a real Markdown pipeline. Rendering must still route links and assets through existing Raya resolution code so `raya:<id>`, local Markdown links, colocated `_assets/`, and deployment-neutral static URLs keep working.

The practical implementation shape is:

```text
Markdown source
      |
      v
Markdown parser tokens / AST
      |
      +--> link rewrite through Raya link resolver
      +--> code block highlighting
      +--> math wrapping / support resources
      +--> heading IDs and page TOC
      +--> callout and footnote handling
      |
      v
HTML fragment
      |
      v
Glintstone page shell + generated indexes + navigation
```

### Support math statically without external network services

Inline and display math should render in generated HTML without depending on a CDN. If browser-side math resources are needed, they must be copied under `site/_raya/` and work from a direct static read path. The source TeX should remain inspectable in HTML so future renderers can improve accessibility without changing course source.

### Support code display but not execution

Fenced code blocks should render with language labels and syntax highlighting when a language is declared. Unknown languages should still render as escaped code. This phase may render metadata such as filename or caption if a compact syntax is accepted, but it must not execute code.

### Generate heading anchors and a page table of contents

Rendered headings should receive stable per-page anchor IDs derived from heading text with duplicate suffixes. These anchors are page-local convenience anchors, not durable course identity. Durable references remain frontmatter IDs and `raya:<id>` links.

Pages with headings below the main title should expose a generated page table of contents. The page table of contents is rendered output and should not be written back into source files.

### Include footnotes; defer citations

Footnotes are small enough to include in the rich static baseline. Bibliographies, CSL, citation keys, and source maps are a larger academic references contract and should be proposed later.

### Treat render support files as generated resources

Any browser-facing render support files, such as CSS, math scripts, or highlighting assets, belong under `artifact/site/_raya/`. Machine-readable render metadata, if added, belongs under `artifact/data/` and must be declared by `manifest.json`.

## Risks / Trade-offs

- [Renderer dependency sprawl] New libraries could become de facto architecture. Mitigation: keep library names out of source contracts and validate artifact behavior, not library internals.
- [Math accessibility] Browser-side math rendering may be less accessible than server-side MathML. Mitigation: preserve source TeX and keep the artifact contract open to richer math output later.
- [Heading anchor instability] Heading text changes can break fragment links. Mitigation: document anchors as page-local convenience links; durable links use `raya:<id>`.
- [Too much syntax at once] Adding every Markdown extension creates unclear authoring rules. Mitigation: accept a compact baseline and defer citations, executable code, notebooks, and custom components.
- [Fixture-as-pedagogy] Rich examples may look like course canon. Mitigation: label fixtures as fixture material and point to foundation docs as authority.

## Migration Plan

1. Add the `rich-static-rendering` spec and delta specs for builder, artifact, resource, and workflow behavior.
2. Replace ad hoc rendering internals with a controlled parser-backed renderer while preserving existing link/asset rewrite behavior.
3. Add representative rich-render fixture pages and documentation fixture pages.
4. Add contract tests for HTML fragments and artifact/resource outputs.
5. Add e2e/static-read-path tests for root and nested rich-render pages.
6. Update foundation guidance and English/Spanish role docs where user-facing authoring rules change.
7. Validate docs, specs, host tests, and representative Docker workflow before archive.

Rollback is straightforward because source pages remain Markdown and artifacts are generated output. If a rendering library choice proves wrong, Glintstone can change internals while keeping the accepted source and artifact contracts.

## Resolved Phase 1 Choices

- Accept GitHub-style blockquote callouts first: `[!NOTE]`, `[!TIP]`, `[!WARNING]`, and `[!CAUTION]`.
- Generate a page table of contents automatically when a page has at least two headings below the page title. This is rendered output only.
- Render math as static structured HTML with TeX preserved and generated local CSS under `site/_raya/`. Richer MathML or browser math engines can be added later without changing source syntax.
