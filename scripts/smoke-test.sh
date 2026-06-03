#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/raya-smoke.XXXXXX")"
external_course="$tmpdir/course"
initialized_course="$tmpdir/initialized-course"

cleanup() {
  rm -rf "$tmpdir"
}
trap cleanup EXIT

cp -R "$repo_root/examples/courses/minimal" "$external_course"

cd "$repo_root"

echo "smoke: validating external course locally"
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate "$external_course"

echo "smoke: building external course locally"
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build "$external_course"

echo "smoke: inspecting external artifact locally"
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya artifacts inspect "$external_course/artifact"

echo "smoke: initializing external course locally"
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya course init "$initialized_course" --course-id initialized-course --title "Initialized Course"

echo "smoke: validating initialized course locally"
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate "$initialized_course"

echo "smoke: building initialized course locally"
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build "$initialized_course"

echo "smoke: inspecting initialized artifact locally"
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya artifacts inspect "$initialized_course/artifact"

echo "smoke: validating external course in Docker"
docker compose run --rm --user "$(id -u):$(id -g)" --env UV_PROJECT_ENVIRONMENT=/tmp/raya-venv --volume "$external_course:/tmp/raya-smoke-course" dev uv run raya validate /tmp/raya-smoke-course

echo "smoke: building external course in Docker"
docker compose run --rm --user "$(id -u):$(id -g)" --env UV_PROJECT_ENVIRONMENT=/tmp/raya-venv --volume "$external_course:/tmp/raya-smoke-course" dev uv run raya build /tmp/raya-smoke-course

echo "smoke: inspecting external artifact in Docker"
docker compose run --rm --user "$(id -u):$(id -g)" --env UV_PROJECT_ENVIRONMENT=/tmp/raya-venv --volume "$external_course:/tmp/raya-smoke-course" dev uv run raya artifacts inspect /tmp/raya-smoke-course/artifact

echo "smoke: initializing course in Docker"
docker compose run --rm --user "$(id -u):$(id -g)" --env UV_PROJECT_ENVIRONMENT=/tmp/raya-venv --volume "$tmpdir:/tmp/raya-smoke-root" dev uv run raya course init /tmp/raya-smoke-root/docker-initialized-course --course-id docker-initialized-course --title "Docker Initialized Course"

echo "smoke: validating initialized course in Docker"
docker compose run --rm --user "$(id -u):$(id -g)" --env UV_PROJECT_ENVIRONMENT=/tmp/raya-venv --volume "$tmpdir:/tmp/raya-smoke-root" dev uv run raya validate /tmp/raya-smoke-root/docker-initialized-course

echo "smoke: building initialized course in Docker"
docker compose run --rm --user "$(id -u):$(id -g)" --env UV_PROJECT_ENVIRONMENT=/tmp/raya-venv --volume "$tmpdir:/tmp/raya-smoke-root" dev uv run raya build /tmp/raya-smoke-root/docker-initialized-course

echo "smoke: inspecting initialized artifact in Docker"
docker compose run --rm --user "$(id -u):$(id -g)" --env UV_PROJECT_ENVIRONMENT=/tmp/raya-venv --volume "$tmpdir:/tmp/raya-smoke-root" dev uv run raya artifacts inspect /tmp/raya-smoke-root/docker-initialized-course/artifact

echo "smoke: passed"
