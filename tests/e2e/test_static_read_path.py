from __future__ import annotations

import contextlib
import shutil
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

from raya_static import build_course


ROOT = Path(__file__).resolve().parents[2]
RENDER_FIXTURE = ROOT / "examples" / "courses" / "render-fixture"


def test_render_fixture_static_read_path_serves_pages_and_assets(tmp_path: Path) -> None:
    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    site = course / "artifact" / "site"

    with _serve(site) as base_url:
        root_html = _fetch_text(f"{base_url}/index.html")
        nested_html = _fetch_text(f"{base_url}/01_static_path/index.html")
        asset_text = _fetch_text(f"{base_url}/_raya/assets/diagrams/static-path.txt")

    assert "Raya Lucaria Render Fixture" in root_html
    assert 'href="_raya/assets/diagrams/static-path.txt"' in root_html
    assert 'href="../_raya/assets/diagrams/static-path.txt"' in nested_html
    assert "Raya Lucaria render fixture asset" in asset_text


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
