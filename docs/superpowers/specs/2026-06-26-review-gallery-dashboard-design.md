# Review Gallery Dashboard Design

## Context

The renderer now has a rich reader shell, discovery workspaces, graph workspace, skins, OpenDyslexic/text-size controls, render-debug screenshots, and many browser tests. The existing `examples/gallery/index.html` is useful but shallow: it links only to fixture entrypoints and inspection pages. Agents and humans still need to remember the exact URLs for graph focus, reader UX, math authoring, numbered objects, practice, tasks, schedule, and search handoffs.

## Decision

Turn the examples gallery into a static review dashboard. It remains fixture material and does not become a course authority surface. The dashboard adds:

- a compact review checklist for what to inspect;
- direct deep links into the render fixture reader states;
- direct deep links into generated discovery workspaces;
- static command notes for rebuilding fixtures and running render-debug;
- responsive cards that fit on mobile and desktop without overlap.

The gallery stays hand-authored HTML. It does not commit generated screenshots, generated artifact files, JavaScript, fetches, iframes, or external assets. All links remain deployment-neutral relative links into already built fixture artifact sites.

## UX Shape

Use three sections:

- Fixture previews: keep the existing fixture cards with entrypoint and inspection links.
- Review states: add cards for Reader shell, Graph/Search, Practice/Tasks/Schedule, and Render debug.
- Local commands: show the exact local commands used to rebuild and inspect fixture output.

Cards are compact and scannable. Each card uses short link labels and short descriptions so the gallery is useful as a launchpad, not a documentation page.

## Tests

Update gallery tests to prove:

- fixture-authority labeling remains present;
- existing fixture entrypoint and inspection links remain;
- deep links exist for render fixture reader pages and generated workspaces;
- render-debug/check commands are visible;
- the gallery stays static, with no `<script>`, `<iframe>`, external URLs, or generated screenshot references;
- responsive card layout still avoids overlap in browser tests.

## Self-Review

No placeholders remain. The scope is gallery UX only. This supports visual debugging and manual review without changing renderer contracts or adding generated artifacts to source control.
