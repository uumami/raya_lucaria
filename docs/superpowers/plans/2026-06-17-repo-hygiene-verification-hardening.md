# Repo Hygiene Verification Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep generated/dependency files out of GitHub and prevent host/Docker verification from racing over shared dependency preparation.

**Architecture:** Strengthen the existing shell-script verification path instead of adding a new tool. `scripts/check-python.sh` owns the shared dependency preparation lock because both host and Docker gates call it; `scripts/check-hygiene.sh` owns source-pollution detection; docs explain the safe sequence and lock recovery.

**Tech Stack:** Bash, Git, `rg`, npm, uv, Docker Compose, pytest.

---

## File Structure

- Modify `scripts/check-python.sh`: add a fail-fast repository-local verification lock around dependency-mutating setup.
- Modify `scripts/check-hygiene.sh`: expand generated/debug pollution patterns and add a dedicated render-debug output check.
- Modify `.gitignore`: add explicit render-debug/report screenshot patterns while preserving authored source assets.
- Modify `README.md`, `AGENTS.md`, `docs/guides/en/contributors/index.md`, `docs/guides/en/agents/index.md`, `docs/guides/es/colaboradores/index.md`, and `docs/guides/es/agentes/index.md`: document sequential verification and lock behavior.
- Create `tests/scripts/test_check_python_lock.py`: test lock behavior through a small temporary shell harness that exercises the same lock protocol.

## Task 1: Verification Lock In `check-python`

**Files:**
- Modify: `scripts/check-python.sh`
- Create: `tests/scripts/test_check_python_lock.py`

- [ ] **Step 1: Write the failing lock test**

Create `tests/scripts/test_check_python_lock.py` with this content:

```python
from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _write_harness(tmp_path: Path) -> Path:
    harness = tmp_path / "lock-harness.sh"
    harness.write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -euo pipefail

            ROOT="{ROOT}"
            source "$ROOT/scripts/check-python.sh" --source-lock-functions
            acquire_dependency_lock
            echo acquired
            sleep "${{1:-0}}"
            """
        ),
        encoding="utf-8",
    )
    harness.chmod(0o755)
    return harness


def test_check_python_dependency_lock_fails_fast_when_already_held(
    tmp_path: Path,
) -> None:
    harness = _write_harness(tmp_path)
    env = os.environ.copy()
    env["RAYA_CHECK_LOCK_DIR"] = str(tmp_path / "lock")

    first = subprocess.Popen(
        [str(harness), "5"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert first.stdout is not None
        assert first.stdout.readline().strip() == "acquired"

        second = subprocess.run(
            [str(harness), "0"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        assert second.returncode == 75
        assert "Another Raya verification is preparing dependencies" in second.stderr
        assert "Wait for it to finish, then rerun this command." in second.stderr
    finally:
        first.terminate()
        first.wait(timeout=10)


def test_check_python_dependency_lock_releases_on_exit(tmp_path: Path) -> None:
    harness = _write_harness(tmp_path)
    env = os.environ.copy()
    env["RAYA_CHECK_LOCK_DIR"] = str(tmp_path / "lock")

    first = subprocess.run(
        [str(harness), "0"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    second = subprocess.run(
        [str(harness), "0"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert first.stdout.strip() == "acquired"
    assert second.stdout.strip() == "acquired"
```

- [ ] **Step 2: Run the failing lock test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/scripts/test_check_python_lock.py -q
```

Expected: FAIL because `scripts/check-python.sh` does not yet support `--source-lock-functions` and does not expose `acquire_dependency_lock`.

- [ ] **Step 3: Add sourceable lock functions**

Modify the top of `scripts/check-python.sh` so it can expose lock helpers without running the full check:

```bash
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
  fi
}

acquire_dependency_lock() {
  RAYA_CHECK_LOCK_DIR="${RAYA_CHECK_LOCK_DIR:-$ROOT/.raya-check.lock}"
  if ! mkdir "$RAYA_CHECK_LOCK_DIR" 2>/dev/null; then
    lock_message
    return 75
  fi
  RAYA_CHECK_LOCK_HELD=1
  trap release_dependency_lock EXIT INT TERM
}

if [[ "${1:-}" == "--source-lock-functions" ]]; then
  return 0 2>/dev/null || exit 0
fi
```

Keep the existing usage and argument parsing below this block, but remove the later duplicate `ROOT=...` assignment so `ROOT` is defined once.

- [ ] **Step 4: Wrap dependency preparation with the lock**

In `scripts/check-python.sh`, call the lock before dependency-mutating setup and release it after `uv sync`:

```bash
acquire_dependency_lock
run npm ci --ignore-scripts --no-audit --no-fund
run npm run raya-render-math -- --self-test
run uv sync --python 3.10 --all-packages --dev
release_dependency_lock
trap - EXIT INT TERM
```

Leave `uv run pytest -q`, fixture builds, render-debug, and docs builds outside the lock.

- [ ] **Step 5: Run the lock tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/scripts/test_check_python_lock.py -q
```

Expected: `2 passed`.

- [ ] **Step 6: Commit the lock change**

Run:

```bash
git add scripts/check-python.sh tests/scripts/test_check_python_lock.py
git commit -m "Guard verification dependency setup"
```

## Task 2: Hygiene Rules For Render-Debug And Generated Pollution

**Files:**
- Modify: `.gitignore`
- Modify: `scripts/check-hygiene.sh`
- Test: `tests/scripts/test_check_hygiene.py`

- [ ] **Step 1: Check for an existing script-test pattern**

Run:

```bash
find tests -maxdepth 3 -type f | sort | rg 'scripts|hygiene|check'
```

Expected: either an existing script test file to extend or no output. If no output, create `tests/scripts/test_check_hygiene.py` in the next step.

- [ ] **Step 2: Write failing hygiene tests**

Create or extend `tests/scripts/test_check_hygiene.py` with this content:

```python
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _minimal_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (repo / "README.md").write_text("# Test\n", encoding="utf-8")
    (repo / "AGENTS.md").write_text("# Test\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "foundation").mkdir(parents=True)
    (repo / "docs" / "guides").mkdir(parents=True)
    (repo / "openspec").mkdir()
    (repo / "openspec" / "config.yaml").write_text("{}\n", encoding="utf-8")
    (repo / "openspec" / "specs").mkdir()
    (repo / "packages").mkdir()
    (repo / "examples").mkdir()
    (repo / "examples" / "gallery").mkdir()
    (repo / "examples" / "gallery" / "index.html").write_text(
        "fixture material\n",
        encoding="utf-8",
    )
    return repo


def test_hygiene_rejects_untracked_render_debug_output(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    debug_dir = repo / "tmp" / "raya-render-debug.sample"
    debug_dir.mkdir(parents=True)
    (debug_dir / "report.json").write_text("{}\n", encoding="utf-8")
    (debug_dir / "desktop-index.png").write_bytes(b"png")

    result = subprocess.run(
        [str(ROOT / "scripts" / "check-hygiene.sh"), "--root", str(repo)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "generated output appears as untracked source" in result.stdout
    assert "raya-render-debug.sample/report.json" in result.stdout


def test_hygiene_allows_authored_png_assets(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    asset = repo / "examples" / "courses" / "demo" / "course" / "_assets" / "diagram.png"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"png")

    result = subprocess.run(
        [str(ROOT / "scripts" / "check-hygiene.sh"), "--root", str(repo)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
```

- [ ] **Step 3: Run the failing hygiene tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/scripts/test_check_hygiene.py -q
```

Expected: the render-debug test fails because the current generated path pattern does not catch `raya-render-debug.*` directories.

- [ ] **Step 4: Update `.gitignore`**

Add this block under the generated course/site artifacts section:

```gitignore
# Local render-debug evidence
raya-render-debug*/
**/raya-render-debug*/
render-debug/
**/render-debug/
```

Do not ignore all `*.png`, `report.json`, or `index.html` globally.

- [ ] **Step 5: Strengthen generated path pattern**

In `scripts/check-hygiene.sh`, update `generated_path_pattern()` to include render-debug directories:

```bash
generated_path_pattern() {
  printf '%s' '(^|/)(artifact|site|_site|dist|build|coverage|htmlcov|node_modules|__pycache__|\.pytest_cache|\.ruff_cache|\.mypy_cache|\.tox|\.nox|\.hypothesis|\.superpowers|\.uv-cache|\.cache|raya-render-debug[^/]*|render-debug)(/|$)'
}
```

- [ ] **Step 6: Run the hygiene tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/scripts/test_check_hygiene.py -q
```

Expected: `2 passed`.

- [ ] **Step 7: Confirm no unwanted tracked files exist**

Run:

```bash
git ls-files | rg '(^|/)(artifact|site|_site|dist|build|coverage|htmlcov|node_modules|__pycache__|\.pytest_cache|\.ruff_cache|\.mypy_cache|\.tox|\.nox|\.hypothesis|\.superpowers|\.uv-cache|\.cache|raya-render-debug[^/]*|render-debug)(/|$)'
```

Expected: no output and exit code 1. If output appears, inspect each path. For generated files, run `git rm --cached <path>` and leave local copies in place when possible.

- [ ] **Step 8: Commit hygiene changes**

Run:

```bash
git add .gitignore scripts/check-hygiene.sh tests/scripts/test_check_hygiene.py
git commit -m "Harden generated output hygiene"
```

## Task 3: Verification Workflow Documentation

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update README verification guidance**

In `README.md`, find the paragraph after the check command list that begins with `` `./scripts/check.sh` is the host archive gate.`` Replace it with:

```markdown
`./scripts/check.sh` is the host archive gate. `./scripts/check-docker.sh` runs the Python/Raya verification path inside the reference container. Run them sequentially, not at the same time: both prepare local Node/MathJax dependencies through `scripts/check-python.sh`, and that setup is protected by a fail-fast repository lock. If a check reports that another Raya verification is preparing dependencies, wait for the active check to finish and rerun the command. `./scripts/check-render-debug.sh` runs the focused render-fixture browser parity gate for screenshots, raw TeX, overflow, local MathJax resources, and external renderer requests. It writes `report.json` and `index.html` in the debug output directory and checks copied static-site parity. Treat render-debug files as local evidence only; do not commit them. `./scripts/smoke-test.sh` validates, builds, and inspects temporary external courses locally and through Docker.
```

- [ ] **Step 2: Update AGENTS command guidance**

In `AGENTS.md`, after the bullet for `./scripts/check-docker.sh`, add:

```markdown
- Run `./scripts/check.sh` and `./scripts/check-docker.sh` sequentially, not concurrently. Both paths prepare local Node/MathJax dependencies through `scripts/check-python.sh`; if the verification lock reports another Raya verification is preparing dependencies, wait for that process to finish and rerun the command.
```

- [ ] **Step 3: Update English contributor guide**

In `docs/guides/en/contributors/index.md`, update the first verification paragraph to include:

```markdown
Run `./scripts/check.sh` and `./scripts/check-docker.sh` sequentially. Both prepare local Node/MathJax dependencies through `scripts/check-python.sh`, so the scripts fail fast when another verification is already preparing dependencies. Wait for the active check to finish, then rerun the blocked command.
```

- [ ] **Step 4: Update English agent guide**

In `docs/guides/en/agents/index.md`, add a short verification paragraph near the existing preview/rendering guidance:

```markdown
For repository gates, run `./scripts/check.sh` and `./scripts/check-docker.sh` sequentially. Do not start them in parallel. If the dependency-preparation lock reports an active Raya verification, wait for the active process to finish and rerun the blocked command.
```

- [ ] **Step 5: Update Spanish collaborator guide**

In `docs/guides/es/colaboradores/index.md`, update the first verification paragraph to include:

```markdown
Ejecuta `./scripts/check.sh` y `./scripts/check-docker.sh` en secuencia, no en paralelo. Ambos preparan dependencias locales Node/MathJax mediante `scripts/check-python.sh`, por eso los scripts fallan de forma clara si otra verificacion ya esta preparando dependencias. Espera a que termine el proceso activo y vuelve a ejecutar el comando bloqueado.
```

- [ ] **Step 6: Update Spanish agent guide**

In `docs/guides/es/agentes/index.md`, add:

```markdown
Para compuertas de repositorio, ejecuta `./scripts/check.sh` y `./scripts/check-docker.sh` en secuencia. No los inicies en paralelo. Si el lock de preparacion de dependencias informa que hay otra verificacion Raya activa, espera a que termine y vuelve a ejecutar el comando bloqueado.
```

- [ ] **Step 7: Run documentation scans**

Run:

```bash
scripts/check-hygiene.sh
```

Expected: `hygiene: passed`.

- [ ] **Step 8: Commit docs**

Run:

```bash
git add README.md AGENTS.md docs/guides/en/contributors/index.md docs/guides/en/agents/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md
git commit -m "Document sequential verification gates"
```

## Task 4: Final Verification And Review

**Files:**
- No planned source edits.

- [ ] **Step 1: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/scripts/test_check_python_lock.py tests/scripts/test_check_hygiene.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run hygiene gate**

Run:

```bash
scripts/check-hygiene.sh
```

Expected: `hygiene: passed`.

- [ ] **Step 3: Run host gate**

Run:

```bash
./scripts/check.sh
```

Expected: `check: passed`.

- [ ] **Step 4: Run Docker gate after host gate exits**

Run:

```bash
./scripts/check-docker.sh
```

Expected: `check-docker: passed`.

- [ ] **Step 5: Request code review**

Use `superpowers:requesting-code-review`. Ask the reviewer to check:

- lock behavior is fail-fast and cleans up on exit;
- `check.sh` and `check-docker.sh` cannot corrupt shared dependency setup when run concurrently;
- hygiene changes do not reject legitimate authored course assets;
- docs accurately describe the workflow in English and Spanish;
- no generated/dependency files are tracked.

- [ ] **Step 6: Address review findings**

If the reviewer finds issues, use `superpowers:receiving-code-review`, fix them with focused tests, and commit each fix.

- [ ] **Step 7: Final clean status**

Run:

```bash
git status --short --branch
```

Expected: clean working tree on `new_rayalucaria`.
