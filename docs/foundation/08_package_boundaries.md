# Package Boundaries

Use plain package names for filesystem clarity. Raya Lucaria domain names are still core architectural vocabulary; see `docs/foundation/14_domain_language.md`.

The package name explains where code lives. The domain name explains what responsibility the code serves.

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

Domain names such as Glintstone, Primeval Current, Glintstone Key, Rennala, Debate Parlor, Sellen, and Graven School are canonical concepts. They may appear in specs, docs, UI labels, service concepts, and diagrams. They are not required as package directory names.
