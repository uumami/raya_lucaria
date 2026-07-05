---
id: superpowers-guidance-graph-search-reality
title: Guidance Graph/Search Reality Cleanup Design
status: active
workflow: superpowers
---
# Guidance Graph/Search Reality Cleanup Design

## Context

Current foundation authority says local static Search and Graph discovery
surfaces are accepted renderer behavior under
`docs/foundation/20_learning_renderer_contract.md`. Root guidance and a few
foundation summary pages still contain older reset wording that describes graph
UI, backlinks, search, or prose-derived search as future or out of scope without
separating current local static surfaces from deferred dynamic/external work.

The loop is documentation-only. It does not change renderer behavior, fixtures,
course artifacts, or role workflows.

## Chosen Approach

Use a narrow status split:

- current: local static Search and Graph surfaces generated from current
  artifact data under the learning renderer contract;
- deferred: graph scopes, cross-course graph, graph editing, inferred related
  pages, external/full-text search services, dynamic graph/search state, and
  broader web UI/backend work.

This is safer than rewriting the roadmap broadly because the early roadmap still
has useful historical sequencing language. It also avoids treating current local
static Search/Graph as dynamic domains.

## Affected Surfaces

- `README.md`: replace the stale rich-rendering baseline sentence that still
  lists graph UI, backlinks, and search-adjacent work as out of scope.
- `AGENTS.md`: align package-boundary guidance with the current local static
  Search/Graph baseline.
- `docs/foundation/06_artifact_contract.md`: clarify that its old future list
  refers to capabilities beyond the initial artifact floor, while current local
  Search/Graph are defined by the learning renderer contract.
- `docs/foundation/18_known_missing_work.md`: narrow deferred Graph/Search work
  so it no longer claims prose-derived local search is missing.
- `scripts/check-hygiene.sh` and `tests/contracts/test_hygiene_scripts.py`: add
  a regression check for stale current-status wording.
- `docs/superpowers/course-first-ux-goal.md`: update the Goal Iteration Ledger
  when the loop is complete.

## TDD Gate

First failing test command:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_hygiene_scripts.py::test_check_hygiene_rejects_stale_graph_search_guidance
```

Expected first result: fail because the test does not exist. After adding the
test and script scan, the focused test should fail against the current fixture
phrase. After editing guidance, the focused test and `scripts/check-hygiene.sh`
should pass.

## Verification

Run these checks after edits:

- `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_hygiene_scripts.py::test_check_hygiene_rejects_stale_graph_search_guidance`
- `./scripts/check-hygiene.sh`
- `rg -n "graph UI, backlinks|Full-text search indexes, prose-derived search|Search, themes, graphs, offline support" README.md AGENTS.md docs/foundation docs/guides openspec/config.yaml`
- `git diff --check`

`./scripts/check.sh` and `./scripts/check-docker.sh` are required for final
archive evidence because this touches root guidance and foundation docs. Run
them sequentially after focused verification unless an environment blocker
prevents it.

Render-debug, local preview, and Chromium probes are not applicable because no
browser-visible renderer output changes in this loop.
