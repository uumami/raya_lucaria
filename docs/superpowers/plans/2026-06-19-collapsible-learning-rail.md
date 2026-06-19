# Collapsible Learning Rail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reset-native desktop collapse control for the right learning rail so readers can reclaim article width without losing orientation.

**Architecture:** The builder wraps existing rail panels in a rail header/body and adds explicit collapse/expand buttons. The shell script owns non-persistent rail-level state and focus safety. CSS narrows the right rail to a compact button on desktop while leaving mobile article-first layout unchanged.

**Tech Stack:** Python static renderer, generated HTML/CSS/JavaScript strings, pytest contract tests, Playwright e2e tests.

---

### Task 1: Contract And Browser Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing contract assertions**

Add assertions to `test_render_fixture_uses_static_learning_shell`:

```python
assert (
    '<aside id="raya-learning-rail" class="raya-learning-rail" '
    'aria-label="Learning context" data-raya-learning-rail="expanded">'
) in html
assert '<div id="raya-learning-rail-body" class="raya-learning-rail-body">' in html
assert 'data-raya-learning-rail-collapse' in html
assert 'data-raya-learning-rail-expand' in html
assert 'aria-controls="raya-learning-rail-body"' in html
```

Add required CSS hooks to `test_rich_css_defines_learning_shell_regions`:

```python
".raya-learning-rail-header",
".raya-learning-rail-body",
".raya-learning-rail-expand",
'[data-raya-learning-rail="collapsed"]',
```

- [ ] **Step 2: Write the failing browser test**

Add `test_render_fixture_learning_rail_collapses_to_compact_context_tab` to `tests/e2e/test_preview_static_read_path.py`. Use the render fixture preview, open `reader-ux/index.html` at `1280x900`, measure article and rail widths, click `[data-raya-learning-rail-collapse]`, and assert:

```python
collapsed = page.evaluate(
    """() => {
      const root = document.documentElement;
      const rail = document.querySelector('#raya-learning-rail');
      const body = document.querySelector('#raya-learning-rail-body');
      const article = document.querySelector('#raya-article');
      const expand = document.querySelector('[data-raya-learning-rail-expand]');
      return {
        rootState: root.dataset.rayaLearningRail,
        railState: rail?.dataset.rayaLearningRail,
        bodyHidden: body?.getAttribute('aria-hidden'),
        bodyInert: body?.inert,
        articleWidth: article?.getBoundingClientRect().width,
        railWidth: rail?.getBoundingClientRect().width,
        expandVisible: !!expand && getComputedStyle(expand).display !== 'none',
        expandExpanded: expand?.getAttribute('aria-expanded'),
      };
    }"""
)
assert collapsed["rootState"] == "collapsed"
assert collapsed["railState"] == "collapsed"
assert collapsed["bodyHidden"] == "true"
assert collapsed["bodyInert"] is True
assert collapsed["articleWidth"] > initial["articleWidth"]
assert collapsed["railWidth"] < 120
assert collapsed["expandVisible"] is True
assert collapsed["expandExpanded"] == "false"
```

Then click `[data-raya-learning-rail-expand]` and assert the rail returns to expanded state.

- [ ] **Step 3: Run tests to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell \
  tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_rail_collapses_to_compact_context_tab
```

Expected: fail because the new rail wrapper, controls, state, and CSS hooks do not exist yet.

### Task 2: Renderer Markup And CSS

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add rail wrapper markup**

Change `_render_learning_rail(...)` to render:

```python
return "\n".join(
    [
        (
            '<aside id="raya-learning-rail" class="raya-learning-rail" '
            'aria-label="Learning context" data-raya-learning-rail="expanded">'
        ),
        '<div class="raya-learning-rail-header">',
        '<p class="raya-region-title">Learning context</p>',
        (
            '<button class="raya-learning-rail-collapse" type="button" '
            'data-raya-learning-rail-collapse '
            'aria-controls="raya-learning-rail-body" '
            'aria-expanded="true" '
            'aria-label="Hide learning context">Hide context</button>'
        ),
        "</div>",
        '<div id="raya-learning-rail-body" class="raya-learning-rail-body">',
        body,
        "</div>",
        (
            '<button class="raya-learning-rail-expand" type="button" '
            'data-raya-learning-rail-expand '
            'aria-controls="raya-learning-rail-body" '
            'aria-expanded="true" '
            'aria-label="Show learning context">Context</button>'
        ),
        "</aside>",
    ]
)
```

- [ ] **Step 2: Add desktop collapsed CSS**

In `rendering.py`, add styles for:

```css
.raya-learning-rail-header { ... }
.raya-learning-rail-body { ... }
.raya-learning-rail-expand { display: none; ... }

@media (min-width: 901px) {
  .raya-learning-shell[data-raya-learning-rail="collapsed"] {
    grid-template-columns: minmax(12rem, 15rem) minmax(0, 1fr) 3.25rem;
  }
  .raya-learning-rail[data-raya-learning-rail="collapsed"] {
    padding: var(--raya-space-2);
    align-items: center;
  }
  .raya-learning-rail[data-raya-learning-rail="collapsed"] .raya-learning-rail-header,
  .raya-learning-rail[data-raya-learning-rail="collapsed"] .raya-learning-rail-body {
    display: none;
  }
  .raya-learning-rail[data-raya-learning-rail="collapsed"] .raya-learning-rail-expand {
    display: inline-flex;
  }
}
```

Use existing skin tokens and avoid vertical wrapped words.

- [ ] **Step 3: Run contract tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell \
  tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions
```

Expected: contract tests pass; browser test may still fail until shell behavior exists.

### Task 3: Shell Behavior And Contract Docs

**Files:**
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `docs/foundation/20_learning_renderer_contract.md`

- [ ] **Step 1: Add rail-level state controller**

In `shell.py`, select:

```javascript
const learningRail = document.querySelector("#raya-learning-rail");
const learningRailBody = document.querySelector("#raya-learning-rail-body");
const learningRailCollapse = document.querySelector("[data-raya-learning-rail-collapse]");
const learningRailExpand = document.querySelector("[data-raya-learning-rail-expand]");
```

Add:

```javascript
function setLearningRailExpanded(nextExpanded) {
  if (!learningRail || !learningRailBody) return;
  root.dataset.rayaLearningRail = nextExpanded ? "expanded" : "collapsed";
  shell.dataset.rayaLearningRail = nextExpanded ? "expanded" : "collapsed";
  learningRail.dataset.rayaLearningRail = nextExpanded ? "expanded" : "collapsed";
  learningRailBody.setAttribute("aria-hidden", nextExpanded ? "false" : "true");
  learningRailBody.inert = !nextExpanded;
  setFocusableDescendantsEnabled(learningRailBody, nextExpanded);
  if (learningRailCollapse) {
    learningRailCollapse.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
  }
  if (learningRailExpand) {
    learningRailExpand.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
  }
}
```

Register click handlers for collapse/expand and initialize to expanded. Add Escape handling that collapses the rail when focus is inside the rail body.

- [ ] **Step 2: Update foundation contract**

Change the right learning rail wording to say it is expanded by default on desktop and may collapse through explicit click control into an operable compact context tab. Preserve the prohibition on inferred goals, progress, recommendations, and dynamic study state.

- [ ] **Step 3: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell \
  tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_rail_collapses_to_compact_context_tab
```

Expected: all focused tests pass.

### Task 4: Verification, Review, Commit

**Files:**
- All modified files from Tasks 1-3.

- [ ] **Step 1: Run full relevant verification**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -q
./scripts/check-render-debug.sh
```

Expected: all commands exit 0.

- [ ] **Step 2: Request code review**

Dispatch a reviewer against the committed or uncommitted diff. Ask specifically about accessibility, focus leaks, mobile layout, contract drift, and whether the behavior copies legacy state/persistence.

- [ ] **Step 3: Fix review findings and re-run focused verification**

If the reviewer reports Critical or Important issues, patch them and re-run the focused tests from Task 3 plus any command relevant to the finding.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-06-19-collapsible-learning-rail-design.md \
  docs/superpowers/plans/2026-06-19-collapsible-learning-rail.md \
  docs/foundation/20_learning_renderer_contract.md \
  packages/static/src/raya_static/builder.py \
  packages/static/src/raya_static/rendering.py \
  packages/static/src/raya_static/shell.py \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Add collapsible learning rail"
```
