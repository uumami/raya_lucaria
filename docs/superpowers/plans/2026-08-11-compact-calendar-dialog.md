# Compact Calendar Dialog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Calendar month cells compact and readable while exposing complete day details in one accessible dialog.

**Architecture:** Keep the normalized artifact and server agenda unchanged. Enhance the existing local Calendar renderer so it emits compact controls, then populate one native dialog from the embedded public payload; phone defaults to agenda and wide screens default to month.

**Tech Stack:** Python 3.10, static HTML/CSS/vanilla JavaScript, pytest, Playwright.

## Global Constraints

- Preserve `data/calendar.json`, no-JS agenda, local-only Calendar JS, and deployment-relative links.
- Wide month cells render at most two filtered event controls; `+N more` opens every omitted matching event.
- On narrow screens Agenda is the enhanced default; Month shows no wrapped titles.
- Use one accessible native `<dialog>`; Escape closes it before Calendar reset and focus returns to the opener.
- No nested interactive controls, no fetch/XHR/storage, no course-specific behavior.

---

### Task 1: Compact month controls and reusable detail dialog

**Files:**
- Modify: `packages/static/src/raya_static/calendar.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Test: `tests/contracts/test_static_builder.py`

**Interfaces:**
- Produces `renderCalendarDialog(events, opener)` and compact event buttons from the existing embedded Calendar payload.

- [ ] **Step 1: Write failing static tests**

```python
assert 'data-raya-calendar-event-open' in calendar_html
assert 'data-raya-calendar-overflow' in calendar_html
assert '<dialog id="raya-calendar-detail"' in calendar_html
```

- [ ] **Step 2: Verify red**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k compact_calendar_dialog`

Expected: FAIL because the grid clones full event articles and has no dialog.

- [ ] **Step 3: Implement minimal semantic controls**

```javascript
const MAX_WIDE_DAY_EVENTS = 2;
function openCalendarDetail(date, opener, selectedId) {
  detail.showModal();
  detail.dataset.rayaCalendarOpener = opener.id;
}
```

Render buttons, not links, for compact chips and overflow; render real page/graph anchors only inside the dialog. Use `textContent` and created DOM nodes for payload values.

- [ ] **Step 4: Verify green and commit**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k calendar`

```bash
git add packages/static tests/contracts/test_static_builder.py
git commit -m "Compact calendar month events"
```

### Task 2: Responsive dialog, filters, and keyboard behavior

**Files:**
- Modify: `packages/static/src/raya_static/calendar.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

**Interfaces:**
- Consumes compact controls from Task 1 and existing Calendar filters/month state.
- Produces deterministic wide/narrow initial views and dialog focus behavior.

- [ ] **Step 1: Write failing browser tests**

```python
page.get_by_role("button", name="Show 2 more events for Thursday, August 13, 2026").click()
assert page.get_by_role("dialog").is_visible()
page.keyboard.press("Escape")
assert page.get_by_role("dialog").is_hidden()
assert page.evaluate("document.activeElement.dataset.rayaCalendarOverflow !== undefined")
```

- [ ] **Step 2: Verify red**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k calendar_dialog`

Expected: FAIL because the dialog/focus contract does not exist.

- [ ] **Step 3: Implement dialog-first Escape and responsive CSS**

```css
@media (max-width: 700px) {
  .raya-calendar-grid-event-title { display: none; }
  .raya-calendar-detail { inline-size: 100%; block-size: 100dvh; }
}
```

Close the dialog before Calendar Escape reset; calculate caps after filters; retain month/view on Clear; use one visible status and one visually hidden polite status.

- [ ] **Step 4: Verify wide/mobile/no-JS behavior and commit**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k calendar`

```bash
git add packages/static tests/e2e/test_preview_static_read_path.py
git commit -m "Add accessible calendar details"
```

### Task 3: Contract/docs and final verification

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `tests/contracts/test_documentation_surfaces.py`

- [ ] **Step 1: Write failing contract assertion**

```python
assert "accessible day-detail dialog" in renderer_contract
assert "Agenda is the enhanced default on narrow screens" in renderer_contract
```

- [ ] **Step 2: Verify red, document, verify green, and commit**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_documentation_surfaces.py -k calendar`

```bash
git add docs/foundation tests/contracts/test_documentation_surfaces.py
git commit -m "Document compact calendar details"
```

- [ ] **Step 3: Run release checks**

Run sequentially: `./scripts/check.sh`, `./scripts/check-docker.sh`, `./scripts/check-render-debug.sh`.

Expected: all pass before framework or course deployment.
