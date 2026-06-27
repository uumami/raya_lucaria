# Numbered Object Learning Rail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add static right-rail navigation links for public numbered objects and proofs on math-heavy pages.

**Architecture:** Reuse public section anchors already extracted from rendered article HTML during build. Pass those anchors into the learning rail and render a compact `Key objects` list inside the existing Page contents panel after normal heading links.

**Tech Stack:** Python 3.10 static builder, Playwright e2e tests, render-fixture course, Superpowers TDD workflow.

---

### Task 1: Contract Test For Key Object Rail Links

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Write the failing contract test**

Add assertions to the render-fixture contract area that `reader-ux/index.html`
contains a `Key objects` rail group with object/proof anchors.

- [x] **Step 2: Run the focused contract test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages
```

Expected: failure because no `raya-page-toc-objects` or `Key objects` rail
group exists yet.

- [x] **Step 3: Implement minimal builder changes**

Pass `public_sections` into `_render_learning_rail`, pass it to
`_render_page_contents_rail`, and render a compact nested object list for public
sections whose explicit kind is `numbered-object` or `proof`.

- [x] **Step 4: Run the focused contract test to verify it passes**

Run the same command and expect `1 passed`.

### Task 2: Browser Rail Verification

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Write the failing browser test**

Add or extend a render-fixture rail test to assert the desktop right rail on
`reader-ux/index.html` exposes `Key objects`, object links, no horizontal
overflow, no storage calls, and no runtime fetches.

- [x] **Step 2: Run the focused browser test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_rail_content_starts_in_first_viewport
```

Expected: failure before implementation if the e2e assertion is added first.

- [x] **Step 3: Add minimal rail styling if needed**

If the browser test shows cramped or overflowing object links, add scoped CSS
for `.raya-page-toc-objects` and related classes in `rendering.py`.

- [x] **Step 4: Run focused browser tests to verify green**

Run the same e2e test plus nearby rail/mobile tests.

### Task 3: Full Slice Verification And Commit

**Files:**
- Verify all changed files.

- [x] **Step 1: Run source and render verification**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
./scripts/check-render-debug.sh
```

- [x] **Step 2: Request independent review**

Ask an independent reviewer to inspect source/test changes for contract
alignment, accessibility, no persistence/fetch/external requests, and layout
risk.

- [ ] **Step 3: Commit and push**

Commit source/test/spec/plan changes and push to `origin/new_rayalucaria`.
