# Native Course Calendar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the dated-work-only Schedule with a static, accessible Calendar that combines explicitly authored course dates with automatically derived official work while preserving the deployment-neutral `/_raya/schedule/` route.

**Architecture:** `raya.yaml` supplies one IANA timezone and `course/_official/calendar/` becomes a separately validated source family for non-inferable events. The schema package normalizes authored calendar events and validated official due/available fields into one public `data/calendar.json`; Glintstone embeds that same payload in a server-rendered Calendar agenda and progressively enhances it into an accessible month view. Existing task data remains intact, and all public links are rendered relative to the workspace output path.

**Tech Stack:** Python 3.10, JSON Schema, PyYAML, Raya schema/static/CLI packages, static HTML/CSS/vanilla JavaScript, pytest, Playwright, Docker Compose.

## Global Constraints

- `docs/foundation/` remains the highest truth; update the smallest affected course, artifact, and learning-renderer contracts.
- `raya.yaml.calendar.timezone` is one required non-empty IANA timezone string for every course; use `America/Mexico_City` for IA O26, never a fixed UTC offset.
- Calendar source is only `course/_official/calendar/<ordered-name>.yaml`; it is separately discovered and must never enter generic official discovery or `data/official.json`.
- Calendar documents have `authority: official`, `type: calendar`, one stable document ID, `scope.quantum`, and ordered event entries.
- Allowed authored event kinds are exactly `session`, `holiday`, `milestone`, and `cancellation`; dates are ISO civil `YYYY-MM-DD`, times are local 24-hour `HH:MM`, and an end time requires a later start time.
- Every populated `content.due` and `content.available` on accepted assignments, exams, projects, and tasks is a strict ISO civil date and yields a separate derived occurrence; no prose parsing or status-based suppression.
- Calendar occurrence IDs are globally unique: `calendar:<document-id>:<event-id>`, `official:<object-id>:due`, and `official:<object-id>:available`.
- Always emit validated `data/calendar.json` and `/_raya/schedule/`, including an empty course; `data/calendar.json` is manifest-declared.
- Keep `/_raya/schedule/` only as a compatibility path. Every visible label, title, action, and course-map tile says `Calendar`.
- The browser uses an escaped embedded payload, local resources, volatile/URL state, and timezone-aware `Intl.DateTimeFormat` parts with the configured `timeZone`; it performs no fetch, XHR, localStorage, or sessionStorage operation.
- Preserve the persistent Course map and its working mobile drawer on Calendar; Calendar is active and reader-only Context is absent. Do not restore the legacy command bar or discovery rail.
- Calendar is a static course view, not sync, reminder, submission, grading, personal state, analytics, recommendation, or progress functionality.

---

## File Structure

| Path | Responsibility |
| --- | --- |
| `packages/schema/src/raya_schema/calendar.py` | Discover, validate, and normalize the dedicated authored calendar documents; validate task-family civil dates. |
| `packages/schema/src/raya_schema/schemas/calendar-document.schema.json` | Structural source schema for a calendar document and author-controlled events. |
| `packages/schema/src/raya_schema/schemas/calendar-index.schema.json` | Structural contract for manifest-declared generated calendar data. |
| `packages/schema/src/raya_schema/schemas/raya-course.schema.json` | Require one `calendar.timezone` source configuration value. |
| `packages/schema/src/raya_schema/artifacts.py` | Validate a declared `calendar` artifact index during inspection. |
| `packages/static/src/raya_static/builder.py` | Build/write Calendar data, use occurrence records, and render the compatibility workspace with relative links. |
| `packages/static/src/raya_static/calendar.py` | Local Calendar progressive enhancement resource and its small view/timezone helpers. |
| `packages/static/src/raya_static/render.css` | Calendar agenda/month-grid layout, responsive behavior, skin-safe badges, and reduced-motion rules. |
| `docs/foundation/{05_course_contract,06_artifact_contract,20_learning_renderer_contract}.md` | Accepted source, artifact, and student-facing renderer truth. |
| `docs/guides/{en,es}/{professors,contributors,agents,students}/index.md` | Authoring and review guidance in both supported documentation languages. |
| `tests/contracts/test_course_validation.py` | Source configuration/document/date validation contracts. |
| `tests/contracts/test_static_builder.py` | Generated index, rendered HTML, escaping, relative links, and empty-course contracts. |
| `tests/contracts/test_artifact_validation.py` | Manifest/index inspection contract. |
| `tests/e2e/test_preview_static_read_path.py` | Browser keyboard, timezone, no-network/storage, Course-map, and narrow-layout checks. |

### Task 1: Establish Calendar source and validation contracts

**Files:**
- Create: `packages/schema/src/raya_schema/calendar.py`
- Create: `packages/schema/src/raya_schema/schemas/calendar-document.schema.json`
- Modify: `packages/schema/src/raya_schema/schemas/raya-course.schema.json`
- Modify: `packages/schema/src/raya_schema/course.py`
- Modify: `packages/schema/src/raya_schema/official.py`
- Test: `tests/contracts/test_course_validation.py`

**Interfaces:**
- Consumes: `ContentModel`, `ValidationReport`, `parse_ordered_name`, and the resolved course configuration.
- Produces: `discover_calendar_documents(course_root: Path, source_dir: Path, content_model: ContentModel, timezone: str, report: ValidationReport) -> list[dict[str, Any]]` and `validate_official_calendar_dates(objects: list[dict[str, Any]], report: ValidationReport) -> None`.
- Produces: Each returned document has only `id`, `authority`, `scope`, `source_path`, `source_order`, and ordered normalized event mappings; no document is returned by `discover_official_objects`.

- [ ] **Step 1: Write failing source-contract tests**

```python
def test_calendar_document_is_separate_from_official_objects(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    _set_calendar_timezone(course, "America/Mexico_City")
    _write_calendar_document(course, "1_2026-o26.yaml", events=[_session_event()])

    report = validate_course(course)

    assert report.ok, [item.format() for item in report.diagnostics]
    objects = discover_official_objects_for_test(course)
    assert all(item["type"] != "calendar" for item in objects)


@pytest.mark.parametrize("field,value", [("due", "2026-2-03"), ("available", "tomorrow")])
def test_task_family_dates_must_be_iso_civil_dates(tmp_path: Path, field: str, value: str) -> None:
    course = _copy_minimal(tmp_path)
    _write_assignment(course, content_line=f"  {field}: '{value}'")

    report = validate_course(course)

    assert not report.ok
    assert any(item.field == f"content.{field}" for item in report.diagnostics)
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_course_validation.py -k 'calendar_document_is_separate or task_family_dates_must'`

Expected: FAIL because Calendar configuration/source discovery and civil-date validation do not exist.

- [ ] **Step 3: Define the schema and parser with explicit semantic checks**

```python
# packages/schema/src/raya_schema/calendar.py
CALENDAR_KINDS = frozenset({"session", "holiday", "milestone", "cancellation"})
TASK_FAMILY_TYPES = frozenset({"assignment", "exam", "project", "task"})

def discover_calendar_documents(*, course_root: Path, source_dir: Path,
                                content_model: ContentModel, timezone: str,
                                report: ValidationReport) -> list[dict[str, Any]]:
    calendar_dir = source_dir / "_official" / "calendar"
    return _read_calendar_documents(
        calendar_dir=calendar_dir, course_root=course_root,
        content_model=content_model, timezone=timezone, report=report,
    )

def validate_official_calendar_dates(objects: list[dict[str, Any]],
                                    report: ValidationReport) -> None:
    for item in objects:
        if item.get("type") not in TASK_FAMILY_TYPES:
            continue
        for field in ("due", "available"):
            _validate_civil_date(item, field, report)
```

Add `calendar` to the required `raya-course.schema.json` properties with an object containing required `timezone`; check it with `zoneinfo.ZoneInfo`. Call the new document discovery and date validator from `validate_course` after content/official discovery. In `official._official_sources`, skip exactly the source-root `_official/calendar` directory before generic family validation; do not weaken ordered validation for any other family.

- [ ] **Step 4: Extend the negative validation matrix**

```python
@pytest.mark.parametrize("event", [
    {"id": "x", "kind": "meeting", "date": "2026-08-10", "title": "Bad"},
    {"id": "x", "kind": "session", "date": "2026-08-10", "end_time": "18:00", "title": "Bad"},
    {"id": "x", "kind": "session", "date": "2026-08-10", "start_time": "18:00", "end_time": "16:00", "title": "Bad"},
])
def test_calendar_rejects_invalid_event_semantics(
    tmp_path: Path, event: dict[str, str]
) -> None:
    course = _copy_minimal(tmp_path)
    _set_calendar_timezone(course, "America/Mexico_City")
    _write_calendar_document(course, "1_term.yaml", events=[event])
    assert not validate_course(course).ok
```

Also test invalid timezone, unordered calendar filename, duplicate document/event IDs, unresolved `page`, duplicate global occurrence ID, and a valid `cancellation` event.

- [ ] **Step 5: Run source-contract tests and commit**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_course_validation.py tests/contracts/test_static_builder.py -k 'calendar or official'`

Expected: PASS.

```bash
git add packages/schema tests/contracts/test_course_validation.py
git commit -m "Add calendar source validation"
```

### Task 2: Publish a normalized, inspectable Calendar artifact

**Files:**
- Create: `packages/schema/src/raya_schema/schemas/calendar-index.schema.json`
- Modify: `packages/schema/src/raya_schema/__init__.py`
- Modify: `packages/schema/src/raya_schema/artifacts.py`
- Modify: `packages/schema/src/raya_schema/schemas/artifact-manifest.schema.json`
- Modify: `packages/static/src/raya_static/builder.py`
- Test: `tests/contracts/test_artifact_validation.py`
- Test: `tests/contracts/test_static_builder.py`

**Interfaces:**
- Consumes: `list[dict[str, Any]]` calendar documents from Task 1, `official_by_page`, and `ContentModel`.
- Produces: `build_calendar_index(content_model: ContentModel, calendar_documents: list[dict[str, Any]], official_by_page: dict[str, list[dict[str, Any]]], timezone: str) -> dict[str, Any]`.
- Produces: `validate_calendar_index(index_path: str | Path) -> ValidationReport`; manifest key `data.calendar == 'data/calendar.json'`.

- [ ] **Step 1: Write failing artifact and occurrence tests**

```python
def test_calendar_index_emits_authored_and_both_derived_dates(tmp_path: Path) -> None:
    course = _copy_render_fixture(tmp_path)
    _set_calendar_timezone(course, "America/Mexico_City")
    _write_calendar_document(course, "1_term.yaml", events=[_holiday_event()])
    _write_assignment(course, content_lines=["  available: '2026-09-01'", "  due: '2026-09-15'"])

    assert build_course(course).ok
    index = json.loads((course / "artifact/data/calendar.json").read_text())

    assert index["timezone"] == "America/Mexico_City"
    assert {event["id"] for event in index["events"]} >= {
        "calendar:term:independence-day",
        "official:unit-assignment:available",
        "official:unit-assignment:due",
    }
```

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_artifact_validation.py tests/contracts/test_static_builder.py -k 'calendar_index or both_derived_dates'`

Expected: FAIL because neither `calendar.json` nor the manifest declaration exists.

- [ ] **Step 3: Build the public index once, then use it everywhere**

```python
def build_calendar_index(content_model: ContentModel,
                         calendar_documents: list[dict[str, Any]],
                         official_by_page: dict[str, list[dict[str, Any]]],
                         timezone: str) -> dict[str, Any]:
    events = [
        *_authored_calendar_events(calendar_documents),
        *_official_calendar_occurrences(content_model, official_by_page),
    ]
    events.sort(key=_calendar_event_sort_key)
    return {"version": 1, "timezone": timezone, "events": events,
            "kinds": _calendar_kinds(events)}

def _official_calendar_occurrences(content_model: ContentModel,
                                   official_by_page: dict[str, list[dict[str, Any]]]):
    for field, kind in (("available", "available"), ("due", "due")):
        if value := task[field]:
            yield {
                "id": f"official:{task['id']}:{field}", "origin": "official",
                "source_object_id": task["id"], "kind": kind, "date": value,
                "type": task["type"], "title": task["title"],
                "page_id": task["page_id"], "page_output_path": task["page_output_path"],
                "anchor": task["anchor"], "tags": task["tags"],
            }
```

Keep only allow-listed public strings/tags/page IDs/anchors/output targets. Author events must have no synthetic page or graph URL. Enforce global IDs again after composed occurrence creation, then write `data/calendar.json`, pass the index to the renderer in Task 3, add `calendar` to the required manifest data schema and `inspect_artifact` validators.

- [ ] **Step 4: Test empty and malicious public data boundaries**

```python
def test_empty_course_still_publishes_valid_calendar_index(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    _set_calendar_timezone(course, "America/Mexico_City")
    assert build_course(course).ok
    assert json.loads((course / "artifact/data/calendar.json").read_text()) == {
        "version": 1, "timezone": "America/Mexico_City", "events": [], "kinds": []}
```

Assert the artifact inspector rejects an absent/non-string `data.calendar` path and rejects an invalid index. Assert serialized index excludes source paths, `_official`, answers, solutions, cache keys, and `</script>` becomes safe through the renderer’s existing JSON-script escaping path.

- [ ] **Step 5: Run artifact contracts and commit**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_artifact_validation.py tests/contracts/test_static_builder.py -k 'calendar or artifact'`

Expected: PASS.

```bash
git add packages/schema packages/static/src/raya_static/builder.py tests/contracts/test_artifact_validation.py tests/contracts/test_static_builder.py
git commit -m "Publish normalized calendar data"
```

### Task 3: Replace the Schedule surface with the persistent-map Calendar agenda

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/render.css`
- Test: `tests/contracts/test_static_builder.py`
- Test: `tests/e2e/test_static_read_path.py`

**Interfaces:**
- Consumes: `calendar_index: dict[str, Any]` from Task 2.
- Produces: `_write_schedule_surface(site_dir: Path, content_model: ContentModel, calendar_index: dict[str, Any], course_title: str, language: str, skin_context: SkinContext, report: ValidationReport) -> None` and `_render_schedule_surface(content_model: ContentModel, calendar_index: dict[str, Any], course_title: str, language: str, skin_context: SkinContext) -> str` at unchanged `STATIC_SCHEDULE_PATH`.
- Produces: Server-rendered `data-raya-calendar-agenda`, event records, relative action links only for owned events, and one `data-raya-course-map` with `current_workspace='schedule'`.

- [ ] **Step 1: Write failing render and URL-prefix tests**

```python
def test_calendar_keeps_schedule_route_but_uses_calendar_copy_and_map(tmp_path: Path) -> None:
    course = _calendar_fixture(tmp_path)
    assert build_course(course).ok
    html = (course / "artifact/site/_raya/schedule/index.html").read_text()

    assert "<title>Calendar - " in html
    assert ">Calendar<" in html
    assert 'data-raya-course-map' in html
    assert 'data-raya-current-workspace="schedule"' in html
    assert 'raya-discovery-rail' not in html
    assert 'raya-command-bar' not in html
```

Add a prefix static-read test that opens `/ia_o26/_raya/schedule/`, resolves every owned-event `Open page` and `View in graph` link, and asserts each stays below `/ia_o26/`; assert an unowned holiday emits neither action.

- [ ] **Step 2: Run focused rendering tests to verify they fail**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py tests/e2e/test_static_read_path.py -k 'calendar_keeps or calendar_prefix'`

Expected: FAIL because the old Schedule shell/rail and dated-task cards are still rendered.

- [ ] **Step 3: Render semantic agenda markup from normalized records**

```python
def _render_calendar_agenda(events: list[dict[str, Any]], *, from_path: str) -> str:
    # Group by YYYY-MM, render <section><h2>, then <ol> of <article> records.
    # Use _relative_href(from_path, target) for owned actions only.
    grouped = _calendar_events_by_month(events)
    return "\n".join(
        _render_calendar_month_agenda(month, month_events, from_path=from_path)
        for month, month_events in grouped
    )

def _calendar_event_actions(event: dict[str, Any], *, from_path: str) -> str:
    if not event.get("page_output_path"):
        return ""
    return _render_relative_page_and_graph_actions(event, from_path=from_path)
```

Use the already-merged shared Course-map renderer rather than discovery command-bar/rail helpers. Preserve the route and stable `data-raya-schedule-*` compatibility hooks where they are harmless, but visible headings, skip-link copy, controls, status, and workspace links must say `Calendar`. Keep an always-visible, chronological, month-grouped agenda as no-JS content; only authored event data and public official data may be visible.

- [ ] **Step 4: Add CSS for readable agenda and small screens**

```css
.raya-calendar-agenda { display: grid; gap: 1rem; }
.raya-calendar-event { border-inline-start: .25rem solid var(--raya-calendar-kind); }
@media (max-width: 700px) { .raya-calendar-workspace { grid-template-columns: minmax(0, 1fr); } }
@media (prefers-reduced-motion: reduce) { .raya-calendar-page * { transition: none !important; } }
```

Use textual kind/type badges in addition to color. Do not introduce a modal, hover-only detail, fixed-height grid, or horizontal overflow.

- [ ] **Step 5: Run static render tests and commit**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py tests/e2e/test_static_read_path.py -k 'calendar or schedule'`

Expected: PASS.

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/render.css tests/contracts/test_static_builder.py tests/e2e/test_static_read_path.py
git commit -m "Render static course calendar agenda"
```

### Task 4: Add accessible local month enhancement and page focus

**Files:**
- Create: `packages/static/src/raya_static/calendar.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/render.css`
- Test: `tests/contracts/test_static_builder.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

**Interfaces:**
- Consumes: the escaped `calendar_index` embedded as `#raya-calendar-data` and server-rendered agenda from Task 3.
- Produces: `calendar_resources() -> CalendarResources` with local `calendar.js`; a progressive month grid with `data-raya-calendar-view`, `data-raya-calendar-prev`, `data-raya-calendar-next`, `data-raya-calendar-today`, and event-kind/type filters.
- Produces: `?page=<stable-page-id>` behavior where owned derived/authored events match, unlinked holiday/milestone events remain visible, and Clear/Escape restores all events without persistence.

- [ ] **Step 1: Write failing browser behavior tests**

```python
def test_calendar_month_controls_and_today_use_course_timezone(preview_server) -> None:
    page = preview_server.page
    page.goto("/_raya/schedule/index.html")
    page.get_by_role("button", name="Month view").click()
    assert page.locator("[data-raya-calendar-grid] table").is_visible()
    assert page.locator('[aria-current="date"]').count() == 1
    page.get_by_role("button", name="Next month").press("Enter")
    assert page.locator("[data-raya-calendar-month-caption]").inner_text() == "September 2026"
```

Add browser tests for a browser whose local zone differs from `America/Mexico_City`, Monday headers, text badges and real links, keyboard activation of both views and filters, focus restoration after view switch, agenda visibility with JavaScript disabled/narrow viewport, page focus/Clear/Escape behavior, no external requests, no fetch/XHR/storage, no overflow, and one persistent Course map/mobile drawer.

- [ ] **Step 2: Run the browser tests to verify they fail**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k 'calendar_month or calendar_timezone or calendar_page_focus'`

Expected: FAIL because `calendar.js`, month controls, and Calendar-specific focus behavior do not exist.

- [ ] **Step 3: Implement a small progressive enhancement only**

```javascript
function civilToday(timeZone, now = new Date()) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone, year: "numeric", month: "2-digit", day: "2-digit"
  }).formatToParts(now);
  return Object.fromEntries(parts.map(({ type, value }) => [type, value]));
}

function eventMatchesPage(event, pageId) {
  return !pageId || event.page_id === pageId ||
    (!event.page_id && ["holiday", "milestone"].includes(event.kind));
}
```

Parse only the embedded `#raya-calendar-data`; do not request `data/calendar.json`. Use buttons with `aria-pressed` for agenda/month view, semantic `<table>` markup with `<caption>` and weekday `<th scope="col">`, `aria-current="date"` plus a visible Today label, real anchor elements for events with targets, and a live status summary. Month selection follows the specified deterministic initial month and uses Monday-first calendar arithmetic on civil strings, not `Date.parse`/UTC conversion. Keep state in DOM/URL only.

- [ ] **Step 4: Render safe payload and local resource**

```python
calendar_payload_text = _json_script_text(calendar_index)
calendar_js_href = _relative_href(STATIC_SCHEDULE_PATH.as_posix(),
                                  Path(CALENDAR_RESOURCE_PATH) / CALENDAR_SCRIPT_NAME)
```

Write the local script beside existing render resources and add it with `defer`. Test a public title/summary containing `</script>` and assert the generated HTML has one intact JSON script element with no injected executable script.

- [ ] **Step 5: Run browser checks and commit**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k 'calendar'`

Expected: PASS.

```bash
git add packages/static tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add accessible calendar month view"
```

### Task 5: Update accepted truth and role guidance

**Files:**
- Modify: `docs/foundation/00_index.md`
- Modify: `docs/foundation/05_course_contract.md`
- Modify: `docs/foundation/06_artifact_contract.md`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/{professors,contributors,agents,students}/index.md`
- Modify: `docs/guides/es/{profesores,colaboradores,agentes,estudiantes}/index.md`
- Test: `tests/contracts/test_documentation_surfaces.py`

**Interfaces:**
- Consumes: exact schema, normalized index, and UI names implemented in Tasks 1–4.
- Produces: Foundation and role documentation that call the route `/_raya/schedule/` only as a compatibility path and call the surface `Calendar` everywhere else.

- [ ] **Step 1: Write failing documentation surface assertions**

```python
def test_calendar_contract_is_indexed_and_uses_one_timezone() -> None:
    course_contract = (FOUNDATION / "05_course_contract.md").read_text()
    artifact_contract = (FOUNDATION / "06_artifact_contract.md").read_text()
    assert "calendar.timezone" in course_contract
    assert "course/_official/calendar/" in course_contract
    assert "data/calendar.json" in artifact_contract
```

- [ ] **Step 2: Run documentation test to verify it fails**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_documentation_surfaces.py -k calendar`

Expected: FAIL because Calendar is not yet foundation truth.

- [ ] **Step 3: Document the exact authoring and safety contract**

Add one concise source example with explicit events to Course Contract; add `data/calendar.json` and manifest declaration to Artifact Contract; replace the dated-work Schedule renderer row/details with the Calendar’s agenda/month/no-network contract in Learning Renderer Contract. Update `00_index.md` only if its artifact example needs Calendar shown. In both language guide sets, explain that authors add sessions/closures/milestones explicitly, author official due/available dates once, and never manually duplicate derived homework/exams/projects/tasks in the Calendar document.

- [ ] **Step 4: Verify documentation and terminology consistency**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_documentation_surfaces.py`

Expected: PASS.

Run: `rg -n 'Official Schedule|official schedule workspace' docs packages/static/src/raya_static | tee /tmp/calendar-terminology.txt`

Expected: Only explicit compatibility-route prose remains; visible UI strings are `Calendar`.

- [ ] **Step 5: Commit documentation**

```bash
git add docs/foundation docs/guides tests/contracts/test_documentation_surfaces.py
git commit -m "Document native course calendar"
```

### Task 6: Gate, release framework, then adopt IA O26 without course-specific renderer behavior

**Files:**
- Modify (framework): files from Tasks 1–5 only
- Modify (separate `raya-lucaria/ia_o26` checkout after framework merge): `raya.yaml`, `course/_official/calendar/1_2026-o26.yaml`, and only the five known calendar-only fake task objects
- Test: framework `tests/`; IA `raya validate`, `raya build`, and live Pages verification

**Interfaces:**
- Consumes: framework `main` commit whose artifact contains `data/calendar.json` and Calendar assets; IA’s normal reusable Pages workflow pinned to that immutable SHA.
- Produces: deployed `https://rayalucaria.org/ia_o26/_raya/schedule/` using the framework feature with no DNS change and no IA-specific rendering code.

- [ ] **Step 1: Run complete framework gates sequentially**

Run: `./scripts/check.sh`

Expected: PASS.

Run only after the host gate exits successfully: `./scripts/check-docker.sh`

Expected: PASS.

Run: `./scripts/check-render-debug.sh`

Expected: PASS with updated Calendar visual/static evidence.

- [ ] **Step 2: Review, merge, and push only after green evidence**

```bash
git status --short
git log --oneline origin/main..HEAD
git push origin HEAD:main
```

Before pushing, confirm the working tree contains only the reviewed feature and no generated artifact, cache, legacy template, or unrelated user change. Record exact commit SHA and gate summaries.

- [ ] **Step 3: Create the IA O26 source adoption from current remote main**

```yaml
# raya.yaml
calendar:
  timezone: America/Mexico_City
```

Create `course/_official/calendar/1_2026-o26.yaml` with explicit Monday/Wednesday 16:00–18:00 sessions, ITAM closures, and course milestones using real date/title material already approved for the semester. Use `page: course-root` only where the landing page owns the event. Replace exactly the five existing calendar-only fake task objects with equivalent calendar entries; retain genuine official work and give future homework, projects, and exams valid `content.available`/`content.due` fields so the framework derives them automatically. Do not invent topic names, closures, or exam dates: if a particular source date/title has not been supplied or approved, omit it until it is authoritatively authored.

- [ ] **Step 4: Validate IA in an isolated checkout and inspect output**

Run: `raya validate . && raya build . && raya inspect artifact`

Expected: PASS; `artifact/data/calendar.json` includes explicit events plus every dated official object, and no duplicate occurrence IDs.

Run: `rg -n 'Calendar|data-raya-course-map|raya-discovery-rail|raya-command-bar' artifact/site/_raya/schedule/index.html`

Expected: Calendar and one Course map are present; legacy rail/bar are absent.

- [ ] **Step 5: Pin/deploy and verify the live prefixed route**

Commit IA source separately from any Pages workflow SHA update, push `raya-lucaria/ia_o26` main, wait for its Pages run, then verify with Chromium:

```text
https://rayalucaria.org/ia_o26/_raya/schedule/
```

Assert HTTP 200, one persistent Course map with Calendar active, no broken event links, agenda available with JavaScript disabled, month controls keyboard-operable, no external/browser storage requests, and no horizontal overflow on phone and desktop. Report the framework SHA, IA SHA, Actions URL, and exact live URL.

## Final Verification Checklist

- [ ] `./scripts/check.sh` passed after the final framework commit.
- [ ] `./scripts/check-docker.sh` passed after the final framework commit.
- [ ] `./scripts/check-render-debug.sh` passed after the final framework commit.
- [ ] Calendar source validation covers timezone, order, IDs, kinds, dates, times, scope, global occurrence collisions, and malformed official dates.
- [ ] Artifact inspection validates required `data/calendar.json`; an empty Calendar is emitted and valid.
- [ ] An official object with both `available` and `due` yields two different events.
- [ ] Calendar browser checks cover Mexico City date boundaries, semantic month view, no-JS agenda, keyboard controls, page focus reset, prefix-relative links, no fetch/XHR/storage, privacy, persistent map, and mobile overflow.
- [ ] Framework is merged/pushed only after gates are green; IA O26 adoption is a downstream content-only change and its live Pages deployment is verified.
