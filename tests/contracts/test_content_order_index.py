from __future__ import annotations

import json
import shutil
from pathlib import Path

from raya_schema import validate_course
from raya_static import build_course


ROOT = Path(__file__).resolve().parents[2]
ORDERED = ROOT / "examples" / "courses" / "ordered-fixture"
INVALID = ROOT / "examples" / "courses" / "invalid"


def test_ordered_fixture_validates_with_metadata_and_stable_links() -> None:
    report = validate_course(ORDERED)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert (
        ORDERED / "course" / "1_foundations" / "2_derivatives" / "0_index.md"
        in report.files_read
    )


def test_invalid_ordered_fixtures_fail_with_expected_diagnostics() -> None:
    expected = {
        "broken-raya-link": "Broken stable content reference",
        "course-level-official-missing-scope": "requires scope.quantum",
        "duplicate-alias": "Duplicate page alias",
        "duplicate-clean-slug": "Duplicate clean slug",
        "duplicate-id": "Duplicate quantum ID",
        "duplicate-official-id": "Duplicate official learning object ID",
        "duplicate-order": "Duplicate normalized order",
        "invalid-support-link": "non-asset support material",
        "missing-colocated-asset": "Missing local asset reference",
        "missing-section-index": "Rendered section directory is missing an index page",
        "missing-source-root": "authored source directory is missing",
        "official-scope-mismatch": "scope does not match nearest quantum",
        "mixed-prefix-widths": "Mixed ordered prefix widths",
        "unordered-official-object": "Unordered official learning object file",
        "unsupported-content-field": "Unsupported course configuration field",
        "unordered-file": "Unordered published content file",
    }

    for fixture, message in expected.items():
        report = validate_course(INVALID / fixture)
        assert not report.ok, fixture
        assert any(message in item.message for item in report.diagnostics), [
            diagnostic.format() for diagnostic in report.diagnostics
        ]


def test_path_link_guidance_is_non_failing(tmp_path: Path) -> None:
    course = tmp_path / "course"
    shutil.copytree(ORDERED, course, ignore=shutil.ignore_patterns("artifact"))
    root = course / "course" / "0_index.md"
    root.write_text(
        root.read_text(encoding="utf-8")
        + "\nPath link to [limits](1_foundations/1_limits/0_index.md).\n",
        encoding="utf-8",
    )

    report = validate_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert any("raya: alternative" in item.message for item in report.diagnostics)


def test_ordered_artifact_data_preserves_navigation_indices_and_links(
    tmp_path: Path,
) -> None:
    course = tmp_path / "ordered-fixture"
    shutil.copytree(ORDERED, course, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    artifact = course / "artifact"
    manifest = json.loads((artifact / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["data"]["navigation"] == "data/navigation.json"
    assert manifest["data"]["indices"] == "data/indices.json"

    pages = json.loads((artifact / "data" / "pages.json").read_text(encoding="utf-8"))
    derivatives = next(item for item in pages["pages"] if item["quantum_id"] == "derivatives-rates")
    assert derivatives["url"] == "foundations/derivatives/index.html"
    assert derivatives["aliases"] == ["old-derivatives"]
    assert derivatives["prerequisites"] == ["limits-intuition"]

    links = json.loads((artifact / "data" / "links.json").read_text(encoding="utf-8"))
    assert {
        "from": "optimization-practice",
        "to": "derivatives-rates",
        "kind": "content",
    } in links["links"]

    navigation = json.loads(
        (artifact / "data" / "navigation.json").read_text(encoding="utf-8")
    )
    nav_item = next(item for item in navigation["items"] if item["id"] == "derivatives-rates")
    assert nav_item["parent"] == "foundations"
    assert nav_item["previous"] == "limits-intuition"
    assert nav_item["next"] == "practice"
    appendix_item = next(item for item in navigation["items"] if item["id"] == "reference")
    assert appendix_item["hierarchy_key"] == "appendix"
    assert appendix_item["hierarchy_label"] == "Anexo"

    indices = json.loads((artifact / "data" / "indices.json").read_text(encoding="utf-8"))
    master_titles = [item["title"] for item in indices["master"]]
    assert master_titles == ["Foundations", "Practice", "Reference"]
    appendix_entry = next(item for item in indices["master"] if item["id"] == "reference")
    assert appendix_entry["hierarchy_label"] == "Anexo"
    foundations = next(item for item in indices["local"] if item["id"] == "foundations")
    assert [entry["id"] for entry in foundations["entries"]] == [
        "limits-intuition",
        "derivatives-rates",
    ]
    assert foundations["study_counts"] == {"card": 1, "prompt": 1}
