# Mobile Discovery Collapse Design

## Goal

Search, Practice, Tasks, and Schedule should let narrow-screen readers collapse
controls and context panels so results can move up quickly on phones and small
tablets.

## Current Problem

Discovery panels already collapse on desktop. On narrow screens the script
forces controls and context back open, and CSS displays panel bodies even when
their `aria-hidden` state says they are collapsed. That prevents students from
using the existing collapse affordance where vertical space is most constrained.

## Design

Use the existing panel toggle model at every viewport width:

- clicking `Collapse controls` or `Collapse context` toggles the same state
  attributes on desktop and mobile;
- collapsed panel bodies remain hidden with `aria-hidden="true"`;
- focusable controls inside collapsed bodies receive `tabindex="-1"` through
  the existing focus management;
- narrow screens keep normal horizontal heading text and single-column layout;
- no state is persisted and no external request is added.

The desktop rail behavior remains unchanged. Mobile collapse uses the same
header, button labels, and rail summary text, but it does not turn headings
vertical or create side rails.

## Constraints

- No `localStorage`, `sessionStorage`, `fetch`, `XMLHttpRequest`, or CDN usage.
- Keep generated markup and static scripts local to the artifact.
- Do not add progress, mastery, recommendations, grades, scoring, or submission
  language.
- Preserve existing controls/results/context order and existing panel labels.

## Testing

Use browser tests against the render fixture:

1. confirm the current mobile click fails because state remains expanded;
2. implement script and CSS changes;
3. confirm mobile controls hide, focusable elements are removed from tab order,
   rail summaries show, and no storage is written;
4. keep existing desktop context-collapse coverage green while relying on the
   shared panel-state path for context behavior on narrow screens.
