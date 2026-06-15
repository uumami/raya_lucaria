# Preview Render Debug Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `raya preview <course> --render-debug <output-dir>` so contributors and agents can capture browser screenshots and renderer inspection summaries from the same static site used by local preview.

**Architecture:** Keep preview validation/build/serving in `packages/cli/src/raya_cli/preview.py`. Add a small CLI-owned browser capture module, `packages/cli/src/raya_cli/render_debug.py`, that receives an already-running preview URL and writes external debug artifacts. Wire the option through `packages/cli/src/raya_cli/main.py` so normal preview behavior remains unchanged and render debug mode closes the server before exiting.

**Tech Stack:** Python 3.10, argparse, existing `ValidationReport`, Playwright sync API when installed, Chromium-compatible browser discovered from `RAYA_TEST_BROWSER` or common executable names, pytest, local `uv`, Docker verification path.

---

## File Structure

- Create `packages/cli/src/raya_cli/render_debug.py`.
  - Own browser executable discovery, page/viewport constants, screenshot capture, raw TeX marker detection, external request capture, stale debug file reset, and `summary.json` writing.
  - Import Playwright lazily inside the capture function so ordinary `raya preview` and `raya --help` do not require Playwright import at module import time.
- Modify `packages/cli/src/raya_cli/main.py`.
  - Add `--render-debug <output-dir>` to `preview`.
  - Call the render debug helper only after `create_preview(...)` succeeds and before normal `serve_forever()`.
  - Print the render debug output directory through the preview summary.
- Modify `packages/cli/src/raya_cli/preview.py`.
  - Add an optional `render_debug_dir` field to `PreviewHandle` only if needed by printing/reporting.
  - Do not move browser logic into preview.
- Modify `tests/contracts/test_cli.py`.
  - Add a CLI help/argument test that proves `--render-debug` is exposed.
  - Add a subprocess test for `raya preview <course> --render-debug <dir>` that writes expected screenshots and summary records.
- Modify `tests/e2e/test_preview_static_read_path.py`.
  - Replace duplicate test-local render debug capture helpers with imports from `raya_cli.render_debug` where practical.
  - Keep existing e2e assertions proving no raw TeX, no external requests, and no overflow.
- Modify `docs/guides/en/contributors/index.md`, `docs/guides/en/agents/index.md`, `docs/guides/es/colaboradores/index.md`, and `docs/guides/es/agentes/index.md`.
  - Document `raya preview --render-debug`.
  - Keep source/artifact authority language explicit.

## Task 1: CLI Surface Red Test

**Files:**
- Modify: `tests/contracts/test_cli.py`
- Later modify: `packages/cli/src/raya_cli/main.py`

- [ ] **Step 1: Write the failing help test**

Add this test near the other CLI help tests in `tests/contracts/test_cli.py`:

```python
def test_cli_preview_help_lists_render_debug_option() -> None:
    result = run_cli("preview", "--help")

    assert result.returncode == 0
    assert "--render-debug" in result.stdout
    assert "renderer debug screenshots" in result.stdout
```

- [ ] **Step 2: Run the help test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_cli.py::test_cli_preview_help_lists_render_debug_option
```

Expected: FAIL because `--render-debug` is not listed in preview help.

- [ ] **Step 3: Add the CLI option**

In `packages/cli/src/raya_cli/main.py`, add this argument after the existing `--dry-run` preview argument:

```python
    preview_parser.add_argument(
        "--render-debug",
        metavar="DIR",
        help=(
            "Capture renderer debug screenshots and summary JSON into DIR, "
            "then stop the preview server"
        ),
    )
```

- [ ] **Step 4: Run the help test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_cli.py::test_cli_preview_help_lists_render_debug_option
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add tests/contracts/test_cli.py packages/cli/src/raya_cli/main.py
git commit -m "Expose preview render debug option"
```

## Task 2: Render Debug Helper Red Test

**Files:**
- Create: `packages/cli/src/raya_cli/render_debug.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing direct helper test**

Add this import at the top of `tests/e2e/test_preview_static_read_path.py` with the other imports:

```python
from raya_cli.render_debug import capture_render_debug
```

Add this test after `test_render_fixture_debug_summary_is_reset_between_runs`:

```python
def test_capture_render_debug_writes_screenshots_and_summary(tmp_path: Path) -> None:
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    debug_dir = tmp_path / "renderer-debug"

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        assert handle.base_url is not None
        result = capture_render_debug(
            base_url=handle.base_url,
            site_dir=course / "artifact" / "site",
            output_dir=debug_dir,
        )
    finally:
        handle.close()

    assert result.ok, [diagnostic.format() for diagnostic in result.diagnostics]
    expected_screenshots = {
        "desktop-index.png",
        "mobile-index.png",
        "desktop-static-path.png",
        "mobile-static-path.png",
    }
    assert {path.name for path in debug_dir.glob("*.png")} == expected_screenshots
    assert all((debug_dir / name).stat().st_size > 0 for name in expected_screenshots)

    summary = json.loads((debug_dir / "summary.json").read_text(encoding="utf-8"))
    assert len(summary["captures"]) == 4
    assert {Path(capture["screenshot"]).name for capture in summary["captures"]} == expected_screenshots
    assert all(capture["raw_tex_visible"] is False for capture in summary["captures"])
    assert all(capture["raw_tex_markers"] == [] for capture in summary["captures"])
    assert all(capture["external_requests"] == [] for capture in summary["captures"])
    assert all(capture["horizontal_overflow"] <= 1 for capture in summary["captures"])
```

- [ ] **Step 2: Run the helper test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary
```

Expected: FAIL with `ModuleNotFoundError: No module named 'raya_cli.render_debug'`.

- [ ] **Step 3: Create the minimal helper implementation**

Create `packages/cli/src/raya_cli/render_debug.py`:

```python
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from raya_schema import ValidationReport


RENDER_DEBUG_PAGE_NAMES = ("index", "static-path")
RENDER_DEBUG_VIEWPORTS = (
    {"width": 1280, "height": 900},
    {"width": 390, "height": 844},
)
RENDER_RAW_TEX_MARKERS = (
    "\\rayaVec",
    "\\argmax",
    "\\renewcommand",
    "\\fixtureUnit",
    "\\begin{bmatrix}",
    "a^2 + b^2 = c^2",
)


def capture_render_debug(
    *,
    base_url: str,
    site_dir: str | Path,
    output_dir: str | Path,
) -> ValidationReport:
    report = ValidationReport(context="preview")
    site_root = Path(site_dir)
    debug_dir = Path(output_dir)
    _reset_render_debug_dir(debug_dir)

    browser_executable = _browser_executable(report)
    if browser_executable is None:
        return report

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        report.add_error(
            "Playwright is required for renderer debug capture",
            path=debug_dir,
            next_action="Install dev dependencies with uv sync --all-packages --dev or use ./scripts/check-docker.sh",
        )
        return report

    external_requests: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(browser_executable),
            headless=True,
            args=["--no-sandbox"],
        )
        try:
            for viewport in RENDER_DEBUG_VIEWPORTS:
                for page_name in _available_page_names(site_root):
                    page = browser.new_page(viewport=viewport)
                    page.on(
                        "request",
                        lambda request: _record_external_request(
                            request.url,
                            base_url,
                            external_requests,
                        ),
                    )
                    try:
                        page_url = _page_url(base_url, page_name)
                        page.goto(page_url, wait_until="networkidle")
                        capture = _capture_render_debug_artifact(
                            page,
                            debug_dir=debug_dir,
                            page_name=page_name,
                            viewport_name=_viewport_name(viewport),
                            viewport=viewport,
                            external_requests=external_requests,
                        )
                        _add_capture_diagnostics(report, debug_dir, capture)
                    finally:
                        page.close()
        finally:
            browser.close()

    report.wrote_output(debug_dir / "summary.json")
    for screenshot in debug_dir.glob("*.png"):
        report.wrote_output(screenshot)
    if report.ok:
        report.add_info(
            "Renderer debug artifacts written",
            path=debug_dir,
            next_action=f"Inspect screenshots and summary={debug_dir / 'summary.json'}",
        )
    return report


def _available_page_names(site_root: Path) -> list[str]:
    page_names = ["index"]
    if (site_root / "static-path" / "index.html").is_file():
        page_names.append("static-path")
    return page_names


def _page_url(base_url: str, page_name: str) -> str:
    if page_name == "index":
        return f"{base_url}/index.html"
    return f"{base_url}/{page_name}/index.html"


def _browser_executable(report: ValidationReport) -> Path | None:
    configured = os.environ.get("RAYA_TEST_BROWSER")
    if configured:
        path = Path(configured)
        if path.exists():
            return path
        report.add_error(
            "Configured Chromium-compatible browser does not exist",
            path=path,
            field="RAYA_TEST_BROWSER",
            next_action="Set RAYA_TEST_BROWSER to an existing Chromium-compatible executable",
        )
        return None

    for name in (
        "chromium",
        "chromium-browser",
        "google-chrome-stable",
        "google-chrome",
    ):
        resolved = shutil.which(name)
        if resolved is not None:
            return Path(resolved)
    report.add_error(
        "A Chromium-compatible browser is required for renderer debug capture",
        next_action="Use the reference Docker workflow or set RAYA_TEST_BROWSER=/path/to/browser",
    )
    return None


def _capture_render_debug_artifact(
    page,
    *,
    debug_dir: Path,
    page_name: str,
    viewport_name: str,
    viewport: dict[str, int],
    external_requests: list[str],
) -> dict[str, object]:
    screenshot_path = debug_dir / f"{viewport_name}-{page_name}.png"
    page.screenshot(path=str(screenshot_path), full_page=True)
    visible_text = page.locator("body").inner_text()
    raw_tex_markers = _raw_tex_markers(visible_text)
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
        "raw_tex_visible": bool(raw_tex_markers),
        "raw_tex_markers": raw_tex_markers,
        "external_requests": sorted(set(external_requests)),
        "horizontal_overflow": overflow,
    }
    _append_summary(debug_dir / "summary.json", capture)
    return capture


def _append_summary(summary_path: Path, capture: dict[str, object]) -> None:
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    else:
        summary = {"captures": []}
    summary["captures"].append(capture)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _add_capture_diagnostics(
    report: ValidationReport,
    debug_dir: Path,
    capture: dict[str, object],
) -> None:
    if capture["raw_tex_visible"]:
        report.add_error(
            "Renderer debug found visible raw TeX",
            path=debug_dir,
            field=str(capture["page"]),
            next_action=f"Inspect {capture['screenshot']} and fix build-time math diagnostics",
        )
    if capture["external_requests"]:
        report.add_error(
            "Renderer debug found external requests",
            path=debug_dir,
            field=str(capture["page"]),
            next_action="Keep renderer support files local under artifact/site/_raya/",
        )


def _reset_render_debug_dir(debug_dir: Path) -> None:
    debug_dir.mkdir(parents=True, exist_ok=True)
    for path in debug_dir.iterdir():
        if path.name == "summary.json" or path.name in _render_debug_screenshot_names():
            path.unlink()


def _render_debug_screenshot_names() -> set[str]:
    return {
        f"{_viewport_name(viewport)}-{page_name}.png"
        for viewport in RENDER_DEBUG_VIEWPORTS
        for page_name in RENDER_DEBUG_PAGE_NAMES
    }


def _raw_tex_markers(visible_text: str) -> list[str]:
    return [marker for marker in RENDER_RAW_TEX_MARKERS if marker in visible_text]


def _viewport_name(viewport: dict[str, int]) -> str:
    if viewport["width"] <= 720:
        return "mobile"
    return "desktop"


def _record_external_request(url: str, base_url: str, requests: list[str]) -> None:
    if not url.startswith(base_url):
        requests.append(url)
```

- [ ] **Step 4: Run the helper test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add packages/cli/src/raya_cli/render_debug.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add preview render debug capture helper"
```

## Task 3: Preview CLI Execution Red Test

**Files:**
- Modify: `tests/contracts/test_cli.py`
- Modify: `packages/cli/src/raya_cli/main.py`

- [ ] **Step 1: Write the failing CLI behavior test**

Add a render fixture constant near `MINIMAL` in `tests/contracts/test_cli.py`:

```python
RENDER_FIXTURE = ROOT / "examples" / "courses" / "render-fixture"
```

Add this test after `test_cli_build_success`:

```python
def test_cli_preview_render_debug_writes_artifacts_and_exits(tmp_path: Path) -> None:
    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    debug_dir = tmp_path / "renderer-debug"

    result = run_cli(
        "preview",
        str(course),
        "--port",
        "0",
        "--render-debug",
        str(debug_dir),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "render_debug=" in result.stdout
    assert str(debug_dir) in result.stdout
    assert (debug_dir / "desktop-index.png").stat().st_size > 0
    assert (debug_dir / "mobile-index.png").stat().st_size > 0
    summary = json.loads((debug_dir / "summary.json").read_text(encoding="utf-8"))
    assert len(summary["captures"]) == 4
    assert all(capture["raw_tex_visible"] is False for capture in summary["captures"])
    assert all(capture["external_requests"] == [] for capture in summary["captures"])
```

Add `import json` at the top of `tests/contracts/test_cli.py`.

- [ ] **Step 2: Run the CLI behavior test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_cli.py::test_cli_preview_render_debug_writes_artifacts_and_exits
```

Expected: FAIL because `main.py` parses the option but does not run debug capture or exit.

- [ ] **Step 3: Wire render debug mode into preview command**

In `packages/cli/src/raya_cli/main.py`, add this import with the other imports:

```python
from raya_cli.render_debug import capture_render_debug
```

Change the preview branch to this shape:

```python
    if args.command == "preview":
        handle = create_preview(
            args.course,
            host=args.host,
            port=args.port,
            dry_run=args.dry_run,
        )
        if not args.dry_run and handle.report.ok:
            _print_preview_summary(handle, render_debug_dir=args.render_debug)
        _print_report(handle.report)
        sys.stdout.flush()
        if not handle.report.ok:
            handle.close()
            return 1
        if args.dry_run:
            handle.close()
            return 0
        if args.render_debug:
            if handle.base_url is None or handle.plan is None:
                handle.close()
                return 1
            try:
                debug_report = capture_render_debug(
                    base_url=handle.base_url,
                    site_dir=handle.plan.site_dir,
                    output_dir=args.render_debug,
                )
                _print_report(debug_report)
                return 0 if debug_report.ok else 1
            finally:
                handle.close()
        try:
            handle.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            handle.close()
        return 0
```

Update `_print_preview_summary` to accept the optional render debug path:

```python
def _print_preview_summary(handle, *, render_debug_dir: str | None = None) -> None:
    if handle.plan is None or handle.base_url is None:
        return
    print("preview:")
    print("- status=Static preview ready")
    print(f"- entrypoint={handle.base_url}/index.html")
    print(f"- artifact={handle.plan.artifact_dir}")
    if handle.plan.inspection_path.is_file():
        print(f"- inspection={handle.base_url}/_raya/inspect/index.html")
    if render_debug_dir is not None:
        print(f"- render_debug={render_debug_dir}")
```

- [ ] **Step 4: Run the CLI behavior test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_cli.py::test_cli_preview_render_debug_writes_artifacts_and_exits
```

Expected: PASS and command exits without hanging.

- [ ] **Step 5: Run focused preview/debug tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_cli.py::test_cli_preview_help_lists_render_debug_option \
  tests/contracts/test_cli.py::test_cli_preview_render_debug_writes_artifacts_and_exits \
  tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_math_is_visible_and_uses_only_local_assets
```

Expected: all selected tests PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add packages/cli/src/raya_cli/main.py tests/contracts/test_cli.py
git commit -m "Run render debug from preview"
```

## Task 4: Replace Duplicate Test Debug Helpers

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing regression test for stale summary reset through the helper**

Update `test_render_fixture_debug_summary_is_reset_between_runs` so it calls `capture_render_debug(...)` directly instead of the environment-variable path:

```python
def test_render_fixture_debug_summary_is_reset_between_runs(tmp_path: Path) -> None:
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    debug_dir = tmp_path / "renderer-debug"
    debug_dir.mkdir()
    (debug_dir / "summary.json").write_text(
        json.dumps({"captures": [{"page": "stale"}]}) + "\n",
        encoding="utf-8",
    )

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        assert handle.base_url is not None
        result = capture_render_debug(
            base_url=handle.base_url,
            site_dir=course / "artifact" / "site",
            output_dir=debug_dir,
        )
    finally:
        handle.close()

    assert result.ok, [diagnostic.format() for diagnostic in result.diagnostics]
    summary = json.loads((debug_dir / "summary.json").read_text(encoding="utf-8"))
    assert len(summary["captures"]) == 4
    assert all(capture["page"] != "stale" for capture in summary["captures"])
```

- [ ] **Step 2: Run the reset test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_debug_summary_is_reset_between_runs
```

Expected: PASS if Task 2 reset behavior is correct. If it fails because stale data remains, fix `_reset_render_debug_dir(...)` in `render_debug.py` before continuing.

- [ ] **Step 3: Remove duplicate local debug helper code**

In `tests/e2e/test_preview_static_read_path.py`, remove duplicate constants and helpers that are now owned by `raya_cli.render_debug`:

```python
RENDER_DEBUG_PAGE_NAMES = ("index", "static-path")
RENDER_DEBUG_VIEWPORTS = (...)
RENDER_RAW_TEX_MARKERS = (...)
_capture_render_debug_artifact(...)
_reset_render_debug_dir(...)
_render_debug_screenshot_names(...)
_raw_tex_markers(...)
_viewport_name(...)
_record_external_request(...)
```

Import the shared names used by the remaining tests:

```python
from raya_cli.render_debug import (
    RENDER_DEBUG_PAGE_NAMES,
    RENDER_DEBUG_VIEWPORTS,
    capture_render_debug,
    raw_tex_markers,
    record_external_request,
    viewport_name,
)
```

If the helper module currently uses private names, rename the public test-shared helpers in `render_debug.py`:

```python
def raw_tex_markers(visible_text: str) -> list[str]:
    return [marker for marker in RENDER_RAW_TEX_MARKERS if marker in visible_text]


def viewport_name(viewport: dict[str, int]) -> str:
    if viewport["width"] <= 720:
        return "mobile"
    return "desktop"


def record_external_request(url: str, base_url: str, requests: list[str]) -> None:
    if not url.startswith(base_url):
        requests.append(url)
```

Then update internal calls in `render_debug.py` and test calls from `_raw_tex_markers`, `_viewport_name`, and `_record_external_request` to the public names.

- [ ] **Step 4: Run existing render debug tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_debug_artifacts_are_written_when_enabled \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_debug_summary_is_reset_between_runs \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_math_is_visible_and_uses_only_local_assets
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add packages/cli/src/raya_cli/render_debug.py tests/e2e/test_preview_static_read_path.py
git commit -m "Share renderer debug test helpers"
```

## Task 5: Role Documentation

**Files:**
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update English contributor guidance**

Replace the existing renderer debugging paragraph in `docs/guides/en/contributors/index.md` with:

```markdown
When debugging browser-only renderer regressions, prefer `raya preview <course> --render-debug /tmp/raya-render-debug`. The command validates, builds, serves the generated `artifact/site/`, captures desktop/mobile screenshots, and writes `summary.json` without executing course code or using browser-side MathJax. Treat those files as local evidence only; do not commit them and do not treat them as artifact authority.
```

- [ ] **Step 2: Update English agent guidance**

Replace the existing renderer debugging paragraph in `docs/guides/en/agents/index.md` with:

```markdown
For renderer debugging, prefer `raya preview <course> --render-debug /tmp/raya-render-debug` to capture screenshots and `summary.json` from the generated static site. Use debug output as evidence for layout/math failures, raw TeX leakage, external requests, and overflow, but keep authority in source files, `manifest.json`, and manifest-declared `data/*.json`.
```

- [ ] **Step 3: Update Spanish contributor guidance**

In `docs/guides/es/colaboradores/index.md`, replace the matching renderer debugging paragraph with:

```markdown
Al depurar regresiones del renderizador que solo aparecen en el navegador, prefiere `raya preview <course> --render-debug /tmp/raya-render-debug`. El comando valida, construye, sirve el `artifact/site/` generado, captura screenshots de escritorio/movil y escribe `summary.json` sin ejecutar codigo del curso ni usar MathJax en el navegador. Trata esos archivos solo como evidencia local; no los confirmes en git ni los trates como autoridad del artifact.
```

- [ ] **Step 4: Update Spanish agent guidance**

In `docs/guides/es/agentes/index.md`, replace the matching renderer debugging paragraph with:

```markdown
Para depurar renderizado, prefiere `raya preview <course> --render-debug /tmp/raya-render-debug` para capturar screenshots y `summary.json` desde el sitio static generado. Usa esa salida como evidencia para fallas de layout/math, fuga de TeX visible, requests externos y overflow, pero conserva la autoridad en los archivos fuente, `manifest.json` y los `data/*.json` declarados por el manifest.
```

- [ ] **Step 5: Validate and build docs**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate docs
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build docs
```

Expected: both commands exit 0.

- [ ] **Step 6: Commit**

Run:

```bash
git add docs/guides/en/contributors/index.md docs/guides/en/agents/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md
git commit -m "Document preview render debug workflow"
```

## Task 6: Verification And Review

**Files:**
- Modify: `docs/superpowers/plans/2026-06-14-preview-render-debug.md`

- [ ] **Step 1: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_cli.py::test_cli_preview_help_lists_render_debug_option \
  tests/contracts/test_cli.py::test_cli_preview_render_debug_writes_artifacts_and_exits \
  tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_debug_artifacts_are_written_when_enabled \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_debug_summary_is_reset_between_runs \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_math_is_visible_and_uses_only_local_assets
```

Expected: all selected tests PASS.

- [ ] **Step 2: Build the render fixture**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
```

Expected: exit 0 and `examples/courses/render-fixture/artifact/site/index.html` is generated.

- [ ] **Step 3: Run host archive gate**

Run:

```bash
./scripts/check.sh
```

Expected: exit 0 with `check: passed`.

- [ ] **Step 4: Run Docker reference gate**

Run:

```bash
./scripts/check-docker.sh
```

Expected: exit 0 with `check-docker: passed`.

- [ ] **Step 5: Request code review**

Use `superpowers:requesting-code-review` over the implementation commits after the design and plan commits. Ask the reviewer to focus on:

```text
Review preview render debug implementation for CLI behavior, server lifecycle, no-execution guarantees, browser dependency diagnostics, static parity, no external requests, and documentation drift.
```

- [ ] **Step 6: Address review findings with TDD**

For every bug or behavior change from review:

```text
1. Write or update a failing test that demonstrates the finding.
2. Run the focused test and confirm the expected failure.
3. Implement the minimal fix.
4. Re-run the focused test and relevant gate.
5. Commit the fix.
```

- [ ] **Step 7: Update this plan with execution status**

Append a short section:

```markdown
## Execution Status

- Implemented in commits: `<commit-list>`.
- Verification run:
  - `<command>`: passed
- Code review: requested and addressed.
```

- [ ] **Step 8: Commit the plan status update**

Run:

```bash
git add docs/superpowers/plans/2026-06-14-preview-render-debug.md
git commit -m "Track preview render debug execution"
```

## Self-Review

- Spec coverage: Tasks cover CLI option, browser capture helper, preview integration, stale debug reset, role docs, focused verification, host/Docker gates, and code review.
- Placeholder scan: no incomplete implementation markers or unspecified steps remain.
- Type consistency: the plan uses `capture_render_debug(base_url=..., site_dir=..., output_dir=...) -> ValidationReport` consistently across tests and CLI wiring.

## Execution Status

- Implemented in commits:
  - `edb458f` Expose preview render debug option
  - `3893520` Add preview render debug capture helper
  - `495bd32` Run render debug from preview
  - `63f4726` Share renderer debug test helpers
  - `c91c446` Document preview render debug workflow
  - `01e2e82` Harden preview render debug diagnostics
- Verification run:
  - `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_cli.py::test_cli_preview_help_lists_render_debug_option tests/contracts/test_cli.py::test_cli_preview_render_debug_writes_artifacts_and_exits tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_fails_on_visible_raw_tex tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_reports_invalid_browser_executable tests/e2e/test_preview_static_read_path.py::test_render_fixture_debug_artifacts_are_written_when_enabled tests/e2e/test_preview_static_read_path.py::test_render_fixture_debug_summary_is_reset_between_runs tests/e2e/test_preview_static_read_path.py::test_render_fixture_math_is_visible_and_uses_only_local_assets`: passed, `8 passed in 32.29s`
  - `UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture`: passed
  - `UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate docs`: passed
  - `UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build docs`: passed
  - `./scripts/check.sh`: passed, `205 passed in 89.59s`, `check: passed`
  - `./scripts/check-docker.sh`: passed, `205 passed in 131.97s`, `check-docker: passed`
- Code review: requested over `d8c9470..c91c446`; Important and Minor findings were addressed in `01e2e82`.
