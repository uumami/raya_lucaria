# Static Official Tasks Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static Official Tasks workspace and manifest-declared task index for work-bearing official objects.

**Architecture:** Reuse the existing static discovery-page pattern used by Practice. The builder extracts safe public planning metadata at build time, writes `data/tasks.json`, renders `_raya/tasks/index.html` with an embedded payload, and ships a local `tasks.js` script for filtering and sorting.

**Tech Stack:** Python static builder, JSON artifact indexes, Playwright e2e tests, local JavaScript resources, Markdown docs.

---

### Task 1: Add Failing Contract Coverage

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] Add a test that creates official `assignment`, `project`, `exam`, and `task` objects in the minimal fixture copy.
- [ ] Assert build output contains `artifact/data/tasks.json`.
- [ ] Assert `artifact/manifest.json` declares `"tasks": "data/tasks.json"`.
- [ ] Assert `artifact/site/_raya/tasks/index.html` and `artifact/site/_raya/render/tasks.js` exist.
- [ ] Assert task HTML uses `data-raya-surface="tasks"`, links to Search, Graph, and Practice, includes only local scripts/styles, and does not contain `_official`, source paths, answer/solution fields, `fetch(`, `localStorage`, `sessionStorage`, `https://`, or `http://`.
- [ ] Assert task payload contains only allowed public keys and preserves `due`, `points`, `weight`, `status`, and `tags` when authored.

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace -q
```

Expected: fail because the task index and page do not exist yet.

### Task 2: Add Failing Browser Coverage

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] Add a preview test for `_raya/tasks/index.html` using the minimal fixture copy plus work-bearing official objects.
- [ ] Assert no browser request leaves the preview base URL.
- [ ] Assert desktop uses control, results, and context panels in left-to-right order.
- [ ] Assert mobile has no horizontal overflow.
- [ ] Assert search, type filter, due sort, context update, OpenDyslexic, text-size control, arrow-key selection, and Enter-to-open behavior work.
- [ ] Assert the local script contains no `fetch(`, `XMLHttpRequest`, `localStorage`, or `sessionStorage`.

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_tasks_workspace -q
```

Expected: fail because `_raya/tasks/index.html` is missing.

### Task 3: Implement Task Extraction and Artifact Output

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/schema/src/raya_schema/schemas/artifact-manifest.schema.json`

- [ ] Add `STATIC_TASKS_PATH = Path("_raya") / "tasks" / "index.html"`.
- [ ] Add a safe task payload builder that includes only official objects with types `assignment`, `exam`, `project`, and `task`.
- [ ] Extract public planning fields from accepted official object `content`: `title`, `summary`, `prompt`, `instructions`, `due`, `available`, `points`, `weight`, `status`, and `tags`.
- [ ] Write `artifact/data/tasks.json`.
- [ ] Declare `"tasks": "data/tasks.json"` in `manifest.json`.
- [ ] Add optional `tasks` to the artifact manifest schema.
- [ ] Add task workspace links where the discovery command bar can expose them without replacing existing Practice links.

Run the contract test from Task 1.

Expected: pass.

### Task 4: Render Task Workspace and Local Script

**Files:**
- Create: `packages/static/src/raya_static/tasks.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] Add `tasks_resources()` returning `tasks.js`.
- [ ] Write `_write_tasks_resources`, `_write_tasks_surface`, and `_render_tasks_surface` using the Practice/Search discovery layout pattern.
- [ ] Add cards with task type, title/preview, page, optional due/status/points/weight/tags, Open page, and View in graph links.
- [ ] Implement local script filtering by search text and type, sorting by course order or due date, transient active context, and keyboard Enter-to-open.
- [ ] Add CSS for `.raya-tasks-*` using existing skin tokens and responsive discovery layout conventions.

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_tasks_workspace -q
```

Expected: pass.

### Task 5: Update Foundation and Role Docs

**Files:**
- Modify: `docs/foundation/06_artifact_contract.md`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] Document that tasks are authored official objects and the workspace is generated.
- [ ] Document that `data/tasks.json` is public artifact metadata, not source authority or learner state.
- [ ] Document that local preview and static deployment use the same task page and script.
- [ ] Document the privacy and non-goals: no grading, submission, progress, recommendations, backend, runtime fetches, external renderers, or storage.

Run focused documentation/static tests that changed surfaces already cover.

### Task 6: Review and Verify

**Files:**
- All changed files

- [ ] Request an independent code review focused on contract fit, privacy, static parity, and browser UX.
- [ ] Fix review findings or record why they are not applicable.
- [ ] Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_tasks_workspace -q
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

- [ ] Commit and push to `origin/new_rayalucaria`.
