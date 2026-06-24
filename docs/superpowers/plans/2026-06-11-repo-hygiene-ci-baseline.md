# Repo Hygiene And CI Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a repo hygiene and CI baseline that gives contributors and agents one canonical way to verify the current Raya Lucaria foundation and keep stale guidance, generated output, and workflow drift out of the repository.

**Architecture:** Add an OpenSpec change for the hygiene contract, then implement a small script layer around existing commands. Keep `scripts/check-python.sh` focused on Python/Raya validation, `scripts/check-hygiene.sh` focused on repository cleanliness scans, `scripts/check.sh` as the host canonical full check, and `scripts/check-docker.sh` as the Docker equivalent. CI calls the same scripts instead of duplicating logic.

**Tech Stack:** Bash, Python 3.10, `uv`, Docker Compose, OpenSpec 1.3.1, pytest, GitHub Actions.

---

## File Structure

Create:

- `openspec/changes/establish-repo-hygiene-and-ci-baseline/proposal.md` - why this hygiene baseline exists.
- `openspec/changes/establish-repo-hygiene-and-ci-baseline/design.md` - implementation choices and boundaries.
- `openspec/changes/establish-repo-hygiene-and-ci-baseline/specs/dev-workflow-baseline/spec.md` - canonical check and CI requirements.
- `openspec/changes/establish-repo-hygiene-and-ci-baseline/specs/documentation-surface-baseline/spec.md` - known-missing-work and doc consistency requirements.
- `openspec/changes/establish-repo-hygiene-and-ci-baseline/tasks.md` - OpenSpec implementation checklist.
- `scripts/check-python.sh` - local environment sync, tests, fixture builds, docs build, artifact inspections.
- `scripts/check-hygiene.sh` - stale current guidance, generated-output, OpenSpec incomplete-marker, and fixture-label scans.
- `scripts/check.sh` - host canonical check: hygiene, OpenSpec, Python/Raya verification.
- `scripts/check-docker.sh` - Docker verification path using the same Python/Raya check script inside the `dev` service.
- `.github/workflows/check.yml` - CI workflow that installs tools and runs canonical checks.
- `docs/foundation/18_known_missing_work.md` - compact deferred-work inventory.
- `tests/contracts/test_hygiene_scripts.py` - tests for script help, stale guidance detection, and command composition.

Modify:

- `.gitignore` - ensure generated/cache/session outputs stay ignored.
- `README.md` - replace long drifting command lists with canonical check commands and fix stale `code/`/`notebooks/` guidance.
- `AGENTS.md` - point agents to canonical checks and hygiene rules.
- `docs/foundation/00_index.md` - add known-missing-work entry.
- `docs/render-content/1_foundation/18_known_missing_work.md` - symlink to the new foundation doc.
- `docs/guides/en/contributors/index.md` - contributor check workflow.
- `docs/guides/es/colaboradores/index.md` - Spanish contributor check workflow.
- `docs/guides/en/agents/index.md` - agent check workflow.
- `docs/guides/es/agentes/index.md` - Spanish agent check workflow.
- `openspec/config.yaml` - future proposal hygiene expectations.

Do not modify archived OpenSpec changes just to modernize wording. Do not implement `polish-rendered-preview-workflow` in this cycle.

---

### Task 1: Park Current Preview Proposal And Open Hygiene Change

**Files:**
- Commit existing: `openspec/changes/polish-rendered-preview-workflow/**`
- Create: `openspec/changes/establish-repo-hygiene-and-ci-baseline/**`

- [ ] **Step 1: Verify current state**

Run:

```bash
git status --short
openspec list --json
openspec validate polish-rendered-preview-workflow --strict
```

Expected:

- `openspec/changes/polish-rendered-preview-workflow/` appears as untracked or already tracked.
- `polish-rendered-preview-workflow` validates.

- [ ] **Step 2: Commit the parked preview proposal if it is still uncommitted**

Run:

```bash
git add openspec/changes/polish-rendered-preview-workflow
git commit -m "Propose rendered preview workflow polish"
```

Expected:

- A commit is created if the proposal was uncommitted.
- If Git reports nothing staged, record that the proposal was already committed and continue.

- [ ] **Step 3: Create the hygiene OpenSpec change**

Run:

```bash
openspec new change establish-repo-hygiene-and-ci-baseline
```

Expected:

- `openspec/changes/establish-repo-hygiene-and-ci-baseline/.openspec.yaml` exists.

- [ ] **Step 4: Write the OpenSpec proposal**

Create `openspec/changes/establish-repo-hygiene-and-ci-baseline/proposal.md` with:

```markdown
## Why

The foundation, static renderer, explicit execution, reviewed outputs, and rendered-surface discipline now work, but the repository still lacks a single accepted hygiene and CI gate. Current contributors and agents must copy long command lists, and stale current guidance can survive after specs change.

This change makes cleanliness enforceable before more preview or pedagogy work: canonical checks, CI, generated-output ignore rules, stale-reference scans, and a known-missing-work inventory.

## What Changes

- Add canonical host and Docker verification scripts.
- Add CI that calls repository scripts instead of duplicating command lists.
- Add hygiene scans for stale current guidance, generated-output pollution, OpenSpec incomplete markers, fixture labeling, and command/source-layout drift.
- Clean current README, AGENTS, foundation docs, role guides, and OpenSpec config so they agree on commands and source layout.
- Add a known-missing-work document for deferred features and intentional gaps.
- Keep archived OpenSpec changes as history and leave the parked preview proposal out of implementation scope.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `dev-workflow-baseline`: Add canonical hygiene, local, Docker, and CI verification requirements.
- `documentation-surface-baseline`: Add known-missing-work and current-doc consistency requirements.

## Impact

- Affected scripts: `scripts/check.sh`, `scripts/check-python.sh`, `scripts/check-hygiene.sh`, `scripts/check-docker.sh`.
- Affected CI: `.github/workflows/check.yml`.
- Affected docs: `README.md`, `AGENTS.md`, foundation docs, rendered docs, English/Spanish contributor and agent guides, and `openspec/config.yaml`.
- Affected tests: contract tests for the new scripts and hygiene behavior.
- Out of scope: `raya preview`, visual e2e, rendered UX polish, cards, quizzes, spaced repetition, graph UI, identity, and dynamic services.
```

- [ ] **Step 5: Write the OpenSpec design**

Create `openspec/changes/establish-repo-hygiene-and-ci-baseline/design.md` by adapting the committed Superpowers design at `docs/superpowers/specs/2026-06-11-repo-hygiene-ci-baseline-design.md`. Keep the OpenSpec design shorter and include these decisions:

- Host full check is `./scripts/check.sh`.
- Docker check is `./scripts/check-docker.sh`.
- Python/Raya work lives in `./scripts/check-python.sh`.
- Repository cleanliness scans live in `./scripts/check-hygiene.sh`.
- CI calls scripts from the repo.
- Archived changes are historical and not rewritten for wording cleanup.
- The parked preview proposal remains out of scope.

- [ ] **Step 6: Write delta specs**

Create `openspec/changes/establish-repo-hygiene-and-ci-baseline/specs/dev-workflow-baseline/spec.md` with added requirements:

- `Canonical repository verification`: host check script, Docker check script, clear command output, no duplicated CI command list.
- `Repository hygiene verification`: stale current-guidance scan, generated-output pollution scan, OpenSpec incomplete-marker scan, fixture-label scan.
- `CI verification`: CI installs accepted tools, runs canonical scripts, and documents Docker limitations if any.

Create `openspec/changes/establish-repo-hygiene-and-ci-baseline/specs/documentation-surface-baseline/spec.md` with added requirements:

- `Known missing work documentation`: current deferred work is documented without becoming current requirements.
- `Current guidance consistency`: README, AGENTS, role docs, and OpenSpec config agree on canonical commands and source layout.

- [ ] **Step 7: Write OpenSpec tasks**

Create `openspec/changes/establish-repo-hygiene-and-ci-baseline/tasks.md` with checkboxes for:

- tests for scripts,
- check script implementation,
- CI workflow,
- stale guidance cleanup,
- known missing work doc,
- role guide and config updates,
- local and Docker verification,
- archive validation.

- [ ] **Step 8: Validate and commit the proposal**

Run:

```bash
openspec validate establish-repo-hygiene-and-ci-baseline --strict
openspec validate --specs --strict
git diff --check
git add openspec/changes/establish-repo-hygiene-and-ci-baseline
git commit -m "Propose repo hygiene CI baseline"
```

Expected:

- The new OpenSpec change validates.
- Current specs still validate.
- The proposal is committed separately from implementation.

---

### Task 2: Add Tests For Hygiene Scripts

**Files:**
- Create: `tests/contracts/test_hygiene_scripts.py`
- Test: `pytest -q tests/contracts/test_hygiene_scripts.py`

- [ ] **Step 1: Write failing tests**

Create `tests/contracts/test_hygiene_scripts.py`:

```python
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def run_script(*args: str, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    return subprocess.run(
        list(args),
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def test_hygiene_script_help() -> None:
    result = run_script("bash", "scripts/check-hygiene.sh", "--help")

    assert result.returncode == 0
    assert "Usage: scripts/check-hygiene.sh" in result.stdout
    assert "--root" in result.stdout


def test_hygiene_script_rejects_stale_required_code_notebook_guidance(tmp_path: Path) -> None:
    fixture = tmp_path / "repo"
    shutil.copytree(REPO_ROOT, fixture, ignore=shutil.ignore_patterns(".git", ".venv-local", ".superpowers"))
    readme = fixture / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + "\nLocal `.py` files must resolve under accepted `code/` support roots.\n",
        encoding="utf-8",
    )

    result = run_script("bash", "scripts/check-hygiene.sh", "--root", str(fixture))

    assert result.returncode != 0
    assert "stale code/notebook folder requirement" in result.stdout
    assert "README.md" in result.stdout


def test_hygiene_script_rejects_tracked_generated_output(tmp_path: Path) -> None:
    fixture = tmp_path / "repo"
    shutil.copytree(REPO_ROOT, fixture, ignore=shutil.ignore_patterns(".git", ".venv-local", ".superpowers"))
    run_script("git", "init", cwd=fixture)
    run_script("git", "add", ".", cwd=fixture)
    run_script("git", "commit", "-m", "fixture", cwd=fixture)
    generated = fixture / "examples" / "courses" / "minimal" / "artifact" / "site" / "index.html"
    generated.parent.mkdir(parents=True, exist_ok=True)
    generated.write_text("<html></html>\n", encoding="utf-8")
    run_script("git", "add", str(generated.relative_to(fixture)), cwd=fixture)

    result = run_script("bash", "scripts/check-hygiene.sh", "--root", str(fixture))

    assert result.returncode != 0
    assert "generated output tracked by git" in result.stdout


def test_check_script_help() -> None:
    result = run_script("bash", "scripts/check.sh", "--help")

    assert result.returncode == 0
    assert "Usage: scripts/check.sh" in result.stdout
    assert "scripts/check-python.sh" in result.stdout


def test_check_docker_script_help() -> None:
    result = run_script("bash", "scripts/check-docker.sh", "--help")

    assert result.returncode == 0
    assert "Usage: scripts/check-docker.sh" in result.stdout
    assert "docker compose" in result.stdout
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
pytest -q tests/contracts/test_hygiene_scripts.py
```

Expected:

- Tests fail because `scripts/check-hygiene.sh`, `scripts/check.sh`, and `scripts/check-docker.sh` do not exist yet.

- [ ] **Step 3: Commit failing tests**

Run:

```bash
git add tests/contracts/test_hygiene_scripts.py
git commit -m "Add hygiene script contract tests"
```

Expected:

- The commit contains only the new test file.

---

### Task 3: Implement Hygiene Scan Script

**Files:**
- Create: `scripts/check-hygiene.sh`
- Test: `tests/contracts/test_hygiene_scripts.py`

- [ ] **Step 1: Create `scripts/check-hygiene.sh`**

Create `scripts/check-hygiene.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/check-hygiene.sh [--root PATH]

Run repository hygiene checks:
  - stale current guidance scans
  - generated-output git pollution scans
  - OpenSpec incomplete marker scans
  - fixture labeling scans

Options:
  --root PATH  Repository root to check. Defaults to the parent of scripts/.
  -h, --help   Show this help text.
USAGE
}

ROOT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      ROOT="$2"
      shift 2
      ;;
    -h|--help)
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
  "$@" || failures=$((failures + 1))
}

reject_matches() {
  local label="$1"
  local pattern="$2"
  shift 2
  local output
  if output="$(rg -n --glob '!openspec/changes/archive/**' "$pattern" "$@" 2>/dev/null)"; then
    echo "FAILED: $label"
    echo "$output"
    return 1
  fi
  echo "passed: $label"
}

check_stale_code_notebook_guidance() {
  reject_matches \
    "stale code/notebook folder requirement" \
    'under accepted `code/` or `notebooks/` support roots|must resolve under accepted `code/`|must resolve under accepted `notebooks/`|required `code/` support root|required `notebooks/` support root|must live under `code/`|must live under `notebooks/`' \
    README.md AGENTS.md docs openspec/config.yaml openspec/specs packages
}

check_stale_renderer_guidance() {
  reject_matches \
    "stale renderer stack guidance" \
    'Eleventy|Tailwind|Pagefind' \
    docs/foundation openspec/specs docs/guides packages
}

check_incomplete_markers() {
  reject_matches \
    "current spec/doc incomplete markers" \
    'Purpose: TBD|TBD|FIXME|TODO' \
    openspec/specs docs/foundation docs/guides README.md AGENTS.md
}

check_tracked_generated_outputs() {
  local output
  if output="$(git ls-files | rg '(^|/)(artifact|site|__pycache__|\.pytest_cache|\.ruff_cache|node_modules|\.superpowers)(/|$)' 2>/dev/null)"; then
    echo "FAILED: generated output tracked by git"
    echo "$output"
    return 1
  fi
  echo "passed: generated output tracked by git"
}

check_untracked_generated_outputs() {
  local output
  if output="$(git status --porcelain --untracked-files=all | rg '^\?\? .*(^|/)(artifact|site|__pycache__|\.pytest_cache|\.ruff_cache|node_modules|\.superpowers)(/|$)' 2>/dev/null)"; then
    echo "FAILED: generated output appears as untracked source"
    echo "$output"
    return 1
  fi
  echo "passed: generated output appears as untracked source"
}

check_gallery_fixture_label() {
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

run_check "stale code/notebook folder requirement" check_stale_code_notebook_guidance
run_check "stale renderer stack guidance" check_stale_renderer_guidance
run_check "current spec/doc incomplete markers" check_incomplete_markers
run_check "tracked generated outputs" check_tracked_generated_outputs
run_check "untracked generated outputs" check_untracked_generated_outputs
run_check "examples gallery fixture label" check_gallery_fixture_label

if [[ "$failures" -ne 0 ]]; then
  echo "hygiene: failed with $failures issue(s)"
  exit 1
fi

echo "hygiene: passed"
```

- [ ] **Step 2: Make the script executable**

Run:

```bash
chmod +x scripts/check-hygiene.sh
```

- [ ] **Step 3: Run focused tests**

Run:

```bash
pytest -q tests/contracts/test_hygiene_scripts.py::test_hygiene_script_help tests/contracts/test_hygiene_scripts.py::test_hygiene_script_rejects_stale_required_code_notebook_guidance tests/contracts/test_hygiene_scripts.py::test_hygiene_script_rejects_tracked_generated_output
```

Expected:

- The three hygiene tests pass after stale README guidance is cleaned in Task 6. If they fail before cleanup because current README still contains stale wording, keep the failure visible and continue to Task 6 before committing.

---

### Task 4: Implement Canonical Check Scripts

**Files:**
- Create: `scripts/check-python.sh`
- Create: `scripts/check.sh`
- Create: `scripts/check-docker.sh`
- Test: `tests/contracts/test_hygiene_scripts.py`

- [ ] **Step 1: Create `scripts/check-python.sh`**

Create `scripts/check-python.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/check-python.sh

Run Python/Raya verification:
  - uv sync
  - pytest
  - representative fixture validate/build/inspect
  - docs validate/build/inspect
USAGE
}

case "${1:-}" in
  -h|--help)
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
```

- [ ] **Step 2: Create `scripts/check.sh`**

Create `scripts/check.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/check.sh

Run the canonical host repository check:
  - whitespace diff check
  - repository hygiene scans
  - OpenSpec strict validation
  - Python/Raya verification through scripts/check-python.sh
USAGE
}

case "${1:-}" in
  -h|--help)
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
```

- [ ] **Step 3: Create `scripts/check-docker.sh`**

Create `scripts/check-docker.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/check-docker.sh

Run the Docker Compose verification path:
  docker compose run --rm dev ./scripts/check-python.sh

This command verifies Python/Raya behavior inside the reference container.
Host-only checks such as OpenSpec validation run through scripts/check.sh.
USAGE
}

case "${1:-}" in
  -h|--help)
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
```

- [ ] **Step 4: Make scripts executable**

Run:

```bash
chmod +x scripts/check-python.sh scripts/check.sh scripts/check-docker.sh
```

- [ ] **Step 5: Run script help tests**

Run:

```bash
pytest -q tests/contracts/test_hygiene_scripts.py::test_check_script_help tests/contracts/test_hygiene_scripts.py::test_check_docker_script_help
```

Expected:

- Both tests pass.

- [ ] **Step 6: Commit scripts and tests**

Run:

```bash
git add scripts/check-python.sh scripts/check-hygiene.sh scripts/check.sh scripts/check-docker.sh tests/contracts/test_hygiene_scripts.py
git commit -m "Add canonical repository check scripts"
```

Expected:

- The commit contains script files and hygiene script tests.

---

### Task 5: Add CI Workflow

**Files:**
- Create: `.github/workflows/check.yml`

- [ ] **Step 1: Create CI workflow**

Create `.github/workflows/check.yml`:

```yaml
name: Checks

on:
  push:
  pull_request:

jobs:
  host-check:
    name: Host checks
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "22"

      - name: Set up uv
        uses: astral-sh/setup-uv@v5
        with:
          version: "0.9.7"

      - name: Install OpenSpec
        run: npm install -g @fission-ai/openspec@1.3.1

      - name: Run canonical host check
        run: ./scripts/check.sh

  docker-check:
    name: Docker checks
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Run Docker verification
        run: ./scripts/check-docker.sh
```

- [ ] **Step 2: Validate workflow syntax locally**

Run:

```bash
git diff --check .github/workflows/check.yml
```

Expected:

- No whitespace errors.

- [ ] **Step 3: Commit CI workflow**

Run:

```bash
git add .github/workflows/check.yml
git commit -m "Add canonical CI checks"
```

Expected:

- CI workflow is committed separately.

---

### Task 6: Clean Current Guidance And Add Known Missing Work

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `docs/foundation/00_index.md`
- Create: `docs/foundation/18_known_missing_work.md`
- Create: `docs/render-content/1_foundation/18_known_missing_work.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Modify: `openspec/config.yaml`

- [ ] **Step 1: Fix stale README code/notebook guidance**

In `README.md`, replace:

```markdown
Local `.py` and `.ipynb` references are source support links, not page links. They must resolve under accepted `code/` or `notebooks/` support roots, and cross-quantum references fail until a future shared-code contract exists.
```

with:

```markdown
Local `.py` and `.ipynb` references are source support links, not page links. They are classified by extension and own-or-ancestor learning-quantum ownership, not by required folder names. Folder names such as `scripts/`, `labs/`, `code/`, and `notebooks/` are ordinary author organization choices. Cross-quantum references fail until a future shared-code contract exists.
```

- [ ] **Step 2: Replace long command lists with canonical commands**

In `README.md`, keep the existing detailed examples only where they teach behavior, and add this canonical block near the top of Development Commands:

````markdown
Canonical checks:

```bash
./scripts/check.sh
./scripts/check-docker.sh
./scripts/smoke-test.sh
```

`./scripts/check.sh` is the host archive gate. `./scripts/check-docker.sh` runs the Python/Raya verification path inside the reference container. `./scripts/smoke-test.sh` validates, builds, and inspects temporary external courses locally and through Docker.
````

- [ ] **Step 3: Add known missing work foundation doc**

Create `docs/foundation/18_known_missing_work.md`:

```markdown
---
id: docs-known-missing-work
title: Known Missing Work
summary: Deferred capabilities and intentional gaps after the current foundation baseline.
status: ready
---
# Known Missing Work

This document names intentional gaps so they do not become tribal knowledge or accidental requirements.

## Deferred Static Workflow

- `raya preview <course>` local static preview command.
- Screenshot or visual e2e checks for rendered pages.
- Rendered examples/gallery polish beyond fixture review.

## Deferred Pedagogy

- Student-facing rendering for official cards, quizzes, prompts, and tasks.
- Personal notes, private cards, review queues, spaced repetition, confidence ratings, and mastery maps.
- Shared study state and course-level study planning.

## Deferred Graph And Search

- Backlinks, graph scopes, graph UI, and cross-course graph.
- Search indexes and browser search UI.

## Deferred Dynamic Domains

- Glintstone Key identity and registration.
- Rennala dynamic study state.
- Debate Parlor live classroom workflows.
- Sellen tutoring and agent workflows.
- Graven School collaboration, discussion, and annotation workflows.

## Deferred Deployment

- Hosted application packaging.
- Authentication provider adapters.
- Offline/PWA support.
- Multi-course installation operations.

## Rule

Deferred work is not current behavior. It becomes current only through an accepted OpenSpec change, implementation, tests, and documentation.
```

- [ ] **Step 4: Add known missing work to foundation index and rendered docs**

In `docs/foundation/00_index.md`, add:

```markdown
- [Known Missing Work](18_known_missing_work.md) -- deferred capabilities and intentional gaps.
```

Create the rendered-doc symlink:

```bash
ln -s ../../foundation/18_known_missing_work.md docs/render-content/1_foundation/18_known_missing_work.md
```

- [ ] **Step 5: Update contributor and agent role docs**

In `docs/guides/en/contributors/index.md` and `docs/guides/es/colaboradores/index.md`, add a compact note that contributors should run `./scripts/check.sh` before archive/commit and `./scripts/check-docker.sh` when Docker behavior changes.

In `docs/guides/en/agents/index.md` and `docs/guides/es/agentes/index.md`, add a compact note that agents should use canonical check scripts, avoid editing generated outputs, and keep deferred work in `docs/foundation/18_known_missing_work.md`.

- [ ] **Step 6: Update AGENTS and OpenSpec config**

In `AGENTS.md`, add the canonical check commands to Build/Test and add a rule that current guidance cleanup should update `README.md`, `AGENTS.md`, role docs, and `openspec/config.yaml` together.

In `openspec/config.yaml`, add a rule under `tasks` requiring hygiene changes to include canonical script checks, stale current-guidance scans, generated-output scans, and known-missing-work updates.

- [ ] **Step 7: Run hygiene scan and commit docs cleanup**

Run:

```bash
scripts/check-hygiene.sh
git diff --check
git add README.md AGENTS.md docs/foundation/00_index.md docs/foundation/18_known_missing_work.md docs/render-content/1_foundation/18_known_missing_work.md docs/guides/en/contributors/index.md docs/guides/es/colaboradores/index.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md openspec/config.yaml
git commit -m "Clean current guidance and document deferred work"
```

Expected:

- Hygiene scan passes.
- Current docs no longer claim code/notebook references require `code/` or `notebooks/` roots.

---

### Task 7: Apply, Sync, And Archive OpenSpec Change

**Files:**
- Modify: `openspec/specs/dev-workflow-baseline/spec.md`
- Modify: `openspec/specs/documentation-surface-baseline/spec.md`
- Move after archive: `openspec/changes/archive/YYYY-MM-DD-establish-repo-hygiene-and-ci-baseline/`

- [ ] **Step 1: Mark OpenSpec tasks complete as implementation lands**

During apply, update:

```bash
openspec/changes/establish-repo-hygiene-and-ci-baseline/tasks.md
```

Expected:

- Each completed task changes from `- [ ]` to `- [x]` only after code/docs/tests are done.

- [ ] **Step 2: Run OpenSpec validation**

Run:

```bash
openspec validate establish-repo-hygiene-and-ci-baseline --strict
openspec validate --specs --strict
```

Expected:

- The active change validates.
- Current specs validate.

- [ ] **Step 3: Sync delta specs into main specs**

Update:

- `openspec/specs/dev-workflow-baseline/spec.md`
- `openspec/specs/documentation-surface-baseline/spec.md`

Use the accepted delta requirements from the change. Do not edit archived changes.

- [ ] **Step 4: Archive the hygiene change**

Run:

```bash
today="$(date +%F)"
mv openspec/changes/establish-repo-hygiene-and-ci-baseline "openspec/changes/archive/${today}-establish-repo-hygiene-and-ci-baseline"
```

Expected:

- `openspec list --json` no longer lists `establish-repo-hygiene-and-ci-baseline`.
- `polish-rendered-preview-workflow` may remain active and parked.

- [ ] **Step 5: Commit archived OpenSpec change**

Run:

```bash
openspec validate --specs --strict
git diff --check
git add openspec/specs/dev-workflow-baseline/spec.md openspec/specs/documentation-surface-baseline/spec.md openspec/changes/archive/*-establish-repo-hygiene-and-ci-baseline
git commit -m "Archive repo hygiene CI baseline"
```

Expected:

- Archived change and synced specs are committed.

---

### Task 8: Final Verification

**Files:**
- No new source files unless final checks reveal a specific hygiene miss.

- [ ] **Step 1: Run canonical host check**

Run:

```bash
./scripts/check.sh
```

Expected:

- Host hygiene, OpenSpec validation, Python tests, fixture builds, docs build, and artifact inspections pass.

- [ ] **Step 2: Run Docker check**

Run:

```bash
./scripts/check-docker.sh
```

Expected:

- Python/Raya verification passes inside Docker Compose.

- [ ] **Step 3: Run external-course smoke test**

Run:

```bash
./scripts/smoke-test.sh
```

Expected:

- Temporary external courses validate, build, and inspect locally and through Docker.

- [ ] **Step 4: Confirm final OpenSpec and Git state**

Run:

```bash
openspec list --json
openspec validate --specs --strict
git diff --check
git status --short
```

Expected:

- `openspec list --json` shows only deliberately parked active changes, currently `polish-rendered-preview-workflow`.
- `openspec validate --specs --strict` passes.
- `git diff --check` passes.
- `git status --short` shows no generated/cache/session files.

- [ ] **Step 5: Commit any final cleanup**

If final checks required small cleanup, inspect the exact file list before staging:

```bash
git status --short
```

Stage only current source, docs, scripts, tests, specs, or workflow files shown by `git status --short`; do not stage generated outputs. Then run:

```bash
git commit -m "Tighten repo hygiene checks"
```

Expected:

- No generated outputs are staged.
- The commit contains only current source, docs, scripts, tests, specs, or workflow files.

---

## Self-Review Checklist

- The plan creates an OpenSpec change before implementation.
- The parked preview proposal is preserved and kept out of scope.
- Scripts have clear ownership and do not duplicate CI logic.
- Docker verification avoids host-only OpenSpec assumptions.
- Current docs are cleaned instead of archived changes.
- Deferred work is documented without becoming current behavior.
- Tests cover script behavior before relying on scripts as gates.
- Final verification includes host, Docker, smoke, OpenSpec, and Git cleanliness.
