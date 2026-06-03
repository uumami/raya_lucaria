# Domain Language

Raya Lucaria's named domains are core architectural vocabulary. They are not decorative labels, and they are not legacy implementation details by themselves.

The reset keeps two naming layers:

- plain package and path names for inspectable code,
- Raya Lucaria domain names for product, pedagogy, and responsibility boundaries.

Both layers are authoritative when used in the right place.

## Canonical Domains

| Name | Meaning | Responsibility |
| --- | --- | --- |
| Raya Lucaria | the academy, framework, and commons | the whole system and its public identity |
| Glintstone | content engine and static course path | source courses, validation, build pipeline, static artifacts, accessible course sites |
| Primeval Current | knowledge graph | links, backlinks, wikilinks, quanta graph, course context maps |
| Glintstone Key | entry and trust | identity, authentication, registration, enrollment, roles, permission checks |
| Rennala | study and mastery | cards, quizzes, retrieval practice, spaced review, metacognition, mastery state |
| Debate Parlor | live classroom | sessions, polls, Q&A, pace signals, confusion signals, synchronous participation |
| Sellen | learning and coding agents | AI assistant, Socratic tutor, BYOK/local agent workflows, prompt contracts, context assembly |
| Graven School | collaboration and shared learning | discussions, annotations, peer explanations, shared artifacts, study groups |

These names should appear in proposals, specs, UI labels, documentation, and service concepts when they clarify responsibility.

## Package Mapping

Plain package names remain the filesystem default because they are easy for new contributors and coding agents to inspect.

| Package | Domain language |
| --- | --- |
| `static` | Glintstone |
| `graph` | Primeval Current |
| `identity` | Glintstone Key |
| `study` | Rennala |
| `live` | Debate Parlor |
| `agents` | Sellen |
| `collaboration` | Graven School |
| `schema` | contracts for all domains |
| `cli` | operational command surface for all domains |
| `core` | shared dynamic services, registry, jobs, persistence, audit, adapters |
| `web` | browser workflows across domains |
| `ui` | shared interface primitives across domains |

Package names and domain names should not fight each other. Use package names for code paths and dependency boundaries. Use domain names for conceptual ownership, user-facing areas, proposals, and architectural diagrams.

## Naming Rules

Use a domain name when the work is about a stable Raya Lucaria capability:

- "Glintstone validates and builds static course artifacts."
- "Primeval Current owns backlinks and graph data."
- "Rennala stores study state and review schedules."
- "Sellen consumes course context but does not change canon without review."

Use a plain package name when the work is about repository structure:

- `packages/static`
- `packages/graph`
- `packages/study`
- `packages/agents`

On first mention in technical docs, pair them when useful:

```text
Glintstone (`packages/static`)
Primeval Current (`packages/graph`)
Rennala (`packages/study`)
```

## Reset Boundary

Canonical domain names do not make old implementation choices canonical.

Glintstone survives as the static/content-engine domain. Old names such as `glintstone.yaml` or `clase/`, old Eleventy/Tailwind/Pagefind renderer assumptions, old generated JSON shapes, and old examples remain historical unless a current foundation decision or regenerated spec accepts them.

The same rule applies to every domain. Salvage the principle and domain responsibility, then define the new contract.
