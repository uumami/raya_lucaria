#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/check-docker.sh

Run the Docker Compose verification path:
  docker compose run --rm dev ./scripts/check-python.sh

This command verifies Python/Raya behavior inside the reference container.
Host-only checks such as OpenSpec validation run through scripts/check.sh.

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

echo "check-docker: docker compose run --rm dev ./scripts/check-python.sh"
docker compose run --rm dev ./scripts/check-python.sh
echo "check-docker: passed"
