# Render Debug Inspection Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a static render-debug inspection report and extend the focused render-debug gate to inspect both the local artifact site and a copied external static site.

**Architecture:** Keep `raya preview --render-debug` as the browser capture path. Add a focused `raya_cli.render_debug_report` module that can inspect `summary.json`, screenshots, generated HTML, local MathJax resources, and optional copied-site parity, then write `report.json` and `index.html`. Simplify `scripts/check-render-debug.sh` so it runs preview, copies `artifact/site/`, calls the Python report module, and prints the report path on failures.

**Tech Stack:** Python 3.10, `uv`, `pytest`, Playwright/Chromium through existing render-debug tests, shell script gate, static HTML/JSON report artifacts.

---

## File Structure

- Create `packages/cli/src/raya_cli/render_debug_report.py`: owns inspection, report JSON shape, static HTML report, and optional CLI entrypoint for the shell script.
- Modify `packages/cli/src/raya_cli/render_debug.py`: calls the report writer after browser captures so `--render-debug` alone creates report artifacts.
- Modify `scripts/check-render-debug.sh`: removes embedded inspector, copies `artifact/site/` to a temp external directory, invokes `uv run python -m raya_cli.render_debug_report`.
- Modify `tests/e2e/test_preview_static_read_path.py`: validates `capture_render_debug` writes report files.
- Modify `tests/e2e/test_render_debug_parity_gate.py`: validates script report output, copied-site parity failures, and failure report generation.
- Modify `tests/contracts/test_renderer_dependencies.py`: locks the new module/script contract and command guidance.
- Modify role docs only where they already mention the focused render-debug gate.

---

### Task 1: Lock Report Artifacts From `capture_render_debug`

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify later: `packages/cli/src/raya_cli/render_debug.py`
- Create later: `packages/cli/src/raya_cli/render_debug_report.py`

- [ ] **Step 1: Write the failing report artifact test**

Add assertions to `test_capture_render_debug_writes_screenshots_and_summary` after the existing summary assertions:

```python
    report_json = json.loads((debug_dir / "report.json").read_text(encoding="utf-8"))
    report_html = (debug_dir / "index.html").read_text(encoding="utf-8")

    assert report_json["ok"] is True
    assert report_json["summary_path"].endswith("summary.json")
    assert report_json["html_report_path"].endswith("index.html")
    assert {check["id"] for check in report_json["checks"]} >= {
        "capture:index:desktop",
        "capture:index:mobile",
        "capture:static-path:desktop",
        "capture:static-path:mobile",
    }
    assert report_json["diagnostics"] == []
    assert "Render Debug Inspection Report" in report_html
    assert 'href="desktop-index.png"' in report_html
    assert 'href="mobile-static-path.png"' in report_html
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary
```

Expected: FAIL because `report.json` and `index.html` do not exist.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/e2e/test_preview_static_read_path.py
git commit -m "Test render debug report artifacts"
```

---

### Task 2: Add The Report Writer Module

**Files:**
- Create: `packages/cli/src/raya_cli/render_debug_report.py`
- Modify: `packages/cli/src/raya_cli/render_debug.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Create `render_debug_report.py` with the shared report writer**

Create `packages/cli/src/raya_cli/render_debug_report.py`:

```python
from __future__ import annotations

import html
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any


EXPECTED_CAPTURES = {
    ("index", "desktop"): "desktop-index.png",
    ("index", "mobile"): "mobile-index.png",
    ("static-path", "desktop"): "desktop-static-path.png",
    ("static-path", "mobile"): "mobile-static-path.png",
}

BLOCKED_RENDERER_FRAGMENTS = (
    "mathjax.js",
    "tex-chtml",
    "tex-svg",
    "mml-chtml",
    "tex-mml-chtml",
    "startup.js",
    "cdn.jsdelivr.net",
    "unpkg.com",
    "cdnjs.cloudflare.com",
    "polyfill.io",
    "https://cdn",
    "http://cdn",
)

RAW_TEX_PATTERNS = (
    re.compile(r"(?<!\\)(\${1,2})(?!\s)([^$\n]{1,200}?)(?<!\s)\1"),
    re.compile(r"\\[A-Za-z]+(?=[\s{(\[])"),
)


def inspect_render_debug(
    *,
    site_dir: str | Path,
    debug_dir: str | Path,
    copied_site_dir: str | Path | None = None,
) -> dict[str, Any]:
    site_root = Path(site_dir)
    debug_root = Path(debug_dir)
    copied_root = Path(copied_site_dir) if copied_site_dir is not None else None
    checks: list[dict[str, Any]] = []
    diagnostics: list[dict[str, str]] = []

    summary = _load_summary(debug_root / "summary.json", diagnostics)
    captures = summary.get("captures")
    if not isinstance(captures, list):
        captures = []
        diagnostics.append(_diagnostic("summary.json captures must be a list", debug_root / "summary.json"))

    _inspect_captures(captures, debug_root, checks, diagnostics)
    _inspect_site(site_root, "site", checks, diagnostics)
    if copied_root is not None:
        _inspect_site(copied_root, "copied-site", checks, diagnostics)

    report = {
        "ok": not diagnostics,
        "site_dir": str(site_root),
        "copied_site_dir": str(copied_root) if copied_root is not None else None,
        "summary_path": str(debug_root / "summary.json"),
        "html_report_path": str(debug_root / "index.html"),
        "checks": checks,
        "diagnostics": diagnostics,
    }
    write_render_debug_report(debug_root, report)
    return report


def copy_static_site(site_dir: str | Path, destination: str | Path) -> Path:
    source = Path(site_dir)
    target = Path(destination)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    return target


def write_render_debug_report(debug_dir: Path, report: dict[str, Any]) -> None:
    debug_dir.mkdir(parents=True, exist_ok=True)
    (debug_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (debug_dir / "index.html").write_text(_render_html(report), encoding="utf-8")
```

Then add the helper functions in the same file:

```python
def _load_summary(summary_path: Path, diagnostics: list[dict[str, str]]) -> dict[str, Any]:
    try:
        value = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception as exc:
        diagnostics.append(_diagnostic(f"missing or malformed summary.json: {exc}", summary_path))
        return {"captures": []}
    if not isinstance(value, dict):
        diagnostics.append(_diagnostic("summary.json must be an object", summary_path))
        return {"captures": []}
    return value


def _inspect_captures(
    captures: list[Any],
    debug_dir: Path,
    checks: list[dict[str, Any]],
    diagnostics: list[dict[str, str]],
) -> None:
    debug_root = debug_dir.resolve()
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for capture in captures:
        if not isinstance(capture, dict):
            diagnostics.append(_diagnostic(f"summary.json capture must be an object: {capture!r}", debug_dir / "summary.json"))
            continue
        page = capture.get("page")
        viewport = capture.get("viewport")
        viewport_name = viewport.get("name") if isinstance(viewport, dict) else None
        if isinstance(page, str) and isinstance(viewport_name, str):
            seen[(page, viewport_name)] = capture
        _inspect_capture_record(capture, debug_dir, checks, diagnostics)

    for key, screenshot_name in EXPECTED_CAPTURES.items():
        if key not in seen:
            diagnostics.append(_diagnostic(f"missing expected capture page={key[0]} viewport={key[1]}", debug_dir / "summary.json"))
            checks.append({"id": f"capture:{key[0]}:{key[1]}", "ok": False, "page": key[0], "viewport": key[1], "screenshot": screenshot_name, "diagnostics": ["missing expected capture"]})
            continue
        screenshot = debug_dir / screenshot_name
        if not screenshot.is_file() or screenshot.stat().st_size <= 0:
            diagnostics.append(_diagnostic(f"missing or empty screenshot {screenshot}", screenshot))
        declared = Path(str(seen[key].get("screenshot", screenshot_name)))
        if not declared.is_absolute():
            declared = debug_dir / declared
        try:
            declared.resolve().relative_to(debug_root)
        except ValueError:
            diagnostics.append(_diagnostic(f"screenshot path is outside debug directory for page={key[0]} viewport={key[1]}: {declared}", declared))
        if declared.name != screenshot_name:
            diagnostics.append(_diagnostic(f"unexpected screenshot for page={key[0]} viewport={key[1]}: {declared}", declared))
```

Continue the helper implementation:

```python
def _inspect_capture_record(
    capture: dict[str, Any],
    debug_dir: Path,
    checks: list[dict[str, Any]],
    diagnostics: list[dict[str, str]],
) -> None:
    page = str(capture.get("page", "unknown"))
    viewport = capture.get("viewport")
    viewport_name = str(viewport.get("name", "unknown")) if isinstance(viewport, dict) else "unknown"
    local_diagnostics: list[str] = []
    if capture.get("raw_tex_visible"):
        local_diagnostics.append("visible raw TeX")
        diagnostics.append(_diagnostic(f"visible raw TeX in capture page={page!r} viewport={viewport_name!r}", debug_dir / "summary.json"))
    external_requests = capture.get("external_requests")
    if external_requests:
        local_diagnostics.append("external requests")
        diagnostics.append(_diagnostic(f"external requests in capture page={page!r} viewport={viewport_name!r}: {external_requests}", debug_dir / "summary.json"))
    overflow = capture.get("horizontal_overflow", 0)
    if isinstance(overflow, (int, float)) and overflow > 1:
        local_diagnostics.append("horizontal overflow")
        diagnostics.append(_diagnostic(f"horizontal overflow in capture page={page!r} viewport={viewport_name!r}: {overflow}", debug_dir / "summary.json"))
    elif not isinstance(overflow, (int, float)):
        local_diagnostics.append("nonnumeric horizontal_overflow")
        diagnostics.append(_diagnostic(f"horizontal_overflow must be numeric in capture page={page!r} viewport={viewport_name!r}", debug_dir / "summary.json"))
    checks.append({
        "id": f"capture:{page}:{viewport_name}",
        "ok": not local_diagnostics,
        "page": page,
        "viewport": viewport_name,
        "screenshot": Path(str(capture.get("screenshot", ""))).name,
        "diagnostics": local_diagnostics,
    })


def _inspect_site(
    site_dir: Path,
    label: str,
    checks: list[dict[str, Any]],
    diagnostics: list[dict[str, str]],
) -> None:
    html_paths = sorted(site_dir.rglob("*.html")) if site_dir.is_dir() else []
    local_diagnostics: list[str] = []
    if not html_paths:
        local_diagnostics.append("no generated HTML")
        diagnostics.append(_diagnostic(f"no generated HTML found under {site_dir}", site_dir))
    has_math = False
    for html_path in html_paths:
        text = html_path.read_text(encoding="utf-8")
        text_lower = text.lower()
        has_math = has_math or "mjx-container" in text_lower or "_raya/render/math/" in text_lower
        for fragment in BLOCKED_RENDERER_FRAGMENTS:
            if fragment in text_lower:
                local_diagnostics.append(f"blocked renderer dependency {fragment!r}")
                diagnostics.append(_diagnostic(f"browser-side or external renderer dependency {fragment!r} in {html_path}", html_path))
        if re.search(r"_raya/render/math/[^\"')\s>]+\.js\b", text_lower):
            local_diagnostics.append("blocked _raya/render/math/*.js")
            diagnostics.append(_diagnostic(f"browser-side or external renderer dependency '_raya/render/math/*.js' in {html_path}", html_path))
        visible_text = _strip_html_support(text)
        for pattern in RAW_TEX_PATTERNS:
            if pattern.search(visible_text):
                local_diagnostics.append("raw visible TeX marker")
                diagnostics.append(_diagnostic(f"raw visible TeX marker in generated HTML {html_path}", html_path))
                break
    if has_math:
        css = site_dir / "_raya" / "render" / "math" / "mathjax.css"
        fonts = site_dir / "_raya" / "render" / "math" / "fonts"
        if not css.is_file():
            local_diagnostics.append("missing local MathJax CSS")
            diagnostics.append(_diagnostic(f"missing local MathJax CSS {css}", css))
        if not fonts.is_dir() or not any(fonts.glob("*.woff2")):
            local_diagnostics.append("missing local MathJax fonts")
            diagnostics.append(_diagnostic(f"missing local MathJax fonts under {fonts}", fonts))
    checks.append({"id": f"site:{label}", "ok": not local_diagnostics, "path": str(site_dir), "diagnostics": sorted(set(local_diagnostics))})


def _strip_html_support(text: str) -> str:
    text = re.sub(r"<(script|style|code|pre|kbd|samp|textarea)\b[^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(text)


def _diagnostic(message: str, path: Path, *, severity: str = "error", next_action: str | None = None) -> dict[str, str]:
    diagnostic = {"severity": severity, "message": message, "path": str(path)}
    diagnostic["next_action"] = next_action or "Inspect debug/index.html, report.json, and the referenced generated file."
    return diagnostic
```

Add HTML and CLI entrypoint:

```python
def _render_html(report: dict[str, Any]) -> str:
    status = "PASS" if report.get("ok") else "FAIL"
    rows = "\n".join(_render_check_row(check) for check in report.get("checks", []))
    diagnostics = "\n".join(
        f"<li><strong>{html.escape(item.get('message', 'diagnostic'))}</strong><br><code>{html.escape(item.get('path', ''))}</code><br>{html.escape(item.get('next_action', ''))}</li>"
        for item in report.get("diagnostics", [])
    ) or "<li>No diagnostics.</li>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Render Debug Inspection Report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #ddd; padding: 0.5rem; text-align: left; vertical-align: top; }}
    .pass {{ color: #146c2e; font-weight: 700; }}
    .fail {{ color: #9f1d20; font-weight: 700; }}
    img {{ max-width: 220px; border: 1px solid #ddd; }}
    code {{ background: #f6f6f6; padding: 0.1rem 0.25rem; }}
  </style>
</head>
<body>
  <h1>Render Debug Inspection Report</h1>
  <p>Status: <span class="{html.escape(status.lower())}">{html.escape(status)}</span></p>
  <p>Site: <code>{html.escape(str(report.get("site_dir", "")))}</code></p>
  <p>Copied site: <code>{html.escape(str(report.get("copied_site_dir", "")))}</code></p>
  <h2>Checks</h2>
  <table><thead><tr><th>ID</th><th>Status</th><th>Screenshot</th><th>Diagnostics</th></tr></thead><tbody>{rows}</tbody></table>
  <h2>Diagnostics</h2>
  <ul>{diagnostics}</ul>
</body>
</html>
"""


def _render_check_row(check: dict[str, Any]) -> str:
    status = "PASS" if check.get("ok") else "FAIL"
    screenshot = str(check.get("screenshot") or "")
    screenshot_cell = f'<a href="{html.escape(screenshot)}"><img src="{html.escape(screenshot)}" alt="{html.escape(screenshot)}"></a>' if screenshot else ""
    diagnostics = "<br>".join(html.escape(str(item)) for item in check.get("diagnostics", [])) or "none"
    return f"<tr><td><code>{html.escape(str(check.get('id', '')))}</code></td><td>{status}</td><td>{screenshot_cell}</td><td>{diagnostics}</td></tr>"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) not in (2, 3):
        print("Usage: python -m raya_cli.render_debug_report SITE_DIR DEBUG_DIR [COPIED_SITE_DIR]", file=sys.stderr)
        return 2
    report = inspect_render_debug(
        site_dir=args[0],
        debug_dir=args[1],
        copied_site_dir=args[2] if len(args) == 3 else None,
    )
    print(f"render-debug-report: {report['html_report_path']}")
    if not report["ok"]:
        for diagnostic in report["diagnostics"]:
            print(f"render-debug-report: ERROR: {diagnostic['message']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Call the report writer from `capture_render_debug`**

In `packages/cli/src/raya_cli/render_debug.py`, add:

```python
from raya_cli.render_debug_report import inspect_render_debug
```

After the loop and before `report.wrote_output(debug_dir / "summary.json")`, add:

```python
    inspection = inspect_render_debug(site_dir=site_root, debug_dir=debug_dir)
    report.wrote_output(debug_dir / "report.json")
    report.wrote_output(debug_dir / "index.html")
    if not inspection["ok"]:
        for diagnostic in inspection["diagnostics"]:
            report.add_error(
                diagnostic["message"],
                path=Path(diagnostic["path"]),
                next_action=diagnostic.get("next_action"),
            )
```

- [ ] **Step 3: Run the report artifact test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary
```

Expected: PASS.

- [ ] **Step 4: Commit the implementation**

```bash
git add packages/cli/src/raya_cli/render_debug.py packages/cli/src/raya_cli/render_debug_report.py
git commit -m "Add render debug inspection report"
```

---

### Task 3: Add Copied-Site Parity Tests For The Gate

**Files:**
- Modify: `tests/e2e/test_render_debug_parity_gate.py`
- Modify later: `scripts/check-render-debug.sh`
- Modify later: `packages/cli/src/raya_cli/render_debug_report.py`

- [ ] **Step 1: Extend the positive gate test**

In `test_render_debug_parity_gate_passes_on_render_fixture_copy`, add:

```python
    report_json = json.loads((debug_dir / "report.json").read_text(encoding="utf-8"))
    report_html = (debug_dir / "index.html").read_text(encoding="utf-8")

    assert report_json["ok"] is True
    assert report_json["copied_site_dir"]
    assert any(check["id"] == "site:copied-site" for check in report_json["checks"])
    assert "Render Debug Inspection Report" in report_html
    assert "Copied site:" in report_html
```

- [ ] **Step 2: Add copied-site failure tests**

Add these tests to `tests/e2e/test_render_debug_parity_gate.py`:

```python
def test_render_debug_parity_gate_report_is_written_on_failure(tmp_path: Path) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    (debug_dir / "mobile-static-path.png").unlink()

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir))

    assert result.returncode == 1
    assert "debug report" in result.stderr or "render-debug-report:" in result.stdout
    assert (debug_dir / "report.json").is_file()
    assert (debug_dir / "index.html").is_file()
    report = json.loads((debug_dir / "report.json").read_text(encoding="utf-8"))
    assert report["ok"] is False
    assert any("missing or empty screenshot" in item["message"] for item in report["diagnostics"])


def test_render_debug_parity_gate_fails_when_copied_site_has_browser_runtime(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    copied_site = tmp_path / "copied-site"
    shutil.copytree(site_dir, copied_site)
    (copied_site / "index.html").write_text(
        '<html><head><script src="_raya/render/math/tex-chtml.js"></script></head></html>',
        encoding="utf-8",
    )

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir), str(copied_site))

    assert result.returncode == 1
    report = json.loads((debug_dir / "report.json").read_text(encoding="utf-8"))
    assert any(
        item["path"].startswith(str(copied_site))
        and "browser-side or external renderer dependency" in item["message"]
        for item in report["diagnostics"]
    )


def test_render_debug_parity_gate_fails_when_copied_site_lacks_math_css(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    math_dir = site_dir / "_raya" / "render" / "math"
    (math_dir / "fonts").mkdir(parents=True)
    (math_dir / "fonts" / "fixture.woff2").write_bytes(b"font")
    (math_dir / "mathjax.css").write_text("mjx-container {}", encoding="utf-8")
    copied_site = tmp_path / "copied-site"
    shutil.copytree(site_dir, copied_site)
    (copied_site / "_raya" / "render" / "math" / "mathjax.css").unlink()

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir), str(copied_site))

    assert result.returncode == 1
    assert "missing local MathJax CSS" in result.stderr
```

Update `write_debug_fixture` so the fixture includes local MathJax resources by default:

```python
    math_dir = site_dir / "_raya" / "render" / "math"
    (math_dir / "fonts").mkdir(parents=True)
    (math_dir / "mathjax.css").write_text("mjx-container {}", encoding="utf-8")
    (math_dir / "fonts" / "fixture.woff2").write_bytes(b"font")
```

- [ ] **Step 3: Run the new tests and verify they fail**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_render_debug_parity_gate.py::test_render_debug_parity_gate_passes_on_render_fixture_copy tests/e2e/test_render_debug_parity_gate.py::test_render_debug_parity_gate_report_is_written_on_failure tests/e2e/test_render_debug_parity_gate.py::test_render_debug_parity_gate_fails_when_copied_site_has_browser_runtime tests/e2e/test_render_debug_parity_gate.py::test_render_debug_parity_gate_fails_when_copied_site_lacks_math_css
```

Expected: FAIL because the script does not yet create copied-site report metadata or accept the optional copied-site argument.

- [ ] **Step 4: Commit the copied-site tests**

```bash
git add tests/e2e/test_render_debug_parity_gate.py
git commit -m "Test render debug copied site report parity"
```

---

### Task 4: Replace The Embedded Script Inspector

**Files:**
- Modify: `scripts/check-render-debug.sh`
- Modify: `packages/cli/src/raya_cli/render_debug_report.py`
- Test: `tests/e2e/test_render_debug_parity_gate.py`

- [ ] **Step 1: Update script usage and argument parsing**

Change usage in `scripts/check-render-debug.sh` to:

```bash
Usage: scripts/check-render-debug.sh [--inspect-only SITE_DIR DEBUG_DIR [COPIED_SITE_DIR]]
```

Change the `--inspect-only` argument check to accept three or four total arguments:

```bash
  --inspect-only)
    if [[ $# -ne 3 && $# -ne 4 ]]; then
      echo "--inspect-only requires SITE_DIR and DEBUG_DIR, with optional COPIED_SITE_DIR" >&2
      usage >&2
      exit 2
    fi
    INSPECT_ONLY=1
    INSPECT_SITE_DIR="$2"
    INSPECT_DEBUG_DIR="$3"
    INSPECT_COPIED_SITE_DIR="${4:-}"
    ;;
```

- [ ] **Step 2: Add copied-site temp directory handling**

After normal preview execution sets `SITE_DIR` and `DEBUG_DIR`, add:

```bash
if [[ "${INSPECT_ONLY:-0}" == "1" && -n "${INSPECT_COPIED_SITE_DIR:-}" ]]; then
  COPIED_SITE_DIR="$INSPECT_COPIED_SITE_DIR"
elif [[ "${INSPECT_ONLY:-0}" == "1" ]]; then
  COPIED_SITE_DIR=""
else
  COPIED_SITE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/raya-render-site-copy.XXXXXX")"
  CLEANUP_COPIED_SITE=1
  cp -R "$SITE_DIR"/. "$COPIED_SITE_DIR"/
fi
```

Update `cleanup()`:

```bash
  cleanup() {
    if [[ "${CLEANUP_DEBUG:-0}" == "1" ]]; then
      rm -rf "$DEBUG_DIR"
    fi
    if [[ "${CLEANUP_COPIED_SITE:-0}" == "1" ]]; then
      rm -rf "$COPIED_SITE_DIR"
    fi
  }
```

- [ ] **Step 3: Replace the embedded Python block**

Delete the current `uv run python - "$SITE_DIR" "$DEBUG_DIR" <<'PY'` block.

Replace it with:

```bash
if [[ -n "${COPIED_SITE_DIR:-}" ]]; then
  if ! uv run python -m raya_cli.render_debug_report "$SITE_DIR" "$DEBUG_DIR" "$COPIED_SITE_DIR"; then
    echo "check-render-debug: debug report $DEBUG_DIR/index.html" >&2
    exit 1
  fi
else
  if ! uv run python -m raya_cli.render_debug_report "$SITE_DIR" "$DEBUG_DIR"; then
    echo "check-render-debug: debug report $DEBUG_DIR/index.html" >&2
    exit 1
  fi
fi
```

- [ ] **Step 4: Ensure module diagnostics match existing script messages**

If tests fail because expected strings changed, update `render_debug_report.py` diagnostics rather than weakening tests. The module must emit these substrings:

```text
visible raw TeX
external requests
missing or empty screenshot
horizontal overflow
browser-side or external renderer dependency
outside debug directory
missing local MathJax CSS
```

- [ ] **Step 5: Run copied-site tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_render_debug_parity_gate.py
```

Expected: PASS.

- [ ] **Step 6: Run the direct gate**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local scripts/check-render-debug.sh
```

Expected: exit 0 and stdout includes:

```text
render-debug-report:
check-render-debug: passed
```

- [ ] **Step 7: Commit script integration**

```bash
git add scripts/check-render-debug.sh packages/cli/src/raya_cli/render_debug_report.py tests/e2e/test_render_debug_parity_gate.py
git commit -m "Add copied static parity to render debug gate"
```

---

### Task 5: Lock Contracts And Documentation Guidance

**Files:**
- Modify: `tests/contracts/test_renderer_dependencies.py`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `openspec/config.yaml`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Write the contract test**

Add to `tests/contracts/test_renderer_dependencies.py`:

```python
def test_render_debug_report_module_and_guidance_are_declared() -> None:
    module = ROOT / "packages" / "cli" / "src" / "raya_cli" / "render_debug_report.py"
    script = (ROOT / "scripts" / "check-render-debug.sh").read_text(encoding="utf-8")

    assert module.exists()
    module_text = module.read_text(encoding="utf-8")
    assert "inspect_render_debug" in module_text
    assert "report.json" in module_text
    assert "index.html" in module_text
    assert "copied_site_dir" in module_text
    assert "python -m raya_cli.render_debug_report" in script

    for path in (
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "openspec" / "config.yaml",
        ROOT / "docs" / "guides" / "en" / "contributors" / "index.md",
        ROOT / "docs" / "guides" / "en" / "agents" / "index.md",
        ROOT / "docs" / "guides" / "es" / "colaboradores" / "index.md",
        ROOT / "docs" / "guides" / "es" / "agentes" / "index.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert "report.json" in text
        assert "index.html" in text
```

- [ ] **Step 2: Run the contract test and verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_renderer_dependencies.py::test_render_debug_report_module_and_guidance_are_declared
```

Expected: FAIL until guidance is updated.

- [ ] **Step 3: Update top-level guidance**

In `README.md` and `AGENTS.md`, extend the `check-render-debug.sh` sentence to mention:

```markdown
It writes `report.json` and `index.html` in the debug output directory and checks copied static-site parity.
```

In `openspec/config.yaml`, extend the math rendering checklist line to include:

```yaml
render-debug `report.json`/`index.html` artifacts and copied static-site parity
```

- [ ] **Step 4: Update role docs**

In English contributor and agent docs, update the existing render-debug gate paragraphs to mention:

```markdown
The gate writes `report.json` and `index.html` beside the screenshots. When it fails, inspect `index.html` first, then use `report.json` for exact page, viewport, file path, and copied-site diagnostics.
```

In Spanish collaborator and agent docs, add the equivalent text while keeping technical identifiers in English:

```markdown
El gate escribe `report.json` e `index.html` junto a los screenshots. Cuando falle, inspecciona primero `index.html` y usa `report.json` para ubicar pagina, viewport, path de archivo y diagnosticos del copied site.
```

- [ ] **Step 5: Run the contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_renderer_dependencies.py::test_render_debug_report_module_and_guidance_are_declared
```

Expected: PASS.

- [ ] **Step 6: Commit docs and contract**

```bash
git add README.md AGENTS.md openspec/config.yaml docs/guides/en/contributors/index.md docs/guides/en/agents/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md tests/contracts/test_renderer_dependencies.py
git commit -m "Document render debug inspection report"
```

---

### Task 6: Focused Verification

**Files:**
- No source edits unless verification finds a failure.

- [ ] **Step 1: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_render_debug_parity_gate.py tests/e2e/test_preview_static_read_path.py tests/contracts/test_renderer_dependencies.py
```

Expected: PASS.

- [ ] **Step 2: Run direct render-debug gate**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local scripts/check-render-debug.sh
```

Expected: PASS and writes `summary.json`, screenshots, `report.json`, and `index.html` during the run.

- [ ] **Step 3: Commit any verification fixes**

If any source or test changes were needed:

```bash
git add <changed-files>
git commit -m "Fix render debug inspection parity verification"
```

If no changes were needed, do not create an empty commit.

---

### Task 7: Full Verification And Code Review

**Files:**
- Modify: `docs/superpowers/plans/2026-06-15-render-debug-inspection-parity.md` after verification.

- [ ] **Step 1: Run host archive gate**

Run:

```bash
./scripts/check.sh
```

Expected: PASS with `check: passed`.

- [ ] **Step 2: Run Docker archive gate**

Run:

```bash
./scripts/check-docker.sh
```

Expected: PASS with `check-docker: passed`.

- [ ] **Step 3: Request code review**

Use `superpowers:requesting-code-review` over commits after `3abcf37`.

Reviewer prompt:

```text
Review the render-debug inspection parity implementation. Focus on report artifact determinism, script cleanup behavior, copied static-site parity, browser-side MathJax/CDN detection, raw TeX false positives, generated report safety, role documentation drift, and whether failures preserve enough diagnostics for agents.
```

- [ ] **Step 4: Address review findings with TDD**

For each accepted review finding:

```text
1. Write or update a focused failing test.
2. Run it and confirm it fails for the expected reason.
3. Implement the minimal fix.
4. Re-run the focused test and relevant gate.
5. Commit the fix.
```

- [ ] **Step 5: Update execution status**

Append:

```markdown
## Execution Status

- Implemented in commits:
  - `<hash>` `<subject>`
- Verification run:
  - `<command>`: passed
- Code review: requested and addressed.
```

- [ ] **Step 6: Commit execution status**

```bash
git add docs/superpowers/plans/2026-06-15-render-debug-inspection-parity.md
git commit -m "Track render debug inspection parity execution"
```

## Self-Review

- Spec coverage: tasks cover report JSON, report HTML, failure report generation, copied external static-site inspection, no browser-side MathJax runtime checks, no CDN/external renderer checks, local MathJax CSS/font checks, focused script output, command guidance, role docs, host/Docker verification, and review.
- Placeholder scan: no unresolved placeholder markers or open-ended implementation steps remain.
- Type consistency: the plan consistently uses `inspect_render_debug`, `report.json`, `index.html`, `copied_site_dir`, `checks`, and `diagnostics`.
