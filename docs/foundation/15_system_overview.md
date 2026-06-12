---
id: docs-system-overview
title: System Overview
summary: Newcomer map for Raya Lucaria core concepts, system parts, and ASCII diagrams.
status: ready
---
# System Overview

This is the fast map for a new contributor, professor, student, or coding agent. It summarizes the shape of Raya Lucaria without replacing the detailed foundation docs.

Read this first, then follow the specific contract files when making a proposal or implementation.

## One Sentence

Raya Lucaria is an open educational framework and commons where course teams own portable course source, Glintstone builds useful static artifacts, and optional dynamic domains add identity, study, live classroom, agents, and collaboration without making the static path dependent on a backend.

## Core Shape

```text
                             RAYA LUCARIA
                    open educational framework and commons

        +----------------------+        +----------------------+
        | Course Source        |<------>| Course Team          |
        | raya.yaml            |        | review, canon,       |
        | course/              |        | quality, ownership   |
        | _official/ _assets/  |        +----------------------+
        | _reviewed/           |
        +----------+-----------+
                   |
                   | validate and build
                   v
        +----------------------+        +----------------------+
        | Glintstone           |------->| Course Artifact      |
        | content engine       |        | site/                |
        | static builder       |        | manifest.json        |
        +----------+-----------+        | data/*.json          |
                   |                    +----------+-----------+
                   |                               |
                   | graph data                    | readable without backend
                   v                               v
        +----------------------+        +----------------------+
        | Primeval Current     |        | Student Experience   |
        | links, backlinks,    |        | read, retrieve,      |
        | wikilinks, graph     |        | reflect, contribute  |
        +----------------------+        +----------+-----------+
                                                   |
                         +-------------------------+-------------------------+
                         |                                                   |
                         v                                                   v
              +----------------------+                         +----------------------+
              | Local Workspace      |                         | Shared Installation  |
              | notes, drafts,       |                         | identity, sync,      |
              | cards, agents        |                         | review, realtime     |
              +----------------------+                         +----------------------+
```

## Static First

The static course path is the baseline. It must remain useful with no accounts, no dynamic service, and no provider dependency.

```text
source course
  |
  v
raya validate
  |
  v
raya build
  |
  v
artifact/
  site/
  manifest.json
  data/
    pages.json
    quanta.json
    links.json
    navigation.json
    indices.json
    official.json
    reviewed-outputs.json
  reviewed/
  |
  v
raya preview
  |
  v
local static review
student pages + _raya/inspect/
```

Minimum static expectations:

- readable course pages,
- navigation,
- internal links,
- accessible HTML,
- local assets,
- build-time MathJax for accepted math with local support resources,
- local static preview,
- manifest and generated data for future services.

Search, themes, graph UI, slides, offline support, and rich interactivity are future capabilities unless a current spec accepts them.

## Rendered Surfaces

The artifact can contain complete machine data while the normal page shows a focused student view.

```text
source course
      |
      v
artifact data
manifest.json + data/*.json + copied files
      |
      +--------------------+--------------------+
      |                    |                    |
      v                    v                    v
student-default       support panels       inspection
course pages          compact resource     static audit pages
                      and status views     for professors,
                                           contributors,
                                           and agents
```

Rule: complete data belongs in manifest-declared artifact surfaces; default rendered pages show only what helps reading, navigation, study, resource access, and trust. Agents and dynamic services should read artifact data, not scrape normal HTML.

## Minimum Is A Floor

The early system is intentionally small, but it is not meant to stay small. Minimal contracts create stable surfaces so pedagogy-driven capabilities can grow without rewriting the framework.

```text
                 capability grows from stable contracts

  Level 0   Foundation truth
            identity, pedagogy, authority, portability
      |
      v
  Level 1   Static course baseline
            source, validation, readable site, manifest, data indexes
      |
      v
  Level 2   Study seeds
            official cards, quizzes, prompts, tasks, quanta scopes
      |
      v
  Level 3   Personal learning state
            notes, private cards, review queues, retrieval history
      |
      v
  Level 4   Shared installation
            identity, sync, review queues, exports, audit
      |
      v
  Level 5   Full dynamic domains
            mastery, live class, agents, collaboration, analytics
```

Growth rule:

- add the smallest contract that supports a real learning behavior,
- preserve static usefulness before adding dynamic state,
- label authority before sharing or generating material,
- keep student work portable,
- split large dynamic domains into their own proposals and tests.

## Capability Ladder

Each domain has a minimum useful contract and a growth path. The foundation should make both visible.

| Domain | Minimum requirement | First growth | Later growth |
| --- | --- | --- | --- |
| Glintstone | validate and build readable static course artifacts | richer components and local assets | optional renderer capabilities after artifact contracts stabilize |
| Primeval Current | internal links and generated link data | backlinks and graph scopes | graph UI, cross-course graph, context expansion |
| Rennala | official cards, quizzes, prompts, and retrieval hooks | personal review queues and spaced repetition | mastery maps, metacognition, exam planning |
| Glintstone Key | stable IDs, registration model, role concepts | auth adapters and enrollment | multi-course trust, audit, provider migration |
| Sellen | prompt/context contracts and agent authority rules | Socratic tutor, answer comparison, card drafting | study plans and graph-aware agent workflows |
| Debate Parlor | live session concept and participation boundaries | polls, Q&A, pace/confusion signals | classroom analytics and reusable session patterns |
| Graven School | shared artifact labels and visibility scopes | discussions, annotations, peer explanations | study groups and community review |

Spaced repetition, retrieval practice, and mastery tools belong in this growth model. They are not bolt-on extras; they are how Rennala develops from official learning objects into personal and shared study systems.

## Dynamic Domains

Dynamic services are progressive enhancement. They may add state, identity, sync, realtime, agents, and community workflows, but they must read course truth through artifacts and manifests instead of scraping rendered HTML.

```text
                           Shared Installation
                                  |
                                  v
                           Glintstone Key
                    identity, registration, trust
                                  |
          +-----------------------+-----------------------+
          |                       |                       |
          v                       v                       v
       Rennala              Debate Parlor              Sellen
       study and            live classroom             agents and
       mastery              participation              tutoring
          |                       |                       |
          +-----------------------+-----------------------+
                                  |
                                  v
                            Graven School
                     collaboration and shared learning
```

Dynamic domains should get separate proposals after static contracts are stable.

## Domain Names And Packages

Raya Lucaria keeps both plain package names and canonical domain names.

```text
plain package path          canonical domain
------------------          ----------------
packages/static             Glintstone
packages/graph              Primeval Current
packages/identity           Glintstone Key
packages/study              Rennala
packages/live               Debate Parlor
packages/agents             Sellen
packages/collaboration      Graven School
packages/schema             contracts for all domains
packages/cli                operational command surface
packages/core               shared dynamic services
packages/web                browser workflows
packages/ui                 interface primitives
```

Use package names for code paths and dependency boundaries. Use domain names for conceptual ownership, proposals, UI areas, and architecture diagrams.

## Authority Boundaries

The same text, card, note, explanation, or generated answer has different authority depending on who created it and whether it was reviewed.

```text
student / professor / agent output
              |
              v
       classify authority
              |
    +---------+----------+----------------+
    |                    |                |
    v                    v                v
personal work       shared course    proposed canon
private by          visible within   review queue,
default             scope            patch, or PR
    |                    |                |
    |                    |                v
    |                    |          course team review
    |                    |                |
    |                    |                v
    |                    |          accepted change
    |                    |                |
    +--------------------+----------------+
                         |
                         v
                 explicit labels in UI,
                 data, permissions,
                 exports, and audit
```

Authority domains:

- official canon,
- static artifact,
- personal work,
- shared course material,
- generated draft,
- backend state,
- accepted change.

Agents inherit user authority. They do not get special trust because they are agents.

## Source, Artifact, State, Deployment

Do not blur these surfaces.

```text
Course Source       Course Artifact       Dynamic State       Deployment
-------------       ---------------       -------------       ----------
raya.yaml           site/                 notes               static host
course/             manifest.json         study progress      local machine
course/_official/   data/*.json           discussions         one server
course/_assets/     generated assets      sessions            on-prem
course/_reviewed/   reviewed copies       permissions         free/paid cloud

canonical           portable              scoped by           adapter layer,
course truth        build product         user/course/role    not architecture
```

Generated data is not canonical course truth. It can always be rebuilt from source.

## Ordered Content And Generated Indexes

Course source uses visible order for authoring and stable IDs for references.

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

```text
ordered source tree
        |
        v
Glintstone validation
        |
        v
generated student surfaces
  clean URLs
  breadcrumbs
  previous / next
  local indexes
  master indexes
  study-object counts
        |
        v
artifact data
  navigation.json
  indices.json
```

Order prefixes are not stable identity. Published pages use frontmatter `id`,
and durable source links use `raya:<id>` so links, official objects, future
graph data, and future study state can survive renumbering or moves.

The authored source tree is unified: rendered pages, colocated `_official/`
study seeds, colocated `_assets/`, colocated `_reviewed/` execution output,
drafts, and partials live under the learning structure they support. Support directories stay private and do not
enter navigation, local indexes, or master indexes.

## Documentation Surfaces

Documentation is an explanatory surface for contributors/collaborators, professors, students, and agents. It sits below foundation docs and accepted specs, and it stays separate from examples, course/class material, generated artifacts, and history.

```text
foundation docs       accepted specs        role documentation
seed truth            testable contracts    operational guidance
       |                    |                       |
       +---------+----------+-----------------------+
                 |
                 v
          examples and rendered docs
          fixtures or generated output,
          never higher authority
```

Role documentation uses separate English and Spanish role directories with index pages. Code, package names, commands, schema fields, paths, domain names, and stable IDs stay in English.

The live docs are renderable through Glintstone:

```text
docs/raya.yaml
      |
      v
docs/render-content/       docs/foundation/ and docs/guides/
ordered render tree  ----> readable source pages
      |
      v
docs/artifact/
generated static docs, ignored and rebuildable
```

Edit the readable docs, not generated output. Keep `docs/render-content/` aligned when new documentation pages should appear in the rendered docs site.

## Learning Loop

Every feature should know which part of learning it supports.

```text
      +-------+       +----------+       +---------+
      | Read  | ----> | Retrieve | ----> | Reflect |
      +-------+       +----------+       +----+----+
                                             |
                                             v
      +------------+   +---------+       +---------+
      | Contribute | <-| Revisit | <---- | Adapt   |
      +------------+   +---------+       +---------+
```

Examples:

- Glintstone supports reading and access.
- Primeval Current supports connection and revisiting.
- Rennala supports retrieval, spaced review, metacognition, and adaptation.
- Sellen supports Socratic practice, explanation, comparison, and agent-assisted drafts.
- Graven School supports contribution and peer learning.
- Debate Parlor supports live participation and feedback.

Feature growth should be judged against this loop. A larger system is acceptable when it deepens learning, preserves agency, and keeps authority visible.

## Build Order After Reset

The reset builds from contracts outward.

```text
Phase 0  Foundation
   |
   v
Phase 1  Course and artifact contracts
   |
   v
Phase 2  CLI foundation
   |
   v
Phase 3  Fresh static builder
   |
   v
Phase 4  Graph and study seeds
   |
   v
Bridge   Personal study contracts
   |
   v
Phase 5  Templates and installation
   |
   v
Phase 6  Dynamic domains
```

Do not start with a rich renderer, backend, or web UI. The first operational loop is:

```text
raya --help
raya doctor
raya validate <course>
raya build <course>
```

## What To Read Next

```text
Need identity and principles?       01_charter.md
Need source/artifact/state model?   02_system_model.md
Need learning model?                03_pedagogy.md
Need authority and permissions?     04_ownership_permissions.md
Need course file contract?          05_course_contract.md
Need artifact contract?             06_artifact_contract.md
Need CLI behavior?                  07_cli_contract.md
Need packages?                      08_package_boundaries.md
Need deployment profiles?           09_deployment_model.md
Need trust and registration?        10_security_registration.md
Need implementation order?          11_iteration_roadmap.md
Need legacy salvage rules?          12_legacy_salvage.md
Need authority hierarchy?           13_truth_surfaces.md
Need domain names?                  14_domain_language.md
```

If a lower surface conflicts with foundation docs, the lower surface is wrong until a new accepted decision updates the foundation.
