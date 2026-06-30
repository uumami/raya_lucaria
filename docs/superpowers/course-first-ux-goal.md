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

The foundation treats skins as source-selected course/section profiles. The
current static code also contains a `localStorage` path named
`raya:skin-override`. Under current foundation and role docs, browser storage
must not store skin authority. Treat this as a contract violation unless and
until a later foundation decision changes the rule. Future skin or shell loops
must not expand this behavior. A dedicated cleanup or contract-hardening loop
must remove it or first update the foundation and role docs through an accepted
workflow. Any loop touching shell, skin, storage, or reader JavaScript must fail
its completion review while browser skin authority remains in default rendered
student pages.

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

The likely next loops, in order, are:

1. **Guidance cleanup for current graph/search reality.** Align stale guidance
   that still describes graph UI or backlinks as out of scope before or inside
   the first affected UX implementation loop.
2. **Course-first shell hierarchy.** Reorder and relabel the reader and
   discovery chrome so `Course path`, `Article`, `Page support`,
   `Course tools`, course-owned references, and `Inspection` are explicit
   without making repository role docs part of normal student course chrome.
3. **Collapsed rail polish.** Resolve `Map`/`Context` collapsed-tab direction,
   improve independent and combined collapse behavior, and verify article width
   gain. Right learning-rail collapse remains desktop-only; tablet and mobile
   must keep the rail body visible and accessible when collapse controls are
   hidden.
4. **Workspace course integration.** Make Search, Graph, Practice, Tasks, and
   Schedule feel like ordered course tools with clear return paths and current
   page handoffs.
5. **Reference skin and card density.** Use EVA Unit 02 as one reference skin
   direction while preserving calm article reading, high contrast, source
   selected skins, and semantic skin tokens.

Each loop should produce its own focused Superpowers design and plan. This
charter sets the target and guardrails; it is not an implementation plan. UX
loops that change learner, professor, contributor, or agent behavior should
carry a tutorial or role-guide update beside the code and fixture changes.

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

- **Current active target:** Guidance cleanup for current graph/search reality,
  followed by course-first shell hierarchy.
- **Latest completed loop:** Course-first UX goal charter created and hardened
  through adversarial review.
- **Latest verification evidence:** `git diff --check` passed for the
  charter-only change before the current charter commit.
- **Latest adversarial outcome:** Three independent review agents reported no
  blocking findings after the second re-check.
- **Latest local preview / Chromium probe outcome:** Not applicable for the
  charter-only change; required after visible renderer features.
- **Next handoff action:** In the next session, read this document, run
  Superpowers brainstorming, then update this ledger when the next loop finishes.

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
back. Treat this document as the persistent goal artifact: read it at the start,
use it to pick the next loop, and update its **Goal Iteration Ledger** before
ending a completed loop or handing off to another conversation. The next loop
should start with Superpowers brainstorming. If the user has not redirected the
work, begin with **Guidance cleanup for current graph/search reality**, then
move to **Course-first shell hierarchy**. Before implementation, the loop must
name one surface, one fixture or page, one measurable UX assertion, and one
verification command. For visible UX work, locally deploy the fixture, share the
URL, and send Chromium-driven subagent/browser probes to interact with it as a
reader after each feature addition or meaningful part.

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
