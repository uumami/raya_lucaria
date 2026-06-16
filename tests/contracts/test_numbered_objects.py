from __future__ import annotations

import json
from pathlib import Path

from raya_schema.numbered_objects import (
    BUILT_IN_NUMBERED_OBJECT_FAMILIES,
    BUILT_IN_NUMBERED_OBJECT_SEQUENCES,
    NUMBERED_OBJECT_INDEX_PATH,
    NumberedObject,
    build_numbered_objects_index,
    collect_numbered_object_source_references,
    normalize_numbered_object_config,
    validate_numbered_objects_index,
)
from raya_schema.links import stable_markdown_id
from raya_schema.validation import ValidationReport
from raya_static.numbered_objects import (
    NumberedObjectRenderContext,
    NumberedObjectRenderItem,
    REFERENCE_RE,
    collect_numbered_object_sources,
    compute_numbered_objects_for_page,
    expand_shorthand_references,
    page_number_prefix_from_source_path,
    prepare_numbered_object_markdown,
    render_reference_link,
)


def test_built_in_numbered_object_defaults_group_math_and_coursework() -> None:
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["theorem"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["lemma"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["proposition"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["corollary"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["definition"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["example"]["sequence"] == "example"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["exercise"]["sequence"] == "exercise"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["problem"]["sequence"] == "exercise"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["homework"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["assignment"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["project"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["exam"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["task"]["sequence"] == "assignment"
    assert "proof" not in BUILT_IN_NUMBERED_OBJECT_FAMILIES
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["figure"]["sequence"] == "figure"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["table"]["sequence"] == "table"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["equation"]["sequence"] == "equation"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["theorem"]["style"] == "margin"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["assignment"]["style"] == "banded"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["figure"]["style"] == "caption"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["table"]["style"] == "caption"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["equation"]["style"] == "equation"
    assert NUMBERED_OBJECT_INDEX_PATH == "data/numbered-objects.json"


def test_normalize_numbered_object_config_accepts_course_overrides() -> None:
    report = ValidationReport()
    config = normalize_numbered_object_config(
        {
            "render": {
                "numbered_objects": {
                    "numbering": "page-hierarchy",
                    "sequences": {
                        "assignment": {"label": "Activity", "style": "margin"},
                        "lab": {"label": "Lab", "style": "banded"},
                    },
                    "families": {
                        "lab": {"sequence": "lab", "label": "Lab"},
                        "checkpoint": {"sequence": "exercise", "label": "Checkpoint"},
                    },
                },
            }
        },
        report=report,
        context="raya.yaml",
    )

    assert report.ok
    assert config.numbering == "page-hierarchy"
    assert config.sequences["assignment"].label == "Activity"
    assert config.sequences["assignment"].style == "margin"
    assert config.sequences["lab"].label == "Lab"
    assert config.families["lab"].sequence == "lab"
    assert config.families["checkpoint"].sequence == "exercise"


def test_normalize_numbered_object_config_accepts_positional_api() -> None:
    report = ValidationReport()

    config = normalize_numbered_object_config({}, report, "raya.yaml")

    assert report.ok
    assert config.numbering == "page-hierarchy"


def test_normalize_numbered_object_config_accepts_caption_and_equation_styles() -> None:
    report = ValidationReport()
    config = normalize_numbered_object_config(
        {
            "render": {
                "numbered_objects": {
                    "sequences": {
                        "figure": {"style": "caption"},
                        "equation": {"style": "equation"},
                    }
                }
            }
        },
        report=report,
        context="raya.yaml",
    )

    assert report.ok
    assert config.sequences["figure"].style == "caption"
    assert config.sequences["equation"].style == "equation"


def test_normalize_numbered_object_config_rejects_non_string_numbering() -> None:
    report = ValidationReport()

    normalize_numbered_object_config(
        {"render": {"numbered_objects": {"numbering": []}}},
        report=report,
        context="raya.yaml",
    )

    assert not report.ok
    assert any("numbering" in issue.message for issue in report.issues)


def test_normalize_numbered_object_config_rejects_non_string_style() -> None:
    report = ValidationReport()

    normalize_numbered_object_config(
        {"render": {"numbered_objects": {"sequences": {"figure": {"style": []}}}}},
        report=report,
        context="raya.yaml",
    )

    assert not report.ok
    assert any("style" in issue.message for issue in report.issues)


def test_normalize_numbered_object_config_rejects_unknown_sequence_reference() -> None:
    report = ValidationReport()

    normalize_numbered_object_config(
        {"render": {"numbered_objects": {"families": {"claim": {"sequence": "claims"}}}}},
        report=report,
        context="raya.yaml",
    )

    assert not report.ok
    assert any("claims" in issue.message and "claim" in issue.message for issue in report.issues)


def test_prepare_numbered_object_markdown_extracts_directive_source() -> None:
    report = ValidationReport()
    source_path = Path("course/2_vectors/3_norms.md")
    body = """# Norms

Intro text.

::: theorem {#pythagorean title="Pythagorean theorem"}
For a right triangle,

$$a^2 + b^2 = c^2$$
:::

After text.
"""

    prepared = prepare_numbered_object_markdown(
        body,
        report=report,
        source_path=source_path,
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert "RAYA_NUMBERED_OBJECT_0" in prepared.body
    assert "::: theorem" not in prepared.body
    assert len(prepared.sources) == 1
    source = prepared.sources[0]
    assert source.placeholder == "RAYA_NUMBERED_OBJECT_0"
    assert source.id == "pythagorean"
    assert source.family == "theorem"
    assert source.title == "Pythagorean theorem"
    assert source.body == "For a right triangle,\n\n$$a^2 + b^2 = c^2$$"
    assert source.source_path == source_path
    assert source.start_line == 5


def test_prepare_numbered_object_markdown_preserves_indented_body_lines() -> None:
    report = ValidationReport()
    prepared = prepare_numbered_object_markdown(
        """::: example {#code}
    x = 1
    print(x)
:::
""",
        report=report,
        source_path=Path("course/2_vectors/3_norms.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert prepared.sources[0].body == "    x = 1\n    print(x)"


def test_prepare_numbered_object_markdown_accepts_indented_directive_fences() -> None:
    report = ValidationReport()
    prepared = prepare_numbered_object_markdown(
        """   ::: theorem {#indented}
Body.
   :::
""",
        report=report,
        source_path=Path("course/2_vectors/3_norms.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert prepared.body == "\nRAYA_NUMBERED_OBJECT_0\n\n"
    assert prepared.sources[0].id == "indented"


def test_collect_numbered_object_source_references_ignores_fenced_directive_text() -> None:
    references = collect_numbered_object_source_references(
        "\n".join(
            [
                "```markdown",
                "::: theorem {#simple}",
                "Simple code sample.",
                "```",
                "",
                "- ```markdown",
                "  ::: theorem {#list}",
                "  List code sample.",
                "  ```",
                "",
                "> ```markdown",
                "> ::: theorem {#quote}",
                "> Quote code sample.",
                "> ```",
                "",
                "::: theorem {#real}",
                "Real body.",
                ":::",
            ]
        ),
        source_path=Path("course/0_index.md"),
    )

    assert [reference.id for reference in references] == ["real"]


def test_page_number_prefix_from_source_path_uses_ordered_path_parts() -> None:
    assert (
        page_number_prefix_from_source_path("course/2_vectors/3_norms/0_index.md")
        == "2.3"
    )
    assert (
        page_number_prefix_from_source_path("lessons/02_vectors/003_norms/index.md")
        == "2.3"
    )
    assert (
        page_number_prefix_from_source_path("course/A_reference/1_topic/0_index.md")
        == "A.1"
    )
    assert (
        page_number_prefix_from_source_path("course/A_reference/1_formula_sheet.md")
        == "A.1"
    )


def test_reference_re_matches_shorthand_object_references() -> None:
    assert REFERENCE_RE.search("@pythagorean").group("object_id") == "pythagorean"
    assert REFERENCE_RE.search("@main-theorem").group("object_id") == "main-theorem"
    assert REFERENCE_RE.search(r"\@pythagorean") is None
    assert REFERENCE_RE.search("teacher@example.com") is None


def test_render_reference_link_escapes_href_and_text() -> None:
    html = render_reference_link(
        "pythagorean",
        'Theorem <2.3.1> "quoted"',
        'chapter/?x="bad"&next=<tag>',
    )

    assert 'data-object-id="pythagorean"' in html
    assert 'href="chapter/?x=&quot;bad&quot;&amp;next=&lt;tag&gt;"' in html
    assert "Theorem &lt;2.3.1&gt; &quot;quoted&quot;" in html


def test_expand_shorthand_references_uses_reference_text_and_reports_unknowns() -> None:
    report = ValidationReport()
    source_path = Path("course/0_index.md")
    object_source = collect_numbered_object_sources(
        "::: theorem {#pythagorean}\nBody.\n:::\n",
        report=report,
        source_path=Path("course/1_math/0_index.md"),
    )[0]
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title="Pythagorean theorem",
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[NumberedObjectRenderItem(source=object_source, object=obj)],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        "Use @pythagorean and @missing.",
        context=context,
        report=report,
        source_path=source_path,
    )

    assert "[Theorem 1.1](raya:ref/pythagorean)" in expanded
    assert "@missing" in expanded
    assert not report.ok
    assert any(
        diagnostic.message == "Unknown numbered object reference '@missing'"
        and diagnostic.path == source_path
        for diagnostic in report.diagnostics
    )


def test_expand_shorthand_references_skips_code_spans_fences_and_urlish_text() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        "\n".join(
            [
                "Use @pythagorean.",
                "Keep `@pythagorean` literal.",
                "Keep https://example.test/@pythagorean literal.",
                "```",
                "@pythagorean",
                "```",
            ]
        ),
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert expanded.count("[Theorem 1.1](raya:ref/pythagorean)") == 1
    assert "`@pythagorean`" in expanded
    assert "https://example.test/@pythagorean" in expanded
    assert "```\n@pythagorean\n```" in expanded


def test_expand_shorthand_references_skips_existing_link_and_image_syntax() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        "\n".join(
            [
                "[see @pythagorean](other.md)",
                "[see [nested @pythagorean]](other.md)",
                "[see](raya:@pythagorean)",
                "[see @pythagorean][label]",
                "![alt @pythagorean](image.png)",
                "![alt [nested @pythagorean]](image.png)",
                "[see @missing]()",
                "![alt @missing]()",
                '[link](dest(and) "title @pythagorean")',
                '[link](dest(and) "title @missing")',
                '[link](<dest(and)> "title @pythagorean")',
                "[explicit](raya:ref/pythagorean)",
                "Use @pythagorean.",
            ]
        ),
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert "[see @pythagorean](other.md)" in expanded
    assert "[see [nested @pythagorean]](other.md)" in expanded
    assert "[see](raya:@pythagorean)" in expanded
    assert "[see @pythagorean][label]" in expanded
    assert "![alt @pythagorean](image.png)" in expanded
    assert "![alt [nested @pythagorean]](image.png)" in expanded
    assert "[see @missing]()" in expanded
    assert "![alt @missing]()" in expanded
    assert '[link](dest(and) "title @pythagorean")' in expanded
    assert '[link](dest(and) "title @missing")' in expanded
    assert '[link](<dest(and)> "title @pythagorean")' in expanded
    assert "[explicit](raya:ref/pythagorean)" in expanded
    assert expanded.count("[Theorem 1.1](raya:ref/pythagorean)") == 1


def test_expand_shorthand_references_skips_bare_urlish_parenthesized_text() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        "Keep https://example.test/path(@pythagorean) literal.\nUse @pythagorean.",
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert "https://example.test/path(@pythagorean)" in expanded
    assert expanded.count("[Theorem 1.1](raya:ref/pythagorean)") == 1


def test_expand_shorthand_references_skips_known_shortcut_reference_label() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="known",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-known",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"known": obj},
    )

    expanded = expand_shorthand_references(
        "[label @known]: https://example.test\n\nUse [label @known].\nUse @known.",
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert "[label @known]: https://example.test" in expanded
    assert "Use [label @known]." in expanded
    assert expanded.count("[Theorem 1.1](raya:ref/known)") == 1


def test_expand_shorthand_references_skips_unknown_object_inside_shortcut_reference_label() -> None:
    report = ValidationReport()
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={},
    )

    expanded = expand_shorthand_references(
        "[label @missing]: https://example.test\n\nUse [label @missing].",
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert "[label @missing]: https://example.test" in expanded
    assert "Use [label @missing]." in expanded


def test_expand_shorthand_references_ignores_pseudo_reference_definitions_in_code_and_math() -> None:
    report = ValidationReport()
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={},
    )

    expanded = expand_shorthand_references(
        "\n".join(
            [
                "```",
                "[fenced @missing]: https://example.test",
                "```",
                "$$",
                "[math @missing]: https://example.test",
                "$$",
                "    [code @missing]: https://example.test",
                "",
                "Use [fenced @missing].",
                "Use [math @missing].",
                "Use [code @missing].",
            ]
        ),
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert not report.ok
    messages = [diagnostic.message for diagnostic in report.diagnostics]
    assert messages == [
        "Unknown numbered object reference '@missing'",
        "Unknown numbered object reference '@missing'",
        "Unknown numbered object reference '@missing'",
    ]
    assert "Use [fenced @missing]." in expanded
    assert "Use [math @missing]." in expanded
    assert "Use [code @missing]." in expanded


def test_expand_shorthand_references_does_not_shield_malformed_reference_definition() -> None:
    report = ValidationReport()
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={},
    )

    expanded = expand_shorthand_references(
        "[label @missing]: <unterminated\n\nUse [label @missing].",
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert not report.ok
    messages = [diagnostic.message for diagnostic in report.diagnostics]
    assert messages == [
        "Unknown numbered object reference '@missing'",
        "Unknown numbered object reference '@missing'",
    ]
    assert "[label @missing]: <unterminated" in expanded
    assert "Use [label @missing]." in expanded


def test_expand_shorthand_references_does_not_shield_malformed_inline_link() -> None:
    report = ValidationReport()
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={},
    )

    expanded = expand_shorthand_references(
        "[see @missing](bad dest)",
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert not report.ok
    messages = [diagnostic.message for diagnostic in report.diagnostics]
    assert messages == ["Unknown numbered object reference '@missing'"]
    assert "[see @missing](bad dest)" in expanded


def test_expand_shorthand_references_skips_reference_definition_labels() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        "[see @pythagorean]: other.md\nUse [text][see @pythagorean].\nUse @pythagorean.",
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert "[see @pythagorean]: other.md" in expanded
    assert "Use [text][see @pythagorean]." in expanded
    assert expanded.count("[Theorem 1.1](raya:ref/pythagorean)") == 1


def test_expand_shorthand_references_skips_reference_definition_titles() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        '[label]: other.md "see @pythagorean"\nUse @pythagorean.',
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert '[label]: other.md "see @pythagorean"' in expanded
    assert expanded.count("[Theorem 1.1](raya:ref/pythagorean)") == 1


def test_expand_shorthand_references_allows_footnote_definition_body() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        "[^n]: See @pythagorean.",
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert "[^n]: See [Theorem 1.1](raya:ref/pythagorean)." in expanded


def test_expand_shorthand_references_skips_reference_definition_title_continuation() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        '[label]: other.md\n  "see @pythagorean"\nUse @pythagorean.',
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert '[label]: other.md\n  "see @pythagorean"' in expanded
    assert expanded.count("[Theorem 1.1](raya:ref/pythagorean)") == 1


def test_expand_shorthand_references_skips_unindented_reference_definition_title_continuation() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        '[label]: other.md\n"see @pythagorean"\nUse @pythagorean.',
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert '[label]: other.md\n"see @pythagorean"' in expanded
    assert expanded.count("[Theorem 1.1](raya:ref/pythagorean)") == 1


def test_expand_shorthand_references_only_skips_one_reference_definition_title_continuation() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        '[label]: other.md\n  "title @missing"\n  "visible @pythagorean"\nUse [label].',
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert '  "title @missing"' in expanded
    assert '  "visible [Theorem 1.1](raya:ref/pythagorean)"' in expanded


def test_expand_shorthand_references_inline_reference_title_does_not_shield_following_paragraph() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        '[label]: other.md "title"\n  "visible @pythagorean"',
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert '  "visible [Theorem 1.1](raya:ref/pythagorean)"' in expanded


def test_expand_shorthand_references_expands_visible_quoted_paragraph_after_reference_definition() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        '[label]: other.md "title"\n"visible @pythagorean"',
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert '"visible [Theorem 1.1](raya:ref/pythagorean)"' in expanded


def test_expand_shorthand_references_expands_paragraph_after_reference_definition() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        "[label]: other.md\n  See @pythagorean\nUse [x][label].",
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert "[label]: other.md" in expanded
    assert "  See [Theorem 1.1](raya:ref/pythagorean)" in expanded
    assert "Use [x][label]." in expanded


def test_expand_shorthand_references_skips_blockquoted_fenced_code() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        "\n".join(
            [
                "> [!NOTE]",
                "> ```",
                "> @pythagorean",
                "> ```",
                "",
                "Use @pythagorean.",
            ]
        ),
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert "> @pythagorean" in expanded
    assert "> [Theorem 1.1](raya:ref/pythagorean)" not in expanded
    assert "Use [Theorem 1.1](raya:ref/pythagorean)." in expanded


def test_expand_shorthand_references_skips_list_item_fenced_code() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        "- ```markdown\n  @pythagorean\n  ```\nUse @pythagorean.",
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert "  @pythagorean" in expanded
    assert expanded.count("[Theorem 1.1](raya:ref/pythagorean)") == 1


def test_expand_shorthand_references_skips_nested_list_item_fenced_code() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        "  - ```\n    @pythagorean\n    ```\nUse @pythagorean.",
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert "    @pythagorean" in expanded
    assert expanded.count("[Theorem 1.1](raya:ref/pythagorean)") == 1


def test_expand_shorthand_references_skips_list_item_display_math() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        "- $$\n  @pythagorean\n  @missing\n  $$\nUse @pythagorean.",
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert "  @pythagorean" in expanded
    assert "  @missing" in expanded
    assert expanded.count("[Theorem 1.1](raya:ref/pythagorean)") == 1


def test_expand_shorthand_references_skips_math_spans_and_blocks() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        "\n".join(
            [
                "Inline known $@pythagorean$ stays math.",
                "Inline missing $@missing$ stays math.",
                "$$",
                "@pythagorean",
                "$$",
                "Use @pythagorean.",
            ]
        ),
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert "$@pythagorean$" in expanded
    assert "$@missing$" in expanded
    assert "$$\n@pythagorean\n$$" in expanded
    assert expanded.count("[Theorem 1.1](raya:ref/pythagorean)") == 1
    assert "@missing" in expanded


def test_expand_shorthand_references_skips_indented_code() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        "    @missing\nUse @pythagorean.",
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert "    @missing" in expanded
    assert "[Theorem 1.1](raya:ref/pythagorean)" in expanded


def test_expand_shorthand_references_skips_blockquoted_indented_code() -> None:
    report = ValidationReport()
    obj = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="1.1",
        title=None,
        source_path="course/1_math/0_index.md",
        page_id="math",
        page_title="Math",
        page_output_path="1_math/index.html",
        href="1_math/#raya-object-pythagorean",
        style="margin",
    )
    context = NumberedObjectRenderContext(
        items=[],
        objects_by_id={"pythagorean": obj},
    )

    expanded = expand_shorthand_references(
        ">     @pythagorean\nUse @pythagorean.",
        context=context,
        report=report,
        source_path=Path("course/0_index.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert ">     @pythagorean" in expanded
    assert expanded.count("[Theorem 1.1](raya:ref/pythagorean)") == 1


def test_stable_markdown_id_keeps_ref_namespace() -> None:
    assert stable_markdown_id("raya:ref/abc") == "ref/abc"


def test_collect_numbered_object_sources_returns_prepared_sources() -> None:
    report = ValidationReport()
    body = """::: exercise {#practice}
Compute the norm.
:::
"""

    sources = collect_numbered_object_sources(
        body,
        report=report,
        source_path=Path("course/2_vectors/3_norms.md"),
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert [source.id for source in sources] == ["practice"]


def test_prepare_numbered_object_markdown_rejects_nested_numbered_directives() -> None:
    report = ValidationReport()
    body = """::: theorem {#outer}
Outer body.

::: corollary {#inner}
Inner body.
:::

:::
"""

    prepare_numbered_object_markdown(
        body,
        report=report,
        source_path=Path("course/2_vectors/3_norms.md"),
    )

    assert not report.ok
    assert any("nested numbered object" in issue.message for issue in report.issues)


def test_compute_numbered_objects_for_page_uses_page_prefix_and_shared_sequences() -> None:
    report = ValidationReport()
    config = normalize_numbered_object_config({}, report, "raya.yaml")
    prepared = prepare_numbered_object_markdown(
        """::: theorem {#pythagorean title="Pythagorean theorem"}
Body.
:::

::: corollary {#reverse}
Reverse body.
:::

::: exercise {#practice}
Practice body.
:::
""",
        report=report,
        source_path=Path("course/2_vectors/3_norms.md"),
    )

    objects = compute_numbered_objects_for_page(
        prepared.sources,
        config=config,
        course_relative_source_path="course/2_vectors/3_norms.md",
        page_id="norms",
        page_title="Norms",
        page_output_path="2_vectors/3_norms/index.html",
        page_number_prefix="2.3",
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert [item.family for item in objects] == ["theorem", "corollary", "exercise"]
    assert [item.sequence for item in objects] == ["theorem", "theorem", "exercise"]
    assert [item.number for item in objects] == ["2.3.1", "2.3.2", "2.3.1"]
    assert [item.href for item in objects] == [
        "2_vectors/3_norms/#raya-object-pythagorean",
        "2_vectors/3_norms/#raya-object-reverse",
        "2_vectors/3_norms/#raya-object-practice",
    ]


def test_numbered_object_serializes_anchor_in_json_entry() -> None:
    item = NumberedObject(
        id="pythagorean",
        family="theorem",
        sequence="theorem",
        label="Theorem",
        number="2.3.1",
        title="Pythagorean theorem",
        source_path="course/2_vectors/3_norms.md",
        page_id="norms",
        page_title="Norms",
        page_output_path="2_vectors/3_norms/index.html",
        href="2_vectors/3_norms/#raya-object-pythagorean",
        style="margin",
    )

    entry = item.to_json()

    assert entry["anchor"] == "raya-object-pythagorean"
    assert entry["reference_text"] == "Theorem 2.3.1"


def test_numbered_objects_index_validation_requires_stable_shape(tmp_path) -> None:
    index = build_numbered_objects_index(
        course_id="demo",
        objects=[
            NumberedObject(
                id="pythagorean",
                family="theorem",
                sequence="theorem",
                label="Theorem",
                number="2.3.1",
                title="Pythagorean theorem",
                source_path="course/2_vectors/3_norms.md",
                page_id="norms",
                page_title="Norms",
                page_output_path="2_vectors/3_norms/index.html",
                href="2_vectors/3_norms/#raya-object-pythagorean",
                style="margin",
            )
        ],
    )
    path = tmp_path / "numbered-objects.json"
    path.write_text(json.dumps(index), encoding="utf-8")

    report = validate_numbered_objects_index(path)

    assert report.ok
    assert index["objects"][0]["reference_text"] == "Theorem 2.3.1"
    assert index["objects"][0]["anchor"] == "raya-object-pythagorean"
    assert index["by_id"]["pythagorean"] == 0


def test_numbered_objects_index_validation_allows_untitled_objects(tmp_path) -> None:
    index = build_numbered_objects_index(
        "demo",
        [
            NumberedObject(
                id="untitled-theorem",
                family="theorem",
                sequence="theorem",
                label="Theorem",
                number="1.1",
                title="",
                source_path="course/1_intro/0_index.md",
                page_id="intro",
                page_title="Intro",
                page_output_path="1_intro/index.html",
                href="1_intro/#raya-object-untitled-theorem",
                style="margin",
            )
        ],
    )
    index["objects"][0]["title"] = None
    path = tmp_path / "numbered-objects-null-title.json"
    path.write_text(json.dumps(index), encoding="utf-8")

    null_report = validate_numbered_objects_index(path)

    assert null_report.ok

    del index["objects"][0]["title"]
    path = tmp_path / "numbered-objects-missing-title.json"
    path.write_text(json.dumps(index), encoding="utf-8")

    missing_report = validate_numbered_objects_index(path)

    assert missing_report.ok


def test_numbered_objects_index_validation_rejects_non_string_title(tmp_path) -> None:
    index = build_numbered_objects_index(
        "demo",
        [
            NumberedObject(
                id="bad-title",
                family="theorem",
                sequence="theorem",
                label="Theorem",
                number="1.1",
                title=None,
                source_path="course/1_intro/0_index.md",
                page_id="intro",
                page_title="Intro",
                page_output_path="1_intro/index.html",
                href="1_intro/#raya-object-bad-title",
                style="margin",
            )
        ],
    )
    index["objects"][0]["title"] = []
    path = tmp_path / "numbered-objects-bad-title.json"
    path.write_text(json.dumps(index), encoding="utf-8")

    report = validate_numbered_objects_index(path)

    assert not report.ok
    assert any("title" in issue.message for issue in report.issues)


def test_numbered_objects_index_validation_rejects_href_anchor_mismatch(tmp_path) -> None:
    index = build_numbered_objects_index(
        "demo",
        [
            NumberedObject(
                id="bad-href",
                family="theorem",
                sequence="theorem",
                label="Theorem",
                number="1.1",
                title=None,
                source_path="course/1_intro/0_index.md",
                page_id="intro",
                page_title="Intro",
                page_output_path="1_intro/index.html",
                href="1_intro/#raya-object-bad-href",
                style="margin",
            )
        ],
    )
    index["objects"][0]["href"] = "1_intro/#wrong-target"
    path = tmp_path / "numbered-objects-bad-href.json"
    path.write_text(json.dumps(index), encoding="utf-8")

    report = validate_numbered_objects_index(path)

    assert not report.ok
    assert any("href" in issue.message and "anchor" in issue.message for issue in report.issues)


def test_build_numbered_objects_index_accepts_positional_api() -> None:
    index = build_numbered_objects_index("demo", [])

    assert index["course_id"] == "demo"
    assert index["objects"] == []
    assert index["by_id"] == {}


def test_numbered_objects_index_validation_accepts_all_supported_styles(tmp_path) -> None:
    objects = []
    for style in ("margin", "banded", "caption", "equation"):
        objects.append(
            NumberedObject(
                id=f"{style}-item",
                family="example",
                sequence="example",
                label="Example",
                number=f"1.{len(objects) + 1}",
                title=f"{style.title()} item",
                source_path="course/1_intro/0_index.md",
                page_id="intro",
                page_title="Intro",
                page_output_path="1_intro/index.html",
                href=f"1_intro/#raya-object-{style}-item",
                style=style,
            )
        )
    index = build_numbered_objects_index("demo", objects)
    path = tmp_path / "numbered-objects.json"
    path.write_text(json.dumps(index), encoding="utf-8")

    report = validate_numbered_objects_index(path)

    assert report.ok


def test_numbered_objects_index_validation_rejects_stale_by_id_keys(tmp_path) -> None:
    index = build_numbered_objects_index("demo", [])
    index["by_id"]["stale"] = 0
    path = tmp_path / "numbered-objects.json"
    path.write_text(json.dumps(index), encoding="utf-8")

    report = validate_numbered_objects_index(path)

    assert not report.ok
    assert any("stale" in issue.message for issue in report.issues)


def test_numbered_objects_index_validation_rejects_non_integer_by_id_values(tmp_path) -> None:
    for value in (False, 0.0):
        index = build_numbered_objects_index(
            "demo",
            [
                NumberedObject(
                    id="pythagorean",
                    family="theorem",
                    sequence="theorem",
                    label="Theorem",
                    number="2.3.1",
                    title="Pythagorean theorem",
                    source_path="course/2_vectors/3_norms.md",
                    page_id="norms",
                    page_title="Norms",
                    page_output_path="2_vectors/3_norms/index.html",
                    href="2_vectors/3_norms/#raya-object-pythagorean",
                    style="margin",
                )
            ],
        )
        index["by_id"]["pythagorean"] = value
        path = tmp_path / f"numbered-objects-by-id-{type(value).__name__}.json"
        path.write_text(json.dumps(index), encoding="utf-8")

        report = validate_numbered_objects_index(path)

        assert not report.ok
        assert any("by_id" in issue.message for issue in report.issues)
