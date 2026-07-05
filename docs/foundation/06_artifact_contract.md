---
id: docs-artifact-contract
title: Artifact Contract
summary: Portable artifact shape for static sites, manifests, data indexes, and assets.
status: ready
---
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
    navigation.json
    indices.json
    numbered-objects.json
    official.json
    reviewed-outputs.json
  assets/
  files/
  reviewed/
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
- page/quanta/link/navigation/index data locations,
- numbered object index location,
- official learning-object indexes,
- reviewed execution output indexes,
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
- local assets,
- pre-rendered math and local MathJax support resources when pages use accepted math.

Build-time math resources belong to the static read path, for example
`artifact/site/_raya/render/math/mathjax.css` and
`artifact/site/_raya/render/math/fonts/`. Generated pages must link them with
relative deployment-neutral URLs. Static hosting and `raya preview` should use
the same pre-rendered HTML, CSS, and font files; neither path should require a
CDN, configured host, backend, Python, Node, or browser-side MathJax conversion.

`raya preview <course>` is the local review workflow for this static site. It serves the generated `artifact/site/` read path and exposes the inspection URL for reviewers, but it does not make rendered HTML the authority surface and does not execute course code.

The initial artifact floor did not require Search, themes, graphs, offline
support, slides, or interactive components. Current local static Search and
Graph discovery surfaces are now defined by
`20_learning_renderer_contract.md`; offline support, slides, broader
interactive components, external search services, dynamic graph/search state,
and cross-course graph capabilities remain future work.

## Rendered Surface Discipline

Rendered HTML is a view over artifact data, not the authority surface. Glintstone should keep ordinary pages focused and move verbose internals to inspection or machine surfaces.

```text
artifact data                 rendered surfaces
-------------                 -----------------
manifest.json + data/*.json   student-default pages
copied files                  compact support panels
reviewed copies               static inspection pages
                              machine-only data
```

Surface tiers:

- `student-default`: authored learning content, navigation, indexes, local assets, selected study/resource cues.
- `support-panel`: compact status, labels, summaries, and deployment-neutral links for references, reviewed output, or study support.
- `inspection`: static audit pages for professors, contributors, and agents, generated from artifact data.
- `machine-only`: manifest-declared JSON and copied files for tools and future services.

Default pages should not dump raw JSON, source hashes, cache keys, artifact storage paths, runtime profile internals, or reviewed-output freshness details into the reading flow. Those details remain available through `manifest.json`, `data/*.json`, copied artifact files, and optional static inspection pages.

## Data Products

Generated data should make the course legible to future domains:

- graph and backlinks,
- study scopes,
- resolved navigation tree,
- generated local and master indexes,
- official cards/quizzes/prompts,
- task lists,
- citation/source map,
- numbered object map,
- quanta tree,
- asset map.
- reviewed output map.

Generated data is not canonical course truth. It can always be rebuilt from source.

Navigation and generated index data should expose clean URLs, hierarchy labels, breadcrumbs, previous/next relationships, child entries, summaries, appendices/anexos, and official study-object counts. Dynamic services read these data products through `manifest.json`; they do not scrape rendered HTML as authority.

Numbered object data is manifest-declared as `data/numbered-objects.json`.
It records object IDs, families, labels, numbers, optional titles, source
paths, page output paths, rendered anchors, deployment-neutral hrefs, and
reference text. Rendered pages use this data to show static labels and links,
while agents and future services use the JSON index instead of scraping HTML.

Official task data is manifest-declared as `data/tasks.json`. It is generated
from accepted official objects whose type is `assignment`, `exam`, `project`,
or `task`, and records public planning fields such as title, preview, type,
owning page, rendered anchor, deployment-neutral hrefs, graph focus link, due
date, availability, points, weight, status, and tags when those fields are
authored under the object `content`. It is not source authority, learner state,
submission state, grading state, personal progress, recommendation data, or a
calendar integration feed.

The static renderer may also publish a browser-facing Schedule workspace over
the same `data/tasks.json` payload. That page is a dated view of accepted
official task metadata only; it is not a separate machine authority surface,
calendar feed, reminder system, synchronization contract, or learner-state
record.

## Study Seed Data

Artifacts should expose official learning objects as seed data for future study systems. Static artifacts may include cards, quizzes, prompts, tasks, and quanta scopes, but they should not contain private review history or personal mastery state.

```text
course/_official/
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

## Reviewed Output Data

Artifacts may expose reviewed execution output that was frozen into source support before build. Reviewed output data is useful to static pages, agents, launchers, and future execution tools, but the source `_reviewed/` manifest and files remain the authority.

```text
course/_reviewed/execution/<target>/
          |
          v
artifact/data/reviewed-outputs.json
artifact/reviewed/<target>/
artifact/site/_raya/reviewed/<target>/
```

The builder must not execute code to produce reviewed output. It validates current reviewed metadata and copied files, then renders compact panels or links from manifest-declared data. Stale or missing reviewed output should fail before a static artifact presents it as current.

## Builder Boundary

The first static builder should be fresh code. Legacy implementations may be mined for ideas, but no renderer dependency is part of the framework contract.
