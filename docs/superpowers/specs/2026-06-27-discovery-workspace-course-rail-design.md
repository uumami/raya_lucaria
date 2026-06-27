---
id: superpowers-discovery-workspace-course-rail-design
title: Discovery Workspace Course Rail Design
status: ready
created: 2026-06-27
---

# Discovery Workspace Course Rail Design

## Context

The legacy `main` branch gave course tools a persistent left navigation frame:
course identity, task/workspace links, graph entry, collapsible content
navigation, and comfort controls. The reset renderer already has stronger
static contracts, local assets, generated graph/search/practice/task/schedule
workspaces, and an article course map, but generated discovery pages still feel
like isolated tools. They have cross-workspace command links and local
controls, yet they do not expose a shared course-orientation rail.

This loop adapts the useful legacy pattern without copying its stack. There
will be no Eleventy/Tailwind/Pagefind/Cytoscape dependency, no CDN resources,
no runtime fetch, and no persistent graph/search/workspace state.

## Design

Generated Search, Graph, Practice, Tasks, and Schedule pages should include a
shared static course workspace rail on desktop. The rail sits to the left of
the existing workspace body and gives students one stable place to answer:

- what course am I in;
- which discovery workspace am I using;
- what other generated workspaces are available;
- where are the nearby course pages;
- how do I return to the course reading path.

The rail is generated from current artifact data only. It reuses the same
public navigation records and workspace availability data already used by the
course map, search index, graph data, and official-object indexes. It must not
infer progress, recommendations, mastery, ranking, related practice, or learner
state.

## Desktop Behavior

On desktop, the generated discovery page layout becomes:

1. a sticky discovery command bar;
2. a compact discovery overview/guide area;
3. a three-zone workspace body: course rail, primary workspace, and existing
   control/context panels.

The course rail should show:

- course title and a `Back to course` link;
- workspace switcher links for Search, Graph, Practice, Tasks, and Schedule,
  with `aria-current="page"` on the active workspace;
- structural badges such as `Course`, explicit graph link counts, accepted
  official-object counts, accepted task counts, and dated task counts when
  already available;
- a compact local course list using page order, page title, hierarchy label,
  current URL page focus when available, and links to public pages;
- page-scoped handoff links where the current focused page supports them.

The rail can collapse through an explicit button into an operable compact rail.
Collapsed state is volatile display state only. It must not write
`localStorage`, `sessionStorage`, cookies, URL state, artifact data, or hidden
source data. While collapsed, non-visible rail body controls are removed from
keyboard and assistive navigation, and a compact `Course` tab remains
keyboard-operable.

## Mobile Behavior

Mobile and tablet discovery workspaces should keep the existing single-column
workspace flow. The course rail becomes an in-flow `Course workspace` section
near the top rather than a separate drawer. This avoids competing with the
reader course-map drawer and keeps the page predictable on small screens.

## Data Flow

The builder should create one shared rail payload or render model from current
public course data:

- course title;
- relative course root URL;
- available workspace URLs and labels;
- active workspace kind;
- optional page focus ID from the generated workspace URL context;
- ordered public page links and hierarchy labels;
- workspace badge counts already available from generated public metadata.

Each workspace builder passes this model into the shared renderer. The rail is
server-rendered into static HTML. The only JavaScript behavior is local
collapse/expand and accessibility bookkeeping.

## Styling

The rail uses existing skin tokens and discovery panel styles. It should not
introduce a second theme system. It should use the current Eva-inspired default
skin through tokens, and it should respect OpenDyslexic and text-size comfort
preferences already exposed by discovery chrome.

Layout rules should prioritize desktop readability:

- primary workspace area gets the largest column;
- rail and context/control panels are bounded and sticky when useful;
- collapsed rails use stable widths to prevent blinking or layout jumps;
- no text should overflow buttons, cards, chips, or rail labels.

## Testing

Tests should prove the feature from generated static output, not implementation
details:

- every discovery workspace renders the course rail and active workspace link;
- rail links are deployment-neutral and do not expose source/private paths;
- desktop collapse hides the rail body from visual, keyboard, and assistive
  navigation while keeping the compact tab operable;
- mobile keeps the rail content in flow and does not create horizontal
  overflow;
- no workspace rail behavior writes browser storage, fetches data, or requests
  external resources;
- render debug still passes for screenshots, overflow, raw TeX, local MathJax,
  and external request checks.

## Non-Goals

This loop does not add personal progress, recommendations, adaptive study,
runtime graph fetching, persistent workspace state, new source contracts,
browser-side MathJax, or a replacement for the reader course map. It adds a
shared static orientation rail to generated discovery pages only.
