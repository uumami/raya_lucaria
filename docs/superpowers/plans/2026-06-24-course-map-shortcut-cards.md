# Course Map Shortcut Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the course-map workspace links into compact static shortcut cards with structural badges and page-focused Practice handoff.

**Architecture:** Use existing renderer inputs only: current page, content model, direct `official_counts`, current page `official_objects`, and `page_graph_context`. Compute display badges during page render, emit richer HTML in `_render_course_map()`, and style it with existing skin tokens.

**Tech Stack:** Python static builder, static CSS in `rendering.py`, pytest, Playwright e2e.

---

### Task 1: Failing Browser Coverage

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] Add assertions in the shell/course-map browser coverage that `.raya-course-map-workspace-link` cards contain label and badge elements.
- [x] Add assertions that the render-fixture reader page shows generic Practice href and structural badges such as `Course` and `<N> links`.
- [x] Add assertions that a copied minimal fixture topic page, which directly owns official objects and injected task objects, shows page-owned Practice and Tasks badges plus a Practice card href ending in `_raya/practice/index.html?page=first-topic`.
- [x] Run the focused tests and confirm they fail because current links are plain anchors without badge elements and generic page-owned Practice handoff.

### Task 2: Builder Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [x] Pass `official_counts`, current page `official_objects`, and `page_graph_context` into `_render_course_map()`.
- [x] Compute direct official count from `official_counts.get(page.id, {})`.
- [x] Compute direct task count from current page official objects whose type is one of `assignment`, `exam`, `project`, or `task`.
- [x] Compute current page explicit link count from `len(page_graph_context["outgoing"]) + len(page_graph_context["incoming"])`.
- [x] Emit each workspace link as:

```html
<a class="raya-course-map-workspace-link raya-course-map-workspace-graph" ...>
  <span class="raya-course-map-workspace-label">Graph</span>
  <span class="raya-course-map-workspace-badge">0 links</span>
</a>
```

- [x] Use `_href_with_query(practice_href, {"page": page.id})` only when direct official count is nonzero.
- [x] Run the focused tests and confirm the markup behavior passes.

### Task 3: Card Styling

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] Style workspace links as compact two-line cards using existing `--raya-color-*` tokens.
- [x] Add `.raya-course-map-workspace-label` and `.raya-course-map-workspace-badge` rules.
- [x] Keep the card grid stable on desktop and mobile.
- [x] Confirm the collapsed course map still hides `.raya-course-map-workspaces`.

### Task 4: Docs, Review, Verification

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] Document course-map workspace shortcut cards as structural navigation cues, not progress or recommendations.
- [x] Run focused e2e tests.
- [x] Run `./scripts/check-render-debug.sh`.
- [x] Request independent code review.
- [x] Run `./scripts/check.sh`.
- [ ] Commit and push to `origin/new_rayalucaria`.
