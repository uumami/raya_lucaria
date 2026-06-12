# Renderer Debug Artifacts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional test-owned browser debug artifact workflow for rendered math/layout fixtures, plus role guidance for using it.

**Architecture:** Extend the existing Playwright e2e test helpers in `tests/e2e/test_preview_static_read_path.py` so renderer tests can capture screenshots and a compact JSON summary when `RAYA_RENDER_DEBUG_DIR` is set. Keep debug files outside source fixtures and generated course artifacts; they are evidence for humans and agents, not authority surfaces. Strengthen the existing render fixture and role docs without adding a public CLI command or OpenSpec change.

**Tech Stack:** Python 3.10, Pytest, Playwright/Chromium, `raya preview`, Glintstone static artifacts, Markdown role docs in English and Spanish.

---

## File Structure

- Modify: `tests/e2e/test_preview_static_read_path.py`
  - Owns browser-driven static-read-path checks.
  - Add focused helpers for optional renderer debug capture.
  - Add a TDD test that proves screenshots and `summary.json` are written only when requested.
- Modify: `examples/courses/render-fixture/course/0_index.md`
  - Add explicit fixture math authoring examples for `\renewcommand`, vectors, matrices, macros, and diagnostics-oriented edge cases.
  - Keep fixture labels clear and non-pedagogical.
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`
  - Document accepted math authoring and debug-artifact workflow by role, keeping language directories separate.

## Task 1: Add Optional Renderer Debug Capture To E2E Tests

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing test**

Add imports near the top:

```python
import json
```

Add this test after `test_render_fixture_math_is_visible_and_uses_only_local_assets`:

```python
def test_render_fixture_debug_artifacts_are_written_when_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    debug_dir = tmp_path / "renderer-debug"
    monkeypatch.setenv("RAYA_RENDER_DEBUG_DIR", str(debug_dir))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    external_requests: list[str] = []
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        base_url = handle.base_url
        assert base_url is not None

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 390, "height": 844})
                page.on(
                    "request",
                    lambda request: _record_external_request(
                        request.url,
                        base_url,
                        external_requests,
                    ),
                )
                try:
                    page.goto(f"{base_url}/index.html", wait_until="networkidle")
                    _assert_no_horizontal_overflow(page)
                    _assert_visible_mathjax_output(page, minimum=6)
                    _capture_render_debug_artifact(
                        page,
                        debug_dir=debug_dir,
                        page_name="index",
                        viewport_name="mobile",
                        viewport={"width": 390, "height": 844},
                        external_requests=external_requests,
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    screenshot = debug_dir / "mobile-index.png"
    summary_path = debug_dir / "summary.json"
    assert screenshot.is_file()
    assert screenshot.stat().st_size > 0
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["captures"][0]["page"] == "index"
    assert summary["captures"][0]["viewport"]["name"] == "mobile"
    assert summary["captures"][0]["mathjax_container_count"] >= 6
    assert summary["captures"][0]["raw_tex_visible"] is False
    assert summary["captures"][0]["horizontal_overflow"] <= 1
    assert summary["captures"][0]["external_requests"] == []
    assert summary["captures"][0]["screenshot"].endswith("mobile-index.png")
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_debug_artifacts_are_written_when_enabled
```

Expected: FAIL with `NameError: name '_capture_render_debug_artifact' is not defined`.

- [ ] **Step 3: Add the minimal implementation**

Add this helper near the existing e2e helper functions:

```python
def _capture_render_debug_artifact(
    page,
    *,
    debug_dir: Path,
    page_name: str,
    viewport_name: str,
    viewport: dict[str, int],
    external_requests: list[str],
) -> None:
    debug_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = debug_dir / f"{viewport_name}-{page_name}.png"
    page.screenshot(path=str(screenshot_path), full_page=True)
    visible_text = page.locator("body").inner_text()
    overflow = page.evaluate(
        "() => Math.ceil(document.documentElement.scrollWidth - window.innerWidth)"
    )
    capture = {
        "page": page_name,
        "url": page.url,
        "viewport": {
            "name": viewport_name,
            "width": viewport["width"],
            "height": viewport["height"],
        },
        "screenshot": str(screenshot_path),
        "mathjax_container_count": page.locator("mjx-container").count(),
        "raw_tex_visible": any(
            token in visible_text
            for token in ("\\rayaVec", "\\argmax", "a^2 + b^2 = c^2")
        ),
        "external_requests": sorted(set(external_requests)),
        "horizontal_overflow": overflow,
    }
    summary_path = debug_dir / "summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    else:
        summary = {"captures": []}
    summary["captures"].append(capture)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run the focused test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_debug_artifacts_are_written_when_enabled
```

Expected: PASS.

- [ ] **Step 5: Wire optional capture into the existing render fixture browser test**

In `test_render_fixture_math_is_visible_and_uses_only_local_assets`, after the browser checks for each loaded page, call the helper only when `RAYA_RENDER_DEBUG_DIR` is configured:

```python
debug_dir_value = os.environ.get("RAYA_RENDER_DEBUG_DIR")
debug_dir = Path(debug_dir_value) if debug_dir_value else None
```

Then after the root page assertions:

```python
                        if debug_dir is not None:
                            _capture_render_debug_artifact(
                                page,
                                debug_dir=debug_dir,
                                page_name="index",
                                viewport_name=_viewport_name(viewport),
                                viewport=viewport,
                                external_requests=external_requests,
                            )
```

And after the nested page assertions:

```python
                        if debug_dir is not None:
                            _capture_render_debug_artifact(
                                page,
                                debug_dir=debug_dir,
                                page_name="static-path",
                                viewport_name=_viewport_name(viewport),
                                viewport=viewport,
                                external_requests=external_requests,
                            )
```

Add this helper:

```python
def _viewport_name(viewport: dict[str, int]) -> str:
    if viewport["width"] <= 720:
        return "mobile"
    return "desktop"
```

- [ ] **Step 6: Run the existing render fixture browser test without debug capture**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_math_is_visible_and_uses_only_local_assets
```

Expected: PASS and no persistent screenshot output in the repository.

- [ ] **Step 7: Run the existing render fixture browser test with debug capture**

Run:

```bash
RAYA_RENDER_DEBUG_DIR="$(mktemp -d)" UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_math_is_visible_and_uses_only_local_assets
```

Expected: PASS and the temporary debug directory contains `desktop-index.png`, `desktop-static-path.png`, `mobile-index.png`, `mobile-static-path.png`, and `summary.json`.

- [ ] **Step 8: Commit Task 1**

Run:

```bash
git add tests/e2e/test_preview_static_read_path.py
git commit -m "Add renderer debug capture test artifacts"
```

## Task 2: Strengthen Render Fixture Math Examples

**Files:**
- Modify: `examples/courses/render-fixture/course/0_index.md`
- Test: `tests/contracts/test_static_builder.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing fixture assertion**

In `tests/contracts/test_static_builder.py`, inside `test_render_fixture_rich_markdown_baseline`, add assertions near the existing math checks:

```python
    assert "Macro Redefinition Fixture" in _visible_text(html)
    assert "\\renewcommand" not in _visible_text(html)
    assert "\\fixtureUnit" not in _visible_text(html)
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_rich_markdown_baseline
```

Expected: FAIL because `Macro Redefinition Fixture` is not present in the render fixture yet.

- [ ] **Step 3: Add the fixture authoring example**

Append this section after the existing probability/statistics fixture and before the Python code block:

```markdown
## Macro Redefinition Fixture

This fixture demonstrates page-local macro definition and redefinition without
making the fixture pedagogical canon:
$\newcommand{\fixtureUnit}{\mathrm{unit}}\renewcommand{\fixtureUnit}{\mathrm{u}}$.

Vectors, matrices, and redefined units should all render before publication:

$$
\rayaVec{v}_{\fixtureUnit}
=
\begin{bmatrix}
2 \\
-1
\end{bmatrix}
$$
```

- [ ] **Step 4: Run the focused contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_rich_markdown_baseline
```

Expected: PASS.

- [ ] **Step 5: Run the focused browser math test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_math_is_visible_and_uses_only_local_assets
```

Expected: PASS with no visible raw macro leakage.

- [ ] **Step 6: Commit Task 2**

Run:

```bash
git add examples/courses/render-fixture/course/0_index.md tests/contracts/test_static_builder.py
git commit -m "Extend render fixture macro examples"
```

## Task 3: Document Math Authoring And Debug Artifacts By Role

**Files:**
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update English professor guidance**

In `docs/guides/en/professors/index.md`, extend the rich static rendering paragraph with:

```markdown
For common course notation, prefer small page-local macros such as `\newcommand{\rayaVec}[1]{\mathbf{#1}}` and use them consistently after definition. Matrices such as `\begin{bmatrix} ... \end{bmatrix}`, aligned equations, cases, derivatives, integrals, probability notation, optimization notation, and `\renewcommand` for page-local adjustments are fixture-tested. Keep macro definitions close to the page that uses them so diagnostics point to the relevant source page.
```

- [ ] **Step 2: Update English contributor guidance**

In `docs/guides/en/contributors/index.md`, extend the rich static rendering paragraph with:

```markdown
When debugging browser-only renderer regressions, set `RAYA_RENDER_DEBUG_DIR` to a temporary directory before running the focused Playwright test. The renderer test may write screenshots and `summary.json` for desktop/mobile fixture pages. Treat those files as local evidence only; do not commit them and do not treat them as artifact authority.
```

- [ ] **Step 3: Update English student guidance**

In `docs/guides/en/students/index.md`, extend the static math paragraph with:

```markdown
If math appears as raw TeX commands such as `\begin{bmatrix}` or an unknown macro on a published page, treat that as a rendering problem to report to the course team, not as a step you need to fix in your browser.
```

- [ ] **Step 4: Update English agent guidance**

In `docs/guides/en/agents/index.md`, extend the rich static rendering paragraph with:

```markdown
For renderer debugging, use `RAYA_RENDER_DEBUG_DIR=/tmp/raya-render-debug UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_math_is_visible_and_uses_only_local_assets` to capture screenshots and `summary.json`. Use them as evidence for layout/math failures, but keep authority in source files, `manifest.json`, and manifest-declared `data/*.json`.
```

- [ ] **Step 5: Update Spanish professor guidance**

In `docs/guides/es/profesores/index.md`, extend the rich static rendering paragraph with:

```markdown
Para notacion comun de curso, prefiere macros pequenas locales a la pagina como `\newcommand{\rayaVec}[1]{\mathbf{#1}}` y usalas consistentemente despues de definirlas. Matrices como `\begin{bmatrix} ... \end{bmatrix}`, ecuaciones alineadas, cases, derivadas, integrales, notacion de probabilidad, notacion de optimizacion y `\renewcommand` para ajustes locales de pagina estan cubiertas por fixtures. Mantiene las definiciones de macros cerca de la pagina que las usa para que los diagnosticos apunten al source relevante.
```

- [ ] **Step 6: Update Spanish collaborator guidance**

In `docs/guides/es/colaboradores/index.md`, extend the rich static rendering paragraph with:

```markdown
Cuando depures regresiones del renderer visibles solo en browser, define `RAYA_RENDER_DEBUG_DIR` hacia un directorio temporal antes de correr el test Playwright enfocado. El test del renderer puede escribir screenshots y `summary.json` para paginas fixture desktop/mobile. Trata esos archivos como evidencia local solamente; no los commitees ni los trates como autoridad del artifact.
```

- [ ] **Step 7: Update Spanish student guidance**

In `docs/guides/es/estudiantes/index.md`, extend the static math paragraph with:

```markdown
Si la math aparece como comandos TeX crudos como `\begin{bmatrix}` o una macro desconocida en una pagina publicada, tratalo como un problema de rendering para reportar al equipo del curso, no como un paso que debas arreglar en tu browser.
```

- [ ] **Step 8: Update Spanish agent guidance**

In `docs/guides/es/agentes/index.md`, extend the rich static rendering paragraph with:

```markdown
Para depurar el renderer, usa `RAYA_RENDER_DEBUG_DIR=/tmp/raya-render-debug UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_math_is_visible_and_uses_only_local_assets` para capturar screenshots y `summary.json`. Usalos como evidencia de fallas de layout/math, pero conserva la autoridad en archivos source, `manifest.json` y `data/*.json` declarados por manifest.
```

- [ ] **Step 9: Run docs validation/build**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate docs
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build docs
```

Expected: both commands exit 0.

- [ ] **Step 10: Commit Task 3**

Run:

```bash
git add docs/guides/en docs/guides/es
git commit -m "Document renderer debug workflow"
```

## Task 4: Final Verification And Review

**Files:**
- Verify all files changed in Tasks 1-3.

- [ ] **Step 1: Run focused renderer checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_rich_markdown_baseline tests/e2e/test_preview_static_read_path.py::test_render_fixture_math_is_visible_and_uses_only_local_assets tests/e2e/test_preview_static_read_path.py::test_render_fixture_debug_artifacts_are_written_when_enabled
```

Expected: all selected tests pass.

- [ ] **Step 2: Build the render fixture**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
```

Expected: build exits 0 and writes the render fixture artifact.

- [ ] **Step 3: Run the host archive gate**

Run:

```bash
./scripts/check.sh
```

Expected: archive gate exits 0.

- [ ] **Step 4: Run Docker verification if practical**

Run:

```bash
./scripts/check-docker.sh
```

Expected: Docker reference verification exits 0. If Docker is unavailable, record the exact failure and do not claim Docker verification passed.

- [ ] **Step 5: Request code review for the completed implementation**

Use `superpowers:requesting-code-review`. Provide the reviewer:

```text
DESCRIPTION: Added optional renderer debug screenshots/summary for Playwright tests, strengthened render fixture macro examples, and documented math/debug workflows in English and Spanish role docs.
PLAN_OR_REQUIREMENTS: docs/superpowers/specs/2026-06-12-renderer-debug-artifacts-design.md and docs/superpowers/plans/2026-06-12-renderer-debug-artifacts.md.
BASE_SHA: e143b07
HEAD_SHA: $(git rev-parse HEAD)
```

- [ ] **Step 6: Address review findings**

Fix Critical and Important findings before final response. Re-run the focused verification command from Step 1 after any changes.

- [ ] **Step 7: Final status**

Run:

```bash
git status --short
git log --oneline -5
```

Expected: working tree is clean after commits, or any remaining uncommitted files are intentionally reported.
