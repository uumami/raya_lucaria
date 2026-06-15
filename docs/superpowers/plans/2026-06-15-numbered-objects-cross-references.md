# Numbered Objects Cross-References Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add course-configurable numbered content objects and cross-references for theorem-like blocks, figures, tables, equations, exercises, homework, assignments, projects, exams, and custom course families.

**Architecture:** The schema package owns the course config model, built-in families/sequences, and artifact index validation. The static package owns Markdown directive extraction, course-global numbering, `@label` reference expansion, `raya:ref/<id>` link resolution, HTML rendering, CSS, and artifact/index emission. Role docs and render fixtures demonstrate authoring and browser-debuggable output in English and Spanish.

**Tech Stack:** Python 3.10, `uv`, `pytest`, `markdown-it-py`, existing Raya schema/static packages, local Chromium e2e tests, Docker reference verification.

---

## File Structure

- Create `packages/schema/src/raya_schema/numbered_objects.py`: built-in numbered-object defaults, config normalization, index construction, and index validation.
- Modify `packages/schema/src/raya_schema/__init__.py`: export numbered-object helpers used by static and artifact validation tests.
- Modify `packages/schema/src/raya_schema/artifacts.py`: validate manifest-declared `data/numbered-objects.json`.
- Modify `packages/schema/src/raya_schema/links.py`: classify `raya:ref/<object-id>` as a stable numbered-object reference without weakening existing `raya:<page-id>` links.
- Create `packages/static/src/raya_static/numbered_objects.py`: parse `:::` directive blocks, collect objects by page, compute numbers from page hierarchy labels, expand references, and render numbered-object HTML fragments.
- Modify `packages/static/src/raya_static/rendering.py`: accept a numbered-object render context, include object fragments in math rendering, emit local links, and add CSS for `margin`, `banded`, `caption`, and `equation` styles.
- Modify `packages/static/src/raya_static/builder.py`: load config, collect objects before rendering pages, pass render context, write `data/numbered-objects.json`, add manifest data path, and resolve `raya:ref/<id>` links.
- Modify `packages/static/src/raya_static/render_debug.py`: include numbered object pages in debug/inspection pages when the fixture exists.
- Modify `examples/courses/render-fixture/raya.yaml`: add a visible course-level `render.numbered_objects` config using the default margin theorem-like style and one explicit assignment override.
- Create `examples/courses/render-fixture/course/3_numbered_objects/0_index.md`: fixture content for theorem, corollary, definition, equation, figure, table, exercise, homework, and references.
- Modify `examples/courses/render-fixture/course/0_index.md`: link to the numbered objects fixture.
- Modify `docs/foundation/05_course_contract.md`, `docs/foundation/06_artifact_contract.md`, `docs/foundation/13_truth_surfaces.md`, `docs/foundation/17_rendering_execution_plan.md`: make the new config, source syntax, artifact surface, and debugging responsibility canonical.
- Modify role docs:
  - `docs/guides/en/professors/index.md`
  - `docs/guides/en/students/index.md`
  - `docs/guides/en/contributors/index.md`
  - `docs/guides/en/agents/index.md`
  - `docs/guides/es/profesores/index.md`
  - `docs/guides/es/estudiantes/index.md`
  - `docs/guides/es/colaboradores/index.md`
  - `docs/guides/es/agentes/index.md`
- Create `tests/contracts/test_numbered_objects.py`: schema/config/source/render contract tests.
- Modify `tests/contracts/test_static_builder.py`: artifact/build integration assertions.
- Modify `tests/contracts/test_artifact_validation.py`: manifest/index validation coverage.
- Modify `tests/contracts/test_renderer_dependencies.py`: role-doc and no-CDN/no-browser-MathJax expectations.
- Modify `tests/e2e/test_preview_static_read_path.py`: browser/static-read-path checks for numbered object HTML, refs, screenshot/inspection parity, and no external renderer requests.

---

### Task 1: Add Schema Defaults And Index Validation

**Files:**
- Create: `packages/schema/src/raya_schema/numbered_objects.py`
- Modify: `packages/schema/src/raya_schema/__init__.py`
- Test: `tests/contracts/test_numbered_objects.py`

- [ ] **Step 1: Write failing schema/config tests**

Add `tests/contracts/test_numbered_objects.py`:

```python
from __future__ import annotations

import json

from raya_schema.numbered_objects import (
    BUILT_IN_NUMBERED_OBJECT_FAMILIES,
    BUILT_IN_NUMBERED_OBJECT_SEQUENCES,
    NumberedObject,
    build_numbered_objects_index,
    normalize_numbered_object_config,
    validate_numbered_objects_index,
)
from raya_schema.validation import ValidationReport


def test_built_in_numbered_object_defaults_group_math_and_coursework() -> None:
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["theorem"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["lemma"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["corollary"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["definition"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["example"]["sequence"] == "example"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["exercise"]["sequence"] == "exercise"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["problem"]["sequence"] == "exercise"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["homework"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["assignment"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["project"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["exam"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["figure"]["sequence"] == "figure"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["table"]["sequence"] == "table"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["equation"]["sequence"] == "equation"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["theorem"]["style"] == "margin"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["assignment"]["style"] == "banded"


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


def test_normalize_numbered_object_config_rejects_unknown_sequence_reference() -> None:
    report = ValidationReport()

    normalize_numbered_object_config(
        {"render": {"numbered_objects": {"families": {"claim": {"sequence": "claims"}}}}},
        report=report,
        context="raya.yaml",
    )

    assert not report.ok
    assert any("claims" in issue.message and "claim" in issue.message for issue in report.issues)


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
    assert index["by_id"]["pythagorean"] == 0
```

- [ ] **Step 2: Run the tests and verify the missing module failure**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_numbered_objects.py -q
```

Expected: fail during import with `ModuleNotFoundError: No module named 'raya_schema.numbered_objects'`.

- [ ] **Step 3: Implement the schema module**

Create `packages/schema/src/raya_schema/numbered_objects.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .validation import ValidationReport

NUMBERED_OBJECT_INDEX_PATH = "data/numbered-objects.json"
NUMBERED_OBJECT_STYLES = {"margin", "banded", "caption", "equation"}

BUILT_IN_NUMBERED_OBJECT_SEQUENCES: dict[str, dict[str, str]] = {
    "theorem": {"label": "Theorem", "style": "margin"},
    "example": {"label": "Example", "style": "margin"},
    "exercise": {"label": "Exercise", "style": "banded"},
    "assignment": {"label": "Assignment", "style": "banded"},
    "figure": {"label": "Figure", "style": "caption"},
    "table": {"label": "Table", "style": "caption"},
    "equation": {"label": "Equation", "style": "equation"},
}

BUILT_IN_NUMBERED_OBJECT_FAMILIES: dict[str, dict[str, str]] = {
    "theorem": {"sequence": "theorem", "label": "Theorem"},
    "lemma": {"sequence": "theorem", "label": "Lemma"},
    "proposition": {"sequence": "theorem", "label": "Proposition"},
    "corollary": {"sequence": "theorem", "label": "Corollary"},
    "definition": {"sequence": "theorem", "label": "Definition"},
    "example": {"sequence": "example", "label": "Example"},
    "exercise": {"sequence": "exercise", "label": "Exercise"},
    "problem": {"sequence": "exercise", "label": "Problem"},
    "homework": {"sequence": "assignment", "label": "Homework"},
    "assignment": {"sequence": "assignment", "label": "Assignment"},
    "project": {"sequence": "assignment", "label": "Project"},
    "exam": {"sequence": "assignment", "label": "Exam"},
    "task": {"sequence": "assignment", "label": "Task"},
    "figure": {"sequence": "figure", "label": "Figure"},
    "table": {"sequence": "table", "label": "Table"},
    "equation": {"sequence": "equation", "label": "Equation"},
}


@dataclass(frozen=True)
class NumberedObjectSequence:
    name: str
    label: str
    style: str


@dataclass(frozen=True)
class NumberedObjectFamily:
    name: str
    sequence: str
    label: str


@dataclass(frozen=True)
class NumberedObjectConfig:
    numbering: str
    sequences: dict[str, NumberedObjectSequence]
    families: dict[str, NumberedObjectFamily]


@dataclass(frozen=True)
class NumberedObject:
    id: str
    family: str
    sequence: str
    label: str
    number: str
    title: str | None
    source_path: str
    page_id: str
    page_title: str
    page_output_path: str
    href: str
    style: str

    @property
    def reference_text(self) -> str:
        return f"{self.label} {self.number}"

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "family": self.family,
            "sequence": self.sequence,
            "label": self.label,
            "number": self.number,
            "reference_text": self.reference_text,
            "title": self.title,
            "source_path": self.source_path,
            "page_id": self.page_id,
            "page_title": self.page_title,
            "page_output_path": self.page_output_path,
            "href": self.href,
            "style": self.style,
            "anchor": f"raya-object-{self.id}",
        }


def normalize_numbered_object_config(
    course_config: dict[str, Any],
    *,
    report: ValidationReport,
    context: str,
) -> NumberedObjectConfig:
    raw = (course_config.get("render") or {}).get("numbered_objects") or {}
    if not isinstance(raw, dict):
        report.add_error(f"{context}: render.numbered_objects must be a mapping")
        raw = {}
    numbering = raw.get("numbering", "page-hierarchy")
    if numbering != "page-hierarchy":
        report.add_error(f"{context}: render.numbered_objects.numbering must be page-hierarchy")
        numbering = "page-hierarchy"

    sequences: dict[str, NumberedObjectSequence] = {
        name: NumberedObjectSequence(name=name, label=value["label"], style=value["style"])
        for name, value in BUILT_IN_NUMBERED_OBJECT_SEQUENCES.items()
    }
    for name, value in (raw.get("sequences") or {}).items():
        if not isinstance(value, dict):
            report.add_error(f"{context}: render.numbered_objects.sequences.{name} must be a mapping")
            continue
        label = str(value.get("label") or sequences.get(name, NumberedObjectSequence(name, name.title(), "margin")).label)
        style = str(value.get("style") or sequences.get(name, NumberedObjectSequence(name, label, "margin")).style)
        if style not in NUMBERED_OBJECT_STYLES:
            report.add_error(f"{context}: render.numbered_objects.sequences.{name}.style must be one of {sorted(NUMBERED_OBJECT_STYLES)}")
            style = "margin"
        sequences[name] = NumberedObjectSequence(name=name, label=label, style=style)

    families: dict[str, NumberedObjectFamily] = {
        name: NumberedObjectFamily(name=name, sequence=value["sequence"], label=value["label"])
        for name, value in BUILT_IN_NUMBERED_OBJECT_FAMILIES.items()
    }
    for name, value in (raw.get("families") or {}).items():
        if not isinstance(value, dict):
            report.add_error(f"{context}: render.numbered_objects.families.{name} must be a mapping")
            continue
        sequence = str(value.get("sequence") or name)
        label = str(value.get("label") or name.title())
        if sequence not in sequences:
            report.add_error(
                f"{context}: numbered object family {name!r} references undeclared sequence {sequence!r}"
            )
            continue
        families[name] = NumberedObjectFamily(name=name, sequence=sequence, label=label)

    return NumberedObjectConfig(numbering=numbering, sequences=sequences, families=families)


def build_numbered_objects_index(*, course_id: str, objects: list[NumberedObject]) -> dict[str, Any]:
    serialized = [obj.to_json() for obj in objects]
    return {
        "version": 1,
        "course_id": course_id,
        "objects": serialized,
        "by_id": {obj["id"]: index for index, obj in enumerate(serialized)},
    }


def validate_numbered_objects_index(path: Path) -> ValidationReport:
    report = ValidationReport()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report.add_error(f"{path}: could not read numbered objects index: {exc}")
        return report
    if data.get("version") != 1:
        report.add_error(f"{path}: numbered objects index version must be 1")
    objects = data.get("objects")
    by_id = data.get("by_id")
    if not isinstance(objects, list):
        report.add_error(f"{path}: objects must be a list")
        objects = []
    if not isinstance(by_id, dict):
        report.add_error(f"{path}: by_id must be a mapping")
        by_id = {}
    required = {
        "id",
        "family",
        "sequence",
        "label",
        "number",
        "reference_text",
        "source_path",
        "page_id",
        "page_title",
        "page_output_path",
        "href",
        "style",
        "anchor",
    }
    seen: set[str] = set()
    for index, obj in enumerate(objects):
        if not isinstance(obj, dict):
            report.add_error(f"{path}: objects[{index}] must be a mapping")
            continue
        missing = sorted(required - set(obj))
        if missing:
            report.add_error(f"{path}: objects[{index}] is missing {missing}")
        obj_id = obj.get("id")
        if not isinstance(obj_id, str) or not obj_id:
            report.add_error(f"{path}: objects[{index}].id must be a non-empty string")
            continue
        if obj_id in seen:
            report.add_error(f"{path}: duplicate numbered object id {obj_id!r}")
        seen.add(obj_id)
        if by_id.get(obj_id) != index:
            report.add_error(f"{path}: by_id[{obj_id!r}] must point to index {index}")
        if obj.get("style") not in NUMBERED_OBJECT_STYLES:
            report.add_error(f"{path}: objects[{index}].style is not supported")
    return report
```

Modify `packages/schema/src/raya_schema/__init__.py` to import and export:

```python
from .numbered_objects import (
    NUMBERED_OBJECT_INDEX_PATH,
    NumberedObject,
    NumberedObjectConfig,
    NumberedObjectFamily,
    NumberedObjectSequence,
    build_numbered_objects_index,
    normalize_numbered_object_config,
    validate_numbered_objects_index,
)
```

- [ ] **Step 4: Run the schema tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_numbered_objects.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add packages/schema/src/raya_schema/numbered_objects.py packages/schema/src/raya_schema/__init__.py tests/contracts/test_numbered_objects.py
git commit -m "Add numbered object schema defaults"
```

---

### Task 2: Parse Directive Blocks And Compute Numbers

**Files:**
- Create: `packages/static/src/raya_static/numbered_objects.py`
- Modify: `tests/contracts/test_numbered_objects.py`

- [ ] **Step 1: Add failing source parsing and numbering tests**

Append to `tests/contracts/test_numbered_objects.py`:

```python
from pathlib import Path

from raya_static.numbered_objects import (
    collect_numbered_object_sources,
    compute_numbered_objects_for_page,
    prepare_numbered_object_markdown,
)


def test_collect_numbered_object_sources_parses_fenced_blocks() -> None:
    body = """Before

::: theorem {#pythagorean title="Pythagorean theorem"}
For a right triangle, $a^2 + b^2 = c^2$.
:::

After @pythagorean
"""
    report = ValidationReport()

    prepared = prepare_numbered_object_markdown(body, report=report, source_path=Path("course/2/3.md"))

    assert report.ok
    assert "RAYA_NUMBERED_OBJECT_0" in prepared.body
    assert prepared.sources[0].id == "pythagorean"
    assert prepared.sources[0].family == "theorem"
    assert prepared.sources[0].title == "Pythagorean theorem"
    assert "a^2 + b^2" in prepared.sources[0].body


def test_prepare_numbered_object_markdown_rejects_nested_directives() -> None:
    body = """::: theorem {#outer}
::: corollary {#inner}
Nested text
:::
:::
"""
    report = ValidationReport()

    prepare_numbered_object_markdown(body, report=report, source_path=Path("course/0_index.md"))

    assert not report.ok
    assert any("nested numbered object" in issue.message for issue in report.issues)


def test_compute_numbered_objects_uses_page_prefix_and_shared_sequences() -> None:
    body = """::: theorem {#main}
Main result.
:::

::: corollary {#next}
Consequence.
:::

::: exercise {#practice}
Practice.
:::
"""
    report = ValidationReport()
    config = normalize_numbered_object_config({}, report=report, context="raya.yaml")
    prepared = prepare_numbered_object_markdown(body, report=report, source_path=Path("course/2_vectors/3_norms.md"))

    objects = compute_numbered_objects_for_page(
        prepared.sources,
        config=config,
        course_relative_source_path="course/2_vectors/3_norms.md",
        page_id="norms",
        page_title="Norms",
        page_output_path="2_vectors/3_norms/index.html",
        page_number_prefix="2.3",
    )

    assert report.ok
    assert [obj.number for obj in objects] == ["2.3.1", "2.3.2", "2.3.1"]
    assert objects[0].label == "Theorem"
    assert objects[1].label == "Corollary"
    assert objects[2].label == "Exercise"
```

- [ ] **Step 2: Run and verify missing static module failure**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_numbered_objects.py -q
```

Expected: fail with `ModuleNotFoundError: No module named 'raya_static.numbered_objects'`.

- [ ] **Step 3: Implement parser and numbering helpers**

Create `packages/static/src/raya_static/numbered_objects.py` with these public types and functions:

```python
from __future__ import annotations

from dataclasses import dataclass
import html
import re
import shlex
from pathlib import Path

from raya_schema.numbered_objects import NumberedObject, NumberedObjectConfig
from raya_schema.validation import ValidationReport

DIRECTIVE_OPEN_RE = re.compile(r"^(?P<indent> {0,3}):::\s+(?P<family>[A-Za-z][A-Za-z0-9_-]*)(?:\s+(?P<attrs>\{.*\}))?\s*$")
DIRECTIVE_CLOSE_RE = re.compile(r"^ {0,3}:::\s*$")
REFERENCE_RE = re.compile(r"(?<![`\\\w])@([A-Za-z][A-Za-z0-9_-]*)")
PLACEHOLDER_PREFIX = "RAYA_NUMBERED_OBJECT_"


@dataclass(frozen=True)
class NumberedObjectSource:
    placeholder: str
    id: str
    family: str
    title: str | None
    body: str
    source_path: Path
    start_line: int


@dataclass(frozen=True)
class PreparedNumberedMarkdown:
    body: str
    sources: list[NumberedObjectSource]


def _parse_attrs(raw: str | None, *, report: ValidationReport, source_path: Path, line_number: int) -> dict[str, str]:
    if not raw:
        return {}
    text = raw.strip()
    if not (text.startswith("{") and text.endswith("}")):
        report.add_error(f"{source_path}:{line_number}: numbered object attributes must use {{#id key=\"value\"}} syntax")
        return {}
    lexer = shlex.shlex(text[1:-1], posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    attrs: dict[str, str] = {}
    for part in lexer:
        if part.startswith("#"):
            attrs["id"] = part[1:]
        elif "=" in part:
            key, value = part.split("=", 1)
            attrs[key] = value
        else:
            report.add_error(f"{source_path}:{line_number}: unsupported numbered object attribute {part!r}")
    return attrs


def prepare_numbered_object_markdown(
    body: str,
    *,
    report: ValidationReport,
    source_path: Path,
) -> PreparedNumberedMarkdown:
    lines = body.splitlines()
    output: list[str] = []
    sources: list[NumberedObjectSource] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        match = DIRECTIVE_OPEN_RE.match(line)
        if not match:
            output.append(line)
            index += 1
            continue
        start_line = index + 1
        family = match.group("family")
        attrs = _parse_attrs(match.group("attrs"), report=report, source_path=source_path, line_number=start_line)
        object_id = attrs.get("id")
        if not object_id:
            report.add_error(f"{source_path}:{start_line}: numbered object requires an id such as {{#pythagorean}}")
            object_id = f"missing-id-{len(sources)}"
        block_lines: list[str] = []
        index += 1
        closed = False
        while index < len(lines):
            if DIRECTIVE_OPEN_RE.match(lines[index]):
                report.add_error(f"{source_path}:{index + 1}: nested numbered object directives are not supported")
            if DIRECTIVE_CLOSE_RE.match(lines[index]):
                closed = True
                break
            block_lines.append(lines[index])
            index += 1
        if not closed:
            report.add_error(f"{source_path}:{start_line}: numbered object directive is missing a closing ::: line")
        placeholder = f"{PLACEHOLDER_PREFIX}{len(sources)}"
        sources.append(
            NumberedObjectSource(
                placeholder=placeholder,
                id=object_id,
                family=family,
                title=attrs.get("title"),
                body="\n".join(block_lines).strip("\n"),
                source_path=source_path,
                start_line=start_line,
            )
        )
        output.append("")
        output.append(placeholder)
        output.append("")
        index += 1
    return PreparedNumberedMarkdown(body="\n".join(output), sources=sources)


def collect_numbered_object_sources(
    body: str,
    *,
    report: ValidationReport,
    source_path: Path,
) -> list[NumberedObjectSource]:
    return prepare_numbered_object_markdown(body, report=report, source_path=source_path).sources


def compute_numbered_objects_for_page(
    sources: list[NumberedObjectSource],
    *,
    config: NumberedObjectConfig,
    course_relative_source_path: str,
    page_id: str,
    page_title: str,
    page_output_path: str,
    page_number_prefix: str,
) -> list[NumberedObject]:
    counters: dict[str, int] = {}
    objects: list[NumberedObject] = []
    for source in sources:
        family = config.families.get(source.family)
        if family is None:
            continue
        sequence = config.sequences[family.sequence]
        counters[family.sequence] = counters.get(family.sequence, 0) + 1
        number = f"{page_number_prefix}.{counters[family.sequence]}" if page_number_prefix else str(counters[family.sequence])
        objects.append(
            NumberedObject(
                id=source.id,
                family=source.family,
                sequence=family.sequence,
                label=family.label,
                number=number,
                title=source.title,
                source_path=course_relative_source_path,
                page_id=page_id,
                page_title=page_title,
                page_output_path=page_output_path,
                href=f"{page_output_path}#raya-object-{source.id}",
                style=sequence.style,
            )
        )
    return objects


def render_reference_link(object_id: str, reference_text: str, href: str) -> str:
    return f'<a class="raya-object-ref" href="{html.escape(href, quote=True)}">{html.escape(reference_text)}</a>'
```

- [ ] **Step 4: Run source parsing tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_numbered_objects.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/numbered_objects.py tests/contracts/test_numbered_objects.py
git commit -m "Parse numbered object directives"
```

---

### Task 3: Build Numbered Object Artifact Data

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/schema/src/raya_schema/artifacts.py`
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/contracts/test_artifact_validation.py`

- [ ] **Step 1: Add failing builder artifact assertions**

In `tests/contracts/test_static_builder.py`, extend the minimal build test to assert the new empty data index:

```python
numbered_objects = json.loads((artifact / "data" / "numbered-objects.json").read_text(encoding="utf-8"))
assert numbered_objects == {
    "version": 1,
    "course_id": "minimal",
    "objects": [],
    "by_id": {},
}
assert manifest["data"]["numbered_objects"] == "data/numbered-objects.json"
```

In the render fixture build test, after reading `manifest`, add:

```python
numbered_index = json.loads((artifact / "data" / "numbered-objects.json").read_text(encoding="utf-8"))
assert numbered_index["course_id"] == "render-fixture"
assert "by_id" in numbered_index
```

In `tests/contracts/test_artifact_validation.py`, add:

```python
def test_artifact_validation_rejects_invalid_numbered_objects_index(tmp_path: Path) -> None:
    artifact = _minimal_valid_artifact(tmp_path)
    manifest = json.loads((artifact / "manifest.json").read_text(encoding="utf-8"))
    manifest["data"]["numbered_objects"] = "data/numbered-objects.json"
    (artifact / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (artifact / "data" / "numbered-objects.json").write_text('{"version": 2, "objects": [], "by_id": {}}', encoding="utf-8")

    report = validate_artifact(artifact)

    assert not report.ok
    assert any("numbered objects index version must be 1" in issue.message for issue in report.issues)
```

- [ ] **Step 2: Run and verify failures**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py tests/contracts/test_artifact_validation.py -q
```

Expected: fail because `data/numbered-objects.json` and manifest `numbered_objects` are not written or validated.

- [ ] **Step 3: Integrate artifact writing and validation**

Modify `packages/static/src/raya_static/builder.py`:

```python
from raya_schema.numbered_objects import build_numbered_objects_index, normalize_numbered_object_config
```

After course config is loaded and a `ValidationReport` exists, normalize:

```python
numbered_config = normalize_numbered_object_config(course_config, report=report, context=str(config_path))
```

Before rendering pages, initialize:

```python
all_numbered_objects: list[NumberedObject] = []
```

Write the index after page collection and before manifest writing:

```python
numbered_objects_index = build_numbered_objects_index(
    course_id=course_config["course_id"],
    objects=all_numbered_objects,
)
_write_json(data_dir / "numbered-objects.json", numbered_objects_index)
```

Add to the manifest `data` mapping:

```python
"numbered_objects": "data/numbered-objects.json",
```

Modify `packages/schema/src/raya_schema/artifacts.py` to import `validate_numbered_objects_index` and, when manifest data contains `numbered_objects`, validate the path:

```python
numbered_objects_path = data_paths.get("numbered_objects")
if numbered_objects_path:
    report.extend(validate_numbered_objects_index(artifact_root / numbered_objects_path))
```

- [ ] **Step 4: Run artifact tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py tests/contracts/test_artifact_validation.py -q
```

Expected: pass after updating any expected manifest data fixtures in tests to include `numbered_objects`.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/builder.py packages/schema/src/raya_schema/artifacts.py tests/contracts/test_static_builder.py tests/contracts/test_artifact_validation.py
git commit -m "Write numbered object artifact index"
```

---

### Task 4: Collect Objects From Course Pages During Build

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/numbered_objects.py`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add failing fixture collection test**

In `tests/contracts/test_static_builder.py`, add a temporary course test:

```python
def test_build_collects_numbered_objects_with_page_hierarchy(tmp_path: Path) -> None:
    course = tmp_path / "course"
    (course / "course" / "2_vectors" / "3_norms").mkdir(parents=True)
    (course / "raya.yaml").write_text(
        "\n".join(
            [
                "course_id: numbered-demo",
                "title: Numbered Demo",
                "language: en",
                "source: course",
                "artifact: artifact",
                "hierarchy:",
                "  levels:",
                "    - key: unit",
                "      label: Unit",
                "    - key: topic",
                "      label: Topic",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (course / "course" / "0_index.md").write_text("---\nid: home\ntitle: Home\n---\n", encoding="utf-8")
    (course / "course" / "2_vectors" / "3_norms" / "0_index.md").write_text(
        """---
id: norms
title: Norms
---

::: theorem {#main title="Main theorem"}
The first result.
:::

::: corollary {#consequence}
The consequence.
:::

::: exercise {#practice}
Practice.
:::
""",
        encoding="utf-8",
    )

    result = build_course(course)

    assert result.report.ok
    numbered = json.loads((course / "artifact" / "data" / "numbered-objects.json").read_text(encoding="utf-8"))
    assert numbered["by_id"] == {"main": 0, "consequence": 1, "practice": 2}
    assert [obj["number"] for obj in numbered["objects"]] == ["2.3.1", "2.3.2", "2.3.1"]
    assert numbered["objects"][0]["href"].endswith("#raya-object-main")
```

- [ ] **Step 2: Run and verify empty index failure**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_collects_numbered_objects_with_page_hierarchy -q
```

Expected: fail because the index has no objects.

- [ ] **Step 3: Add page prefix helper and build collection**

In `packages/static/src/raya_static/numbered_objects.py`, add:

```python
def page_number_prefix_from_source_path(source_path: str) -> str:
    parts: list[str] = []
    for part in Path(source_path).parts:
        if part in {"course", "0_index.md", "index.md"}:
            continue
        stem = Path(part).stem
        match = re.match(r"^(\d+)(?:_|-|$)", stem)
        if match:
            parts.append(match.group(1))
    return ".".join(parts)
```

In `packages/static/src/raya_static/builder.py`, import:

```python
from raya_static.numbered_objects import (
    compute_numbered_objects_for_page,
    page_number_prefix_from_source_path,
    prepare_numbered_object_markdown,
)
```

During page discovery before rendering, read each page Markdown body, call `prepare_numbered_object_markdown`, compute page objects, reject duplicate IDs across the course, and append them to `all_numbered_objects`:

```python
prepared = prepare_numbered_object_markdown(page_body, report=report, source_path=page.source_path)
page_objects = compute_numbered_objects_for_page(
    prepared.sources,
    config=numbered_config,
    course_relative_source_path=str(page.source_path.relative_to(course_root)),
    page_id=page.id,
    page_title=page.title,
    page_output_path=page.output_path,
    page_number_prefix=page_number_prefix_from_source_path(str(page.source_path.relative_to(course_root))),
)
for obj in page_objects:
    if obj.id in numbered_ids:
        report.add_error(f"{page.source_path}: duplicate numbered object id {obj.id!r}")
    numbered_ids.add(obj.id)
all_numbered_objects.extend(page_objects)
```

Store the prepared Markdown by page path or page ID so rendering can reuse it instead of reparsing with different diagnostics.

- [ ] **Step 4: Run collection test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_collects_numbered_objects_with_page_hierarchy -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/numbered_objects.py tests/contracts/test_static_builder.py
git commit -m "Collect numbered objects during build"
```

---

### Task 5: Render Numbered Blocks And References

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/numbered_objects.py`
- Modify: `packages/schema/src/raya_schema/links.py`
- Test: `tests/contracts/test_numbered_objects.py`
- Test: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add failing render/reference tests**

Append to `tests/contracts/test_static_builder.py`:

```python
def test_numbered_objects_render_html_and_cross_references(tmp_path: Path) -> None:
    course = tmp_path / "course"
    (course / "course" / "1_math").mkdir(parents=True)
    (course / "raya.yaml").write_text(
        "course_id: refs-demo\ntitle: Refs Demo\nlanguage: en\nsource: course\nartifact: artifact\n",
        encoding="utf-8",
    )
    (course / "course" / "0_index.md").write_text(
        "---\nid: home\ntitle: Home\n---\n\nSee @pythagorean and [named theorem](raya:ref/pythagorean).\n",
        encoding="utf-8",
    )
    (course / "course" / "1_math" / "0_index.md").write_text(
        """---
id: math
title: Math
---

::: theorem {#pythagorean title="Pythagorean theorem"}
For a right triangle, $a^2 + b^2 = c^2$.
:::

The result above is @pythagorean.
""",
        encoding="utf-8",
    )

    result = build_course(course)

    assert result.report.ok
    home_html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    math_html = (course / "artifact" / "site" / "1_math" / "index.html").read_text(encoding="utf-8")
    assert 'href="1_math/#raya-object-pythagorean"' in home_html
    assert ">Theorem 1.1<" in home_html
    assert 'href="1_math/#raya-object-pythagorean">named theorem</a>' in home_html
    assert 'id="raya-object-pythagorean"' in math_html
    assert 'class="raya-numbered-object raya-numbered-object--margin raya-numbered-object--theorem"' in math_html
    assert "Pythagorean theorem" in math_html
    assert "a^2 + b^2" not in math_html
    assert "mjx-container" in math_html
```

- [ ] **Step 2: Run and verify raw placeholder/reference failure**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_numbered_objects_render_html_and_cross_references -q
```

Expected: fail because placeholders remain or `raya:ref` is unresolved.

- [ ] **Step 3: Implement render context and reference expansion**

In `packages/static/src/raya_static/numbered_objects.py`, add:

```python
@dataclass(frozen=True)
class NumberedObjectRenderItem:
    source: NumberedObjectSource
    object: NumberedObject


@dataclass(frozen=True)
class NumberedObjectRenderContext:
    items: list[NumberedObjectRenderItem]
    objects_by_id: dict[str, NumberedObject]
    current_page_output_path: str


def expand_shorthand_references(body: str, *, context: NumberedObjectRenderContext, report: ValidationReport, source_path: Path) -> str:
    def replace(match: re.Match[str]) -> str:
        object_id = match.group(1)
        obj = context.objects_by_id.get(object_id)
        if obj is None:
            report.add_error(f"{source_path}: unknown numbered object reference @{object_id}")
            return match.group(0)
        return f"[{obj.reference_text}](raya:ref/{object_id})"
    return REFERENCE_RE.sub(replace, body)
```

In `packages/static/src/raya_static/rendering.py`, change `render_markdown_body(...)` to accept:

```python
numbered_objects: NumberedObjectRenderContext | None = None,
```

Before Markdown parsing, use the prepared body for the page and call `expand_shorthand_references`. After HTML render, replace `<p>RAYA_NUMBERED_OBJECT_N</p>` with rendered HTML for that object. Render the object body through the existing Markdown renderer path so inline/display math is collected and converted by build-time MathJax.

Add an object HTML helper in `rendering.py`:

```python
def _render_numbered_object_html(rendered_body: str, *, item: NumberedObjectRenderItem) -> str:
    obj = item.object
    title = f'<span class="raya-numbered-object__title">{escape(obj.title)}</span>' if obj.title else ""
    return (
        f'<section class="raya-numbered-object raya-numbered-object--{obj.style} raya-numbered-object--{obj.family}" '
        f'id="raya-object-{escape(obj.id)}" data-raya-object-id="{escape(obj.id)}" data-raya-object-family="{escape(obj.family)}">'
        f'<div class="raya-numbered-object__marker">{escape(obj.reference_text)}</div>'
        f'<div class="raya-numbered-object__content">{title}{rendered_body}</div>'
        f'</section>'
    )
```

In `packages/static/src/raya_static/builder.py`, pass a `NumberedObjectRenderContext` for each page and resolve `raya:ref/<id>` in `_resolve_markdown_href`:

```python
if href.startswith("raya:ref/"):
    object_id = href.removeprefix("raya:ref/").split("#", 1)[0].split("?", 1)[0]
    obj = numbered_objects_by_id.get(object_id)
    if obj is not None:
        return _relative_href(page.output_path, obj.page_output_path) + f"#raya-object-{object_id}"
```

In `packages/schema/src/raya_schema/links.py`, keep `raya:ref/<id>` as stable but make `stable_markdown_id("raya:ref/abc")` return `ref/abc` so page IDs cannot collide accidentally.

- [ ] **Step 4: Run render/reference test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_numbered_objects_render_html_and_cross_references -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/rendering.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/numbered_objects.py packages/schema/src/raya_schema/links.py tests/contracts/test_static_builder.py tests/contracts/test_numbered_objects.py
git commit -m "Render numbered object references"
```

---

### Task 6: Add Diagnostics For Authoring Errors

**Files:**
- Modify: `packages/static/src/raya_static/numbered_objects.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `tests/contracts/test_numbered_objects.py`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add failing diagnostics tests**

Add to `tests/contracts/test_static_builder.py`:

```python
def test_build_rejects_duplicate_numbered_object_ids(tmp_path: Path) -> None:
    course = _make_numbered_course(tmp_path)
    (course / "course" / "0_index.md").write_text(
        "---\nid: home\ntitle: Home\n---\n\n::: theorem {#same}\nFirst.\n:::\n\n::: exercise {#same}\nSecond.\n:::\n",
        encoding="utf-8",
    )

    result = build_course(course)

    assert not result.report.ok
    assert any("duplicate numbered object id 'same'" in issue.message for issue in result.report.issues)


def test_build_rejects_unknown_numbered_reference(tmp_path: Path) -> None:
    course = _make_numbered_course(tmp_path)
    (course / "course" / "0_index.md").write_text(
        "---\nid: home\ntitle: Home\n---\n\nSee @missing.\n",
        encoding="utf-8",
    )

    result = build_course(course)

    assert not result.report.ok
    assert any("unknown numbered object reference @missing" in issue.message for issue in result.report.issues)


def test_build_rejects_unknown_numbered_family(tmp_path: Path) -> None:
    course = _make_numbered_course(tmp_path)
    (course / "course" / "0_index.md").write_text(
        "---\nid: home\ntitle: Home\n---\n\n::: claim {#main}\nUnsupported.\n:::\n",
        encoding="utf-8",
    )

    result = build_course(course)

    assert not result.report.ok
    assert any("unknown numbered object family 'claim'" in issue.message for issue in result.report.issues)
```

Add helper:

```python
def _make_numbered_course(tmp_path: Path) -> Path:
    course = tmp_path / "course"
    (course / "course").mkdir(parents=True)
    (course / "raya.yaml").write_text(
        "course_id: numbered-errors\ntitle: Numbered Errors\nlanguage: en\nsource: course\nartifact: artifact\n",
        encoding="utf-8",
    )
    return course
```

- [ ] **Step 2: Run and verify diagnostics failures**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_rejects_duplicate_numbered_object_ids tests/contracts/test_static_builder.py::test_build_rejects_unknown_numbered_reference tests/contracts/test_static_builder.py::test_build_rejects_unknown_numbered_family -q
```

Expected: fail for at least one missing diagnostic.

- [ ] **Step 3: Implement diagnostics**

In `compute_numbered_objects_for_page`, when a source family is unknown, add a report argument and emit:

```python
report.add_error(f"{source.source_path}:{source.start_line}: unknown numbered object family {source.family!r}; configure it under render.numbered_objects.families in raya.yaml")
```

In builder duplicate detection, include both the new source path and the original object source path:

```python
report.add_error(
    f"{page.source_path}: duplicate numbered object id {obj.id!r}; first defined in {existing.source_path}"
)
```

In `_resolve_markdown_href`, if a `raya:ref/<id>` target is missing, report:

```python
report.add_error(f"{page.source_path}: unknown numbered object link target raya:ref/{object_id}")
```

- [ ] **Step 4: Run diagnostics tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_rejects_duplicate_numbered_object_ids tests/contracts/test_static_builder.py::test_build_rejects_unknown_numbered_reference tests/contracts/test_static_builder.py::test_build_rejects_unknown_numbered_family -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/numbered_objects.py packages/static/src/raya_static/builder.py tests/contracts/test_static_builder.py tests/contracts/test_numbered_objects.py
git commit -m "Diagnose numbered object authoring errors"
```

---

### Task 7: Fixture Content, CSS, And Browser Debug Parity

**Files:**
- Modify: `examples/courses/render-fixture/raya.yaml`
- Create: `examples/courses/render-fixture/course/3_numbered_objects/0_index.md`
- Modify: `examples/courses/render-fixture/course/0_index.md`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/render_debug.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add render fixture page and config**

Append to `examples/courses/render-fixture/raya.yaml`:

```yaml
render:
  numbered_objects:
    numbering: page-hierarchy
    sequences:
      assignment:
        label: Activity
        style: banded
```

Create `examples/courses/render-fixture/course/3_numbered_objects/0_index.md`:

```markdown
---
id: numbered-objects
title: Numbered Objects
---

This fixture checks course-global references such as @main-theorem, @vector-corollary, @matrix-equation, @fixture-figure, @fixture-table, @practice-problem, and @homework-one.

::: theorem {#main-theorem title="Fixture theorem"}
If $A$ is an invertible matrix, then the equation $A\mathbf{x}=\mathbf{b}$ has a unique solution.
:::

::: corollary {#vector-corollary}
With the same hypotheses as @main-theorem, the solution vector is $\mathbf{x}=A^{-1}\mathbf{b}$.
:::

::: definition {#basis-definition title="Basis"}
A basis is a linearly independent spanning set.
:::

::: equation {#matrix-equation}
$$
\begin{bmatrix}
1 & 0 \\
0 & 1
\end{bmatrix}
\vec{x} = \vec{x}
$$
:::

::: figure {#fixture-figure title="Fixture diagram"}
![Local fixture asset](../_assets/sample.svg)
:::

::: table {#fixture-table title="Fixture values"}
| Object | Expected sequence |
| --- | --- |
| theorem | theorem |
| corollary | theorem |
| exercise | exercise |
:::

::: problem {#practice-problem}
Use @matrix-equation to explain why the identity matrix fixes every vector.
:::

::: homework {#homework-one title="Homework fixture"}
Submit a short explanation that references [the theorem](raya:ref/main-theorem), @fixture-figure, and @fixture-table.
:::
```

Add a link in `examples/courses/render-fixture/course/0_index.md`:

```markdown
- [Numbered object fixture](3_numbered_objects/)
```

- [ ] **Step 2: Add failing browser/static assertions**

In `tests/contracts/test_static_builder.py`, extend the render fixture test:

```python
numbered_html = (artifact / "site" / "3_numbered_objects" / "index.html").read_text(encoding="utf-8")
numbered_index = json.loads((artifact / "data" / "numbered-objects.json").read_text(encoding="utf-8"))
assert numbered_index["by_id"]["main-theorem"] >= 0
assert numbered_index["by_id"]["vector-corollary"] >= 0
assert "Theorem 3.1" in numbered_html
assert "Corollary 3.2" in numbered_html
assert "Equation 3.1" in numbered_html
assert "Figure 3.1" in numbered_html
assert "Table 3.1" in numbered_html
assert "Problem 3.1" in numbered_html
assert "Homework 3.1" in numbered_html
assert "raya-numbered-object--margin" in numbered_html
assert "raya-numbered-object--banded" in numbered_html
assert "raya-numbered-object--caption" in numbered_html
assert "raya-numbered-object--equation" in numbered_html
```

In `tests/e2e/test_preview_static_read_path.py`, add browser assertions:

```python
def test_render_fixture_numbered_objects_are_static_and_local(tmp_path: Path) -> None:
    course = _copy_render_fixture(tmp_path)
    build = run_cli(["build", str(course)])
    assert build.returncode == 0, build.stderr
    site = course / "artifact" / "site"
    result = _run_browser_probe(
        site / "3_numbered_objects" / "index.html",
        """
        const objects = [...document.querySelectorAll(".raya-numbered-object")].map((node) => ({
          id: node.id,
          text: node.innerText,
          cls: node.className,
        }));
        const refs = [...document.querySelectorAll("a.raya-object-ref")].map((node) => ({
          text: node.textContent,
          href: node.getAttribute("href"),
        }));
        return {
          objects,
          refs,
          mathjaxScripts: [...document.scripts].filter((script) => /mathjax/i.test(script.src)).map((script) => script.src),
          rawTexVisible: document.body.innerText.includes("\\\\begin{bmatrix}"),
        };
        """,
    )
    assert any(item["id"] == "raya-object-main-theorem" for item in result["objects"])
    assert any("Theorem 3.1" in item["text"] for item in result["objects"])
    assert any(ref["text"] == "Theorem 3.1" and "#raya-object-main-theorem" in ref["href"] for ref in result["refs"])
    assert result["mathjaxScripts"] == []
    assert result["rawTexVisible"] is False
```

- [ ] **Step 3: Run and verify fixture/browser failures**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_rich_static_fixture_renders_markdown_math_code_and_assets tests/e2e/test_preview_static_read_path.py::test_render_fixture_numbered_objects_are_static_and_local -q
```

Expected: fail until rendering/CSS/browser probe support is complete.

- [ ] **Step 4: Add CSS and render-debug availability**

In `rich_render_css()` in `packages/static/src/raya_static/rendering.py`, add:

```css
.raya-numbered-object {
  margin: 1.25rem 0;
  border: 1px solid var(--raya-border);
  border-radius: 8px;
  background: var(--raya-surface);
}
.raya-numbered-object--margin {
  display: grid;
  grid-template-columns: minmax(7rem, max-content) 1fr;
  gap: 1rem;
  padding: 1rem;
}
.raya-numbered-object--banded {
  border-left: 0.35rem solid var(--raya-accent);
  padding: 1rem;
}
.raya-numbered-object--caption {
  padding: 0.875rem 1rem;
}
.raya-numbered-object--equation {
  border: 0;
  background: transparent;
  padding: 0.5rem 0;
}
.raya-numbered-object__marker {
  font-weight: 700;
  color: var(--raya-accent-strong);
}
.raya-numbered-object__title {
  display: block;
  font-weight: 700;
  margin-bottom: 0.5rem;
}
.raya-object-ref {
  font-weight: 600;
}
@media (max-width: 720px) {
  .raya-numbered-object--margin {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
}
```

In `packages/static/src/raya_static/render_debug.py`, include `numbered-objects` in fixture page names or page discovery so screenshots/inspection artifacts can find the new page.

- [ ] **Step 5: Run fixture/browser tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_rich_static_fixture_renders_markdown_math_code_and_assets tests/e2e/test_preview_static_read_path.py::test_render_fixture_numbered_objects_are_static_and_local -q
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add examples/courses/render-fixture/raya.yaml examples/courses/render-fixture/course/3_numbered_objects/0_index.md examples/courses/render-fixture/course/0_index.md packages/static/src/raya_static/rendering.py packages/static/src/raya_static/render_debug.py tests/e2e/test_preview_static_read_path.py tests/contracts/test_static_builder.py
git commit -m "Add numbered object render fixture"
```

---

### Task 8: Foundation And Role Documentation

**Files:**
- Modify: `docs/foundation/05_course_contract.md`
- Modify: `docs/foundation/06_artifact_contract.md`
- Modify: `docs/foundation/13_truth_surfaces.md`
- Modify: `docs/foundation/17_rendering_execution_plan.md`
- Modify: eight role docs listed in File Structure
- Modify: `tests/contracts/test_renderer_dependencies.py`

- [ ] **Step 1: Add failing documentation contract checks**

In `tests/contracts/test_renderer_dependencies.py`, add:

```python
def test_role_docs_cover_numbered_objects_and_references() -> None:
    required = {
        "docs/guides/en/professors/index.md": ["::: theorem", "@", "raya:ref/"],
        "docs/guides/en/students/index.md": ["Theorem", "Figure", "references"],
        "docs/guides/en/contributors/index.md": ["numbered_objects", "data/numbered-objects.json", "no browser-side MathJax"],
        "docs/guides/en/agents/index.md": ["numbered object", "raya:ref/", "data/numbered-objects.json"],
        "docs/guides/es/profesores/index.md": ["::: theorem", "@", "raya:ref/"],
        "docs/guides/es/estudiantes/index.md": ["Teorema", "Figura", "referencias"],
        "docs/guides/es/colaboradores/index.md": ["numbered_objects", "data/numbered-objects.json", "MathJax en el navegador"],
        "docs/guides/es/agentes/index.md": ["objeto numerado", "raya:ref/", "data/numbered-objects.json"],
    }
    for relative_path, needles in required.items():
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{relative_path} must mention {needle}"
```

- [ ] **Step 2: Run and verify docs test failure**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_renderer_dependencies.py::test_role_docs_cover_numbered_objects_and_references -q
```

Expected: fail until docs are updated.

- [ ] **Step 3: Update foundation docs**

Add concise canonical guidance:

- `docs/foundation/05_course_contract.md`: `raya.yaml` supports `render.numbered_objects.numbering`, `render.numbered_objects.sequences`, and `render.numbered_objects.families`; source supports fenced `:::` directives with `{#id title="..."}` and `@id` / `raya:ref/id` references.
- `docs/foundation/06_artifact_contract.md`: artifacts include manifest-declared `data/numbered-objects.json` with object IDs, labels, numbers, source paths, page output paths, anchors, and reference text.
- `docs/foundation/13_truth_surfaces.md`: source fenced directives and course config are authoring truth; rendered pages are reader-facing views; `data/numbered-objects.json` is machine-readable artifact truth.
- `docs/foundation/17_rendering_execution_plan.md`: numbered objects render at build time, share the no-CDN/no-browser-MathJax constraint, and participate in debug screenshots/inspection.

- [ ] **Step 4: Update English role docs**

Add role-appropriate sections:

- Professors: author examples for theorem/corollary/equation/figure/homework with `@id`.
- Students: how visible references like `Theorem 2.3.1` and `Figure 2.3.1` work.
- Contributors: config model, index contract, static parity, no external renderer/CDN requests.
- Agents: diagnostics, artifact inspection, and how to debug `data/numbered-objects.json` plus rendered anchors.

- [ ] **Step 5: Update Spanish role docs**

Mirror the same guidance in Spanish in the separate Spanish role directories. Keep commands, paths, schema keys, package names, stable IDs, and `raya:ref/` in English.

- [ ] **Step 6: Run documentation test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_renderer_dependencies.py::test_role_docs_cover_numbered_objects_and_references -q
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add docs/foundation/05_course_contract.md docs/foundation/06_artifact_contract.md docs/foundation/13_truth_surfaces.md docs/foundation/17_rendering_execution_plan.md docs/guides/en/professors/index.md docs/guides/en/students/index.md docs/guides/en/contributors/index.md docs/guides/en/agents/index.md docs/guides/es/profesores/index.md docs/guides/es/estudiantes/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md tests/contracts/test_renderer_dependencies.py
git commit -m "Document numbered object authoring"
```

---

### Task 9: Verification Gates And Review

**Files:**
- No planned source changes unless verification reveals defects.

- [ ] **Step 1: Run focused contract tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_numbered_objects.py tests/contracts/test_static_builder.py tests/contracts/test_artifact_validation.py tests/contracts/test_renderer_dependencies.py -q
```

Expected: pass.

- [ ] **Step 2: Run focused browser/static path tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -q
```

Expected: pass. If no browser is available locally, run the Docker verification in Step 5 and record the local browser limitation in the final status.

- [ ] **Step 3: Build and inspect the render fixture locally**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate examples/courses/render-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya artifacts inspect examples/courses/render-fixture/artifact
```

Expected: all commands exit 0. Confirm:

```bash
rg -n "main-theorem|Theorem 3\\.1|raya-object-main-theorem|data/numbered-objects.json" examples/courses/render-fixture/artifact
```

Expected: matches in `data/numbered-objects.json`, `manifest.json`, and `site/3_numbered_objects/index.html`.

- [ ] **Step 4: Run canonical host gate**

Run:

```bash
./scripts/check.sh
```

Expected: pass.

- [ ] **Step 5: Run canonical Docker gate**

Run:

```bash
./scripts/check-docker.sh
```

Expected: pass.

- [ ] **Step 6: Request code review**

Use `superpowers:requesting-code-review`. Ask the reviewer to focus on:

- Course-global duplicate object IDs and missing reference diagnostics.
- Build-time math handling inside numbered object bodies.
- Local/deployed static parity and absence of browser-side MathJax/CDN/external renderer requests.
- Manifest and `data/numbered-objects.json` stability.
- English/Spanish role-doc separation.

- [ ] **Step 7: Apply review feedback with receiving-review discipline**

If the review returns findings, use `superpowers:receiving-code-review`, verify each finding technically, patch only confirmed issues, and rerun the smallest affected test plus the host gate.

- [ ] **Step 8: Commit review fixes**

If changes were made:

```bash
git add <changed-files>
git commit -m "Fix numbered object review findings"
```

- [ ] **Step 9: Final status**

Report:

- Commits created.
- Verification commands run and their pass/fail result.
- Any unavailable local browser/Docker caveat.
- Whether `new_rayalucaria` is ahead of `origin/new_rayalucaria` and ready to push.

---

## Self-Review Notes

- Spec coverage: The plan covers course render config, built-in numbered families/sequences, custom sequence validation, page-hierarchy numbering, fenced directives, shorthand `@id`, explicit `raya:ref/id`, artifact data, stable anchors, render fixture, browser/static debugging, diagnostics, and EN/ES role docs. It keeps proof numbering out of the default numbered-object set, matching the design decision that proof treatment is separate from numbered theorem-like objects.
- Placeholder scan: The plan avoids deferred implementation placeholders and provides exact files, commands, expected failures, and code skeletons for the new interfaces.
- Type consistency: The plan consistently uses `NumberedObject`, `NumberedObjectConfig`, `NumberedObjectSource`, `PreparedNumberedMarkdown`, `NumberedObjectRenderContext`, `data/numbered-objects.json`, and `raya:ref/<id>`.
