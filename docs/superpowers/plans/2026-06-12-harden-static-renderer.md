# Harden Static Renderer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Glintstone render serious course pages with build-time MathJax math, deployment-neutral images/links/assets, non-executing code display, and browser-verified local plus deployed static behavior.

**Architecture:** Keep one canonical build path: `raya build` writes `artifact/site/`, `raya preview` serves the same files, and static deployment serves the same files. Add an isolated MathJax renderer adapter so `packages/static` can pre-render math without turning Node into course runtime or scattering MathJax details through the Markdown renderer. Preserve current artifact authority: rendered HTML is a view; manifest-declared data and copied files remain machine surfaces.

**Tech Stack:** Python 3.10, `uv`, Docker Compose, `markdown-it-py`, `mdit-py-plugins`, Pygments, Node 22, `@mathjax/src` v4, Pytest, Playwright/Chromium, OpenSpec.

---

## File Structure

- Create `openspec/changes/harden-static-renderer/` with proposal, design, delta specs, and tasks.
- Create `package.json` and `package-lock.json` at repository root for the renderer-only Node dependency.
- Modify `.gitignore` to ignore `node_modules/` and npm cache artifacts if missing.
- Modify `Dockerfile` to include Node/npm in the reference container.
- Modify `scripts/check-python.sh` to install/check renderer Node dependencies before Python tests.
- Create `packages/static/scripts/render_math.mjs` as the command-line MathJax adapter.
- Create `packages/static/src/raya_static/math_renderer.py` as the Python adapter boundary.
- Modify `packages/static/src/raya_static/rendering.py` to render `math_inline` and `math_block` through the adapter.
- Modify `packages/static/src/raya_static/builder.py` to pass the adapter/report into page rendering and write math CSS/assets under `site/_raya/render/math/`.
- Extend `examples/courses/render-fixture/` or create `examples/courses/math-fixture/` with broad math, images, links, code, callouts, tables, footnotes, and nested pages.
- Add invalid fixtures under `examples/courses/invalid/` for math conversion errors and malformed math delimiter cases.
- Add contract tests in `tests/contracts/test_math_renderer.py` and update `tests/contracts/test_static_builder.py`.
- Update e2e/browser tests in `tests/e2e/test_static_read_path.py` and `tests/e2e/test_preview_static_read_path.py`.
- Update `docs/foundation/17_rendering_execution_plan.md`, related foundation docs if needed, `openspec/config.yaml`, `AGENTS.md`, `README.md`, `CLAUDE.md`, and separate English/Spanish role guide pages.

## Task 1: Create OpenSpec Change

**Files:**
- Create: `openspec/changes/harden-static-renderer/proposal.md`
- Create: `openspec/changes/harden-static-renderer/design.md`
- Create: `openspec/changes/harden-static-renderer/tasks.md`
- Create: `openspec/changes/harden-static-renderer/specs/rich-static-rendering/spec.md`
- Create: `openspec/changes/harden-static-renderer/specs/minimal-static-builder/spec.md`
- Create: `openspec/changes/harden-static-renderer/specs/dev-workflow-baseline/spec.md`
- Modify after archive only: `openspec/specs/**/spec.md`

- [ ] **Step 1: Scaffold the OpenSpec change**

Run:

```bash
openspec new change harden-static-renderer
```

Expected: `openspec/changes/harden-static-renderer/.openspec.yaml` exists.

- [ ] **Step 2: Write proposal from the approved design**

Use this summary in `proposal.md`:

```markdown
## Why

Glintstone currently preserves TeX inside static math elements, but serious
math-heavy courses need actual typeset math. Rendering must be identical for
local preview, offline artifacts, and web deployment, so math must be rendered
during `raya build` into the same `artifact/site/` files that preview and static
hosting serve.

## What Changes

- Add build-time MathJax rendering through an isolated renderer adapter.
- Keep one canonical static artifact path for local preview and web deployment.
- Strengthen math, image, link, code, and layout fixtures.
- Add Chromium checks proving math is visibly typeset and no external renderer
  assets are requested.
- Add strict diagnostics for math that would visibly break published pages.
- Update foundation docs, role guides, `AGENTS.md`, and `openspec/config.yaml`.

## Non-Goals

- No official study-object UI.
- No personal study state.
- No browser-only MathJax as the canonical baseline.
- No course-code execution through validation, build, preview, or inspection.
```

- [ ] **Step 3: Write design artifact**

Copy the accepted design decisions from `docs/superpowers/specs/2026-06-12-renderer-hardening-design.md` into `design.md`, then add this implementation-specific boundary:

```markdown
## Adapter Boundary

`packages/static/src/raya_static/math_renderer.py` owns Python-side math
requests, diagnostics, subprocess calls, and CSS collection.
`packages/static/scripts/render_math.mjs` owns MathJax invocation. `rendering.py`
only knows about `MathRenderer.render_many()` output and token replacement.
```

- [ ] **Step 4: Add delta spec requirements**

Add these requirements to the delta specs:

```markdown
### Requirement: Build-time MathJax rendering
Glintstone SHALL pre-render supported TeX/LaTeX math during `raya build` into
the generated static artifact.

#### Scenario: Inline math is typeset
- **WHEN** a page contains supported inline math
- **THEN** generated HTML MUST contain MathJax-rendered output rather than only raw TeX text

#### Scenario: Display math is typeset
- **WHEN** a page contains supported display math
- **THEN** generated HTML MUST contain MathJax-rendered display output with local support CSS

#### Scenario: Broken math fails build
- **WHEN** MathJax reports a conversion error for source math
- **THEN** build MUST fail with a diagnostic naming the source file and math expression context

#### Scenario: Preview and deployment use one artifact
- **WHEN** preview serves a course after build
- **THEN** it MUST serve the same pre-rendered math files that static deployment serves
```

- [ ] **Step 5: Validate the change before implementation**

Run:

```bash
openspec validate harden-static-renderer --strict
```

Expected: the change validates before code work begins.

## Task 2: Add Renderer Dependency Baseline

**Files:**
- Create: `package.json`
- Create: `package-lock.json`
- Modify: `.gitignore`
- Modify: `Dockerfile`
- Modify: `scripts/check-python.sh`
- Test: `tests/contracts/test_dockerfile.py`
- Test: `tests/contracts/test_hygiene_scripts.py`

- [ ] **Step 1: Add failing dependency checks**

Add or update tests so the repository requires Node/MathJax support:

```python
def test_root_package_declares_mathjax_renderer_dependency() -> None:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert package["private"] is True
    assert package["dependencies"]["@mathjax/src"].startswith("4.")


def test_dockerfile_installs_node_for_math_renderer() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "node:22" in dockerfile
    assert "/usr/local/bin/node" in dockerfile
```

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_dockerfile.py tests/contracts/test_hygiene_scripts.py
```

Expected: tests fail because `package.json` and Docker Node support do not exist yet.

- [ ] **Step 2: Add root Node dependency files**

Create `package.json`:

```json
{
  "name": "raya-lucaria-renderer-tools",
  "private": true,
  "type": "module",
  "scripts": {
    "raya-render-math": "node packages/static/scripts/render_math.mjs"
  },
  "dependencies": {
    "@mathjax/src": "4.0.0"
  }
}
```

Run:

```bash
npm install --package-lock-only --ignore-scripts --no-audit --no-fund
```

Expected: `package-lock.json` is created and locks `@mathjax/src`.

- [ ] **Step 3: Ignore local Node install output**

Add these lines to `.gitignore` if absent:

```gitignore
node_modules/
.npm/
```

- [ ] **Step 4: Add Node to Docker reference image**

Modify `Dockerfile` to use the Node 22 toolchain while keeping Python/uv as the main environment:

```dockerfile
FROM node:22-slim AS node

FROM python:3.10-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
```

Keep the existing Chromium/git/ripgrep apt install after this block.

- [ ] **Step 5: Install Node dependencies in the verification path**

Modify `scripts/check-python.sh` before `uv sync`:

```bash
run npm ci --ignore-scripts --no-audit --no-fund
run npm run raya-render-math -- --self-test
```

Update the usage text to mention renderer dependency installation.

- [ ] **Step 6: Verify dependency checks**

Run:

```bash
npm ci --ignore-scripts --no-audit --no-fund
npm run raya-render-math -- --self-test
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_dockerfile.py tests/contracts/test_hygiene_scripts.py
```

Expected: `npm run raya-render-math -- --self-test` fails until Task 3 creates the script; the Python tests pass after test updates.

## Task 3: Add Node MathJax Renderer Script

**Files:**
- Create: `packages/static/scripts/render_math.mjs`
- Test through: `npm run raya-render-math -- --self-test`

- [ ] **Step 1: Create the MathJax command-line adapter**

Create `packages/static/scripts/render_math.mjs`:

```javascript
import {readFileSync} from 'node:fs';
import {mathjax} from '@mathjax/src/js/mathjax.js';
import {TeX} from '@mathjax/src/js/input/tex.js';
import {CHTML} from '@mathjax/src/js/output/chtml.js';
import {liteAdaptor} from '@mathjax/src/js/adaptors/liteAdaptor.js';
import {RegisterHTMLHandler} from '@mathjax/src/js/handlers/html.js';
import '@mathjax/src/js/util/asyncLoad/esm.js';

import '@mathjax/src/js/input/tex/base/BaseConfiguration.js';
import '@mathjax/src/js/input/tex/ams/AmsConfiguration.js';
import '@mathjax/src/js/input/tex/newcommand/NewcommandConfiguration.js';
import '@mathjax/src/js/input/tex/noundefined/NoUndefinedConfiguration.js';

const EM = 16;
const EX = 8;
const WIDTH = 80 * EM;

function readStdin() {
  return readFileSync(0, 'utf8');
}

function payloadFromStdin() {
  const raw = readStdin().trim();
  if (!raw) {
    return {items: []};
  }
  return JSON.parse(raw);
}

function createDocument() {
  const adaptor = liteAdaptor({fontSize: EM});
  RegisterHTMLHandler(adaptor);
  const tex = new TeX({
    packages: ['base', 'ams', 'newcommand', 'noundefined'],
    formatError(_jax, error) {
      throw error;
    }
  });
  const chtml = new CHTML({
    fontURL: './math/woff2'
  });
  const html = mathjax.document('', {
    InputJax: tex,
    OutputJax: chtml
  });
  return {adaptor, chtml, html};
}

async function renderItems(items) {
  const {adaptor, chtml, html} = createDocument();
  const rendered = [];
  const errors = [];
  for (const item of items) {
    try {
      const node = await html.convertPromise(item.tex, {
        display: Boolean(item.display),
        em: EM,
        ex: EX,
        containerWidth: WIDTH
      });
      rendered.push({
        id: item.id,
        html: adaptor.outerHTML(node)
      });
    } catch (error) {
      errors.push({
        id: item.id,
        message: String(error && error.message ? error.message : error)
      });
    }
  }
  return {
    rendered,
    errors,
    css: adaptor.cssText(chtml.styleSheet(html))
  };
}

async function main() {
  if (process.argv.includes('--self-test')) {
    const result = await renderItems([
      {id: 'inline', tex: 'a^2 + b^2 = c^2', display: false},
      {id: 'display', tex: '\\\\frac{1}{n}\\\\sum_{i=1}^{n} x_i', display: true}
    ]);
    if (result.errors.length) {
      console.error(JSON.stringify(result));
      process.exit(1);
    }
    if (!result.rendered[0].html.includes('mjx-container')) {
      console.error('MathJax self-test did not produce CHTML output');
      process.exit(1);
    }
    console.log('render_math: self-test passed');
    return;
  }

  const payload = payloadFromStdin();
  const result = await renderItems(Array.isArray(payload.items) ? payload.items : []);
  console.log(JSON.stringify(result));
  if (result.errors.length) {
    process.exit(1);
  }
}

main().catch((error) => {
  console.error(String(error && error.stack ? error.stack : error));
  process.exit(1);
});
```

- [ ] **Step 2: Run the self-test**

Run:

```bash
npm ci --ignore-scripts --no-audit --no-fund
npm run raya-render-math -- --self-test
```

Expected: `render_math: self-test passed`.

- [ ] **Step 3: Run a JSON conversion smoke check**

Run:

```bash
printf '%s\n' '{"items":[{"id":"one","tex":"\\\\int_0^1 x^2 dx","display":true}]}' | npm run raya-render-math --
```

Expected: JSON output contains `"id":"one"`, `"mjx-container"`, and `"css"`.

## Task 4: Add Python Math Renderer Adapter

**Files:**
- Create: `packages/static/src/raya_static/math_renderer.py`
- Test: `tests/contracts/test_math_renderer.py`

- [ ] **Step 1: Write failing adapter tests**

Create `tests/contracts/test_math_renderer.py`:

```python
from __future__ import annotations

from pathlib import Path

from raya_schema import ValidationReport
from raya_static.math_renderer import MathItem, MathRenderer


def test_math_renderer_typesets_inline_and_display_math() -> None:
    report = ValidationReport(context="test")
    renderer = MathRenderer()

    result = renderer.render_many(
        [
            MathItem(id="inline-1", tex="a^2 + b^2 = c^2", display=False, source_path=Path("course/0_index.md")),
            MathItem(id="display-1", tex="\\\\frac{1}{n}\\\\sum_{i=1}^{n} x_i", display=True, source_path=Path("course/0_index.md")),
        ],
        report=report,
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert "mjx-container" in result.html_by_id["inline-1"]
    assert "mjx-container" in result.html_by_id["display-1"]
    assert "mjx-container" in result.css


def test_math_renderer_reports_conversion_errors() -> None:
    report = ValidationReport(context="test")
    renderer = MathRenderer()

    result = renderer.render_many(
        [
            MathItem(id="broken", tex="\\\\frac{1", display=True, source_path=Path("course/0_index.md")),
        ],
        report=report,
    )

    assert not report.ok
    assert result.html_by_id == {}
    assert any(
        diagnostic.message == "Math rendering failed"
        and diagnostic.path == Path("course/0_index.md")
        and diagnostic.field == "math:broken"
        for diagnostic in report.diagnostics
    )
```

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_math_renderer.py
```

Expected: import failure because `raya_static.math_renderer` does not exist.

- [ ] **Step 2: Implement adapter dataclasses and subprocess bridge**

Create `packages/static/src/raya_static/math_renderer.py`:

```python
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from raya_schema import ValidationReport


ROOT = Path(__file__).resolve().parents[4]
RENDER_SCRIPT = ROOT / "packages" / "static" / "scripts" / "render_math.mjs"


@dataclass(frozen=True)
class MathItem:
    id: str
    tex: str
    display: bool
    source_path: Path


@dataclass(frozen=True)
class MathRenderResult:
    html_by_id: dict[str, str]
    css: str


class MathRenderer:
    def __init__(self, node: str = "node", script: Path = RENDER_SCRIPT) -> None:
        self._node = node
        self._script = script

    def render_many(
        self,
        items: list[MathItem],
        *,
        report: ValidationReport,
    ) -> MathRenderResult:
        if not items:
            return MathRenderResult(html_by_id={}, css="")
        payload = {
            "items": [
                {"id": item.id, "tex": item.tex, "display": item.display}
                for item in items
            ]
        }
        completed = subprocess.run(
            [self._node, str(self._script)],
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.stdout.strip():
            try:
                data = json.loads(completed.stdout)
            except json.JSONDecodeError:
                self._add_process_error(report, items, completed)
                return MathRenderResult(html_by_id={}, css="")
        else:
            self._add_process_error(report, items, completed)
            return MathRenderResult(html_by_id={}, css="")

        item_by_id = {item.id: item for item in items}
        for error in data.get("errors", []):
            item_id = str(error.get("id", "unknown"))
            source = item_by_id.get(item_id)
            report.add_error(
                "Math rendering failed",
                path=source.source_path if source is not None else None,
                field=f"math:{item_id}",
                next_action=str(error.get("message", "Fix the TeX expression")),
            )
        html_by_id = {
            str(item["id"]): str(item["html"])
            for item in data.get("rendered", [])
            if "id" in item and "html" in item
        }
        return MathRenderResult(html_by_id=html_by_id, css=str(data.get("css", "")))

    def _add_process_error(
        self,
        report: ValidationReport,
        items: list[MathItem],
        completed: subprocess.CompletedProcess[str],
    ) -> None:
        detail = completed.stderr.strip() or completed.stdout.strip() or "No output"
        for item in items:
            report.add_error(
                "Math renderer process failed",
                path=item.source_path,
                field=f"math:{item.id}",
                next_action=detail,
            )
```

- [ ] **Step 3: Run adapter tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_math_renderer.py
```

Expected: tests pass.

## Task 5: Integrate MathJax Output Into Markdown Rendering

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Test: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Update rich renderer tests to expect MathJax output**

Change `tests/contracts/test_static_builder.py::test_render_fixture_rich_markdown_baseline` assertions:

```python
assert "mjx-container" in html
assert "a^2 + b^2 = c^2" not in _visible_text(html)
assert '<span class="math inline">a^2 + b^2 = c^2</span>' not in html
assert "mjx-container" in nested_html
assert '<span class="math inline">x_i</span>' not in nested_html
```

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_rich_markdown_baseline
```

Expected: failure because the renderer still emits raw math spans.

- [ ] **Step 2: Extend `rendering.py` to collect math tokens**

Modify `RichMarkdownRenderer.__init__` to accept an optional math renderer result map:

```python
from raya_static.math_renderer import MathItem, MathRenderer, MathRenderResult
```

Add renderer rules:

```python
self._md.renderer.rules["math_inline"] = self._render_math_inline
self._md.renderer.rules["math_block"] = self._render_math_block
```

Replace `self._md.render(prepared_body, env)` in `render()` with parse and render:

```python
tokens = self._md.parse(prepared_body, env)
math_items = _collect_math_items(tokens, source_path=self._source_path)
math_result = self._math_renderer.render_many(math_items, report=self._report)
env["raya_math_html"] = math_result.html_by_id
env["raya_math_css"] = math_result.css
html_fragment = self._md.renderer.render(tokens, self._md.options, env)
```

Add token rendering helpers:

```python
def _render_math_inline(self, tokens: list[Token], idx: int, options: dict, env: dict) -> str:
    item_id = _math_token_id(tokens[idx], idx)
    rendered = env.get("raya_math_html", {}).get(item_id)
    if rendered:
        return rendered
    return f'<code class="raya-math-fallback">{html.escape(tokens[idx].content)}</code>'


def _render_math_block(self, tokens: list[Token], idx: int, options: dict, env: dict) -> str:
    item_id = _math_token_id(tokens[idx], idx)
    rendered = env.get("raya_math_html", {}).get(item_id)
    if rendered:
        return rendered + "\n"
    return f'<pre class="raya-math-fallback">{html.escape(tokens[idx].content)}</pre>\n'
```

Add collection helper:

```python
def _collect_math_items(tokens: list[Token], source_path: Path) -> list[MathItem]:
    items: list[MathItem] = []
    for index, token in enumerate(_walk_tokens(tokens)):
        if token.type in {"math_inline", "math_block"}:
            item_id = _math_token_id(token, index)
            items.append(
                MathItem(
                    id=item_id,
                    tex=token.content.strip(),
                    display=token.type == "math_block",
                    source_path=source_path,
                )
            )
    return items
```

Add `_walk_tokens()` to recurse through inline children.

- [ ] **Step 3: Pass report/source path through builder**

Change `_render_page()` signature in `builder.py`:

```python
def _render_page(
    *,
    page: ContentPage,
    content_model: ContentModel,
    pages_by_source: dict[Path, ContentPage],
    pages_by_reference: dict[str, ContentPage],
    course_root: Path,
    source_dir: Path,
    course_title: str,
    language: str,
    official_counts: dict[str, dict[str, int]],
    page_references: list[SourceReference],
    reviewed_by_reference: dict[str, ReviewedOutput],
    report: ValidationReport,
    math_renderer: MathRenderer,
) -> str:
```

Change the `render_markdown_body()` call:

```python
render_markdown_body(
    page.body,
    generated_index=generated_index,
    resolve_href=lambda href: _resolve_markdown_href(
        page,
        href,
        pages_by_source,
        pages_by_reference,
        course_root,
        source_dir,
    ),
    source_path=page.source_path,
    report=report,
    math_renderer=math_renderer,
)
```

In `build_course()`, create the renderer before the page loop:

```python
math_renderer = MathRenderer()
```

Pass `report=report` and `math_renderer=math_renderer` into `_render_page()`.

- [ ] **Step 4: Stop build when math diagnostics fail**

After each `_render_page()` call and before writing output, check:

```python
page_html = _render_page(
    page=page,
    content_model=content_model,
    pages_by_source=pages_by_source,
    pages_by_reference=pages_by_reference,
    course_root=root,
    source_dir=source_dir,
    course_title=str(config["title"]),
    language=str(config["language"]),
    official_counts=official_counts,
    page_references=references_by_page.get(page.id, []),
    reviewed_by_reference=reviewed_by_reference,
    report=report,
    math_renderer=math_renderer,
)
if not report.ok:
    return report
output_file.write_text(page_html, encoding="utf-8")
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_math_renderer.py tests/contracts/test_static_builder.py::test_render_fixture_rich_markdown_baseline
```

Expected: tests pass and generated HTML contains `mjx-container`.

## Task 6: Write Math CSS And Local Support Assets

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Test: `tests/contracts/test_static_builder.py`
- Test: `tests/e2e/test_static_read_path.py`

- [ ] **Step 1: Add failing CSS/static asset assertions**

Update static-read-path test for render fixture:

```python
math_css = _fetch_text(f"{base_url}/_raya/render/math/mathjax.css")
assert "mjx-container" in math_css
assert "_raya/render/math/mathjax.css" in root_html
assert "../_raya/render/math/mathjax.css" in nested_html
```

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_static_read_path.py::test_render_fixture_static_read_path_serves_pages_and_assets
```

Expected: failure because no math CSS file is written.

- [ ] **Step 2: Collect math CSS during rendering**

Add a per-build collector in `builder.py`:

```python
math_css_chunks: list[str] = []
```

After rendering each page, append non-empty MathJax CSS from the renderer. The simplest implementation is to add a `css_chunks` list to `MathRenderer`:

```python
class MathRenderer:
    def __init__(self, node: str = "node", script: Path = RENDER_SCRIPT) -> None:
        self._node = node
        self._script = script
        self.css_chunks: list[str] = []
```

Then in `render_many()`:

```python
css = str(data.get("css", ""))
if css and css not in self.css_chunks:
    self.css_chunks.append(css)
return MathRenderResult(html_by_id=html_by_id, css=css)
```

- [ ] **Step 3: Write math CSS under the static render resource path**

Add constants in `builder.py`:

```python
MATH_STYLESHEET_PATH = Path(STATIC_RESOURCE_DIR) / "render" / "math" / "mathjax.css"
```

After page rendering and before manifest validation:

```python
_write_math_render_resources(site_dir, math_renderer, report)
```

Add:

```python
def _write_math_render_resources(
    site_dir: Path,
    math_renderer: MathRenderer,
    report: ValidationReport,
) -> None:
    math_dir = site_dir / MATH_STYLESHEET_PATH.parent
    math_dir.mkdir(parents=True, exist_ok=True)
    report.wrote_output(math_dir)
    css_path = site_dir / MATH_STYLESHEET_PATH
    css = "\n".join(math_renderer.css_chunks).strip()
    css_path.write_text(css + "\n", encoding="utf-8")
    report.wrote_output(css_path)
```

- [ ] **Step 4: Link math CSS from pages**

In `_render_page()`, add:

```python
math_stylesheet_href = _relative_href(page.output_path, str(MATH_STYLESHEET_PATH))
```

In the `<head>` list, after `rich.css`:

```python
f'<link rel="stylesheet" href="{html.escape(math_stylesheet_href)}">',
```

- [ ] **Step 5: Run focused static path tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_static_read_path.py::test_render_fixture_static_read_path_serves_pages_and_assets
```

Expected: test passes and math CSS is served from `site/_raya/render/math/mathjax.css`.

## Task 7: Add Math Failure Fixtures And Diagnostics

**Files:**
- Create: `examples/courses/invalid/broken-math-expression/raya.yaml`
- Create: `examples/courses/invalid/broken-math-expression/course/0_index.md`
- Create: `examples/courses/invalid/unclosed-display-math/raya.yaml`
- Create: `examples/courses/invalid/unclosed-display-math/course/0_index.md`
- Test: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add invalid math fixtures**

Create `examples/courses/invalid/broken-math-expression/raya.yaml`:

```yaml
course_id: broken-math-expression
title: Broken Math Expression
description: Invalid fixture for MathJax conversion diagnostics.
language: en
source: course
artifact: artifact
```

Create `examples/courses/invalid/broken-math-expression/course/0_index.md`:

```markdown
---
id: broken-math-expression
title: Broken Math Expression
summary: Invalid fixture for MathJax conversion diagnostics.
status: ready
---
# Broken Math Expression

This display expression has malformed TeX:

$$
\frac{1
$$
```

Create `examples/courses/invalid/unclosed-display-math/raya.yaml` with the same shape and course ID `unclosed-display-math`.

Create `examples/courses/invalid/unclosed-display-math/course/0_index.md`:

```markdown
---
id: unclosed-display-math
title: Unclosed Display Math
summary: Invalid fixture for display math delimiter diagnostics.
status: ready
---
# Unclosed Display Math

The display delimiter is never closed.

$$
\sum_i x_i
```

- [ ] **Step 2: Add diagnostic tests**

Add to `tests/contracts/test_static_builder.py`:

```python
def test_build_stops_when_mathjax_expression_fails(tmp_path: Path) -> None:
    source = ROOT / "examples" / "courses" / "invalid" / "broken-math-expression"
    course = tmp_path / "broken-math-expression"
    shutil.copytree(source, course)

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message == "Math rendering failed"
        and diagnostic.field.startswith("math:")
        and diagnostic.path == course / "course" / "0_index.md"
        for diagnostic in report.diagnostics
    )


def test_build_stops_when_display_math_delimiter_is_unclosed(tmp_path: Path) -> None:
    source = ROOT / "examples" / "courses" / "invalid" / "unclosed-display-math"
    course = tmp_path / "unclosed-display-math"
    shutil.copytree(source, course)

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message in {
            "Malformed display math delimiter",
            "Math rendering failed",
        }
        and diagnostic.path == course / "course" / "0_index.md"
        for diagnostic in report.diagnostics
    )
```

- [ ] **Step 3: Add delimiter validation if parser leaves unclosed display math as text**

If the unclosed display math fixture does not produce a MathJax failure, add this validation to `rendering.py`:

```python
_DISPLAY_DELIMITER_RE = re.compile(r"(?m)^\\s*\\$\\$\\s*$")


def malformed_display_math_delimiters(body: str) -> bool:
    text = _without_fenced_blocks(body)
    return len(_DISPLAY_DELIMITER_RE.findall(text)) % 2 == 1
```

Then in `_validate_rich_markdown_inputs()`:

```python
if malformed_display_math_delimiters(page.body):
    report.add_error(
        "Malformed display math delimiter",
        path=page.source_path,
        field="math:display-delimiter",
        next_action="Close the display math block with a matching $$ delimiter",
    )
```

- [ ] **Step 4: Run diagnostic tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_stops_when_mathjax_expression_fails tests/contracts/test_static_builder.py::test_build_stops_when_display_math_delimiter_is_unclosed
```

Expected: tests pass and no artifact success is written for invalid math.

## Task 8: Expand Representative Fixture Coverage

**Files:**
- Modify: `examples/courses/render-fixture/course/0_index.md`
- Modify: `examples/courses/render-fixture/course/1_static_path/0_index.md`
- Test: `tests/contracts/test_static_builder.py`
- Test: `tests/e2e/test_static_read_path.py`

- [ ] **Step 1: Replace current shallow math examples with serious fixture math**

In `examples/courses/render-fixture/course/0_index.md`, change the math table row to:

```markdown
| Math | Typeset MathJax output for inline, display, aligned, matrix, cases, probability, and optimization notation. |
```

Add this content after the existing first display equation:

```markdown
Inline notation includes gradients $\nabla J(\theta)$, probability $P(Y = 1 \mid X = x)$, and vector norms $\lVert x \rVert_2$.

$$
\begin{aligned}
\theta_{t+1} &= \theta_t - \eta \nabla J(\theta_t) \\
J(\theta) &= \frac{1}{m}\sum_{i=1}^{m}(h_\theta(x^{(i)}) - y^{(i)})^2
\end{aligned}
$$

$$
A =
\begin{bmatrix}
1 & 0 \\
0 & 1
\end{bmatrix}
$$

$$
f(x) =
\begin{cases}
x^2 & \text{if } x \ge 0 \\
-x & \text{if } x < 0
\end{cases}
$$
```

- [ ] **Step 2: Add nested math and image/link stress**

In `examples/courses/render-fixture/course/1_static_path/0_index.md`, add:

```markdown
Nested display math must use the same local MathJax resources:

$$
\operatorname*{arg\,min}_{\theta \in \mathbb{R}^d}
\frac{1}{n}\sum_{i=1}^{n}\ell(f_\theta(x_i), y_i)
$$
```

- [ ] **Step 3: Update fixture assertions**

In `test_render_fixture_rich_markdown_baseline`, assert:

```python
assert "Gradient Descent" not in html
assert "\\theta_{t+1}" not in _visible_text(html)
assert "mjx-container" in html
assert "mjx-container" in nested_html
assert "arg" in nested_html
```

Keep existing checks for code, escaped raw HTML, callouts, footnotes, anchors, links, and assets.

- [ ] **Step 4: Run focused fixture tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_rich_markdown_baseline tests/e2e/test_static_read_path.py::test_render_fixture_static_read_path_serves_pages_and_assets
```

Expected: tests pass.

## Task 9: Add Browser Verification For Real Math Rendering

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add failing Playwright math assertions**

Add a new test:

```python
def test_preview_renders_mathjax_without_external_requests(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        base_url = handle.base_url
        assert base_url is not None
        external_requests: list[str] = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.on(
                    "request",
                    lambda request: external_requests.append(request.url)
                    if request.url.startswith(("http://", "https://"))
                    and not request.url.startswith(base_url)
                    else None,
                )
                page.goto(f"{base_url}/index.html", wait_until="networkidle")
                assert page.locator("mjx-container").count() >= 4
                assert page.locator(".math.inline").count() == 0
                assert page.locator(".math.block").count() == 0
                _assert_no_horizontal_overflow(page)
            finally:
                browser.close()
        assert external_requests == []
    finally:
        handle.close()
```

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_renders_mathjax_without_external_requests
```

Expected: failure until MathJax output and local assets are integrated.

- [ ] **Step 2: Make the test pass**

Complete Tasks 5 and 6 first. Then rerun:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_renders_mathjax_without_external_requests
```

Expected: test passes with no external requests.

## Task 10: Update Documentation And Config

**Files:**
- Modify: `docs/foundation/17_rendering_execution_plan.md`
- Modify: `docs/foundation/18_known_missing_work.md`
- Modify: `docs/foundation/06_artifact_contract.md` if math assets need artifact wording
- Modify: `openspec/config.yaml`
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Modify rendered docs under `docs/render-content/`

- [ ] **Step 1: Update foundation rendering plan**

Change the Phase 1 accepted baseline from TeX preservation to build-time MathJax:

```markdown
- Inline math such as `$a+b$` and display math delimited with `$$` render through
  build-time MathJax into pre-rendered static HTML. The original TeX remains
  available for diagnostics or inspection, but successful pages do not show raw
  TeX as the default visual math surface.
- MathJax support is a renderer dependency used during `raya build`, not a
  course runtime. `raya preview` and web deployment serve the same generated
  files from `artifact/site/`.
```

- [ ] **Step 2: Update OpenSpec config**

Add this rule under `rules.tasks` in `openspec/config.yaml`:

```yaml
    - Include build-time math rendering tests, no-external-renderer-asset browser checks, and Docker dependency coverage when changes affect math rendering or renderer support resources.
```

- [ ] **Step 3: Update role docs in English and Spanish**

Add compact guidance to each role page. English professor example:

```markdown
Use normal Markdown math delimiters for course notation. `raya build` renders
supported TeX/LaTeX math into the static artifact, and `raya preview` shows the
same files that can be deployed online. If math fails, fix the source expression
before publishing; do not rely on browser-only rendering or CDN scripts.
```

Spanish professor example:

```markdown
Usa los delimitadores normales de Markdown para la notacion matematica.
`raya build` renderiza la matematica TeX/LaTeX soportada dentro del artefacto
estatico, y `raya preview` muestra los mismos archivos que se pueden desplegar
en linea. Si la matematica falla, corrige la expresion fuente antes de publicar;
no dependas de renderizado solo en el navegador ni de scripts CDN.
```

Keep technical identifiers in English.

- [ ] **Step 4: Update README/AGENTS/CLAUDE**

Add the build dependency and authoring boundary:

```markdown
Math rendering is build-time and static-first. The reference Docker path
contains Node and MathJax renderer dependencies; local `uv` users must run
`npm ci` before building math-heavy pages. Do not add CDN MathJax scripts,
browser-only rendering, or course-runtime execution to make math appear.
```

- [ ] **Step 5: Verify docs render**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate docs
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build docs
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya artifacts inspect docs/artifact
```

Expected: all pass.

## Task 11: Full Verification And Archive

**Files:**
- Modify: `openspec/changes/harden-static-renderer/tasks.md`
- Archive path after completion: `openspec/changes/archive/YYYY-MM-DD-harden-static-renderer/`

- [ ] **Step 1: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_math_renderer.py tests/contracts/test_static_builder.py tests/e2e/test_static_read_path.py tests/e2e/test_preview_static_read_path.py tests/contracts/test_dockerfile.py
```

Expected: all selected tests pass.

- [ ] **Step 2: Run full local check**

Run:

```bash
./scripts/check.sh
```

Expected: `check: passed`.

- [ ] **Step 3: Rebuild Docker image and run Docker check**

Run:

```bash
docker compose build dev
./scripts/check-docker.sh
```

Expected: Docker build succeeds and `check-docker: passed`.

- [ ] **Step 4: Validate OpenSpec**

Run:

```bash
openspec validate harden-static-renderer --strict
openspec validate --specs --strict
git diff --check
```

Expected: change validation passes, all specs pass, and whitespace check has no output.

- [ ] **Step 5: Mark tasks complete**

Update `openspec/changes/harden-static-renderer/tasks.md` so each implemented task uses `- [x]`.

- [ ] **Step 6: Archive**

Run:

```bash
openspec archive harden-static-renderer --yes
```

Expected: delta specs sync into `openspec/specs/` and the change moves to `openspec/changes/archive/<date>-harden-static-renderer/`.

- [ ] **Step 7: Run post-archive verification**

Run:

```bash
./scripts/check.sh
./scripts/check-docker.sh
openspec validate --specs --strict
git diff --check
git status --short
```

Expected: checks pass and `git status --short` shows only intentional implementation/archive changes before commit.

- [ ] **Step 8: Commit**

Run:

```bash
git add -A
git commit -m "Harden static renderer"
```

Expected: commit succeeds and `git status --short` is clean.

## Self-Review Notes

- Spec coverage: The plan covers build-time MathJax, strict failure policy, one static artifact for preview/deployment, images, links, code, browser checks, Docker/local workflow, role docs, config, and archive.
- Scope: The plan excludes official study-object panels and personal study state, matching the approved design.
- Type consistency: `MathItem`, `MathRenderResult`, and `MathRenderer.render_many()` are defined before integration tasks reference them.
- Verification: The plan includes red/green focused tests, local check, Docker check, OpenSpec validation, docs build/inspect, browser verification, and post-archive checks.
