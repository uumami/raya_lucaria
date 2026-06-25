# Public Article Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reset-native static full-text search surface over public rendered article text.

**Architecture:** The static builder extracts public text from rendered article HTML, writes `data/search-index.json`, and embeds the same public records into the generated Search page. The local Search script continues filtering already rendered DOM cards from embedded JSON only.

**Tech Stack:** Python 3.10, `html.parser`, existing Glintstone static builder, existing local Search JavaScript, pytest, Playwright e2e.

---

## File Map

- Modify `packages/static/src/raya_static/builder.py`: extract public article text, carry it through build data, write `data/search-index.json`, and include search fields in the Search payload.
- Modify `packages/static/src/raya_static/search.py`: search `search_text` and show optional public match snippets in the context panel.
- Modify `tests/contracts/test_static_builder.py`: add contract checks for generated search index, public prose matches, privacy exclusions, and payload shape.
- Modify `tests/e2e/test_preview_static_read_path.py`: add a browser check that prose-only queries filter Search correctly without external/runtime requests.
- Modify `docs/foundation/20_learning_renderer_contract.md`: update Search contract from metadata-only to public article prose plus metadata.
- Modify English and Spanish role docs for students, professors, contributors, and agents.

## Tasks

### Task 1: Contract Test for Public Search Index

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write the failing test**

Add assertions to `test_build_writes_local_course_search_surface`:

```python
    search_index_path = course / "artifact" / "data" / "search-index.json"
    assert search_index_path.exists()
    search_index = json.loads(search_index_path.read_text(encoding="utf-8"))
    assert search_index["version"] == 1
    assert {record["id"] for record in search_index["pages"]} >= {
        "render-root",
        "authoring-matrix",
    }
    search_records = {record["id"]: record for record in search_index["pages"]}
    assert "fixture material for renderer and documentation tests" in (
        search_records["authoring-matrix"]["search_text"].lower()
    )
    assert "matrix norm fixture" in (
        search_records["authoring-matrix"]["search_text"].lower()
    )
    assert len(search_records["authoring-matrix"]["search_snippet"]) <= 280
    assert "mjx-container" not in json.dumps(search_index)
    assert "\\\\begin" not in json.dumps(search_index)
```

Update payload assertions:

```python
    assert set(search_payload) == {"pages", "version"}
    allowed_page_keys = {
        ...
        "search_snippet",
        "search_text",
    }
    assert "fixture material for renderer and documentation tests" in (
        pages_by_id["authoring-matrix"]["search_text"].lower()
    )
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface -q
```

Expected: FAIL because `artifact/data/search-index.json` does not exist and payload pages do not include `search_text`.

### Task 2: Build Public Article Search Records

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add public text extraction helpers**

Implement a small `HTMLParser`-based helper near the existing render helpers:

```python
class _PublicArticleTextParser(HTMLParser):
    _SKIP_CLASSES = {
        "MathJax",
        "mjx-container",
        "raya-page-brief",
        "raya-official-practice",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name: value or "" for name, value in attrs}
        classes = set(attr_map.get("class", "").split())
        if tag in {"script", "style", "svg"} or classes & self._SKIP_CLASSES:
            self._skip_depth += 1
        if not self._skip_depth and tag in {"p", "li", "h1", "h2", "h3", "h4", "td", "th", "blockquote"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth:
            self._skip_depth -= 1
            return
        if tag in {"p", "li", "h1", "h2", "h3", "h4", "td", "th", "blockquote"}:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)


def _public_article_search_text(article_html: str) -> str:
    parser = _PublicArticleTextParser()
    parser.feed(article_html)
    return _compact_public_text(" ".join(parser.parts))


def _compact_public_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _public_search_snippet(text: str, *, limit: int = 240) -> str:
    compact = _compact_public_text(text)
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "..."
```

- [ ] **Step 2: Capture per-page records while rendering**

Thread a `search_records: dict[str, dict[str, str]]` through the page rendering loop. After `article_html, toc_html = _extract_page_toc(article_html)`, compute:

```python
public_article_text = _public_article_search_text(article_html)
search_records[page.id] = {
    "id": page.id,
    "search_text": public_article_text,
    "search_snippet": _public_search_snippet(public_article_text),
}
```

- [ ] **Step 3: Write generated data**

Write `artifact/data/search-index.json` with:

```python
{
    "version": 1,
    "pages": [search_records.get(page.id, {"id": page.id, "search_text": "", "search_snippet": ""}) for page in content_model.pages],
}
```

Add it to manifest-declared data indexes following the current `data/*.json` pattern.

- [ ] **Step 4: Run the contract test and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface -q
```

Expected: PASS for the new data-file checks, or fail only on Search payload fields addressed by Task 3.

### Task 3: Embed Public Text in Search Payload and Script

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/search.py`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add payload fields**

Update `_browser_search_payload` and `_public_discovery_page_payload` call path so each Search page record includes:

```python
"search_text": _compact_public_text(" ".join([
    page.id,
    page.title,
    page.nav_title,
    page.summary,
    page.status,
    page.hierarchy_label,
    " ".join(page.tags),
    search_records.get(page.id, {}).get("search_text", ""),
])),
"search_snippet": search_records.get(page.id, {}).get("search_snippet", ""),
```

- [ ] **Step 2: Search the new field**

In `packages/static/src/raya_static/search.py`, replace the `pageText` construction with `page.search_text` as the primary field while retaining metadata fallback:

```javascript
const pageText = new Map(
  pages.map((page) => [
    page.id,
    normalize(page.search_text || [
      page.id,
      page.stable_id,
      page.title,
      page.nav_title,
      page.summary,
      page.status,
      page.hierarchy_label,
      ...(Array.isArray(page.tags) ? page.tags : []),
    ].join(" ")),
  ])
);
```

In `updateContext`, append snippet text when present:

```javascript
const snippet = page.search_snippet ? `Match text: ${page.search_snippet}` : "";
...
snippet,
```

- [ ] **Step 3: Run the focused contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface -q
```

Expected: PASS.

### Task 4: Browser E2E for Prose Query

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing browser assertion**

In the existing Search workspace e2e block, add:

```python
page.goto(
    f"{base_url}/_raya/search/index.html?q=matrix%20norm%20fixture",
    wait_until="networkidle",
)
page.wait_for_selector('[data-raya-search-result="authoring-matrix"]:not([hidden])')
assert page.locator('[data-raya-search-result="authoring-matrix"]').is_visible()
assert "Match text:" in page.locator("[data-raya-search-context-meta]").inner_text()
```

- [ ] **Step 2: Run the focused e2e**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -q -k "search"
```

Expected: PASS after Tasks 2-3.

### Task 5: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update wording**

Replace metadata-only wording with public article prose plus metadata. Keep explicit exclusions: no source paths, private folders, official answers/support, learner state, recommendations, progress, or external search services.

- [ ] **Step 2: Run docs/search tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_search_graph_course_map_visible_text_avoids_learner_state_language -q
```

Expected: PASS.

### Task 6: Verification and Review

**Files:**
- No implementation edits unless verification exposes bugs.

- [ ] **Step 1: Run focused verification**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -q -k "search"
./scripts/check-render-debug.sh
```

- [ ] **Step 2: Request independent review**

Ask one subagent to review current Search code against the design, focusing on privacy, reset principles, and test gaps.

- [ ] **Step 3: Final gates**

Run:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both pass sequentially.
