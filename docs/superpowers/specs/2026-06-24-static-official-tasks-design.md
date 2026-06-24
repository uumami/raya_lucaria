# Static Official Tasks Workspace Design

## Context

Raya already accepts official learning objects with types `assignment`, `exam`, `project`, and `task`. These objects render on their owning pages and are exported in `data/official.json`, but students do not yet get a focused planning surface for work-bearing objects.

The legacy site had task aggregation and calendar views, but those implementations depended on legacy preprocessing and page layouts. The current reset needs the same learning value rebuilt as static artifact output: no backend, no personal state, no recommendations, no runtime fetches, and no source path exposure.

## Decision

Add a generated static Official Tasks workspace:

- `artifact/data/tasks.json` records public planning metadata for official objects whose type is `assignment`, `exam`, `project`, or `task`.
- `artifact/manifest.json` declares that index as `data.tasks`.
- `artifact/site/_raya/tasks/index.html` renders a student-facing task workspace with local filtering, sorting, status/context text, owning page links, and graph focus links.
- `artifact/site/_raya/render/tasks.js` handles only local DOM filtering/sorting from an embedded JSON payload. It must not fetch, persist, score, submit, or infer progress.

## Public Metadata

Task records may include:

- stable object ID
- type and human label
- authority
- page ID and page title
- owning page URL and object anchor
- graph focus URL
- title or preview
- optional `due`, `available`, `points`, `weight`, `status`, and `tags` when authored directly on the accepted official object or under `content`

The renderer must not include source paths, `_official/` paths, private support paths, cache keys, source hashes, answers, solutions, quiz correctness, review state, learner progress, or date-based progress claims.

## UX Principles

The page is a planning and orientation surface:

- students scan course work by type, page, due date, and label;
- desktop uses a three-panel discovery layout consistent with Search/Graph/Practice;
- mobile keeps the controls and cards stacked without horizontal overflow;
- keyboard movement can choose a visible task and Enter opens the owning page;
- no wording implies personalization, completion, grading, mastery, or next-step recommendations.

## Documentation Impact

Update the learning renderer foundation contract, artifact contract, and English/Spanish role docs. The docs must explain that tasks remain authored `_official/` source objects, while the generated task workspace and task index are artifact conveniences.

## Test Strategy

- Contract tests verify `data/tasks.json`, manifest declaration, task workspace HTML, local script, safe payload keys, links, and privacy constraints.
- Browser tests verify static preview serves the workspace, filtering/sorting works, keyboard navigation opens the owning page, desktop panels are arranged correctly, mobile has no horizontal overflow, and no external/fetch/storage behavior appears.
- Existing practice, graph, search, render-debug, host, and Docker gates remain valid.
