#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/check.sh

Run the canonical host repository check:
  - git diff --check
  - scripts/check-hygiene.sh
  - openspec validate --specs --strict
  - Python/Raya verification through scripts/check-python.sh

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

run() {
  echo "check: $*"
  "$@"
}

run git diff --check
run scripts/check-hygiene.sh
run openspec validate --specs --strict
run scripts/check-python.sh

echo "check: passed"
