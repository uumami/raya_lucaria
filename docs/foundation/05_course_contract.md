---
id: docs-course-contract
title: Course Contract
summary: Source course shape, ordered content, learning quanta, metadata, and validation rules.
status: ready
---
# Course Contract

A course is source-controlled educational material plus configuration. It must be understandable as files, not only through a database or web UI.

## Minimal Shape

```text
course-root/
  raya.yaml
  course/
    0_index.md
    _assets/
    _official/
      cards/
        1_course_card.yaml
    _reviewed/
      execution/
        cache-script/
          reviewed.yaml
          stdout.txt
    1_unit/
      0_index.md
      1_topic/
        0_index.md
        _assets/
        _official/
          cards/
            1_topic_card.yaml
    A_reference/
      0_index.md
```

`source: course` and `course/` are the canonical authored source shape for source courses. The authored course tree is one ordered tree: rendered pages, official learning objects, local assets, reviewed execution output support, drafts, and partials live under `course/` with private support directories. Do not add source `content:`, root `official/`, or root source `assets/` to new course contracts, scaffolds, fixtures, or examples.

## Course Configuration

`raya.yaml` identifies the course and declares source locations, build options, and optional registration metadata.

Initial required ideas:

- stable `course_id`,
- human title and description,
- course language,
- authored source root,
- artifact output directory,
- optional hierarchy labels such as Unit/Topic or Chapter/Section,
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

Source order is visible in file and directory names. Numeric prefixes define the main sequence and appendix prefixes define appendix/anexo material:

```text
course/
  0_index.md
  1_foundations/
    0_index.md
    1_limits/
      0_index.md
      _official/
        prompts/
          1_limits_prompt.yaml
    2_derivatives/
      0_index.md
  2_practice/
    0_index.md
  A_reference/
    0_index.md
```

Prefixes are authoring order only. They are stripped from rendered URLs, labels, and stable IDs. Source links that must survive renumbering or moves should target stable IDs:

```markdown
Review [derivatives](raya:derivatives-rates).
```

Rendered directories use `0_index.md` as the manual landing page and metadata source. Generated local indexes and master indexes are rendered from child metadata and official learning-object scopes, but generated sections are not written back into source files.

Private support directories do not render. `_official/`, `_assets/`, `_reviewed/`, `_drafts/`, `drafts/`, `_partials/`, and other leading-underscore support paths are source support, not navigation entries. A quantum that owns `_official/`, `_assets/`, or `_reviewed/` must be a directory page with `0_index.md`; a standalone file page remains valid only when it owns no child support material.

Page frontmatter should stay compact:

```yaml
---
id: derivatives-rates
title: Derivatives as Rates of Change
nav_title: Derivatives
summary: Introduces derivatives through average and instantaneous rates.
status: ready
estimated_time: 25m
tags: [calculus, rates]
prerequisites:
  - limits-intuition
aliases:
  - old-derivatives
---
```

Stable IDs, aliases, prerequisites, official learning-object scopes, links, graph data, and future study state must not depend on order prefixes.

## Official Learning Objects

Official flashcards, quizzes, prompts, examples, assignments, exams, projects, and tasks are course-owned artifacts. Courses author them under `_official/<family>/` beside the learning quantum they support, or under source-root `course/_official/<family>/` when the object is intentionally course-level and declares an explicit scope.

At minimum, official learning objects should be structured enough to validate, index, export, and attach to learning quanta. They should not be only prose hidden inside rendered pages.

Initial object families:

- cards for retrieval and spaced review,
- quizzes for concept checks and practice,
- prompts for reflection, Socratic work, or agent-assisted practice,
- examples and worked examples,
- assignments, exams, projects, and tasks.

The first contract does not need to implement personal review scheduling. It should make the official source objects legible so Rennala can later add private cards, review queues, spaced repetition state, confidence ratings, mastery maps, and study planning.

```text
course/1_unit/1_topic/_official/cards/1_topic_card.yaml
          |
          v
validated object with inferred scope.quantum
          |
          v
artifact data readable by static site
          |
          v
future personal/shared study state
```

Colocated official object filenames use ordered prefixes for authoring and export order. The object `id` remains the durable identity; the filename prefix is not an ID. Objects under a quantum's `_official/` may omit `scope.quantum`; Glintstone infers the nearest directory page. Source-root `_official/` objects require explicit `scope.quantum`.

Colocated assets use `_assets/` beside the page or section that owns them. Rendered Markdown may reference its own `_assets/` or an ancestor `_assets/` inside the authored source tree. Rendered pages must not link into `_official/`, `_drafts/`, `_partials/`, or other non-asset support paths.

Rendered Markdown may link to `.py` and `.ipynb` files as code and notebook source support. Glintstone classifies those references by extension and validates that the target belongs to the page's own learning quantum or an accepted ancestor. Folder names such as `scripts/`, `labs/`, `code/`, and `notebooks/` are ordinary author organization choices; only validated, linked files are copied into generated reference artifacts.

Reviewed execution output uses `_reviewed/execution/<target>/` beside the quantum or accepted ancestor that owns the target. A `reviewed.yaml` manifest records target identity, source/runtime/input/review hashes, and reviewed files. `_reviewed/` is source support for reviewed course material; it must not overwrite pages, assets, official objects, code, or notebooks.

## Validation

A course must be validated before build. Validation should check at least:

- required configuration,
- authored source directory existence,
- readable markdown/frontmatter,
- missing indexes where required,
- invalid ordered source names,
- duplicate order values or clean slugs,
- duplicate stable IDs or aliases,
- broken internal links,
- broken `raya:` stable references,
- missing local or colocated assets,
- missing, stale, or escaping reviewed execution output files,
- `policy: frozen` targets without current reviewed output,
- invalid dates or schema fields,
- generated/official authority labels,
- invalid, unscoped, unordered, duplicated, or mismatched official learning objects.

Validation errors must be actionable.
