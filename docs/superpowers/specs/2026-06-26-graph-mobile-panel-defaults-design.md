# Graph Mobile Panel Defaults Design

## Goal

Keep the mobile graph map usable after the canvas by defaulting the stacked list and inspector panels to compact summaries, while preserving full access to both panels.

## Context

The current graph page already has panel collapse behavior for the list and inspector. On `390x844`, the map is now visible early, but the post-map content still starts with:

- List panel around `1469px`
- Inspector panel around `3527px`

That makes the mobile graph feel like a long wall after the map. The old `main` branch used collapsible navigation and side panels to preserve space. The current reset renderer should reuse its own URL-backed panel state and static graph script, not import the old Eleventy sidebar implementation.

## Design

Use the existing graph panel state machinery:

- Desktop default remains list expanded and inspector expanded.
- Stacked graph layouts default list and inspector collapsed.
- Explicit URL params override the responsive default:
  - `list=0` means collapsed.
  - `list=1` means expanded.
  - `inspector=0` means collapsed.
  - `inspector=1` means expanded.
- URL state records only deviations from the responsive default, so a normal mobile open does not rewrite the URL with `list=0&inspector=0`.
- Reset graph returns panels to the responsive default.
- Opening orientation details still expands the inspector when needed.
- Existing focus management remains: hidden panel bodies are `aria-hidden="true"` and their focusable children are removed from tab order.

No graph payload, storage, backend, dependency, external request, or renderer contract changes.

## Acceptance Criteria

- At `390x844`, graph page starts with list and inspector collapsed.
- At `390x844`, list and inspector panel bodies are hidden and their links/buttons are not tabbable.
- At `390x844`, both collapsed panel summaries remain visible and useful.
- At `390x844`, clicking each panel toggle expands the panel and restores focusability.
- At `390x844`, `?list=1&inspector=1` starts both panels expanded.
- At desktop width, graph page still starts with both panels expanded.
- Reset graph restores responsive defaults.
- Exiting graph focus mode through either the focus button or a panel toggle restores responsive defaults.
- URL state only records panel state when it differs from the responsive default.
- Existing graph mobile toolbar, first-viewport, deep-link, and render-debug gates remain green.
