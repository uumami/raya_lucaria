# Package Boundaries

Use plain package names first. Lore names can remain in docs or UI if they help, but package names should be obvious to new contributors and agents.

## Fresh Monorepo Shape

```text
raya-lucaria/
  docs/
    foundation/
    decisions/
  packages/
    cli/
    schema/
    static/
    graph/
    study/
    agents/
    collaboration/
    live/
    identity/
    core/
    web/
    ui/
  templates/
    course/
    installation/
  examples/
    courses/
      minimal/
  tests/
    contracts/
    integration/
    e2e/
  deploy/
    compose/
    opentofu/
  tools/
```

## Package Responsibilities

| Package | Owns |
| --- | --- |
| `cli` | command surface, diagnostics, orchestration |
| `schema` | course, artifact, installation, permission, and API schemas |
| `static` | fresh static builder and artifact generation |
| `graph` | links, backlinks, quanta graph, course context maps |
| `study` | cards, quizzes, retrieval practice, mastery and review logic |
| `agents` | agent context, prompt contracts, BYOK/local agent workflows |
| `collaboration` | annotations, discussions, shared artifacts, peer learning |
| `live` | classroom sessions, polls, Q&A, pace/confusion signals |
| `identity` | auth adapters, roles, enrollment, permission checks |
| `core` | API, jobs, persistence, realtime, registry, audit, provider adapters |
| `web` | browser workflows for students, professors, admins, and review |
| `ui` | shared UI primitives, accessibility patterns, design tokens |

## Dependency Rule

The CLI can orchestrate packages. Domain packages should not depend on UI or deployment details. Provider adapters belong at the edges.

```text
schemas -> packages -> cli/web -> deploy adapters
```

Schemas and contracts should be lower-level than implementations.

## Naming Rule

Public repo and package names should be clear:

- `raya-lucaria`
- `raya-lucaria-cli`
- `raya-lucaria-core`
- `raya-lucaria-course-template`

Lore names are optional labels, not required package names.
