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
- Execution output is generated artifact data unless it is explicitly frozen into reviewed `_reviewed/` source support.
- Normal rendered pages should stay focused. Verbose reference, runtime, cache, hash, freshness, and copied-file internals belong in manifest-declared data or static inspection surfaces.
- `raya preview <course>` is the local static review loop for generated pages. It validates, builds, serves `artifact/site/`, and exposes `_raya/inspect/` without running execution targets, Docker, kernels, package installers, or cache refreshes.

## Layer Model

```text
course source
  course/
    pages
    code references
    notebook references
    _assets/
    _official/
    _reviewed/
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
  never / manual / cache / always
  uv by default
  Docker for class reproducibility
        |
        v
reviewed output
  raya outputs list
  raya outputs freeze
  _reviewed/ source support
  frozen validation
        |
        v
artifact
  site/
  data/
  assets/
  reviewed/
  execution/
  logs/
  cache/
  execution metadata and outputs
```

`course/` remains the learning source tree. Runtime files such as `pyproject.toml`, `uv.lock`, Docker files, and profile files live beside `course/` because they support execution instead of defining learning order.

## Surface Discipline Across Phases

Each phase adds artifact data before it adds more default page display. Use these tiers:

| Tier | Use |
| --- | --- |
| `student-default` | Course reading, navigation, indexes, local assets, selected study cues. |
| `support-panel` | Compact resource, execution-status, reviewed-output, or study-object summaries. |
| `inspection` | Static audit pages for professors, contributors, and agents. |
| `machine-only` | `manifest.json`, `data/*.json`, copied files, hashes, cache keys, and future service inputs. |

Code/notebook references, runtime profiles, cache keys, execution plans, and reviewed outputs may all be complete in artifact data. Default pages should show compact labels and links, not raw JSON or internal paths. Inspection pages can expose the detailed metadata without becoming course canon.

Rendered-surface changes should include static-read-path or equivalent visual/layout checks for representative desktop and mobile-sized viewports. These checks protect readability and reviewability; screenshots and HTML are not machine authority.

## Execution Policies

Future executable content should use explicit policies:

| Policy | Meaning |
| --- | --- |
| `never` | Render code only. Do not execute. This is the safe default for ordinary code blocks. |
| `manual` | Execute only when an author or student explicitly requests it. |
| `cache` | Execute when source, inputs, runtime, or policy hashes change; otherwise reuse output. |
| `always` | Execute every build. Use only for cheap deterministic examples. |
| `frozen` | Validate current reviewed source support and fail if it is missing or stale. It never executes. |

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
- Inline dollar math and display dollar-delimiter blocks are pre-rendered at build time with MathJax into `artifact/site/`.
- Build-time math uses renderer dependencies only. It does not execute course code, notebooks, kernels, `uv`, Docker, package installers, runtime profiles, or cache refreshes.
- MathJax support CSS and fonts are copied under `artifact/site/_raya/render/math/` and linked with deployment-neutral relative URLs so local preview and static web deployment use the same files.
- The first accepted math subset uses MathJax `base`, `ams`, and `newcommand`: common algebra, calculus, matrices, aligned equations, cases, probability/statistics notation, optimization notation, Greek symbols, operators, accents, sums, products, limits, integrals, page-local `\newcommand`, and page-local `\renewcommand`.
- Unknown macros, malformed display delimiters, unsupported nested delimiters, full LaTeX documents, missing local MathJax resources, and raw visible math leakage are publication-blocking diagnostics.
- GitHub-style blockquote callouts render for `[!NOTE]`, `[!TIP]`, `[!WARNING]`, and `[!CAUTION]`.
- Footnotes render on the same page. A missing footnote definition is a build diagnostic naming the source page and label.
- Heading anchors are page-local conveniences derived from heading text. Duplicate anchors receive suffixes. Durable identity remains frontmatter `id` plus `raya:<id>` links.
- Pages with enough section headings get a generated page table of contents. The table of contents and generated indexes are output, not source edits.
- Numbered objects render at build time from fenced `:::` directives and
  `render.numbered_objects` configuration. Theorem, corollary, equation,
  figure, table, problem, homework, and assignment families may share or use
  separate sequences according to course configuration. `remark` is also a
  built-in theorem-family object. The default reader presentation uses the
  `scannable` style for theorem, example, exercise, and assignment sequences;
  figure and table keep `caption` presentation, and equation keeps `equation`
  presentation. The course-level customization surface remains current through
  `render.numbered_objects` sequence and family overrides in `raya.yaml`;
  page/section style overrides are future work. Course-global shorthand
  references such as `@compactness` and explicit links such as
  `raya:ref/compactness` resolve to static labels, anchors, hrefs, and
  manifest-declared `data/numbered-objects.json` entries.
- Numbered object rendering follows the same no-CDN, no-browser-MathJax,
  no-external-renderer-request discipline as build-time math. Browser pages
  receive static HTML, labels, anchors, and links; they do not run a client-side
  numbering or reference resolver.
- Proof blocks use `::: proof {of="object-id"}` and render statically as proof environments. They may target any numbered object family, including theorems, definitions, equations, figures, tables, problems, homework, and activities. Proofs are not numbered objects and do not appear in `data/numbered-objects.json`.
- Static environments are current build-time rendering behavior. `proof`,
  `solution`, `hint`, and `answer` use fenced directives, may carry stable
  IDs, and may target a numbered object with `of="object-id"`. They render
  static headings such as `Solution of Problem 3.1`, `Hint for Activity 4.1`,
  and `Answer to Homework 5.1`, but they do not appear in
  `data/numbered-objects.json`. Unknown targets, malformed attributes,
  duplicate static-environment IDs, and collisions with numbered object IDs
  fail build with source diagnostics.
- Numbered objects participate in render-debug inspection. Debug screenshots,
  copied static-site parity checks, raw TeX checks, overflow checks, and
  inspection pages should make numbered labels, anchors, hrefs, and reference
  text reviewable without treating screenshots or HTML as machine authority.
  Numbered content diagnostics are a current renderer quality pillar. CLI/build
  diagnostics and `data/numbered-objects.json` remain authoritative; render-debug
  adds screenshots, report JSON, and inspection HTML as evidence for labels,
  anchors, references, proof targets, raw TeX leakage, external requests, and
  browser-side MathJax absence.
- Raw HTML is escaped by default.
- Browser-facing renderer support files live under `artifact/site/_raya/` and use deployment-neutral relative URLs.

Compact rendered example:

> [!NOTE]
> This note is rendered documentation. It demonstrates the accepted static surface, not course canon.

| Source feature | Baseline behavior |
| --- | --- |
| Math | Inline $E = mc^2$ and display math are pre-rendered with MathJax. |
| Code | Code is displayed and highlighted, not executed. |

$$
\int_0^1 x^2\,dx = \frac{1}{3}
$$

Accepted display math uses delimiter lines on their own:

```markdown
$$
\begin{aligned}
\hat{\theta} &= \operatorname*{arg\,max}_{\theta \in \Theta} L(\theta) \\
\bar{x} &= \frac{1}{n}\sum_{i=1}^{n}x_i
\end{aligned}
$$
```

Escaped dollar signs such as `\$5` stay text. Fenced code is code, not math.
Standalone LaTeX document commands such as `documentclass` or `begin{document}`
are not part of the static course authoring contract.

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
- static rendering of code links, notebook links, and safe source previews,
- artifact data for code/notebook references,
- examples and e2e tests that prove local and web static paths work.

Accepted baseline:

- Markdown links to `.py` and `.ipynb` files define code and notebook references. Glintstone classifies the target by extension, not by a required folder name.
- `code/`, `notebooks/`, `scripts/`, `helpers/`, `labs/`, and similar names are ordinary author organization choices. None of them are required or reserved support roots.
- Do not put runnable code or notebooks under `_assets/`; assets are opaque support files, while code and notebooks need semantic validation and future execution metadata.
- Do not put code or notebooks under `_official/`; official learning objects are cards, prompts, quizzes, tasks, and similar pedagogical objects, not arbitrary runtime files.
- Do not put source code or notebooks under `_reviewed/`; reviewed output is frozen support produced after explicit execution and review.
- Treat linked code and notebook files as authored source support material, not rendered navigation entries.
- Let ordinary Markdown links reference supported files first. Add richer reference syntax only when normal links cannot express a needed behavior.
- Validate referenced files before build and diagnose missing, unsupported, private, or path-escaping references.
- Own-or-ancestor `.py` and `.ipynb` references are accepted; cross-quantum references are invalid until a later shared-code contract exists.
- Only validated, linked `.py` and `.ipynb` files are copied into generated reference storage. Unlinked scripts and notebooks remain source files and are not published by reference handling.
- Copy referenced files into `artifact/files/` for artifact inspection and `artifact/site/_raya/files/` for browser-facing static storage.
- Generate manifest-declared `artifact/data/references.json` so future agents, launchers, graph tools, and execution managers do not scrape rendered HTML.
- Record page ID, source path, target, kind, format, hash, artifact path, browser path, and `not-executed` status for each reference.
- Render deployment-neutral links plus safe previews: code previews show source excerpts; notebook previews read JSON source cells and ignore outputs.
- Defer notebook execution, output trust, cache refresh, kernel selection, and browser execution.

Recommended source shape:

```text
course/
  1_foundations/
    1_cleaning_data/
      0_index.md
      scripts/
        clean_data.py
        train_model.py
      labs/
        exploration.ipynb
      _assets/
        sample.csv
      _official/
        cards/
          1_cleaning.yaml
```

In this shape, `0_index.md` owns the learning quantum. `scripts/`, `labs/`,
`_assets/`, and `_official/` support that quantum but do not create child pages.
Authors may choose names like `code/` or `notebooks/` when those names fit the
course, but Glintstone validates the linked `.py` or `.ipynb` target by
extension and ownership boundary. If a course needs a child page, it should
create an ordered Markdown file or ordered directory instead of hiding page
content inside support folders.

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
[cleaning script](scripts/clean_data.py) or open the
[exploration notebook](labs/exploration.ipynb).

The script uses [sample data](_assets/sample.csv).
```

Phase 2 should render a small generated reference panel from validated links:

```text
Referenced Work
  Script    clean_data.py        view source | download
  Notebook  exploration.ipynb    preview | download
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
      1_foundations/1_cleaning_data/scripts/clean_data.py
      1_foundations/1_cleaning_data/labs/exploration.ipynb
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
`artifact/data/references.json` records at least source page ID, source path,
target, kind, format, hash, artifact path, browser path, and no-execution
status. `manifest.json` declares the reference index and generated `files/`
directory.

Suggested validation boundary:

| Reference | Phase 2 behavior |
| --- | --- |
| `scripts/example.py` | Valid if the linked `.py` target is owned by the page's quantum or an accepted ancestor. |
| `labs/example.ipynb` | Valid if the linked `.ipynb` target is readable notebook JSON and owned by the page's quantum or an accepted ancestor. |
| `code/example.py` | Valid by the same `.py` ownership rule; `code/` is an ordinary folder name. |
| `notebooks/example.ipynb` | Valid by the same `.ipynb` ownership rule; `notebooks/` is an ordinary folder name. |
| `_assets/data.csv` | Valid asset reference through existing asset rules. |
| `_official/...` or `_reviewed/...` | Invalid from rendered Markdown unless a future contract explicitly allows it. |
| `../other_topic/scripts/example.py` | Invalid unless the proposal accepts cross-quantum support references deliberately. |
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

Accepted baseline:

- Runtime profile source lives beside the ordered `course/` tree.
- Use `runtime/profiles.yaml` for named runtime profiles.
- Root-level `pyproject.toml` and `uv.lock` are runtime support files, not learning quanta.
- `uv` is the only baseline runtime manager; other managers are future adapters.
- Docker plus `uv` is represented as profile metadata, such as a Docker Compose service name, without making Docker required for static reading.
- Execution policies are explicit: `never`, `manual`, `cache`, `always`, and `frozen`.
- Missing policy defaults to `never`; `always` must be target-specific and cannot be inferred as a default.
- Validation may parse runtime metadata, validate paths, check profile references, and check cache input declarations.
- Validation, build, artifact inspection, and static serving must not execute scripts, notebooks, kernels, `uv`, Docker, package installers, or cache refreshes.
- Glintstone may emit manifest-declared `data/runtime.json`, `data/execution.json`, and `data/cache.json`.
- Generated execution metadata records planned targets with status `not-executed`.
- Cache keys are metadata derived from source hashes, declared input hashes, runtime profile metadata, lockfile hash when present, execution policy, and Raya or Glintstone schema versions.
- Phase 3 does not define reviewed frozen outputs, output logs, notebook kernels, browser execution, remote runners, or `raya run`.

Recommended source shape:

```text
course-root/
  raya.yaml
  pyproject.toml
  uv.lock
  runtime/
    profiles.yaml
  course/
    0_index.md
    scripts/
      example.py
```

Compact `runtime/profiles.yaml` example:

```yaml
profiles:
  default:
    manager: uv
    python: "3.10"
    project: pyproject.toml
    lockfile: uv.lock
    docker:
      compose_service: dev
execution:
  defaults:
    policy: never
    profile: default
  references:
    - source: course/scripts/example.py
      policy: cache
      profile: default
      inputs:
        - course/_assets/sample.csv
```

### Phase 4: Local Execution

Add real local execution using the phase 3 contract.

Minimum work:

- `raya run` or equivalent command shape,
- notebook execution through established Jupyter tooling,
- script execution through `uv run`,
- Docker execution path,
- cache reuse and explicit refresh,
- docs for professors, students, contributors, and agents.

Accepted baseline:

- Local execution is available only through `raya run <course> <target>`.
- The target is explicit: a validated reference ID, runtime target ID, or course-root-relative referenced source path. There is no implicit course-wide execution.
- `raya run --dry-run` reports the resolved target, policy, profile, command shape, cache decision, and output paths without executing code.
- Script targets execute through `uv run` from the course root using the selected runtime profile metadata.
- Notebook targets execute through Jupyter `nbconvert` under the selected `uv` profile and write a generated output notebook under the artifact root.
- Docker plus `uv` is an explicit wrapper through `raya run --docker`; it requires profile Docker Compose service metadata and is never the default.
- Policy behavior is enforced: `never` refuses, `manual` runs only when selected, `cache` reuses valid generated cache results unless `--refresh` is passed, `always` reruns when selected, and `frozen` validates reviewed source support without executing.
- Build, validate, artifact inspection, and static serving remain non-executing. They must not call `uv`, Docker, kernels, package installers, notebooks, scripts, or cache refreshes.
- Execution results are generated artifact data. `raya run` writes logs, captured stdout/stderr, output notebooks or stdout files, cache result records, and manifest-declared `data/execution-results.json` under the artifact root.
- Generated execution results do not become course source truth. They become reviewed course support only after an explicit `raya outputs freeze` step writes `_reviewed/` source files for human review and commit.

Recommended command shape:

```text
raya run . manual-script --dry-run
raya run . manual-script
raya run . cache-script
raya run . cache-script --refresh
raya run . manual-script --docker --dry-run
raya outputs list .
raya outputs freeze . cache-script
```

Recommended generated artifact shape after an execution run:

```text
artifact/
  manifest.json
  data/
    execution-results.json
  execution/
    outputs/
      <target>/
        stdout.txt
        <target>.ipynb
  logs/
    <target>.log
    <target>.stdout.log
    <target>.stderr.log
  cache/
    results/
      <cache-key>.json
```

### Phase 5: Reviewed And Frozen Execution Outputs

Promote selected generated outputs into reviewed course support without making build or validation execute code.

Minimum work:

- `_reviewed/` private source support colocated with the owning quantum,
- `raya outputs list <course>` for non-executing status inspection,
- `raya outputs freeze <course> <target>` for copying a current successful generated result into `_reviewed/`,
- source and artifact schemas for reviewed output metadata and files,
- `policy: frozen` validation against reviewed output,
- static reviewed-output panels and static read-path links,
- tests proving stale/missing reviewed output fails before publishing.

Accepted baseline:

- Reviewed output lives under `<owner>/_reviewed/execution/<target>/reviewed.yaml` with reviewed files beside the manifest.
- `_reviewed/` is private source support. It does not render as pages, navigation, ordinary assets, official objects, code references, or notebook references.
- `raya outputs list` reads source/runtime/reviewed/generated state and reports target status without building or executing.
- `raya outputs freeze` reads the latest successful current generated execution result, copies reviewed files into `_reviewed/`, writes source metadata, and exits without executing.
- Reviewed output freshness is checked against the current source hash, declared input hashes, runtime profile hash, lockfile hash when present, a policy-independent review key, and reviewed file hashes.
- `policy: frozen` means current reviewed output is required and validated. It never runs scripts, notebooks, kernels, `uv`, Docker, package installers, or cache refreshes.
- Glintstone writes manifest-declared `data/reviewed-outputs.json`, copies reviewed files to `artifact/reviewed/`, copies browser-facing reviewed files to `artifact/site/_raya/reviewed/`, and renders compact reviewed-output panels for pages that reference current reviewed targets.
- Artifact inspection validates reviewed output data and copied files without executing.
- Generated results remain generated until explicitly frozen and reviewed through normal source review.

Recommended source shape:

```text
course/
  1_topic/
    0_index.md
    scripts/
      train.py
    _reviewed/
      execution/
        train-cache/
          reviewed.yaml
          stdout.txt
```

Recommended author workflow:

```text
raya run . train-cache
raya outputs list .
raya outputs freeze . train-cache
# review and commit course/_reviewed/... through the normal source workflow
```

Recommended artifact shape:

```text
artifact/
  data/
    reviewed-outputs.json
  reviewed/
    train-cache/
      stdout.txt
  site/
    _raya/
      reviewed/
        train-cache/
          stdout.txt
```

### Phase 6: Browser And Optional Runners

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
raya run . <target>
raya run . <target> --refresh
docker compose run --rm dev ...
```

Professors should be able to publish static notes without executing anything unexpectedly, and students should have a clear path from web reading to local or Docker execution when the course requires real computation.
