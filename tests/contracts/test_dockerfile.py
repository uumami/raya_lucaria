from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_reference_dev_image_keeps_python_310_and_copies_node_22_from_node_image() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    normalized = " ".join(dockerfile.replace("\\\n", " ").split())

    assert "FROM node:22-slim AS node" in normalized
    assert "FROM python:3.10-slim" in normalized
    assert "COPY --from=node" in normalized
    assert "COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/" in normalized


def test_reference_dev_image_installs_hygiene_tools_minimally() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    normalized = " ".join(dockerfile.replace("\\\n", " ").split())

    install = re.search(
        r"apt-get install -y --no-install-recommends (?P<packages>.*?) &&",
        normalized,
    )

    assert "apt-get update" in normalized
    assert install is not None
    assert {"chromium", "git", "ripgrep"}.issubset(set(install.group("packages").split()))
    assert "nodejs" not in install.group("packages").split()
    assert "npm" not in install.group("packages").split()
    assert "rm -rf /var/lib/apt/lists/*" in normalized
