# Artifact Contract

A course artifact is the portable output of a course build. It must be useful as static files and readable by optional dynamic services.

## Required Outputs

```text
artifact/
  site/                 static read path
  manifest.json         machine-readable artifact contract
  data/
    pages.json
    quanta.json
    links.json
    official.json
  assets/
```

The exact renderer can change. The artifact contract should not depend on a specific static-site generator, JavaScript framework, or CSS pipeline.

## Manifest

The manifest is the backend-readable and agent-readable entrypoint.

It should include:

- `artifact_version`,
- `course_id`,
- `course_version_id` or content hash,
- generated timestamp,
- source schema version,
- page/quanta index locations,
- official learning-object indexes,
- static site root,
- optional graph/search data locations.

Optional shared services must read artifacts through the manifest, not by scraping rendered HTML.

## Static Site

The static site should remain useful without accounts, JavaScript-heavy dynamic behavior, or network services beyond static hosting.

Minimum expectations:

- course landing page,
- page rendering,
- navigation,
- internal links,
- accessible HTML,
- local assets.

Search, themes, graphs, offline support, slides, and interactive components are future capabilities, not initial requirements.

## Data Products

Generated data should make the course legible to future domains:

- graph and backlinks,
- study scopes,
- official cards/quizzes/prompts,
- task lists,
- citation/source map,
- quanta tree,
- asset map.

Generated data is not canonical course truth. It can always be rebuilt from source.

## Study Seed Data

Artifacts should expose official learning objects as seed data for future study systems. Static artifacts may include cards, quizzes, prompts, tasks, and quanta scopes, but they should not contain private review history or personal mastery state.

```text
course source official/
          |
          v
artifact data official indexes
          |
          v
Rennala can later add:
  private cards
  review queues
  spaced repetition state
  confidence ratings
  mastery maps
```

This keeps the official base portable while allowing dynamic study features to grow around it.

## Builder Boundary

The first static builder should be fresh code. Legacy implementations may be mined for ideas, but no renderer dependency is part of the framework contract.
