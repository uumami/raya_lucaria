---
id: wide-desktop-command-labels
title: Wide Desktop Command Labels
status: ready
date: 2026-06-27
workflow: superpowers
---

# Wide Desktop Command Labels

## Problem

The reader command bar exposes important navigation and comfort controls, but at desktop widths the current CSS keeps every command label visually clipped. This preserves density, but on wide desktop viewports it makes controls such as `Text size`, `OpenDyslexic`, and `Skin` harder to discover even though there is enough horizontal space.

## Design

Keep the compact icon-first command bar for mobile, tablet, and normal desktop widths. This does not undo the earlier reader-comfort-labels decision: `Text size` and `OpenDyslexic` remain visibly named at normal desktop widths, while navigation, layout, and skin labels stay compact until wide desktop. At wide desktop viewports, reveal command labels inside the existing command buttons:

- show labels only when the viewport is wide enough for a single-row toolbar;
- keep the existing icons, groups, search form, links, buttons, and JavaScript behavior;
- keep comfort controls as local display preferences only;
- do not add browser storage, external resources, new state, or new authoring data.

This slice changes only presentation. It does not alter graph/search/practice/task/schedule URLs, course-map state, reader-focus state, skin authority, OpenDyslexic behavior, or text-size persistence.

## Testing

Add browser e2e coverage against the render fixture:

- at `1800px` and wider, visible command labels are not clipped and the toolbar remains one row without horizontal overflow;
- at `1440px`, navigation, layout, and skin command labels remain compact so normal desktop density does not regress, while the accepted comfort labels remain visible;
- navigation, layout, and comfort command labels are discoverable on wide desktop.

Run the focused command-bar and shell tests, then the render-debug gate.
