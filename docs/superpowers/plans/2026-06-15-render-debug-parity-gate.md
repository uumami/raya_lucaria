# Render Debug Parity Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a focused render-debug parity gate that validates browser screenshots, summary diagnostics, local static assets, and no browser-side MathJax dependency for `examples/courses/render-fixture`.

**Architecture:** Keep the public CLI unchanged and add a repository verification script, `scripts/check-render-debug.sh`, around the existing `raya preview --render-debug` workflow. The script owns only verification orchestration and artifact inspection; the renderer remains under `packages/static`, and browser capture remains under `packages/cli/src/raya_cli/render_debug.py`.

**Tech Stack:** Bash, Python 3.10 standard library, `uv`, existing `raya preview --render-debug`, pytest, Chromium/Playwright through existing dev dependencies, Docker through existing `scripts/check-docker.sh`.

---

## File Structure

- Create `scripts/check-render-debug.sh`.
  - Runs the focused render fixture browser-debug gate.
  - Uses `UV_PROJECT_ENVIRONMENT=.venv-local` by default.
  - Creates a temporary debug directory unless `RAYA_RENDER_DEBUG_OUTPUT_DIR` is set.
  - Deletes the temporary directory on exit unless `RAYA_RENDER_DEBUG_KEEP=1`.
  - Calls `uv run raya preview <course> --port 0 --render-debug <dir>`.
  - Uses embedded Python to inspect `summary.json`, screenshots, and generated HTML.
  - Supports `--inspect-only <site-dir> <debug-dir>` for deterministic negative tests that do not need to launch a browser.
- Modify `scripts/check-python.sh`.
  - Document and invoke `scripts/check-render-debug.sh`.
  - Place it after fixture build/inspect checks and before docs checks so renderer dependencies and the render fixture artifact already exist.
- Modify `tests/contracts/test_renderer_dependencies.py`.
  - Add contract tests for script existence, help text, `check-python.sh` wiring, and Docker coverage through `check-python.sh`.
- Create `tests/e2e/test_render_debug_parity_gate.py`.
  - Run the focused gate on a temporary copy of `examples/courses/render-fixture`.
  - Exercise `--inspect-only` negative cases for raw TeX, external requests, missing screenshots, overflow, and browser-side MathJax runtime script references.
- Modify role docs:
  - `docs/guides/en/contributors/index.md`
  - `docs/guides/en/agents/index.md`
  - `docs/guides/es/colaboradores/index.md`
  - `docs/guides/es/agentes/index.md`

## Task 1: Script Contract Red Tests

**Files:**
- Modify: `tests/contracts/test_renderer_dependencies.py`
- Later create: `scripts/check-render-debug.sh`
- Later modify: `scripts/check-python.sh`

- [ ] **Step 1: Add failing contract tests**

Add these tests to `tests/contracts/test_renderer_dependencies.py` after `test_check_python_installs_renderer_dependencies_before_python_sync`:

```python
def test_render_debug_parity_script_is_declared() -> None:
    script = ROOT / "scripts" / "check-render-debug.sh"

    assert script.exists(), "renderer parity gate script must exist"
    content = script.read_text(encoding="utf-8")
    assert "Usage: scripts/check-render-debug.sh" in content
    assert "raya preview" in content
    assert "--render-debug" in content
    assert "summary.json" in content


def test_check_python_runs_render_debug_parity_gate_after_fixture_builds() -> None:
    script = (ROOT / "scripts" / "check-python.sh").read_text(encoding="utf-8")

    render_fixture_build = 'run uv run raya build "$course"'
    render_debug_gate = "run scripts/check-render-debug.sh"
    docs_validate = "run uv run raya validate docs"

    assert "render-debug parity gate" in script
    assert render_debug_gate in script
    assert script.index(render_fixture_build) < script.index(render_debug_gate)
    assert script.index(render_debug_gate) < script.index(docs_validate)


def test_docker_check_inherits_render_debug_parity_gate() -> None:
    docker_script = (ROOT / "scripts" / "check-docker.sh").read_text(encoding="utf-8")
    python_script = (ROOT / "scripts" / "check-python.sh").read_text(encoding="utf-8")

    assert "./scripts/check-python.sh" in docker_script
    assert "scripts/check-render-debug.sh" in python_script
```

- [ ] **Step 2: Run the contract tests and verify they fail**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_renderer_dependencies.py::test_render_debug_parity_script_is_declared tests/contracts/test_renderer_dependencies.py::test_check_python_runs_render_debug_parity_gate_after_fixture_builds tests/contracts/test_renderer_dependencies.py::test_docker_check_inherits_render_debug_parity_gate
```

Expected: FAIL because `scripts/check-render-debug.sh` does not exist and `scripts/check-python.sh` does not call it.

- [ ] **Step 3: Commit the red tests**

Run:

```bash
git add tests/contracts/test_renderer_dependencies.py
git commit -m "Test render debug parity script contract"
```

## Task 2: Script Skeleton And Gate Wiring

**Files:**
- Create: `scripts/check-render-debug.sh`
- Modify: `scripts/check-python.sh`
- Test: `tests/contracts/test_renderer_dependencies.py`

- [ ] **Step 1: Create the script skeleton**

Create `scripts/check-render-debug.sh` with this content:

```bash
#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/check-render-debug.sh [--inspect-only SITE_DIR DEBUG_DIR]

Run the focused render-debug parity gate for the render fixture:
  - build and serve the render fixture through raya preview
  - capture renderer debug screenshots with --render-debug
  - inspect summary.json for raw TeX, external requests, overflow, and screenshots
  - inspect generated HTML for browser-side MathJax runtime or external renderer resources

Environment:
  UV_PROJECT_ENVIRONMENT defaults to .venv-local.
  RAYA_RENDER_DEBUG_COURSE overrides the course path for tests.
  RAYA_RENDER_DEBUG_OUTPUT_DIR reuses a specific debug output directory.
  RAYA_RENDER_DEBUG_KEEP=1 keeps temporary debug output after the run.

Options:
  --inspect-only SITE_DIR DEBUG_DIR  Inspect an existing site/debug pair without running preview.
  -h, --help                        Show this help text.
USAGE
}

case "${1:-}" in
  -h | --help)
    usage
    exit 0
    ;;
  --inspect-only)
    if [[ $# -ne 3 ]]; then
      echo "--inspect-only requires SITE_DIR and DEBUG_DIR" >&2
      usage >&2
      exit 2
    fi
    INSPECT_ONLY=1
    INSPECT_SITE_DIR="$2"
    INSPECT_DEBUG_DIR="$3"
    ;;
  "")
    INSPECT_ONLY=0
    ;;
  *)
    echo "Unknown argument: $1" >&2
    usage >&2
    exit 2
    ;;
esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-.venv-local}"

COURSE="${RAYA_RENDER_DEBUG_COURSE:-examples/courses/render-fixture}"

if [[ "${INSPECT_ONLY:-0}" == "1" ]]; then
  SITE_DIR="$INSPECT_SITE_DIR"
  DEBUG_DIR="$INSPECT_DEBUG_DIR"
else
  SITE_DIR="$COURSE/artifact/site"
  if [[ -n "${RAYA_RENDER_DEBUG_OUTPUT_DIR:-}" ]]; then
    DEBUG_DIR="$RAYA_RENDER_DEBUG_OUTPUT_DIR"
    mkdir -p "$DEBUG_DIR"
    CLEANUP_DEBUG=0
  else
    DEBUG_DIR="$(mktemp -d "${TMPDIR:-/tmp}/raya-render-debug.XXXXXX")"
    CLEANUP_DEBUG=1
  fi
  if [[ "${RAYA_RENDER_DEBUG_KEEP:-0}" == "1" ]]; then
    CLEANUP_DEBUG=0
  fi
  cleanup() {
    if [[ "${CLEANUP_DEBUG:-0}" == "1" ]]; then
      rm -rf "$DEBUG_DIR"
    fi
  }
  trap cleanup EXIT

  echo "check-render-debug: uv run raya preview $COURSE --port 0 --render-debug $DEBUG_DIR"
  uv run raya preview "$COURSE" --port 0 --render-debug "$DEBUG_DIR"
fi

python - "$SITE_DIR" "$DEBUG_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

site_dir = Path(sys.argv[1])
debug_dir = Path(sys.argv[2])
summary_path = debug_dir / "summary.json"
expected = {
    ("index", "desktop"): "desktop-index.png",
    ("index", "mobile"): "mobile-index.png",
    ("static-path", "desktop"): "desktop-static-path.png",
    ("static-path", "mobile"): "mobile-static-path.png",
}
errors: list[str] = []

def fail(message: str) -> None:
    errors.append(message)

try:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
except Exception as exc:
    summary = {"captures": []}
    fail(f"missing or malformed summary.json at {summary_path}: {exc}")

captures = summary.get("captures")
if not isinstance(captures, list):
    captures = []
    fail(f"summary.json captures must be a list at {summary_path}")

seen: dict[tuple[str, str], dict[str, object]] = {}
for capture in captures:
    if not isinstance(capture, dict):
        fail(f"summary.json capture must be an object: {capture!r}")
        continue
    page = capture.get("page")
    viewport = capture.get("viewport")
    viewport_name = viewport.get("name") if isinstance(viewport, dict) else None
    if isinstance(page, str) and isinstance(viewport_name, str):
        seen[(page, viewport_name)] = capture
    if capture.get("raw_tex_visible"):
        fail(f"visible raw TeX in capture page={page!r} viewport={viewport_name!r}")
    external_requests = capture.get("external_requests")
    if external_requests:
        fail(f"external requests in capture page={page!r} viewport={viewport_name!r}: {external_requests}")
    overflow = capture.get("horizontal_overflow", 0)
    if isinstance(overflow, (int, float)) and overflow > 1:
        fail(f"horizontal overflow in capture page={page!r} viewport={viewport_name!r}: {overflow}")
    elif not isinstance(overflow, (int, float)):
        fail(f"horizontal_overflow must be numeric in capture page={page!r} viewport={viewport_name!r}")

for key, screenshot_name in expected.items():
    capture = seen.get(key)
    if capture is None:
        fail(f"missing expected capture page={key[0]} viewport={key[1]}")
        continue
    screenshot_value = capture.get("screenshot")
    screenshot = Path(str(screenshot_value)) if screenshot_value else debug_dir / screenshot_name
    if not screenshot.is_absolute():
        screenshot = debug_dir / screenshot
    if screenshot.name != screenshot_name:
        fail(f"unexpected screenshot for page={key[0]} viewport={key[1]}: {screenshot}")
    if not screenshot.is_file() or screenshot.stat().st_size <= 0:
        fail(f"missing or empty screenshot {screenshot}")

html_paths = sorted(site_dir.rglob("*.html")) if site_dir.is_dir() else []
if not html_paths:
    fail(f"no generated HTML found under {site_dir}")

blocked_fragments = (
    "MathJax.js",
    "tex-mml-chtml",
    "cdn.jsdelivr.net",
    "unpkg.com",
    "cdnjs.cloudflare.com",
    "polyfill.io",
    "https://cdn",
    "http://cdn",
)
for html_path in html_paths:
    text = html_path.read_text(encoding="utf-8")
    for fragment in blocked_fragments:
        if fragment in text:
            fail(f"browser-side or external renderer dependency {fragment!r} in {html_path}")

if errors:
    for error in errors:
        print(f"check-render-debug: ERROR: {error}", file=sys.stderr)
    sys.exit(1)

print(f"check-render-debug: inspected {len(captures)} capture(s) and {len(html_paths)} HTML file(s)")
PY

echo "check-render-debug: passed"
```

- [ ] **Step 2: Make the script executable**

Run:

```bash
chmod +x scripts/check-render-debug.sh
```

- [ ] **Step 3: Wire it into `scripts/check-python.sh`**

Edit `scripts/check-python.sh`:

1. In the usage list, add:

```text
  - render-debug parity gate for the render fixture
```

2. After the course validate/build/inspect loop and before `run uv run raya validate docs`, add:

```bash
run scripts/check-render-debug.sh
```

- [ ] **Step 4: Run the contract tests and verify they pass**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_renderer_dependencies.py::test_render_debug_parity_script_is_declared tests/contracts/test_renderer_dependencies.py::test_check_python_runs_render_debug_parity_gate_after_fixture_builds tests/contracts/test_renderer_dependencies.py::test_docker_check_inherits_render_debug_parity_gate
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/check-render-debug.sh scripts/check-python.sh tests/contracts/test_renderer_dependencies.py
git commit -m "Add render debug parity gate script"
```

## Task 3: Focused Gate Behavior Tests

**Files:**
- Create: `tests/e2e/test_render_debug_parity_gate.py`
- Modify: `scripts/check-render-debug.sh`

- [ ] **Step 1: Add focused e2e and negative tests**

Create `tests/e2e/test_render_debug_parity_gate.py`:

```python
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RENDER_FIXTURE = ROOT / "examples" / "courses" / "render-fixture"
SCRIPT = ROOT / "scripts" / "check-render-debug.sh"


def run_gate(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = {**os.environ, **(env or {})}
    merged_env.setdefault("UV_PROJECT_ENVIRONMENT", ".venv-local")
    return subprocess.run(
        [str(SCRIPT), *args],
        cwd=ROOT,
        env=merged_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )


def test_render_debug_parity_gate_passes_on_render_fixture_copy(tmp_path: Path) -> None:
    course = tmp_path / "render-fixture"
    debug_dir = tmp_path / "debug"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    result = run_gate(
        env={
            "RAYA_RENDER_DEBUG_COURSE": str(course),
            "RAYA_RENDER_DEBUG_OUTPUT_DIR": str(debug_dir),
            "RAYA_RENDER_DEBUG_KEEP": "1",
        },
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "check-render-debug: passed" in result.stdout
    assert (debug_dir / "summary.json").is_file()
    assert (debug_dir / "desktop-index.png").stat().st_size > 0
    assert (debug_dir / "mobile-static-path.png").stat().st_size > 0


def test_render_debug_parity_gate_fails_on_visible_raw_tex(tmp_path: Path) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    summary_path = debug_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["captures"][0]["raw_tex_visible"] = True
    summary["captures"][0]["raw_tex_markers"] = ["$x^2$"]
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir))

    assert result.returncode == 1
    assert "visible raw TeX" in result.stderr


def test_render_debug_parity_gate_fails_on_external_requests(tmp_path: Path) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    summary_path = debug_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["captures"][1]["external_requests"] = ["https://cdn.example/math.css"]
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir))

    assert result.returncode == 1
    assert "external requests" in result.stderr


def test_render_debug_parity_gate_fails_on_missing_screenshot(tmp_path: Path) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    (debug_dir / "mobile-static-path.png").unlink()

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir))

    assert result.returncode == 1
    assert "missing or empty screenshot" in result.stderr


def test_render_debug_parity_gate_fails_on_horizontal_overflow(tmp_path: Path) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    summary_path = debug_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["captures"][2]["horizontal_overflow"] = 12
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir))

    assert result.returncode == 1
    assert "horizontal overflow" in result.stderr


def test_render_debug_parity_gate_fails_on_browser_side_mathjax_runtime(tmp_path: Path) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    html_path = site_dir / "index.html"
    html_path.write_text(
        '<html><head><script src="https://cdn.jsdelivr.net/npm/mathjax/tex-mml-chtml.js"></script></head></html>',
        encoding="utf-8",
    )

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir))

    assert result.returncode == 1
    assert "browser-side or external renderer dependency" in result.stderr


def write_debug_fixture(tmp_path: Path) -> tuple[Path, Path]:
    site_dir = tmp_path / "site"
    debug_dir = tmp_path / "debug"
    (site_dir / "static-path").mkdir(parents=True)
    debug_dir.mkdir()
    (site_dir / "index.html").write_text("<html><body><mjx-container></mjx-container></body></html>", encoding="utf-8")
    (site_dir / "static-path" / "index.html").write_text("<html><body>static</body></html>", encoding="utf-8")

    captures = []
    for page, viewport, screenshot in (
        ("index", "desktop", "desktop-index.png"),
        ("index", "mobile", "mobile-index.png"),
        ("static-path", "desktop", "desktop-static-path.png"),
        ("static-path", "mobile", "mobile-static-path.png"),
    ):
        screenshot_path = debug_dir / screenshot
        screenshot_path.write_bytes(b"png")
        captures.append(
            {
                "page": page,
                "url": f"http://127.0.0.1/{page}/index.html",
                "viewport": {"name": viewport, "width": 1280 if viewport == "desktop" else 390, "height": 900 if viewport == "desktop" else 844},
                "screenshot": str(screenshot_path),
                "mathjax_container_count": 1,
                "raw_tex_visible": False,
                "raw_tex_markers": [],
                "external_requests": [],
                "horizontal_overflow": 0,
            }
        )
    (debug_dir / "summary.json").write_text(json.dumps({"captures": captures}), encoding="utf-8")
    return site_dir, debug_dir
```

- [ ] **Step 2: Run the focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_render_debug_parity_gate.py
```

Expected: PASS after Task 2 implementation. If any negative test fails, adjust `scripts/check-render-debug.sh` diagnostics or inspection logic until all pass.

- [ ] **Step 3: Run the script directly**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local scripts/check-render-debug.sh
```

Expected: exit 0 and output ending in `check-render-debug: passed`.

- [ ] **Step 4: Commit**

Run:

```bash
git add tests/e2e/test_render_debug_parity_gate.py scripts/check-render-debug.sh
git commit -m "Test render debug parity gate behavior"
```

## Task 4: Role Documentation

**Files:**
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update English contributor docs**

In `docs/guides/en/contributors/index.md`, update the renderer-debug paragraph to include the focused gate:

```markdown
Before changing renderer behavior, run the focused parity gate with `scripts/check-render-debug.sh`. It builds and previews `examples/courses/render-fixture`, captures desktop/mobile render-debug artifacts, and fails on visible raw TeX, external renderer requests, missing screenshots, overflow, or browser-side MathJax runtime dependencies. For an individual course regression, use `raya preview <course> --render-debug /tmp/raya-render-debug`. Treat those files as local evidence only; do not commit them and do not treat them as artifact authority.
```

- [ ] **Step 2: Update English agent docs**

In `docs/guides/en/agents/index.md`, update the renderer-debug paragraph to include:

```markdown
Use `scripts/check-render-debug.sh` when you need the focused fixture parity gate that also runs in host/Docker verification. Use `raya preview <course> --render-debug /tmp/raya-render-debug` when diagnosing a specific course. Both paths inspect generated static pages; neither path executes course code or relies on browser-side MathJax conversion.
```

- [ ] **Step 3: Update Spanish contributor docs**

In `docs/guides/es/colaboradores/index.md`, update the renderer-debug paragraph to include:

```markdown
Antes de cambiar comportamiento del renderizador, ejecuta la compuerta enfocada con `scripts/check-render-debug.sh`. Construye y previsualiza `examples/courses/render-fixture`, captura evidencia desktop/mobile y falla si hay TeX crudo visible, requests externos del renderizador, screenshots faltantes, overflow o dependencias MathJax ejecutadas en el browser. Para una regresion de un curso especifico, usa `raya preview <course> --render-debug /tmp/raya-render-debug`. Trata esos archivos solo como evidencia local; no los confirmes en git ni los trates como autoridad del artifact.
```

- [ ] **Step 4: Update Spanish agent docs**

In `docs/guides/es/agentes/index.md`, update the renderer-debug paragraph to include:

```markdown
Usa `scripts/check-render-debug.sh` cuando necesites la compuerta enfocada de paridad del fixture que tambien corre en la verificacion host/Docker. Usa `raya preview <course> --render-debug /tmp/raya-render-debug` cuando diagnostiques un curso especifico. Ambos caminos inspeccionan paginas static generadas; ninguno ejecuta codigo del curso ni depende de conversion MathJax en el browser.
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
git commit -m "Document render debug parity gate"
```

## Task 5: Verification And Code Review

**Files:**
- Modify: `docs/superpowers/plans/2026-06-15-render-debug-parity-gate.md`

- [x] **Step 1: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_renderer_dependencies.py::test_render_debug_parity_script_is_declared tests/contracts/test_renderer_dependencies.py::test_check_python_runs_render_debug_parity_gate_after_fixture_builds tests/contracts/test_renderer_dependencies.py::test_docker_check_inherits_render_debug_parity_gate tests/e2e/test_render_debug_parity_gate.py
UV_PROJECT_ENVIRONMENT=.venv-local scripts/check-render-debug.sh
```

Expected: all selected tests pass and the script exits 0.

- [x] **Step 2: Run host gate**

Run:

```bash
./scripts/check.sh
```

Expected: exit 0 with `check: passed`.

- [x] **Step 3: Run Docker gate**

Run:

```bash
./scripts/check-docker.sh
```

Expected: exit 0 with `check-docker: passed`.

- [x] **Step 4: Request code review**

Use `superpowers:requesting-code-review` over the implementation commits after the design and plan commits. Ask the reviewer to focus on:

```text
Review the render-debug parity gate for script safety, deterministic diagnostics, temp directory cleanup, no browser-side MathJax dependency checks, host/Docker wiring, and role documentation drift.
```

- [x] **Step 5: Address review findings with TDD**

For each accepted finding:

```text
1. Write or update a failing focused test.
2. Run the focused test and confirm the expected failure.
3. Implement the minimal fix.
4. Re-run the focused test and relevant gate.
5. Commit the fix.
```

- [x] **Step 6: Update this plan with execution status**

Append:

```markdown
## Execution Status

- Implemented in commits:
  - `<hash>` `<subject>`
- Verification run:
  - `<command>`: passed
- Code review: requested and addressed.
```

- [x] **Step 7: Commit the execution status**

Run:

```bash
git add docs/superpowers/plans/2026-06-15-render-debug-parity-gate.md
git commit -m "Track render debug parity gate execution"
```

## Self-Review

- Spec coverage: tasks cover the focused script, summary and screenshot assertions, browser-side MathJax runtime checks, `check-python.sh` wiring, Docker inheritance through `check-docker.sh`, role docs, host/Docker verification, and review.
- Placeholder scan: no TBD, TODO, or open-ended implementation steps remain.
- Type consistency: environment variable names, paths, script flags, and expected diagnostics are consistent across tasks.

## Execution Status

- Implemented in commits:
  - `27ec8a8` Test render debug parity script contract
  - `c07e845` Add render debug parity gate script
  - `ceffdcb` Test render debug parity gate behavior
  - `b6473f2` Document render debug parity gate
  - `491d6dd` Harden render debug parity gate checks
- Verification run:
  - `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_renderer_dependencies.py tests/e2e/test_render_debug_parity_gate.py && UV_PROJECT_ENVIRONMENT=.venv-local scripts/check-render-debug.sh`: passed, `20 passed`, `check-render-debug: passed`
  - `./scripts/check.sh`: passed, `218 passed`, `check: passed`
  - `./scripts/check-docker.sh`: passed, `218 passed`, `check-docker: passed`
- Code review: requested with `superpowers:requesting-code-review`; both important findings and the command-guidance drift were addressed with TDD regression coverage.
