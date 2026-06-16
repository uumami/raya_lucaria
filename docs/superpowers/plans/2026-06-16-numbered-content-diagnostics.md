# Numbered Content Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden numbered-object diagnostics, fixture coverage, and render-debug evidence for course-wide numbered content, references, and proofs.

**Architecture:** Keep CLI/build diagnostics and `data/numbered-objects.json` as authority. Extend the render fixture and render-debug report as inspection evidence only, using DOM-derived summaries and generated artifact data without adding a new canonical data file.

**Tech Stack:** Python 3.10, `pytest`, Playwright/Chromium, Raya schema/static/CLI packages, Markdown fixture content, shell verification scripts.

---

## File Structure

- `packages/schema/src/raya_schema/numbered_objects.py`
  - Owns numbered-object config normalization, built-in family/sequence contracts, source-reference collection, and `data/numbered-objects.json` validation.
- `packages/static/src/raya_static/numbered_objects.py`
  - Owns numbered-object directive parsing, shorthand reference expansion, and HTML rendering helpers.
- `packages/static/src/raya_static/builder.py`
  - Owns build-time collection of numbered objects/proofs and artifact writes.
- `packages/cli/src/raya_cli/render_debug.py`
  - Owns browser capture and `summary.json` evidence gathered from rendered pages.
- `packages/cli/src/raya_cli/render_debug_report.py`
  - Owns report inspection, `report.json`, and `index.html` rendering for render-debug evidence.
- `examples/courses/render-fixture/raya.yaml`
  - Owns fixture-level numbered-object config.
- `examples/courses/render-fixture/course/3_numbered_objects/0_index.md`
  - Owns the compact numbered-content matrix fixture page.
- `tests/contracts/test_numbered_objects.py`
  - Add focused schema/config and source-reference diagnostics tests.
- `tests/contracts/test_static_builder.py`
  - Extend build diagnostics and render-fixture artifact assertions.
- `tests/e2e/test_preview_static_read_path.py`
  - Extend browser/static-read-path and render-debug summary assertions.
- `tests/e2e/test_render_debug_report.py`
  - Add render-debug report inspection tests for numbered-content evidence.
- `tests/e2e/test_render_debug_parity_gate.py`
  - Add parity gate assertions for numbered-content evidence fields in `report.json`.
- `docs/foundation/17_rendering_execution_plan.md`
  - Update renderer quality/debugging status.
- `docs/guides/en/professors/index.md`, `docs/guides/en/contributors/index.md`, `docs/guides/en/students/index.md`, `docs/guides/en/agents/index.md`
  - Update English role guidance.
- `docs/guides/es/profesores/index.md`, `docs/guides/es/colaboradores/index.md`, `docs/guides/es/estudiantes/index.md`, `docs/guides/es/agentes/index.md`
  - Update Spanish role guidance, keeping technical identifiers in English.

## Task 1: Config And Source Diagnostics

**Files:**
- Modify: `tests/contracts/test_numbered_objects.py`
- Modify: `packages/schema/src/raya_schema/numbered_objects.py`
- Modify: `tests/contracts/test_static_builder.py`
- Modify only if required by failing tests: `packages/static/src/raya_static/numbered_objects.py`

- [ ] **Step 1: Write failing config diagnostic tests**

Add focused tests to `tests/contracts/test_numbered_objects.py`:

```python
from raya_schema import ValidationReport
from raya_schema.numbered_objects import normalize_numbered_object_config


def test_numbered_object_config_rejects_family_sequence_with_precise_field() -> None:
    report = ValidationReport(context="test")
    config = {
        "course_id": "demo",
        "render": {
            "numbered_objects": {
                "families": {
                    "activity": {
                        "sequence": "missing-practice",
                        "label": "Activity",
                    }
                }
            }
        },
    }

    normalize_numbered_object_config(config, report=report, context="raya.yaml")

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert (
        diagnostic.message
        == "Numbered object family 'activity' references unknown sequence "
        "'missing-practice' in raya.yaml"
    )
    assert diagnostic.field == "render.numbered_objects.families.activity.sequence"
    assert (
        diagnostic.next_action
        == "Define the sequence under render.numbered_objects.sequences or use a built-in sequence"
    )


def test_numbered_object_config_rejects_unknown_style_with_precise_field() -> None:
    report = ValidationReport(context="test")
    config = {
        "course_id": "demo",
        "render": {
            "numbered_objects": {
                "sequences": {
                    "practice": {
                        "label": "Practice",
                        "style": "poster",
                    }
                }
            }
        },
    }

    normalize_numbered_object_config(config, report=report, context="raya.yaml")

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert (
        diagnostic.message
        == "Numbered object sequence 'practice' in raya.yaml uses unknown style 'poster'"
    )
    assert diagnostic.field == "render.numbered_objects.sequences.practice.style"
    assert diagnostic.next_action == "Use margin, banded, caption, or equation"
```

- [ ] **Step 2: Run the new tests to verify current behavior**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_numbered_objects.py::test_numbered_object_config_rejects_family_sequence_with_precise_field tests/contracts/test_numbered_objects.py::test_numbered_object_config_rejects_unknown_style_with_precise_field -q
```

Expected: either PASS if existing diagnostics already satisfy the contract, or FAIL with the exact mismatch to fix. If both pass, keep the tests and continue.

- [ ] **Step 3: Write failing build diagnostic test for braceless numbered attrs**

Add to `tests/contracts/test_static_builder.py` near existing numbered-object diagnostics:

```python
def test_build_reports_malformed_numbered_object_attrs_before_body_directives(
    tmp_path: Path,
) -> None:
    course = _copy_minimal_fixture(tmp_path)
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
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Numbered object directive attributes must use braces"
    assert diagnostic.path == page.resolve()
    assert diagnostic.field == "line:7"
    assert diagnostic.next_action == 'Use attributes such as {#object-id title="Optional title"}'
```

- [ ] **Step 4: Run the failing build diagnostic test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_reports_malformed_numbered_object_attrs_before_body_directives -q
```

Expected: FAIL if malformed numbered openers are not recognized, or PASS if current parser already reports this exact diagnostic.

- [ ] **Step 5: Implement minimal parser support if Step 4 fails**

If the test fails because `::: theorem #bad-main` is not recognized as a numbered-object opener, add a loose opener regex to `packages/static/src/raya_static/numbered_objects.py`:

```python
NUMBERED_OBJECT_OPEN_RE = re.compile(
    r"^ {0,3}:::[ \t]+(?P<family>[A-Za-z][A-Za-z0-9_-]*)(?:[ \t]+(?P<attrs>\S.*?))?[ \t]*$"
)
```

Then change the opener detection in `prepare_numbered_object_markdown()` from:

```python
opened = DIRECTIVE_OPEN_RE.match(line)
if opened is None:
    output_lines.append(line)
    index += 1
    continue
```

to:

```python
opened = NUMBERED_OBJECT_OPEN_RE.match(line)
if opened is None:
    output_lines.append(line)
    index += 1
    continue
```

Keep `_parse_attrs()` unchanged so `attrs` values without braces produce the existing `"Numbered object directive attributes must use braces"` diagnostic.

- [ ] **Step 6: Run focused diagnostics tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_numbered_objects.py tests/contracts/test_static_builder.py::test_build_reports_malformed_numbered_object_attrs_before_body_directives tests/contracts/test_static_builder.py::test_build_rejects_unknown_numbered_object_family_without_crashing tests/contracts/test_static_builder.py::test_build_rejects_duplicate_numbered_object_ids_across_pages -q
```

Expected: PASS.

- [ ] **Step 7: Commit diagnostics task**

Run:

```bash
git add packages/schema/src/raya_schema/numbered_objects.py packages/static/src/raya_static/numbered_objects.py tests/contracts/test_numbered_objects.py tests/contracts/test_static_builder.py
git commit -m "Tighten numbered content diagnostics"
```

## Task 2: Numbered Content Matrix Fixture

**Files:**
- Modify: `examples/courses/render-fixture/raya.yaml`
- Modify: `examples/courses/render-fixture/course/3_numbered_objects/0_index.md`
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing artifact assertions for full family coverage**

Extend `test_render_fixture_builds_rich_static_pages` in `tests/contracts/test_static_builder.py` after the current numbered index assertions:

```python
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
    }
    assert set(numbered_index["by_id"]) >= expected_numbered_ids
    by_id = {
        item["id"]: item for item in numbered_index["objects"]
    }
    assert by_id["activity-one"]["family"] == "activity"
    assert by_id["activity-one"]["label"] == "Activity"
    assert by_id["assignment-one"]["family"] == "assignment"
    assert by_id["assignment-one"]["label"] == "Activity"
    assert by_id["assignment-one"]["sequence"] == "assignment"
    assert "Activity 3.2" in numbered_objects_visible
    assert "Activity 3.3" in numbered_objects_visible
    assert "Proof of Activity 3.3" in numbered_objects_visible
```

- [ ] **Step 2: Run the artifact assertion to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages -q
```

Expected: FAIL because `activity-one` and `assignment-one` are not in the fixture yet.

- [ ] **Step 3: Write failing browser assertions for matrix coverage**

Extend `test_render_fixture_numbered_objects_are_static_and_local` in `tests/e2e/test_preview_static_read_path.py`:

```python
    assert set(probe["ids"]) >= {
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
    }
    assert "Activity 3.2" in probe["text"]
    assert "Activity 3.3" in probe["text"]
    assert any(
        ref["href"] == "index.html#raya-object-assignment-one"
        and ref["text"] == "Activity 3.3"
        for ref in probe["refs"]
    )
    assert "Proof of Activity 3.3" in probe["text"]
```

- [ ] **Step 4: Run the browser test to verify it fails**

Run:

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_numbered_objects_are_static_and_local -q
```

Expected: FAIL because the fixture does not yet include the new objects.

- [ ] **Step 5: Extend the fixture config**

Modify `examples/courses/render-fixture/raya.yaml` so the assignment sequence remains labeled `Activity`, and add an explicit `activity` family:

```yaml
render:
  numbered_objects:
    numbering: page-hierarchy
    sequences:
      assignment:
        label: Activity
        style: banded
    families:
      homework:
        sequence: assignment
        label: Activity
      activity:
        sequence: assignment
        label: Activity
```

Keep `assignment` on the built-in assignment sequence so it also renders as `Activity`.

- [ ] **Step 6: Extend the numbered-object fixture page**

Append compact valid examples to `examples/courses/render-fixture/course/3_numbered_objects/0_index.md` after the existing homework block and before or after the current homework proof:

```markdown
::: activity {#activity-one title="Activity fixture"}
Compare @practice-problem with [the homework](raya:ref/homework-one), then record
one invariant preserved by @matrix-equation.
:::

::: assignment {#assignment-one title="Assignment fixture"}
Use @activity-one and @main-theorem to write a two-line explanation for the
identity matrix case.
:::

::: proof {of="assignment-one" title="Solution sketch"}
The assignment reduces to the matrix equality in @matrix-equation, so its
numbered target stays a practice object while the proof remains unnumbered.
:::
```

Adjust the surrounding reference sentence at the top of the page to include `@activity-one` and `@assignment-one`.

- [ ] **Step 7: Run focused fixture tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages -q
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_numbered_objects_are_static_and_local -q
```

Expected: both PASS.

- [ ] **Step 8: Commit fixture matrix task**

Run:

```bash
git add examples/courses/render-fixture/raya.yaml examples/courses/render-fixture/course/3_numbered_objects/0_index.md tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Expand numbered content render fixture"
```

## Task 3: Render-Debug Numbered Evidence

**Files:**
- Modify: `packages/cli/src/raya_cli/render_debug.py`
- Modify: `packages/cli/src/raya_cli/render_debug_report.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `tests/e2e/test_render_debug_report.py`
- Modify: `tests/e2e/test_render_debug_parity_gate.py`

- [ ] **Step 1: Write failing capture summary assertions**

Extend `test_capture_render_debug_writes_screenshots_and_summary` in `tests/e2e/test_preview_static_read_path.py` after loading `summary`:

```python
    numbered_capture = next(
        capture
        for capture in summary["captures"]
        if capture["page"] == "numbered-objects"
        and capture["viewport"]["name"] == "desktop"
    )
    evidence = numbered_capture["numbered_content"]
    assert {item["id"] for item in evidence["objects"]} >= {
        "main-theorem",
        "assignment-one",
    }
    assert {item["target_text"] for item in evidence["proofs"]} >= {
        "Theorem 3.1",
        "Activity 3.3",
    }
    assert any(
        ref["text"] == "Activity 3.3"
        and ref["href"].endswith("#raya-object-assignment-one")
        for ref in evidence["references"]
    )
```

- [ ] **Step 2: Run the capture summary assertion to verify it fails**

Run:

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary -q
```

Expected: FAIL with missing `numbered_content`.

- [ ] **Step 3: Implement browser-side evidence extraction**

In `packages/cli/src/raya_cli/render_debug.py`, add this helper near `_visible_non_code_text()`:

```python
def _numbered_content_evidence(page: Any) -> dict[str, object]:
    return page.evaluate(
        """() => {
            const objects = Array.from(document.querySelectorAll('.raya-numbered-object'))
              .map((node) => ({
                id: node.getAttribute('data-object-id') || '',
                family: Array.from(node.classList)
                  .find((name) => name.startsWith('raya-numbered-object--') &&
                    !['raya-numbered-object--margin', 'raya-numbered-object--banded',
                      'raya-numbered-object--caption', 'raya-numbered-object--equation']
                      .includes(name))
                  ?.replace('raya-numbered-object--', '') || '',
                anchor: node.id || '',
                label: node.querySelector('.raya-numbered-object-reference')?.innerText || '',
                title: node.querySelector('.raya-numbered-object-title')?.innerText || '',
                text: node.innerText || '',
              }));
            const references = Array.from(document.querySelectorAll('a[href*="raya-object-"]'))
              .map((node) => ({
                text: node.innerText || '',
                href: node.getAttribute('href') || '',
              }));
            const proofs = Array.from(document.querySelectorAll('.raya-proof'))
              .map((node) => {
                const reference = node.querySelector('.raya-proof-reference')?.innerText || '';
                const targetText = reference.startsWith('Proof of ')
                  ? reference.slice('Proof of '.length).replace(/\\.$/, '')
                  : '';
                return {
                  id: node.id || '',
                  heading: node.querySelector('.raya-proof-heading')?.innerText || '',
                  target_text: targetText,
                  target_id: '',
                };
              });
            return {objects, references, proofs};
        }"""
    )
```

Then add the evidence field to `_capture_render_debug_artifact()`:

```python
        "numbered_content": _numbered_content_evidence(page),
```

Keep `target_id` empty in browser capture for now; the report task will enrich target IDs from `data/numbered-objects.json`.

- [ ] **Step 4: Run the capture test to verify raw evidence**

Run:

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary -q
```

Expected: PASS for raw capture evidence. `summary.json` records proof target text;
`report.json` will enrich target IDs from `data/numbered-objects.json`.

- [ ] **Step 5: Write failing report enrichment test**

Add to `tests/e2e/test_render_debug_report.py`:

```python
def test_render_debug_report_enriches_numbered_content_from_index(tmp_path: Path) -> None:
    site = tmp_path / "site"
    debug = tmp_path / "debug"
    site.mkdir()
    debug.mkdir()
    data = site / "data"
    data.mkdir()
    (data / "numbered-objects.json").write_text(
        json.dumps(
            {
                "version": 1,
                "course_id": "debug-demo",
                "objects": [
                    {
                        "id": "main-theorem",
                        "family": "theorem",
                        "sequence": "theorem",
                        "label": "Theorem",
                        "number": "1",
                        "reference_text": "Theorem 1",
                        "anchor": "raya-object-main-theorem",
                        "title": "Main",
                        "source_path": "course/0_index.md",
                        "page_id": "index",
                        "page_title": "Index",
                        "page_output_path": "index.html",
                        "href": "#raya-object-main-theorem",
                        "style": "margin",
                    }
                ],
                "by_id": {"main-theorem": 0},
            }
        ),
        encoding="utf-8",
    )
    (site / "index.html").write_text(
        '<!doctype html><html><body><section class="raya-numbered-object" '
        'id="raya-object-main-theorem" data-object-id="main-theorem">'
        '<span class="raya-numbered-object-label">Theorem 1</span>'
        '</section><section class="raya-proof" id="raya-proof-proof-main">'
        '<div class="raya-proof-heading">Proof of Theorem 1.</div></section>'
        '</body></html>',
        encoding="utf-8",
    )
    for name in ("desktop-index.png", "mobile-index.png"):
        (debug / name).write_bytes(b"png")
    (debug / "summary.json").write_text(
        json.dumps(
            {
                "captures": [
                    {
                        "page": "index",
                        "url": "http://127.0.0.1/index.html",
                        "viewport": {"name": "desktop", "width": 1280, "height": 900},
                        "screenshot": str(debug / "desktop-index.png"),
                        "mathjax_container_count": 0,
                        "raw_tex_visible": False,
                        "raw_tex_markers": [],
                        "external_requests": [],
                        "horizontal_overflow": 0,
                        "numbered_content": {
                            "objects": [
                                {
                                    "id": "main-theorem",
                                    "anchor": "raya-object-main-theorem",
                                    "label": "Theorem 1",
                                    "title": "Main",
                                    "text": "Theorem 1",
                                }
                            ],
                            "references": [],
                            "proofs": [
                                {
                                    "id": "raya-proof-proof-main",
                                    "heading": "Proof of Theorem 1.",
                                    "target_text": "Theorem 1",
                                    "target_id": "",
                                }
                            ],
                        },
                    },
                    {
                        "page": "index",
                        "url": "http://127.0.0.1/index.html",
                        "viewport": {"name": "mobile", "width": 390, "height": 844},
                        "screenshot": str(debug / "mobile-index.png"),
                        "mathjax_container_count": 0,
                        "raw_tex_visible": False,
                        "raw_tex_markers": [],
                        "external_requests": [],
                        "horizontal_overflow": 0,
                        "numbered_content": {"objects": [], "references": [], "proofs": []},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    report = inspect_render_debug(site_dir=site, debug_dir=debug)

    assert report["ok"] is True, report["diagnostics"]
    numbered_check = next(
        check for check in report["checks"] if check["id"] == "numbered-content:index:desktop"
    )
    assert numbered_check["details"]["object_count"] == 1
    assert numbered_check["details"]["proof_targets"] == [
        {"proof_id": "raya-proof-proof-main", "target_id": "main-theorem", "target_text": "Theorem 1"}
    ]
    assert "Theorem 1" in (debug / "index.html").read_text(encoding="utf-8")
```

- [ ] **Step 6: Run the report enrichment test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_render_debug_report.py::test_render_debug_report_enriches_numbered_content_from_index -q
```

Expected: FAIL because no `numbered-content:*` check exists yet.

- [ ] **Step 7: Implement report enrichment**

In `packages/cli/src/raya_cli/render_debug_report.py`:

1. Add `_read_numbered_index(site_dir: Path, report: dict[str, Any]) -> dict[str, Any]`.
2. Call it from `inspect_render_debug()` after capture inspection:

```python
    numbered_index = _read_numbered_index(site_root, report)
    _inspect_numbered_content(captures, numbered_index, report)
```

3. Implement proof target enrichment by matching `capture["numbered_content"]["proofs"][*]["target_text"]` to numbered index `reference_text`.

Use this check shape:

```python
def _inspect_numbered_content(
    captures: list[dict[str, Any]],
    numbered_index: dict[str, Any],
    report: dict[str, Any],
) -> None:
    reference_to_id = {
        item.get("reference_text"): item.get("id")
        for item in numbered_index.get("objects", [])
        if isinstance(item, dict)
    }
    for capture in captures:
        page = str(capture.get("page", ""))
        viewport = capture.get("viewport")
        viewport_name = viewport.get("name") if isinstance(viewport, dict) else ""
        evidence = capture.get("numbered_content")
        if not isinstance(evidence, dict):
            _add_check(
                report,
                check_id=f"numbered-content:{page}:{viewport_name}",
                status="fail",
                path=report["summary_path"],
                message=f"missing numbered content evidence for {page} {viewport_name}",
                next_action="Regenerate render debug capture artifacts.",
            )
            continue
        proof_targets = []
        for proof in evidence.get("proofs", []):
            if not isinstance(proof, dict):
                continue
            target_text = proof.get("target_text") or ""
            target_id = proof.get("target_id") or reference_to_id.get(target_text, "")
            proof_targets.append(
                {
                    "proof_id": proof.get("id", ""),
                    "target_id": target_id,
                    "target_text": target_text,
                }
            )
        _add_check(
            report,
            check_id=f"numbered-content:{page}:{viewport_name}",
            status="pass",
            path=report["summary_path"],
            message=f"numbered content evidence for {page} {viewport_name}",
            details={
                "object_count": len(evidence.get("objects", [])),
                "reference_count": len(evidence.get("references", [])),
                "proof_count": len(evidence.get("proofs", [])),
                "proof_targets": proof_targets,
            },
        )
```

Update `_render_html_report()` if needed so check details are already visible through the existing details rendering. If details are not currently rendered, add a `<pre>` block with JSON details for each check that has details.

- [ ] **Step 8: Rerun focused render-debug tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_render_debug_report.py::test_render_debug_report_enriches_numbered_content_from_index -q
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary -q
```

Expected: PASS. Keep `summary.json` as raw browser capture evidence and
`report.json` as enriched inspection evidence.

- [ ] **Step 9: Add parity gate assertion**

Extend `test_render_debug_parity_gate_passes_on_render_fixture_copy` in `tests/e2e/test_render_debug_parity_gate.py`:

```python
    numbered_checks = [
        check for check in report_json["checks"]
        if check["id"].startswith("numbered-content:numbered-objects:")
    ]
    assert numbered_checks
    assert any(
        check["details"]["object_count"] >= 10
        and check["details"]["proof_count"] >= 3
        for check in numbered_checks
    )
```

- [ ] **Step 10: Run focused render-debug gate tests**

Run:

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_debug_artifacts_are_written_when_enabled tests/e2e/test_render_debug_parity_gate.py::test_render_debug_parity_gate_passes_on_render_fixture_copy -q
```

Expected: PASS.

- [ ] **Step 11: Commit render-debug evidence task**

Run:

```bash
git add packages/cli/src/raya_cli/render_debug.py packages/cli/src/raya_cli/render_debug_report.py tests/e2e/test_preview_static_read_path.py tests/e2e/test_render_debug_report.py tests/e2e/test_render_debug_parity_gate.py
git commit -m "Add numbered content render debug evidence"
```

## Task 4: Role Docs And Foundation Status

**Files:**
- Modify: `docs/foundation/17_rendering_execution_plan.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Modify if fixture text changes require it: `examples/courses/render-fixture/course/2_math_authoring/0_index.md`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write failing docs/fixture assertion**

Extend `test_render_fixture_builds_rich_static_pages` in `tests/contracts/test_static_builder.py` near existing role/docs assertions:

```python
    assert "numbered-content matrix" in numbered_objects_visible.lower()
    assert "render-debug evidence" in math_authoring_visible.lower()
```

If `math_authoring_visible` is not the right page for this assertion, add a docs-artifact assertion against the contributor or agent guide generated by the same test.

- [ ] **Step 2: Run the docs assertion to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages -q
```

Expected: FAIL because docs/fixture prose has not yet been updated.

- [ ] **Step 3: Update foundation status**

In `docs/foundation/17_rendering_execution_plan.md`, add a short status note under the current renderer/debugging section:

```markdown
Numbered content diagnostics are a current renderer quality pillar. CLI/build
diagnostics and `data/numbered-objects.json` remain authoritative; render-debug
adds screenshots, report JSON, and inspection HTML as evidence for labels,
anchors, references, proof targets, raw TeX leakage, external requests, and
browser-side MathJax absence.
```

- [ ] **Step 4: Update English role docs**

Add concise role-specific paragraphs:

Professor docs:

```markdown
Use the numbered-content matrix pattern when checking a course: include
theorem-like, equation, figure/table, and practice objects with stable IDs.
Build diagnostics should point to the source file and line for bad IDs,
unknown references, malformed directives, and proof targets that do not exist.
```

Contributor docs:

```markdown
When changing numbered content behavior, keep CLI/build diagnostics and
`data/numbered-objects.json` authoritative. Render-debug may summarize objects,
references, proof headings, and screenshots, but it is evidence for inspection,
not a replacement data contract.
```

Student docs:

```markdown
Numbered content appears as static labels and links, such as `Theorem 3.1`,
`Figure 3.1`, or `Activity 3.3`. Proof headings such as `Proof of Activity 3.3`
are generated during build; the browser does not calculate references.
```

Agent docs:

```markdown
For numbered-content failures, compare five surfaces in order: the source
directive, the build diagnostic, `data/numbered-objects.json`, the rendered
anchor/link text, and render-debug screenshots/report details.
```

- [ ] **Step 5: Update Spanish role docs**

Add equivalent Spanish prose, preserving technical identifiers in English:

```markdown
Para fallas de contenido numerado, compara en este orden: la directive source,
el diagnostico de build, `data/numbered-objects.json`, el anchor/link renderizado
y la evidencia de render-debug.
```

Use `prueba/pruebas` for proof prose, and keep IDs/family names/commands in English.

- [ ] **Step 6: Update fixture prose if needed**

Add a compact sentence to `examples/courses/render-fixture/course/3_numbered_objects/0_index.md`:

```markdown
This numbered-content matrix is fixture material for labels, references, proofs,
and render-debug evidence.
```

Add a compact sentence to `examples/courses/render-fixture/course/2_math_authoring/0_index.md` only if the failing test from Step 1 needs that page:

```markdown
Render-debug evidence should confirm that numbered content and math are static,
local, and free of browser-side MathJax conversion.
```

- [ ] **Step 7: Run focused docs/build test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages -q
```

Expected: PASS.

- [ ] **Step 8: Commit docs task**

Run:

```bash
git add docs/foundation/17_rendering_execution_plan.md docs/guides/en/professors/index.md docs/guides/en/contributors/index.md docs/guides/en/students/index.md docs/guides/en/agents/index.md docs/guides/es/profesores/index.md docs/guides/es/colaboradores/index.md docs/guides/es/estudiantes/index.md docs/guides/es/agentes/index.md examples/courses/render-fixture/course/2_math_authoring/0_index.md examples/courses/render-fixture/course/3_numbered_objects/0_index.md tests/contracts/test_static_builder.py
git commit -m "Document numbered content diagnostics"
```

## Task 5: Final Verification And Review

**Files:**
- No planned source edits unless verification exposes a bug.

- [ ] **Step 1: Run focused contract and e2e tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_numbered_objects.py tests/contracts/test_static_builder.py tests/e2e/test_render_debug_report.py -q
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_numbered_objects_are_static_and_local tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary tests/e2e/test_render_debug_parity_gate.py::test_render_debug_parity_gate_passes_on_render_fixture_copy -q
```

Expected: PASS.

- [ ] **Step 2: Run render-debug parity gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS and output includes `check-render-debug: passed`.

- [ ] **Step 3: Run host archive gate**

Run:

```bash
./scripts/check.sh
```

Expected: PASS with final `check: passed`.

- [ ] **Step 4: Run Docker reference gate**

Run:

```bash
./scripts/check-docker.sh
```

Expected: PASS with final `check-docker: passed`.

- [ ] **Step 5: Request final code review**

Use `superpowers:requesting-code-review` with:

- base SHA: commit before Task 1;
- head SHA: current `HEAD`;
- description: numbered-content diagnostics, fixture matrix, render-debug evidence, and role docs;
- requirements: design spec at `docs/superpowers/specs/2026-06-16-numbered-content-diagnostics-design.md` and this plan.

If the reviewer finds Critical or Important issues, fix them with TDD and rerun the relevant focused tests plus any affected gates.

- [ ] **Step 6: Commit final fixes if review requires them**

If review fixes were needed:

```bash
git status --short
git add packages/cli/src/raya_cli/render_debug.py packages/cli/src/raya_cli/render_debug_report.py packages/schema/src/raya_schema/numbered_objects.py packages/static/src/raya_static/numbered_objects.py tests/contracts/test_numbered_objects.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py tests/e2e/test_render_debug_report.py tests/e2e/test_render_debug_parity_gate.py docs/foundation/17_rendering_execution_plan.md docs/guides/en/professors/index.md docs/guides/en/contributors/index.md docs/guides/en/students/index.md docs/guides/en/agents/index.md docs/guides/es/profesores/index.md docs/guides/es/colaboradores/index.md docs/guides/es/estudiantes/index.md docs/guides/es/agentes/index.md examples/courses/render-fixture/raya.yaml examples/courses/render-fixture/course/2_math_authoring/0_index.md examples/courses/render-fixture/course/3_numbered_objects/0_index.md
git commit -m "Polish numbered content diagnostics"
```

- [ ] **Step 7: Finish branch**

After review approval and fresh verification, use `superpowers:finishing-a-development-branch` and offer the user merge/push/keep/discard options.

## Self-Review

- Spec coverage: diagnostics, fixture coverage, render-debug evidence, EN/ES role docs, host and Docker gates are all represented by tasks.
- Authority boundary: CLI/build diagnostics and `data/numbered-objects.json` stay authoritative; render-debug is evidence only.
- Scope: no new object families, `data/proofs.json`, browser-side resolver, or browser-side MathJax are added.
- TDD: each implementation task starts with failing tests or a confirmation step that existing behavior already satisfies the new assertion.
- Verification: focused tests, render-debug gate, host gate, Docker gate, and final code review are included.
