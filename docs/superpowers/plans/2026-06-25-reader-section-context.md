# Reader Section Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact current-section cue to reader pages so students can keep their place inside long articles.

**Architecture:** Reuse the generated page TOC and existing active-heading logic. The builder emits a small right-rail current-section component when a TOC exists; the shell updates it from the same active TOC link used today; CSS styles it as structural orientation, not progress.

**Tech Stack:** Python static builder, generated HTML/CSS, vanilla shell JavaScript, pytest contract tests, Playwright e2e tests.

---

## File Structure

- Modify `packages/static/src/raya_static/builder.py`: render the current-section rail component from existing `toc_html`.
- Modify `packages/static/src/raya_static/shell.py`: sync the current-section link when active heading changes.
- Modify `packages/static/src/raya_static/rendering.py`: style the component.
- Modify `tests/contracts/test_static_builder.py`: assert static markup and script hooks.
- Modify `tests/e2e/test_preview_static_read_path.py`: assert browser scroll updates the cue.
- Modify `docs/foundation/20_learning_renderer_contract.md`: document current-section semantics.
- Modify `docs/guides/en/students/index.md`, `docs/guides/en/agents/index.md`, `docs/guides/es/estudiantes/index.md`, and `docs/guides/es/agentes/index.md`: document learner use and agent verification.

## Task 1: Contract Markup And Script Hooks

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/shell.py`

- [ ] **Step 1: Write the failing contract assertions**

In `test_render_fixture_builds_rich_static_pages`, add:

```python
    assert 'class="raya-current-section"' in html
    assert 'data-raya-current-section' in html
    assert 'data-raya-current-section-link' in html
    assert 'href="#rich-static-baseline"' in html
```

In the shell script contract test that reads `shell.js`, add:

```python
    assert "currentSectionLink" in script_text
    assert "syncCurrentSection" in script_text
    assert "data-raya-current-section-link" in script_text
```

- [ ] **Step 2: Run the contract tests to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource -q
```

Expected: FAIL because the current-section component and shell hook do not exist.

- [ ] **Step 3: Render current-section markup**

In `packages/static/src/raya_static/builder.py`, add a helper near `_render_page_contents_rail`:

```python
def _render_current_section_rail(toc_html: str) -> str:
    if not toc_html:
        return ""
    first_link = re.search(r'<a href="([^"]+)">([^<]+)</a>', toc_html)
    if first_link is None:
        return ""
    href = first_link.group(1)
    label = first_link.group(2)
    return "\n".join(
        [
            '<div class="raya-current-section" data-raya-current-section>',
            '<span class="raya-current-section-label">Current section</span>',
            (
                '<a class="raya-current-section-link" '
                'data-raya-current-section-link '
                'aria-live="polite" '
                f'href="{html.escape(href, quote=True)}">'
                f"{html.escape(label)}"
                "</a>"
            ),
            "</div>",
        ]
    )
```

Then include `_render_current_section_rail(toc_html)` immediately before `_render_page_contents_rail(toc_html)` in `_render_learning_rail`.

- [ ] **Step 4: Add shell hook**

In `packages/static/src/raya_static/shell.py`, define:

```javascript
  const currentSectionLink = document.querySelector("[data-raya-current-section-link]");
```

After `updateActiveHeading()` chooses `active`, call:

```javascript
    syncCurrentSection(active.link);
```

Add:

```javascript
  function syncCurrentSection(activeLink) {
    if (!currentSectionLink || !activeLink) {
      return;
    }
    const href = activeLink.getAttribute("href") || "";
    currentSectionLink.setAttribute("href", href);
    currentSectionLink.textContent = activeLink.textContent || "Current section";
  }
```

- [ ] **Step 5: Run the contract tests to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource -q
```

Expected: PASS.

## Task 2: Browser Behavior And Styling

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/shell.py`

- [ ] **Step 1: Write failing e2e assertions**

In `test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading`, after the existing `#worked-example` active-heading assertion, add:

```python
                    current_section = page.evaluate(
                        """() => ({
                          href: document
                            .querySelector('[data-raya-current-section-link]')
                            ?.getAttribute('href'),
                          text: document
                            .querySelector('[data-raya-current-section-link]')
                            ?.textContent
                            ?.trim(),
                        })"""
                    )
                    assert current_section["href"] == "#worked-example"
                    assert current_section["text"] == "Worked example"
```

After scrolling to `#1-numeric-heading`, add:

```python
                    page.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-current-section-link]')
                          ?.getAttribute('href') === '#1-numeric-heading'"""
                    )
```

- [ ] **Step 2: Run e2e to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
```

Expected: FAIL until the current-section markup and shell sync exist.

- [ ] **Step 3: Add CSS**

In `packages/static/src/raya_static/rendering.py`, near `.raya-page-toc` styles, add:

```css
.raya-current-section {
  border: 1px solid var(--raya-color-border);
  background: var(--raya-color-surface);
  padding: 0.65rem 0.75rem;
  margin: 0 0 0.75rem;
}
.raya-current-section-label {
  display: block;
  color: var(--raya-color-text-muted);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0;
  margin-bottom: 0.25rem;
}
.raya-current-section-link {
  color: var(--raya-color-accent);
  font-weight: 700;
  text-decoration-thickness: 0.08em;
  text-underline-offset: 0.16em;
}
.raya-current-section-link:focus-visible {
  outline: 2px solid var(--raya-color-accent);
  outline-offset: 3px;
}
```

- [ ] **Step 4: Run e2e to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
```

Expected: PASS.

## Task 3: Docs, Review, Verification, Commit

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update docs**

Update the right learning rail contract to say it may show the current article section derived from generated page headings and active TOC links. Update role docs to describe it as structural orientation only, not progress.

- [ ] **Step 2: Request review**

Ask an independent review agent to inspect the changes for static-boundary, accessibility, and test coverage issues.

- [ ] **Step 3: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
./scripts/check-render-debug.sh
```

Expected: PASS.

- [ ] **Step 4: Run full host gate**

Run:

```bash
./scripts/check.sh
```

Expected: PASS.

- [ ] **Step 5: Commit and push**

Run:

```bash
git add docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/agents/index.md docs/guides/es/estudiantes/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/shell.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/superpowers/specs/2026-06-25-reader-section-context-design.md docs/superpowers/plans/2026-06-25-reader-section-context.md
git commit -m "Add reader section context"
git push origin new_rayalucaria
```

Expected: branch is clean and pushed.

## Self-Review

- Spec coverage: markup, active-heading sync, styling, docs, review, and verification are covered.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: `data-raya-current-section-link`, `currentSectionLink`, and `syncCurrentSection` are named consistently.
