# Course Discovery Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build richer static Search and Graph discovery cards from public course metadata only.

**Architecture:** Add one shared public page-summary payload in `builder.py` and reuse it for Search and Graph browser payloads. Keep all behavior static, embedded, deployment-neutral, and free of recommendation/progress language.

**Tech Stack:** Python 3.10 static builder, local JavaScript resources, pytest contract tests, Playwright e2e checks.

---

### Task 1: Contract And Role Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update the renderer contract**

Add explicit wording that generated Search and Graph cards may show public page metadata, previous/next course-order links, explicit graph counts, accepted official-object counts, and local workspace handoff links. State that these are structural discovery cues, not recommendations, progress, mastery, ranking, or related-practice inference.

- [ ] **Step 2: Update agent guides**

Tell agent reviewers to verify public-only embedded payloads, relative links, no private paths, no answer/support leakage, no learner-state wording, no runtime fetching/storage for discovery state, and preserved Search/Graph keyboard/navigation behavior.

- [ ] **Step 3: Review docs for forbidden wording**

Run:

```bash
rg -n "recommended practice|related practice|progress|mastery|completion|ranking|source_path|_official" docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md
```

Expected: only contract-safe negative wording appears.

### Task 2: Failing Contract Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add failing Search assertions**

Extend `test_build_writes_local_course_search_surface` so it expects Search result cards and payload pages to include:

- `stable_id`
- `previous_url`
- `next_url`
- `practice_url`
- `study_counts`
- `link_counts`
- visible `Open page`, `View in graph`, `Open practice`, `Explicit links`, and `Official objects` labels

Keep private token and runtime-token guards.

- [ ] **Step 2: Add failing Graph assertions**

Extend the graph surface test so it expects Graph payload nodes and detail placeholders to include:

- `stable_id`
- `summary`
- `hierarchy_label`
- `search_url`
- `practice_url`
- `study_counts`
- `link_counts`
- detail elements for summary, study counts, search link, and practice link

- [ ] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: FAIL because the new card fields and detail placeholders do not exist yet.

### Task 3: Shared Public Discovery Payload

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add public helper functions**

Add builder helpers that derive page discovery data from `ContentModel`, `graph_index`, `official_counts`, and relative base path:

- stable ID and public page metadata
- previous/next URLs from flattened navigation order
- study counts from accepted official object counts
- explicit link counts from generated graph edges
- Graph/Search/Practice workspace URLs

Do not read source paths, support paths, official answers, or artifact internals into the payload.

- [ ] **Step 2: Pass official counts into Search and Graph renderers**

Thread `official_counts` through `_write_search_surface`, `_render_search_surface`, `_browser_search_payload`, `_write_graph_surface`, `_render_graph_surface`, and `_browser_graph_payload`.

- [ ] **Step 3: Verify GREEN for contract payload shape**

Run the same focused contract tests. Expected: Search/Graph payload assertions pass or fail only on HTML/JS presentation still to implement.

### Task 4: Search And Graph Card Presentation

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/search.py`
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Render richer Search cards**

Update generated Search HTML cards with title, summary, stable ID, hierarchy/status/tags, explicit link-count badges, official-object count badges, and action links: `Open page`, `View in graph`, and `Open practice` when counts exist.

- [ ] **Step 2: Preserve Search behavior**

Keep Enter opening the first card page link. Add new public fields to local searchable text only.

- [ ] **Step 3: Render richer Graph selected detail**

Update Graph JS and HTML placeholders so selected detail shows summary, stable ID, hierarchy/status/tags, explicit link counts, official-object counts, `Open page`, `Find in search`, and `Open practice` when counts exist.

- [ ] **Step 4: Render denser Graph list rows**

Update Graph list HTML to show compact metadata and counts without changing graph selection behavior.

- [ ] **Step 5: Add shared styling**

Extend existing Search/Graph styles with dense metadata rows, badges, and action links that work on desktop and mobile without horizontal overflow.

- [ ] **Step 6: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: PASS.

### Task 5: Browser Behavior And Verification

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add e2e assertions**

Extend Search/Graph e2e coverage so the browser verifies card labels, action links, Graph selected detail summary/counts/actions, Search-to-Graph focus, no external requests, and no horizontal overflow on representative desktop/mobile viewports.

- [ ] **Step 2: Verify focused e2e**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface
```

Expected: PASS.

- [ ] **Step 3: Run renderer gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS and no committed debug artifacts.

### Task 6: Review, Full Verification, Commit, Push

**Files:**
- Review all modified files.

- [ ] **Step 1: Request code review**

Dispatch independent reviewers for contract safety, browser UX, and payload privacy before final verification.

- [ ] **Step 2: Apply valid review feedback**

Fix Critical and Important review findings with focused tests first when behavior changes.

- [ ] **Step 3: Run archive gates sequentially**

Run:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both PASS.

- [ ] **Step 4: Commit and push**

Commit with an imperative subject and push to `origin/new_rayalucaria`.

```bash
git status --short
git add docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md docs/superpowers/specs/2026-06-23-course-discovery-cards-design.md docs/superpowers/plans/2026-06-23-course-discovery-cards.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/search.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add course discovery cards"
git push origin new_rayalucaria
```
