# Proof Blocks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add authored `::: proof` blocks that render as proof environments, can point to existing numbered objects, support build-time math, and remain local/static with no browser-side MathJax dependency.

**Architecture:** Introduce a focused proof parser/model in `packages/static/src/raya_static/proofs.py`, then integrate it after numbered-object collection so proofs can resolve `of="object-id"` against the final numbered-object index. Rendering extends `RichMarkdownRenderer` with proof fragments that are parsed through the same Markdown and build-time MathJax path as page bodies and numbered objects. Proofs are rendered HTML only; they are not numbered objects, not included in `data/numbered-objects.json`, and not valid `@id`/`raya:ref/id` targets.

**Tech Stack:** Python 3.10, `markdown-it-py`, local MathJax artifact resources, `uv`, pytest, Chromium browser e2e tests.

---

## File Map

- Create `packages/static/src/raya_static/proofs.py`: proof directive dataclasses, attribute parsing, placeholder extraction, `of` validation, and render-item context.
- Modify `packages/static/src/raya_static/numbered_objects.py`: keep `::: proof` blocks out of numbered-object extraction while preserving existing numbered-object diagnostics for other directive families.
- Modify `packages/static/src/raya_static/builder.py`: collect proofs after numbered objects, validate proof targets against `objects_by_id`, pass proof context to page rendering.
- Modify `packages/static/src/raya_static/rendering.py`: parse and render proof fragments with Markdown, shorthand reference expansion, build-time math, local CSS, and QED marker.
- Create `tests/contracts/test_proofs.py`: parser/unit coverage for proof directives and diagnostics.
- Modify `tests/contracts/test_static_builder.py`: build-level proof behavior, math rendering, index exclusion, and diagnostics.
- Modify `tests/e2e/test_preview_static_read_path.py`: browser/static proof checks in the render fixture and debug artifact workflow.
- Modify `examples/courses/render-fixture/course/2_math_authoring/0_index.md`: replace proof prose baseline with a proof-block pointer to the numbered-object page.
- Modify `examples/courses/render-fixture/course/3_numbered_objects/0_index.md`: add theorem proof, homework solution-style proof, matrix/vector proof math, and diagnostic-friendly examples.
- Modify role docs:
  - `docs/guides/en/professors/index.md`
  - `docs/guides/en/students/index.md`
  - `docs/guides/en/contributors/index.md`
  - `docs/guides/en/agents/index.md`
  - `docs/guides/es/profesores/index.md`
  - `docs/guides/es/estudiantes/index.md`
  - `docs/guides/es/colaboradores/index.md`
  - `docs/guides/es/agentes/index.md`
- Modify foundation docs:
  - `docs/foundation/13_truth_surfaces.md`
  - `docs/foundation/17_rendering_execution_plan.md`

## Task 1: Proof Parser Contract

**Files:**
- Create: `packages/static/src/raya_static/proofs.py`
- Modify: `packages/static/src/raya_static/numbered_objects.py`
- Test: `tests/contracts/test_proofs.py`

- [ ] **Step 1: Write failing parser tests**

Create `tests/contracts/test_proofs.py`:

```python
from pathlib import Path

from raya_schema import ValidationReport
from raya_static.numbered_objects import prepare_numbered_object_markdown
from raya_static.proofs import PLACEHOLDER_PREFIX, prepare_proof_markdown


def _report() -> ValidationReport:
    return ValidationReport()


def test_prepare_proof_markdown_extracts_plain_proof() -> None:
    report = _report()
    prepared = prepare_proof_markdown(
        "Before\n\n::: proof\nUse induction.\n:::\n\nAfter\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert report.ok
    assert prepared.body == f"Before\n\n\n{PLACEHOLDER_PREFIX}0\n\n\nAfter\n"
    assert len(prepared.sources) == 1
    source = prepared.sources[0]
    assert source.placeholder == f"{PLACEHOLDER_PREFIX}0"
    assert source.id is None
    assert source.of_id is None
    assert source.title is None
    assert source.body == "Use induction."
    assert source.start_line == 3


def test_prepare_proof_markdown_extracts_id_target_and_title() -> None:
    report = _report()
    prepared = prepare_proof_markdown(
        '::: proof {#proof-main of="main-theorem" title="Key steps"}\nDone.\n:::\n',
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert report.ok
    source = prepared.sources[0]
    assert source.id == "proof-main"
    assert source.of_id == "main-theorem"
    assert source.title == "Key steps"
    assert source.body == "Done."


def test_numbered_object_parser_leaves_proof_blocks_for_proof_parser() -> None:
    report = _report()
    prepared = prepare_numbered_object_markdown(
        '::: proof {of="main-theorem"}\nText.\n:::\n',
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert report.ok
    assert prepared.sources == []
    assert '::: proof {of="main-theorem"}' in prepared.body


def test_prepare_proof_markdown_rejects_invalid_id() -> None:
    report = _report()
    prepare_proof_markdown(
        "::: proof {#bad/id}\nText.\n:::\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Invalid proof ID 'bad/id'"
    assert diagnostic.field == "line:1"
    assert diagnostic.next_action.startswith("Use an ID that starts with a letter")


def test_prepare_proof_markdown_rejects_unknown_attribute() -> None:
    report = _report()
    prepare_proof_markdown(
        '::: proof {kind="direct"}\nText.\n:::\n',
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Unknown proof attribute 'kind'"
    assert diagnostic.field == "line:1"
    assert diagnostic.next_action == "Use #id, of=\"object-id\", or title=\"Optional title\""


def test_prepare_proof_markdown_rejects_missing_close() -> None:
    report = _report()
    prepare_proof_markdown(
        "::: proof\nText.\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Proof directive is missing a closing ::: line"
    assert diagnostic.field == "line:1"


def test_prepare_proof_markdown_rejects_nested_proof_or_numbered_block() -> None:
    report = _report()
    prepare_proof_markdown(
        "::: proof\n::: theorem {#inner}\nNo.\n:::\n:::\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Proof directive contains nested directive"
    assert diagnostic.field == "line:2"
    assert diagnostic.next_action == "Close the proof before starting another directive block"


def test_prepare_proof_markdown_ignores_fenced_directive_text() -> None:
    report = _report()
    prepared = prepare_proof_markdown(
        "```md\n::: proof\nNot real.\n:::\n```\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert report.ok
    assert prepared.sources == []
    assert "Not real." in prepared.body


def test_prepare_proof_markdown_allows_fenced_directive_text_inside_proof() -> None:
    report = _report()
    prepared = prepare_proof_markdown(
        "::: proof\n```md\n::: theorem {#not-real}\n:::\n```\nDone.\n:::\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert report.ok
    assert len(prepared.sources) == 1
    assert "not-real" in prepared.sources[0].body


def test_authored_proof_placeholder_prefix_is_rejected() -> None:
    report = _report()
    prepare_proof_markdown(
        f"{PLACEHOLDER_PREFIX}0\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Reserved proof placeholder text"
    assert diagnostic.next_action == "Remove text that starts with RAYA_PROOF_"
```

- [ ] **Step 2: Run parser tests to verify they fail**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_proofs.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'raya_static.proofs'`.

- [ ] **Step 3: Implement proof parser dataclasses and extraction**

Create `packages/static/src/raya_static/proofs.py`:

```python
from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path

from raya_schema import ValidationReport
from raya_schema.numbered_objects import NumberedObject
from raya_static.numbered_objects import (
    DIRECTIVE_CLOSE_RE,
    DIRECTIVE_OPEN_RE,
    OBJECT_ID_RE,
    _FenceState,
    _fence_opener,
    _is_closing_fence,
)

PLACEHOLDER_PREFIX = "RAYA_PROOF_"


@dataclass(frozen=True)
class ProofSource:
    placeholder: str
    id: str | None
    of_id: str | None
    title: str | None
    body: str
    source_path: Path
    start_line: int


@dataclass(frozen=True)
class PreparedProofMarkdown:
    body: str
    sources: list[ProofSource]


@dataclass(frozen=True)
class ProofRenderItem:
    source: ProofSource
    target: NumberedObject | None


@dataclass(frozen=True)
class ProofRenderContext:
    items: list[ProofRenderItem]
    objects_by_id: dict[str, NumberedObject]


def prepare_proof_markdown(
    body: str,
    *,
    report: ValidationReport,
    source_path: Path,
) -> PreparedProofMarkdown:
    _validate_no_reserved_placeholder_text(body, report=report, source_path=source_path)
    output_lines: list[str] = []
    sources: list[ProofSource] = []
    lines = body.splitlines()
    index = 0
    fence_state: _FenceState | None = None

    while index < len(lines):
        line = lines[index]
        if fence_state is not None:
            output_lines.append(line)
            if _is_closing_fence(line, fence_state):
                fence_state = None
            index += 1
            continue

        opener = _fence_opener(line)
        if opener is not None:
            fence_state = opener
            output_lines.append(line)
            index += 1
            continue

        opened = DIRECTIVE_OPEN_RE.match(line)
        if opened is None or opened.group("family") != "proof":
            output_lines.append(line)
            index += 1
            continue

        start_line = index + 1
        attrs = _parse_attrs(opened.group("attrs"), report, source_path, start_line)
        content_lines: list[str] = []
        index += 1
        closed = False

        content_fence_state: _FenceState | None = None
        while index < len(lines):
            current = lines[index]
            if content_fence_state is not None:
                content_lines.append(current)
                if _is_closing_fence(current, content_fence_state):
                    content_fence_state = None
                index += 1
                continue

            content_opener = _fence_opener(current)
            if content_opener is not None:
                content_fence_state = content_opener
                content_lines.append(current)
                index += 1
                continue

            if DIRECTIVE_OPEN_RE.match(current):
                report.add_error(
                    "Proof directive contains nested directive",
                    path=source_path,
                    field=f"line:{index + 1}",
                    next_action="Close the proof before starting another directive block",
                )
            if DIRECTIVE_CLOSE_RE.match(current):
                closed = True
                index += 1
                break
            content_lines.append(current)
            index += 1

        if not closed:
            report.add_error(
                "Proof directive is missing a closing ::: line",
                path=source_path,
                field=f"line:{start_line}",
                next_action="Add a closing ::: line after the proof body",
            )

        placeholder = f"{PLACEHOLDER_PREFIX}{len(sources)}"
        output_lines.extend(["", placeholder, ""])
        sources.append(
            ProofSource(
                placeholder=placeholder,
                id=attrs.get("id"),
                of_id=attrs.get("of"),
                title=attrs.get("title"),
                body="\n".join(content_lines).strip("\n"),
                source_path=source_path,
                start_line=start_line,
            )
        )

    trailing_newline = "\n" if body.endswith("\n") else ""
    return PreparedProofMarkdown(
        body="\n".join(output_lines) + trailing_newline,
        sources=sources,
    )


def _parse_attrs(
    raw: str | None,
    report: ValidationReport,
    source_path: Path,
    line_number: int,
) -> dict[str, str]:
    if raw is None:
        return {}
    stripped = raw.strip()
    if not stripped.startswith("{") or not stripped.endswith("}"):
        report.add_error(
            "Proof directive attributes must use braces",
            path=source_path,
            field=f"line:{line_number}",
            next_action='Use attributes such as {#proof-id of="theorem-id"}',
        )
        return {}
    try:
        tokens = shlex.split(stripped[1:-1])
    except ValueError as error:
        report.add_error(
            f"Could not parse proof attributes: {error}",
            path=source_path,
            field=f"line:{line_number}",
            next_action='Use shell-style quoted attributes, for example of="main-theorem"',
        )
        return {}

    attrs: dict[str, str] = {}
    for token in tokens:
        if token.startswith("#"):
            attrs["id"] = token[1:]
            continue
        if "=" not in token:
            report.add_error(
                f"Unknown proof attribute '{token}'",
                path=source_path,
                field=f"line:{line_number}",
                next_action='Use #id, of="object-id", or title="Optional title"',
            )
            continue
        key, value = token.split("=", 1)
        if key not in {"of", "title"}:
            report.add_error(
                f"Unknown proof attribute '{key}'",
                path=source_path,
                field=f"line:{line_number}",
                next_action='Use #id, of="object-id", or title="Optional title"',
            )
            continue
        attrs[key] = value

    for attr_name in ("id", "of"):
        value = attrs.get(attr_name)
        if value and OBJECT_ID_RE.fullmatch(value) is None:
            noun = "proof ID" if attr_name == "id" else "proof target ID"
            report.add_error(
                f"Invalid {noun} '{value}'",
                path=source_path,
                field=f"line:{line_number}",
                next_action=(
                    "Use an ID that starts with a letter and contains only letters, "
                    "digits, underscores, or hyphens"
                ),
            )
    return attrs


def _validate_no_reserved_placeholder_text(
    body: str,
    *,
    report: ValidationReport,
    source_path: Path,
) -> None:
    for line_number, line in enumerate(body.splitlines(), start=1):
        if PLACEHOLDER_PREFIX in line:
            report.add_error(
                "Reserved proof placeholder text",
                path=source_path,
                field=f"line:{line_number}",
                next_action=f"Remove text that starts with {PLACEHOLDER_PREFIX}",
            )
```

Modify `packages/static/src/raya_static/numbered_objects.py` inside `prepare_numbered_object_markdown`, immediately after `family = opened.group("family")`, so proof blocks remain intact for the proof parser and numbered objects inside proofs are not extracted:

```python
        if family == "proof":
            output_lines.append(line)
            index += 1
            while index < len(lines):
                current = lines[index]
                output_lines.append(current)
                index += 1
                if DIRECTIVE_CLOSE_RE.match(current):
                    break
            continue
```

- [ ] **Step 4: Run parser tests to verify they pass**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_proofs.py -q
```

Expected: all tests in `tests/contracts/test_proofs.py` pass.

- [ ] **Step 5: Commit parser contract**

Run:

```bash
git add packages/static/src/raya_static/proofs.py packages/static/src/raya_static/numbered_objects.py tests/contracts/test_proofs.py
git commit -m "Add proof block parser contract"
```

Expected: commit succeeds.

## Task 2: Builder Integration and Diagnostics

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Test: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add failing build tests**

Append these tests near the numbered-object build tests in `tests/contracts/test_static_builder.py`:

```python
def test_build_renders_proof_of_numbered_object(tmp_path: Path) -> None:
    course = _copy_minimal_course(tmp_path)
    course.joinpath("raya.yaml").write_text(
        _minimal_config("proof-demo").replace(
            "source: course",
            "source: course\nrender:\n  numbered_objects:\n    scheme: section",
        ),
        encoding="utf-8",
    )
    page = course / "course" / "0_index.md"
    page.write_text(
        "\n".join(
            [
                "# Proof Demo",
                "",
                '::: theorem {#main-theorem title="Fixture theorem"}',
                "For every vector $v$, $v=v$.",
                ":::",
                "",
                '::: proof {#proof-main of="main-theorem" title="Identity"}',
                "The vector identity follows from $v-v=0$.",
                ":::",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    visible = _visible_text(html)
    numbered_index = json.loads(
        (course / "artifact" / "data" / "numbered-objects.json").read_text(
            encoding="utf-8"
        )
    )
    assert "Proof of Theorem 0.1" in visible
    assert "Identity" in visible
    assert "raya-proof" in html
    assert 'id="raya-proof-proof-main"' in html
    assert "mjx-container" in html
    assert "proof-main" not in numbered_index["by_id"]
    assert list(numbered_index["by_id"]) == ["main-theorem"]


def test_build_rejects_unknown_proof_target(tmp_path: Path) -> None:
    course = _copy_minimal_course(tmp_path)
    page = course / "course" / "0_index.md"
    page.write_text(
        "# Proof Demo\n\n::: proof {of=\"missing-theorem\"}\nNo target.\n:::\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Unknown proof target 'missing-theorem'"
    assert diagnostic.field == "line:3"
    assert diagnostic.next_action == "Use of=\"object-id\" with an existing numbered object ID"
```

- [ ] **Step 2: Run build tests to verify they fail**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_renders_proof_of_numbered_object tests/contracts/test_static_builder.py::test_build_rejects_unknown_proof_target -q
```

Expected: tests fail because proof blocks are not integrated into the builder/rendering context.

- [ ] **Step 3: Add proof collection to builder**

Modify imports in `packages/static/src/raya_static/builder.py`:

```python
from raya_static.proofs import (
    ProofRenderContext,
    ProofRenderItem,
    prepare_proof_markdown,
)
```

Add a collection dataclass near `_NumberedObjectCollection`:

```python
@dataclass(frozen=True)
class _ProofCollection:
    items_by_page_id: dict[str, list[ProofRenderItem]]
    prepared_bodies_by_page_id: dict[str, str]
```

Add this function after `_collect_numbered_objects`:

```python
def _collect_proofs(
    *,
    pages: list[ContentPage],
    numbered_bodies_by_page_id: dict[str, str],
    objects_by_id: dict[str, NumberedObject],
    report: ValidationReport,
) -> _ProofCollection:
    items_by_page_id: dict[str, list[ProofRenderItem]] = {}
    prepared_bodies_by_page_id: dict[str, str] = {}

    for page in pages:
        prepared = prepare_proof_markdown(
            numbered_bodies_by_page_id.get(page.id, page.body),
            report=report,
            source_path=page.source_path,
        )
        prepared_bodies_by_page_id[page.id] = prepared.body
        if not report.ok:
            continue

        items: list[ProofRenderItem] = []
        for source in prepared.sources:
            target = None
            if source.of_id:
                target = objects_by_id.get(source.of_id)
                if target is None:
                    report.add_error(
                        f"Unknown proof target '{source.of_id}'",
                        path=source.source_path,
                        field=f"line:{source.start_line}",
                        next_action='Use of="object-id" with an existing numbered object ID',
                    )
                    continue
            items.append(ProofRenderItem(source=source, target=target))
        items_by_page_id[page.id] = items

    return _ProofCollection(
        items_by_page_id=items_by_page_id,
        prepared_bodies_by_page_id=prepared_bodies_by_page_id,
    )
```

In `build_course`, after `_collect_numbered_objects(...)`, collect proofs and use proof-prepared bodies:

```python
    proof_collection = _collect_proofs(
        pages=content_model.pages,
        numbered_bodies_by_page_id=numbered_object_collection.prepared_bodies_by_page_id,
        objects_by_id=numbered_object_collection.objects_by_id,
        report=report,
    )
    if not report.ok:
        return report
```

When rendering each page, create a proof context and pass the proof-prepared body:

```python
        proof_context = ProofRenderContext(
            items=proof_collection.items_by_page_id.get(page.id, []),
            objects_by_id=numbered_object_collection.objects_by_id,
        )
```

Change the `_render_page(...)` call body argument:

```python
            body=proof_collection.prepared_bodies_by_page_id.get(
                page.id,
                numbered_object_collection.prepared_bodies_by_page_id.get(
                    page.id,
                    page.body,
                ),
            ),
```

Add `proofs: ProofRenderContext` to `_render_page(...)` and pass it through to `render_markdown_body(...)` as `proofs=proofs`.

- [ ] **Step 4: Run build tests to verify remaining render failures**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_renders_proof_of_numbered_object tests/contracts/test_static_builder.py::test_build_rejects_unknown_proof_target -q
```

Expected: unknown target diagnostic passes; render test still fails until `render_markdown_body(..., proofs=...)` exists.

- [ ] **Step 5: Keep the builder changes uncommitted until renderer integration**

Run:

```bash
git diff -- packages/static/src/raya_static/builder.py tests/contracts/test_static_builder.py
```

Expected: the diff only contains proof collection, proof context plumbing, and the two proof build tests. Do not commit this red checkpoint; continue to Task 3 and commit after proof rendering passes.

## Task 3: Proof Rendering and CSS

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Test: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Extend renderer test expectations**

In `test_build_renders_proof_of_numbered_object`, keep the existing assertions and add:

```python
    assert 'class="raya-proof"' in html
    assert '<span class="raya-proof-reference">Proof of Theorem 0.1</span>' in html
    assert '<span class="raya-proof-title">Identity</span>' in html
    assert '<span class="raya-proof-qed" aria-hidden="true">&#x25A1;</span>' in html
    assert "RAYA_PROOF_" not in visible
    assert "\\(" not in visible
```

- [ ] **Step 2: Run render test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_renders_proof_of_numbered_object -q
```

Expected: failure because proof placeholders are not rendered.

- [ ] **Step 3: Add proof fragments to rich renderer**

Modify `packages/static/src/raya_static/rendering.py` imports:

```python
from raya_static.proofs import ProofRenderContext, ProofRenderItem
```

Add a fragment type near `_NumberedObjectFragment`:

```python
_ProofFragment = tuple[ProofRenderItem, list[Token], dict]
```

Change `RichMarkdownRenderer.render(...)` signature:

```python
        proofs: ProofRenderContext | None = None,
```

After numbered-object fragment preparation, add:

```python
        proof_fragments: dict[str, _ProofFragment] = {}
        if proofs is not None:
            reference_context = NumberedObjectRenderContext(
                items=numbered_objects.items if numbered_objects is not None else [],
                objects_by_id=proofs.objects_by_id,
            )
            for item in proofs.items:
                proof_env = _new_env(self._resolve_href, collect_headings=False)
                proof_body = expand_shorthand_references(
                    item.source.body,
                    context=reference_context,
                    report=self._report,
                    source_path=item.source.source_path,
                )
                if not self._report.ok:
                    return ""
                proof_tokens = self._md.parse(proof_body, proof_env)
                proof_fragments[item.source.placeholder] = (
                    item,
                    proof_tokens,
                    proof_env,
                )
```

Pass `proof_fragments` into `_collect_math_items_in_render_order(...)`, set `raya_math_html_by_id` on each `proof_env`, render proof HTML, and replace placeholders:

```python
        for _, _, proof_env in proof_fragments.values():
            proof_env["raya_math_html_by_id"] = math_result.html_by_id
```

```python
        rendered_proofs = {
            placeholder: _render_proof_html(
                self._md.renderer.render(proof_tokens, self._md.options, proof_env),
                item=item,
            )
            for placeholder, (item, proof_tokens, proof_env) in proof_fragments.items()
        }
        html_fragment = self._replace_proof_placeholders(html_fragment, rendered_proofs)
```

Add replacement helper:

```python
    def _replace_proof_placeholders(
        self,
        html_fragment: str,
        proofs: dict[str, str],
    ) -> str:
        for placeholder, proof_html in proofs.items():
            html_fragment = html_fragment.replace(f"<p>{placeholder}</p>", proof_html)
        return html_fragment
```

Update `render_markdown_body(...)` to accept and pass `proofs`.

- [ ] **Step 4: Extend math collection to include proofs**

Change `_collect_math_items_in_render_order(...)` signature to accept:

```python
    proof_fragments: dict[str, _ProofFragment],
```

When walking page tokens, mirror the numbered-object placeholder branch for proof placeholders:

```python
        proof_placeholder = _proof_placeholder_at(
            page_tokens,
            idx,
            proof_fragments,
        )
        if proof_placeholder is not None:
            _, proof_tokens, _ = proof_fragments[proof_placeholder]
            new_items = _collect_math_items(
                proof_tokens,
                source_path=source_path,
                counter=len(items),
            )
            items.extend(new_items)
            idx += 3
            continue
```

Add helper:

```python
def _proof_placeholder_at(
    tokens: list[Token],
    idx: int,
    proof_fragments: dict[str, _ProofFragment],
) -> str | None:
    if idx + 2 >= len(tokens):
        return None
    if tokens[idx].type != "paragraph_open":
        return None
    inline = tokens[idx + 1]
    if inline.type != "inline" or inline.content not in proof_fragments:
        return None
    if tokens[idx + 2].type != "paragraph_close":
        return None
    return inline.content
```

- [ ] **Step 5: Add proof HTML renderer and CSS**

Add to `packages/static/src/raya_static/rendering.py` near `_render_numbered_object_html(...)`:

```python
def _render_proof_html(rendered_body: str, *, item: ProofRenderItem) -> str:
    proof_id = item.source.id
    id_attr = (
        f' id="raya-proof-{html.escape(proof_id, quote=True)}"'
        if proof_id
        else ""
    )
    if item.target is not None:
        reference = f"Proof of {item.target.reference_text}"
    else:
        reference = "Proof"
    title = item.source.title or ""
    title_html = (
        f' <span class="raya-proof-title">{html.escape(title)}</span>'
        if title
        else ""
    )
    body = rendered_body.strip() or "<p></p>"
    return "\n".join(
        [
            f'<section{id_attr} class="raya-proof">',
            '<p class="raya-proof-heading">',
            f'<span class="raya-proof-reference">{html.escape(reference)}</span>'
            f"{title_html}",
            "</p>",
            '<div class="raya-proof-body">',
            body,
            '<span class="raya-proof-qed" aria-hidden="true">&#x25A1;</span>',
            "</div>",
            "</section>",
        ]
    )
```

Add to `rich_render_css()` after numbered-object CSS:

```css
.raya-proof {
  border-left: 3px solid #57606a;
  margin: 1.25rem 0;
  padding: 0.2rem 0 0.2rem 1rem;
}
.raya-proof-heading {
  color: #24292f;
  font-weight: 650;
  margin: 0 0 0.55rem;
}
.raya-proof-reference {
  font-style: italic;
}
.raya-proof-title {
  color: #57606a;
  font-weight: 500;
}
.raya-proof-body {
  overflow-x: auto;
}
.raya-proof-body > :first-child {
  margin-top: 0;
}
.raya-proof-body > :last-child {
  margin-bottom: 0;
}
.raya-proof-qed {
  float: right;
  margin-left: 0.75rem;
}
```

- [ ] **Step 6: Run proof builder tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_proofs.py tests/contracts/test_static_builder.py::test_build_renders_proof_of_numbered_object tests/contracts/test_static_builder.py::test_build_rejects_unknown_proof_target -q
```

Expected: tests pass.

- [ ] **Step 7: Commit proof rendering**

Run:

```bash
git add packages/static/src/raya_static/rendering.py packages/static/src/raya_static/builder.py tests/contracts/test_static_builder.py
git commit -m "Render proof blocks in static pages"
```

Expected: commit succeeds.

## Task 4: Fixture and Browser Debug Coverage

**Files:**
- Modify: `examples/courses/render-fixture/course/2_math_authoring/0_index.md`
- Modify: `examples/courses/render-fixture/course/3_numbered_objects/0_index.md`
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add fixture content**

In `examples/courses/render-fixture/course/3_numbered_objects/0_index.md`, add a proof after the main theorem:

```markdown
::: proof {#proof-main of="main-theorem" title="Fixture proof"}
Let $\vect{v}=\begin{bmatrix}1\\0\end{bmatrix}$ and compare the components of
$A\vect{v}$ with the stated basis relation. The local macros and matrix render
through the same build-time MathJax path used by the theorem.
:::
```

Add a proof after the homework/activity object:

```markdown
::: proof {of="homework-fixture" title="Solution sketch"}
The reviewed structure is the same static page surface as theorem references:
the proof can point to homework while homework keeps its own numbered identity.
:::
```

In `examples/courses/render-fixture/course/2_math_authoring/0_index.md`, replace prose that says proof is only authored text with:

```markdown
Proof blocks are rendered statically in the numbered object fixture page. They can
point to theorems, homework, or other numbered course objects while keeping math
pre-rendered at build time.
```

- [ ] **Step 2: Update fixture contract assertions**

In `tests/contracts/test_static_builder.py`, inside the render fixture test near the numbered-object assertions, add:

```python
    assert "Proof of Theorem 3.1" in numbered_objects_visible
    assert "Fixture proof" in numbered_objects_visible
    assert "Proof of Homework 3.1" in numbered_objects_visible
    assert "Solution sketch" in numbered_objects_visible
    assert 'class="raya-proof"' in numbered_objects_html
    assert 'id="raya-proof-proof-main"' in numbered_objects_html
    assert "RAYA_PROOF_" not in numbered_objects_visible
```

Update the math-authoring visible assertion to:

```python
    assert "Proof blocks are rendered statically" in math_authoring_visible
```

- [ ] **Step 3: Update browser e2e proof probe**

In `tests/e2e/test_preview_static_read_path.py`, in `test_render_fixture_numbered_objects_are_static_and_local`, extend the page probe:

```javascript
proofCount: document.querySelectorAll('.raya-proof').length,
proofHeading: document.querySelector('.raya-proof-heading')?.textContent || '',
proofHasMath: Boolean(document.querySelector('.raya-proof mjx-container')),
proofIds: Array.from(document.querySelectorAll('.raya-proof[id]')).map((node) => node.id),
```

Add Python assertions after the probe:

```python
    assert probe["proofCount"] >= 2
    assert "Proof of Theorem 3.1" in probe["proofHeading"]
    assert probe["proofHasMath"]
    assert "raya-proof-proof-main" in probe["proofIds"]
```

- [ ] **Step 4: Run fixture and e2e checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_build_outputs_expected_static_pages -q
RAYA_TEST_BROWSER=chromium UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_numbered_objects_are_static_and_local -q
```

Expected: both tests pass. If the host browser path differs, set `RAYA_TEST_BROWSER` to the available Chromium-compatible binary used in this checkout.

- [ ] **Step 5: Commit fixture and browser coverage**

Run:

```bash
git add examples/courses/render-fixture/course/2_math_authoring/0_index.md examples/courses/render-fixture/course/3_numbered_objects/0_index.md tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Cover proof blocks in render fixture"
```

Expected: commit succeeds.

## Task 5: Role and Foundation Documentation

**Files:**
- Modify: `docs/foundation/13_truth_surfaces.md`
- Modify: `docs/foundation/17_rendering_execution_plan.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Test: `tests/contracts/test_renderer_dependencies.py`

- [ ] **Step 1: Add failing documentation coverage test**

In `tests/contracts/test_renderer_dependencies.py`, add:

```python
def test_role_docs_cover_proof_blocks() -> None:
    required = [
        Path("docs/guides/en/professors/index.md"),
        Path("docs/guides/en/students/index.md"),
        Path("docs/guides/en/contributors/index.md"),
        Path("docs/guides/en/agents/index.md"),
        Path("docs/guides/es/profesores/index.md"),
        Path("docs/guides/es/estudiantes/index.md"),
        Path("docs/guides/es/colaboradores/index.md"),
        Path("docs/guides/es/agentes/index.md"),
    ]

    for path in required:
        text = path.read_text(encoding="utf-8")
        assert "::: proof" in text, path
        assert 'of="' in text, path
```

- [ ] **Step 2: Run documentation test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_renderer_dependencies.py::test_role_docs_cover_proof_blocks -q
```

Expected: fails until all role docs include proof authoring examples.

- [ ] **Step 3: Update English role docs**

Add a concise proof section to each English role page with role-specific wording and this fenced example:

````markdown
```markdown
::: theorem {#main-theorem title="Fixture theorem"}
For every vector $\vect{v}$, the identity map returns $\vect{v}$.
:::

::: proof {#proof-main of="main-theorem" title="Identity"}
The equality follows component by component:
$$
I\vect{v}=\vect{v}.
$$
:::
```
````

Use these role emphases:
- Professors: proofs can point to theorems, homework, problems, figures, tables, equations, definitions, and activities while keeping each object independently numbered.
- Students: proof headings show the object being proved; math is rendered at build time and no browser MathJax request is needed.
- Contributors: proof blocks are static render surfaces, not numbered-index records.
- Agents: validate `of` targets against `data/numbered-objects.json`; do not introduce LaTeX `\label`, `\ref`, `\begin{proof}`, or browser-side MathJax.

- [ ] **Step 4: Update Spanish role docs**

Add equivalent Spanish sections to each Spanish role page with this fenced example:

````markdown
```markdown
::: theorem {#teorema-principal title="Teorema de ejemplo"}
Para cada vector $\vect{v}$, la identidad devuelve $\vect{v}$.
:::

::: proof {#prueba-principal of="teorema-principal" title="Identidad"}
La igualdad se verifica componente por componente:
$$
I\vect{v}=\vect{v}.
$$
:::
```
````

Keep technical identifiers in English: `::: proof`, `of`, `title`, `raya:ref/id`, `data/numbered-objects.json`, and path names.

- [ ] **Step 5: Update foundation rendering notes**

In `docs/foundation/17_rendering_execution_plan.md`, add proof blocks to the current Glintstone rendering baseline:

```markdown
- Proof blocks use `::: proof {of="object-id"}` and render statically as proof environments. They may target any numbered object family, including theorems, definitions, equations, figures, tables, problems, homework, and activities. Proofs are not numbered objects and do not appear in `data/numbered-objects.json`.
```

In `docs/foundation/13_truth_surfaces.md`, add proof diagnostics to the rendered-page authority notes:

```markdown
- Proof rendering is a browser-facing static surface derived from authored Markdown and the numbered-object index. The authored page and `data/numbered-objects.json` remain the authority for object IDs; rendered proof headings are inspection surfaces.
```

- [ ] **Step 6: Run documentation tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_renderer_dependencies.py::test_role_docs_cover_proof_blocks -q
```

Expected: test passes.

- [ ] **Step 7: Commit documentation**

Run:

```bash
git add docs/foundation/13_truth_surfaces.md docs/foundation/17_rendering_execution_plan.md docs/guides/en/professors/index.md docs/guides/en/students/index.md docs/guides/en/contributors/index.md docs/guides/en/agents/index.md docs/guides/es/profesores/index.md docs/guides/es/estudiantes/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md tests/contracts/test_renderer_dependencies.py
git commit -m "Document proof block authoring"
```

Expected: commit succeeds.

## Task 6: Full Verification and Review

**Files:**
- Read: all files changed in Tasks 1-5

- [ ] **Step 1: Run focused local verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_proofs.py tests/contracts/test_static_builder.py tests/contracts/test_renderer_dependencies.py -q
RAYA_TEST_BROWSER=chromium UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_numbered_objects_are_static_and_local -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run canonical host gate**

Run:

```bash
./scripts/check.sh
```

Expected: script exits 0.

- [ ] **Step 3: Run canonical Docker gate**

Run:

```bash
./scripts/check-docker.sh
```

Expected: script exits 0.

- [ ] **Step 4: Use verification-before-completion**

Read and follow `superpowers:verification-before-completion` before claiming the implementation works. Record the exact verification commands and whether each passed.

- [ ] **Step 5: Request code review**

Read and follow `superpowers:requesting-code-review` because this changes parsing, rendering, fixture behavior, and user-facing docs. Provide the reviewer the design spec, this plan, changed files, and verification output.

- [ ] **Step 6: Address review feedback**

If review returns findings, read and follow `superpowers:receiving-code-review`, classify each finding by evidence, implement required fixes using TDD, rerun affected verification, and commit fixes.

- [ ] **Step 7: Final branch status**

Run:

```bash
git status --short --branch
git log --oneline -5
```

Expected: branch is ahead of `origin/new_rayalucaria` by the implementation commits, with no uncommitted changes.
