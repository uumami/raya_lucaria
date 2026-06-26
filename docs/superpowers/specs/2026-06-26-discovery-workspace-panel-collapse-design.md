# Discovery Workspace Panel Collapse Design

## Goal

Bring Search, Practice, Tasks, and Schedule closer to Graph's workspace comfort
by letting desktop readers collapse the left controls panel and right context
panel through explicit buttons. The collapse state is volatile display state
only.

## Authority

This design follows `docs/foundation/20_learning_renderer_contract.md` and
`docs/superpowers/legacy-ux-convergence-audit.md`. Generated discovery
workspaces may expose local volatile controls and control/results/context
regions. They must not load the course shell script, store workspace state,
fetch runtime data, contact external resources, or use progress,
recommendation, ranking, grading, or personalization language.

## Approach

Use the same interaction shape as the current Graph page:

- each side panel has a visible header with a button;
- clicking the button collapses that panel into a narrow operable rail;
- the button updates `aria-expanded`;
- the collapsible panel body updates `aria-hidden`;
- the page root receives data attributes that CSS uses for desktop grid
  changes;
- no state is stored in `localStorage`, `sessionStorage`, the URL, cookies, or
  generated data.

The behavior is shared by one local `discovery.js` resource, not duplicated in
the four workspace scripts. `search.js`, `practice.js`, `tasks.js`, and
`schedule.js` keep their existing filtering, page-focus, active-card, and reset
logic. The shared script only handles elements marked with
`data-raya-discovery-toggle-panel`.

## Markup

Each Search, Practice, Tasks, and Schedule page will add:

- root data attributes:
  - `data-raya-discovery-controls-state="expanded"`
  - `data-raya-discovery-context-state="expanded"`
- a control panel header with `data-raya-discovery-toggle-panel="controls"`;
- a context panel header with `data-raya-discovery-toggle-panel="context"`;
- body wrappers:
  - `data-raya-discovery-panel-body="controls"`
  - `data-raya-discovery-panel-body="context"`

The button text uses structural language: `Collapse controls`,
`Expand controls`, `Collapse context`, and `Expand context`.

## Responsive Behavior

Desktop layouts may narrow collapsed side panels and give the results column
more room. At tablet/mobile widths, the side panels stay visually expanded so
readers do not lose controls or context in a single-column page. The shared
script may keep `aria-expanded` current, but CSS must not hide panel bodies on
small screens.

## Constraints

- No persistence, URL state, runtime fetch, external resources, shell script
  dependency, service worker, or new payload fields.
- Existing IDs, data attributes, page-focus behavior, filters, Clear/Escape
  reset, and active context behavior must remain intact.
- Collapsed panel bodies must be hidden from keyboard and assistive navigation
  on desktop, while remaining visible in print and narrow layouts.
- Print output continues hiding discovery controls and context panels.

## Testing

Use TDD before production changes. Contract tests should assert all four
workspaces include the shared `discovery.js` resource, panel toggle buttons,
state attributes, body wrappers, and preserved script hooks. Browser e2e should
exercise at least one representative workspace collapse/expand flow and verify
no horizontal overflow and no storage writes. The full branch gate remains
`./scripts/check.sh`.
