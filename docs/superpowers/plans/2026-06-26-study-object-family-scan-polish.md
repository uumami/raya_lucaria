# Study Object Family Scan Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make reader-page numbered objects and official practice objects easier to scan by adapting legacy component-family visual affordances to current reset renderer classes.

**Architecture:** Keep all behavior inside existing generated markup and `packages/static/src/raya_static/rendering.py` CSS. Add a Playwright regression against the render fixture, then implement skin-token-based CSS variables for numbered and official object families.

**Tech Stack:** Python static renderer, generated CSS, pytest, Playwright browser e2e, render fixture.

---

### Task 1: Browser Regression For Study Object Family Accents

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add failing browser test**

Add a test near the other render-fixture layout tests:

```python
def test_render_fixture_study_object_families_are_visually_distinct(
    tmp_path: Path,
) -> None:
    with _preview_course(RENDER_FIXTURE, tmp_path) as handle:
        with sync_playwright() as playwright:
            browser = _launch_browser(playwright)
            page = browser.new_page(viewport={"width": 1440, "height": 950})
            try:
                requests: list[str] = []
                page.on("request", lambda request: requests.append(request.url))
                page.goto(f"{handle.base_url}/reader-ux/index.html")
                page.wait_for_load_state("networkidle")
                metrics = page.evaluate(
                    """
                    () => {
                      const styleOf = (selector) => {
                        const node = document.querySelector(selector);
                        if (!node) {
                          return null;
                        }
                        const rect = node.getBoundingClientRect();
                        const style = getComputedStyle(node);
                        return {
                          background: style.backgroundColor,
                          borderLeft: style.borderLeftColor,
                          color: style.color,
                          height: rect.height,
                          width: rect.width,
                        };
                      };
                      return {
                        bodyScroll: document.documentElement.scrollWidth,
                        bodyClient: document.documentElement.clientWidth,
                        definitionBadge: styleOf('#raya-object-orthogonal-definition .raya-numbered-object-badge'),
                        problemBadge: styleOf('#raya-object-orthogonal-problem .raya-numbered-object-badge'),
                        officialCard: styleOf('.raya-official-card'),
                        officialQuiz: styleOf('.raya-official-quiz'),
                        officialCardKind: styleOf('.raya-official-card .raya-official-kind'),
                        officialQuizKind: styleOf('.raya-official-quiz .raya-official-kind'),
                      };
                    }
                    """
                )
            finally:
                browser.close()
    assert metrics["definitionBadge"] is not None
    assert metrics["problemBadge"] is not None
    assert metrics["officialCard"] is not None
    assert metrics["officialQuiz"] is not None
    assert metrics["officialCardKind"] is not None
    assert metrics["officialQuizKind"] is not None
    assert metrics["definitionBadge"]["background"] != metrics["problemBadge"]["background"]
    assert metrics["officialCard"]["borderLeft"] != metrics["officialQuiz"]["borderLeft"]
    assert metrics["officialCardKind"]["background"] != metrics["officialQuizKind"]["background"]
    assert metrics["definitionBadge"]["width"] >= 80
    assert metrics["definitionBadge"]["height"] >= 40
    assert metrics["officialCardKind"]["width"] >= 40
    assert metrics["officialCardKind"]["height"] >= 20
    assert metrics["bodyScroll"] <= metrics["bodyClient"] + 1
    assert not _external_requests(requests, handle.base_url)
```

- [x] **Step 2: Run test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_study_object_families_are_visually_distinct -q
```

Expected: FAIL because current official card and quiz objects share the same
computed accent and numbered scannable badges share the same background.

### Task 2: CSS Family Accent Implementation

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add numbered object family variables**

In the existing numbered-object CSS block, define default variables on
`.raya-numbered-object` and override them on family classes such as
`.raya-numbered-object--definition`, `--theorem`, `--proposition`,
`--corollary`, `--problem`, `--activity`, `--example`, `--remark`,
`--figure`, `--table`, and `--equation`.

- [x] **Step 2: Wire numbered object rules to variables**

Use those variables for borders, scannable badge background, badge label color,
header background, and focus outlines while keeping the existing scannable
layout and mobile stacking behavior.

- [x] **Step 3: Add official object type variables**

Define default variables on `.raya-official-object` and override them on
`.raya-official-card`, `.raya-official-quiz`, `.raya-official-assignment`,
`.raya-official-exam`, `.raya-official-project`, `.raya-official-task`, and
`.raya-official-example`. Prompt official objects use the default official
accent so the paragraph-level `.raya-official-prompt` class remains unambiguous.

- [x] **Step 4: Wire official object rules to variables**

Use the official variables for object left border, type chip background,
authority/reveal backgrounds, and focus outlines. Keep details/summary native
and do not add JavaScript.

- [x] **Step 5: Run focused browser test to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_study_object_families_are_visually_distinct -q
```

Expected: PASS.

### Task 3: Verification, Review, Commit, And Preview

**Files:**
- Create: `docs/superpowers/specs/2026-06-26-study-object-family-scan-polish-design.md`
- Create: `docs/superpowers/plans/2026-06-26-study-object-family-scan-polish.md`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Run focused regression set**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_study_object_families_are_visually_distinct tests/e2e/test_preview_static_read_path.py::test_rendered_surfaces_have_no_obvious_layout_overlap_at_viewports -q
```

- [x] **Step 2: Run render-debug parity gate**

Run:

```bash
./scripts/check-render-debug.sh
```

- [x] **Step 3: Request independent code review**

Ask an independent reviewer to check the diff against this design, with
particular attention to current renderer constraints and accidental legacy
behavior.

- [ ] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-study-object-family-scan-polish-design.md docs/superpowers/plans/2026-06-26-study-object-family-scan-polish.md packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git commit -m "Polish study object family scanning"
git push origin new_rayalucaria
```

- [ ] **Step 5: Refresh local preview**

Restart or verify the render fixture preview and provide the current URL:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --host 127.0.0.1 --port 46400
```

## Plan Self-Review

- The test proves actual browser-visible differences instead of relying only on
  CSS string checks.
- The implementation touches only current renderer CSS and existing tests.
- No plan step introduces new authoring syntax, schema fields, JavaScript
  state, external requests, or legacy runtime behavior.
