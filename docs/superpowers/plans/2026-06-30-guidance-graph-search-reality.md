# Guidance Graph/Search Reality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align current repository guidance with the accepted local static Search and Graph renderer surfaces.

**Architecture:** Add a focused hygiene regression for stale graph/search status wording, then update only the guidance surfaces that contradict the current foundation contract. Keep current local static Search/Graph distinct from deferred dynamic, external, cross-course, and inferred graph/search features.

**Tech Stack:** Bash hygiene script, Python pytest contract tests, Markdown guidance.

---

### Task 1: Add The Stale Guidance Regression

**Files:**
- Modify: `scripts/check-hygiene.sh`
- Modify: `tests/contracts/test_hygiene_scripts.py`

- [x] **Step 1: Run the focused test before adding it**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_hygiene_scripts.py::test_check_hygiene_rejects_stale_graph_search_guidance
```

Expected: FAIL with no matching test found.

- [x] **Step 2: Add the fixture test**

Add `test_check_hygiene_rejects_stale_graph_search_guidance` to
`tests/contracts/test_hygiene_scripts.py`. The test should create a minimal
hygiene root, write stale guidance such as
`graph UI, backlinks, wikilinks, and expanded external link policy remain out of
scope until later proposals` to `README.md`, run `scripts/check-hygiene.sh
--root <fixture>`, and assert a nonzero exit with the label
`stale graph/search current-status guidance`.

- [x] **Step 3: Add the hygiene scan**

In `scripts/check-hygiene.sh`, add
`check_stale_graph_search_guidance()` using `reject_matches` with stale phrases
that should not appear in current guidance:

```text
graph UI, backlinks, wikilinks, and expanded external link policy remain out of scope until later proposals|Renderer, TypeScript/web UI, backend, identity, dynamic study state, graph UI, backlinks, wikilinks, heading-anchor validation, and external link policy remain out of scope until later proposals|Search, themes, graphs, offline support, slides, and interactive components are future capabilities, not initial requirements|Full-text search indexes, prose-derived search, external search services, and dynamic search state
```

Scan `README.md`, `AGENTS.md`, `docs/foundation`, `docs/guides`,
`openspec/config.yaml`, `openspec/specs`, and `packages`, excluding historical
Superpowers and archived OpenSpec paths through the existing `reject_matches`
defaults.

- [x] **Step 4: Verify the focused test passes**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_hygiene_scripts.py::test_check_hygiene_rejects_stale_graph_search_guidance
```

Expected: PASS.

- [x] **Step 5: Verify the repository currently fails the new hygiene scan**

```bash
./scripts/check-hygiene.sh
```

Expected: FAIL with current stale hits in `README.md`, `AGENTS.md`,
`docs/foundation/06_artifact_contract.md`, and
`docs/foundation/18_known_missing_work.md`.

### Task 2: Update Guidance Surfaces

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `docs/foundation/06_artifact_contract.md`
- Modify: `docs/foundation/18_known_missing_work.md`
- Modify: `docs/superpowers/course-first-ux-goal.md`

- [x] **Step 1: Update root guidance**

In `README.md` and `AGENTS.md`, replace stale out-of-scope wording with the
current split:

- local static Search and Graph are current renderer capabilities under
  `docs/foundation/20_learning_renderer_contract.md`;
- TypeScript/web UI, backend, identity, dynamic study state, graph scopes,
  cross-course graph, graph editing, inferred relationships, wikilink
  expansion, and expanded external link policy remain future work.

- [x] **Step 2: Update foundation summaries**

In `docs/foundation/06_artifact_contract.md`, clarify that the initial artifact
floor did not require Search/Graph, but current local static Search/Graph are
defined by `20_learning_renderer_contract.md`.

In `docs/foundation/18_known_missing_work.md`, remove prose-derived local search
from missing work and keep deferred Graph/Search focused on dynamic, external,
cross-course, inferred, editing, and full-text-service capabilities.

- [x] **Step 3: Update the goal ledger**

In `docs/superpowers/course-first-ux-goal.md`, set the latest completed loop to
guidance cleanup for current graph/search reality. Record focused test and
hygiene evidence, skipped non-visible gates, and next loop as course-first shell
hierarchy.

- [x] **Step 4: Run focused verification**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_hygiene_scripts.py::test_check_hygiene_rejects_stale_graph_search_guidance
./scripts/check-hygiene.sh
rg -n "graph UI, backlinks|Full-text search indexes, prose-derived search|Search, themes, graphs, offline support" README.md AGENTS.md docs/foundation docs/guides openspec/config.yaml
git diff --check
```

Expected: pytest, hygiene, and diff-check pass. The `rg` command should return
no matches.

- [x] **Step 5: Run final required gates**

Run sequentially:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both pass. If an environment issue prevents a gate, record the skipped
gate rationale in the goal ledger with date, cause, scope, replacement evidence,
owner or resolution condition.

### Task 3: Review

**Files:**
- Review all modified files from Tasks 1 and 2.

- [x] **Step 1: Request adversarial review**

Ask the reviewer to check whether the cleanup preserves the current Search/Graph
contract, avoids moving dynamic/external graph/search into current scope, keeps
role-doc impact correctly scoped as no user-facing behavior change, and uses
hygiene checks that are specific enough to avoid blocking historical
Superpowers docs.

- [x] **Step 2: Address blocking findings**

Fix critical or important findings before claiming the loop is complete.

- [x] **Step 3: Final verification**

Repeat any focused commands affected by review fixes and confirm `git diff
--check` remains clean.

## Self-Review

- Spec coverage: the plan covers stale-surface detection, guidance edits, goal
  ledger update, verification, and review.
- Placeholder scan: no placeholders remain.
- Scope: documentation-only; no renderer, fixture, or browser output changes.

## Completion Evidence

- Focused regression:
  `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_hygiene_scripts.py::test_check_hygiene_rejects_stale_graph_search_guidance`
  passed after implementation.
- Hygiene scan: `./scripts/check-hygiene.sh` passed after guidance cleanup.
- Stale-term scan:
  `rg -n "graph UI, backlinks|Full-text search indexes, prose-derived search|Search, themes, graphs, offline support" README.md AGENTS.md docs/foundation docs/guides openspec/config.yaml`
  returned no stale current-guidance matches after cleanup.
- Final gates for the full course-first goal later passed sequentially:
  `./scripts/check.sh` and `./scripts/check-docker.sh`.
- Adversarial review was requested during the loop and no remaining blocker
  from this guidance-cleanup plan is open.
