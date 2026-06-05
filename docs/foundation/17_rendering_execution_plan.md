---
id: docs-rendering-execution-plan
title: Rendering And Execution Plan
summary: Phase plan for rich rendering, executable code, notebooks, runtime profiles, caching, examples, tests, and documentation.
status: ready
---
# Rendering And Execution Plan

Raya Lucaria should render serious course notes and support executable learning work without letting a renderer, notebook tool, hosted service, or environment manager become the architecture.

This document is the planning anchor for several future OpenSpec changes. Each phase should move through the same loop:

```text
explore -> propose -> apply -> archive
```

Do not batch all rendering and execution work into one proposal. Each phase should leave accepted specs, examples, tests, docs, rendered docs, and role guidance in a coherent state.

## Core Decisions

- Raya owns the source contract, rendered artifact contract, navigation, indexes, official objects, and study scopes.
- Glintstone owns the static rendering pipeline and may use proven libraries internally.
- Quarto is a useful reference or optional adapter, not a core dependency.
- `uv` is the default Python runtime contract for local execution because `pyproject.toml` and `uv.lock` make environments reproducible.
- Docker plus `uv` is the reference classroom path for reproducibility.
- Raw `venv`, system Python, Conda, remote runners, Pyodide, JupyterLite, and marimo are future adapters, not the baseline source of truth.
- Rendering must not accidentally execute expensive or unsafe code.
- Execution output is generated artifact data unless a future accepted contract explicitly defines reviewed frozen output as source.

## Layer Model

```text
course source
  course/
    pages
    code references
    notebook references
    _assets/
    _official/
  pyproject.toml
  uv.lock
  runtime/
        |
        v
validation
  source order
  metadata
  links
  runtime profiles
  execution policy
        |
        v
rendering
  Markdown
  math
  code display
  static outputs
        |
        v
execution manager
  never / manual / cache / always / frozen
  uv by default
  Docker for class reproducibility
        |
        v
artifact
  site/
  data/
  assets/
  execution metadata and outputs
```

`course/` remains the learning source tree. Runtime files such as `pyproject.toml`, `uv.lock`, Docker files, and profile files live beside `course/` because they support execution instead of defining learning order.

## Execution Policies

Future executable content should use explicit policies:

| Policy | Meaning |
| --- | --- |
| `never` | Render code only. Do not execute. This is the safe default for ordinary code blocks. |
| `manual` | Execute only when an author or student explicitly requests it. |
| `cache` | Execute when source, inputs, runtime, or policy hashes change; otherwise reuse output. |
| `always` | Execute every build. Use only for cheap deterministic examples. |
| `frozen` | Reuse existing reviewed output and fail if it is missing or stale. |

Cache keys should include code, referenced input files, runtime profile, lockfile or environment hash, execution policy, and relevant renderer version. This prevents a weeks-long training job from running during normal render while still letting authors intentionally refresh it.

## Phase Order

### Phase 1: Rich Static Rendering

Define how pages render before adding live execution.

Minimum work:

- Markdown rendering contract,
- math rendering,
- code block highlighting,
- tables,
- footnotes or citations if accepted,
- callouts/admonitions,
- heading anchors and page table of contents,
- artifact and e2e tests,
- examples that demonstrate the rendering surface,
- updates to foundation docs, role guides, rendered docs, and OpenSpec config when needed.

Accepted baseline:

- Glintstone uses a parser-backed Markdown pipeline; Quarto remains an optional future adapter, not core.
- Common Markdown blocks and inline syntax render, including headings, paragraphs, ordered and unordered lists, blockquotes, thematic breaks, emphasis, strong text, inline code, links, images, and pipe tables.
- Fenced code blocks render as escaped static code with language metadata and syntax highlighting when supported. They never execute.
- Inline math with `$...$` and display math with `$$...$$` render as static math elements with TeX preserved in generated HTML.
- GitHub-style blockquote callouts render for `[!NOTE]`, `[!TIP]`, `[!WARNING]`, and `[!CAUTION]`.
- Footnotes render on the same page. A missing footnote definition is a build diagnostic naming the source page and label.
- Heading anchors are page-local conveniences derived from heading text. Duplicate anchors receive suffixes. Durable identity remains frontmatter `id` plus `raya:<id>` links.
- Pages with enough section headings get a generated page table of contents. The table of contents and generated indexes are output, not source edits.
- Raw HTML is escaped by default.
- Browser-facing renderer support files live under `artifact/site/_raya/` and use deployment-neutral relative URLs.

Compact rendered example:

> [!NOTE]
> This note is rendered documentation. It demonstrates the accepted static surface, not course canon.

| Source feature | Baseline behavior |
| --- | --- |
| Math | Inline $E = mc^2$ and display math preserve TeX. |
| Code | Code is displayed and highlighted, not executed. |

$$
\int_0^1 x^2\,dx = \frac{1}{3}
$$

```python
def displayed_only() -> str:
    return "not executed during render"
```

Rendered footnotes are allowed for documentation notes.[^rich-static-footnote]

[^rich-static-footnote]: This footnote belongs to the rendering plan documentation.

### Phase 2: Code And Notebook References

Let pages reference executable material without executing it by default.

Minimum work:

- source conventions for code files and notebooks beside quanta,
- validation for referenced `.py` and `.ipynb` files,
- static rendering of code links, notebook links, and declared outputs,
- artifact data for code/notebook references,
- examples and e2e tests that prove local and web static paths work.

Proposal-ready target:

- Use `code/` and `notebooks/` as user-facing support directories owned by the nearest learning quantum.
- Do not put runnable code or notebooks under `_assets/`; assets are opaque support files, while code and notebooks need semantic validation and future execution metadata.
- Do not put code or notebooks under `_official/`; official learning objects are cards, prompts, quizzes, tasks, and similar pedagogical objects, not arbitrary runtime files.
- Treat code and notebook files as authored source support material, not rendered navigation entries.
- Let ordinary Markdown links reference supported files first. Add richer reference syntax only when normal links cannot express a needed behavior.
- Validate referenced files before build and diagnose missing, unsupported, private, or path-escaping references.
- Copy referenced files into artifact-level inspection storage and browser-facing static storage with deployment-neutral links.
- Generate machine-readable reference data so future agents, launchers, graph tools, and execution managers do not scrape rendered HTML.
- Render source previews safely: code source can be displayed; notebooks can show a static outline or cell-source preview; neither path executes.
- Defer notebook execution, output trust, cache refresh, kernel selection, and browser execution.

Recommended source shape:

```text
course/
  1_foundations/
    1_cleaning_data/
      0_index.md
      code/
        clean_data.py
        train_model.py
      notebooks/
        exploration.ipynb
      _assets/
        sample.csv
      _official/
        cards/
          1_cleaning.yaml
```

In this shape, `0_index.md` owns the learning quantum. `code/`,
`notebooks/`, `_assets/`, and `_official/` support that quantum but do not
create child pages. If a course needs a child page, it should create an ordered
Markdown file or ordered directory instead of hiding page content inside code
or notebook folders.

Recommended authoring example:

```markdown
---
id: cleaning-data
title: Cleaning Data
summary: Fixture-sized example of code and notebook references.
status: ready
---
# Cleaning Data

Read the displayed excerpt, then download the
[cleaning script](code/clean_data.py) or open the
[exploration notebook](notebooks/exploration.ipynb).

The script uses [sample data](_assets/sample.csv).
```

Phase 2 should render a small generated reference panel from validated links:

```text
Referenced Work
  Script    clean_data.py        view source | download
  Notebook  exploration.ipynb    preview | download
  Asset     sample.csv           download
```

The panel is generated output. It should not be written back into source. The
page remains readable if the panel is not supported by a future theme.

Recommended artifact shape:

```text
artifact/
  manifest.json
  data/
    pages.json
    links.json
    references.json
  files/
    _source/
      1_foundations/1_cleaning_data/code/clean_data.py
      1_foundations/1_cleaning_data/notebooks/exploration.ipynb
  site/
    cleaning-data/
      index.html
    _raya/
      files/
        _source/...
      assets/
        _source/...
      render/
        rich.css
```

`artifact/files/` is for artifact inspection and future local tooling.
`artifact/site/_raya/files/` is for browser download and static read paths.
`artifact/data/references.json` should record at least source page ID, source
path, kind, language or format, hash, artifact path, browser path, and whether
the file was copied because it was referenced. If `references.json` is added,
`manifest.json` must declare it.

Suggested validation boundary:

| Reference | Phase 2 behavior |
| --- | --- |
| `code/example.py` | Valid if it stays under the owning quantum's `code/` or an allowed ancestor `code/`. |
| `notebooks/example.ipynb` | Valid if it is readable notebook JSON and stays under the owning quantum's `notebooks/` or an allowed ancestor `notebooks/`. |
| `_assets/data.csv` | Valid asset reference through existing asset rules. |
| `_official/...` | Invalid from rendered Markdown unless a future contract explicitly allows it. |
| `../other_topic/code/example.py` | Prefer invalid unless the proposal accepts cross-quantum support references deliberately. |
| External notebook or repository URL | Link as external content; do not validate or copy in Phase 2. |

The conservative default should be own-or-ancestor support references, matching
the current `_assets/` ergonomics. Cross-quantum code reuse is useful, but it
should be explicit because it affects ownership, export scope, and future
execution caches.

Phase 2 should not decide:

- `raya run`,
- execution policies beyond recording that referenced files are display-only,
- `uv` runtime profiles,
- Docker execution commands,
- notebook kernels,
- cached outputs,
- trusted frozen outputs,
- Pyodide, JupyterLite, marimo, or remote runners.

Those belong to phases 3 through 5. The only acceptable Phase 2 "execution"
behavior is a clear statement in generated HTML and reference data that nothing
was executed by the builder.

### Phase 3: Runtime Profiles And Cache Metadata

Define execution profiles and cache contracts before running expensive work.

Minimum work:

- `uv` default profile,
- Docker plus `uv` reference profile,
- policy metadata for `never`, `manual`, `cache`, `always`, and `frozen`,
- artifact shape for execution outputs, logs, and cache metadata,
- diagnostics for missing runtimes, stale lockfiles, and unsafe execution defaults.

### Phase 4: Local Execution

Add real local execution using the phase 3 contract.

Minimum work:

- `raya run` or equivalent command shape,
- notebook execution through established Jupyter tooling,
- script execution through `uv run`,
- Docker execution path,
- cache reuse and explicit refresh,
- docs for professors, students, contributors, and agents.

### Phase 5: Browser And Optional Runners

Add progressive execution paths after local execution is stable.

Possible adapters:

- Pyodide or JupyterLite for small browser Python,
- marimo for reactive notebooks,
- remote or GPU runners for heavy work,
- institutional execution services.

These must remain optional. Static rendering and local/Docker workflows should keep working without them.

## Required Surfaces For Each Phase

Every phase that changes rendering or execution should update the smallest necessary set of:

- foundation recommendation,
- OpenSpec proposal/design/spec/tasks,
- schema and validation contracts,
- static builder behavior,
- examples and invalid fixtures,
- unit or contract tests,
- e2e/static-read-path tests,
- live documentation render content,
- English and Spanish role guides when user-facing workflows change,
- OpenSpec config guidance when future proposal rules need tightening.

The goal is simple authoring and predictable builds:

```text
raya validate .
raya build .
raya run <target>
raya run --refresh <target>
docker compose run --rm dev ...
```

Professors should be able to publish static notes without executing anything unexpectedly, and students should have a clear path from web reading to local or Docker execution when the course requires real computation.
