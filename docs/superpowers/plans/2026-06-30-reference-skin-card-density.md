# Reference Skin And Card Density Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make existing skin `tokens.density` visibly control repeated discovery card density without shrinking the authored article reading surface, and remove the legacy browser-side skin override path because this loop touches skin authority.

**Architecture:** Keep skin profile schema unchanged. Emit additional semantic density CSS variables from `packages/static/src/raya_static/skins.py` and consume them in repeated workspace cards, controls, chips, and action links in `packages/static/src/raya_static/rendering.py`. Use browser e2e coverage on a compact EVA Unit 02-derived render fixture to prove card density changes while static-path constraints remain intact.

**Tech Stack:** Python 3.10, pytest, Playwright/Chromium, Glintstone static renderer CSS, existing YAML skin profiles.

---

## File Map

- Modify `tests/e2e/test_preview_static_read_path.py`: add RED browser coverage for compact density card styling on Practice, Tasks, and Schedule workspace cards.
- Modify `tests/contracts/test_static_skins.py`: require skin CSS to stay source-selected without `data-raya-skin-override` selectors.
- Modify `tests/contracts/test_static_builder.py`: require default student pages to omit skin override scripts and Skin toolbar commands.
- Modify `packages/static/src/raya_static/skins.py`: add card/control density variables to `DENSITY_SPACING` output.
- Modify `packages/static/src/raya_static/builder.py`: stop writing and including browser skin override scripts and commands.
- Modify `packages/static/src/raya_static/rendering.py`: apply the new variables to repeated discovery cards, chips, controls, and action links.
- Inspect and maybe update `docs/guides/en/` and `docs/guides/es/`: role docs should mention density changes workspace card/control density without changing source authority or reading comfort controls.
- Update `docs/superpowers/course-first-ux-goal.md`: record evidence and next handoff only after review and gates pass.

## Task 1: Add RED Browser Regression

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add a compact skin helper and test**

Add a helper near existing render-fixture helpers:

```python
def _select_compact_eva_skin(course: Path) -> None:
    source_skin = course / "skins" / "eva-unit-02.yaml"
    compact_skin = course / "skins" / "eva-unit-02-compact.yaml"
    compact_skin.write_text(
        source_skin.read_text(encoding="utf-8")
        .replace("id: eva-unit-02", "id: eva-unit-02-compact")
        .replace("name: Eva Unit 02", "name: Eva Unit 02 Compact")
        .replace("  density: comfortable", "  density: compact"),
        encoding="utf-8",
    )
    config = course / "raya.yaml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "  skin: eva-unit-02", "  skin: eva-unit-02-compact", 1
        ),
        encoding="utf-8",
    )
```

Add this test near the existing skin/page-brief/render-fixture browser tests:

```python
def test_compact_skin_makes_discovery_cards_dense_without_shrinking_article_text(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    _select_compact_eva_skin(course)
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    external_requests: list[str] = []
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        base_url = handle.base_url
        assert base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                probes = []
                for viewport in (
                    {"width": 1280, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    page.on(
                        "request",
                        lambda request: record_external_request(
                            request.url,
                            base_url,
                            external_requests,
                        ),
                    )
                    try:
                        for path, card_selector, action_selector in (
                            (
                                "_raya/practice/index.html",
                                ".raya-practice-object",
                                ".raya-practice-open",
                            ),
                            (
                                "_raya/tasks/index.html",
                                ".raya-task-object",
                                ".raya-task-open",
                            ),
                            (
                                "_raya/schedule/index.html",
                                ".raya-schedule-item",
                                ".raya-schedule-open",
                            ),
                        ):
                            page.goto(f"{base_url}/{path}", wait_until="networkidle")
                            _assert_no_horizontal_overflow(page)
                            page.wait_for_selector(card_selector)
                            probe = page.evaluate(
                                """({ cardSelector, actionSelector }) => {
                                  const card = document.querySelector(cardSelector);
                                  const action = document.querySelector(actionSelector);
                                  const style = getComputedStyle(card);
                                  const actionStyle = getComputedStyle(action);
                                  const bodyStyle = getComputedStyle(document.body);
                                  return {
                                    path: location.pathname,
                                    skin: document.body.dataset.rayaSkin || "",
                                    cardPaddingTop: Number.parseFloat(style.paddingTop || "0"),
                                    cardPaddingInline: Number.parseFloat(style.paddingLeft || "0"),
                                    actionMinHeight: Number.parseFloat(actionStyle.minHeight || "0"),
                                    bodyFontSize: Number.parseFloat(bodyStyle.fontSize || "0"),
                                    text: document.body.innerText,
                                    localKeys: Object.keys(localStorage),
                                    sessionKeys: Object.keys(sessionStorage),
                                  };
                                }""",
                                {
                                    "cardSelector": card_selector,
                                    "actionSelector": action_selector,
                                },
                            )
                            probes.append(probe)
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert probes
    for probe in probes:
        assert probe["skin"] == "eva-unit-02-compact"
        assert probe["cardPaddingTop"] <= 14
        assert probe["cardPaddingInline"] <= 14
        assert probe["actionMinHeight"] <= 34
        assert probe["bodyFontSize"] >= 16
        assert probe["localKeys"] == []
        assert probe["sessionKeys"] == []
        for forbidden in (
            "progress",
            "mastery",
            "recommend",
            "personal",
            "ranking",
            "score",
            "grade",
            "submit",
        ):
            assert forbidden not in probe["text"].lower()
    assert external_requests == []
```

Implementation note: the test also adds `_add_render_fixture_density_task()` so
Tasks and Schedule have representative official objects to measure.

- [x] **Step 2: Run the RED test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_compact_skin_makes_discovery_cards_dense_without_shrinking_article_text
```

Expected: FAIL because repeated cards still use hard-coded `1rem` padding and
action min-heights around `2.25rem`.

Observed RED: failed on `cardPaddingTop <= 14` with hard-coded card padding.

- [x] **Step 3: Add RED browser skin-authority cleanup coverage**

Updated existing contract/browser tests to require no
`data-raya-skin-override`, `skin-prepaint.js`, `skin-toggle.js`,
`raya:skin-override`, or Skin toolbar command in default generated student
pages.

Observed RED:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_skins.py::test_render_skin_css_is_deterministic_and_writes_token_variables \
  tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_uses_authored_skin_without_browser_override
```

Failed on the old override CSS selectors, generated skin scripts, and visible
Skin button.

## Task 2: Emit Card Density Variables

**Files:**
- Modify: `packages/static/src/raya_static/skins.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Extend density spacing output**

Update `DENSITY_SPACING` to include:

```python
"compact": {
    "page": "0.75rem",
    "panel": "0.75rem",
    "block": "0.85rem",
    "inline": "0.5rem",
    "card-padding": "0.72rem",
    "card-gap": "0.55rem",
    "card-action-min-height": "2rem",
    "chip-padding-block": "0.12rem",
    "chip-padding-inline": "0.42rem",
},
"comfortable": {
    "page": "1rem",
    "panel": "1rem",
    "block": "1rem",
    "inline": "0.75rem",
    "card-padding": "1rem",
    "card-gap": "0.75rem",
    "card-action-min-height": "2.25rem",
    "chip-padding-block": "0.15rem",
    "chip-padding-inline": "0.5rem",
},
"spacious": {
    "page": "1.5rem",
    "panel": "1.25rem",
    "block": "1.5rem",
    "inline": "1rem",
    "card-padding": "1.2rem",
    "card-gap": "1rem",
    "card-action-min-height": "2.5rem",
    "chip-padding-block": "0.2rem",
    "chip-padding-inline": "0.6rem",
},
```

This will emit `--raya-space-card-padding`, `--raya-space-card-gap`,
`--raya-space-card-action-min-height`, `--raya-space-chip-padding-block`, and
`--raya-space-chip-padding-inline` in `skin.css`.

## Task 3: Apply Density Variables To Workspace Cards

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Replace hard-coded repeated-card spacing**

Update repeated workspace styles so these selectors consume the new variables:

```css
.raya-search-results,
.raya-practice-results,
.raya-practice-group,
.raya-practice-grid,
.raya-tasks-results,
.raya-schedule-results {
  gap: var(--raya-space-card-gap);
}

.raya-search-results li,
.raya-practice-object,
.raya-task-object,
.raya-schedule-item {
  padding: var(--raya-space-card-padding);
}

.raya-search-result-section-list,
.raya-task-object-header,
.raya-task-actions,
.raya-task-tags,
.raya-schedule-item-header,
.raya-schedule-actions,
.raya-schedule-tags,
.raya-practice-object-header,
.raya-practice-actions {
  gap: var(--raya-space-inline);
}

.raya-search-result-sections {
  margin-top: var(--raya-space-card-gap);
  padding: var(--raya-space-card-gap) var(--raya-space-card-padding);
}

.raya-practice-actions,
.raya-task-actions,
.raya-schedule-actions,
.raya-search-result-actions {
  margin-top: var(--raya-space-card-gap);
}

.raya-practice-kind,
.raya-practice-authority,
.raya-task-kind,
.raya-task-authority,
.raya-task-tag,
.raya-schedule-date,
.raya-schedule-kind,
.raya-schedule-tag {
  padding: var(--raya-space-chip-padding-block) var(--raya-space-chip-padding-inline);
}

.raya-search-result-open,
.raya-search-result-graph,
.raya-search-result-practice,
.raya-search-result-tasks,
.raya-search-result-schedule,
.raya-practice-open,
.raya-practice-graph,
.raya-task-open,
.raya-task-graph,
.raya-schedule-open,
.raya-schedule-graph {
  min-height: var(--raya-space-card-action-min-height);
}
```

Keep article body, article headings, MathJax, and authored content font sizes
unchanged.

- [x] **Step 2: Run the focused browser test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_compact_skin_makes_discovery_cards_dense_without_shrinking_article_text
```

Expected: PASS.

Observed GREEN:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_compact_skin_makes_discovery_cards_dense_without_shrinking_article_text
```

Passed.

Review follow-up: adversarial review found that the first version measured
cards and action links but missed fixed control sizing. Expanded the browser
test to include Search plus control min-height, padding, and control-group gap
for Search, Practice, Tasks, and Schedule. Observed RED on fixed `2.5rem`
controls, then updated the shared workspace control CSS to use density
variables. Observed GREEN on the expanded test.

## Task 3A: Remove Browser Skin Override Path

**Files:**
- Modify: `packages/static/src/raya_static/skins.py`
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Keep skin CSS source-selected only**

Removed `data-raya-skin-override` selectors from `render_skin_css()`.

- [x] **Step 2: Stop writing and including override scripts**

Removed `skin-prepaint.js`, `skin-toggle.js`, their builder output writes, and
their reader-page script tags.

- [x] **Step 3: Remove the Skin toolbar command**

Removed the generated Skin command from the reader comfort toolbar. Text size
and OpenDyslexic controls remain as reading comfort preferences.

- [x] **Step 4: Run focused cleanup coverage**

Observed GREEN:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_skins.py::test_render_skin_css_is_deterministic_and_writes_token_variables \
  tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_uses_authored_skin_without_browser_override \
  tests/e2e/test_preview_static_read_path.py::test_compact_skin_makes_discovery_cards_dense_without_shrinking_article_text
```

Passed.

Observed GREEN after review fix: same focused browser set passed again in
`6 passed`.

## Task 4: Focused Regression And Role Docs

**Files:**
- Test: `tests/e2e/test_preview_static_read_path.py`
- Inspect/modify: `docs/guides/en/agents/index.md`
- Inspect/modify: `docs/guides/en/contributors/index.md`
- Inspect/modify: `docs/guides/en/professors/index.md`
- Inspect/modify: `docs/guides/en/students/index.md`
- Inspect/modify: `docs/guides/es/agentes/index.md`
- Inspect/modify: `docs/guides/es/colaboradores/index.md`
- Inspect/modify: `docs/guides/es/profesores/index.md`
- Inspect/modify: `docs/guides/es/estudiantes/index.md`

- [x] **Step 1: Run nearby browser coverage**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_compact_skin_makes_discovery_cards_dense_without_shrinking_article_text \
  tests/e2e/test_preview_static_read_path.py::test_discovery_command_bar_marks_current_workspace_without_overflow \
  tests/e2e/test_preview_static_read_path.py::test_discovery_workspaces_show_shared_page_focus_strip \
  tests/e2e/test_preview_static_read_path.py::test_preview_reader_page_brief_is_visible_static_and_responsive
```

Expected: PASS.

Observed GREEN:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_compact_skin_makes_discovery_cards_dense_without_shrinking_article_text \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_uses_authored_skin_without_browser_override \
  tests/e2e/test_preview_static_read_path.py::test_discovery_command_bar_marks_current_workspace_without_overflow \
  tests/e2e/test_preview_static_read_path.py::test_discovery_workspaces_show_shared_page_focus_strip \
  tests/e2e/test_preview_static_read_path.py::test_preview_reader_page_brief_is_visible_static_and_responsive \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading
```

Passed.

- [x] **Step 2: Review role docs**

Run:

```bash
rg -n "skin|density|compact|card|workspace|comfort|visual|tarjeta|densidad|compact" docs/guides/en docs/guides/es
```

Update role docs if they do not explain that source-selected skin density can
compact workspace cards/controls, while comfort controls remain reader
preferences and do not change source skin authority.

Updated English and Spanish agent, contributor/collaborator, professor, and
student role docs with this distinction.

## Task 5: Final Verification And Review

**Files:**
- Modify: `docs/superpowers/course-first-ux-goal.md`
- Modify: `docs/superpowers/plans/2026-06-30-reference-skin-card-density.md`

- [x] **Step 1: Run lightweight checks**

Run:

```bash
git diff --check
./scripts/check-hygiene.sh
```

Expected: both pass.

Observed GREEN: `git diff --check` passed and `./scripts/check-hygiene.sh`
reported `hygiene: passed`. Reran both after the review fix with the same
result.

- [x] **Step 2: Run render-debug**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS with `render-debug-report: passed`.

Observed GREEN: `./scripts/check-render-debug.sh` passed with
`render-debug-report: passed (129 check(s))`. Reran after the review fix with
the same result.

- [x] **Step 3: Request adversarial review**

Ask review to inspect:

- whether density remains profile-driven with no schema change;
- whether compact density affects repeated cards/controls but not article
  reading font scale;
- whether browser skin override behavior was not expanded;
- whether no storage, external requests, private paths, or learner-state
  language were introduced;
- whether role docs stay aligned in English and Spanish.

Observed review finding: compact density did not affect several repeated
workspace controls. Fixed by expanding coverage and applying density variables
to Search/Practice control groups, discovery control groups, Practice filters,
and Search/Practice/Tasks/Schedule input/button/chip sizing.

- [x] **Step 4: Run host gate**

Run:

```bash
./scripts/check.sh
```

Expected: PASS.

Observed: first host run exposed stale command-bar expectations for the removed
Skin button. Updated the test, confirmed the focused failure passed, then reran
`./scripts/check.sh`; result `check: passed`.

- [x] **Step 5: Run Docker gate after host gate completes**

Run:

```bash
./scripts/check-docker.sh
```

Expected: PASS. Run sequentially after the host gate.

Observed GREEN: `./scripts/check-docker.sh` passed after the host gate;
Docker pytest reported `555 passed in 1135.87s (0:18:55)`.

- [x] **Step 6: Update the goal ledger**

In `docs/superpowers/course-first-ux-goal.md`, mark **Reference skin and card
density** as the latest completed loop only after focused tests, render-debug,
host, Docker, role-doc impact review, and adversarial review pass. Set the next
recommended loop based on current evidence rather than inventing a new broader
scope.

Updated the ledger after focused tests, render-debug, host, Docker, role-doc
impact review, and adversarial review passed.
