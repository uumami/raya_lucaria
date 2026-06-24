# Discovery Active Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make generated Search and Practice workspaces inspectable by hover, focus, and keyboard while preserving the static renderer boundary.

**Architecture:** Reuse the existing generated static payloads and DOM hooks. Search already has an active-result model; extend it with pointer/focus activation. Practice gets the same transient active-object model, backed by generated `data-raya-practice-active` hooks, CSS, and browser tests.

**Tech Stack:** Python static builder, embedded vanilla JavaScript resources, pytest contract tests, Playwright-style e2e tests through the existing static-read-path suite.

---

### Task 1: Contract Tests For Active Hooks

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Test: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write failing contract assertions**

Add these assertions to the existing search and practice workspace tests:

```python
assert 'addEventListener("focusin"' in search_script
assert 'addEventListener("pointerenter"' in search_script
assert "setActiveResult(indexForResult(item))" in search_script

assert 'data-raya-practice-active="false"' in html
assert "function setActiveObject" in practice_script
assert 'data-raya-practice-active' in practice_script
assert 'event.key === "ArrowDown"' in practice_script
assert 'event.key === "ArrowUp"' in practice_script
assert 'querySelector(".raya-practice-open")' in practice_script
assert '.raya-practice-object[data-raya-practice-active="true"]' in css
```

- [ ] **Step 2: Run tests and confirm RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "search or practice"
```

Expected: FAIL because Practice active hooks and Search pointer/focus activation are missing.

### Task 2: Browser Tests For Inspection Behavior

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add failing Search inspection checks**

In the generated search workspace test, after narrowing to a known result, assert:

```python
result = page.locator('[data-raya-search-result="authoring-matrix"]')
result.hover()
expect(result).to_have_attribute("data-raya-search-active", "true")
expect(page.locator("[data-raya-search-context-title]")).to_contain_text("Authoring Matrix")

result.locator("a").first.focus()
expect(result).to_have_attribute("data-raya-search-active", "true")
expect(page.locator("[data-raya-search-context-meta]")).to_contain_text("Explicit links")
```

- [ ] **Step 2: Add failing Practice inspection checks**

In the official practice workspace test, assert:

```python
quiz = page.locator('[data-raya-practice-object="first-topic-quiz"]')
quiz.hover()
expect(quiz).to_have_attribute("data-raya-practice-active", "true")
expect(page.locator("[data-raya-practice-context-meta]")).to_contain_text("Quiz")

page.locator("#raya-practice-search").focus()
page.keyboard.press("ArrowDown")
expect(page.locator('[data-raya-practice-active="true"]')).to_have_count(1)
expect(page.locator("[data-raya-practice-context-title]")).not_to_contain_text("No visible")

active = page.locator('[data-raya-practice-active="true"]')
active_open_href = active.locator(".raya-practice-open").first.get_attribute("href")
page.keyboard.press("Enter")
expect(page).to_have_url(re.compile(re.escape(active_open_href.split("#")[0])))
```

Use the existing navigation/reset pattern in the test if it needs to return to `_raya/practice/index.html` before later assertions.

- [ ] **Step 3: Run tests and confirm RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "search_workspace or practice_workspace"
```

Expected: FAIL because hover/focus Practice active behavior is not implemented.

### Task 3: Implement Search Pointer And Focus Activation

**Files:**
- Modify: `packages/static/src/raya_static/search.py`
- Test: `tests/contracts/test_static_builder.py`, `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add visible-result index helper**

Add a helper near `visibleResults()`:

```javascript
function indexForResult(item) {
  return visibleResults().indexOf(item);
}
```

- [ ] **Step 2: Add per-result event listeners**

Before input event listeners, add:

```javascript
results.forEach((item) => {
  item.addEventListener("focusin", () => {
    const index = indexForResult(item);
    if (index >= 0) setActiveResult(index);
  });
  item.addEventListener("pointerenter", () => {
    const index = indexForResult(item);
    if (index >= 0) setActiveResult(index);
  });
});
```

- [ ] **Step 3: Run focused checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k search
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k search_workspace
```

Expected: PASS for Search active-context checks.

### Task 4: Implement Practice Active Object Model

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/practice.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Test: `tests/contracts/test_static_builder.py`, `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add generated active hook**

In the Practice object card markup, add:

```html
data-raya-practice-active="false"
```

- [ ] **Step 2: Add active state to Practice JavaScript**

In `practice.py`, add `let activeIndex = -1;` beside `activeType`, add `setActiveObject(nextIndex)`, and update `updateContext()` to use the active visible object first:

```javascript
let activeIndex = -1;

function setActiveObject(nextIndex) {
  const visible = visibleObjects();
  if (visible.length === 0) {
    activeIndex = -1;
  } else {
    activeIndex = Math.max(-1, Math.min(nextIndex, visible.length - 1));
  }
  objects.forEach((object) => {
    object.dataset.rayaPracticeActive = "false";
    object.setAttribute("data-raya-practice-active", "false");
  });
  if (activeIndex >= 0 && visible[activeIndex]) {
    visible[activeIndex].dataset.rayaPracticeActive = "true";
    visible[activeIndex].setAttribute("data-raya-practice-active", "true");
  }
  updateContext();
}

function bestContextObject(visible) {
  if (activeIndex >= 0 && visible[activeIndex]) {
    return visible[activeIndex];
  }
  return visible[0];
}
```

- [ ] **Step 3: Wire Practice pointer, focus, and keyboard**

Add:

```javascript
function indexForObject(object) {
  return visibleObjects().indexOf(object);
}

objects.forEach((object) => {
  object.addEventListener("focusin", () => {
    const index = indexForObject(object);
    if (index >= 0) setActiveObject(index);
  });
  object.addEventListener("pointerenter", () => {
    const index = indexForObject(object);
    if (index >= 0) setActiveObject(index);
  });
});
```

Update input/filter/clear behavior:

```javascript
input.addEventListener("input", () => {
  activeIndex = -1;
  render();
});
```

For `keydown`, handle:

```javascript
if (event.key === "ArrowDown") {
  event.preventDefault();
  const visible = visibleObjects();
  setActiveObject(visible.length === 0 ? -1 : (activeIndex + 1) % visible.length);
} else if (event.key === "ArrowUp") {
  event.preventDefault();
  const visible = visibleObjects();
  const next = activeIndex <= 0 ? visible.length - 1 : activeIndex - 1;
  setActiveObject(visible.length === 0 ? -1 : next);
} else if (event.key === "Enter" && activeIndex >= 0) {
  const visible = visibleObjects();
  const link = visible[activeIndex] ? visible[activeIndex].querySelector(".raya-practice-open") : null;
  if (link && link.href) {
    event.preventDefault();
    window.location.href = link.href;
  }
} else if (event.key === "Escape") {
  event.preventDefault();
  input.value = "";
  activeType = "all";
  activeIndex = -1;
  render();
}
```

- [ ] **Step 4: Add active object styling**

Add CSS:

```css
.raya-practice-object[data-raya-practice-active="true"] {
  border-color: var(--raya-accent-strong);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--raya-accent) 24%, transparent);
  transform: translateY(-1px);
}

.raya-practice-object[data-raya-practice-active="true"] .raya-practice-object-title {
  color: var(--raya-accent-strong);
}
```

- [ ] **Step 5: Run focused checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k practice
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k practice_workspace
```

Expected: PASS for Practice active-context checks.

### Task 5: Foundation And Role Docs

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update renderer contract**

State that Search and Practice context panels can follow transient active cards selected by hover, focus, or keyboard, and that active state is non-persistent static UI state.

- [ ] **Step 2: Update role docs**

Student docs should describe scanning Search/Practice cards and opening the owning page. Agent docs should describe verifying active-state hooks and confirming no storage/fetch/external requests.

- [ ] **Step 3: Run docs grep**

Run:

```bash
rg -n "active|focus|hover|keyboard|Search|Practice" docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/agents/index.md docs/guides/es/estudiantes/index.md docs/guides/es/agentes/index.md
```

Expected: Updated English and Spanish guidance appears in the intended role docs.

### Task 6: Full Verification, Review, Commit, Push

**Files:**
- Review all changed files.
- Test: full host and Docker gates.

- [ ] **Step 1: Run focused discovery tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "search or practice"
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "search_workspace or practice_workspace"
```

- [ ] **Step 2: Run render debug**

```bash
./scripts/check-render-debug.sh
```

- [ ] **Step 3: Run host archive gate**

```bash
./scripts/check.sh
```

- [ ] **Step 4: Run Docker archive gate**

```bash
./scripts/check-docker.sh
```

- [ ] **Step 5: Request code review**

Use `superpowers:requesting-code-review` and ask for a focused review of Search/Practice active context, static boundary, accessibility, and tests.

- [ ] **Step 6: Commit and push**

```bash
git status --short
git add docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/agents/index.md docs/guides/es/estudiantes/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/search.py packages/static/src/raya_static/practice.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/superpowers/plans/2026-06-24-discovery-active-context.md
git commit -m "Add discovery active context"
git push origin new_rayalucaria
```

---

## Plan Self-Review

- Spec coverage: Search pointer/focus, Practice active object, docs, static boundary, and tests are covered.
- Placeholder scan: no TODO/TBD/placeholders remain.
- Type consistency: hook names match the existing `data-raya-search-*` and `data-raya-practice-*` patterns.
