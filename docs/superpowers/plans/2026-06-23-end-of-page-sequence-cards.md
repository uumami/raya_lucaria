# End-of-Page Sequence Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add static article-end Previous/Next cards generated from course order.

**Architecture:** Reuse the current static content model and sequence-link behavior. Add one renderer helper for sequence targets, one renderer helper for bottom card markup, CSS for responsive cards, focused contract/browser tests, and role documentation updates.

**Tech Stack:** Python 3.10 static renderer, pytest, Playwright e2e tests, local static CSS/JS only.

---

### Task 1: Contract Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add a helper to extract bottom card nav**

Add near `_article_connections_html`:

```python
def _article_sequence_cards_html(html_text: str) -> str:
    start = html_text.index('<nav class="raya-article-sequence-cards"')
    end = html_text.index("</nav>", start) + len("</nav>")
    return html_text[start:end]
```

- [ ] **Step 2: Extend the shell contract test**

In `test_static_builder_renders_collapsible_shell_controls_and_page_position`,
assert the root page has only a next bottom card, the middle page has previous
and next bottom cards, and the last render fixture page has only previous.

- [ ] **Step 3: Run the focused contract test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position -q
```

Expected: FAIL because `.raya-article-sequence-cards` does not exist yet.

### Task 2: Renderer Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add sequence-target calculation**

Add a helper beside `_sequence_links()` that returns previous/next target data
from `content_model.pages`, including relative href, title, one-based page
index, and total page count.

- [ ] **Step 2: Render bottom cards**

Add `_render_article_sequence_cards(page, content_model)` and include its output
after `article_connections_html` in `_render_page()`.

- [ ] **Step 3: Run the focused contract test and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position -q
```

Expected: PASS.

### Task 3: Responsive CSS and Browser Regression

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add a browser test**

Add a test that previews `examples/courses/render-fixture`, opens
`/static-path/index.html`, scrolls to `.raya-article-sequence-cards`, checks the
previous and next card hrefs, checks no horizontal overflow on desktop and
mobile viewports, and confirms ArrowRight still navigates to
`/math-authoring/index.html`.

- [ ] **Step 2: Run the browser test and verify RED or style gap**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_end_of_page_sequence_cards_are_static_and_responsive -q
```

Expected before CSS: fail if cards are missing or overflow; after renderer markup
exists, it may fail only on missing layout classes.

- [ ] **Step 3: Add card CSS**

Style `.raya-article-sequence-cards`, `.raya-sequence-card`,
`.raya-sequence-card-kicker`, `.raya-sequence-card-title`, and
`.raya-sequence-card-meta` as a responsive two-card grid with one-column
fallback and visible focus state.

- [ ] **Step 4: Run browser regression and keyboard test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_end_of_page_sequence_cards_are_static_and_responsive tests/e2e/test_preview_static_read_path.py::test_render_fixture_keyboard_shortcuts_move_between_sequence_pages -q
```

Expected: PASS.

### Task 4: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`

- [ ] **Step 1: Update renderer contract**

Document article-end sequence cards as generated structural navigation.

- [ ] **Step 2: Update role docs**

Tell students the cards are static course-order links. Tell professors and
contributors that the cards come from authored course order and are not authored
separately. Tell agents to verify bottom cards, static links, no external
requests, and no progress/recommendation language.

- [ ] **Step 3: Run documentation contract tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py -q
```

Expected: PASS.

### Task 5: Review, Full Verification, Commit, Push

**Files:**
- Review all modified files.

- [ ] **Step 1: Request code review**

Use `superpowers:requesting-code-review` and independent review agents for
renderer behavior, UX/accessibility, and docs/contract consistency.

- [ ] **Step 2: Run focused renderer gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS.

- [ ] **Step 3: Run host archive gate**

Run:

```bash
./scripts/check.sh
```

Expected: PASS.

- [ ] **Step 4: Run Docker gate**

Run:

```bash
./scripts/check-docker.sh
```

Expected: PASS.

- [ ] **Step 5: Commit and push**

Run:

```bash
git status --short
git add docs/superpowers/specs/2026-06-23-end-of-page-sequence-cards-design.md docs/superpowers/plans/2026-06-23-end-of-page-sequence-cards.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/agents/index.md docs/guides/en/professors/index.md docs/guides/en/contributors/index.md docs/guides/es/estudiantes/index.md docs/guides/es/agentes/index.md docs/guides/es/profesores/index.md docs/guides/es/colaboradores/index.md
git commit -m "Add end-of-page sequence cards"
git push origin new_rayalucaria
```

Expected: commit pushed to `origin/new_rayalucaria`.
