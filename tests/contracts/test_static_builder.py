from __future__ import annotations

import json
import shutil
from pathlib import Path

from raya_schema import (
    inspect_artifact,
    validate_artifact_manifest,
    validate_indices_index,
    validate_links_index,
    validate_navigation_index,
    validate_official_index,
    validate_pages_index,
    validate_quanta_index,
)
from raya_static import build_course


ROOT = Path(__file__).resolve().parents[2]
MINIMAL = ROOT / "examples" / "courses" / "minimal"
RENDER_FIXTURE = ROOT / "examples" / "courses" / "render-fixture"


def test_build_minimal_fixture_into_temporary_course(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    artifact = course / "artifact"
    assert (artifact / "site" / "index.html").exists()
    assert (artifact / "site" / "unit" / "index.html").exists()
    assert (artifact / "site" / "unit" / "topic" / "index.html").exists()
    assert (artifact / "manifest.json").exists()
    assert (artifact / "data" / "pages.json").exists()
    assert (artifact / "data" / "quanta.json").exists()
    assert (artifact / "data" / "links.json").exists()
    assert (artifact / "data" / "navigation.json").exists()
    assert (artifact / "data" / "indices.json").exists()
    assert (artifact / "data" / "official.json").exists()
    assert (artifact / "assets").is_dir()
    assert artifact / "manifest.json" in report.outputs_written


def test_generated_artifact_contract_validates(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    artifact = course / "artifact"

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    for validation_report in (
        validate_artifact_manifest(artifact / "manifest.json"),
        validate_pages_index(artifact / "data" / "pages.json"),
        validate_quanta_index(artifact / "data" / "quanta.json"),
        validate_links_index(artifact / "data" / "links.json"),
        validate_navigation_index(artifact / "data" / "navigation.json"),
        validate_indices_index(artifact / "data" / "indices.json"),
        validate_official_index(artifact / "data" / "official.json"),
    ):
        assert validation_report.ok, [
            diagnostic.format() for diagnostic in validation_report.diagnostics
        ]


def test_generated_html_is_escaped_and_static_linked(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    extra = course / "course" / "2_escape.md"
    extra.write_text(
        "---\n"
        "id: escaping\n"
        "title: Escaping\n"
        "summary: Escaping fixture page.\n"
        "status: ready\n"
        "---\n"
        "# Escaping\n\n"
        "Use <script>alert('x')</script> safely and visit [root](raya:course-root).\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "escape" / "index.html").read_text(
        encoding="utf-8"
    )
    assert "&lt;script&gt;alert('x')&lt;/script&gt;" in html
    assert "<script>" not in html
    assert 'href="../index.html"' in html
    nested = (course / "artifact" / "site" / "unit" / "topic" / "index.html").read_text(
        encoding="utf-8"
    )
    assert 'href="../../index.html"' in nested


def test_official_objects_export_without_personal_state(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    official = json.loads(
        (course / "artifact" / "data" / "official.json").read_text(encoding="utf-8")
    )
    objects = official["objects"]
    assert {item["type"] for item in objects} == {"card", "prompt", "quiz"}
    assert all(item["authority"] == "official" for item in objects)
    assert all(item["scope"]["quantum"] == "first-topic" for item in objects)
    assert all("_official" in item["source_path"] for item in objects)
    forbidden = {"review_history", "confidence", "mastery", "spaced_repetition"}
    assert all(forbidden.isdisjoint(item.keys()) for item in objects)


def test_source_assets_are_copied(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    asset = course / "course" / "_assets" / "notes" / "diagram.txt"
    asset.parent.mkdir(parents=True)
    asset.write_text("asset fixture", encoding="utf-8")

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    copied = course / "artifact" / "assets" / "_source" / "_local" / "notes" / "diagram.txt"
    assert copied.read_text(encoding="utf-8") == "asset fixture"


def test_render_fixture_local_asset_links_are_rewritten_and_copied(tmp_path: Path) -> None:
    course = _copy_render_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    artifact = course / "artifact"
    root_html = (artifact / "site" / "index.html").read_text(encoding="utf-8")
    nested_html = (artifact / "site" / "static-path" / "index.html").read_text(
        encoding="utf-8"
    )
    site_asset = (
        artifact
        / "site"
        / "_raya"
        / "assets"
        / "_source"
        / "_local"
        / "diagrams"
        / "static-path.txt"
    )
    artifact_asset = (
        artifact
        / "assets"
        / "_source"
        / "_local"
        / "diagrams"
        / "static-path.txt"
    )
    site_local_asset = (
        artifact
        / "site"
        / "_raya"
        / "assets"
        / "_source"
        / "1_static_path"
        / "_local"
        / "local-static-path.txt"
    )
    artifact_local_asset = (
        artifact
        / "assets"
        / "_source"
        / "1_static_path"
        / "_local"
        / "local-static-path.txt"
    )

    assert 'href="_raya/assets/_source/_local/diagrams/static-path.txt"' in root_html
    assert 'src="_raya/assets/_source/_local/diagrams/static-path.txt"' in root_html
    assert 'href="static-path/index.html"' in root_html
    assert 'href="../_raya/assets/_source/_local/diagrams/static-path.txt"' in nested_html
    assert (
        'href="../_raya/assets/_source/1_static_path/_local/local-static-path.txt"'
        in nested_html
    )
    assert site_asset.read_text(encoding="utf-8") == artifact_asset.read_text(
        encoding="utf-8"
    )
    assert site_local_asset.read_text(encoding="utf-8") == artifact_local_asset.read_text(
        encoding="utf-8"
    )
    assert "Raya Lucaria render fixture asset" in site_asset.read_text(encoding="utf-8")
    assert "colocated asset" in site_local_asset.read_text(encoding="utf-8")


def test_render_fixture_rich_markdown_baseline(tmp_path: Path) -> None:
    course = _copy_render_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    nested_html = (course / "artifact" / "site" / "static-path" / "index.html").read_text(
        encoding="utf-8"
    )

    assert '<link rel="stylesheet" href="_raya/render/rich.css">' in html
    assert '<nav class="raya-page-toc" aria-label="Page contents">' in html
    assert 'href="#rich-static-baseline"' in html
    assert 'id="duplicate-heading"' in html
    assert 'id="duplicate-heading-2"' in html
    assert "<strong>strong text</strong>" in html
    assert "<em>emphasis</em>" in html
    assert "<code>inline code</code>" in html
    assert "<ol>" in html
    assert "<ul>" in html
    assert "<blockquote>" in html
    assert "<hr />" in html
    assert "<table>" in html
    assert '<span class="math inline">a^2 + b^2 = c^2</span>' in html
    assert '<div class="math block">' in html
    assert 'data-language="python"' in html
    assert 'class="language-python"' in html
    assert 'data-language="unknownlang"' in html
    assert "&lt;script&gt;not_executed()&lt;/script&gt;" in html
    assert '<aside class="raya-callout raya-callout-note"' in html
    assert '<aside class="raya-callout raya-callout-warning"' in html
    assert '<section class="footnotes">' in html
    assert 'href="#fn1"' in html
    assert "&lt;script&gt;alert('fixture')&lt;/script&gt;" in html
    assert "<script>" not in html

    assert '<link rel="stylesheet" href="../_raya/render/rich.css">' in nested_html
    assert 'href="#nested-rich-content"' in nested_html
    assert 'id="nested-duplicate"' in nested_html
    assert 'id="nested-duplicate-2"' in nested_html
    assert '<aside class="raya-callout raya-callout-tip"' in nested_html
    assert '<span class="math inline">x_i</span>' in nested_html


def test_render_fixture_artifact_assets_remain_inspectable(tmp_path: Path) -> None:
    course = _copy_render_fixture(tmp_path)

    build_report = build_course(course)
    inspect_report = inspect_artifact(course / "artifact")

    assert build_report.ok, [diagnostic.format() for diagnostic in build_report.diagnostics]
    assert inspect_report.ok, [
        diagnostic.format() for diagnostic in inspect_report.diagnostics
    ]
    assert (
        course
        / "artifact"
        / "assets"
        / "_source"
        / "_local"
        / "diagrams"
        / "static-path.txt"
    ).exists()
    assert (
        course
        / "artifact"
        / "assets"
        / "_source"
        / "1_static_path"
        / "_local"
        / "local-static-path.txt"
    ).exists()
    assert (
        course / "artifact" / "site" / "_raya" / "render" / "rich.css"
    ).exists()


def test_external_and_fragment_links_are_not_rewritten_as_static_assets(
    tmp_path: Path,
) -> None:
    course = _copy_render_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    assert 'href="https://example.com"' in html
    assert 'href="mailto:test@example.com"' in html
    assert 'href="tel:123"' in html
    assert 'href="#fixture"' in html
    assert 'href="_raya/assets/https://example.com"' not in html


def test_rendered_internal_urls_are_deployment_neutral(tmp_path: Path) -> None:
    course = _copy_render_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    root_html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    nested_html = (course / "artifact" / "site" / "static-path" / "index.html").read_text(
        encoding="utf-8"
    )
    assert 'href="static-path/index.html"' in root_html
    assert 'href="_raya/assets/_source/_local/diagrams/static-path.txt"' in root_html
    assert 'href="../index.html"' in nested_html
    assert 'href="../_raya/assets/_source/_local/diagrams/static-path.txt"' in nested_html
    assert 'href="/_raya/' not in root_html
    assert 'href="/static-path/' not in root_html


def test_source_content_links_are_exported_to_links_index(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\nContinue to [First Topic](1_unit/1_topic/0_index.md).\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    links = json.loads(
        (course / "artifact" / "data" / "links.json").read_text(encoding="utf-8")
    )
    assert {
        "from": "course-root",
        "to": "first-topic",
        "kind": "content",
    } in links["links"]


def test_build_stops_when_footnote_definition_is_missing(tmp_path: Path) -> None:
    source = ROOT / "examples" / "courses" / "invalid" / "missing-footnote-definition"
    course = tmp_path / "missing-footnote-definition"
    shutil.copytree(source, course, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message == "Missing footnote definition"
        and diagnostic.field == "footnote:missing-note"
        for diagnostic in report.diagnostics
    )
    assert not (course / "artifact" / "manifest.json").exists()


def test_rebuild_replaces_stale_artifact_output(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    stale = course / "artifact" / "site" / "stale.html"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale", encoding="utf-8")

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert not stale.exists()


def test_build_stops_when_local_source_link_is_broken(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8") + "\nContinue to [Missing](missing.md).\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    assert any("Broken local content link" in item.message for item in report.diagnostics)
    assert not (course / "artifact" / "manifest.json").exists()


def test_build_stops_when_source_validation_fails(tmp_path: Path) -> None:
    (tmp_path / "raya.yaml").write_text(
        "\n".join(
            [
                "course_id: broken-course",
                "title: Broken Course",
                "description: Missing source",
                "language: en",
                "source: course",
                "artifact: artifact",
            ]
        ),
        encoding="utf-8",
    )

    report = build_course(tmp_path)

    assert not report.ok
    assert any(
        "authored source directory is missing" in item.message
        for item in report.diagnostics
    )
    assert not (tmp_path / "artifact" / "manifest.json").exists()


def _copy_minimal(tmp_path: Path) -> Path:
    course = tmp_path / "course"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))
    return course


def _copy_render_fixture(tmp_path: Path) -> Path:
    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    return course
