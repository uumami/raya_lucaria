#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/check-docker.sh

Run the Docker Compose verification path:
  RAYA_DOCKER_USER=<caller uid:gid> docker compose run --rm dev node --version
  RAYA_DOCKER_USER=<caller uid:gid> docker compose run --rm dev npm --version
  RAYA_DOCKER_USER=<caller uid:gid> docker compose run --rm dev npx --version
  RAYA_DOCKER_USER=<caller uid:gid> docker compose run --rm dev ./scripts/check-python.sh

This command verifies Node/npm renderer tooling and Python/Raya behavior inside the reference container.
Host-only checks such as OpenSpec validation run through scripts/check.sh.
By default, RAYA_DOCKER_USER uses the caller UID:GID; set it explicitly to
override the Compose user.

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

export RAYA_DOCKER_USER="${RAYA_DOCKER_USER:-$(id -u):$(id -g)}"

run_docker() {
  echo "check-docker: RAYA_DOCKER_USER=$RAYA_DOCKER_USER docker $*"
  docker "$@"
}

run_docker compose run --rm dev node --version
run_docker compose run --rm dev npm --version
run_docker compose run --rm dev npx --version
run_docker compose run --rm dev ./scripts/check-python.sh
echo "check-docker: passed"
