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

uv run python - "$SITE_DIR" "$DEBUG_DIR" <<'PY'
from __future__ import annotations

import json
import re
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
        fail(
            "external requests in capture "
            f"page={page!r} viewport={viewport_name!r}: {external_requests}"
        )
    overflow = capture.get("horizontal_overflow", 0)
    if isinstance(overflow, (int, float)) and overflow > 1:
        fail(
            "horizontal overflow in capture "
            f"page={page!r} viewport={viewport_name!r}: {overflow}"
        )
    elif not isinstance(overflow, (int, float)):
        fail(
            "horizontal_overflow must be numeric in capture "
            f"page={page!r} viewport={viewport_name!r}"
        )

for key, screenshot_name in expected.items():
    capture = seen.get(key)
    if capture is None:
        fail(f"missing expected capture page={key[0]} viewport={key[1]}")
        continue
    screenshot = debug_dir / screenshot_name
    screenshot_value = capture.get("screenshot")
    if screenshot_value:
        declared_screenshot = Path(str(screenshot_value))
        if not declared_screenshot.is_absolute():
            declared_screenshot = debug_dir / declared_screenshot
        declared_screenshot = declared_screenshot.resolve()
        try:
            declared_screenshot.relative_to(debug_dir.resolve())
        except ValueError:
            fail(
                "screenshot path is outside debug directory "
                f"for page={key[0]} viewport={key[1]}: {declared_screenshot}"
            )
        if declared_screenshot.name != screenshot_name:
            fail(
                "unexpected screenshot for "
                f"page={key[0]} viewport={key[1]}: {declared_screenshot}"
            )
    if not screenshot.is_file() or screenshot.stat().st_size <= 0:
        fail(f"missing or empty screenshot {screenshot}")

html_paths = sorted(site_dir.rglob("*.html")) if site_dir.is_dir() else []
if not html_paths:
    fail(f"no generated HTML found under {site_dir}")

blocked_fragments = (
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
for html_path in html_paths:
    text = html_path.read_text(encoding="utf-8")
    text_lower = text.lower()
    for fragment in blocked_fragments:
        if fragment in text_lower:
            fail(f"browser-side or external renderer dependency {fragment!r} in {html_path}")
    if re.search(r"_raya/render/math/[^\"')\s>]+\.js\b", text_lower):
        fail(f"browser-side or external renderer dependency '_raya/render/math/*.js' in {html_path}")

if errors:
    for error in errors:
        print(f"check-render-debug: ERROR: {error}", file=sys.stderr)
    sys.exit(1)

print(f"check-render-debug: inspected {len(captures)} capture(s) and {len(html_paths)} HTML file(s)")
PY

echo "check-render-debug: passed"
