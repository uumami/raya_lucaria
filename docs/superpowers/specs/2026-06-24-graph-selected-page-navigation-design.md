# Graph Selected Page Navigation Design

## Context

The old `main` graph made navigation highly obvious: graph nodes were direct
page links and the help text said clicking a node opens that page. The current
static graph intentionally changed single click to select/inspect so students
can read neighborhood, official-object counts, sequence links, and workspace
handoffs before leaving the graph. That current behavior is better aligned with
the new framework, but the page-opening path is weaker because it relies on a
small `Open page` link in the inspector or a hidden double-click behavior.

This slice adapts the old graph's direct navigation clarity without restoring
old unsafe assumptions. The graph remains static, local, embedded, and free of
browser storage, fetch calls, external graph libraries, CDN requests, learner
state, progress, ranking, recommendation, or mastery semantics.

## Goals

- Make the selected page's open action visually obvious in the graph detail
  panel.
- Preserve single-click graph node selection and inspection.
- Preserve double-click graph node navigation as an existing pointer shortcut.
- Add explicit keyboard parity for opening the selected graph page without
  relying on pointer double-click.
- Keep URL, search, filters, selected-page details, graph data, and layout state
  unchanged until the reader deliberately opens a page.
- Document the behavior in the foundation and agent guides.

## Non-Goals

- No single-click graph-node navigation.
- No Cytoscape, force animation, CDN script, browser fetch, or external graph
  renderer.
- No stored graph state, learner state, progress, ranking, recommendations, or
  mastery language.
- No route changes, schema changes, or graph data format changes.
- No new dynamic shortcut preference.

## Options Considered

### Option A: Restore old single-click navigation

This most closely matches old `main`, but it conflicts with the current graph's
inspection-first workflow. Students would lose an easy way to select a page,
read relationships, inspect official objects, or use workspace handoffs before
leaving.

### Option B: Keep current behavior and only improve help text

This is low risk, but it leaves the main discoverability problem unresolved.
The open action remains easy to miss and keyboard users still lack a direct
selected-page open shortcut outside the search box.

### Option C: Add an explicit selected-page action strip

This is the selected design. The detail panel will promote the page-opening
action to a primary `Open selected page` link, keep the existing Search,
Practice, Tasks, Schedule, sequence, and neighborhood actions, and add keyboard
support so Enter on a focused graph node opens its page with normal link
semantics. The action is visible, static, accessible, and does not change graph
data or state until navigation occurs.

## Design

### Graph Detail Actions

The selected-page detail panel keeps one action region. The first action becomes
the primary page-opening action with the label `Open selected page`. It receives
a distinct class for styling and testing but remains a normal static anchor with
a local generated `href`.

The secondary action links remain explicit handoffs: `Find in search`, `Open
practice`, `Open tasks`, and `Open schedule` when available. `Focus
neighborhood` remains a button because it changes transient graph visibility
without navigating.

### Graph Node Keyboard Behavior

Focused SVG graph nodes are real anchors. Pointer click remains intercepted for
selection and inspection, and pointer double-click remains an open-page shortcut.
Keyboard activation should preserve native link expectations:

- Enter on a focused graph node opens its generated page URL.
- Focus still inspects the graph node before activation.
- The graph search input keeps its existing Enter-to-open active result
  behavior.

This adapts old-main immediacy while preserving the current pointer inspection
model.

### Help And Documentation

Graph help text names the pointer and keyboard behavior:

- click selects a page for inspection;
- double-click opens a graph node page;
- keyboard focus plus Enter opens the focused graph node page;
- the selected-page detail card exposes `Open selected page`.

Foundation and agent guide docs should describe this as transient static
navigation, not recommendation or progress behavior.

### Testing

Contract tests should assert the primary action markup, label, help text, and
script symbols. Browser tests should cover:

- selected detail shows `Open selected page`;
- clicking the primary action navigates to the selected page URL;
- pointer click on an SVG graph node still selects and does not navigate;
- focused SVG graph node plus Enter navigates to the node URL;
- graph search Enter behavior remains unchanged;
- double-click graph navigation remains unchanged;
- no fetch, storage, external renderer, or CDN requests are introduced.

## Self-Review

- No placeholders remain.
- The design is scoped to graph navigation affordance, not a broad graph rewrite.
- The design preserves the current static graph model and adapts only the old
  main branch's navigation clarity.
- The keyboard rule is explicit enough to test and does not conflict with graph
  canvas Arrow-key panning.
