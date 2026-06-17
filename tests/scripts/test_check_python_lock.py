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
