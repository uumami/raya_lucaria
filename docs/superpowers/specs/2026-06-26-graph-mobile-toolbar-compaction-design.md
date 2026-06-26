# Graph Mobile Toolbar Compaction Design

## Goal

The graph toolbar should stay fully available on mobile without consuming most of the first viewport.

## Problem

At narrow widths the graph toolbar wraps each control group vertically. On a 390px viewport the toolbar can be about 280px tall before the learner reaches the graph map. The prior map-priority slice moved the map before the dense list and inspector panels, but the toolbar still delays the canvas.

## Design

- Keep the existing generated graph controls and JavaScript behavior.
- At the mobile command-bar breakpoint, make the graph toolbar a horizontal command strip:
  - keep all groups in DOM order;
  - keep search, layout, filters, fit, pan, reset, and focus controls operable;
  - prevent toolbar groups from wrapping vertically;
  - allow horizontal overflow for secondary controls;
  - keep the toolbar within a compact height;
  - keep keyboard focus rings visible inside the horizontal scroll strip.
- Keep desktop and tablet behavior unchanged.
- Do not add browser storage, URL state, runtime persistence, external graph libraries, or new generated data.

## Testing

Add a browser e2e regression for `_raya/graph/index.html?page=reader-ux` at `390x844`.

The test should assert:

- toolbar height is compact;
- toolbar uses horizontal overflow instead of vertical wrapping;
- primary controls remain visible and operable;
- secondary controls remain reachable in the toolbar DOM;
- focused toolbar controls keep a visible focus outline;
- the map panel still appears before the list panel;
- no local or session storage is used.

## Out of Scope

- Changing graph interaction semantics.
- Replacing controls with a JavaScript drawer.
- Changing desktop toolbar layout.
- Hiding controls from assistive technology.
