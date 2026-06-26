---
id: reader-comfort-labels-design
title: Reader Comfort Labels Design
status: implemented
---
# Reader Comfort Labels Design

## Context

The current reader command bar has the accepted comfort controls: text size and
OpenDyslexic. They are local reader comfort preferences, not course skin
authority or learning state. The old `main` branch kept font controls visibly
named in reader chrome. Current reader pages hide every command label below
1500px, so at normal desktop widths the comfort controls read primarily as
`A+` and `Aa`.

## Goal

Keep comfort controls understandable in the reader chrome at normal desktop
widths without making the toolbar overflow or adding persistence beyond the
accepted comfort keys.

## Design

Use CSS only:

- keep the existing command markup and JavaScript;
- keep all non-comfort command labels clipped below the current breakpoint;
- restore visible labels only for `.raya-command-group-comfort` at reader
  desktop widths;
- keep mobile command labels clipped so the toolbar remains compact;
- do not change graph/search/practice/tasks/schedule workspace persistence or
  source contracts.

The labels remain the existing authored text: `Text size` and `OpenDyslexic`.

## Testing

Tests should prove that:

- at common reader desktop widths, the two comfort labels are visible and have
  usable dimensions;
- the toolbar does not overflow horizontally;
- mobile still keeps the comfort labels visually clipped;
- no browser storage keys are added by rendering the page;
- the existing click behavior for text size and OpenDyslexic remains intact.

## Risks

The main risk is increasing command-bar height or width. The implementation
should scope the visible labels to desktop reader pages only and keep existing
mobile clipping unchanged.
