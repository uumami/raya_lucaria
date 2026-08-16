from __future__ import annotations

import contextlib
import os
import shutil
import struct
import threading
import zlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from raya_static import build_course

ROOT = Path(__file__).resolve().parents[2]
MINIMAL_FIXTURE = ROOT / "examples" / "courses" / "minimal"

# rendering.py scopes the diagram-native-width rule to
# `@media (max-width: 1469px)`. Below that boundary, shrink-to-fit alone
# does not keep the diagrams' dominant 11.5-12.5px labels at >=10px
# (measured with this same browser-geometry method, on rendered img width
# rather than the figure body's own padding-inclusive clientWidth, against
# the reference course -- see task-8b-report.md; the true crossover is
# ~1466px). Pick one viewport solidly on each side of the boundary rather
# than probing 1469/1470 themselves, so the test isn't pixel-fragile
# against unrelated rail-geometry changes.
BELOW_THRESHOLD_VIEWPORT = 1024
ABOVE_THRESHOLD_VIEWPORT = 1500


def _browser_executable() -> Path:
    # Local copy of tests/e2e/test_rail_collapse_contract._browser_executable:
    # a cross-module `tests.e2e....` import does not resolve under pytest's
    # rootdir-relative import mode here (no tests/__init__.py package), so we
    # duplicate the small helper rather than fight import mode configuration.
    configured = os.environ.get("RAYA_TEST_BROWSER")
    if configured:
        path = Path(configured)
        if path.exists():
            return path
        pytest.fail(f"RAYA_TEST_BROWSER does not exist: {configured}")

    for name in (
        "chromium",
        "chromium-browser",
        "google-chrome-stable",
        "google-chrome",
    ):
        resolved = shutil.which(name)
        if resolved is not None:
            return Path(resolved)
    pytest.fail("A Chromium-compatible browser is required for visual/layout e2e tests")


def _make_png(width: int, height: int, rgb: tuple[int, int, int] = (200, 60, 60)) -> bytes:
    """Build a tiny, valid, solid-color PNG without a Pillow dependency.

    Saved to disk with a `.jpg` extension on purpose: this test only needs
    the file's *src suffix* to be `.jpg`, to prove the CSS rule's
    `img[src$=".svg"]` half does not also match illustrations. Chromium
    content-sniffs the real image bytes when decoding an `<img>`, so this
    renders with a correct `naturalWidth` despite the extension (and the
    `Content-Type: image/jpeg` the static server derives from it) not
    matching the actual PNG encoding.
    """

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    row = bytes([0]) + bytes(rgb) * width
    idat = zlib.compress(row * height, 9)
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


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


def _figure_course(tmp_path: Path) -> Path:
    course = tmp_path / "figure-scroll-course"
    shutil.copytree(MINIMAL_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        + '::: figure {#diagram-figure title="Diagram"}\n'
        + "![Diagram asset](_assets/diagram.svg)\n"
        + ":::\n\n"
        + '::: figure {#photo-figure title="Photo"}\n'
        + "![Photo asset](_assets/photo.jpg)\n"
        + ":::\n",
        encoding="utf-8",
    )
    assets = course / "course" / "_assets"
    assets.mkdir(exist_ok=True)
    # width="880" mirrors the reference course's real diagrams.
    (assets / "diagram.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="880" height="200">'
        '<text x="10" y="20" font-size="12.5">diagram label</text></svg>\n',
        encoding="utf-8",
    )
    # Natural width picked well above any figure-body width this test
    # exercises, so the illustration is always still shrinking on both
    # sides of the threshold -- proving the .jpg half of the selector
    # never engages, not just that it happens to fit once.
    (assets / "photo.jpg").write_bytes(_make_png(2400, 400))
    return course


def _image_geometry(page) -> dict[str, dict]:
    rows = page.eval_on_selector_all(
        'img[src$=".svg"], img[src$=".jpg"]',
        """els => els.map(el => {
            const rect = el.getBoundingClientRect();
            return {
                src: el.getAttribute('src'),
                renderedWidth: rect.width,
                naturalWidth: el.naturalWidth,
            };
        })""",
    )
    return {row["src"].rsplit("/", 1)[-1]: row for row in rows}


def test_figure_svg_renders_native_below_threshold_and_shrinks_above(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright

    course = _figure_course(tmp_path)
    report = build_course(course)
    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    site = course / "artifact" / "site"

    with _serve(site) as base_url:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(
                    viewport={"width": BELOW_THRESHOLD_VIEWPORT, "height": 900}
                )
                page.goto(f"{base_url}/index.html", wait_until="networkidle")
                below = _image_geometry(page)

                page.set_viewport_size(
                    {"width": ABOVE_THRESHOLD_VIEWPORT, "height": 900}
                )
                page.wait_for_timeout(50)
                above = _image_geometry(page)
                page.close()
            finally:
                browser.close()

    svg_below, svg_above = below["diagram.svg"], above["diagram.svg"]
    jpg_below, jpg_above = below["photo.jpg"], above["photo.jpg"]

    assert svg_below["naturalWidth"] == 880
    # Below the threshold: the diagram renders at native size (max-width:
    # none wins) even though the figure body is much narrower -- that gap
    # is exactly what makes .raya-numbered-object-body's overflow-x: auto
    # scroll instead of shrinking the text away.
    assert svg_below["renderedWidth"] == pytest.approx(880, abs=1), svg_below

    # Above the threshold: the override no longer applies, so the diagram
    # is back under the global img { max-width: 100% } rule and shrinks
    # with the figure body, same as it did before this fix existed.
    assert svg_above["renderedWidth"] < svg_above["naturalWidth"] - 1, svg_above

    # The illustration (.jpg) must keep shrinking to fit on BOTH sides of
    # the threshold -- the rule's other half never reaches it.
    assert jpg_below["renderedWidth"] < jpg_below["naturalWidth"] - 1, jpg_below
    assert jpg_above["renderedWidth"] < jpg_above["naturalWidth"] - 1, jpg_above
