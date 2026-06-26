# Discovery Fuzzy Matching Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add typo-tolerant local filtering to Practice, Tasks, and Schedule discovery workspaces.

**Architecture:** Reuse the Search workspace's conservative local Levenshtein/fuzzy matching pattern inside each independent workspace script. Keep all payloads, schemas, links, page focus, filters, and static constraints unchanged.

**Tech Stack:** Python-generated local JavaScript resources in `packages/static/src/raya_static/{practice,tasks,schedule}.py`, pytest contract tests, Playwright e2e tests.

**Status: implemented.** This checklist is a historical execution record. Current
source support lives in local `fuzzyMatch` helpers for Practice, Tasks, and
Schedule plus contract/browser checks.

---

### Task 1: RED Tests For Fuzzy Workspace Filtering

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add static script assertions**

In existing Practice, Tasks, and Schedule static builder tests, assert each local script contains:

```python
assert "function levenshtein" in practice_script
assert "function fuzzyMatch" in practice_script
assert "function levenshtein" in tasks_script
assert "function fuzzyMatch" in tasks_script
assert "function levenshtein" in schedule_script
assert "function fuzzyMatch" in schedule_script
```

- [ ] **Step 2: Add browser assertions for misspelled Practice query**

In `test_preview_serves_static_official_practice_workspace`, after the existing exact `retrieval` query assertions, clear the search and query `retrievel`:

```python
page.click("#raya-practice-clear")
page.fill("#raya-practice-search", "retrievel")
page.wait_for_function(
    """() => document
      .querySelector('#raya-practice-status')
      ?.textContent
      ?.includes('1 visible practice object')"""
)
assert page.locator('[data-raya-practice-object="first-topic-prompt"]').is_visible()
```

- [ ] **Step 3: Add browser assertions for misspelled Tasks query**

In `test_preview_serves_static_official_tasks_workspace`, after the existing exact `retrieval` task query assertions, clear the search and query `retrievel`:

```python
page.click("#raya-tasks-clear")
page.fill("#raya-tasks-search", "retrievel")
page.wait_for_function(
    """() => document
      .querySelector('#raya-tasks-status')
      ?.textContent
      ?.includes('2 visible tasks')"""
)
assert page.locator('[data-raya-task-object="unit-assignment"]').is_visible()
assert page.locator('[data-raya-task-object="unit-project"]').is_visible()
```

- [ ] **Step 4: Add browser assertions for misspelled Schedule query**

In the Schedule section of `test_preview_serves_static_official_tasks_workspace`, after the existing exact `retrieval` schedule query assertions, clear the search and query `retrievel`:

```python
schedule.click("#raya-schedule-clear")
schedule.fill("#raya-schedule-search", "retrievel")
schedule.wait_for_function(
    """() => document
      .querySelector('#raya-schedule-status')
      ?.textContent
      ?.includes('2 visible schedule items')"""
)
assert schedule.locator('[data-raya-schedule-item="unit-assignment"]').is_visible()
assert schedule.locator('[data-raya-schedule-item="unit-project"]').is_visible()
```

- [ ] **Step 5: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace -q -x
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_practice_workspace tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_tasks_workspace -q -x
```

Expected before implementation: failures for missing `levenshtein`/`fuzzyMatch`
script tokens or misspelled queries not finding visible objects.

### Task 2: Implement Practice Fuzzy Matching

**Files:**
- Modify: `packages/static/src/raya_static/practice.py`

- [ ] **Step 1: Add helpers after `normalize(value)`**

Add:

```javascript
  function levenshtein(a, b) {
    const left = normalize(a);
    const right = normalize(b);
    if (left.length === 0) return right.length;
    if (right.length === 0) return left.length;
    const previous = Array.from({ length: right.length + 1 }, (_, index) => index);
    const current = Array(right.length + 1).fill(0);
    for (let i = 1; i <= left.length; i += 1) {
      current[0] = i;
      for (let j = 1; j <= right.length; j += 1) {
        const cost = left[i - 1] === right[j - 1] ? 0 : 1;
        current[j] = Math.min(
          previous[j] + 1,
          current[j - 1] + 1,
          previous[j - 1] + cost
        );
      }
      for (let j = 0; j <= right.length; j += 1) {
        previous[j] = current[j];
      }
    }
    return previous[right.length];
  }

  function fuzzyMatch(queryText, targetText) {
    const needle = normalize(queryText);
    const haystack = normalize(targetText);
    if (!needle) return true;
    if (haystack.includes(needle)) return true;
    const words = haystack.split(/[\s_\/-]+/).filter(Boolean);
    if (words.some((word) => word.startsWith(needle))) return true;
    const threshold = needle.length <= 3 ? 1 : Math.floor(needle.length * 0.35);
    return words.some((word) => levenshtein(needle, word) <= threshold) ||
      (haystack.length <= 28 && levenshtein(needle, haystack) <= threshold);
  }
```

- [ ] **Step 2: Use helper in `matchesSearch`**

Replace:

```javascript
    return haystack.includes(query);
```

with:

```javascript
    return fuzzyMatch(query, haystack);
```

- [ ] **Step 3: Verify Practice focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_practice_workspace -q
```

Expected after Task 2: Practice checks pass; Tasks/Schedule checks still fail
until their scripts are updated.

### Task 3: Implement Tasks And Schedule Fuzzy Matching

**Files:**
- Modify: `packages/static/src/raya_static/tasks.py`
- Modify: `packages/static/src/raya_static/schedule.py`

- [ ] **Step 1: Add the same helpers to Tasks**

Add the `levenshtein` and `fuzzyMatch` helper block after `normalize(value)` in
`tasks.py`, then replace `return haystack.includes(query);` with:

```javascript
    return fuzzyMatch(query, haystack);
```

- [ ] **Step 2: Add the same helpers to Schedule**

Add the `levenshtein` and `fuzzyMatch` helper block after `normalize(value)` in
`schedule.py`, then replace `return haystack.includes(query);` with:

```javascript
    return fuzzyMatch(query, haystack);
```

- [ ] **Step 3: Verify focused suite**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_practice_workspace tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_tasks_workspace -q
```

Expected: all focused checks pass.

### Task 4: Documentation And Review

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `tests/contracts/test_documentation_surfaces.py`

- [ ] **Step 1: Update contract wording**

Document that Practice, Tasks, and Schedule local text filters may use
approximate matching over public embedded payload fields and visible text.

- [ ] **Step 2: Update student guides**

Add one English and one Spanish sentence explaining that discovery workspace
text filters can tolerate small typos, without implying recommendations or
personalization.

- [ ] **Step 3: Add docs-surface assertion**

Add a compact test assertion in `tests/contracts/test_documentation_surfaces.py`
for the new contract and guide wording.

- [ ] **Step 4: Request independent review**

Ask one reviewer to check current contract/static boundary alignment and one
reviewer to check browser UX/test quality.

### Task 5: Full Verification, Commit, Push

**Files:**
- Review all changed files.

- [ ] **Step 1: Run render-debug**

```bash
./scripts/check-render-debug.sh
```

Expected: `check-render-debug: passed`.

- [ ] **Step 2: Run full host gate**

```bash
./scripts/check.sh
```

Expected: `check: passed`.

- [ ] **Step 3: Commit and push**

```bash
git add docs/superpowers/specs/2026-06-26-discovery-fuzzy-matching-parity-design.md docs/superpowers/plans/2026-06-26-discovery-fuzzy-matching-parity.md packages/static/src/raya_static/practice.py packages/static/src/raya_static/tasks.py packages/static/src/raya_static/schedule.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/es/estudiantes/index.md tests/contracts/test_static_builder.py tests/contracts/test_documentation_surfaces.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add fuzzy discovery workspace filters"
git push origin new_rayalucaria
```
