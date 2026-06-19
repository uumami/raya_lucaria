# Collapsible Learning Rail Design

The old `main` branch made the right table-of-contents sidebar collapsible into a thin tab. That behavior is useful for learning because readers can keep orientation available while reclaiming horizontal space for dense mathematical or technical content. The reset renderer already has a right learning rail with page summary, status, tags, prerequisites, linked pages, page contents, sequence, and support panels; this slice adapts the old idea to that richer reset-native rail.

## Goals

- Add an explicit click-only control that collapses the whole right learning rail on desktop.
- Keep the article primary and wider when the rail is collapsed.
- Leave the rail expanded by default on browser load.
- Keep collapsed behavior non-persistent, matching the current course-map state principle.
- Keep mobile article-first behavior; mobile should not gain a narrow right-side tab.
- Preserve existing panel-level collapses inside the rail.
- Avoid external assets, browser fetches, hover-only behavior, personal progress, recommendations, or dynamic study state.

## Behavior

The rendered learning rail gets a small header with title text and a `Hide context` button. When clicked, the shell sets `data-raya-learning-rail="collapsed"` on the root shell and rail. The expanded rail body becomes `aria-hidden="true"` and `inert`; focusable descendants are removed from the tab order. A compact `Context` button remains visible on desktop and expands the rail again.

The compact tab is a real button, not decorative text. It uses `aria-controls="raya-learning-rail-body"` and `aria-expanded="false"` while the rail is collapsed. Escape may collapse the rail when focus is inside the expanded rail, mirroring the course-map escape behavior.

## Rendering

`packages/static/src/raya_static/builder.py` wraps existing rail panels in:

- `aside.raya-learning-rail`
- `div.raya-learning-rail-header`
- `div#raya-learning-rail-body.raya-learning-rail-body`
- `button.raya-learning-rail-collapse`
- `button.raya-learning-rail-expand`

The existing `_render_rail_panel(...)` functions remain unchanged except for being nested inside the rail body.

## Styling

`packages/static/src/raya_static/rendering.py` adds desktop-only collapsed rail CSS. In expanded mode the rail keeps its current width. In collapsed mode the grid column narrows to a compact tab, the article column grows, and the rail body/header hide without exposing wrapped vertical text.

On small screens, the rail remains a normal full-width region below the article and the rail-level collapse controls are hidden. Panel-level collapses still work.

## Shell Script

`packages/static/src/raya_static/shell.py` adds a rail-level state controller. It reuses the existing focusable-descendant helper used by panel bodies. The state is initialized to expanded on every load and is not stored in `localStorage`.

## Contract

`docs/foundation/20_learning_renderer_contract.md` should describe the right learning rail as expanded by default and collapsible through an explicit click control. It should preserve the existing statement that the rail only shows current artifact data and explicit graph context, not inferred goals or progress.

## Tests

Contract tests should assert the new rail markup and CSS hooks. Browser tests should verify:

- the rail starts expanded on desktop;
- clicking `Hide context` collapses the rail to a compact button;
- the article becomes wider;
- collapsed rail body is inert and hidden;
- clicking `Context` expands the rail again;
- there is no horizontal overflow on desktop or mobile;
- mobile does not show the compact desktop tab.
