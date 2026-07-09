# Reader Rail Rebuild Design

## Context

The current production reader shell has accumulated several sidebar iterations. The left course rail and right learning rail are visually inconsistent, too heavy in places, and fragile around medium-width layouts. The approved preview is `docs/superpowers/previews/reader-rails-preview.html`.

Legacy `main` is historical UX evidence only. The rebuild may adapt its fixed full-height rail, compact search, colored icon rows, dense tree navigation, and narrow collapsed mode. It must not restore Eleventy, Tailwind, Pagefind, CDN assets, old generated data shapes, or durable sidebar state.

## Goal

Rebuild the generated reader rails as a clean, simple shell:

```text
left course rail | article | right learning rail
```

The article remains primary. The rails provide quiet navigation and support without behaving like dashboard cards.

## Accepted Direction

The left rail is the course command center. It contains, in order:

1. compact course title and collapse control;
2. search bar;
3. dense colored icon command tiles arranged two per row for Search, Graph, Practice, Tasks, Schedule, Text, OpenDyslexic, and Context;
4. scrollable course hierarchy with generated structural numbers, disclosure controls, current-page highlight, and visible nesting.

The right rail is secondary page context. It uses the same calm visual grammar as the left rail but remains narrower and content-derived: page outline, reading flow, metadata, connections, and support panels.

Collapsed desktop and medium-width rails become narrow edge controls that return width to the article. Collapsed controls must be readable, keyboard-safe, and transparent enough to keep the page usable, but not visually noisy. Hidden rail content must be removed from keyboard and assistive navigation.

Phone layouts keep the article first. The course map opens as a modal drawer; right context remains accessible as a below-article section or accepted sheet behavior.

## Non-Goals

- No new source course contract or artifact data shape.
- No new search, graph, practice, task, or schedule behavior.
- No persistent reader shell state beyond currently accepted comfort keys and accepted course-map branch session state.
- No top reader command bar.
- No old-main dependencies, renderer stack, or storage model.

## Implementation Boundary

Prefer deleting or replacing the existing rail-specific HTML/CSS blocks over layering more special cases. Keep stable public selectors where tests and shell behavior depend on them: `#raya-course-map`, `#raya-course-map-list`, `#raya-learning-rail`, `#raya-learning-rail-body`, `data-raya-course-map-toggle`, `data-raya-learning-rail-toggle`, and drawer/backdrop hooks.

The implementation must update tests before production code and verify with Chromium screenshots at representative desktop, medium, and mobile viewports.
