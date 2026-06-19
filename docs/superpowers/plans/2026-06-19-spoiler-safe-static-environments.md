# Spoiler-Safe Static Environments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render hints, solutions, and answers as closed native disclosures while keeping proofs expanded and documented.

**Architecture:** Keep all behavior inside the existing static renderer. Use semantic `<details>/<summary>` for optional support blocks, no JavaScript, and CSS-only polish through the existing skin token system.

**Tech Stack:** Python 3.10, pytest, Playwright/browser e2e, static HTML/CSS.

---

### Task 1: Contract Markup

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Write failing contract assertions**

Add assertions to `test_static_environments_render_targeted_headings_and_stay_out_of_numbered_index` that require `hint`, `solution`, and `answer` static environments to render as closed `<details>` with `<summary class="raya-static-environment-heading">`.

- [ ] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_environments_render_targeted_headings_and_stay_out_of_numbered_index -q
```

Expected: fail because the renderer still emits `<section>` and `<p>` for non-proof static environments.

- [ ] **Step 3: Implement minimal renderer change**

In `_render_static_environment_html`, leave the `proof` branch unchanged. Change the non-proof branch to emit `<details>` and `<summary>` while preserving `id`, class names, reference text, title text, body wrapper, and closing tags.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_environments_render_targeted_headings_and_stay_out_of_numbered_index -q
```

Expected: pass.

### Task 2: Browser Behavior

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Write failing browser test**

Add an e2e test that builds `examples/courses/render-fixture`, serves `artifact/site`, opens `reader-ux/index.html`, and verifies `#raya-static-environment-hint-orthogonal-activity` is a closed `DETAILS` element whose body has no layout rects. Click the `summary`, then verify `open` is true, body text is visible, and the URL did not change.

- [ ] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::<new_test_name> -q
```

Expected: fail before the renderer emits native details.

- [ ] **Step 3: Add CSS for native disclosure affordance**

Update static CSS so `summary.raya-static-environment-heading` has pointer affordance, visible focus, and coherent open-state spacing while using existing CSS custom properties.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::<new_test_name> -q
```

Expected: pass.

### Task 3: Fixture and Documentation Coverage

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Add focused contract coverage**

Extend existing render-fixture contract coverage to assert the fixture includes disclosure static environments and expanded proofs.

- [ ] **Step 2: Run focused contract tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
```

Expected: pass.

- [ ] **Step 3: Update docs**

Document that optional support blocks are spoiler-safe disclosures, closed by default, and static. Mention that opening one does not submit an answer, store progress, or contact services.

- [ ] **Step 4: Run docs/renderer gates**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: pass with no render-debug diagnostics.

### Task 4: Verification and Review

**Files:**
- Review all changed files.

- [ ] **Step 1: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -q
./scripts/check-render-debug.sh
```

Expected: all pass.

- [ ] **Step 2: Request independent review**

Dispatch an independent reviewer to check accessibility, reset constraints, docs, and tests for spoiler-safe disclosures.

- [ ] **Step 3: Address review findings**

If the reviewer finds a valid issue, add a failing test first when behavior changes, then implement and rerun relevant gates.

- [ ] **Step 4: Commit**

Run:

```bash
git status --short
git add docs/superpowers/specs/2026-06-19-spoiler-safe-static-environments-design.md docs/superpowers/plans/2026-06-19-spoiler-safe-static-environments.md tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py packages/static/src/raya_static/rendering.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/professors/index.md docs/guides/en/students/index.md docs/guides/en/contributors/index.md docs/guides/en/agents/index.md docs/guides/es/profesores/index.md docs/guides/es/estudiantes/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md
git commit -m "Add spoiler-safe static disclosures"
```

Expected: commit succeeds and working tree is clean.
