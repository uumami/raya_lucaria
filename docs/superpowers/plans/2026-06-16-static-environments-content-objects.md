# Static Environments And Content Objects Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `solution`, `hint`, and `answer` as static environments alongside `proof`, with build-time target resolution, diagnostics, fixture coverage, browser/render-debug checks, and role documentation.

**Architecture:** Generalize the existing `raya_static.proofs` path into a static-environment parser/render context while preserving the public proof behavior and `raya-proof` CSS/classes. Numbered objects remain the only records in `data/numbered-objects.json`; static environments render into pages and resolve optional `of` targets during build. The static package owns parsing/rendering, schema stays authoritative for numbered object data, and docs explain the boundary.

**Tech Stack:** Python 3.10, `pytest`, Playwright/Chromium e2e tests, Raya schema/static/CLI packages, Markdown fixture content, build-time MathJax resources.

**Completion note:** Implemented on branch `new_rayalucaria`.
Verification included focused contracts/e2e tests,
`./scripts/check-render-debug.sh`, `./scripts/check.sh`, and
`./scripts/check-docker.sh`.

---

## File Structure

- `packages/static/src/raya_static/proofs.py`
  - Rename-compatible implementation home for static environments. Keep `prepare_proof_markdown`, `ProofSource`, `ProofRenderItem`, and `ProofRenderContext` aliases or wrappers so existing imports continue to work.
- `packages/static/src/raya_static/numbered_objects.py`
  - Update numbered-object parsing to skip every static environment opener, not only `proof`, so directives inside environments are not collected as numbered objects.
- `packages/static/src/raya_static/builder.py`
  - Collect static environments after numbered objects, resolve optional `of` targets, enforce duplicate/collision diagnostics, and pass context into rendering.
- `packages/static/src/raya_static/rendering.py`
  - Render static environments. Preserve current `raya-proof` markup for proof and add shared `raya-static-environment` markup/classes for `solution`, `hint`, and `answer`.
- `tests/contracts/test_proofs.py`
  - Parser-level static environment tests. Keep existing proof tests and add solution/hint/answer cases.
- `tests/contracts/test_static_builder.py`
  - Build/render diagnostics and fixture assertions.
- `tests/e2e/test_preview_static_read_path.py`
  - Browser/static-read-path checks for static environments on the render fixture.
- `packages/cli/src/raya_cli/render_debug.py`
  - Include static-environment evidence in render-debug page probes.
- `packages/cli/src/raya_cli/render_debug_report.py`
  - Validate static-environment evidence in render-debug reports.
- `tests/e2e/test_render_debug_report.py`
  - Unit/e2e report assertions for static environments.
- `tests/e2e/test_render_debug_parity_gate.py`
  - Parity-gate checks for static-environment evidence.
- `examples/courses/render-fixture/course/4_reader_ux/0_index.md`
  - Extend realistic fixture with hint/solution/answer examples.
- `docs/foundation/17_rendering_execution_plan.md`
  - Add accepted static-environment contract text.
- `docs/guides/en/professors/index.md`
- `docs/guides/en/students/index.md`
- `docs/guides/en/contributors/index.md`
- `docs/guides/en/agents/index.md`
- `docs/guides/es/profesores/index.md`
- `docs/guides/es/estudiantes/index.md`
- `docs/guides/es/colaboradores/index.md`
- `docs/guides/es/agentes/index.md`
  - Role guidance in separate languages.
- `tests/contracts/test_renderer_dependencies.py`
  - Documentation contract needles.

## Task 1: Static Environment Parser Contract

**Files:**
- Modify: `tests/contracts/test_proofs.py`
- Modify: `packages/static/src/raya_static/proofs.py`

- [ ] **Step 1: Add failing parser tests for solution/hint/answer**

In `tests/contracts/test_proofs.py`, extend imports:

```python
from raya_static.proofs import (
    PLACEHOLDER_PREFIX,
    STATIC_ENVIRONMENT_KINDS,
    is_static_environment_directive_open,
    prepare_proof_markdown,
    prepare_static_environment_markdown,
)
```

Add these tests after `test_prepare_proof_markdown_extracts_id_target_and_title()`:

```python
def test_prepare_static_environment_markdown_extracts_solution_hint_and_answer() -> None:
    report = _report()
    prepared = prepare_static_environment_markdown(
        '::: solution {#solution-one of="problem-one" title="Normal equations"}\n'
        "Solve $Ax=b$.\n"
        ":::\n\n"
        '::: hint {#hint-one of="problem-one"}\n'
        "Start with the residual.\n"
        ":::\n\n"
        "::: answer\n"
        "$x=0$.\n"
        ":::\n",
        report=report,
        source_path=Path("course/4_reader_ux/0_index.md"),
    )

    assert report.ok
    assert STATIC_ENVIRONMENT_KINDS == ("proof", "solution", "hint", "answer")
    assert [source.kind for source in prepared.sources] == [
        "solution",
        "hint",
        "answer",
    ]
    assert prepared.sources[0].placeholder == f"{PLACEHOLDER_PREFIX}0"
    assert prepared.sources[0].id == "solution-one"
    assert prepared.sources[0].of_id == "problem-one"
    assert prepared.sources[0].title == "Normal equations"
    assert prepared.sources[0].body == "Solve $Ax=b$."
    assert prepared.sources[1].id == "hint-one"
    assert prepared.sources[1].of_id == "problem-one"
    assert prepared.sources[1].title is None
    assert prepared.sources[2].id is None
    assert prepared.sources[2].of_id is None
    assert prepared.sources[2].title is None
    assert prepared.body.count(PLACEHOLDER_PREFIX) == 3
```

Add this compatibility test:

```python
def test_prepare_proof_markdown_remains_compatible_wrapper() -> None:
    report = _report()
    prepared = prepare_proof_markdown(
        '::: proof {#proof-main of="main-theorem" title="Key steps"}\nDone.\n:::\n',
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert report.ok
    assert prepared.sources[0].kind == "proof"
    assert prepared.sources[0].id == "proof-main"
    assert prepared.sources[0].of_id == "main-theorem"
    assert prepared.sources[0].title == "Key steps"
```

Add this opener test:

```python
def test_static_environment_opener_detects_all_static_environment_kinds() -> None:
    assert is_static_environment_directive_open("::: proof")
    assert is_static_environment_directive_open('::: solution {of="problem"}')
    assert is_static_environment_directive_open("::: hint   ")
    assert is_static_environment_directive_open("::: answer")
    assert not is_static_environment_directive_open("::: theorem {#main}")
```

- [ ] **Step 2: Run parser tests and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_proofs.py::test_prepare_static_environment_markdown_extracts_solution_hint_and_answer \
  tests/contracts/test_proofs.py::test_prepare_proof_markdown_remains_compatible_wrapper \
  tests/contracts/test_proofs.py::test_static_environment_opener_detects_all_static_environment_kinds \
  -q
```

Expected: FAIL because `STATIC_ENVIRONMENT_KINDS`, `prepare_static_environment_markdown`, `is_static_environment_directive_open`, and `kind` do not exist yet.

- [ ] **Step 3: Generalize proof source dataclasses in `proofs.py`**

In `packages/static/src/raya_static/proofs.py`, add the static environment kind tuple and opener regex near the existing constants:

```python
STATIC_ENVIRONMENT_KINDS = ("proof", "solution", "hint", "answer")
_STATIC_ENVIRONMENT_KIND_PATTERN = "|".join(STATIC_ENVIRONMENT_KINDS)
PLACEHOLDER_PREFIX = "RAYA_STATIC_ENVIRONMENT_"
STATIC_ENVIRONMENT_OPEN_RE = re.compile(
    rf"^ {{0,3}}:::[ \t]+(?P<kind>{_STATIC_ENVIRONMENT_KIND_PATTERN})"
    r"(?:[ \t]+(?P<attrs>\S.*?))?[ \t]*$"
)
PROOF_OPEN_RE = STATIC_ENVIRONMENT_OPEN_RE
```

Replace `ProofSource` with a kind-aware dataclass and aliases:

```python
@dataclass(frozen=True)
class StaticEnvironmentSource:
    placeholder: str
    kind: str
    id: str | None
    of_id: str | None
    title: str | None
    body: str
    source_path: Path
    start_line: int


ProofSource = StaticEnvironmentSource
```

Replace `PreparedProofMarkdown` with:

```python
@dataclass(frozen=True)
class PreparedStaticEnvironmentMarkdown:
    body: str
    sources: list[StaticEnvironmentSource]


PreparedProofMarkdown = PreparedStaticEnvironmentMarkdown
```

Replace render dataclasses with:

```python
@dataclass(frozen=True)
class StaticEnvironmentRenderItem:
    source: StaticEnvironmentSource
    target: NumberedObject | None


ProofRenderItem = StaticEnvironmentRenderItem


@dataclass(frozen=True)
class StaticEnvironmentRenderContext:
    items: list[StaticEnvironmentRenderItem]
    objects_by_id: dict[str, NumberedObject]


ProofRenderContext = StaticEnvironmentRenderContext
```

- [ ] **Step 4: Add generalized parser functions**

Replace `is_proof_directive_open()` with:

```python
def is_static_environment_directive_open(line: str) -> bool:
    return STATIC_ENVIRONMENT_OPEN_RE.match(line) is not None


def is_proof_directive_open(line: str) -> bool:
    opened = STATIC_ENVIRONMENT_OPEN_RE.match(line)
    return opened is not None and opened.group("kind") == "proof"
```

Rename the implementation body of `prepare_proof_markdown()` to `prepare_static_environment_markdown()` and adjust these details:

```python
def prepare_static_environment_markdown(
    body: str,
    *,
    report: ValidationReport,
    source_path: Path,
) -> PreparedStaticEnvironmentMarkdown:
```

Inside the loop, use:

```python
opened = STATIC_ENVIRONMENT_OPEN_RE.match(line)
```

Set:

```python
kind = opened.group("kind")
```

Use kind-aware diagnostics:

```python
f"{kind.capitalize()} directive contains nested directive"
f"{kind.capitalize()} directive is missing a closing ::: line"
```

Create sources with:

```python
StaticEnvironmentSource(
    placeholder=placeholder,
    kind=kind,
    id=attrs.get("id"),
    of_id=attrs.get("of"),
    title=attrs.get("title"),
    body="\n".join(content_lines).strip("\n"),
    source_path=source_path,
    start_line=start_line,
)
```

Add wrapper:

```python
def prepare_proof_markdown(
    body: str,
    *,
    report: ValidationReport,
    source_path: Path,
) -> PreparedProofMarkdown:
    return prepare_static_environment_markdown(
        body,
        report=report,
        source_path=source_path,
    )
```

- [ ] **Step 5: Make attribute diagnostics kind-aware without changing proof messages**

Change `_parse_attrs()` signature:

```python
def _parse_attrs(
    raw: str | None,
    report: ValidationReport,
    source_path: Path,
    line_number: int,
    *,
    kind: str,
) -> dict[str, str]:
```

Use `label = kind.capitalize()` for diagnostic text, while proof still says `Proof`:

```python
if raw is None:
    return {}
...
f"{label} directive attributes must use braces"
...
f"Could not parse {kind} attributes: {error}"
...
f"Unknown {kind} attribute '{token}'"
...
f"Unknown {kind} attribute '{key}'"
```

For ID diagnostics:

```python
noun = f"{kind} ID" if attr_name == "id" else f"{kind} target ID"
```

Call `_parse_attrs(..., kind=kind)`.

Keep accepted attrs as `#id`, `of`, and `title`.

- [ ] **Step 6: Run parser tests and full proof contract suite**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_proofs.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit parser contract**

```bash
git add packages/static/src/raya_static/proofs.py tests/contracts/test_proofs.py
git commit -m "Generalize proof parser to static environments"
```

## Task 2: Builder Diagnostics And Numbered Parser Skipping

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `packages/static/src/raya_static/numbered_objects.py`
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add failing builder tests for static environment targets and ID boundaries**

In `tests/contracts/test_static_builder.py`, add near existing proof build tests:

```python
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
```

Add diagnostics tests:

```python
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
        item for item in report.diagnostics if item.message == "Unknown solution target 'missing-problem'"
    )
    assert diagnostic.field == "line:6"
    assert diagnostic.next_action == 'Use of="object-id" with an existing numbered object ID'
```

```python
def test_static_environment_ids_cannot_collide_with_numbered_objects(tmp_path: Path) -> None:
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
        item for item in report.diagnostics if item.message == "Static environment ID 'same' collides with a numbered object ID"
    )
    assert diagnostic.next_action == "Use a unique static environment ID"
```

```python
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
        item for item in report.diagnostics if item.message == "Duplicate static environment ID 'same-hint'"
    )
    assert "first seen in" in diagnostic.next_action
```

- [ ] **Step 2: Run builder tests and verify RED**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_static_environments_render_targeted_headings_and_stay_out_of_numbered_index \
  tests/contracts/test_static_builder.py::test_static_environment_rejects_unknown_target \
  tests/contracts/test_static_builder.py::test_static_environment_ids_cannot_collide_with_numbered_objects \
  tests/contracts/test_static_builder.py::test_static_environment_rejects_duplicate_ids \
  -q
```

Expected: FAIL because `hint`, `solution`, and `answer` are still treated as unknown numbered object families or are not rendered.

- [ ] **Step 3: Update numbered-object parser to skip all static environments**

In `packages/static/src/raya_static/numbered_objects.py`, replace the local import and proof-specific skip:

```python
from raya_static.proofs import is_static_environment_directive_open
...
if is_static_environment_directive_open(line):
```

Keep the existing skip loop body, but rename local variables from `proof_fence_state` to `static_env_fence_state` for clarity.

- [ ] **Step 4: Update builder imports and collection names**

In `packages/static/src/raya_static/builder.py`, replace proof imports with static-environment names while keeping compatibility aliases allowed:

```python
from raya_static.proofs import (
    StaticEnvironmentRenderContext,
    StaticEnvironmentRenderItem,
    StaticEnvironmentSource,
    prepare_static_environment_markdown,
)
```

Rename `_ProofCollection` dataclass if present to `_StaticEnvironmentCollection` with:

```python
@dataclass(frozen=True)
class _StaticEnvironmentCollection:
    items_by_page_id: dict[str, list[StaticEnvironmentRenderItem]]
    prepared_bodies_by_page_id: dict[str, str]
```

If `_ProofCollection` is used only locally, replace references with `_StaticEnvironmentCollection`.

- [ ] **Step 5: Replace `_collect_proofs()` with `_collect_static_environments()`**

Use this implementation shape:

```python
def _collect_static_environments(
    *,
    pages: list[ContentPage],
    prepared_bodies_by_page_id: dict[str, str],
    objects_by_id: dict[str, NumberedObject],
    report: ValidationReport,
) -> _StaticEnvironmentCollection:
    items_by_page_id: dict[str, list[StaticEnvironmentRenderItem]] = {}
    prepared_bodies_by_page_id: dict[str, str] = {}
    seen_ids: dict[str, StaticEnvironmentSource] = {}

    for page in pages:
        prepared = prepare_static_environment_markdown(
            prepared_bodies_by_page_id.get(page.id, page.body),
            report=report,
            source_path=page.source_path,
        )
        prepared_bodies_by_page_id[page.id] = prepared.body
        if not report.ok:
            continue

        page_items: list[StaticEnvironmentRenderItem] = []
        for source in prepared.sources:
            if source.id:
                first_source = seen_ids.get(source.id)
                if first_source is not None:
                    report.add_error(
                        f"Duplicate static environment ID '{source.id}'",
                        path=source.source_path,
                        field=f"line:{source.start_line}",
                        next_action=(
                            "Use a unique static environment ID; first seen in "
                            f"{first_source.source_path} line:{first_source.start_line}"
                        ),
                    )
                    continue
                if source.id in objects_by_id:
                    report.add_error(
                        f"Static environment ID '{source.id}' collides with a numbered object ID",
                        path=source.source_path,
                        field=f"line:{source.start_line}",
                        next_action="Use a unique static environment ID",
                    )
                    continue
                seen_ids[source.id] = source
            target = None
            if source.of_id:
                target = objects_by_id.get(source.of_id)
                if target is None:
                    report.add_error(
                        f"Unknown {source.kind} target '{source.of_id}'",
                        path=source.source_path,
                        field=f"line:{source.start_line}",
                        next_action='Use of="object-id" with an existing numbered object ID',
                    )
                    continue
            page_items.append(StaticEnvironmentRenderItem(source=source, target=target))
        items_by_page_id[page.id] = page_items

    return _StaticEnvironmentCollection(
        items_by_page_id=items_by_page_id,
        prepared_bodies_by_page_id=prepared_bodies_by_page_id,
    )
```

- [ ] **Step 6: Pass static environment contexts into rendering**

In `build_course()`, replace `proof_collection = _collect_proofs(...)` with:

```python
static_environment_collection = _collect_static_environments(
    pages=content_model.pages,
    prepared_bodies_by_page_id=numbered_object_collection.prepared_bodies_by_page_id,
    objects_by_id=numbered_object_collection.objects_by_id,
    report=report,
)
```

Where each page render currently builds `proof_context`, build:

```python
static_environment_context = StaticEnvironmentRenderContext(
    items=static_environment_collection.items_by_page_id.get(page.id, []),
    objects_by_id=numbered_object_collection.objects_by_id,
)
```

Pass `body=static_environment_collection.prepared_bodies_by_page_id.get(page.id, page.body)` and `proofs=static_environment_context` to preserve the current `render_markdown_body` parameter until Task 3 renames rendering internals.

- [ ] **Step 7: Run focused builder diagnostics tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_static_environments_render_targeted_headings_and_stay_out_of_numbered_index \
  tests/contracts/test_static_builder.py::test_static_environment_rejects_unknown_target \
  tests/contracts/test_static_builder.py::test_static_environment_ids_cannot_collide_with_numbered_objects \
  tests/contracts/test_static_builder.py::test_static_environment_rejects_duplicate_ids \
  -q
```

Expected after Task 3 rendering is not yet complete: diagnostics tests may pass, render test may still fail on HTML classes. If render test still fails only on missing classes/headings, continue to Task 3 before committing. If diagnostics fail, fix builder collection before moving on.

## Task 3: Static Environment Rendering

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add proof compatibility assertion**

In `test_build_renders_proof_of_numbered_object()` in `tests/contracts/test_static_builder.py`, add:

```python
    assert 'class="raya-proof"' in html
    assert "raya-static-environment--proof" not in html
```

This keeps proof markup stable.

- [ ] **Step 2: Update rendering imports and fragment names**

In `packages/static/src/raya_static/rendering.py`, replace:

```python
from raya_static.proofs import ProofRenderContext, ProofRenderItem
```

with:

```python
from raya_static.proofs import StaticEnvironmentRenderContext, StaticEnvironmentRenderItem
```

Keep the `render_markdown_body(..., proofs=...)` parameter name in this task to reduce churn, but type it as `StaticEnvironmentRenderContext | None`.

- [ ] **Step 3: Replace proof rendering loop with static environment rendering loop**

Inside `RichMarkdownRenderer.render()`, keep the existing `proof_fragments` variable name and render each item using `_render_static_environment_html()`:

```python
rendered_proofs = {
    placeholder: _render_static_environment_html(
        self._md.renderer.render(proof_tokens, self._md.options, proof_env),
        item=item,
    )
    for placeholder, (
        item,
        proof_tokens,
        proof_env,
    ) in proof_fragments.items()
}
```

- [ ] **Step 4: Implement `_render_static_environment_html()`**

Replace `_render_proof_html()` with:

```python
def _static_environment_reference(item: StaticEnvironmentRenderItem) -> str:
    kind = item.source.kind
    label = {
        "proof": "Proof",
        "solution": "Solution",
        "hint": "Hint",
        "answer": "Answer",
    }[kind]
    if item.target is None:
        return label
    if kind == "hint":
        return f"Hint for {item.target.reference_text}"
    if kind == "answer":
        return f"Answer to {item.target.reference_text}"
    return f"{label} of {item.target.reference_text}"
```

```python
def _render_static_environment_html(
    rendered_body: str,
    *,
    item: StaticEnvironmentRenderItem,
) -> str:
    env_id = item.source.id
    kind = item.source.kind
    reference = _static_environment_reference(item)
    title = item.source.title or ""
    body = rendered_body.strip() or "<p></p>"
    if kind == "proof":
        id_html = (
            f' id="raya-proof-{html.escape(env_id, quote=True)}"' if env_id else ""
        )
        title_html = (
            f'<span class="raya-proof-title">{html.escape(title)}</span>'
            if title
            else ""
        )
        return "\n".join(
            [
                f'<section{id_html} class="raya-proof">',
                '<p class="raya-proof-heading">',
                f'<span class="raya-proof-reference">{html.escape(reference)}</span>'
                + (f" {title_html}" if title_html else ""),
                "</p>",
                '<div class="raya-proof-body">',
                body,
                '<span class="raya-proof-qed" aria-hidden="true">&#x25A1;</span>',
                "</div>",
                "</section>",
            ]
        )

    escaped_kind = html.escape(kind, quote=True)
    id_html = (
        f' id="raya-static-environment-{html.escape(env_id, quote=True)}"'
        if env_id
        else ""
    )
    title_html = (
        f'<span class="raya-static-environment-title">{html.escape(title)}</span>'
        if title
        else ""
    )
    return "\n".join(
        [
            (
                f'<section{id_html} class="raya-static-environment '
                f'raya-static-environment--{escaped_kind}">'
            ),
            '<p class="raya-static-environment-heading">',
            f'<span class="raya-static-environment-reference">{html.escape(reference)}</span>'
            + (f" {title_html}" if title_html else ""),
            "</p>",
            '<div class="raya-static-environment-body">',
            body,
            "</div>",
            "</section>",
        ]
    )
```

- [ ] **Step 5: Add CSS for static environments**

In `rich_render_css()`, after proof CSS, add:

```css
.raya-static-environment {
  border: 1px solid #d8dee4;
  border-left-width: 4px;
  margin: 1.25rem 0;
  overflow: hidden;
}
.raya-static-environment--solution {
  border-left-color: #1a7f37;
}
.raya-static-environment--hint {
  border-left-color: #9a6700;
}
.raya-static-environment--answer {
  border-left-color: #0969da;
}
.raya-static-environment-heading {
  background: #f6f8fa;
  border-bottom: 1px solid #d8dee4;
  font-weight: 650;
  margin: 0;
  padding: 0.6rem 0.85rem;
}
.raya-static-environment-reference {
  color: #24292f;
}
.raya-static-environment-title {
  color: #57606a;
  font-weight: 500;
}
.raya-static-environment-body {
  overflow-x: auto;
  padding: 0.85rem;
}
.raya-static-environment-body > :first-child {
  margin-top: 0;
}
.raya-static-environment-body > :last-child {
  margin-bottom: 0;
}
```

- [ ] **Step 6: Run focused render tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_build_renders_proof_of_numbered_object \
  tests/contracts/test_static_builder.py::test_static_environments_render_targeted_headings_and_stay_out_of_numbered_index \
  tests/contracts/test_static_builder.py::test_static_environment_rejects_unknown_target \
  tests/contracts/test_static_builder.py::test_static_environment_ids_cannot_collide_with_numbered_objects \
  tests/contracts/test_static_builder.py::test_static_environment_rejects_duplicate_ids \
  -q
```

Expected: PASS.

- [ ] **Step 7: Run proof and static builder focused suites**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_proofs.py \
  tests/contracts/test_static_builder.py::test_build_renders_proof_of_numbered_object \
  tests/contracts/test_static_builder.py::test_numbered_object_parser_leaves_malformed_proof_for_proof_parser \
  tests/contracts/test_static_builder.py::test_static_environments_render_targeted_headings_and_stay_out_of_numbered_index \
  -q
```

Expected: PASS.

- [ ] **Step 8: Commit builder/rendering support**

```bash
git add \
  packages/static/src/raya_static/numbered_objects.py \
  packages/static/src/raya_static/builder.py \
  packages/static/src/raya_static/rendering.py \
  tests/contracts/test_static_builder.py
git commit -m "Render static solution hint answer environments"
```

## Task 4: Render Fixture, Browser, And Render-Debug Evidence

**Files:**
- Modify: `examples/courses/render-fixture/course/4_reader_ux/0_index.md`
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/cli/src/raya_cli/render_debug.py`
- Modify: `packages/cli/src/raya_cli/render_debug_report.py`
- Modify: `tests/e2e/test_render_debug_report.py`
- Modify: `tests/e2e/test_render_debug_parity_gate.py`

- [ ] **Step 1: Add failing fixture assertions**

In `test_render_fixture_builds_rich_static_pages()` in `tests/contracts/test_static_builder.py`, add reader UX assertions:

```python
    assert "Hint for Activity 4.1" in reader_ux_visible
    assert "Solution of Activity 4.1" in reader_ux_visible
    assert "Answer to Activity 4.1" in reader_ux_visible
    assert "Standalone Hint" not in reader_ux_visible
    assert "Use the residual formula before expanding the matrix product." in reader_ux_visible
    assert "The residual vector is orthogonal to the direction vector." in reader_ux_visible
    assert "raya-static-environment--hint" in reader_ux_html
    assert "raya-static-environment--solution" in reader_ux_html
    assert "raya-static-environment--answer" in reader_ux_html
```

Do not add `hint`, `solution`, or `answer` to numbered index expected IDs.

- [ ] **Step 2: Run fixture build test and verify RED**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages \
  -q
```

Expected: FAIL because the fixture does not yet contain hint/solution/answer.

- [ ] **Step 3: Extend `reader-ux` fixture**

In `examples/courses/render-fixture/course/4_reader_ux/0_index.md`, after the `activity` block and before the existing proof/solution sketch, add:

```md
::: hint {#hint-orthogonal-activity of="orthogonal-activity"}
Use the residual formula before expanding the matrix product.
:::

::: solution {#solution-orthogonal-activity of="orthogonal-activity" title="Matrix check"}
The residual vector is
$$
\begin{bmatrix}2\\3\end{bmatrix}
-
\begin{bmatrix}2\\0\end{bmatrix}
=
\begin{bmatrix}0\\3\end{bmatrix},
$$
so the inner product with $u=\begin{bmatrix}1\\0\end{bmatrix}$ is $0$.
:::

::: answer {#answer-orthogonal-activity of="orthogonal-activity"}
The residual vector is orthogonal to the direction vector.
:::

::: hint
Standalone hints can support reading without creating a numbered object.
:::
```

- [ ] **Step 4: Update browser static-read-path test**

In `tests/e2e/test_preview_static_read_path.py`, in `test_render_fixture_reader_ux_page_uses_scannable_static_numbering`, extend the page probe to include:

```javascript
staticEnvironmentCount: document.querySelectorAll('.raya-static-environment').length,
staticEnvironmentTexts: Array.from(document.querySelectorAll('.raya-static-environment'))
  .map((node) => node.innerText),
staticEnvironmentIds: Array.from(document.querySelectorAll('.raya-static-environment[id]'))
  .map((node) => node.id),
```

Add Python assertions:

```python
    assert probe["staticEnvironmentCount"] >= 4
    assert "raya-static-environment-hint-orthogonal-activity" in probe["staticEnvironmentIds"]
    assert "raya-static-environment-solution-orthogonal-activity" in probe["staticEnvironmentIds"]
    assert "raya-static-environment-answer-orthogonal-activity" in probe["staticEnvironmentIds"]
    static_environment_text = " ".join(probe["staticEnvironmentTexts"])
    assert "Hint for Activity 4.1" in static_environment_text
    assert "Solution of Activity 4.1" in static_environment_text
    assert "Answer to Activity 4.1" in static_environment_text
    assert "Use the residual formula before expanding the matrix product." in static_environment_text
    assert "The residual vector is orthogonal to the direction vector." in static_environment_text
```

- [ ] **Step 5: Add render-debug static environment evidence**

In `packages/cli/src/raya_cli/render_debug.py`, extend the browser probe returned by `_capture_page()` near proof evidence:

```javascript
const staticEnvironments = Array.from(document.querySelectorAll('.raya-static-environment'))
  .map((node) => ({
    id: node.id || '',
    className: node.className || '',
    heading: node.querySelector('.raya-static-environment-heading')?.innerText || '',
    text: node.innerText || '',
  }));
```

Include `staticEnvironments` in the page evidence JSON.

In `packages/cli/src/raya_cli/render_debug_report.py`, add checks for `reader-ux`:

```python
_add_check(
    checks,
    check_id="static-environment:reader-ux:hint",
    ok=_page_text_contains(page, "Hint for Activity 4.1"),
    message="Reader UX render-debug evidence includes targeted hint",
)
_add_check(
    checks,
    check_id="static-environment:reader-ux:solution",
    ok=_page_text_contains(page, "Solution of Activity 4.1"),
    message="Reader UX render-debug evidence includes targeted solution",
)
_add_check(
    checks,
    check_id="static-environment:reader-ux:answer",
    ok=_page_text_contains(page, "Answer to Activity 4.1"),
    message="Reader UX render-debug evidence includes targeted answer",
)
```

Use the local helper patterns already used for numbered-content/proof checks.

In `tests/e2e/test_render_debug_parity_gate.py`, extend expected parity IDs with:

```python
"static-environment:reader-ux:hint",
"static-environment:reader-ux:solution",
"static-environment:reader-ux:answer",
```

In `tests/e2e/test_render_debug_report.py`, update sample reports or expected report checks to include a `staticEnvironments` entry and the new check IDs.

- [ ] **Step 6: Run focused fixture/browser/debug checks**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages \
  tests/e2e/test_render_debug_report.py \
  -q
```

Then run browser checks:

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_ux_page_uses_scannable_static_numbering \
  tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary \
  tests/e2e/test_render_debug_parity_gate.py::test_render_debug_parity_gate_passes_on_render_fixture_copy \
  -q
```

Expected: PASS.

- [ ] **Step 7: Run render-debug script gate**

```bash
./scripts/check-render-debug.sh
```

Expected: PASS and report includes static-environment checks.

- [ ] **Step 8: Commit fixture/debug evidence**

```bash
git add \
  examples/courses/render-fixture/course/4_reader_ux/0_index.md \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py \
  packages/cli/src/raya_cli/render_debug.py \
  packages/cli/src/raya_cli/render_debug_report.py \
  tests/e2e/test_render_debug_report.py \
  tests/e2e/test_render_debug_parity_gate.py
git commit -m "Add static environment render fixture evidence"
```

## Task 5: Foundation And Role Documentation

**Files:**
- Modify: `docs/foundation/17_rendering_execution_plan.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Modify: `tests/contracts/test_renderer_dependencies.py`

- [ ] **Step 1: Add failing docs contract needles**

In `tests/contracts/test_renderer_dependencies.py`, in `test_role_docs_cover_numbered_objects_and_references()`, add foundation needles:

```python
    assert "`solution`" in foundation
    assert "`hint`" in foundation
    assert "`answer`" in foundation
    assert "do not appear in `data/numbered-objects.json`" in foundation
```

Add EN role doc needles:

```python
    assert "`solution`" in en_professors
    assert "`hint`" in en_professors
    assert "`answer`" in en_professors
    assert "not numbered objects" in en_professors
    assert "static environments" in en_contributors
    assert "reader-ux" in en_agents
```

Add ES role doc needles:

```python
    assert "`solution`" in es_professors
    assert "`hint`" in es_professors
    assert "`answer`" in es_professors
    assert "no son objetos numerados" in es_professors
    assert "entornos estaticos" in es_contributors
    assert "reader-ux" in es_agents
```

- [ ] **Step 2: Run docs test and verify RED**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_renderer_dependencies.py::test_role_docs_cover_numbered_objects_and_references \
  -q
```

Expected: FAIL because docs do not yet mention static environments.

- [ ] **Step 3: Update foundation docs**

In `docs/foundation/17_rendering_execution_plan.md`, after the proof-block bullet, add:

```markdown
- Static environments are current build-time rendering behavior. `proof`,
  `solution`, `hint`, and `answer` use fenced directives, may carry stable
  IDs, and may target a numbered object with `of="object-id"`. They render
  static headings such as `Solution of Problem 3.1`, `Hint for Activity 4.1`,
  and `Answer to Homework 5.1`, but they do not appear in
  `data/numbered-objects.json`. Unknown targets, malformed attributes,
  duplicate static-environment IDs, and collisions with numbered object IDs
  fail build with source diagnostics.
```

- [ ] **Step 4: Update EN role docs**

Add concise paragraphs:

Professors:

```markdown
Use static environments for support around numbered objects. `proof`,
`solution`, `hint`, and `answer` render during build and may use
`of="object-id"` to target a theorem, problem, activity, homework, assignment,
figure, table, or equation. They are not numbered objects and do not create
records in `data/numbered-objects.json`.
```

Contributors:

```markdown
Static environments are separate from numbered objects. Preserve `proof`,
`solution`, `hint`, and `answer` as build-time rendered blocks whose optional
`of` target resolves against `data/numbered-objects.json`; do not add them to
the numbered index or require browser-side reference resolution.
```

Agents:

```markdown
For static-environment failures, inspect the source directive, the build
diagnostic, the target record in `data/numbered-objects.json`, the rendered
heading/anchor, and render-debug evidence from the `reader-ux` fixture.
```

Students:

```markdown
Proofs, solutions, hints, and answers should appear as static course content.
When they name a theorem, problem, activity, homework, figure, table, or
equation, that heading should already be resolved before the page reaches your
browser.
```

- [ ] **Step 5: Update ES role docs**

Use Spanish prose with technical identifiers unchanged.

Profesores:

```markdown
Usa entornos estaticos para apoyo alrededor de objetos numerados. `proof`,
`solution`, `hint` y `answer` se renderizan durante el build y pueden usar
`of="object-id"` para apuntar a un teorema, problema, actividad, tarea,
asignacion, figura, tabla o ecuacion. No son objetos numerados y no crean
registros en `data/numbered-objects.json`.
```

Colaboradores:

```markdown
Los entornos estaticos estan separados de los objetos numerados. Preserva
`proof`, `solution`, `hint` y `answer` como bloques renderizados durante el
build cuyo objetivo opcional `of` se resuelve contra
`data/numbered-objects.json`; no los agregues al index numerado ni exijas un
resolver de referencias en el navegador.
```

Agentes:

```markdown
Para fallas de entornos estaticos, inspecciona la directiva en la fuente, el
diagnostico de build, el registro objetivo en `data/numbered-objects.json`, el
encabezado/ancla renderizado y la evidencia de render-debug del fixture
`reader-ux`.
```

Estudiantes:

```markdown
Las pruebas, soluciones, pistas y respuestas deben aparecer como contenido
estatico del curso. Cuando nombran un teorema, problema, actividad, tarea,
figura, tabla o ecuacion, ese encabezado ya debe estar resuelto antes de que la
pagina llegue al navegador.
```

- [ ] **Step 6: Run docs checks**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_renderer_dependencies.py -q
```

```bash
rg -n "`solution`|`hint`|`answer`|entornos estaticos|static environments|data/numbered-objects.json" \
  docs/foundation/17_rendering_execution_plan.md docs/guides/en docs/guides/es
```

```bash
rg -n "source page|reader style|course-level|page/section|scraped HTML|proof targets|static references|default|examples|links|cross-references" docs/guides/es
```

Expected: docs tests pass. The Spanish avoidable-English scan should return no matches except existing technical/path contexts; if it returns new prose English from this task, translate it.

- [ ] **Step 7: Commit docs**

```bash
git add \
  docs/foundation/17_rendering_execution_plan.md \
  docs/guides/en/professors/index.md \
  docs/guides/en/students/index.md \
  docs/guides/en/contributors/index.md \
  docs/guides/en/agents/index.md \
  docs/guides/es/profesores/index.md \
  docs/guides/es/estudiantes/index.md \
  docs/guides/es/colaboradores/index.md \
  docs/guides/es/agentes/index.md \
  tests/contracts/test_renderer_dependencies.py
git commit -m "Document static environments content objects"
```

## Task 6: Final Verification And Review

**Files:**
- No planned source edits. Fix only issues found by verification or review.

- [ ] **Step 1: Run focused contract and e2e suites**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_proofs.py \
  tests/contracts/test_static_builder.py \
  tests/contracts/test_renderer_dependencies.py \
  tests/e2e/test_render_debug_report.py \
  -q
```

Expected: PASS.

- [ ] **Step 2: Run browser/render-debug checks**

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_ux_page_uses_scannable_static_numbering \
  tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary \
  tests/e2e/test_render_debug_parity_gate.py::test_render_debug_parity_gate_passes_on_render_fixture_copy \
  -q
```

Expected: PASS.

- [ ] **Step 3: Run render-debug script gate**

```bash
./scripts/check-render-debug.sh
```

Expected: PASS.

- [ ] **Step 4: Run host archive gate**

```bash
./scripts/check.sh
```

Expected: PASS.

- [ ] **Step 5: Run Docker reference gate**

```bash
./scripts/check-docker.sh
```

Expected: PASS.

- [ ] **Step 6: Request final code review**

Use `superpowers:requesting-code-review` with:

- base SHA: the commit before Task 1 implementation starts;
- head SHA: current `HEAD`;
- description: static environments for proof/solution/hint/answer, fixture/debug/docs coverage;
- verification output from Steps 1-5.

Fix Critical and Important findings before proceeding.

- [ ] **Step 7: Report branch status**

Run:

```bash
git status --short --branch
git log --oneline -8
```

Expected: clean worktree. Report whether the branch is ahead of `origin/new_rayalucaria`.
