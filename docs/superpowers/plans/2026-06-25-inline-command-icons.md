# Inline Command Icons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace CSS pseudo-text command badges with explicit local inline SVG icons in reader and discovery command bars.

**Architecture:** The static builder emits icon markup through small renderer-local helpers. CSS styles `.raya-command-icon` as the badge surface while preserving existing command classes and behavior.

**Tech Stack:** Python 3.10 static builder, renderer CSS string, Playwright e2e tests, pytest contract tests.

---

### Task 1: Add Failing Icon Markup Tests

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Replace pseudo-content e2e assertions**

Update command-bar checks so they collect icon metadata from `.raya-command-icon` elements:

```javascript
() => Object.fromEntries(
  Array.from(document.querySelectorAll('.raya-top-command-bar .raya-command'))
    .map((node) => {
      const commandClass = Array.from(node.classList)
        .find((name) => name.startsWith('raya-command-'));
      const icon = node.querySelector('.raya-command-icon');
      return [commandClass, {
        tagName: icon?.tagName,
        icon: icon?.getAttribute('data-raya-command-icon'),
        ariaHidden: icon?.getAttribute('aria-hidden'),
        focusable: icon?.getAttribute('focusable'),
        viewBox: icon?.getAttribute('viewBox'),
        label: node.querySelector('.raya-command-label')?.textContent?.trim(),
        before: getComputedStyle(node, '::before').content,
      }];
    })
)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_shell_has_modern_workspace_chrome -q
```

Expected: FAIL because current command bars have no `.raya-command-icon` SVG elements.

### Task 2: Emit Inline SVG Command Icons

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add icon helpers**

Add `_COMMAND_ICON_BODIES`, `_command_icon`, `_render_command_link`, and `_render_command_button` near the command-bar rendering helpers. Icons must be fixed literals and use `currentColor`.

- [ ] **Step 2: Use helpers in reader and discovery bars**

Update `_render_top_command_bar`, `_render_discovery_command_bar`, and `_render_course_map_toggle` so every command includes icon markup before `.raya-command-label`.

- [ ] **Step 3: Verify focused tests still fail only on CSS**

Run the same focused pytest command. Expected: e2e icon markup assertions pass; CSS selector contract may still fail until styling changes.

### Task 3: Style Icon Markup

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Replace pseudo-badge CSS**

Remove command-specific glyph `content` rules and style `.raya-command-icon` directly:

```css
.raya-command-icon {
  background: color-mix(in srgb, var(--raya-color-page) 70%, transparent);
  border: 1px solid color-mix(in srgb, currentColor 36%, transparent);
  border-radius: 0.3rem;
  box-sizing: border-box;
  color: currentColor;
  flex: 0 0 auto;
  height: 1.5rem;
  padding: 0.2rem;
  width: 1.5rem;
}
```

- [ ] **Step 2: Update mobile map rule**

Replace `.raya-command-map::before` mobile styling with `.raya-command-map .raya-command-icon`.

- [ ] **Step 3: Verify GREEN**

Run the focused pytest command. Expected: PASS.

### Task 4: Verify, Review, Preview

**Files:**
- No additional production files expected.

- [ ] **Step 1: Request independent review**

Ask an independent reviewer to inspect the diff for accessibility, static-renderer boundaries, tests, and regressions.

- [ ] **Step 2: Run render verification**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS with no raw TeX, external renderer requests, overflow, or static parity failures.

- [ ] **Step 3: Run host and Docker gates if the review is clean**

Run sequentially:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both PASS.

- [ ] **Step 4: Commit and push**

Commit with:

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py tests/contracts/test_static_builder.py docs/superpowers/specs/2026-06-25-inline-command-icons-design.md docs/superpowers/plans/2026-06-25-inline-command-icons.md
git commit -m "Add inline command icons"
git push origin new_rayalucaria
```

- [ ] **Step 5: Start preview**

Start:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --host 127.0.0.1 --port 0
```

Report the local URL and verify it returns HTTP 200.
