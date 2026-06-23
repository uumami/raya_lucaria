# Official Practice Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a generated static `_raya/practice/` workspace that lets readers find accepted official practice objects across a course without scoring, storage, recommendations, external requests, or private source-path leaks.

**Architecture:** The static builder will render a browser-facing discovery page from the already validated official-object model, embed a minimal public JSON payload, and copy one local `practice.js` resource beside the existing search/graph scripts. Content pages and discovery chrome will link to Practice alongside Search and Graph, while the foundation and role docs define the allowed behavior.

**Tech Stack:** Python 3.10 static builder, local vanilla JavaScript, generated HTML/CSS resources, pytest contract tests, Playwright e2e tests.

---

### Task 1: Contract Tests For Static Practice Workspace

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write the failing contract tests**

Add a test near the existing search/graph surface tests:

```python
def test_build_writes_static_official_practice_workspace(tmp_path: Path) -> None:
    course = _copy_minimal_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    site = course / "artifact" / "site"
    practice_page = site / "_raya" / "practice" / "index.html"
    practice_js = site / "_raya" / "render" / "practice.js"
    index_html = (site / "index.html").read_text(encoding="utf-8")
    topic_html = (site / "unit" / "topic" / "index.html").read_text(encoding="utf-8")
    practice_html = practice_page.read_text(encoding="utf-8")
    practice_script = practice_js.read_text(encoding="utf-8")

    assert practice_page.exists()
    assert practice_js.exists()
    assert 'href="_raya/practice/index.html"' in index_html
    assert 'href="../../_raya/practice/index.html"' in topic_html
    assert 'data-raya-surface="practice"' in practice_html
    assert "raya-discovery-command-bar" in practice_html
    assert "Official practice workspace" in practice_html
    assert 'href="../search/index.html"' in practice_html
    assert 'href="../graph/index.html"' in practice_html
    assert '<span class="raya-command-label">Search</span>' in practice_html
    assert '<span class="raya-command-label">Graph</span>' in practice_html
    assert "shell.js" not in practice_html
    assert "localStorage" not in practice_html
    assert '<script type="application/json" id="raya-practice-data">' in practice_html
    assert 'src="../render/practice.js"' in practice_html
    assert 'href="../render/rich.css"' in practice_html
    assert 'href="../render/skin.css"' in practice_html
    assert 'href="../../data/official.json"' not in practice_html
    assert "https://" not in practice_html
    assert "http://" not in practice_html
    assert 'id="raya-practice-search"' in practice_html
    assert 'id="raya-practice-clear"' in practice_html
    assert 'data-raya-practice-filter="quiz"' in practice_html
    assert 'data-raya-practice-object="first-topic-card"' in practice_html
    assert 'data-raya-practice-object="first-topic-prompt"' in practice_html
    assert 'data-raya-practice-object="first-topic-quiz"' in practice_html
    assert "What loop does Raya Lucaria support?" in practice_html
    assert "Explain how retrieval practice differs from rereading." in practice_html
    assert "Which action is part of the Raya Lucaria learning loop?" in practice_html
    assert "Read, retrieve, reflect, adapt, revisit, and contribute." not in practice_html
    assert "Correct option" not in practice_html
    assert "Vendor lock-in" not in practice_html
    assert 'href="../../unit/topic/index.html#raya-official-first-topic-card"' in practice_html
    assert 'href="../graph/index.html?page=first-topic"' in practice_html

    payload_match = re.search(
        r'<script type="application/json" id="raya-practice-data">\n(.*?)\n</script>',
        practice_html,
        re.DOTALL,
    )
    assert payload_match is not None
    payload = json.loads(payload_match.group(1))
    assert set(payload) == {"objects", "types", "version"}
    assert payload["version"] == 1
    by_id = {item["id"]: item for item in payload["objects"]}
    assert set(by_id) == {"first-topic-card", "first-topic-prompt", "first-topic-quiz"}
    assert by_id["first-topic-card"]["preview"] == "What loop does Raya Lucaria support?"
    assert by_id["first-topic-quiz"]["preview"] == (
        "Which action is part of the Raya Lucaria learning loop?"
    )
    assert by_id["first-topic-card"]["page_url"].endswith(
        "/unit/topic/index.html#raya-official-first-topic-card"
    )
    assert by_id["first-topic-card"]["graph_url"] == "../graph/index.html?page=first-topic"
    allowed_object_keys = {
        "anchor",
        "authority",
        "graph_url",
        "id",
        "page_id",
        "page_title",
        "page_url",
        "preview",
        "type",
        "type_label",
    }
    for item in payload["objects"]:
        assert set(item) == allowed_object_keys
    serialized_payload = json.dumps(payload)
    for private_token in (
        "_official",
        "_reviewed",
        "_assets",
        "artifact",
        "source_path",
        "cache_key",
        "course/",
        "correct",
        "solution",
        "answer",
        "back",
    ):
        assert private_token not in serialized_payload
    for forbidden_runtime_token in (
        "fetch(",
        "XMLHttpRequest",
        "localStorage",
        "sessionStorage",
        "indexedDB",
        "caches.",
        "navigator.sendBeacon",
        "import(",
        "new Worker",
        "EventSource",
        "WebSocket",
    ):
        assert forbidden_runtime_token not in practice_script
```

Extend `test_render_fixture_search_graph_course_map_visible_text_avoids_learner_state_language` by adding:

```python
        (site / "_raya" / "practice" / "index.html").read_text(encoding="utf-8"),
```

to the `surfaces` list.

- [ ] **Step 2: Run the focused contract test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace
```

Expected: fail because `_raya/practice/index.html` or `_raya/render/practice.js` does not exist.

### Task 2: Practice Workspace Builder And Local Script

**Files:**
- Create: `packages/static/src/raya_static/practice.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add the local practice script resource**

Create `packages/static/src/raya_static/practice.py` with a `practice_resources()` helper that returns one `practice.js` script. The script must parse `#raya-practice-data`, filter `[data-raya-practice-object]` cards by search and type chip, update `#raya-practice-status`, toggle `#raya-practice-empty`, and avoid fetch/storage/network APIs.

- [ ] **Step 2: Add practice surface generation**

Modify `builder.py` to:

- Import `PRACTICE_RESOURCE_PATH`, `PRACTICE_SCRIPT_NAME`, and `practice_resources`.
- Define `STATIC_PRACTICE_PATH = Path(STATIC_RESOURCE_DIR) / "practice" / "index.html"`.
- Copy `practice.js` into `site/_raya/render/`.
- Add a `Practice` link to `_render_top_command_bar` and `_render_discovery_command_bar`.
- Write `_write_practice_surface` after graph/search surface generation.
- Render a page with `data-raya-surface="practice"`, discovery chrome, local CSS/JS, filter chips, cards grouped by owning page, and an embedded `raya-practice-data` payload.
- Build payload entries only from validated official objects and the owning page resolved by `_official_objects_by_page`.
- Use only public keys: `id`, `type`, `type_label`, `authority`, `page_id`, `page_title`, `page_url`, `graph_url`, `anchor`, and `preview`.
- Use only safe preview fields: `content.front` for cards, `content.prompt` for prompts, first question `prompt` for quizzes, and title/summary/prompt/instructions/body/question for generic official objects. Do not include backs, answers, solutions, options, correctness, source paths, artifact paths, or `_official` names.

- [ ] **Step 3: Add CSS for the workspace**

Modify `rendering.py` so practice pages have responsive cards, filter chips, status text, grouped sections, and readable action rows. Reuse existing skin variables and command-bar patterns; do not introduce external fonts or CDN resources.

- [ ] **Step 4: Run contract tests and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace tests/contracts/test_static_builder.py::test_render_fixture_search_graph_course_map_visible_text_avoids_learner_state_language
```

Expected: both pass.

### Task 3: Browser Preview Coverage

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing browser test**

Add `test_preview_serves_static_official_practice_workspace` near the search/graph e2e tests. It should serve the minimal fixture, visit `/_raya/practice/index.html`, assert no external requests, assert no horizontal overflow at desktop and mobile widths, search for `retrieval`, filter by `Quiz`, clear, click `Open page` for `first-topic-card`, and verify the URL ends with `/unit/topic/index.html#raya-official-first-topic-card` and the target is visible.

- [ ] **Step 2: Run the browser test and verify RED or GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_practice_workspace
```

Expected before Task 2: fail because the page is missing. Expected after Task 2: pass or reveal a real browser/layout bug to fix.

- [ ] **Step 3: Fix only browser/layout defects exposed by the test**

If the e2e test fails after implementation, adjust `practice.js`, practice markup, or `rendering.py` styles until it passes without weakening the privacy/static assertions.

### Task 4: Foundation And Role Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Document the contract**

Update the renderer contract to name `Official Practice workspace` as a current static discovery surface over accepted official objects. State that it is generated from official data, links to owning page anchors and graph focus, and does not provide scoring, personal progress, recommendations, fetches, storage, or private source paths.

- [ ] **Step 2: Document role usage**

Update role docs:

- Students: use Practice to find accepted course cards/prompts/quizzes/tasks and return to owning pages.
- Professors: author official objects in `_official/`; the build creates page sections and the Practice workspace.
- Agents: verify `_raya/practice/index.html`, local script, no private source paths, no external requests, and no learner-state language.

- [ ] **Step 3: Run docs/content checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace
```

Expected: pass, proving docs changes did not break the build path used by the new surface.

### Task 5: Review And Full Verification

**Files:**
- Review all files changed in this plan.

- [ ] **Step 1: Request code review**

Use `superpowers:requesting-code-review` and dispatch independent reviewers for contract/static behavior, browser UX behavior, and docs/foundation alignment.

- [ ] **Step 2: Run focused render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: pass, with no external renderer requests, no overflow failures, and no committed debug artifacts.

- [ ] **Step 3: Run host gate**

Run:

```bash
./scripts/check.sh
```

Expected: pass.

- [ ] **Step 4: Run Docker gate**

Run:

```bash
./scripts/check-docker.sh
```

Expected: pass.

- [ ] **Step 5: Commit and push**

Run:

```bash
git status --short
git add docs/superpowers/specs/2026-06-23-official-practice-workspace-design.md docs/superpowers/plans/2026-06-23-official-practice-workspace.md packages/static/src/raya_static/practice.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/es/estudiantes/index.md docs/guides/en/professors/index.md docs/guides/es/profesores/index.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md
git commit -m "Add official practice workspace"
git push origin new_rayalucaria
```

Expected: push succeeds to the GitHub branch `new_rayalucaria`.

---

## Self-Review

**Spec coverage:** The plan covers generated workspace HTML, local JS, links from course/discovery chrome, public embedded payload, privacy/static constraints, browser filtering, foundation docs, role docs, review, and full host/Docker verification.

**Placeholder scan:** No task relies on TBD/TODO placeholders. The only conditional instruction is limited to fixing concrete browser/layout defects exposed by the e2e test.

**Type consistency:** The payload keys named in tests match the builder task and the JavaScript filtering target names. Paths match existing `_raya/search` and `_raya/graph` conventions.
