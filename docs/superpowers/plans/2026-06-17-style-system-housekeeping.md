# Style System Housekeeping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Codify the existing course/section skin framework as a coherent style guide while cleaning only style-adjacent drift and fixing small contract gaps found by audit.

**Architecture:** Keep the current Glintstone skin architecture: `skins/<id>.yaml` defines semantic tokens, `render.skin` and `course/**/_raya/skin.yaml` select profiles, `skin.css` emits variables, and pages activate skins with `data-raya-skin`. The loop is split into an audit task, a docs/style-guide task, a small test/contract task if gaps are found, and focused verification. No new theme engine, external fonts, arbitrary CSS, page-level override implementation, or browser-side skin resolver is introduced.

**Tech Stack:** Python 3.10, `raya_static.skins`, PyYAML, pytest, Markdown role docs, Raya fixture courses, Superpowers workflow.

---

## File Structure

- Modify: `docs/foundation/17_rendering_execution_plan.md`
  - Strengthen the authoritative skin/style guide contract and non-goals.
- Modify: `docs/guides/en/professors/index.md`
  - Add clearer copyable examples and authoring guidance for course and section skins.
- Modify: `docs/guides/es/profesores/index.md`
  - Spanish counterpart to professor guidance, keeping existing ASCII/no-accent style.
- Modify: `docs/guides/en/contributors/index.md`
  - Add contributor expectations for token validation, tests, and generated resources.
- Modify: `docs/guides/es/colaboradores/index.md`
  - Spanish counterpart to contributor guidance.
- Modify: `docs/guides/en/agents/index.md`
  - Tighten debugging order for skin selectors, skin profiles, diagnostics, generated CSS, body attributes, and render-debug evidence.
- Modify: `docs/guides/es/agentes/index.md`
  - Spanish counterpart to agent guidance.
- Modify: `docs/guides/en/students/index.md`
  - Clarify that visual skins do not change source truth, labels, links, numbered object identity, or official content.
- Modify: `docs/guides/es/estudiantes/index.md`
  - Spanish counterpart to student guidance.
- Modify if audit finds a real gap: `examples/courses/render-fixture/raya.yaml`
  - Ensure fixture skin selection is clear enough for rendered docs and tests.
- Modify if audit finds a real gap: `examples/courses/render-fixture/skins/*.yaml`
  - Improve example profile names/tokens only within current contract.
- Modify if audit finds a real gap: `tests/contracts/test_static_skins.py`
  - Add or clean focused tests for documented contract rules.
- Do not modify: `packages/static/src/raya_static/skins.py` unless a failing test proves a documented rule is not enforced.
- Do not create: any `src/eleventy`, theme-engine, browser-side resolver, external-font, or arbitrary-CSS surface.

## Task 1: Audit Current Style Surfaces

**Files:**
- Read only:
  - `docs/foundation/17_rendering_execution_plan.md`
  - `docs/guides/en/professors/index.md`
  - `docs/guides/es/profesores/index.md`
  - `docs/guides/en/contributors/index.md`
  - `docs/guides/es/colaboradores/index.md`
  - `docs/guides/en/agents/index.md`
  - `docs/guides/es/agentes/index.md`
  - `docs/guides/en/students/index.md`
  - `docs/guides/es/estudiantes/index.md`
  - `examples/courses/render-fixture/raya.yaml`
  - `examples/courses/render-fixture/skins/warm-academic.yaml`
  - `examples/courses/render-fixture/skins/practice-lab.yaml`
  - `examples/courses/render-fixture/course/4_reader_ux/_raya/skin.yaml`
  - `tests/contracts/test_static_skins.py`
  - `packages/static/src/raya_static/skins.py`

- [ ] **Step 1: Search style and skin guidance**

Run:

```bash
rg -n "skin|theme|style guide|style system|render\\.skin|_raya/skin|skins/|data-raya-skin|skin.css|font|density|contrast|arbitrary CSS|external fonts|browser-side skin" \
  docs/foundation docs/guides examples/courses/render-fixture tests/contracts/test_static_skins.py packages/static/src/raya_static/skins.py \
  -g '!docs/artifact/**' -g '!examples/**/artifact/**'
```

Expected: output identifies the current skin contract surfaces. Any stale
reference to old theme systems outside explicit future/non-goal context should
be recorded as a doc cleanup candidate.

- [ ] **Step 2: Compare docs against implemented constants**

Run:

```bash
rg -n "REQUIRED_COLOR_TOKENS|REQUIRED_FONT_TOKENS|ALLOWED_DENSITIES|ALLOWED_FONT_STACKS|CONTRAST|contrast|text on page|accent" packages/static/src/raya_static/skins.py
```

Expected: implemented constants match the design contract:
`page`, `surface`, `text`, `muted`, `accent`, `accent_soft`, `border`,
`success`, `warning`, `danger`; fonts `body`, `heading`, `mono`; densities
`comfortable`, `compact`, `spacious`; and system/local font stacks only.

- [ ] **Step 3: Record audit findings in worker final message**

Do not create a separate audit file. In the worker final message, list:

```text
Docs to update:
- docs/foundation/17_rendering_execution_plan.md: exact missing or stale style rule

Tests or fixtures to update:
- tests/contracts/test_static_skins.py: exact missing assertion or "none"

No-change confirmations:
- no arbitrary CSS: already covered by tests/contracts/test_static_skins.py
```

Expected: a concrete list that drives Tasks 2 and 3. If no renderer/test gap is
found, Task 3 should be docs/test cleanup only.

## Task 2: Codify Style Guide In Foundation And Role Docs

**Files:**
- Modify: `docs/foundation/17_rendering_execution_plan.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`

- [ ] **Step 1: Update foundation skin contract**

Edit `docs/foundation/17_rendering_execution_plan.md` in the existing Skin
profiles bullet. Preserve the current meaning and add concise style-guide
details:

```markdown
  Skin IDs use lowercase letters, digits, and hyphens. A course-local skin file
  name must match its `id`; for example `skins/warm-academic.yaml` contains
  `id: warm-academic`. `render.skin` and `_raya/skin.yaml` select profiles;
  selector files do not define token values. V1 skin tokens are semantic:
  color tokens `page`, `surface`, `text`, `muted`, `accent`, `accent_soft`,
  `border`, `success`, `warning`, and `danger`; font tokens `body`, `heading`,
  and `mono`; and density `comfortable`, `compact`, or `spacious`.
```

Expected: the foundation page names the exact tokens and distinguishes profile
definitions from selectors.

- [ ] **Step 2: Update professor authoring examples**

In `docs/guides/en/professors/index.md`, replace or extend the existing skin
paragraph so it explicitly names where each snippet lives. The resulting prose
should include this content:

````markdown
Put the course default in `raya.yaml`:

```yaml
render:
  skin: warm-academic
```

Put profile tokens in `skins/warm-academic.yaml`:
````

Keep the existing full YAML profile example. After the section selector example,
add:

```markdown
The selector file does not define colors or fonts; it only names a profile that
already exists under `skins/`.
```

Mirror the same content in `docs/guides/es/profesores/index.md` using the
existing Spanish ASCII style:

```markdown
Pon el default del curso en `raya.yaml`:
Pon los tokens del perfil en `skins/warm-academic.yaml`:
El selector no define colores ni fonts; solo nombra un perfil que ya existe bajo `skins/`.
```

Expected: professors/profesores can copy each snippet and know the file path.

- [ ] **Step 3: Update contributor validation guidance**

In `docs/guides/en/contributors/index.md`, extend the skin paragraph with:

```markdown
When changing this contract, keep docs aligned with
`REQUIRED_COLOR_TOKENS`, `REQUIRED_FONT_TOKENS`, `ALLOWED_DENSITIES`, and
`ALLOWED_FONT_STACKS` in `packages/static/src/raya_static/skins.py`. Tests
should cover unknown selectors, duplicate IDs, filename/id mismatches,
unsupported token fields, malformed colors, low contrast, invalid density,
unsafe fonts, generated `skin.css`, and nearest-section inheritance.
```

Mirror in `docs/guides/es/colaboradores/index.md` with Spanish prose and the
same technical identifiers.

Expected: contributors/collaborators have a direct implementation-to-docs
checklist.

- [ ] **Step 4: Update agent debugging guidance**

In `docs/guides/en/agents/index.md`, extend the skin debugging paragraph with:

```markdown
When a skin issue appears, first classify whether the source is a selector
problem, a profile-token problem, generated CSS output, or a rendered-page
activation problem. Do not infer skin state from screenshots alone; compare
the source selector, loaded profile, diagnostics, `skin.css`, `data-raya-skin`,
and render-debug report.
```

Mirror in `docs/guides/es/agentes/index.md`.

Expected: agents have an ordered diagnostic workflow, not just a list of files.

- [ ] **Step 5: Update student presentation guidance**

In `docs/guides/en/students/index.md`, add one sentence to the existing skin
paragraph:

```markdown
If two sections look different, use the page title, links, and labels as the
source of course meaning; the skin is only visual emphasis.
```

Mirror in `docs/guides/es/estudiantes/index.md`:

```markdown
Si dos secciones se ven diferentes, usa el titulo de pagina, enlaces y labels
como significado del curso; la skin solo es enfasis visual.
```

Expected: students are not told to treat visual skin as content authority.

- [ ] **Step 6: Run docs whitespace and hygiene checks**

Run:

```bash
git diff --check -- \
  docs/foundation/17_rendering_execution_plan.md \
  docs/guides/en/professors/index.md \
  docs/guides/es/profesores/index.md \
  docs/guides/en/contributors/index.md \
  docs/guides/es/colaboradores/index.md \
  docs/guides/en/agents/index.md \
  docs/guides/es/agentes/index.md \
  docs/guides/en/students/index.md \
  docs/guides/es/estudiantes/index.md
scripts/check-hygiene.sh
```

Expected: no whitespace output and `hygiene: passed`.

- [ ] **Step 7: Commit docs**

Run:

```bash
git add \
  docs/foundation/17_rendering_execution_plan.md \
  docs/guides/en/professors/index.md \
  docs/guides/es/profesores/index.md \
  docs/guides/en/contributors/index.md \
  docs/guides/es/colaboradores/index.md \
  docs/guides/en/agents/index.md \
  docs/guides/es/agentes/index.md \
  docs/guides/en/students/index.md \
  docs/guides/es/estudiantes/index.md
git commit -m "Codify skin style guide"
```

Expected: commit succeeds with only the listed docs.

## Task 3: Patch Small Skin Contract Gaps Found By Audit

**Files:**
- Modify only if needed: `tests/contracts/test_static_skins.py`
- Modify only if a failing test proves a gap: `packages/static/src/raya_static/skins.py`
- Modify only if docs/examples need clearer coverage:
  - `examples/courses/render-fixture/raya.yaml`
  - `examples/courses/render-fixture/skins/warm-academic.yaml`
  - `examples/courses/render-fixture/skins/practice-lab.yaml`
  - `examples/courses/render-fixture/course/4_reader_ux/_raya/skin.yaml`

- [ ] **Step 1: Check existing skin contract test coverage**

Run:

```bash
rg -n "unknown|duplicate|filename|unsupported|bad-color|low_contrast|density|font|nearest|render_skin_css|data-raya-skin|skin.css" \
  tests/contracts/test_static_skins.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py tests/e2e/test_render_debug_report.py
```

Expected: most style contract rules are already covered. Missing rules from
Task 1 audit become candidates for the next steps.

- [ ] **Step 2: If a documented rule lacks coverage, write one failing test**

Only perform this step if Task 1 identified a real gap. Example for unsafe
font coverage if missing:

```python
def test_skin_profile_rejects_unsafe_font_stack(tmp_path: Path) -> None:
    course = tmp_path
    source_root = course / "course"
    source_root.mkdir()
    skins_dir = course / "skins"
    skins_dir.mkdir()
    skin_path = skins_dir / "unsafe-font.yaml"
    skin_path.write_text(
        _skin_yaml("unsafe-font").replace(
            'body: "system-ui"',
            'body: "https://fonts.example/font.css"',
        ),
        encoding="utf-8",
    )
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        course,
        {"render": {"skin": "unsafe-font"}},
        source_root=source_root,
        report=report,
    )

    assert "unsafe-font" not in context.profiles
    assert context.default_skin_id == DEFAULT_SKIN_ID
    assert any(
        diagnostic.message == "Skin font token 'body' uses unsupported font stack"
        and diagnostic.field == "tokens.font.body"
        and diagnostic.path == skin_path
        for diagnostic in report.diagnostics
    )
```

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_skins.py::test_skin_profile_rejects_unsafe_font_stack -q
```

Expected before implementation: the test fails if the rule is not enforced, or
passes if the rule is already enforced. If it already passes, keep the test only
if it adds missing explicit coverage.

- [ ] **Step 3: Implement the smallest contract fix if a test fails**

Only edit `packages/static/src/raya_static/skins.py` if Step 2 proves a real
gap. The implementation must stay within the existing helpers and diagnostics.
For unsafe fonts, the existing `_validate_fonts()` helper should be extended or
confirmed, not replaced with a new font system.

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_skins.py -q
```

Expected: all skin contract tests pass.

- [ ] **Step 4: Clean obvious test duplication if touched**

If editing `tests/contracts/test_static_skins.py`, remove accidental duplicate
assertions in the touched area only. For example, keep one
`"tokens.color.page" in diagnostic.next_action` assertion in
`test_low_contrast_skin_profile_reports_error_and_is_not_loaded`.

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_skins.py -q
```

Expected: all skin contract tests pass.

- [ ] **Step 5: Commit any test/code/fixture changes**

If Task 3 changed files, run:

```bash
git add tests/contracts/test_static_skins.py packages/static/src/raya_static/skins.py examples/courses/render-fixture/raya.yaml examples/courses/render-fixture/skins/warm-academic.yaml examples/courses/render-fixture/skins/practice-lab.yaml examples/courses/render-fixture/course/4_reader_ux/_raya/skin.yaml
git commit -m "Tighten skin style contract"
```

Expected: commit includes only files actually changed. If Task 3 found no
enforcement or fixture gap, do not create an empty commit.

## Task 4: Focused Verification And Rendered Docs Check

**Files:**
- No planned edits.

- [ ] **Step 1: Run focused skin and docs checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_skins.py tests/contracts/test_static_builder.py -q
scripts/check-hygiene.sh
git diff --check HEAD~2..HEAD
```

Expected: pytest passes, hygiene passes, and diff check has no output.

- [ ] **Step 2: Run browser/static checks if renderer or fixture changed**

If Task 3 changed renderer code or render fixture files, run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_applies_course_and_section_skins -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_render_debug_report.py -q
```

Expected: tests pass and preserve local `skin.css`, active `data-raya-skin`,
and render-debug skin evidence.

- [ ] **Step 3: Build docs if role/foundation docs changed**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate docs
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build docs
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya artifacts inspect docs/artifact
```

Expected: validation, build, and inspection pass. Generated `docs/artifact/`
remains ignored and uncommitted.

- [ ] **Step 4: Decide full gate need**

Run full gates only if renderer code, validation contracts, or shared
verification behavior changed:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both pass and are run sequentially. If only docs changed, record that
full gates were not rerun because focused docs/skin checks covered the change.

## Task 5: Final Review, Push, And Report

**Files:**
- No planned edits.

- [ ] **Step 1: Request final code/repository review**

Dispatch a reviewer with:

```text
Review the style-system housekeeping loop. Requirements: no new theme engine,
no external fonts/CDN/browser-side skin resolver, docs align EN/ES role
surfaces, examples identify `raya.yaml`, `skins/<id>.yaml`, and
`course/**/_raya/skin.yaml`, and any contract gap has focused tests.
```

Expected: no Critical or Important findings. Fix valid findings before
continuing.

- [ ] **Step 2: Push branch**

Run:

```bash
git status --short --branch
git push origin new_rayalucaria
```

Expected: status is clean except ahead commits before push; push updates
`origin/new_rayalucaria`.

- [ ] **Step 3: Final report**

Report:

```text
style-system docs: updated paths
contract gaps fixed: yes/no, with commit if yes
focused tests: commands and pass/fail result
docs build: pass/fail result
full gates: rerun yes/no and why
branch: synced or ahead
```

Expected: final report distinguishes docs-only verification from renderer-code
verification and names any residual risks.
