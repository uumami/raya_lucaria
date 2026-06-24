# Discovery Workspace Comfort Design

## Context

The generated Search, Graph, Practice, Tasks, and Schedule pages already satisfy the static renderer contract: they are local, generated surfaces with embedded payloads, no backend dependency, no external renderer/CDN requests, and no persistent study state. The reader shell has recently become more comfortable on desktop, but the discovery workspaces still feel like separate tool pages: they repeat the course/back hierarchy below the command bar, use slightly different panel/card treatments, and make the graph feel visually separate from the other discovery surfaces.

Old `main` contains useful workspace ideas, but not reusable architecture. Its Eleventy, Tailwind, Pagefind, Cytoscape/CDN, service worker, and global shell patterns conflict with the current renderer contract. The transferable ideas are limited to local workspace behavior: clear structural navigation, scan-friendly results, graph focus/inspection, card states, and compact cross-workspace commands.

## Goals

- Make Search, Graph, Practice, Tasks, and Schedule feel like one coherent static learning workspace family.
- Use the top discovery command bar as the single course/workspace navigation layer.
- Turn page headers into compact purpose headers that identify the workspace without repeating course title and "Back to course".
- Normalize desktop panel, card, context, and active-state styling across discovery workspaces.
- Keep graph-specific interaction behavior intact while aligning panel chrome, controls, and inspector styling with the other workspaces.
- Improve mobile comfort without making the command bar tall or visually noisy.
- Extend browser/layout tests so workspace regressions are caught across desktop and mobile.

## Non-Goals

- No OpenSpec work in this loop.
- No source-contract or artifact-contract change.
- No personal progress, mastery, recommendation, adaptive practice, scoring, grading, submission, or reminder behavior.
- No browser-side MathJax conversion.
- No runtime fetch/XHR, backend calls, external scripts, external styles, external fonts, or CDN renderer requests.
- No persistence for search, graph, practice, task, or schedule workspace state. Existing comfort preferences for text size and OpenDyslexic remain the only storage-eligible reader controls.
- No port of Eleventy, Tailwind, Pagefind, Cytoscape, or old global shell code from `main`.

## Design

### Shared Discovery Chrome

`_render_discovery_command_bar()` remains the shared navigation layer. It shows the course link, current workspace label, cross-workspace links, text-size control, and OpenDyslexic control. The generated workspace headers stop repeating the course title and `Back to course`; those controls already live in the command bar.

Each page header becomes a compact workspace intro:

- Graph: `Course Graph`, with one structural sentence about generated pages and links.
- Search: `Course Search`, with one structural sentence about page metadata search.
- Practice: `Official Practice`, with one structural sentence about accepted official objects.
- Tasks: `Official Tasks`, with one structural sentence about accepted task-family objects.
- Schedule: `Official Schedule`, with one structural sentence about authored dated task-family objects.

This reduces vertical noise, especially on mobile, while keeping the course navigation and workspace identity visible.

### Shared Workspace Layout

Search, Practice, Tasks, and Schedule use the same three-region desktop layout: controls, results, and context. Existing page-specific classes stay in the markup so scripts and tests remain stable, but CSS groups them into one shared visual system:

- control panels and context panels use the quieter reader-rail background;
- results panels remain the primary scanning surface;
- sticky side panels use the same top offset and spacing;
- panel headings, labels, summaries, and metadata use the same scale;
- context panels use compact title, muted metadata, and stable spacing.

Graph keeps its list/map/inspector grid, but its panels, toolbar, collapsed panel buttons, list items, and inspector surfaces adopt the same panel/card vocabulary.

### Shared Cards And Actions

Result cards across Search, Practice, Tasks, and Schedule share:

- 0.5rem radius;
- surface background and subtle border;
- consistent action button styling;
- clear active state using accent border plus a left inset indicator;
- metadata at a small, muted scale;
- visible keyboard/focus states through existing browser focus plus active card state.

Task and schedule accent colors remain type/date cues. They are structural cues only, not importance, urgency, progress, or recommendation signals.

### Mobile Behavior

At narrow widths, the command bar remains compact and horizontally scrollable for tools. Workspace content stacks in a predictable order: header, controls, results, context. Header copy stays short so students reach content quickly. No workspace should horizontally overflow at representative mobile widths.

### Verification Strategy

Tests should fail before implementation for:

- no duplicate course/back hierarchy inside generated workspace headers;
- desktop Search workspace uses the shared three-column region with command bar as the only course navigation layer;
- Graph/Search/Practice/Tasks/Schedule are included in broad no-overflow checks at desktop and mobile sizes;
- discovery CSS contains shared workspace panel/card classes or grouped selectors rather than only page-specific drift.

Focused checks should continue to assert:

- no `pagefind`, external URLs, `fetch(`, or `XMLHttpRequest` in generated student-facing workspace surfaces;
- command bar links remain deployment-neutral;
- controls, results, and context panels remain visible and operable;
- mobile discovery command bar stays within the existing comfort height bound.

## Risks

- Broad CSS selectors could accidentally affect reader pages. Scope changes to discovery and graph classes.
- Removing duplicate header links could break tests that assumed old text. Update tests to assert the command bar owns course navigation.
- More visual polish could introduce learner-state language by accident. Keep all copy structural and course-data based.
- Graph is interaction-heavy. Avoid JS behavior changes unless a test requires them.

## Acceptance Criteria

- Generated Search, Graph, Practice, Tasks, and Schedule pages no longer show a second course title or `Back to course` link inside the workspace header.
- The command bar remains visible and provides the course link, workspace label, cross-workspace links, text-size control, and OpenDyslexic control.
- Search, Practice, Tasks, and Schedule share consistent controls/results/context panel styling.
- Graph panels visually align with the discovery workspace family without losing collapse, zoom, pan, layout, search, focus, or inspector behavior.
- Desktop and mobile browser checks show no horizontal overflow on reader, inspect, gallery, Search, Graph, Practice, Tasks, and Schedule surfaces.
- Focused render-debug and host checks pass.
