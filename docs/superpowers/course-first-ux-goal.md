---
id: course-first-ux-goal
title: Course-First UX Goal
status: active
workflow: superpowers
---
# Course-First UX Goal

## Authority

This is the active Superpowers goal charter for the current renderer UX work. It
incorporates `docs/superpowers/legacy-ux-convergence-audit.md` and the recent
legacy-main inspection, but it is not architecture authority by itself.

Authority order remains:

1. `docs/foundation/`;
2. accepted specs and current contracts;
3. current role documentation;
4. root guidance and package documentation;
5. committed Superpowers designs, plans, and goal charters for the active loop;
6. examples, rendered output, and old branches as evidence only.

Legacy `main` is historical UX evidence. Its Eleventy, Tailwind, Pagefind,
Cytoscape, CDN, service-worker, browser-side renderer, old JSON, and old source
layout choices must not be copied into the reset renderer.

## Current Goal

Make the static Raya renderer feel course-first:

```text
course position
  -> current page and article
  -> page-local support
  -> explicit graph/context
  -> generated workspaces
```

The course path is the primary mental model. Graph, Search, Practice, Tasks,
Schedule, and inspection surfaces remain valuable, but they must be visibly
ordered as support around the authored course rather than competing with the
course.

Course-first does not mean chrome-first. The course path is the primary
orientation model; the authored article is the primary continuous reading
surface. Future loops must not make the course map, graph, workspace chrome, or
support rails visually dominate the lesson.

The default student experience should answer quickly:

- where am I in the course;
- which unit or section owns this page;
- what should I read now;
- what headings, examples, tasks, figures, proofs, or practice are on this page;
- what explicit graph/search/practice/task/schedule surfaces support this page;
- how do I hide support chrome without losing the course path.

Minimum course hierarchy in the shell is `course -> unit/section ancestors ->
current page -> ordered neighbors`. Collapsed views must keep current page,
ancestor context, and previous/next movement readable before showing optional
workspace or documentation links.

## Salvage From Legacy Main

Keep these UX principles, rewritten under current contracts:

- **Collapsible left course rail.** The course map should remain a strong
  orientation surface. Collapsed mode must be intentional, operable, and
  compact; it must not become squeezed vertical text.
- **Collapsible right page index.** The right side should first behave like a
  page-local reading aid: current section, page contents, reading flow, page
  context, and explicit connections.
- **Explicit surface grouping.** Legacy separated `Curso`, `Contenido`, and
  `Documentacion`. Current labels should be clearer: `Course path`, `Article`,
  `Page support`, `Course tools`, `Course-owned references`, and `Inspection`.
  Repository role docs and framework docs must not appear as ordinary student
  course chrome.
- **Dense scannable cards.** Search, graph details, practice objects, tasks,
  schedule items, section landing cards, and page connections should use compact
  title, position, summary, badges/counts, and actions.
- **Breadcrumbs plus sequence.** Breadcrumbs answer structural location;
  previous/next links answer course-order movement. Both should remain visible
  without becoming progress or recommendation language.
- **Stronger visual identity.** EVA Unit 02 is a reference skin direction for
  hierarchy, contrast, chrome, rails, active states, labels, graph colors, and
  object accents. It is not framework-wide default identity unless a foundation
  decision accepts that. Long reading surfaces must stay calm and high contrast.
- **Visible comfort controls.** Text size and OpenDyslexic controls should be
  predictable and compact. They are reading comfort preferences, not course
  state.
- **Appendices and support zones.** Ordered course units should come first.
  Appendices/reference/support areas should be visibly distinct when present.

## Keep From The Current Framework

The current framework already has stronger contracts than legacy main. Future
UX loops must preserve:

- `raya.yaml` with `source: course`;
- the ordered `course/` source tree;
- colocated `_official/`, `_assets/`, and `_reviewed/` support;
- manifest-declared artifact data under `artifact/data/*.json`;
- rendered static pages under `artifact/site/`;
- build-time MathJax with local artifact resources;
- local Search, Graph, Practice, Tasks, Schedule, and Inspect surfaces;
- source-selected course and section skins through `render.skin`, `skins/`, and
  `_raya/skin.yaml`;
- local OpenDyslexic and text-size comfort controls;
- no backend, account, CDN, browser-side math conversion, or external renderer
  requirement for the static path.

## Rejected Legacy Behaviors

Do not implement these unless a later foundation decision explicitly changes the
contract:

- Eleventy, Tailwind, Pagefind, Cytoscape, or old build staging;
- old `clase/`, `glintstone.yaml`, `_site`, `clase-stage`, or `_data` shapes;
- CDN fonts, CDN graph libraries, CDN math, or external renderer requests;
- browser-side MathJax, KaTeX, Mermaid, or other conversion as the rendering
  path;
- browser-side skin/theme authority or arbitrary theme cycling;
- saved shell, sidebar, nav, graph, filter, search, practice, task, schedule, or
  reader-focus state in browser storage;
- service-worker/offline behavior copied from legacy main;
- scored quizzes, submissions, attempts, grading, analytics, progress, mastery,
  ranking, recommendations, or personalization in static HTML.

Storage remains allowed only for documented reading comfort preferences such as
OpenDyslexic and text size.

## Known Tensions

These must be resolved or explicitly deferred before implementation loops that
touch the affected surface.

### Collapsed Rail Direction

Older Superpowers specs disagree on whether collapsed `Map` and `Context` tabs
should be vertical or horizontal. The current goal prefers the legacy-inspired
utility: a collapsed rail should be compact, readable, keyboard reachable, and
able to give article width back. A loop that edits rail chrome must pick one
visual direction, test it on desktop and mobile, and update any stale docs.

### Browser Skin Override

Resolved in the **Reference skin and card density** loop. The foundation treats
skins as source-selected course/section profiles, and default rendered student
pages no longer include browser skin override selectors, scripts, toolbar
commands, or `raya:skin-override` storage. Future skin or shell loops must
preserve that contract unless a later foundation decision changes the rule.

### Guidance Drift

Some guidance still says graph UI or backlinks are out of scope while current
foundation and renderer behavior include local graph/search surfaces. Any loop
that changes graph, search, shell, or workspace labels must assess whether
`README.md`, `AGENTS.md`, foundation docs, and English/Spanish role guides need
cleanup.

### Graph Importance

The graph can be rich, but it must not outrank the course path. Graph position,
node size, relationship counts, colors, and previews are structural readability
cues only. They are not importance, progress, mastery, ranking, or
recommendation signals.

### Static Quiz Semantics

Static quiz feedback must remain local, transient, and non-tracking. Do not
salvage legacy quiz behavior that implies attempts, scoring, submissions,
analytics, grades, progress, or mastery.

## Autonomous Run Directive

The user has approved fully autonomous execution for this goal. Future agents
working on this goal must not stop to ask for confirmation, design approval,
spec approval, plan approval, review approval, or permission to continue within
the current repository and tool permissions. Treat this directive as explicit
approval to proceed through Superpowers brainstorming, design, spec writing,
planning, implementation, verification, adversarial review, documentation
updates, fixture updates, local preview, Chromium/browser probes, and goal
ledger updates for the active UX/UI effort.

When a Superpowers skill requests user approval, interpret this directive as the
standing user approval for the next conservative, evidence-backed option that
best satisfies this charter and the foundation docs. Record the chosen option
and rationale in the relevant design, plan, or goal ledger instead of waiting
for a reply. Continue from one loop to the next in the suggested order unless
current evidence shows a different loop is necessary to preserve contracts,
verification, or user trust.

Autonomous execution is not permission to weaken quality gates. Keep TDD,
verification-before-completion, adversarial review, render-debug, host/Docker
checks, role-doc impact review, and visible UX browser probes where the loop
requires them. If a gate cannot run, document the skipped-gate rationale with
cause, scope, replacement evidence, owner or resolution condition, and date, and
continue with the strongest safe evidence available when that is technically
possible.

Only stop without completing a loop when a true blocker prevents meaningful
progress: missing credentials or unavailable external state that cannot be
reasonably substituted, repeated tool/environment failure after practical
retries, a required destructive action outside the current repository that is
not explicitly allowed, or a conflict with higher-priority system/developer
safety instructions. Prefer local evidence, conservative implementation,
non-destructive edits, and reversible commits over asking the user.

## Iteration Rules

Every future UX loop under this goal must:

1. Start from current preview, render-debug, screenshots, or built-artifact
   evidence, not legacy memory alone.
2. Name one concrete UX gap.
3. Use Superpowers brainstorming before design.
4. Use TDD before implementation. The design or plan must name the first failing
   test command, expected failure, implementation target, and later passing
   evidence. For visual-only changes, update or add a browser assertion,
   render-debug expectation, or screenshot/inspection artifact before the
   implementation, and show that the assertion fails before the fix or explain
   the existing failing evidence it replaces.
5. Keep the implementation inside current package boundaries unless the user
   explicitly approves a broader contract change.
6. Request adversarial review after each meaningful part of a loop and before
   claiming completion for any loop touching renderer behavior, browser-facing
   payloads, storage, network/resource loading, role docs, foundation guidance,
   or verification gates. Review depth may scale with risk; review itself is not
   optional for those surfaces.
7. Update affected foundation, role, fixture, and test surfaces when visible
   behavior changes.
8. Preserve the tutorial pattern: visible UX or authoring workflow changes must
   update the relevant English and Spanish role guides, tutorial-style guidance,
   and render-fixture examples. If a loop records no tutorial impact, it must
   name the checked role paths, tutorial/example files, and concrete reason.
9. Keep the static path local: no external requests, no browser-side renderer,
   no backend dependency.
10. Verify desktop and mobile layouts, no horizontal overflow, keyboard access,
   collapsed-state accessibility, no private/source paths, no forbidden storage,
   and no learner-state language.
11. Before implementation, name exactly one surface, one fixture or page, one
    measurable UX assertion, and one verification command.
12. For each visible feature added or changed, deploy the built static fixture
    locally and provide the local URL for human inspection unless the work is
    purely documentation or non-rendered verification plumbing.
13. For each visible feature added or changed, run Chromium-driven subagent or
    browser probes that interact with the local URL as a reader would. Probes
    should inspect layout, reading flow, collapse/expand controls, keyboard
    reachability, visual continuity, and obvious human UX failures. If a feature
    is not visible, record why this probe is not applicable.

Adversarial reviewers should ask:

- Does this preserve source and artifact authority?
- Did we accidentally import legacy architecture?
- Does any support surface visually outrank the course path?
- Does any text imply progress, mastery, ranking, recommendations, or
  personalization?
- Does any script write storage outside documented comfort preferences?
- Did tests intercept and fail all unexpected external or runtime network
  requests?
- Did browser checks fail closed on unexpected network channels, including
  navigation, images, CSS `url()`, fonts, scripts, module imports, preloads,
  workers, service workers, `fetch`, XHR, WebSocket, EventSource, `sendBeacon`,
  iframes, and media?
- Did any browser-facing payload expose source paths, private support paths,
  hashes, cache keys, artifact internals, raw TeX, or MathJax internals?
- Did render-debug pass for visible renderer changes?
- Was the static fixture deployed locally for visible changes, and was the URL
  shared for human inspection?
- Did Chromium-driven probes interact with the local URL like a reader and
  report on layout, controls, visual continuity, and learning flow?
- Did host and Docker verification run sequentially when required?
- Are skipped gates justified with cause, scope, replacement evidence, owner or
  resolution condition, and date, and did review accept the skip?
- Are tutorial-style examples and role guidance updated when the learner or
  author experience changes?
- Do role docs in English and Spanish still explain what students, professors,
  contributors, and agents will see?

## Target Surface Order

The reader shell should communicate this order:

1. **Course path.** Course title, page position, hierarchy, current page, and
   previous/next sequence.
2. **Article.** Authored lesson content, math, numbered objects, figures,
   tables, tasks, proofs, hints, solutions, answers, callouts, and local assets.
3. **Page-local support.** Current section, page contents, reading flow, page
   context, prerequisites, tags, estimated time, and explicit connections.
4. **Course tools.** Search, Graph, Practice, Tasks, and Schedule as generated
   static support workspaces.
5. **Documentation surfaces.** Role and framework documentation remain separate
   repository/docs-course surfaces, not normal student course artifact chrome,
   unless a later contract accepts that boundary. Course artifacts may link only
   to course-owned reference/support material when the source contract allows
   it.
6. **Inspection.** Professor/contributor/agent audit pages and artifact review
   surfaces.

Generated workspace pages should preserve the same mental model. They may be
tool-first within the workspace, but they should still show the course identity,
course return path, and ordered relationship to Search, Graph, Practice, Tasks,
and Schedule.

## Suggested Next Loops

The suggested loops for this goal were completed and audited on 2026-06-30:

1. **Guidance cleanup for current graph/search reality.** Aligned stale guidance
   that still describes graph UI or backlinks as out of scope before or inside
   the first affected UX implementation loop.
2. **Course-first shell hierarchy.** Reordered and relabeled the reader and
   discovery chrome so `Course path`, `Article`, `Page support`,
   `Course tools`, course-owned references, and `Inspection` are explicit
   without making repository role docs part of normal student course chrome.
3. **Collapsed rail polish.** Resolved `Map`/`Context` collapsed-tab direction,
   improved independent and combined collapse behavior, and verified article
   width gain. Right learning-rail collapse remains desktop-only; tablet and
   mobile keep the rail body visible and accessible when collapse controls are
   hidden.
4. **Workspace course integration.** Made Search, Graph, Practice, Tasks, and
   Schedule feel like ordered course tools with clear return paths and current
   page handoffs.
5. **Reference skin and card density.** Used EVA Unit 02 as one reference skin
   direction while preserving calm article reading, high contrast, source
   selected skins, and semantic skin tokens.

Each completed loop produced its own focused Superpowers design and plan. Future
course-first renderer work should start from a new goal charter unless it is a
small follow-up to the audited behavior recorded here.

## Goal Iteration Rule

This document is the persistent goal artifact for the Superpowers loop. At the
end of each completed loop, update this document before handing off or starting
the next loop. The update should be small and factual:

- mark the loop that was completed;
- name the main files or surfaces changed;
- record verification evidence and skipped-gate rationale, if any;
- record adversarial review outcome;
- record local preview URL and Chromium probe outcome for visible changes;
- update the next recommended loop.

Do not turn this document into a detailed implementation log. Keep detailed
designs under `docs/superpowers/specs/` and detailed execution plans under
`docs/superpowers/plans/`. The goal document should remain the compact steering
surface that a fresh agent can read to continue the work safely.

## Goal Iteration Ledger

- **Current active target:** Completion audit complete; no further conservative
  loop selected for this goal.
- **Latest completed loop:** Reference skin and card density. The prior loops,
  guidance cleanup for current graph/search reality, course-first shell
  hierarchy, collapsed rail polish, and workspace course integration remain
  accepted context.
- **Latest verification evidence:** The first compact-density browser
  regression failed before implementation on fixed card padding. A later
  adversarial-review follow-up expanded the same test to Search and control
  sizing; it failed on fixed `2.5rem` controls before the CSS fix. After
  implementation, focused coverage passed for compact Search/Practice/Tasks/
  Schedule cards, action links, and controls; authored skin without browser
  override; discovery current-workspace chrome; page-focus strip; reader page
  brief; and mobile article priority. Role-doc impact updates landed in all
  English and Spanish student, professor, contributor, and agent role pages.
  Final gates passed sequentially: `git diff --check`,
  `./scripts/check-hygiene.sh`, `./scripts/check-render-debug.sh`,
  `./scripts/check.sh`, and `./scripts/check-docker.sh`. Host pytest reported
  `555 passed in 1049.20s (0:17:29)`; Docker pytest reported
  `555 passed in 1135.87s (0:18:55)`. Render-debug reported `129 check(s)`
  passed in explicit host runs and inside the host and Docker gates.
- **Latest adversarial outcome:** Review found that the first implementation
  covered repeated cards and action links but missed fixed Search, Practice,
  Tasks, and Schedule control sizing. The loop strengthened the test to measure
  Search plus control min-height, padding, and control-group gaps, then made
  workspace controls consume density variables. The same review confirmed that
  density remained profile-driven with no schema package change, browser skin
  override behavior appeared removed, and English/Spanish role docs were
  aligned.
- **Latest local preview / Chromium probe outcome:** Explicit render-debug runs
  generated local evidence at `/tmp/raya-render-debug.hXEuxA/index.html` and
  `/tmp/raya-render-debug.UmUYkz/index.html`; the host gate generated
  additional evidence under `/tmp/raya-render-debug.UmUYkz/index.html`, and the
  Docker gate generated evidence under `/tmp/raya-render-debug.s1v6Iz`. Focused
  Chromium e2e coverage interacted with Search, Practice, Tasks, and Schedule
  at `1280x900` and `390x844`, verifying compact source-selected EVA Unit 02
  card/control density, readable body text, no horizontal overflow, no browser
  storage, no external requests, and no progress/mastery/recommendation/scoring
  language. Additional browser coverage verified default student pages keep the
  authored skin without `skin-prepaint.js`, `skin-toggle.js`,
  `raya:skin-override`, `data-raya-skin-override`, or a Skin toolbar command.
- **Latest completion audit:** `docs/superpowers/specs/2026-06-30-course-first-ux-completion-audit.md`
  checked the goal against foundation authority, the active charter, current
  renderer behavior, English and Spanish role docs, browser e2e coverage,
  render-debug evidence, and host/Docker gates. The audit found no additional
  conservative UX loop required before handing the work back.
- **Next handoff action:** Preserve source-selected skin authority,
  density-driven workspace controls, the completed workspace strip, canonical
  `_raya/` handoff paths, graph first-viewport constraints, collapsed rail
  behavior, and role-doc evidence above. Start a new goal charter for future
  course-first renderer work rather than extending this one by default.

## Verification Expectations

For implementation loops derived from this goal, minimum verification gates are:

- a contract or browser e2e test added or updated before implementation, with a
  recorded first failing result for the named UX assertion or a documented
  existing failure that the implementation is intended to resolve;
- `./scripts/check-render-debug.sh` for any browser-visible renderer, layout,
  math, local resource, screenshot, or static parity change;
- `./scripts/check.sh` and `./scripts/check-docker.sh`, run sequentially, for
  any shared renderer, fixture, role-doc, foundation, or root-guidance change;
- local static deployment URL shared for any browser-visible feature, plus a
  Chromium-driven interaction probe after each visible feature or a recorded
  non-visible rationale;
- fail-closed browser request interception for no external requests across
  navigation, images, CSS `url()`, fonts, scripts, modules, preloads, workers,
  service workers, `fetch`, XHR, WebSocket, EventSource, `sendBeacon`, iframes,
  and media; no browser-side MathJax conversion; and no raw TeX leakage;
- checks that storage is limited to documented comfort preferences;
- no private paths such as `_official/`, `_drafts/`, `_partials/`, source
  paths, artifact internals, hashes, cache keys, or MathJax internals in any
  browser-facing student/default/support/workspace HTML, CSS, JS, embedded
  payload, search index, graph payload, practice payload, task payload, schedule
  payload, or public static data. Verification must enumerate emitted
  browser-facing files and parse or scan each applicable HTML, CSS, JS, JSON, and
  embedded payload. Intentional `_raya/inspect/` audit surfaces may expose
  inspection data when the current contract allows it;
- no recommendation, progress, mastery, ranking, personalization, scoring,
  submission, or grading language;
- English and Spanish role guides plus tutorial-style examples are updated, with
  exact paths named, or the loop records the exact checked paths and reason the
  change has no learner/author tutorial impact;
- adversarial subagent review after each meaningful part, with final review
  before completion;
- any skipped gate must be named in the plan with cause, scope, replacement
  evidence, owner or resolution condition, and date. Completion remains blocked
  if adversarial review does not accept the skip rationale.

## New Session Bootstrap

When a fresh conversation continues this goal, use this document as the active
handoff, not the prior chat transcript.

Start by reading:

1. `AGENTS.md`;
2. `docs/foundation/00_index.md`;
3. `docs/foundation/13_truth_surfaces.md`;
4. `docs/foundation/15_system_overview.md`;
5. `docs/foundation/19_learning_science_principles.md`;
6. `docs/superpowers/course-first-ux-goal.md`;
7. `docs/superpowers/legacy-ux-convergence-audit.md` when salvaging legacy UX
   behavior.

Use the Superpowers workflow, not OpenSpec, unless the user explicitly switches
back. Treat this document as the completed persistent goal artifact: read it at
the start to preserve the audited behavior and to decide whether a new goal
charter is needed. Do not restart the completed loop sequence by default. If the
user asks for future course-first renderer work, begin from the completion audit
and write a fresh Superpowers goal, design, and plan for the new concrete gap.
Before implementation, the new loop must name one surface, one fixture or page,
one measurable UX assertion, and one verification command. For visible UX work,
locally deploy the fixture, share the URL, and send Chromium-driven
subagent/browser probes to interact with it as a reader after each feature
addition or meaningful part.

The new session must preserve what already works: build-time MathJax, local
static resources, source-selected skins, local Search/Graph/Practice/Tasks/
Schedule/Inspect surfaces, OpenDyslexic and text-size comfort controls, numbered
objects, proof/static learning objects, render-debug parity, and the existing
course/artifact contract. It must improve and adapt the UX; it must not replace
the reset framework with legacy `main` architecture.

Any visible learner, professor, contributor, or agent UX change must carry the
matching tutorial/role-guide impact: English role docs, Spanish role docs,
render-fixture/tutorial examples, or an explicit path-by-path no-impact note.

## Relationship To The Legacy Audit

`docs/superpowers/legacy-ux-convergence-audit.md` remains the feature-level
inventory. This document is the goal-level charter. If they conflict, prefer
this charter for future UX loop selection and prefer foundation docs for
architecture authority.

## 2026-07-04 Reader Shell Parity Review

Adversarial subagent review checked the no-reader-top-bar render path,
reader/discovery command-bar separation, mobile course-map modal inertness,
accepted comfort storage, render-debug selectors, and focused browser tests.
Initial review found committed top-bar and browser skin-override gaps; follow-up
commits removed the reader top-bar render path and removed browser skin override
resources. Final adversarial re-review reported no Critical or Important
findings.

Focused verification before final gates:

- `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q ...` affected reader
  top-bar/storage tests: 12 passed in 59.23s.
- `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q ...` reader shell
  focused regression bundle: 52 passed in 65.70s.
- `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q ...` skin override
  focused checks: 4 passed in 13.55s.
