from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


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
    assert "rm -rf /var/lib/apt/lists/*" in normalized
