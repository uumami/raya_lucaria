# Static Wikilink Resolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve course-local `[[wikilinks]]` during validation/build so rendered pages and graph data gain explicit local links without browser-side resolution.

**Architecture:** Add a small schema-owned wikilink utility for unfenced extraction and page-key resolution. Use it from validation, static link graph generation, and Markdown rendering preprocessing. Keep browser output as normal static HTML links.

**Tech Stack:** Python schema utilities, static builder, MarkdownIt rendering, pytest contract tests, focused render/debug verification.

---

### Task 1: Failing Tests

**Files:**
- Modify: `tests/contracts/test_course_validation.py`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add validation tests**

Add tests proving a unique wikilink validates and missing/ambiguous wikilinks fail with fields like `wikilink:Topic`.

- [ ] **Step 2: Add build/render/graph tests**

Add a temporary course fixture in `test_static_builder.py` where `[[First Topic|topic page]]` renders as a local link and contributes a `content` edge in `data/links.json` and `data/graph.json`.

- [ ] **Step 3: Verify red**

Run the focused validation/build tests. Expected: failures because wikilinks currently render as plain bracket text and do not validate or enter graph links.

### Task 2: Shared Wikilink Utility

**Files:**
- Create: `packages/schema/src/raya_schema/wikilinks.py`
- Modify: `packages/schema/src/raya_schema/course.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Implement extraction and resolution**

Provide unfenced wikilink extraction and a resolver built from the current `ContentModel`.

- [ ] **Step 2: Validate**

Call the resolver from `validate_course()` and report missing or ambiguous targets before publishing.

- [ ] **Step 3: Render**

Preprocess resolved wikilinks into ordinary Markdown links before MarkdownIt parsing.

- [ ] **Step 4: Graph**

Add resolved wikilink targets as `content` links in `links.json`, which feeds `graph.json`.

### Task 3: Docs And Verification

**Files:**
- Modify: `docs/foundation/05_course_contract.md`
- Modify: `docs/foundation/18_known_missing_work.md`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: role docs under `docs/guides/en/` and `docs/guides/es/`

- [ ] **Step 1: Update docs**

Document the static, course-local wikilink form and its non-goals.

- [ ] **Step 2: Verify**

Run focused tests, `./scripts/check-render-debug.sh`, and request independent review before commit/push.
