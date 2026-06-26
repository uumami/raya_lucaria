# Pre-Paint Comfort Restore Design

## Context

The legacy `main` branch restored theme and font comfort state before page
paint. The current renderer already supports local OpenDyslexic and text-size
controls with explicit comfort-preference storage on reader pages, but the
restoration lived in a deferred resource. That can leave a first-paint mismatch
for students who rely on those settings.

## Goal

Restore only accepted reader comfort preferences before CSS and deferred shell
scripts run, without adding shell/navigation persistence or changing discovery
workspace no-storage behavior.

## Design

Reader pages emit a tiny inline head script before stylesheet links. It reads
only `raya:open-dyslexic` and `raya:text-size` from `localStorage`, validates
the text-size value against `normal`, `large`, and `x-large`, and sets
`data-raya-open-dyslexic` and `data-raya-text-size` on the root element.

The existing deferred accessibility script remains responsible for button
state synchronization and click handling. Graph, Search, Practice, Tasks, and
Schedule continue to use the volatile accessibility script and must not gain
storage-backed comfort persistence.

## Constraints

- No shell, graph, discovery, course-map, or learning-rail state persistence.
- No external scripts, fonts, renderers, or CDN requests.
- No browser-side MathJax.
- No source, schema, graph, or artifact contract changes.
- Keep the inline script static and independent of course content.

## Verification

- Browser test blocks the deferred accessibility script and verifies stored
  OpenDyslexic/text-size preferences still apply from the head script.
- Existing comfort toggle tests continue to verify button behavior and
  persistence.
- Existing graph/discovery contract tests continue to reject persistent storage
  in volatile workspaces.
