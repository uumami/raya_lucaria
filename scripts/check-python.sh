#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/check-python.sh

Run Python/Raya verification:
  - npm ci --ignore-scripts --no-audit --no-fund
  - npm run raya-render-math -- --self-test
  - uv sync --python 3.10 --all-packages --dev
  - uv run pytest -q
  - representative fixture validate/build/inspect
  - docs validate/build/inspect

Node/MathJax renderer dependency installation runs before Python/Raya checks so
build-time math rendering dependencies are ready for tests that need them.

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

run npm ci --ignore-scripts --no-audit --no-fund
run npm run raya-render-math -- --self-test
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
run uv run raya preview examples/courses/minimal --dry-run

echo "check-python: passed"
