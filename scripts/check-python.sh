#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/check-python.sh

Run Python/Raya verification:
  - uv sync --python 3.10 --all-packages --dev
  - uv run pytest -q
  - representative fixture validate/build/inspect
  - docs validate/build/inspect

Options:
  -h, --help  Show this help text.
USAGE
}

case "${1:-}" in
  -h | --help)
    usage
    exit 0
    ;;
  "")
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

run() {
  echo "check-python: $*"
  "$@"
}

run uv sync --python 3.10 --all-packages --dev
run uv run pytest -q

courses=(
  examples/courses/minimal
  examples/courses/ordered-fixture
  examples/courses/render-fixture
  examples/courses/reference-fixture
  examples/courses/runtime-fixture
  examples/courses/execution-fixture
)

for course in "${courses[@]}"; do
  run uv run raya validate "$course"
  run uv run raya build "$course"
  run uv run raya artifacts inspect "$course/artifact"
done

run uv run raya validate docs
run uv run raya build docs
run uv run raya artifacts inspect docs/artifact

echo "check-python: passed"
