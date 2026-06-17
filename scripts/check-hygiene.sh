#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/check-hygiene.sh [--root PATH]

Run repository hygiene checks:
  - stale current guidance scans
  - stale renderer stack scans
  - current spec/doc incomplete marker scans
  - generated-output git pollution scans
  - examples gallery fixture authority label scan

Options:
  --root PATH  Repository root to check. Defaults to the parent of scripts/.
  -h, --help   Show this help text.
USAGE
}

ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --root" >&2
        usage >&2
        exit 2
      fi
      ROOT="$2"
      shift 2
      ;;
    --root=*)
      ROOT="${1#--root=}"
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$ROOT" ]]; then
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
else
  ROOT="$(cd "$ROOT" && pwd)"
fi

cd "$ROOT"

failures=0

run_check() {
  local name="$1"
  shift

  echo "hygiene: $name"
  if ! "$@"; then
    failures=$((failures + 1))
  fi
}

existing_paths() {
  local path

  for path in "$@"; do
    if [[ -e "$path" ]]; then
      printf '%s\n' "$path"
    fi
  done
}

reject_matches() {
  local label="$1"
  local pattern="$2"
  shift 2

  local rg_args=(
    --glob '!openspec/changes/archive/**'
    --glob '!docs/superpowers/**'
  )

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --rg-glob)
        if [[ $# -lt 2 ]]; then
          echo "FAILED: $label scan received --rg-glob without a value"
          return 1
        fi
        rg_args+=(--glob "$2")
        shift 2
        ;;
      --)
        shift
        break
        ;;
      *)
        break
        ;;
    esac
  done

  local paths=()
  local path
  while IFS= read -r path; do
    paths+=("$path")
  done < <(existing_paths "$@")

  if [[ "${#paths[@]}" -eq 0 ]]; then
    echo "passed: $label (no scan paths present)"
    return 0
  fi

  local output
  local status
  set +e
  output="$(
    rg -n \
      "${rg_args[@]}" \
      -- "$pattern" "${paths[@]}" 2>&1
  )"
  status=$?
  set -e

  if [[ "$status" -eq 0 ]]; then
    echo "FAILED: $label"
    echo "$output"
    return 1
  fi

  if [[ "$status" -eq 1 ]]; then
    echo "passed: $label"
    return 0
  fi

  echo "FAILED: $label scan could not run"
  echo "$output"
  return 1
}

check_stale_code_notebook_guidance() {
  reject_matches \
    "stale code/notebook folder requirement" \
    'under accepted `code/` or `notebooks/` support roots|must resolve under accepted `code/`|must resolve under accepted `notebooks/`|required `code/` support roots?|required `notebooks/` support roots?|must live under `code/`|must live under `notebooks/`' \
    README.md \
    AGENTS.md \
    docs/foundation \
    docs/guides \
    openspec/config.yaml \
    openspec/specs \
    packages
}

check_stale_renderer_guidance() {
  reject_matches \
    "stale renderer stack guidance" \
    'Eleventy|Tailwind|Pagefind' \
    --rg-glob '!docs/foundation/14_domain_language.md' \
    -- \
    docs/foundation \
    openspec/specs \
    docs/guides \
    packages
}

check_incomplete_markers() {
  reject_matches \
    "current spec/doc incomplete markers" \
    '(^|[^`[:alnum:]_])(Purpose:[[:space:]]*TBD|TBD|TODO|FIXME)([^`[:alnum:]_]|$)' \
    openspec/specs \
    docs/foundation \
    docs/guides \
    README.md \
    AGENTS.md
}

generated_path_pattern() {
  printf '%s' '(^|/)(artifact|site|_site|dist|build|coverage|htmlcov|node_modules|__pycache__|\.pytest_cache|\.ruff_cache|\.mypy_cache|\.tox|\.nox|\.hypothesis|\.superpowers|\.uv-cache|\.cache|raya-render-debug[^/]*|render-debug)(/|$)'
}

render_debug_path_pattern() {
  printf '%s' '(^|/)(raya-render-debug[^/]*|render-debug)(/|$)'
}

check_git_available() {
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "FAILED: $ROOT is not a git worktree"
    return 1
  fi
}

check_tracked_generated_outputs() {
  check_git_available || return 1

  local output
  local status
  set +e
  output="$(git ls-files | rg "$(generated_path_pattern)" 2>&1)"
  status=$?
  set -e

  if [[ "$status" -eq 0 ]]; then
    echo "FAILED: generated output tracked by git"
    echo "$output"
    return 1
  fi

  if [[ "$status" -eq 1 ]]; then
    echo "passed: generated output tracked by git"
    return 0
  fi

  echo "FAILED: generated output tracked by git scan could not run"
  echo "$output"
  return 1
}

check_untracked_generated_outputs() {
  check_git_available || return 1

  local output
  local status
  set +e
  output="$(
    git status --porcelain --untracked-files=all |
      sed -n 's/^?? //p' |
      rg "$(generated_path_pattern)" 2>&1
  )"
  status=$?
  set -e

  if [[ "$status" -eq 0 ]]; then
    echo "FAILED: generated output appears as untracked source"
    echo "$output"
    return 1
  fi

  if [[ "$status" -eq 1 ]]; then
    echo "passed: generated output appears as untracked source"
    return 0
  fi

  echo "FAILED: generated output appears as untracked source scan could not run"
  echo "$output"
  return 1
}

check_ignored_render_debug_outputs() {
  check_git_available || return 1

  local output
  local status
  set +e
  output="$(
    git status --porcelain --ignored=matching --untracked-files=all |
      sed -n 's/^!! //p' |
      rg "$(render_debug_path_pattern)" 2>&1
  )"
  status=$?
  set -e

  if [[ "$status" -eq 0 ]]; then
    echo "FAILED: ignored render-debug outputs"
    echo "$output"
    return 1
  fi

  if [[ "$status" -eq 1 ]]; then
    echo "passed: ignored render-debug outputs"
    return 0
  fi

  echo "FAILED: ignored render-debug outputs scan could not run"
  echo "$output"
  return 1
}

check_gallery_fixture_label() {
  if [[ ! -e examples/gallery && ! -e examples/gallery/index.html ]]; then
    echo "passed: examples gallery fixture authority label (not present)"
    return 0
  fi

  if [[ ! -f examples/gallery/index.html ]]; then
    echo "FAILED: examples/gallery/index.html is missing"
    return 1
  fi

  if ! rg -n 'fixture material|accepted OpenSpec specs|foundation docs' examples/gallery/index.html >/dev/null; then
    echo "FAILED: examples/gallery/index.html does not label fixture authority"
    return 1
  fi

  echo "passed: examples gallery fixture authority label"
}

echo "hygiene: root $ROOT"
run_check "stale code/notebook folder requirement" check_stale_code_notebook_guidance
run_check "stale renderer stack guidance" check_stale_renderer_guidance
run_check "current spec/doc incomplete markers" check_incomplete_markers
run_check "tracked generated outputs" check_tracked_generated_outputs
run_check "untracked generated outputs" check_untracked_generated_outputs
run_check "ignored render-debug outputs" check_ignored_render_debug_outputs
run_check "examples gallery fixture label" check_gallery_fixture_label

if [[ "$failures" -ne 0 ]]; then
  echo "hygiene: failed with $failures issue(s)"
  exit 1
fi

echo "hygiene: passed"
