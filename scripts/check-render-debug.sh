#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/check-render-debug.sh [--inspect-only SITE_DIR DEBUG_DIR [COPIED_SITE_DIR]]

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
  --inspect-only SITE_DIR DEBUG_DIR [COPIED_SITE_DIR]
                                     Inspect an existing site/debug pair without running preview.
  -h, --help                         Show this help text.
USAGE
}

case "${1:-}" in
  -h | --help)
    usage
    exit 0
    ;;
  --inspect-only)
    if [[ $# -ne 3 && $# -ne 4 ]]; then
      echo "--inspect-only requires SITE_DIR and DEBUG_DIR with optional COPIED_SITE_DIR" >&2
      usage >&2
      exit 2
    fi
    INSPECT_ONLY=1
    INSPECT_SITE_DIR="$2"
    INSPECT_DEBUG_DIR="$3"
    INSPECT_COPIED_SITE_DIR="${4:-}"
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
  COPIED_SITE_DIR="$INSPECT_COPIED_SITE_DIR"
  CLEANUP_DEBUG=0
  CLEANUP_COPIED_SITE=0
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

  echo "check-render-debug: uv run raya preview $COURSE --port 0 --render-debug $DEBUG_DIR"
  uv run raya preview "$COURSE" --port 0 --render-debug "$DEBUG_DIR"

  COPIED_SITE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/raya-render-site-copy.XXXXXX")"
  CLEANUP_COPIED_SITE=1
  cp -R "$SITE_DIR"/. "$COPIED_SITE_DIR"/
fi

cleanup() {
  if [[ "${CLEANUP_DEBUG:-0}" == "1" ]]; then
    rm -rf "$DEBUG_DIR"
  fi
  if [[ "${CLEANUP_COPIED_SITE:-0}" == "1" ]]; then
    rm -rf "$COPIED_SITE_DIR"
  fi
}
trap cleanup EXIT

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

echo "check-render-debug: passed"
