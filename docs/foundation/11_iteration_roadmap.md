# Iteration Roadmap

After the reset, build from contracts outward. Do not start with a rich renderer, backend, or web UI.

## Phase 0: Foundation

Inputs:

- these foundation docs,
- decision records,
- a clean repository,
- regenerated OpenSpec specs.

Outcome: shared truth before code.

## Phase 1: Course And Artifact Contracts

Build:

- `raya.yaml` schema,
- `content/` rules,
- learning-quanta model,
- official learning-object model,
- artifact manifest schema,
- minimal fixture course.

Target:

```bash
raya validate examples/courses/minimal
```

## Phase 2: CLI Foundation

Build:

- `raya --help`,
- `raya doctor`,
- `raya validate`,
- `raya build`,
- context detection,
- actionable diagnostics.

The CLI is the first operational surface for humans and agents.

## Phase 3: Fresh Static Builder

Build the smallest renderer that can produce:

- accessible HTML,
- navigation,
- local assets,
- artifact manifest,
- generated data indexes.

No themes, search, graph UI, slides, or complex interactivity at first.

## Phase 4: Graph And Study Seeds

Add:

- internal links and backlinks,
- graph data,
- official cards/quizzes/prompts,
- retrieval-practice hooks,
- artifact indexes that future Rennala and Sellen features can read.

Do not start with full personal study state. First prove that course-owned study objects validate, build, and remain portable.

## Bridge After Phase 4: Personal Study Contracts

After official study objects exist, define contracts for:

- private notes,
- student-created cards,
- review queues,
- spaced repetition state,
- confidence ratings,
- export of personal study data.

This phase is the bridge from static study seeds to Rennala as a dynamic study domain.

## Phase 5: Templates And Installation

Add:

- course template,
- installation template,
- local one-machine profile,
- registration model.

## Phase 6: Dynamic Domains

Only after static contracts are stable:

- identity,
- study state,
- agents,
- collaboration,
- live classroom,
- web UI,
- shared core.

Each domain should get its own proposal and tests.
