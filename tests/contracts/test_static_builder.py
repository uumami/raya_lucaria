from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from types import SimpleNamespace

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


def test_build_applies_course_skin_to_pages_and_writes_skin_css(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    config = course / "raya.yaml"
    config.write_text(
        config.read_text(encoding="utf-8")
        + "\nrender:\n  skin: warm-academic\n",
        encoding="utf-8",
    )
    skins_dir = course / "skins"
    skins_dir.mkdir()
    (skins_dir / "warm-academic.yaml").write_text(
        "id: warm-academic\n"
        "name: Warm Academic\n"
        "tokens:\n"
        "  color:\n"
        '    page: "#ffffff"\n'
        '    surface: "#f6f8fa"\n'
        '    text: "#1f2328"\n'
        '    muted: "#57606a"\n'
        '    accent: "#0969da"\n'
        '    accent_soft: "#ddf4ff"\n'
        '    border: "#d0d7de"\n'
        '    success: "#1a7f37"\n'
        '    warning: "#9a6700"\n'
        '    danger: "#cf222e"\n'
        "  font:\n"
        '    body: "system-ui"\n'
        '    heading: "system-ui"\n'
        '    mono: "ui-monospace"\n'
        "  density: comfortable\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    index_html = (course / "artifact" / "site" / "index.html").read_text(
        encoding="utf-8"
    )
    skin_css = course / "artifact" / "site" / "_raya" / "render" / "skin.css"
    assert 'data-raya-skin="warm-academic"' in index_html
    assert '<link rel="stylesheet" href="_raya/render/skin.css">' in index_html
    assert skin_css.exists()
    assert '[data-raya-skin="warm-academic"]' in skin_css.read_text(encoding="utf-8")


def test_build_applies_nearest_section_skin_to_descendant_pages(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    config = course / "raya.yaml"
    config.write_text(
        config.read_text(encoding="utf-8")
        + "\nrender:\n  skin: warm-academic\n",
        encoding="utf-8",
    )
    _write_test_skin(course / "skins" / "warm-academic.yaml", "warm-academic")
    _write_test_skin(course / "skins" / "practice-lab.yaml", "practice-lab")
    _write_test_skin(course / "skins" / "topic-lab.yaml", "topic-lab")
    selector = course / "course" / "1_unit" / "_raya" / "skin.yaml"
    selector.parent.mkdir(parents=True)
    selector.write_text("render:\n  skin: practice-lab\n", encoding="utf-8")
    topic_selector = (
        course / "course" / "1_unit" / "1_topic" / "_raya" / "skin.yaml"
    )
    topic_selector.parent.mkdir(parents=True)
    topic_selector.write_text("render:\n  skin: topic-lab\n", encoding="utf-8")

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    root_html = (course / "artifact" / "site" / "index.html").read_text(
        encoding="utf-8"
    )
    unit_html = (course / "artifact" / "site" / "unit" / "index.html").read_text(
        encoding="utf-8"
    )
    topic_html = (
        course / "artifact" / "site" / "unit" / "topic" / "index.html"
    ).read_text(encoding="utf-8")
    assert 'data-raya-skin="warm-academic"' in root_html
    assert 'data-raya-skin="practice-lab"' in unit_html
    assert 'data-raya-skin="topic-lab"' in topic_html


def test_build_fails_for_unknown_course_skin(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    config = course / "raya.yaml"
    config.write_text(
        config.read_text(encoding="utf-8")
        + "\nrender:\n  skin: missing-skin\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    messages = [diagnostic.format() for diagnostic in report.diagnostics]
    assert any("Unknown render skin 'missing-skin'" in message for message in messages)
    assert any("render.skin" in message for message in messages)


def test_build_fails_for_invalid_skin_color(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    (course / "raya.yaml").write_text(
        (course / "raya.yaml").read_text(encoding="utf-8")
        + "\nrender:\n  skin: broken\n",
        encoding="utf-8",
    )
    _write_test_skin(course / "skins" / "broken.yaml", "broken")
    skin_path = course / "skins" / "broken.yaml"
    skin_path.write_text(
        skin_path.read_text(encoding="utf-8").replace(
            'page: "#ffffff"',
            'page: "white"',
        ),
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    assert any(
        "tokens.color.page" in diagnostic.format()
        for diagnostic in report.diagnostics
    )


def test_build_fails_for_section_skin_selector_without_section_index(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    _write_test_skin(course / "skins" / "practice-lab.yaml", "practice-lab")
    selector = course / "course" / "orphan" / "_raya" / "skin.yaml"
    selector.parent.mkdir(parents=True)
    selector.write_text("render:\n  skin: practice-lab\n", encoding="utf-8")

    report = build_course(course)

    assert not report.ok
    assert any(
        "_raya/skin.yaml must live beside a section 0_index.md"
        in diagnostic.format()
        for diagnostic in report.diagnostics
    )


def test_build_fails_for_low_contrast_skin(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    (course / "raya.yaml").write_text(
        (course / "raya.yaml").read_text(encoding="utf-8")
        + "\nrender:\n  skin: low-contrast\n",
        encoding="utf-8",
    )
    _write_test_skin(course / "skins" / "low-contrast.yaml", "low-contrast")
    skin_path = course / "skins" / "low-contrast.yaml"
    skin_path.write_text(
        skin_path.read_text(encoding="utf-8").replace(
            'text: "#1f2328"',
            'text: "#ffffff"',
        ),
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    assert any(
        "Skin contrast for text on page is too low" in diagnostic.format()
        and "tokens.color.text" in diagnostic.format()
        and "tokens.color.page" in diagnostic.format()
        for diagnostic in report.diagnostics
    )


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


def test_build_collects_numbered_objects_with_page_hierarchy(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    config = course / "raya.yaml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "course_id: minimal-course",
            "course_id: numbered-demo",
        ),
        encoding="utf-8",
    )
    parent = course / "course" / "2_vectors" / "0_index.md"
    parent.parent.mkdir(parents=True)
    parent.write_text(
        "---\n"
        "id: vectors\n"
        "title: Vectors\n"
        "summary: Parent fixture page.\n"
        "status: ready\n"
        "---\n"
        "# Vectors\n",
        encoding="utf-8",
    )
    page = course / "course" / "2_vectors" / "3_norms" / "0_index.md"
    page.parent.mkdir(parents=True)
    page.write_text(
        "---\n"
        "id: vector-norms\n"
        "title: Vector Norms\n"
        "summary: Numbered object fixture.\n"
        "status: ready\n"
        "---\n"
        "# Vector Norms\n\n"
        "::: theorem {#main title=\"Main theorem\"}\n"
        "Main theorem body.\n"
        ":::\n\n"
        "::: corollary {#consequence}\n"
        "Consequence body.\n"
        ":::\n\n"
        "::: exercise {#practice}\n"
        "Practice body.\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    numbered_index = json.loads(
        (course / "artifact" / "data" / "numbered-objects.json").read_text(
            encoding="utf-8"
        )
    )
    objects = numbered_index["objects"]
    assert numbered_index["course_id"] == "numbered-demo"
    assert numbered_index["by_id"] == {"main": 0, "consequence": 1, "practice": 2}
    assert [item["id"] for item in objects] == ["main", "consequence", "practice"]
    assert [item["number"] for item in objects] == ["2.3.1", "2.3.2", "2.3.1"]
    assert objects[0]["href"].endswith("#raya-object-main")


def test_build_numbers_objects_with_display_labels_not_raw_prefixes(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    shutil.rmtree(course / "course" / "1_unit")
    vectors_index = course / "course" / "2_vectors" / "0_index.md"
    vectors_index.parent.mkdir(parents=True)
    vectors_index.write_text(
        "---\n"
        "id: vectors\n"
        "title: Vectors\n"
        "summary: Vector section fixture.\n"
        "status: ready\n"
        "---\n"
        "# Vectors\n",
        encoding="utf-8",
    )
    main_page = course / "course" / "2_vectors" / "3_norms" / "0_index.md"
    main_page.parent.mkdir(parents=True)
    main_page.write_text(
        "---\n"
        "id: padded-norms\n"
        "title: Padded Norms\n"
        "summary: Padded source prefix fixture.\n"
        "status: ready\n"
        "---\n"
        "# Padded Norms\n\n"
        "::: theorem {#padded-theorem}\n"
        "Padded prefixes should not appear in reader-facing object numbers.\n"
        ":::\n",
        encoding="utf-8",
    )
    appendix_index = course / "course" / "A_reference" / "0_index.md"
    appendix_index.parent.mkdir(parents=True)
    appendix_index.write_text(
        "---\n"
        "id: appendix-reference\n"
        "title: Appendix Reference\n"
        "summary: Appendix section fixture.\n"
        "status: ready\n"
        "---\n"
        "# Appendix Reference\n",
        encoding="utf-8",
    )
    appendix_page = course / "course" / "A_reference" / "1_topic" / "0_index.md"
    appendix_page.parent.mkdir(parents=True)
    appendix_page.write_text(
        "---\n"
        "id: appendix-topic\n"
        "title: Appendix Topic\n"
        "summary: Appendix object numbering fixture.\n"
        "status: ready\n"
        "---\n"
        "# Appendix Topic\n\n"
        "::: theorem {#appendix-theorem}\n"
        "Appendix labels should remain visible in object numbers.\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    numbered_index = json.loads(
        (course / "artifact" / "data" / "numbered-objects.json").read_text(
            encoding="utf-8"
        )
    )
    by_id = {obj["id"]: obj for obj in numbered_index["objects"]}
    assert by_id["padded-theorem"]["number"] == "2.3.1"
    assert by_id["appendix-theorem"]["number"] == "A.1.1"


def test_numbered_objects_render_html_and_cross_references(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    shutil.rmtree(course / "course" / "1_unit")
    home = course / "course" / "0_index.md"
    home.write_text(
        home.read_text(encoding="utf-8")
        + "\n\n"
        "Use @pythagorean and a [named theorem](raya:ref/pythagorean).\n",
        encoding="utf-8",
    )
    math_page = course / "course" / "1_math" / "0_index.md"
    math_page.parent.mkdir(parents=True)
    math_page.write_text(
        "---\n"
        "id: math\n"
        "title: Math\n"
        "summary: Numbered object rendering fixture.\n"
        "status: ready\n"
        "---\n"
        "# Math\n\n"
        "::: theorem {#pythagorean title=\"Pythagorean theorem\"}\n"
        "For a right triangle, $a^2 + b^2 = c^2$.\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    home_html = (course / "artifact" / "site" / "index.html").read_text(
        encoding="utf-8"
    )
    math_html = (course / "artifact" / "site" / "math" / "index.html").read_text(
        encoding="utf-8"
    )
    assert 'href="math/index.html#raya-object-pythagorean"' in home_html
    assert "Theorem 1.1" in _visible_text(home_html)
    assert (
        '<a href="math/index.html#raya-object-pythagorean">named theorem</a>'
        in home_html
    )
    assert 'id="raya-object-pythagorean"' in math_html
    assert (
        'class="raya-numbered-object raya-numbered-object--scannable '
        'raya-numbered-object--theorem"'
        in math_html
    )
    assert 'class="raya-numbered-object-layout"' in math_html
    assert 'class="raya-numbered-object-badge" aria-hidden="true"' in math_html
    assert 'class="raya-numbered-object-badge-label">Theorem</span>' in math_html
    assert 'class="raya-numbered-object-badge-number">1.1</span>' in math_html
    assert "Pythagorean theorem" in _visible_text(math_html)
    assert "a^2 + b^2" not in _visible_text(math_html)
    assert "mjx-container" in math_html


def test_numbered_objects_default_scannable_keeps_caption_and_equation_styles(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    page = course / "course" / "0_index.md"
    page.write_text(
        "---\n"
        "id: style-demo\n"
        "title: Style Demo\n"
        "summary: Numbered object style fixture.\n"
        "status: ready\n"
        "---\n"
        "# Style Demo\n\n"
        "::: remark {#reader-remark title=\"Reader note\"}\n"
        "A remark should use the scannable reader style.\n"
        ":::\n\n"
        "::: figure {#reader-figure title=\"Reader figure\"}\n"
        "![Figure asset](_assets/style-demo.txt)\n"
        ":::\n\n"
        "::: equation {#reader-equation}\n"
        "$$\n"
        "x + y = y + x\n"
        "$$\n"
        ":::\n",
        encoding="utf-8",
    )
    assets = course / "course" / "_assets"
    assets.mkdir(exist_ok=True)
    (assets / "style-demo.txt").write_text("style fixture\n", encoding="utf-8")

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    numbered_index = json.loads(
        (course / "artifact" / "data" / "numbered-objects.json").read_text(
            encoding="utf-8"
        )
    )
    by_id = {item["id"]: item for item in numbered_index["objects"]}
    assert by_id["reader-remark"]["style"] == "scannable"
    assert by_id["reader-figure"]["style"] == "caption"
    assert by_id["reader-equation"]["style"] == "equation"
    assert "Remark 1" in _visible_text(html)
    assert 'raya-numbered-object--remark' in html
    assert 'raya-numbered-object--scannable' in html
    assert 'raya-numbered-object--caption' in html
    assert 'raya-numbered-object--equation' in html


def test_build_renders_proof_of_numbered_object(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    course.joinpath("raya.yaml").write_text(
        course.joinpath("raya.yaml")
        .read_text(encoding="utf-8")
        .replace(
            "source: course",
            "source: course\nrender:\n  numbered_objects:\n    scheme: section",
        )
        .replace("course_id: minimal-course", "course_id: proof-demo"),
        encoding="utf-8",
    )
    page = course / "course" / "0_index.md"
    page.write_text(
        "\n".join(
            [
                "---",
                "id: proof-demo",
                "title: Proof Demo",
                "summary: Proof rendering fixture.",
                "status: ready",
                "---",
                "",
                "# Proof Demo",
                "",
                '::: theorem {#main-theorem title="Fixture theorem"}',
                "For every vector $v$, $v=v$.",
                ":::",
                "",
                '::: proof {#proof-main of="main-theorem" title="Identity"}',
                "Use @main-theorem. The vector identity follows from $v-v=0$.",
                ":::",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    visible = _visible_text(html)
    numbered_index = json.loads(
        (course / "artifact" / "data" / "numbered-objects.json").read_text(
            encoding="utf-8"
        )
    )
    assert "Proof of Theorem 1" in visible
    assert "Identity" in visible
    assert "Use Theorem 1" in visible
    assert "raya-proof" in html
    assert 'id="raya-proof-proof-main"' in html
    assert 'href="index.html#raya-object-main-theorem"' in html
    assert "mjx-container" in html
    assert "proof-main" not in numbered_index["by_id"]
    assert list(numbered_index["by_id"]) == ["main-theorem"]
    assert 'class="raya-proof"' in html
    assert "raya-static-environment--proof" not in html
    assert '<span class="raya-proof-reference">Proof of Theorem 1</span>' in html
    assert '<span class="raya-proof-title">Identity</span>' in html
    assert '<span class="raya-proof-qed" aria-hidden="true">&#x25A1;</span>' in html
    assert "RAYA_PROOF_" not in visible
    assert "\\(" not in visible


def test_static_environments_render_targeted_headings_and_stay_out_of_numbered_index(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    page = course / "course" / "0_index.md"
    page.write_text(
        "---\n"
        "id: static-environments\n"
        "title: Static Environments\n"
        "summary: Static environment fixture.\n"
        "status: ready\n"
        "---\n"
        "# Static Environments\n\n"
        "::: problem {#residual-problem title=\"Residual check\"}\n"
        "Find the residual.\n"
        ":::\n\n"
        "::: hint {#hint-residual of=\"residual-problem\"}\n"
        "Use @residual-problem and compute $v-p$.\n"
        ":::\n\n"
        "::: solution {#solution-residual of=\"residual-problem\" title=\"Worked residual\"}\n"
        "$$v-p=\\begin{bmatrix}0\\\\3\\end{bmatrix}.$$\n"
        ":::\n\n"
        "::: answer {#answer-residual of=\"residual-problem\"}\n"
        "The residual is orthogonal to $u$.\n"
        ":::\n\n"
        "::: hint\n"
        "Standalone hint.\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    visible = _visible_text(html)
    numbered_index = json.loads(
        (course / "artifact" / "data" / "numbered-objects.json").read_text(
            encoding="utf-8"
        )
    )
    ids = {item["id"] for item in numbered_index["objects"]}
    assert ids == {"residual-problem"}
    assert "Hint for Problem 1" in visible
    assert "Solution of Problem 1" in visible
    assert "Worked residual" in visible
    assert "Answer to Problem 1" in visible
    assert "Hint Standalone hint." in visible
    assert 'id="raya-static-environment-hint-residual"' in html
    assert 'id="raya-static-environment-solution-residual"' in html
    assert 'id="raya-static-environment-answer-residual"' in html
    assert "raya-static-environment--hint" in html
    assert "raya-static-environment--solution" in html
    assert "raya-static-environment--answer" in html
    assert "raya-numbered-object--hint" not in html
    assert "raya-numbered-object--solution" not in html
    assert "raya-numbered-object--answer" not in html
    assert "\\begin{bmatrix}" not in visible
    assert "mjx-container" in html


def test_static_environment_rejects_unknown_target(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    page = course / "course" / "0_index.md"
    page.write_text(
        "---\nid: bad-static-target\ntitle: Bad Static Target\n---\n"
        "# Bad Static Target\n\n"
        "::: solution {of=\"missing-problem\"}\nNo target.\n:::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    diagnostic = next(
        item
        for item in report.diagnostics
        if item.message == "Unknown solution target 'missing-problem'"
    )
    assert diagnostic.field == "line:3"
    assert diagnostic.next_action == 'Use of="object-id" with an existing numbered object ID'


def test_static_environment_ids_cannot_collide_with_numbered_objects(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    page = course / "course" / "0_index.md"
    page.write_text(
        "---\nid: static-id-collision\ntitle: Static ID Collision\n---\n"
        "# Static ID Collision\n\n"
        "::: problem {#same}\nProblem.\n:::\n\n"
        "::: hint {#same}\nHint.\n:::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    diagnostic = next(
        item
        for item in report.diagnostics
        if item.message
        == "Static environment ID 'same' collides with a numbered object ID"
    )
    assert diagnostic.next_action == "Use a unique static environment ID"


def test_static_environment_rejects_duplicate_ids(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    page = course / "course" / "0_index.md"
    page.write_text(
        "---\nid: duplicate-static-id\ntitle: Duplicate Static ID\n---\n"
        "# Duplicate Static ID\n\n"
        "::: hint {#same-hint}\nFirst.\n:::\n\n"
        "::: answer {#same-hint}\nSecond.\n:::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    diagnostic = next(
        item
        for item in report.diagnostics
        if item.message == "Duplicate static environment ID 'same-hint'"
    )
    assert "first seen in" in diagnostic.next_action


def test_build_rejects_unknown_proof_target(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    page = course / "course" / "0_index.md"
    page.write_text(
        "---\n"
        "id: proof-demo\n"
        "title: Proof Demo\n"
        "summary: Proof rendering fixture.\n"
        "status: ready\n"
        "---\n\n"
        "# Proof Demo\n\n"
        "::: proof {of=\"missing-theorem\"}\n"
        "No target.\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    diagnostic = next(item for item in report.diagnostics if item.severity == "error")
    assert diagnostic.message == "Unknown proof target 'missing-theorem'"
    assert diagnostic.field == "line:4"
    assert (
        diagnostic.next_action
        == 'Use of="object-id" with an existing numbered object ID'
    )


def test_build_reports_malformed_proof_before_numbered_body_directives(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    page = course / "course" / "0_index.md"
    page.write_text(
        "---\n"
        "id: proof-demo\n"
        "title: Proof Demo\n"
        "summary: Proof rendering fixture.\n"
        "status: ready\n"
        "---\n\n"
        "# Proof Demo\n\n"
        '::: proof of="main-theorem"\n'
        "::: theorem\n"
        "This should remain proof body text for proof diagnostics.\n"
        ":::\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    diagnostic = next(item for item in report.diagnostics if item.severity == "error")
    assert diagnostic.message == "Proof directive attributes must use braces"
    assert diagnostic.field == "line:4"


def test_build_reports_malformed_numbered_object_attrs_before_body_directives(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    page = course / "course" / "0_index.md"
    page.write_text(
        "---\n"
        "id: malformed-numbered\n"
        "title: Malformed Numbered\n"
        "---\n"
        "\n"
        '::: theorem #bad-main title="Bad"\n'
        "This malformed theorem body should not hide the opener diagnostic.\n"
        "::: corollary {#not-real}\n"
        "Nested-looking content remains body text after the opener error.\n"
        ":::\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    diagnostic = next(item for item in report.diagnostics if item.severity == "error")
    assert diagnostic.message == "Numbered object directive attributes must use braces"
    assert diagnostic.path == page.resolve()
    assert diagnostic.field == "line:2"
    assert diagnostic.next_action == 'Use attributes such as {#object-id title="Optional title"}'


def test_build_rejects_duplicate_proof_ids(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    page = course / "course" / "0_index.md"
    page.write_text(
        "---\n"
        "id: proof-demo\n"
        "title: Proof Demo\n"
        "summary: Proof rendering fixture.\n"
        "status: ready\n"
        "---\n\n"
        "# Proof Demo\n\n"
        "::: proof {#same}\n"
        "First proof.\n"
        ":::\n\n"
        "::: proof {#same}\n"
        "Second proof.\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    diagnostic = next(item for item in report.diagnostics if item.severity == "error")
    assert diagnostic.message == "Duplicate proof ID 'same'"
    assert diagnostic.path == page
    assert diagnostic.field == "line:8"
    assert (
        diagnostic.next_action
        == f"Use a unique proof ID; first seen in {page} line:4"
    )


def test_shorthand_reference_escapes_configured_label_markdown(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    shutil.rmtree(course / "course" / "1_unit")
    config = course / "raya.yaml"
    config.write_text(
        config.read_text(encoding="utf-8")
        + "\n"
        "render:\n"
        "  numbered_objects:\n"
        "    sequences:\n"
        "      bracketed:\n"
        "        label: Th[e\\or]em\n"
        "        style: margin\n"
        "    families:\n"
        "      bracketed:\n"
        "        sequence: bracketed\n"
        "        label: Th[e\\or]em\n",
        encoding="utf-8",
    )
    home = course / "course" / "0_index.md"
    home.write_text(
        home.read_text(encoding="utf-8") + "\n\nUse @bracketed-result.\n",
        encoding="utf-8",
    )
    math_page = course / "course" / "1_math" / "0_index.md"
    math_page.parent.mkdir(parents=True)
    math_page.write_text(
        "---\n"
        "id: math\n"
        "title: Math\n"
        "summary: Numbered object rendering fixture.\n"
        "status: ready\n"
        "---\n"
        "# Math\n\n"
        "::: bracketed {#bracketed-result title=\"Bracketed result\"}\n"
        "Body.\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    visible = _visible_text(html)
    assert 'href="math/index.html#raya-object-bracketed-result"' in html
    assert ">Th[e\\or]em 1.1</a>" in html
    assert "Th[e\\or]em 1.1" in visible
    assert "raya:ref/bracketed-result" not in visible


def test_adjacent_numbered_objects_render_as_separate_sections(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "::: theorem {#first-adjacent title=\"First adjacent theorem\"}\n"
        "First body.\n"
        ":::\n"
        "::: theorem {#second-adjacent title=\"Second adjacent theorem\"}\n"
        "Second body.\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    assert html.count('<section id="raya-object-') == 2
    assert 'id="raya-object-first-adjacent"' in html
    assert 'id="raya-object-second-adjacent"' in html
    assert (
        html.count(
            'class="raya-numbered-object raya-numbered-object--scannable '
            'raya-numbered-object--theorem"'
        )
        == 2
    )
    assert html.count('class="raya-numbered-object-layout"') == 2
    assert html.count('class="raya-numbered-object-badge" aria-hidden="true"') == 2
    assert "RAYA_NUMBERED_OBJECT_" not in _visible_text(html)


def test_build_rejects_invalid_numbered_object_id(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "::: theorem {#bad/id}\n"
        "Invalid ID body.\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message == "Invalid numbered object ID 'bad/id'"
        and diagnostic.path == index
        and diagnostic.field == "line:7"
        and "{#pythagorean}" in (diagnostic.next_action or "")
        for diagnostic in report.diagnostics
    )
    assert not (course / "artifact" / "manifest.json").exists()


def test_build_rejects_unknown_explicit_numbered_object_reference(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "See [missing theorem](raya:ref/missing-theorem).\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message
        == "Unknown numbered object reference 'raya:ref/missing-theorem'"
        and diagnostic.path == index
        and diagnostic.field == "link:raya:ref/missing-theorem"
        for diagnostic in report.diagnostics
    )
    assert not (course / "artifact" / "manifest.json").exists()


def test_fenced_directive_text_does_not_create_numbered_object(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "```markdown\n"
        "::: theorem {#sample}\n"
        "Code sample body.\n"
        ":::\n"
        "```\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    numbered_index = json.loads(
        (course / "artifact" / "data" / "numbered-objects.json").read_text(
            encoding="utf-8"
        )
    )
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    assert "sample" not in numbered_index["by_id"]
    assert [item["id"] for item in numbered_index["objects"]] == []
    assert "::: theorem {#sample}" in _visible_text(html)
    assert "Code sample body." in _visible_text(html)
    assert 'id="raya-object-sample"' not in html
    assert "RAYA_NUMBERED_OBJECT_" not in html


def test_list_item_fenced_directive_text_does_not_create_numbered_object(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "- ```markdown\n"
        "  ::: theorem {#list-phantom}\n"
        "  Body.\n"
        "  ```\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    numbered_index = json.loads(
        (course / "artifact" / "data" / "numbered-objects.json").read_text(
            encoding="utf-8"
        )
    )
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    visible = _visible_text(html)
    assert "list-phantom" not in numbered_index["by_id"]
    assert [item["id"] for item in numbered_index["objects"]] == []
    assert "::: theorem {#list-phantom}" in visible
    assert 'id="raya-object-list-phantom"' not in html
    assert "RAYA_NUMBERED_OBJECT_" not in html


def test_fenced_directive_after_nonclosing_backticks_stays_code(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "```markdown\n"
        "```not a commonmark close\n"
        "::: theorem {#phantom}\n"
        "Body.\n"
        ":::\n"
        "```\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    numbered_index = json.loads(
        (course / "artifact" / "data" / "numbered-objects.json").read_text(
            encoding="utf-8"
        )
    )
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    visible = _visible_text(html)
    assert "phantom" not in numbered_index["by_id"]
    assert [item["id"] for item in numbered_index["objects"]] == []
    assert "```not a commonmark close" in visible
    assert "::: theorem {#phantom}" in visible
    assert "Body." in visible
    assert 'id="raya-object-phantom"' not in html
    assert "RAYA_NUMBERED_OBJECT_" not in html


def test_invalid_backtick_fence_opener_does_not_hide_numbered_directive(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "``` info `bad`\n"
        "::: theorem {#still-real title=\"Still real\"}\n"
        "Still real body.\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    numbered_index = json.loads(
        (course / "artifact" / "data" / "numbered-objects.json").read_text(
            encoding="utf-8"
        )
    )
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    assert "still-real" in numbered_index["by_id"]
    assert 'id="raya-object-still-real"' in html
    assert "Still real" in _visible_text(html)
    assert "Still real body." in _visible_text(html)


def test_authored_numbered_object_placeholder_prefix_is_rejected(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "RAYA_NUMBERED_OBJECT_0\n\n"
        "::: theorem {#real-placeholder-test}\n"
        "Real object body.\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message == "Reserved numbered object placeholder text"
        and diagnostic.path == index
        and diagnostic.field == "line:7"
        and "Remove or reword" in (diagnostic.next_action or "")
        for diagnostic in report.diagnostics
    )
    assert not (course / "artifact" / "manifest.json").exists()


def test_numbered_object_body_placeholder_prefix_is_rejected(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "::: theorem {#body-placeholder-test}\n"
        "RAYA_NUMBERED_OBJECT_0\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message == "Reserved numbered object placeholder text"
        and diagnostic.path == index
        and diagnostic.field == "line:8"
        for diagnostic in report.diagnostics
    )
    assert not (course / "artifact" / "manifest.json").exists()


def test_explicit_reference_to_fenced_directive_text_fails(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "```markdown\n"
        "::: theorem {#sample}\n"
        "Code sample body.\n"
        ":::\n"
        "```\n\n"
        "See [sample theorem](raya:ref/sample).\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message == "Unknown numbered object reference 'raya:ref/sample'"
        and diagnostic.path == index
        for diagnostic in report.diagnostics
    )
    assert not (course / "artifact" / "manifest.json").exists()


def test_build_collects_numbered_objects_from_configured_source_root(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    shutil.move(str(course / "course"), str(course / "lessons"))
    config = course / "raya.yaml"
    config.write_text(
        config.read_text(encoding="utf-8")
        .replace("course_id: minimal-course", "course_id: numbered-demo")
        .replace("source: course", "source: lessons"),
        encoding="utf-8",
    )
    parent = course / "lessons" / "2_vectors" / "0_index.md"
    parent.parent.mkdir(parents=True)
    parent.write_text(
        "---\n"
        "id: vectors\n"
        "title: Vectors\n"
        "summary: Parent fixture page.\n"
        "status: ready\n"
        "---\n"
        "# Vectors\n",
        encoding="utf-8",
    )
    page = course / "lessons" / "2_vectors" / "3_norms" / "0_index.md"
    page.parent.mkdir(parents=True)
    page.write_text(
        "---\n"
        "id: vector-norms\n"
        "title: Vector Norms\n"
        "summary: Numbered object fixture.\n"
        "status: ready\n"
        "---\n"
        "# Vector Norms\n\n"
        "::: theorem {#main}\n"
        "Main theorem body.\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    numbered_index = json.loads(
        (course / "artifact" / "data" / "numbered-objects.json").read_text(
            encoding="utf-8"
        )
    )
    first = numbered_index["objects"][0]
    assert first["source_path"] == "lessons/2_vectors/3_norms/0_index.md"
    assert first["number"] == "2.3.1"


def test_numbered_object_prefix_ignores_digit_prefixed_source_root(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    shutil.move(str(course / "course"), str(course / "2026_lessons"))
    config = course / "raya.yaml"
    config.write_text(
        config.read_text(encoding="utf-8")
        .replace("course_id: minimal-course", "course_id: numbered-demo")
        .replace("source: course", "source: 2026_lessons"),
        encoding="utf-8",
    )
    page = course / "2026_lessons" / "2_vectors" / "0_index.md"
    page.parent.mkdir(parents=True)
    page.write_text(
        "---\n"
        "id: vectors\n"
        "title: Vectors\n"
        "summary: Numbered object fixture.\n"
        "status: ready\n"
        "---\n"
        "# Vectors\n\n"
        "::: theorem {#main}\n"
        "Main theorem body.\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    numbered_index = json.loads(
        (course / "artifact" / "data" / "numbered-objects.json").read_text(
            encoding="utf-8"
        )
    )
    first = numbered_index["objects"][0]
    assert first["source_path"] == "2026_lessons/2_vectors/0_index.md"
    assert first["number"] == "2.1"


def test_build_rejects_duplicate_numbered_object_ids_across_pages(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    first = course / "course" / "1_unit" / "0_index.md"
    first.write_text(
        first.read_text(encoding="utf-8")
        + "\n\n"
        "::: theorem {#reused}\n"
        "First body.\n"
        ":::\n",
        encoding="utf-8",
    )
    second = course / "course" / "1_unit" / "1_topic" / "0_index.md"
    second.write_text(
        second.read_text(encoding="utf-8")
        + "\n\n"
        "::: exercise {#reused}\n"
        "Second body.\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message == "Duplicate numbered object ID 'reused'"
        and diagnostic.path == second
        and diagnostic.field == "line:7"
        and "line:9" in (diagnostic.next_action or "")
        and str(first) in (diagnostic.next_action or "")
        for diagnostic in report.diagnostics
    )
    assert not (course / "artifact" / "manifest.json").exists()


def test_build_rejects_unknown_numbered_object_family_without_crashing(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "::: unsupported {#mystery}\n"
        "Mystery body.\n"
        ":::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    assert any(
        diagnostic.message == "Unknown numbered object family 'unsupported'"
        and diagnostic.path == index
        for diagnostic in report.diagnostics
    )
    assert not (course / "artifact" / "manifest.json").exists()


def test_numbered_object_collection_failure_keeps_existing_artifact(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    first_report = build_course(course)
    numbered_index = course / "artifact" / "data" / "numbered-objects.json"
    old_numbered_index = numbered_index.read_text(encoding="utf-8")
    old_manifest = (course / "artifact" / "manifest.json").read_text(encoding="utf-8")
    stale = course / "artifact" / "site" / "stale-numbered-marker.html"
    stale.write_text("keep", encoding="utf-8")
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "::: theorem {#broken}\n"
        "Broken body.\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert first_report.ok, [
        diagnostic.format() for diagnostic in first_report.diagnostics
    ]
    assert not report.ok
    assert any(
        diagnostic.message == "Numbered object directive is missing a closing ::: line"
        for diagnostic in report.diagnostics
    )
    assert numbered_index.read_text(encoding="utf-8") == old_numbered_index
    assert (course / "artifact" / "manifest.json").read_text(encoding="utf-8") == old_manifest
    assert stale.read_text(encoding="utf-8") == "keep"


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


def test_render_fixture_builds_rich_static_pages(
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
    rich_css = (
        course / "artifact" / "site" / "_raya" / "render" / "rich.css"
    ).read_text(encoding="utf-8")
    site_dir = course / "artifact" / "site"
    accessibility_css = (
        site_dir / "_raya" / "render" / "accessibility" / "open-dyslexic.css"
    )
    accessibility_js = (
        site_dir
        / "_raya"
        / "render"
        / "accessibility"
        / "open-dyslexic-toggle.js"
    )
    accessibility_font = (
        site_dir
        / "_raya"
        / "render"
        / "accessibility"
        / "fonts"
        / "OpenDyslexic-Regular.woff"
    )
    assert accessibility_css.is_file()
    assert accessibility_js.is_file()
    assert accessibility_font.is_file()
    assert "OpenDyslexic" in accessibility_css.read_text(encoding="utf-8")
    assert "localStorage" in accessibility_js.read_text(encoding="utf-8")
    numbered_objects_html_path = (
        course / "artifact" / "site" / "numbered-objects" / "index.html"
    )
    assert numbered_objects_html_path.exists()
    numbered_objects_html = numbered_objects_html_path.read_text(encoding="utf-8")
    numbered_objects_visible = _visible_text(numbered_objects_html)
    reader_ux_html_path = course / "artifact" / "site" / "reader-ux" / "index.html"
    assert reader_ux_html_path.exists()
    reader_ux_html = reader_ux_html_path.read_text(encoding="utf-8")
    reader_ux_visible = _visible_text(reader_ux_html)
    authoring_matrix_html_path = (
        course / "artifact" / "site" / "authoring-matrix" / "index.html"
    )
    assert authoring_matrix_html_path.exists()
    authoring_matrix_html = authoring_matrix_html_path.read_text(encoding="utf-8")
    authoring_matrix_visible = _visible_text(authoring_matrix_html)
    math_authoring_visible = _visible_text(math_authoring_html)
    numbered_index = json.loads(
        (
            course / "artifact" / "data" / "numbered-objects.json"
        ).read_text(encoding="utf-8")
    )

    assert numbered_index["course_id"] == "render-fixture"
    assert "by_id" in numbered_index
    assert set(numbered_index["by_id"]) >= {
        "main-theorem",
        "vector-corollary",
        "basis-definition",
        "matrix-equation",
        "fixture-figure",
        "fixture-table",
        "practice-problem",
        "homework-one",
    }
    expected_numbered_ids = {
        "main-theorem",
        "vector-corollary",
        "basis-definition",
        "matrix-equation",
        "fixture-figure",
        "fixture-table",
        "practice-problem",
        "homework-one",
        "activity-one",
        "assignment-one",
        "orthogonal-definition",
        "orthogonal-proposition",
        "orthogonal-remark",
        "orthogonal-example",
        "orthogonal-equation",
        "orthogonal-figure",
        "orthogonal-table",
        "orthogonal-problem",
        "orthogonal-activity",
        "authoring-theorem",
        "authoring-equation",
        "authoring-figure",
        "authoring-table",
        "authoring-activity",
    }
    assert set(numbered_index["by_id"]) >= expected_numbered_ids
    by_id = {item["id"]: item for item in numbered_index["objects"]}
    assert by_id["activity-one"]["family"] == "activity"
    assert by_id["activity-one"]["label"] == "Activity"
    assert by_id["assignment-one"]["family"] == "assignment"
    assert by_id["assignment-one"]["label"] == "Activity"
    assert by_id["assignment-one"]["sequence"] == "assignment"
    assert by_id["assignment-one"]["style"] == "scannable"
    assert by_id["orthogonal-remark"]["family"] == "remark"
    assert by_id["orthogonal-remark"]["style"] == "scannable"
    assert by_id["orthogonal-activity"]["style"] == "scannable"
    assert by_id["orthogonal-figure"]["style"] == "caption"
    assert by_id["orthogonal-equation"]["style"] == "equation"
    assert by_id["authoring-theorem"]["href"] == (
        "authoring-matrix/#raya-object-authoring-theorem"
    )
    assert by_id["authoring-theorem"]["style"] == "scannable"
    assert by_id["authoring-equation"]["style"] == "equation"
    assert by_id["authoring-figure"]["style"] == "caption"
    assert by_id["authoring-activity"]["label"] == "Activity"
    main_theorem = numbered_index["objects"][numbered_index["by_id"]["main-theorem"]]
    assert main_theorem["href"] == "numbered-objects/#raya-object-main-theorem"
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
    assert 'href="reader-ux/index.html"' in html

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
    assert "Numbered Objects And Math Authoring" in math_authoring_visible
    assert "Macro Redefinition" in math_authoring_visible
    assert "mjx-container" in math_authoring_html
    assert "This theorem-like block is authored Markdown" in math_authoring_visible
    assert "Proof blocks are rendered statically" in math_authoring_visible
    assert "Numbered objects and references are current renderer behavior" in math_authoring_visible
    assert "@id shorthand references" in math_authoring_visible
    assert "raya:ref/id" in math_authoring_visible
    assert "numbered object fixture page" in math_authoring_visible
    assert "render-debug evidence" in math_authoring_visible.lower()
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

    assert "Theorem 3.1" in numbered_objects_visible
    assert "Corollary 3.2" in numbered_objects_visible
    assert "Definition 3.3" in numbered_objects_visible
    assert "Equation 3.1" in numbered_objects_visible
    assert "Figure 3.1" in numbered_objects_visible
    assert "Table 3.1" in numbered_objects_visible
    assert "Problem 3.1" in numbered_objects_visible
    assert "Activity 3.1" in numbered_objects_visible
    assert "Activity 3.2" in numbered_objects_visible
    assert "Activity 3.3" in numbered_objects_visible
    assert "numbered-content matrix" in numbered_objects_visible.lower()
    assert "Fixture theorem" in numbered_objects_visible
    assert "Basis" in numbered_objects_visible
    assert "Homework fixture" in numbered_objects_visible
    assert "Proof of Theorem 3.1" in numbered_objects_visible
    assert "Fixture proof" in numbered_objects_visible
    assert "Proof of Activity 3.1" in numbered_objects_visible
    assert "Proof of Activity 3.3" in numbered_objects_visible
    assert "Solution sketch" in numbered_objects_visible
    assert 'class="raya-numbered-object raya-numbered-object--scannable ' in numbered_objects_html
    assert 'class="raya-numbered-object raya-numbered-object--caption ' in numbered_objects_html
    assert 'class="raya-numbered-object raya-numbered-object--equation ' in numbered_objects_html
    assert 'class="raya-proof"' in numbered_objects_html
    assert 'id="raya-proof-proof-main"' in numbered_objects_html
    assert "raya-numbered-object-reference" in numbered_objects_html
    assert "raya-numbered-object-title" in numbered_objects_html
    assert "RAYA_PROOF_" not in numbered_objects_visible
    assert ".raya-numbered-object {\n  border: 1px solid #d8dee4;\n  margin: 1.25rem 0;\n}" in rich_css
    assert ".raya-numbered-object-body {\n  overflow-x: auto;\n  padding: 0.85rem;\n}" in rich_css
    assert ".raya-numbered-object {\n  border: 1px solid #d8dee4;\n  margin: 1.25rem 0;\n  overflow: hidden;\n}" not in rich_css
    assert (
        '<script src="../_raya/render/accessibility/open-dyslexic-toggle.js" defer></script>'
        in numbered_objects_html
    )
    assert re.search(r"<script[^>]+MathJax", numbered_objects_html) is None
    assert "\\begin{bmatrix}" not in numbered_objects_visible
    assert "mjx-container" in numbered_objects_html

    for expected_text in (
        "Reader UX Fixture",
        "Remark 4.4",
        "Example 4.1",
        "Problem 4.1",
        "Activity 4.1",
        "Proof of Proposition 4.2",
        "Solution sketch of Activity 4.1",
        "reader-facing fixture material",
    ):
        assert expected_text in reader_ux_visible
    assert "Hint for Activity 4.1" in reader_ux_visible
    assert "Solution of Activity 4.1" in reader_ux_visible
    assert "Answer to Activity 4.1" in reader_ux_visible
    assert "Standalone Hint" not in reader_ux_visible
    assert (
        "Scaling the direction vector changes the projection coefficient"
        in reader_ux_visible
    )
    assert (
        "before expanding the matrix product."
        in reader_ux_visible
    )
    assert (
        "The residual vector is orthogonal to the direction vector."
        in reader_ux_visible
    )
    assert "raya-static-environment--hint" in reader_ux_html
    assert "raya-static-environment--solution" in reader_ux_html
    assert "raya-static-environment--answer" in reader_ux_html
    assert 'class="raya-numbered-object raya-numbered-object--scannable ' in reader_ux_html
    assert 'class="raya-numbered-object raya-numbered-object--caption ' in reader_ux_html
    assert 'class="raya-numbered-object raya-numbered-object--equation ' in reader_ux_html
    assert "raya-numbered-object-badge" in reader_ux_html
    assert "mjx-container" in reader_ux_html
    assert "\\begin{bmatrix}" not in reader_ux_visible

    for expected_text in (
        "Authoring Matrix Fixture",
        "Theorem 5.1",
        "Equation 5.1",
        "Figure 5.1",
        "Table 5.1",
        "Activity 5.1",
        "Proof of Theorem 5.1",
        "Hint for Activity 5.1",
        "Solution of Activity 5.1",
        "Answer to Activity 5.1",
        "combined authoring matrix",
    ):
        assert expected_text in authoring_matrix_visible
    assert 'data-raya-skin="practice-lab"' in authoring_matrix_html
    assert 'class="raya-numbered-object raya-numbered-object--scannable ' in (
        authoring_matrix_html
    )
    assert 'class="raya-numbered-object raya-numbered-object--caption ' in (
        authoring_matrix_html
    )
    assert 'class="raya-numbered-object raya-numbered-object--equation ' in (
        authoring_matrix_html
    )
    assert "raya-static-environment--hint" in authoring_matrix_html
    assert "raya-static-environment--solution" in authoring_matrix_html
    assert "raya-static-environment--answer" in authoring_matrix_html
    assert "raya-numbered-object-reference" in authoring_matrix_html
    assert 'src="../_raya/assets/_source/_local/diagrams/static-path.svg"' in (
        authoring_matrix_html
    )
    assert "mjx-container" in authoring_matrix_html
    assert "@authoring-theorem" not in authoring_matrix_visible
    assert "\\begin{bmatrix}" not in authoring_matrix_visible
    assert "\\vect" not in authoring_matrix_visible
    assert "\\mat" not in authoring_matrix_visible
    assert "\\norm" not in authoring_matrix_visible


def test_static_build_writes_local_shell_resource(tmp_path: Path) -> None:
    from raya_static.builder import build_course

    course = _copy_minimal(tmp_path)
    report = build_course(course)
    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]

    site = course / "artifact" / "site"
    shell_js = site / "_raya" / "render" / "shell.js"
    index_html = (site / "index.html").read_text(encoding="utf-8")
    script_text = shell_js.read_text(encoding="utf-8")

    assert shell_js.exists()
    assert '<script src="_raya/render/shell.js" defer></script>' in index_html
    assert "raya.courseMapExpanded" not in script_text
    assert "localStorage" not in script_text
    assert "setExpanded(true)" in script_text
    assert "fetch(" not in script_text
    assert "XMLHttpRequest" not in script_text


def test_render_fixture_uses_static_learning_shell(tmp_path: Path) -> None:
    course = _copy_render_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "reader-ux" / "index.html").read_text(
        encoding="utf-8"
    )
    assert '<header class="raya-top-command-bar" aria-label="Course tools">' in html
    assert '<a class="raya-skip-link" href="#raya-article">Skip to content</a>' in html
    assert 'aria-label="Course tools"' in html
    assert '<nav id="raya-course-map" class="raya-course-map"' in html
    assert '<main id="raya-content" class="raya-learning-shell" data-raya-course-map="expanded">' in html
    assert '<article id="raya-article" class="raya-main-article" tabindex="-1">' in html
    assert '<aside class="raya-learning-rail" aria-label="Learning context">' in html
    assert '<section class="raya-rail-panel raya-page-summary"' in html
    assert '<section class="raya-rail-panel raya-page-status"' in html
    assert '<section class="raya-rail-panel raya-page-prerequisites"' in html
    assert '<button class="raya-rail-toggle" type="button" data-raya-rail-toggle' in html
    assert 'aria-expanded="false">Status</button>' in html
    assert html.index('<nav id="raya-course-map"') < html.index(
        '<article id="raya-article"'
    )
    assert html.index('<article id="raya-article"') < html.index(
        '<aside class="raya-learning-rail"'
    )
    assert "Prerequisites" in html
    assert "Raya Lucaria Render Fixture" in html
    assert 'href="../index.html"' in html
    root_html = (course / "artifact" / "site" / "index.html").read_text(
        encoding="utf-8"
    )
    toc = '<nav class="raya-page-toc" aria-label="Page contents">'
    assert root_html.count(toc) == 1
    assert root_html.index('<article id="raya-article"') < root_html.index(
        '<aside class="raya-learning-rail"'
    )
    assert root_html.index('<aside class="raya-learning-rail"') < root_html.index(toc)
    assert "related practice" not in _visible_text(html).lower()
    assert "personal progress" not in _visible_text(html).lower()


def test_static_builder_renders_collapsible_shell_controls_and_page_position(
    tmp_path: Path,
) -> None:
    from raya_static.builder import build_course

    course = _copy_minimal(tmp_path)
    report = build_course(course)
    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]

    site = course / "artifact" / "site"
    html = (site / "index.html").read_text(encoding="utf-8")
    middle_html = (site / "unit" / "index.html").read_text(encoding="utf-8")
    render_course = _copy_render_fixture(tmp_path)
    render_report = build_course(render_course)
    assert render_report.ok, [
        diagnostic.format() for diagnostic in render_report.diagnostics
    ]
    render_html = (render_course / "artifact" / "site" / "index.html").read_text(
        encoding="utf-8"
    )

    assert '<html lang="en" data-raya-course-map="expanded">' in html
    assert '<main id="raya-content" class="raya-learning-shell" data-raya-course-map="expanded">' in html
    assert '<nav id="raya-course-map" class="raya-course-map" aria-label="Course map" data-raya-course-map="expanded">' in html
    assert '<button class="raya-course-map-toggle"' in html
    assert "data-raya-course-map-toggle" in html
    assert 'aria-controls="raya-course-map"' in html
    assert 'aria-expanded="true">Course map</button>' in html
    assert 'aria-expanded="true">Collapse map</button>' in html
    assert 'class="raya-course-map-list" id="raya-course-map-list" aria-hidden="false"' in html
    assert 'data-raya-map-label="Raya Lucaria Render Fixture"' in render_html
    assert 'data-raya-map-index="1"' in render_html
    course_map_html = _element_html(html, '<nav id="raya-course-map"', "</nav>")
    assert 'tabindex="-1"' not in course_map_html
    assert '<p class="raya-page-position">Page 1 of 3</p>' in html
    assert '<nav class="raya-article-sequence raya-article-sequence-top"' in html
    assert 'aria-label="Previous and next pages"' in html
    assert 'rel="next" href="unit/index.html"' in html
    assert 'rel="prev" href="../index.html"' in middle_html
    assert 'rel="next" href="topic/index.html"' in middle_html
    assert html.index('<nav id="raya-course-map"') < html.index(
        '<article id="raya-article"'
    ) < html.index('<aside class="raya-learning-rail"')


def test_render_fixture_reader_page_exercises_learning_rail_metadata(
    tmp_path: Path,
) -> None:
    course = _copy_render_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    pages = json.loads(
        (course / "artifact" / "data" / "pages.json").read_text(encoding="utf-8")
    )
    reader = next(page for page in pages["pages"] if page["quantum_id"] == "reader-ux")
    assert reader["estimated_time"] == "15 minutes"
    assert reader["tags"] == ["reading", "navigation", "accessibility"]
    assert reader["prerequisites"] == ["render-root"]

    html = (course / "artifact" / "site" / "reader-ux" / "index.html").read_text(
        encoding="utf-8"
    )
    estimated_panel = _section_html(html, "raya-page-estimated-time")
    assert 'aria-expanded="false">Estimated time</button>' in estimated_panel
    assert 'aria-hidden="true" inert' in estimated_panel
    assert "15 minutes" in estimated_panel
    tags_panel = _section_html(html, "raya-page-tags")
    assert 'aria-expanded="false">Tags</button>' in tags_panel
    assert 'aria-hidden="true" inert' in tags_panel
    assert "<li>reading</li>" in tags_panel
    assert "<li>navigation</li>" in tags_panel
    assert "<li>accessibility</li>" in tags_panel


def test_rich_css_defines_learning_shell_regions(tmp_path: Path) -> None:
    course = _copy_render_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    css = (
        course / "artifact" / "site" / "_raya" / "render" / "rich.css"
    ).read_text(encoding="utf-8")
    for selector in (
        ".raya-top-command-bar",
        ".raya-learning-shell",
        ".raya-course-map",
        ".raya-main-article",
        ".raya-learning-rail",
        ".raya-rail-panel",
        ".raya-status-chip",
        ".raya-font-toggle:focus-visible",
        ".raya-course-map-toggle:focus-visible",
    ):
        assert selector in css
    assert "grid-template-columns: minmax(13.75rem, 16rem) minmax(0, 1fr) minmax(16rem, 18rem);" in css
    assert "@media (min-width: 901px)" in css
    assert "grid-template-columns: 4.25rem minmax(0, 1fr) minmax(16rem, 18rem);" in css
    assert "outline: 3px solid var(--raya-color-accent);" in css
    assert "@media (max-width: 900px)" in css


def test_learning_rail_omits_unresolved_prerequisites_without_browser_warning(
) -> None:
    page = SimpleNamespace(
        output_path="reader-ux/index.html",
        prerequisites=("render-root", "missing-page-id"),
    )
    content_model = SimpleNamespace(
        pages_by_id={
            "render-root": SimpleNamespace(
                output_path="index.html",
                nav_title="Raya Lucaria Render Fixture",
                title="Render Fixture",
            )
        }
    )

    html = static_builder._render_prerequisites_rail(page, content_model)

    assert "Raya Lucaria Render Fixture" in html
    assert 'href="../index.html"' in html
    assert "missing-page-id" not in html
    assert "unresolved prerequisite" not in _visible_text(html).lower()


def test_open_dyslexic_resource_is_packaged_and_storage_safe() -> None:
    from importlib import resources

    from raya_static.accessibility import (
        OPEN_DYSLEXIC_RESOURCE_PACKAGE,
        OPEN_DYSLEXIC_RESOURCE_PATH,
        open_dyslexic_resources,
    )

    font = resources.files(OPEN_DYSLEXIC_RESOURCE_PACKAGE).joinpath(
        OPEN_DYSLEXIC_RESOURCE_PATH
    )
    accessibility = open_dyslexic_resources()

    assert font.is_file()
    assert accessibility.source_font.is_file()
    assert font.read_bytes() == accessibility.source_font.read_bytes()
    assert '[data-raya-open-dyslexic="true"] body' in accessibility.css
    assert "try {" in accessibility.javascript
    assert "catch" in accessibility.javascript
    assert "localStorage" in accessibility.javascript
    assert "MathJax" not in accessibility.javascript
    assert "tex-chtml" not in accessibility.javascript
    assert "http://" not in accessibility.javascript
    assert "https://" not in accessibility.javascript


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


def _write_test_skin(path: Path, skin_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"id: {skin_id}\n"
        f"name: {skin_id}\n"
        "tokens:\n"
        "  color:\n"
        '    page: "#ffffff"\n'
        '    surface: "#f6f8fa"\n'
        '    text: "#1f2328"\n'
        '    muted: "#57606a"\n'
        '    accent: "#0969da"\n'
        '    accent_soft: "#ddf4ff"\n'
        '    border: "#d0d7de"\n'
        '    success: "#1a7f37"\n'
        '    warning: "#9a6700"\n'
        '    danger: "#cf222e"\n'
        "  font:\n"
        '    body: "system-ui"\n'
        '    heading: "system-ui"\n'
        '    mono: "ui-monospace"\n'
        "  density: comfortable\n",
        encoding="utf-8",
    )


def _visible_text(html_text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", html_text))


def _element_html(html_text: str, element_start: str, element_end: str) -> str:
    start = html_text.index(element_start)
    end = html_text.index(element_end, start) + len(element_end)
    return html_text[start:end]


def _section_html(html_text: str, class_name: str) -> str:
    match = re.search(
        rf'<section class="raya-rail-panel {re.escape(class_name)}"[^>]*>',
        html_text,
    )
    assert match is not None
    start = match.start()
    end = html_text.index("</section>", start) + len("</section>")
    return html_text[start:end]


class _MissingMathHtmlRenderer:
    def render_many(self, items, *, report: ValidationReport) -> MathRenderResult:
        return MathRenderResult(html_by_id={}, css="")
