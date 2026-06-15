from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from raya_schema import (
    ValidationReport,
    inspect_artifact,
    validate_artifact_manifest,
    validate_cache_index,
    validate_execution_index,
    validate_indices_index,
    validate_links_index,
    validate_navigation_index,
    validate_numbered_objects_index,
    validate_official_index,
    validate_pages_index,
    validate_quanta_index,
    validate_references_index,
    validate_reviewed_outputs_index,
    validate_runtime_index,
)
from raya_static import build_course
from raya_static import builder as static_builder
from raya_static.math_renderer import MathRenderResult
from raya_static.rendering import render_markdown_body


ROOT = Path(__file__).resolve().parents[2]
MINIMAL = ROOT / "examples" / "courses" / "minimal"
RENDER_FIXTURE = ROOT / "examples" / "courses" / "render-fixture"
REFERENCE_FIXTURE = ROOT / "examples" / "courses" / "reference-fixture"
RUNTIME_FIXTURE = ROOT / "examples" / "courses" / "runtime-fixture"
EXECUTION_FIXTURE = ROOT / "examples" / "courses" / "execution-fixture"


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
    assert (artifact / "data" / "references.json").exists()
    assert (artifact / "data" / "numbered-objects.json").exists()
    assert (artifact / "data" / "reviewed-outputs.json").exists()
    assert (artifact / "data" / "runtime.json").exists()
    assert (artifact / "data" / "execution.json").exists()
    assert (artifact / "data" / "cache.json").exists()
    assert (artifact / "assets").is_dir()
    assert (artifact / "files").is_dir()
    assert (artifact / "reviewed").is_dir()
    assert artifact / "manifest.json" in report.outputs_written
    manifest = json.loads((artifact / "manifest.json").read_text(encoding="utf-8"))
    numbered_index = json.loads(
        (artifact / "data" / "numbered-objects.json").read_text(encoding="utf-8")
    )
    assert numbered_index == {
        "version": 1,
        "course_id": "minimal-course",
        "objects": [],
        "by_id": {},
    }
    assert manifest["data"]["numbered_objects"] == "data/numbered-objects.json"


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
        validate_references_index(artifact / "data" / "references.json"),
        validate_reviewed_outputs_index(artifact / "data" / "reviewed-outputs.json"),
        validate_numbered_objects_index(artifact / "data" / "numbered-objects.json"),
        validate_runtime_index(artifact / "data" / "runtime.json"),
        validate_execution_index(artifact / "data" / "execution.json"),
        validate_cache_index(artifact / "data" / "cache.json"),
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
    assert 'src="_raya/assets/_source/_local/diagrams/static-path.svg"' in root_html
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


def test_rich_static_fixture_renders_markdown_math_code_and_assets(
    tmp_path: Path,
) -> None:
    course = _copy_render_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    nested_html = (course / "artifact" / "site" / "static-path" / "index.html").read_text(
        encoding="utf-8"
    )
    math_authoring_html = (
        course / "artifact" / "site" / "math-authoring" / "index.html"
    ).read_text(encoding="utf-8")
    math_authoring_visible = _visible_text(math_authoring_html)
    numbered_index = json.loads(
        (
            course / "artifact" / "data" / "numbered-objects.json"
        ).read_text(encoding="utf-8")
    )

    assert numbered_index["course_id"] == "render-fixture"
    assert "by_id" in numbered_index
    assert '<link rel="stylesheet" href="_raya/render/rich.css">' in html
    assert '<link rel="stylesheet" href="_raya/render/math/mathjax.css">' in html
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
    assert "mjx-container" in html
    assert 'src="_raya/assets/_source/_local/diagrams/static-path.svg"' in html
    assert "Fixture authority remains in docs/foundation/" in _visible_text(html)
    assert "Linear Algebra Fixture" in _visible_text(html)
    assert "Probability and Statistics Fixture" in _visible_text(html)
    assert "Macro Redefinition Fixture" in _visible_text(html)
    assert "$5 and $x$" in _visible_text(html)
    assert "\\rayaVec" not in _visible_text(html)
    assert "\\argmax" not in _visible_text(html)
    assert "\\renewcommand" not in _visible_text(html)
    assert "\\fixtureUnit" not in _visible_text(html)
    assert "a^2 + b^2 = c^2" not in _visible_text(html)
    assert '<span class="math inline">a^2 + b^2 = c^2</span>' not in html
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
    assert 'href="math-authoring/index.html"' in html

    assert '<link rel="stylesheet" href="../_raya/render/rich.css">' in nested_html
    assert (
        '<link rel="stylesheet" href="../_raya/render/math/mathjax.css">'
        in nested_html
    )
    assert 'href="#nested-rich-content"' in nested_html
    assert 'id="nested-duplicate"' in nested_html
    assert 'id="nested-duplicate-2"' in nested_html
    assert '<aside class="raya-callout raya-callout-tip"' in nested_html
    assert "mjx-container" in nested_html
    assert '<span class="math inline">x_i</span>' not in nested_html
    assert "display math remain static" not in _visible_text(nested_html)
    assert "pre-rendered display math" in _visible_text(nested_html)

    assert '<link rel="stylesheet" href="../_raya/render/rich.css">' in math_authoring_html
    assert (
        '<link rel="stylesheet" href="../_raya/render/math/mathjax.css">'
        in math_authoring_html
    )
    assert "Math Authoring Fixture" in math_authoring_visible
    assert "Inline And Display Math" in math_authoring_visible
    assert "Vectors And Matrices" in math_authoring_visible
    assert "Page Local Macros" in math_authoring_visible
    assert "Sets Logic And Functions" in math_authoring_visible
    assert "Aligned Derivations And Optimization" in math_authoring_visible
    assert "Theorem Like Writing With Current Markdown" in math_authoring_visible
    assert "Macro Redefinition" in math_authoring_visible
    assert "mjx-container" in math_authoring_html
    assert "This theorem-like block is authored Markdown" in math_authoring_visible
    assert "Real theorem numbering and references are planned next" in math_authoring_visible
    assert "$10" in math_authoring_visible
    assert "$" not in math_authoring_visible.replace("$10", "")
    for raw_marker in (
        "\\newcommand",
        "\\renewcommand",
        "\\begin{bmatrix}",
        "\\rayaVec",
        "\\fixtureNorm",
        "\\mathbb",
        "\\forall",
        "\\int",
        "\\frac",
        "\\label",
        "\\ref",
    ):
        assert raw_marker not in math_authoring_visible


def test_callout_macro_definition_applies_to_later_page_math(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "> [!NOTE]\n"
        "> $\\newcommand{\\calloutmacro}[1]{\\mathbf{#1}}$\n\n"
        "Later page math uses $\\calloutmacro{x}$.\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    assert "mjx-container" in html
    assert "\\calloutmacro" not in _visible_text(html)


def test_callout_macro_use_before_later_page_definition_fails(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "> [!NOTE]\n"
        "> $\\latermacro{x}$\n\n"
        "$\\newcommand{\\latermacro}[1]{\\mathbf{#1}}$\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message == "Math rendering failed"
        and diagnostic.field == "math:math-0"
        and "\\latermacro{x}" in (diagnostic.next_action or "")
        for diagnostic in report.diagnostics
    )


def test_failed_later_page_math_keeps_previous_artifact(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    first_report = build_course(course)
    old_manifest = (course / "artifact" / "manifest.json").read_text(encoding="utf-8")
    old_topic_html = (
        course / "artifact" / "site" / "unit" / "topic" / "index.html"
    ).read_text(encoding="utf-8")
    topic = course / "course" / "1_unit" / "1_topic" / "0_index.md"
    topic.write_text(
        topic.read_text(encoding="utf-8") + "\n\nLater invalid math $\\unknownmacro$.\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert first_report.ok, [diagnostic.format() for diagnostic in first_report.diagnostics]
    assert not report.ok
    assert any(
        diagnostic.message == "Math rendering failed"
        and "unknownmacro" in (diagnostic.next_action or "")
        for diagnostic in report.diagnostics
    )
    assert (course / "artifact" / "manifest.json").read_text(encoding="utf-8") == old_manifest
    assert (
        course / "artifact" / "site" / "unit" / "topic" / "index.html"
    ).read_text(encoding="utf-8") == old_topic_html


def test_missing_math_html_diagnostic_names_item_and_excerpt(tmp_path: Path) -> None:
    report = ValidationReport(context="render-test")

    html = render_markdown_body(
        "Use $x_i$ here.",
        generated_index="",
        resolve_href=lambda href: href,
        source_path=tmp_path / "source.md",
        report=report,
        math_renderer=_MissingMathHtmlRenderer(),
    )

    assert html == ""
    assert not report.ok
    assert any(
        diagnostic.message == "Math rendering failed"
        and diagnostic.field == "math:math-0"
        and "x_i" in (diagnostic.next_action or "")
        for diagnostic in report.diagnostics
    )


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
    assert (
        course / "artifact" / "site" / "_raya" / "render" / "math" / "mathjax.css"
    ).exists()
    assert (
        course
        / "artifact"
        / "site"
        / "_raya"
        / "render"
        / "math"
        / "fonts"
        / "mjx-ncm-n.woff2"
    ).exists()


def test_render_fixture_reports_missing_local_math_font_assets(
    tmp_path: Path,
    monkeypatch,
) -> None:
    course = _copy_render_fixture(tmp_path)
    missing_fonts = tmp_path / "missing-mathjax-fonts"
    monkeypatch.setattr(static_builder, "MATH_FONT_SOURCE_DIR", missing_fonts)

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message == "Missing local MathJax font assets"
        and diagnostic.path == missing_fonts
        and "npm ci --ignore-scripts --no-audit --no-fund"
        in (diagnostic.next_action or "")
        for diagnostic in report.diagnostics
    )


def test_missing_math_fonts_keep_previous_artifact(
    tmp_path: Path,
    monkeypatch,
) -> None:
    course = _copy_render_fixture(tmp_path)
    first_report = build_course(course)
    old_manifest = (course / "artifact" / "manifest.json").read_text(encoding="utf-8")
    old_page = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    missing_fonts = tmp_path / "missing-mathjax-fonts"
    monkeypatch.setattr(static_builder, "MATH_FONT_SOURCE_DIR", missing_fonts)

    report = build_course(course)

    assert first_report.ok, [diagnostic.format() for diagnostic in first_report.diagnostics]
    assert not report.ok
    assert any(
        diagnostic.message == "Missing local MathJax font assets"
        and diagnostic.path == missing_fonts
        for diagnostic in report.diagnostics
    )
    assert (course / "artifact" / "manifest.json").read_text(encoding="utf-8") == old_manifest
    assert (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8") == old_page


def test_math_resource_writer_reports_css_referenced_missing_fonts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    font_source = tmp_path / "fonts-source"
    font_source.mkdir()
    (font_source / "mjx-ncm-n.woff2").write_bytes(b"font")
    monkeypatch.setattr(static_builder, "MATH_FONT_SOURCE_DIR", font_source)
    report = ValidationReport(context="build")

    resources = static_builder._prepare_math_render_resources(
        [
            (
                "mjx-container { display: inline-block; }\n"
                '@font-face { src: url("fonts/mjx-ncm-n.woff2"); }\n'
                "@font-face { src: url('fonts/mjx-ncm-i.woff2'); }\n"
                "@font-face { src: url(fonts/mjx-ncm-b.woff2); }\n"
            )
        ],
        report,
    )

    assert resources.font_files == ()
    assert not report.ok
    assert any(
        diagnostic.message == "Missing local MathJax font assets"
        and diagnostic.path == font_source
        and "mjx-ncm-i.woff2" in (diagnostic.next_action or "")
        and "mjx-ncm-b.woff2" in (diagnostic.next_action or "")
        and "npm ci --ignore-scripts --no-audit --no-fund"
        in (diagnostic.next_action or "")
        for diagnostic in report.diagnostics
    )


def test_math_font_names_from_css_supports_local_url_variants() -> None:
    report = ValidationReport(context="build")

    names = static_builder._math_font_names_from_css(
        "\n".join(
            [
                '@font-face { src: url("fonts/mjx-ncm-n.woff2"); }',
                "@font-face { src: url('fonts/mjx-ncm-i.woff2?v=1#hash'); }",
                "@font-face { src: url( ./fonts/mjx-ncm-b.woff2 ); }",
            ]
        ),
        report=report,
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert names == ["mjx-ncm-b.woff2", "mjx-ncm-i.woff2", "mjx-ncm-n.woff2"]


def test_math_font_names_from_css_rejects_nonlocal_urls() -> None:
    report = ValidationReport(context="build")

    names = static_builder._math_font_names_from_css(
        "\n".join(
            [
                '@font-face { src: url("https://cdn.example/mjx-ncm-n.woff2"); }',
                "@font-face { src: url(//cdn.example/mjx-ncm-i.woff2); }",
                "@font-face { src: url(/fonts/mjx-ncm-b.woff2); }",
                "@font-face { src: url(fonts/../mjx-ncm-c.woff2); }",
            ]
        ),
        report=report,
    )

    assert names == []
    assert not report.ok
    assert len(report.diagnostics) == 4
    assert all(
        diagnostic.message == "Unsupported MathJax font URL"
        and diagnostic.field == "math.fonts"
        for diagnostic in report.diagnostics
    )


def test_reference_fixture_builds_reference_artifacts(tmp_path: Path) -> None:
    course = _copy_reference_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    artifact = course / "artifact"
    manifest = json.loads((artifact / "manifest.json").read_text(encoding="utf-8"))
    references = json.loads(
        (artifact / "data" / "references.json").read_text(encoding="utf-8")
    )
    root_html = (artifact / "site" / "index.html").read_text(encoding="utf-8")
    nested_html = (artifact / "site" / "analysis" / "index.html").read_text(
        encoding="utf-8"
    )

    assert manifest["data"]["references"] == "data/references.json"
    assert manifest["files"] == "files"
    assert len(references["references"]) == 5
    assert {item["kind"] for item in references["references"]} == {"code", "notebook"}
    assert all(
        item["execution"]["status"] == "not-executed"
        for item in references["references"]
    )
    assert any(
        item["source_path"] == "1_analysis/scripts/clean_data.py"
        and item["browser_path"] == "_raya/files/_source/1_analysis/scripts/clean_data.py"
        and item["artifact_path"] == "files/_source/1_analysis/scripts/clean_data.py"
        for item in references["references"]
    )
    assert (
        artifact / "files" / "_source" / "1_analysis" / "scripts" / "clean_data.py"
    ).exists()
    assert (
        artifact
        / "site"
        / "_raya"
        / "files"
        / "_source"
        / "1_analysis"
        / "labs"
        / "exploration.ipynb"
    ).exists()
    assert 'href="_raya/files/_source/code/shared_helper.py"' in root_html
    assert 'href="_raya/files/_source/notebooks/overview.ipynb"' in root_html
    assert 'href="../_raya/files/_source/1_analysis/scripts/clean_data.py"' in nested_html
    assert (
        'href="../_raya/files/_source/1_analysis/labs/exploration.ipynb"'
        in nested_html
    )
    assert not (
        artifact / "files" / "_source" / "unlinked" / "unused_helper.py"
    ).exists()
    assert not (
        artifact / "site" / "_raya" / "files" / "_source" / "unlinked" / "unused_notebook.ipynb"
    ).exists()
    assert '<section class="raya-reference-panel" aria-label="Referenced work"' in root_html
    assert "These files are copied for reading and download. They were not executed during build." in root_html
    assert "Reference fixture helper" in root_html
    assert "1. markdown: # Overview notebook" in root_html
    assert "ignored output" not in root_html
    assert 'data-raya-surface="student-default"' in root_html
    assert 'data-raya-surface="support-panel"' in root_html

    visible_text = _visible_text(root_html + nested_html)
    assert "Referenced Work" in visible_text
    assert "Script" in visible_text
    assert "Notebook" in visible_text
    assert "not executed" in visible_text
    for item in references["references"]:
        assert item["sha256"] not in visible_text
        assert item["artifact_path"] not in visible_text
        assert item["browser_path"] not in visible_text
    assert "source_path" not in visible_text
    assert "artifact_path" not in visible_text
    assert "browser_path" not in visible_text

    inspection_html = (
        artifact / "site" / "_raya" / "inspect" / "index.html"
    ).read_text(encoding="utf-8")
    assert 'data-raya-surface="inspection"' in inspection_html
    assert "Surface tier: inspection" in inspection_html
    assert "Artifact path" in inspection_html
    assert "Browser path" in inspection_html
    assert references["references"][0]["sha256"] in inspection_html
    assert 'href="../files/_source/code/shared_helper.py"' in inspection_html


def test_runtime_fixture_builds_metadata_without_execution(tmp_path: Path) -> None:
    course = _copy_runtime_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    artifact = course / "artifact"
    manifest = json.loads((artifact / "manifest.json").read_text(encoding="utf-8"))
    runtime = json.loads((artifact / "data" / "runtime.json").read_text(encoding="utf-8"))
    execution = json.loads(
        (artifact / "data" / "execution.json").read_text(encoding="utf-8")
    )
    cache = json.loads((artifact / "data" / "cache.json").read_text(encoding="utf-8"))
    references = json.loads(
        (artifact / "data" / "references.json").read_text(encoding="utf-8")
    )
    html = (artifact / "site" / "index.html").read_text(encoding="utf-8")

    assert manifest["data"]["runtime"] == "data/runtime.json"
    assert manifest["data"]["execution"] == "data/execution.json"
    assert manifest["data"]["cache"] == "data/cache.json"
    assert runtime["profiles"][0]["manager"] == "uv"
    assert runtime["profiles"][0]["docker"]["compose_service"] == "dev"
    assert runtime["defaults"] == {"policy": "never", "profile": "default"}
    assert len(execution["targets"]) == 1
    assert execution["targets"][0]["policy"] == "cache"
    assert execution["targets"][0]["profile"] == "default"
    assert execution["targets"][0]["status"] == "not-executed"
    assert execution["targets"][0]["inputs"] == ["course/_assets/runtime-input.txt"]
    assert len(cache["entries"]) == 1
    assert cache["entries"][0]["policy"] == "cache"
    assert len(cache["entries"][0]["cache_key"]) == 64
    assert references["references"][0]["execution"]["policy"] == "cache"
    assert references["references"][0]["execution"]["profile"] == "default"
    assert "runtime_task.py" in html
    assert "not executed during build" in html
    visible_text = _visible_text(html)
    assert cache["entries"][0]["cache_key"] not in visible_text
    assert "cache_key" not in visible_text
    assert "runtime/profiles.yaml" not in visible_text
    assert not (course / "SHOULD_NOT_EXIST_RUNTIME_SENTINEL").exists()
    assert not (artifact / "SHOULD_NOT_EXIST_RUNTIME_SENTINEL").exists()


def test_execution_fixture_builds_reviewed_output_panel_without_execution(
    tmp_path: Path,
) -> None:
    course = _copy_execution_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    artifact = course / "artifact"
    manifest = json.loads((artifact / "manifest.json").read_text(encoding="utf-8"))
    reviewed = json.loads(
        (artifact / "data" / "reviewed-outputs.json").read_text(encoding="utf-8")
    )
    references = json.loads(
        (artifact / "data" / "references.json").read_text(encoding="utf-8")
    )
    html = (artifact / "site" / "index.html").read_text(encoding="utf-8")

    assert manifest["data"]["reviewed_outputs"] == "data/reviewed-outputs.json"
    assert reviewed["authority"] == "reviewed-course-support"
    outputs_by_id = {item["id"]: item for item in reviewed["outputs"]}
    assert outputs_by_id["frozen-script"]["files"][0]["browser_path"] == (
        "_raya/reviewed/frozen-script/stdout.txt"
    )
    assert outputs_by_id["demo-notebook"]["files"][0]["browser_path"] == (
        "_raya/reviewed/demo-notebook/demo-notebook.ipynb"
    )
    assert any(
        item["execution"].get("reviewed_output", {}).get("id") == "frozen-script"
        for item in references["references"]
    )
    assert "Reviewed Output" in html
    assert "frozen reviewed output fixture" in html
    assert "reviewed output current" in html
    visible_text = _visible_text(html)
    assert "profile default" not in visible_text
    assert outputs_by_id["frozen-script"]["review_key"] not in visible_text
    assert outputs_by_id["frozen-script"]["source_sha256"] not in visible_text
    assert "cache_key" not in visible_text
    inspection_html = (
        artifact / "site" / "_raya" / "inspect" / "index.html"
    ).read_text(encoding="utf-8")
    assert "Review key" in inspection_html
    assert outputs_by_id["frozen-script"]["review_key"] in inspection_html
    assert 'href="../reviewed/frozen-script/stdout.txt"' in inspection_html
    assert (
        artifact / "site" / "_raya" / "reviewed" / "frozen-script" / "stdout.txt"
    ).exists()
    assert (
        artifact
        / "site"
        / "_raya"
        / "reviewed"
        / "demo-notebook"
        / "demo-notebook.ipynb"
    ).exists()
    assert not (course / "SHOULD_NOT_EXIST_FROZEN_SENTINEL").exists()
    assert not (course / "execution-side-effect.txt").exists()


def test_reference_fixture_artifact_inspection_checks_copied_files(
    tmp_path: Path,
) -> None:
    course = _copy_reference_fixture(tmp_path)

    build_report = build_course(course)
    assert build_report.ok, [
        diagnostic.format() for diagnostic in build_report.diagnostics
    ]
    missing = (
        course
        / "artifact"
        / "site"
        / "_raya"
        / "files"
        / "_source"
        / "code"
        / "shared_helper.py"
    )
    missing.unlink()

    inspect_report = inspect_artifact(course / "artifact")

    assert not inspect_report.ok
    assert any(
        item.message == "Referenced artifact file is missing"
        for item in inspect_report.diagnostics
    )


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


def test_build_stops_when_mathjax_expression_fails(tmp_path: Path) -> None:
    source = ROOT / "examples" / "courses" / "invalid" / "broken-math-expression"
    course = tmp_path / "broken-math-expression"
    shutil.copytree(source, course, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message == "Math rendering failed"
        and diagnostic.field.startswith("math:")
        and diagnostic.path == course / "course" / "0_index.md"
        and "unknownmacro" in (diagnostic.next_action or "")
        for diagnostic in report.diagnostics
    )
    assert not (course / "artifact" / "manifest.json").exists()


def test_build_stops_when_display_math_delimiter_is_unclosed(
    tmp_path: Path,
) -> None:
    source = ROOT / "examples" / "courses" / "invalid" / "unclosed-display-math"
    course = tmp_path / "unclosed-display-math"
    shutil.copytree(source, course, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message == "Malformed display math delimiter"
        and diagnostic.field == "math:display-delimiter"
        and diagnostic.path == course / "course" / "0_index.md"
        and "$$" in (diagnostic.next_action or "")
        for diagnostic in report.diagnostics
    )
    assert not (course / "artifact" / "manifest.json").exists()


def test_build_stops_when_full_latex_document_is_used(tmp_path: Path) -> None:
    source = ROOT / "examples" / "courses" / "invalid" / "full-latex-document"
    course = tmp_path / "full-latex-document"
    shutil.copytree(source, course, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message == "Full LaTeX documents are not supported"
        and diagnostic.field == "math:latex-document"
        and diagnostic.path == course / "course" / "0_index.md"
        and "\\documentclass" in (diagnostic.next_action or "")
        for diagnostic in report.diagnostics
    )
    assert not (course / "artifact" / "manifest.json").exists()


def test_build_stops_when_math_delimiters_are_nested(tmp_path: Path) -> None:
    source = ROOT / "examples" / "courses" / "invalid" / "nested-math-delimiters"
    course = tmp_path / "nested-math-delimiters"
    shutil.copytree(source, course, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message == "Unsupported nested math delimiter"
        and diagnostic.field == "math:delimiter-nesting"
        and diagnostic.path == course / "course" / "0_index.md"
        and "$$" in (diagnostic.next_action or "")
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


def _copy_reference_fixture(tmp_path: Path) -> Path:
    course = tmp_path / "reference-fixture"
    shutil.copytree(REFERENCE_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    return course


def _copy_runtime_fixture(tmp_path: Path) -> Path:
    course = tmp_path / "runtime-fixture"
    shutil.copytree(RUNTIME_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    return course


def _copy_execution_fixture(tmp_path: Path) -> Path:
    course = tmp_path / "execution-fixture"
    shutil.copytree(EXECUTION_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    return course


def _visible_text(html_text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", html_text))


class _MissingMathHtmlRenderer:
    def render_many(self, items, *, report: ValidationReport) -> MathRenderResult:
        return MathRenderResult(html_by_id={}, css="")
