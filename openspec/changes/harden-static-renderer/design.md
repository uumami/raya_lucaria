# Renderer Hardening Design

Date: 2026-06-12
Status: proposed, ready for implementation review

## Context

Raya Lucaria now has a useful static renderer, preview command, artifact
inspection, deployment-neutral links, and browser-driven layout checks. The weak
point is math: current pages preserve TeX inside static math elements, but they
do not actually typeset serious mathematical notation.

For data mining, statistics, calculus, linear algebra, optimization, and
machine-learning courses, this is foundational. Math, code, images, links, and
deployment behavior must be trustworthy before adding richer pedagogy surfaces
such as official study-object panels.

## Decision

Use a renderer-hardening change as the next implementation boundary.

The canonical path is:

```text
source course
  |
  v
raya build
  |
  v
artifact/site/
  |
  +-- raya preview locally
  |
  +-- static web deployment
```

Local preview and deployed web pages must serve the same generated files. There
must not be separate local and online render behavior.

Math rendering should use build-time MathJax through an isolated renderer
adapter. The generated artifact should contain pre-rendered math HTML plus local
browser-facing support assets. Deployment must not require Python, Node,
MathJax services, CDNs, a backend, or a dynamic app.

## Non-Goals

- No official card, quiz, prompt, or task UI in this change.
- No personal study state, review queues, spaced repetition, confidence ratings,
  or mastery maps.
- No new execution behavior for Python, notebooks, `uv`, Docker, kernels, or
  cache refresh.
- No browser-only math rendering as the canonical baseline.
- No promise to support arbitrary LaTeX documents or arbitrary LaTeX packages.

## Math Contract

The renderer should support a broad MathJax-backed TeX/LaTeX math subset for
course notation, including common arithmetic, algebra, calculus, linear algebra,
probability, statistics, optimization, Greek symbols, matrices, aligned
equations, cases, operators, accents, subscripts, superscripts, fractions,
integrals, sums, products, limits, and page-local macros.

Author-facing documentation must be explicit:

- accepted inline delimiters,
- accepted display delimiters,
- supported environments,
- macro rules,
- escaping rules inside Markdown,
- how math behaves near punctuation and code,
- what is unsupported,
- how diagnostics identify the source file and expression.

MathJax is not a full LaTeX engine. It implements TeX/LaTeX math support in
JavaScript and extensions; it does not support every LaTeX package or full
document behavior. The contract should name the supported subset and link to the
MathJax support and extension documentation.

Sources:

- <https://docs.mathjax.org/en/latest/input/tex/index.html>
- <https://docs.mathjax.org/en/latest/input/tex/extensions.html>
- <https://docs.mathjax.org/en/latest/server/components.html>

## Accepted Math Syntax

The first renderer-hardening baseline accepts a deliberately small authoring
surface:

- Inline math uses `$...$`.
- Display math uses `$$` blocks with opening and closing delimiters on their
  own lines.
- Fenced code blocks are code, not math.
- Escaped dollar signs remain text.
- Arbitrary full LaTeX documents are not accepted.

The MathJax invocation should enable the `base`, `ams`, `newcommand`, and
`noundefined` TeX extensions. The supported first-baseline notation includes
common matrices, aligned equations, cases, operators, accents, fractions, sums,
products, limits, integrals, Greek symbols, subscripts, and superscripts.

Macro support is local to the rendered page or expression through MathJax
handling of `\newcommand` and `\renewcommand`. This change does not introduce a
course-level macro configuration file unless a later accepted proposal opens
that contract.

Unsupported or malformed syntax fails with diagnostics. Delimiter mistakes,
nested unsupported delimiters, MathJax conversion failures, missing local
support resources, and visible raw math leakage are publication-blocking
failures rather than warnings.

## Failure Policy

The default policy is strict.

Validation or build must fail when math would visibly break a published page:

- malformed delimiters,
- parser errors,
- unsupported delimiter nesting,
- MathJax conversion errors,
- missing local MathJax support assets,
- generated math that remains visibly raw because rendering failed.

A controlled fallback is allowed only for explicitly accepted rare unsupported
notation. The fallback must preserve visible source TeX, emit an actionable
diagnostic, and be covered by tests. It must not silently pass as correctly
rendered math.

## Architecture

### Renderer Adapter

Add a small math-renderer adapter boundary rather than embedding MathJax logic
throughout the Markdown renderer.

```text
RichMarkdownRenderer
  extracts math fragments with source locations
        |
        v
MathRenderer adapter
  input: TeX fragments, display mode, source file, source span
  output: rendered HTML, required assets, diagnostics
        |
        v
Glintstone page shell
  writes pre-rendered math and local render assets
```

The adapter may call a Node/MathJax script internally, but course code is never
executed. Node is a renderer dependency, not a course runtime. Docker is the
reference environment that contains the renderer dependencies. Local non-Docker
development may work when the same dependencies are installed.

The implementation baseline uses Node 22 and `@mathjax/src` v4 as renderer
dependencies declared by root `package.json` and `package-lock.json`. Host and
Docker verification install them with
`npm ci --ignore-scripts --no-audit --no-fund` and verify the adapter with
`npm run raya-render-math -- --self-test`.

### Artifact Shape

Math support files belong under the browser-facing static resource area:

```text
artifact/
  site/
    _raya/
      render/
        rich.css
        math/
          ...
```

The exact MathJax asset shape can be chosen during implementation, but all
generated links must be deployment-neutral and local to `artifact/site/`.

### One Static Surface

`raya preview` must serve the same `artifact/site/` that deployment uses.
Browser tests should verify preview, local static serving, and deployment-root
neutral paths against those generated files.

## Rendering Pillars

### Math

Use build-time MathJax output. Browser tests must prove equations are typeset,
not merely preserved as TeX text. The original TeX should remain available for
copy, inspection, or diagnostics where practical, but it should not be the
visible default when rendering succeeds.

### Images

Keep local images deployment-neutral and responsive. Validate local assets
before build, preserve alt text, copy files under `site/_raya/assets/`, and
test nested-page image paths.

### Links

Keep `raya:` stable links, local Markdown links, local assets, copied
code/notebook files, and reviewed-output files portable. Browser tests should
check that generated links resolve from nested pages and from a static server
root.

### Code

Static code display remains non-executing. Fenced code blocks should preserve
readability, language labels, escaping, and syntax highlighting. Linked `.py`
and `.ipynb` files remain copied references with `not-executed` status unless
the user explicitly runs `raya run`.

### Layout

Math, code, tables, images, callouts, footnotes, generated indexes, support
panels, and inspection links must not overlap or cause horizontal page overflow
on representative desktop and mobile viewports.

## Verification

The change should add a representative math/rendering fixture that includes:

- inline and display math,
- matrices and aligned equations,
- cases and piecewise functions,
- derivatives, partial derivatives, integrals, sums, products, limits,
- probability/statistics notation,
- optimization notation,
- page-local macros,
- code blocks beside math,
- images and local assets,
- stable `raya:` links and nested local links,
- callouts, tables, footnotes, and generated table of contents.

Required checks:

- contract tests for math diagnostics and generated artifact assets,
- static-read-path tests for nested links and local render assets,
- Playwright/Chromium checks that math is visibly typeset,
- no external network requests for renderer assets,
- desktop and mobile layout checks for overflow and overlap,
- Docker reference workflow,
- local `uv` workflow,
- docs build and preview where rendered docs are touched.

The visual checks should inspect actual rendered pages, not only generated HTML
strings.

## Documentation

Update the smallest necessary foundation and guide surfaces:

- `docs/foundation/17_rendering_execution_plan.md` for the accepted renderer
  hardening boundary,
- `docs/foundation/07_cli_contract.md` or artifact docs if build/preview
  behavior changes,
- `openspec/config.yaml` so future rendering proposals inherit math and browser
  verification requirements,
- English and Spanish role guides for contributors, professors, students, and
  agents,
- rendered documentation examples that double as authoring guidance and
  fixtures.

Documentation should teach authors how to write math, code, images, and links
that work locally, offline, and online from the same generated artifact.

## Proposed OpenSpec Change

Use:

```text
harden-static-renderer
```

The OpenSpec proposal should cover:

1. renderer contract updates,
2. MathJax build-time adapter,
3. local static asset handling,
4. math/image/link/code fixture coverage,
5. Chromium visual verification,
6. documentation and guide updates.

Archive only after local checks, Docker checks, OpenSpec validation, rendered
docs validation/build, and browser verification pass.

## Adapter Boundary

`packages/static/src/raya_static/math_renderer.py` owns Python-side math
requests, diagnostics, subprocess calls, and CSS collection.
`packages/static/scripts/render_math.mjs` owns MathJax invocation. `rendering.py`
only knows about `MathRenderer.render_many()` output and token replacement.
The JavaScript side runs on Node 22 with `@mathjax/src` v4 from the repository
root `package.json` and `package-lock.json`.
