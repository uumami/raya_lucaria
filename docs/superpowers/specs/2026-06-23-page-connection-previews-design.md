---
id: superpowers-page-connection-previews-design
title: Page Connection Previews Design
summary: Static, keyboard-reachable previews for explicit page relationships in the reading shell.
status: draft
---
# Page Connection Previews Design

## Goal

Make explicit page relationships easier to understand from the normal reading page without forcing students to leave the article for the full graph workspace.

## Reader Problem

The current rail and article connection blocks show counts, page links, and graph-focus links. That is structurally correct, but it does not show public context for the linked page. Legacy graph affordances had hover inspection and neighborhood hints; the reset renderer should adapt the useful part as static page-local context, not as a dynamic graph dependency.

## Current Source Of Truth

Only accepted artifact data may drive the preview:

- current page and linked page stable IDs;
- public page title or nav title;
- public page summary and status when authored in frontmatter;
- explicit incoming and outgoing content-link counts derived from generated graph edges;
- generated local page URL and generated local graph-focus URL.

The preview must not scrape rendered prose, expose source paths, infer relationship quality, or produce learning recommendations.

## Behavior

For each explicit incoming or outgoing connection shown in the right rail and article-end `Page connections` block, render a compact native disclosure with:

- the linked page title as the summary text;
- an `Open page` link to the rendered local page;
- a `Graph` link to the generated graph page focused on the linked page;
- optional `summary` text from page metadata;
- optional `status` text from page metadata;
- structural counts such as `2 from this page` and `1 link here`.

The article block may use a roomier card layout. The rail must remain compact and collapsed inside the existing `Connections` rail panel until the reader opens it.

## Non-Goals

- no scoring, attempts, mastery, progress, ranking, or recommendation wording;
- no browser-side graph payload fetch;
- no external graph or tooltip library;
- no localStorage/sessionStorage for graph, connection, or disclosure state;
- no source paths, private support paths, `_official/` paths, or artifact internals in normal page HTML;
- no course-level related-practice index.

## Verification

Add contract coverage for generated preview markup, escaped public metadata, local links, structural counts, and forbidden strings. Add browser coverage for native disclosure interaction, graph handoff, desktop/mobile no-overflow, and absence of external requests after load.

Update the learning renderer foundation contract and English/Spanish student and agent guides so the reader workflow and verification boundary stay synchronized.
