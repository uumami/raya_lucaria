from __future__ import annotations

import json
from pathlib import Path

import pytest

from raya_cli.render_debug_report import copy_static_site, inspect_render_debug


def test_inspection_ignores_blocked_renderer_terms_in_prose_and_code(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        """
        <!doctype html>
        <html>
          <body>
            <main>
              <p>This page documents cdn.jsdelivr.net and tex-chtml as examples.</p>
              <code>mathjax.js</code>
              <!-- startup.js appears in a comment, not a resource URL. -->
            </main>
          </body>
        </html>
        """,
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    assert report["ok"] is True, report["diagnostics"]
    assert report["diagnostics"] == []


def test_copy_static_site_rejects_destination_under_source(tmp_path: Path) -> None:
    source = tmp_path / "site"
    source.mkdir()
    (source / "index.html").write_text("<html></html>", encoding="utf-8")

    with pytest.raises(ValueError, match="destination must not be inside source"):
        copy_static_site(source, source / "copied")


def test_inspection_fails_on_copied_site_raw_visible_tex(tmp_path: Path) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        """
        <!doctype html>
        <html>
          <body>
            <main><p>Clean generated page.</p></main>
          </body>
        </html>
        """,
    )
    copied_site = tmp_path / "copied-site"
    copied_site.mkdir()
    (copied_site / "index.html").write_text(
        """
        <!doctype html>
        <html>
          <body>
            <main>
              <p>Visible math leaked as $x^2$ in body text.</p>
              <code>$y^2$ is only a code sample.</code>
            </main>
          </body>
        </html>
        """,
        encoding="utf-8",
    )

    report = inspect_render_debug(
        site_dir=site_dir,
        debug_dir=debug_dir,
        copied_site_dir=copied_site,
    )

    raw_tex_diagnostics = [
        diagnostic
        for diagnostic in report["diagnostics"]
        if "raw visible TeX" in diagnostic["message"]
    ]
    assert report["ok"] is False
    assert raw_tex_diagnostics
    assert all(str(copied_site) in diagnostic["path"] for diagnostic in raw_tex_diagnostics)
    assert any("$x^2$" in diagnostic["message"] for diagnostic in raw_tex_diagnostics)
    assert all("$y^2$" not in diagnostic["message"] for diagnostic in raw_tex_diagnostics)


def test_inspection_fails_on_real_blocked_renderer_resource(tmp_path: Path) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        """
        <!doctype html>
        <html>
          <head>
            <script src="https://cdn.jsdelivr.net/npm/mathjax/tex-chtml.js"></script>
          </head>
          <body><main><p>Renderer dependency fixture.</p></main></body>
        </html>
        """,
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    assert report["ok"] is False
    assert any(
        "browser-side or external renderer dependency" in diagnostic["message"]
        for diagnostic in report["diagnostics"]
    )


def test_copy_static_site_rejects_destination_containing_source(tmp_path: Path) -> None:
    work = tmp_path / "work"
    source = work / "site"
    source.mkdir(parents=True)
    sentinel = work / "sentinel.txt"
    (source / "index.html").write_text("<html></html>", encoding="utf-8")
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError, match="destination must not contain source"):
        copy_static_site(source, work)

    assert source.is_dir()
    assert (source / "index.html").is_file()
    assert sentinel.read_text(encoding="utf-8") == "keep"


def _write_debug_fixture(
    tmp_path: Path,
    index_html: str,
) -> tuple[Path, Path]:
    site_dir = tmp_path / "site"
    debug_dir = tmp_path / "debug"
    site_dir.mkdir()
    debug_dir.mkdir()
    (site_dir / "index.html").write_text(index_html, encoding="utf-8")

    captures = []
    for viewport, screenshot in (
        ("desktop", "desktop-index.png"),
        ("mobile", "mobile-index.png"),
    ):
        screenshot_path = debug_dir / screenshot
        screenshot_path.write_bytes(b"png")
        captures.append(
            {
                "page": "index",
                "url": "http://127.0.0.1/index.html",
                "viewport": {
                    "name": viewport,
                    "width": 1280 if viewport == "desktop" else 390,
                    "height": 900 if viewport == "desktop" else 844,
                },
                "screenshot": str(screenshot_path),
                "mathjax_container_count": 0,
                "raw_tex_visible": False,
                "raw_tex_markers": [],
                "external_requests": [],
                "horizontal_overflow": 0,
            }
        )
    (debug_dir / "summary.json").write_text(
        json.dumps({"captures": captures}),
        encoding="utf-8",
    )
    return site_dir, debug_dir
