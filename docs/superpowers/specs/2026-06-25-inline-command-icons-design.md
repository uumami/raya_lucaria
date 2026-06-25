# Inline Command Icons Design

## Context

The render fixture command bars currently use CSS `::before` text badges for Search, Graph, Practice, Tasks, Schedule, Course map, Text size, and OpenDyslexic. That improved recognition over single-letter badges, but the icon system is still implicit CSS content. It is harder to inspect, harder to test as real markup, and less suitable for a modern course shell.

## Decision

Render command icons as local inline SVG inside each command link or button. The renderer owns these icons at build time. The browser receives static HTML, CSS, and existing local scripts only.

Each command keeps:

- the existing command class, such as `raya-command-search`
- the existing link or button behavior
- the visible `.raya-command-label`
- the existing `aria-label` and pressed/expanded state attributes

Each command gains:

- one `.raya-command-icon` SVG before the label
- `aria-hidden="true"` and `focusable="false"` on the SVG
- a stable `data-raya-command-icon="<name>"` marker for tests and future debugging

## Scope

This slice updates reader and discovery command bars only. It does not change course map behavior, graph behavior, search behavior, practice/tasks/schedule content, skin configuration, or JavaScript storage policy.

## Visual Direction

Icons use simple stroke geometry with `currentColor`, so skins can control the final appearance through normal course CSS variables. Text-size and OpenDyslexic controls use compact inline SVG text marks (`A+` and `Aa`) because their meaning is specifically typographic.

## Testing

Tests should fail until the renderer emits inline SVG icons. Assertions should inspect real DOM nodes instead of pseudo-element text content:

- each command in reader and discovery bars has exactly one `.raya-command-icon`
- icons are `svg` elements with `aria-hidden="true"`, `focusable="false"`, `viewBox`, and the expected `data-raya-command-icon`
- command labels remain present
- CSS contains `.raya-command-icon` styling and no longer depends on command-specific `::before` glyph content

## Non-Goals

- No icon CDN, package, browser-side icon hydration, or external renderer request.
- No import from the legacy Eleventy/Tailwind stack.
- No new generated artifact truth beyond the existing static site files.
