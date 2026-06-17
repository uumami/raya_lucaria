#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

lock_message() {
  cat >&2 <<'LOCK'
Another Raya verification is preparing dependencies.
Wait for it to finish, then rerun this command.
LOCK
}

release_dependency_lock() {
  if [[ -n "${RAYA_CHECK_LOCK_HELD:-}" && -n "${RAYA_CHECK_LOCK_DIR:-}" ]]; then
    rmdir "$RAYA_CHECK_LOCK_DIR" 2>/dev/null || true
    unset RAYA_CHECK_LOCK_HELD
  fi
}

acquire_dependency_lock() {
  RAYA_CHECK_LOCK_DIR="${RAYA_CHECK_LOCK_DIR:-$ROOT/.raya-check.lock}"
  if ! mkdir "$RAYA_CHECK_LOCK_DIR" 2>/dev/null; then
    lock_message
    return 75
  fi
  RAYA_CHECK_LOCK_HELD=1
  trap release_dependency_lock EXIT
  trap 'release_dependency_lock; exit 130' INT
  trap 'release_dependency_lock; exit 143' TERM
}

if [[ "${1:-}" == "--source-lock-functions" ]]; then
  return 0 2>/dev/null || exit 0
fi

usage() {
  cat <<'USAGE'
Usage: scripts/check-python.sh

Run Python/Raya verification:
  - npm ci --ignore-scripts --no-audit --no-fund
  - npm run raya-render-math -- --self-test
  - uv sync --python 3.10 --all-packages --dev
  - uv run pytest -q
  - representative fixture validate/build/inspect
  - render-debug parity gate for the render fixture
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

cd "$ROOT"

export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-.venv-local}"

run() {
  echo "check-python: $*"
  "$@"
}

acquire_dependency_lock
run npm ci --ignore-scripts --no-audit --no-fund
run npm run raya-render-math -- --self-test
run uv sync --python 3.10 --all-packages --dev
release_dependency_lock
trap - EXIT INT TERM

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

run scripts/check-render-debug.sh

run uv run raya validate docs
run uv run raya build docs
run uv run raya artifacts inspect docs/artifact
run uv run raya preview examples/courses/minimal --dry-run

echo "check-python: passed"
