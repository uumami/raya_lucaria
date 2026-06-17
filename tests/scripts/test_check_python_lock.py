from __future__ import annotations

import os
import signal
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
            if [[ "${{1:-0}}" == "--self-term" ]]; then
              kill -TERM "$$"
            fi
            sleep "${{1:-0}}"
            """
        ),
        encoding="utf-8",
    )
    harness.chmod(0o755)
    return harness


def _lock_env(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["RAYA_CHECK_LOCK_DIR"] = str(tmp_path / "lock")
    return env


def _terminate_lock_holder(process: subprocess.Popen[str]) -> None:
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)


def test_check_python_dependency_lock_fails_fast_when_already_held(
    tmp_path: Path,
) -> None:
    harness = _write_harness(tmp_path)
    env = _lock_env(tmp_path)

    first = subprocess.Popen(
        [str(harness), "30"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
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
        assert env["RAYA_CHECK_LOCK_DIR"] in second.stderr
        assert "If this lock is stale" in second.stderr
        assert "is still running before removing" in second.stderr
    finally:
        if first.poll() is None:
            _terminate_lock_holder(first)


def test_check_python_dependency_lock_releases_on_exit(tmp_path: Path) -> None:
    harness = _write_harness(tmp_path)
    env = _lock_env(tmp_path)

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


def test_check_python_dependency_lock_releases_on_term(tmp_path: Path) -> None:
    harness = _write_harness(tmp_path)
    env = _lock_env(tmp_path)

    first = subprocess.run(
        [str(harness), "--self-term"],
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

    assert first.returncode == 143, first.stderr
    assert first.stdout.strip() == "acquired"
    assert second.returncode == 0, second.stderr
    assert second.stdout.strip() == "acquired"


def test_check_python_holds_dependency_lock_through_pytest(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    marker = tmp_path / "pytest-saw-lock"
    lock_dir = tmp_path / "lock"

    npm = bin_dir / "npm"
    npm.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "exit 0\n",
        encoding="utf-8",
    )
    npm.chmod(0o755)

    uv = bin_dir / "uv"
    uv.write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -euo pipefail

            if [[ "$*" == "sync --python 3.10 --all-packages --dev" ]]; then
              exit 0
            fi

            if [[ "$*" == "run pytest -q" ]]; then
              if [[ -d "{lock_dir}" ]]; then
                touch "{marker}"
                exit 42
              fi
              exit 43
            fi

            exit 99
            """
        ),
        encoding="utf-8",
    )
    uv.chmod(0o755)

    env = _lock_env(tmp_path)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"

    result = subprocess.run(
        ["scripts/check-python.sh"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 42, result.stderr
    assert marker.exists()
    assert not lock_dir.exists()
