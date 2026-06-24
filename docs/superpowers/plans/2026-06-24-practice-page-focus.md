# Practice Page Focus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add page-scoped handoff from Search and Graph into the static Official Practice workspace.

**Architecture:** Keep page focus as URL state only. Generate page-focused Practice URLs from existing public discovery payloads, then have the local Practice script filter embedded official objects by `page_id` when `?page=<page-id>` is present.

**Tech Stack:** Python static builder, embedded JSON payloads, local vanilla JavaScript, pytest, Playwright e2e tests.

---

### Task 1: Contract And Browser Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] Add contract assertions that Search payload and rendered Search links use `../practice/index.html?page=authoring-matrix` for pages with accepted official objects.
- [x] Add contract assertions that Graph discovery payload or HTML has page-focused Practice URLs for selected pages with official objects.
- [x] Add contract assertions that parent pages with only descendant official objects keep aggregate counts but do not receive direct page-focused Practice URLs.
- [x] Add browser assertions that visiting `_raya/practice/index.html?page=first-topic` shows only first-topic owned official objects and uses no browser storage.
- [x] Add browser assertions that visiting a non-matching `_raya/practice/index.html?page=missing-page` URL hides all objects, updates the empty context, and uses no browser storage.
- [x] Add browser assertions that Clear and Escape reset the Practice workspace to all visible objects.
- [x] Run the focused tests and confirm they fail because Practice URLs are generic and URL page focus is ignored.

### Task 2: Static Builder URLs

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [x] Update `_public_discovery_page_payload()` so `practice_url` includes `?page=<page-id>` when the page has accepted official objects.
- [x] Update Graph selected-page detail data if needed so `data-raya-graph-detail-practice-link` receives the focused Practice URL from the existing payload.
- [x] Run the contract tests and confirm URL assertions pass.

### Task 3: Practice URL Focus

**Files:**
- Modify: `packages/static/src/raya_static/practice.py`

- [x] Parse `new URLSearchParams(window.location.search).get("page")` on load.
- [x] Keep `activePage` as transient in-memory state.
- [x] Include `page_id` in matching logic so page focus composes with type filters and text search.
- [x] Initialize `activePage` from the URL before first render.
- [x] Make Clear and Escape reset `activePage`, `activeType`, search input, and active object index.
- [x] Run focused Practice e2e tests and confirm they pass.

### Task 4: Docs And Verification

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] Document that generated Practice links may carry page context as non-persistent URL state.
- [x] Run focused contract/e2e tests.
- [ ] Run `./scripts/check-render-debug.sh`.
- [x] Request independent code review.
- [ ] Run `./scripts/check.sh`.
- [ ] Commit and push to `origin/new_rayalucaria`.
