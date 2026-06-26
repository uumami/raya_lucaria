# Legacy UX Convergence Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a source-backed inventory that maps legacy `main` UX/UI features to current `new_rayalucaria` status and the next useful frontend/graph subgoals.

**Architecture:** This is a documentation-only Superpowers planning slice. The audit lives under `docs/superpowers/` as active workflow evidence and references foundation docs as higher authority.

**Tech Stack:** Markdown, Git history inspection, current foundation docs, current Superpowers specs/plans.

**Status: implemented.** This checklist is a historical execution record. Current
source support lives in `docs/superpowers/legacy-ux-convergence-audit.md`; later
renderer loops have already completed several subgoals that this plan originally
listed as candidates.

---

### Task 1: Add The Audit Document

**Files:**
- Create: `docs/superpowers/legacy-ux-convergence-audit.md`
- Read-only evidence: `docs/foundation/20_learning_renderer_contract.md`
- Read-only evidence: `docs/foundation/17_rendering_execution_plan.md`
- Read-only evidence: `docs/foundation/13_truth_surfaces.md`
- Read-only evidence: `docs/guides/en/contributors/index.md`
- Read-only evidence: `docs/superpowers/specs/`
- Read-only evidence: `main:src/eleventy/src/js/graph.js`
- Read-only evidence: `main:src/eleventy/src/js/sidebar.js`
- Read-only evidence: `main:src/eleventy/src/js/nav-state.js`
- Read-only evidence: `main:src/eleventy/src/js/theme-toggle.js`
- Read-only evidence: `main:src/eleventy/src/js/font-toggle.js`
- Read-only evidence: `main:src/eleventy/src/js/copy-code.js`
- Read-only evidence: `main:src/eleventy/src/js/keyboard-nav.js`
- Read-only evidence: `main:src/eleventy/src/js/search-init.js`
- Read-only evidence: `main:src/eleventy/src/js/quiz.js`
- Read-only evidence: `main:src/eleventy/src/js/toc.js`
- Read-only evidence: `main:src/eleventy/src/js/sw.js`
- Read-only evidence: `main:src/eleventy/src/js/mermaid-init.js`
- Read-only evidence: `main:src/eleventy/src/css/main.css`
- Read-only evidence: `main:src/eleventy/src/css/themes/*.css`
- Read-only evidence: `main:src/eleventy/_includes/layouts/graph.njk`

- [ ] **Step 1: Write the audit from current evidence**

Create `docs/superpowers/legacy-ux-convergence-audit.md` with these sections:

```markdown
---
id: legacy-ux-convergence-audit
title: Legacy UX Convergence Audit
status: active
---
# Legacy UX Convergence Audit

## Authority

...

## Legacy Evidence Inspected

...

## Convergence Inventory

| Legacy capability | Legacy evidence | Current status | Decision | Next action |
| --- | --- | --- | --- | --- |
| ... | ... | ... | ... | ... |

## Rejected Legacy Behaviors

...

## Remaining Candidate Subgoals

...

## Verification For Future Loops

...
```

The table must include at least graph exploration, graph layouts, graph search,
graph legend/help, collapsible sidebar/map, mobile drawer, theme switching,
OpenDyslexic/text size, copyable code, keyboard navigation, search workspace,
official task/practice surfaces, service worker/offline behavior, and quiz
interactivity.

- [ ] **Step 2: Verify no placeholders or forbidden recommendations**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
needles = (
    "".join(("TO", "DO")),
    "".join(("TB", "D")),
    "implement " + "later",
    "fill in " + "details",
)
paths = [
    Path("docs/superpowers/legacy-ux-convergence-audit.md"),
    Path("docs/superpowers/specs/2026-06-26-legacy-ux-convergence-audit-design.md"),
    Path("docs/superpowers/plans/2026-06-26-legacy-ux-convergence-audit.md"),
]
hits = []
for path in paths:
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), start=1):
        if any(needle in line for needle in needles):
            hits.append(f"{path}:{line_no}:{line}")
print("\n".join(hits))
raise SystemExit(1 if hits else 0)
PY
```

Expected: no output. Mentions of legacy external graph libraries, browser
storage, and browser-side skin switching are allowed only in rejection context,
not as recommended implementation.

- [ ] **Step 3: Inspect git diff**

Run:

```bash
git diff -- docs/superpowers/legacy-ux-convergence-audit.md docs/superpowers/specs/2026-06-26-legacy-ux-convergence-audit-design.md docs/superpowers/plans/2026-06-26-legacy-ux-convergence-audit.md
```

Expected: only the design, plan, and audit document changed.

### Task 2: Independent Review And Commit

**Files:**
- Review: `docs/superpowers/legacy-ux-convergence-audit.md`
- Review: `docs/superpowers/specs/2026-06-26-legacy-ux-convergence-audit-design.md`
- Review: `docs/superpowers/plans/2026-06-26-legacy-ux-convergence-audit.md`

- [ ] **Step 1: Request independent review**

Ask one reviewer to compare the audit against current foundation constraints
and one reviewer to compare it against legacy `main` feature evidence.

- [ ] **Step 2: Apply only concrete review fixes**

If review finds a missing legacy capability, a misclassified current feature,
or an unsafe next subgoal, update the audit table and rerun the placeholder
scan.

- [ ] **Step 3: Commit and push**

Run:

```bash
git add docs/superpowers/legacy-ux-convergence-audit.md docs/superpowers/specs/2026-06-26-legacy-ux-convergence-audit-design.md docs/superpowers/plans/2026-06-26-legacy-ux-convergence-audit.md
git commit -m "Audit legacy UX convergence"
git push origin new_rayalucaria
```

Expected: the branch pushes to `origin/new_rayalucaria`.

## Self-Review

- Spec coverage: The plan creates the audit, verifies wording, requests review,
  and commits the result.
- Placeholder scan: The plan intentionally names forbidden legacy patterns in
  verification text so agents can distinguish rejection context from
  recommendations.
- Type consistency: Documentation paths match the design and current repository
  layout.
