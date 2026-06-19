# Keyboard Page Navigation Design

The old `main` branch included a small keyboard navigation helper that moved to the previous or next page with arrow keys or `Alt+k` / `Alt+j`. The reset renderer already generates explicit previous and next links from current navigation data, so this slice adapts that behavior without adding legacy dependencies, persistence, or a new navigation authority.

## Goals

- Let readers move through the ordered course with keyboard shortcuts.
- Use the existing generated previous/next sequence links as the only navigation targets.
- Keep the behavior static and local in `shell.js`.
- Avoid browser storage, external resources, global command palettes, or inferred progress.
- Do not trigger navigation while the user is typing in inputs, textareas, selects, or editable content.

## Behavior

Rendered sequence links receive `data-raya-prev-page` and `data-raya-next-page` attributes alongside their existing `rel="prev"` and `rel="next"` attributes. The shell script listens for `keydown` on normal course pages:

- `ArrowLeft` navigates to the first previous-page link.
- `ArrowRight` navigates to the first next-page link.
- `Alt+k` also navigates to previous.
- `Alt+j` also navigates to next.

The handler ignores events when `Ctrl`, `Meta`, or `Shift` is pressed, except that `Alt+k` and `Alt+j` are accepted. Plain `Alt+ArrowLeft` and `Alt+ArrowRight` are not Raya shortcuts, so browser history shortcuts remain available. It also ignores events from form controls and editable regions. This preserves expected typing and browser/system shortcuts.

## Rendering

`packages/static/src/raya_static/builder.py` remains the source of page order. `_sequence_links(...)` adds:

- `data-raya-prev-page` to previous links
- `data-raya-next-page` to next links

Both the article-top sequence nav and right-rail sequence panel reuse `_sequence_links(...)`, so they expose the same stable selectors. The shell chooses the first matching link, which is the article-top link in normal pages.

## Shell Script

`packages/static/src/raya_static/shell.py` adds one small keyboard helper:

- detect whether the event target is editable;
- find the appropriate previous or next link;
- prevent default only when a navigation target exists;
- assign `window.location.href` from the link href.

No state is stored and no network fetch is introduced.

## Contract

The learning renderer contract should mention keyboard-reachable reader controls and previous/next keyboard navigation as static reader controls. It must not describe this as progress, completion, or adaptive study state.

## Tests

Contract tests should assert the data attributes exist on generated previous/next links and that `shell.js` contains the shortcut handler without `localStorage`, `fetch`, or `XMLHttpRequest`.

Browser tests should verify:

- `ArrowRight` moves from the render fixture root to the next page;
- `ArrowLeft` moves back to the previous page;
- typing in an input does not trigger navigation;
- `Alt+j` and `Alt+k` work on normal reader pages;
- `Alt+ArrowRight` is not canceled and does not trigger Raya next-page navigation.
