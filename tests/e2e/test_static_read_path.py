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
MINIMAL_FIXTURE = ROOT / "examples" / "courses" / "minimal"
RENDER_FIXTURE = ROOT / "examples" / "courses" / "render-fixture"
REFERENCE_FIXTURE = ROOT / "examples" / "courses" / "reference-fixture"
RUNTIME_FIXTURE = ROOT / "examples" / "courses" / "runtime-fixture"
EXECUTION_FIXTURE = ROOT / "examples" / "courses" / "execution-fixture"
DOCS_FIXTURE = ROOT / "examples" / "docs" / "documentation-fixture"
ORDERED_FIXTURE = ROOT / "examples" / "courses" / "ordered-fixture"
EXAMPLES_GALLERY = ROOT / "examples" / "gallery"


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
        render_css = _fetch_text(f"{base_url}/_raya/render/rich.css")
        math_css = _fetch_text(f"{base_url}/_raya/render/math/mathjax.css")
        math_font = _fetch_bytes(
            f"{base_url}/_raya/render/math/fonts/mjx-ncm-n.woff2"
        )

    assert "Raya Lucaria Render Fixture" in root_html
    assert '<nav class="raya-page-toc" aria-label="Page contents">' in root_html
    assert '<aside class="raya-callout raya-callout-note"' in root_html
    assert '<section class="footnotes">' in root_html
    assert 'href="_raya/assets/_source/_local/diagrams/static-path.txt"' in root_html
    assert 'src="_raya/assets/_source/_local/diagrams/static-path.txt"' in root_html
    assert '<link rel="stylesheet" href="_raya/render/rich.css">' in root_html
    assert '<link rel="stylesheet" href="_raya/render/math/mathjax.css">' in root_html
    assert 'href="../_raya/assets/_source/_local/diagrams/static-path.txt"' in nested_html
    assert '<link rel="stylesheet" href="../_raya/render/rich.css">' in nested_html
    assert (
        '<link rel="stylesheet" href="../_raya/render/math/mathjax.css">'
        in nested_html
    )
    assert '<aside class="raya-callout raya-callout-tip"' in nested_html
    assert (
        'href="../_raya/assets/_source/1_static_path/_local/local-static-path.txt"'
        in nested_html
    )
    assert "Raya Lucaria render fixture asset" in asset_text
    assert "Raya Lucaria render fixture colocated asset" in local_asset_text
    assert ".raya-code-block" in render_css
    assert ".math.block" in render_css
    assert "mjx-container" in math_css
    assert len(math_font) > 0


def test_reference_fixture_static_read_path_serves_referenced_files(
    tmp_path: Path,
) -> None:
    course = tmp_path / "reference-fixture"
    shutil.copytree(REFERENCE_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    site = course / "artifact" / "site"

    with _serve(site) as base_url:
        root_html = _fetch_text(f"{base_url}/index.html")
        nested_html = _fetch_text(f"{base_url}/analysis/index.html")
        inspection_html = _fetch_text(f"{base_url}/_raya/inspect/index.html")
        shared_helper = _fetch_text(f"{base_url}/_raya/files/_source/code/shared_helper.py")
        cleaning_script = _fetch_text(
            f"{base_url}/_raya/files/_source/1_analysis/scripts/clean_data.py"
        )
        overview_notebook = _fetch_text(
            f"{base_url}/_raya/files/_source/notebooks/overview.ipynb"
        )
        exploration_notebook = _fetch_text(
            f"{base_url}/_raya/files/_source/1_analysis/labs/exploration.ipynb"
        )

    assert "Referenced Work" in root_html
    assert 'data-raya-surface="student-default"' in root_html
    assert 'data-raya-surface="inspection"' in inspection_html
    assert "Surface tier: inspection" in inspection_html
    assert 'href="../files/_source/code/shared_helper.py"' in inspection_html
    assert 'href="_raya/files/_source/code/shared_helper.py"' in root_html
    assert 'href="_raya/files/_source/notebooks/overview.ipynb"' in root_html
    assert 'href="../_raya/files/_source/1_analysis/scripts/clean_data.py"' in nested_html
    assert (
        'href="../_raya/files/_source/1_analysis/labs/exploration.ipynb"'
        in nested_html
    )
    assert "not executed during build" in root_html
    assert "def shared_value" in shared_helper
    assert "def clean_rows" in cleaning_script
    assert "Overview notebook" in overview_notebook
    assert "Exploration" in exploration_notebook


def test_runtime_fixture_static_read_path_remains_static(tmp_path: Path) -> None:
    course = tmp_path / "runtime-fixture"
    shutil.copytree(RUNTIME_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    site = course / "artifact" / "site"

    with _serve(site) as base_url:
        root_html = _fetch_text(f"{base_url}/index.html")
        runtime_task = _fetch_text(
            f"{base_url}/_raya/files/_source/code/runtime_task.py"
        )

    assert "Runtime Metadata Fixture" in root_html
    assert 'href="_raya/files/_source/code/runtime_task.py"' in root_html
    assert "not executed during build" in root_html
    assert "SHOULD_NOT_EXIST_RUNTIME_SENTINEL" in runtime_task
    assert not (course / "SHOULD_NOT_EXIST_RUNTIME_SENTINEL").exists()
    assert not (course / "artifact" / "SHOULD_NOT_EXIST_RUNTIME_SENTINEL").exists()


def test_execution_fixture_static_read_path_remains_static(tmp_path: Path) -> None:
    course = tmp_path / "execution-fixture"
    shutil.copytree(EXECUTION_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    site = course / "artifact" / "site"

    with _serve(site) as base_url:
        root_html = _fetch_text(f"{base_url}/index.html")
        inspection_html = _fetch_text(f"{base_url}/_raya/inspect/index.html")
        manual_script = _fetch_text(
            f"{base_url}/_raya/files/_source/code/manual_task.py"
        )
        reviewed_stdout = _fetch_text(
            f"{base_url}/_raya/reviewed/frozen-script/stdout.txt"
        )

    assert "Local Execution Fixture" in root_html
    assert 'href="_raya/files/_source/code/manual_task.py"' in root_html
    assert "Reviewed Output" in root_html
    assert 'href="_raya/reviewed/frozen-script/stdout.txt"' in root_html
    assert 'href="../reviewed/frozen-script/stdout.txt"' in inspection_html
    assert "Review key" in inspection_html
    assert "reviewed output current" in root_html
    assert reviewed_stdout == "frozen reviewed output fixture\n"
    assert "not executed during build" in root_html
    assert "manual execution sentinel" in manual_script
    assert not (course / "execution-side-effect.txt").exists()
    assert not (course / "SHOULD_NOT_EXIST_NEVER_SENTINEL").exists()
    assert not (course / "artifact" / "data" / "execution-results.json").exists()


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


def test_examples_gallery_static_read_path_links_built_fixtures(
    tmp_path: Path,
) -> None:
    examples_root = tmp_path / "examples"
    courses_root = examples_root / "courses"
    shutil.copytree(EXAMPLES_GALLERY, examples_root / "gallery")
    courses_root.mkdir(parents=True)

    fixtures = [
        (MINIMAL_FIXTURE, "minimal"),
        (ORDERED_FIXTURE, "ordered-fixture"),
        (RENDER_FIXTURE, "render-fixture"),
        (REFERENCE_FIXTURE, "reference-fixture"),
        (RUNTIME_FIXTURE, "runtime-fixture"),
        (EXECUTION_FIXTURE, "execution-fixture"),
    ]
    for source, name in fixtures:
        course = courses_root / name
        shutil.copytree(source, course, ignore=shutil.ignore_patterns("artifact"))
        report = build_course(course)
        assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]

    with _serve(examples_root) as base_url:
        gallery_html = _fetch_text(f"{base_url}/gallery/index.html")
        minimal_html = _fetch_text(f"{base_url}/courses/minimal/artifact/site/index.html")
        reference_inspection_html = _fetch_text(
            f"{base_url}/courses/reference-fixture/artifact/site/_raya/inspect/index.html"
        )
        reviewed_file = _fetch_text(
            f"{base_url}/courses/execution-fixture/artifact/site/_raya/reviewed/frozen-script/stdout.txt"
        )

    assert "fixture material" in gallery_html
    assert "../courses/minimal/artifact/site/index.html" in gallery_html
    assert "../courses/execution-fixture/artifact/site/index.html" in gallery_html
    assert "Foundation docs and accepted OpenSpec specs remain the authority" in gallery_html
    assert "Minimal Course Fixture" in minimal_html
    assert "Artifact Inspection" in reference_inspection_html
    assert reviewed_file == "frozen reviewed output fixture\n"


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
        rendering_plan_html = _fetch_text(
            f"{base_url}/foundation/rendering-execution-plan/index.html"
        )
        english_html = _fetch_text(f"{base_url}/guides/en/contributors/index.html")
        spanish_html = _fetch_text(f"{base_url}/guides/es/colaboradores/index.html")
        render_css = _fetch_text(f"{base_url}/_raya/render/rich.css")

    assert "Raya Lucaria Documentation" in root_html
    assert 'href="foundation/index.html"' in root_html
    assert 'href="guides/index.html"' in root_html
    assert "Raya Lucaria Foundation" in foundation_html
    assert "System Overview" in overview_html
    assert "Rendering And Execution Plan" in rendering_plan_html
    assert "Contributors And Collaborators" in english_html
    assert "Colaboradores" in spanish_html
    assert "Course Index" in root_html
    assert ".raya-page-toc" in render_css


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


def _fetch_bytes(url: str) -> bytes:
    with urlopen(url, timeout=10) as response:
        return response.read()
