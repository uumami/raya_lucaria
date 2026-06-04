from __future__ import annotations

import contextlib
import shutil
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

from raya_static import build_course


ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = ROOT / "docs"
RENDER_FIXTURE = ROOT / "examples" / "courses" / "render-fixture"
DOCS_FIXTURE = ROOT / "examples" / "docs" / "documentation-fixture"
ORDERED_FIXTURE = ROOT / "examples" / "courses" / "ordered-fixture"


def test_render_fixture_static_read_path_serves_pages_and_assets(tmp_path: Path) -> None:
    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    site = course / "artifact" / "site"

    with _serve(site) as base_url:
        root_html = _fetch_text(f"{base_url}/index.html")
        nested_html = _fetch_text(f"{base_url}/static-path/index.html")
        asset_text = _fetch_text(
            f"{base_url}/_raya/assets/_source/_local/diagrams/static-path.txt"
        )
        local_asset_text = _fetch_text(
            f"{base_url}/_raya/assets/_source/1_static_path/_local/local-static-path.txt"
        )

    assert "Raya Lucaria Render Fixture" in root_html
    assert 'href="_raya/assets/_source/_local/diagrams/static-path.txt"' in root_html
    assert 'href="../_raya/assets/_source/_local/diagrams/static-path.txt"' in nested_html
    assert (
        'href="../_raya/assets/_source/1_static_path/_local/local-static-path.txt"'
        in nested_html
    )
    assert "Raya Lucaria render fixture asset" in asset_text
    assert "Raya Lucaria render fixture colocated asset" in local_asset_text


def test_documentation_fixture_static_read_path_serves_pages_and_assets(
    tmp_path: Path,
) -> None:
    source = tmp_path / "documentation-fixture"
    shutil.copytree(DOCS_FIXTURE, source, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(source)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    site = source / "artifact" / "site"

    with _serve(site) as base_url:
        root_html = _fetch_text(f"{base_url}/index.html")
        english_html = _fetch_text(f"{base_url}/en/contributors/index.html")
        spanish_html = _fetch_text(f"{base_url}/es/colaboradores/index.html")
        asset_text = _fetch_text(
            f"{base_url}/_raya/assets/_source/_local/reference/documentation-surface.txt"
        )

    assert "Raya Lucaria Documentation Fixture" in root_html
    assert 'href="en/contributors/index.html"' in root_html
    assert 'href="es/colaboradores/index.html"' in root_html
    assert 'href="_raya/assets/_source/_local/reference/documentation-surface.txt"' in root_html
    assert "Contributors" in english_html
    assert "Colaboradores" in spanish_html
    assert "Esta pagina es material" not in english_html
    assert "This page is documentation fixture material" not in spanish_html
    assert "Raya Lucaria documentation fixture asset" in asset_text


def test_ordered_fixture_static_read_path_serves_generated_indexes_and_links(
    tmp_path: Path,
) -> None:
    course = tmp_path / "ordered-fixture"
    shutil.copytree(ORDERED_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    site = course / "artifact" / "site"

    with _serve(site) as base_url:
        root_html = _fetch_text(f"{base_url}/index.html")
        foundations_html = _fetch_text(f"{base_url}/foundations/index.html")
        derivatives_html = _fetch_text(f"{base_url}/foundations/derivatives/index.html")
        practice_html = _fetch_text(f"{base_url}/practice/index.html")
        reference_html = _fetch_text(f"{base_url}/reference/index.html")

    assert "Course Index" in root_html
    assert 'href="foundations/index.html"' in root_html
    assert "Foundations" in root_html
    assert "Practice" in root_html
    assert "Reference" in root_html
    assert "Topics" in foundations_html
    assert "1.1 Limits" in foundations_html
    assert "1.2 Derivatives" in foundations_html
    assert "Card: 1" in foundations_html
    assert "Previous: Limits" in derivatives_html
    assert "Next: Practice" in derivatives_html
    assert 'href="../../index.html"' in derivatives_html
    assert 'href="../foundations/derivatives/index.html"' in practice_html
    assert "Anexo" in reference_html


def test_current_documentation_static_read_path_serves_live_docs(
    tmp_path: Path,
) -> None:
    source = tmp_path / "docs"
    shutil.copytree(DOCS_ROOT, source, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(source)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    site = source / "artifact" / "site"

    with _serve(site) as base_url:
        root_html = _fetch_text(f"{base_url}/index.html")
        foundation_html = _fetch_text(f"{base_url}/foundation/index.html")
        overview_html = _fetch_text(f"{base_url}/foundation/system-overview/index.html")
        english_html = _fetch_text(f"{base_url}/guides/en/contributors/index.html")
        spanish_html = _fetch_text(f"{base_url}/guides/es/colaboradores/index.html")

    assert "Raya Lucaria Documentation" in root_html
    assert 'href="foundation/index.html"' in root_html
    assert 'href="guides/index.html"' in root_html
    assert "Raya Lucaria Foundation" in foundation_html
    assert "System Overview" in overview_html
    assert "Contributors And Collaborators" in english_html
    assert "Colaboradores" in spanish_html
    assert "Course Index" in root_html


@contextlib.contextmanager
def _serve(directory: Path):
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(  # noqa: E731
        *args,
        directory=str(directory),
        **kwargs,
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _fetch_text(url: str) -> str:
    with urlopen(url, timeout=10) as response:
        return response.read().decode("utf-8")
