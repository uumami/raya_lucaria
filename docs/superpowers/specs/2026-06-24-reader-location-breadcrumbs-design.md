---
id: superpowers-reader-location-breadcrumbs-design
title: Reader Location Breadcrumbs Design
summary: Polish reader breadcrumbs into a compact static location strip using current navigation authority.
status: ready
---
# Reader Location Breadcrumbs Design

## Problem

Current rendered pages can include breadcrumbs, but the output is minimal: ancestor links joined by plain slashes. It does not show a stable course-home entry, does not show the current page as the terminal crumb, and has no dedicated hooks for responsive truncation or visual polish. The legacy main branch had a clearer location strip with a home entry, separators, truncation, and current-page treatment.

Students need a fast answer to “where am I?” without relying only on the course map or top command bar. Agents also need a stable, testable surface for location semantics.

## Selected Approach

Adapt the legacy breadcrumb pattern as a **static reader location strip**:

- show a course-home crumb first;
- show ancestor page crumbs as deployment-neutral links;
- show the current page as the final non-link crumb with `aria-current="page"`;
- use explicit classes and separators instead of plain slash text;
- keep labels from current generated navigation data, not source paths;
- make the strip horizontally resilient through wrapping and truncation;
- preserve normal article flow and avoid layout shifts.

This is current static renderer behavior only. It does not add browser state, fetches, storage, inferred recommendations, or dynamic routing.

## Alternatives Considered

1. **Leave breadcrumbs as plain links**: smallest change, but it misses the legacy UX improvement and gives weak visual hierarchy.
2. **Static location strip on article pages**: selected. It uses existing page/order data, improves orientation, and stays easy to test.
3. **Interactive breadcrumb drawer or path picker**: deferred. It would duplicate the course map and add unnecessary UI state.

## Behavior

For a nested page, breadcrumbs render as:

```text
Course home > Parent > Current page
```

The home and ancestor crumbs are links. The current page is text with `aria-current="page"`. Separators are decorative and hidden from assistive technology. Long labels truncate within their crumb rather than forcing horizontal overflow.

Root pages may omit the breadcrumb strip or render only when at least one meaningful location transition exists. The selected baseline keeps root pages free of a one-item breadcrumb.

## Static Boundary

Breadcrumbs are generated at build time from `ContentModel` page relationships and current page output paths. They must not scrape rendered HTML, read source paths into visible text, fetch runtime data, store state, or infer learning progress.

## Documentation Impact

The existing student role docs already state that rendered courses should show breadcrumbs. Update the learning renderer contract and agent guidance to make the current breadcrumb behavior explicit: clean home/ancestor/current location, deployment-neutral links, current-page semantics, and no progress meaning.

## Test Strategy

Use TDD.

- Contract tests assert nested pages render `nav.raya-breadcrumbs`, a home link, ancestor links, separators, and a current-page crumb with `aria-current="page"`.
- Browser tests assert breadcrumbs are visible on nested fixture pages, navigate locally through ancestor crumbs, use no external requests, and do not overflow on desktop or mobile.
- Existing static-read-path and render-debug gates cover broader no-overflow and deployment parity.

## Self-Review

- No schema changes are required.
- The design is scoped to article page breadcrumbs and does not duplicate course-map behavior.
- Requirements are testable through generated HTML and browser static-read-path checks.
