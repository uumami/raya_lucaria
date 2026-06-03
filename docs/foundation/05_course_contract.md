# Course Contract

A course is source-controlled educational material plus configuration. It must be understandable as files, not only through a database or web UI.

## Minimal Shape

```text
course/
  raya.yaml
  content/
    00_index.md
    01_unit/
      00_index.md
      01_topic.md
  assets/
  official/
    cards/
    quizzes/
    prompts/
```

`content/` is the canonical content directory for the new start. Legacy names are not part of the contract.

## Course Configuration

`raya.yaml` identifies the course and declares source locations, build options, and optional registration metadata.

Initial required ideas:

- stable `course_id`,
- human title and description,
- course language,
- content directory,
- artifact output directory,
- optional institution/course-team metadata.

Configuration should be simple enough for a professor, student, or coding agent to edit safely.

## Learning Quanta

Directories and pages are semantic learning quanta. They are not only filesystem organization.

```text
Installation
  Course
    Module / Directory
      Page
        Section
          Component / Task / Card / Prompt
```

Quanta can define navigation scope, graph scope, study scope, permissions, analytics, agent context, review ownership, and export boundaries.

At first, identity may be path-derived:

```text
course_id: algorithms-2026
path: 01_foundations/02_examples.md
```

Later, explicit metadata can stabilize long-lived references:

```yaml
quantum:
  id: foundations-examples
  type: page
  parent: foundations
```

## Official Learning Objects

Official flashcards, quizzes, prompts, examples, assignments, and projects are course-owned artifacts. They may live beside content or under `official/`, but they must be distinguishable from private, shared, and generated material.

At minimum, official learning objects should be structured enough to validate, index, export, and attach to learning quanta. They should not be only prose hidden inside rendered pages.

Initial object families:

- cards for retrieval and spaced review,
- quizzes for concept checks and practice,
- prompts for reflection, Socratic work, or agent-assisted practice,
- examples and worked examples,
- assignments, exams, projects, and tasks.

The first contract does not need to implement personal review scheduling. It should make the official source objects legible so Rennala can later add private cards, review queues, spaced repetition state, confidence ratings, mastery maps, and study planning.

```text
official object in source
          |
          v
validated object index
          |
          v
artifact data readable by static site
          |
          v
future personal/shared study state
```

## Validation

A course must be validated before build. Validation should check at least:

- required configuration,
- content directory existence,
- readable markdown/frontmatter,
- missing indexes where required,
- broken internal links,
- missing local assets,
- duplicate stable IDs,
- invalid dates or schema fields,
- generated/official authority labels,
- invalid or unscoped official learning objects.

Validation errors must be actionable.
