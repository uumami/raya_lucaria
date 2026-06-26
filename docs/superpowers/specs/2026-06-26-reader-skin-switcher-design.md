# Reader Skin Switcher Design

## Context

Old `main` exposed runtime theme cycling in the reader chrome. The reset branch
has stronger course-authored skins: validated `skins/*.yaml`, `render.skin`,
section `_raya/skin.yaml`, generated local `skin.css`, and stable
`data-raya-skin` page attributes. The missing UX capability is reader-facing
visual preview/switching.

## Goal

Add a local reader-facing skin switcher that lets students cycle through the
course's generated skin profiles without changing course truth, graph data,
source content, or section skin selectors.

## Approach

Use an override attribute on the document root:

- body `data-raya-skin` remains the authored course or section skin;
- `html[data-raya-skin-override="<skin-id>"]` applies the same generated CSS
  tokens as that skin;
- the switcher cycles through `authored` plus every generated skin profile;
- the preference is stored locally as `raya:skin-override`;
- a blocking local prepaint script restores the override before `skin.css` loads;
- the interactive script is local, deferred, and does not fetch external data.

This adapts old-main runtime theme switching while keeping the reset framework's
source/artifact distinction. Reader preference may preview a different skin, but
it must not rewrite `data-raya-skin`, `manifest.json`, graph data, numbered
objects, or course source.

## UI

Add a compact `Skin` command to the existing reading comfort command group beside
text size and OpenDyslexic. The command uses an icon, accessible label, visible
desktop label when space allows, and a `data-raya-skin-cycle` list generated from
the course skin context.

The button label reports the active state through `aria-label`:

- `Skin: authored` when no override is active;
- `Skin: Eva Unit 02`, `Skin: Practice Lab`, etc. when overridden.

## Constraints

- No external CSS, CDN, network request, or browser-side renderer dependency.
- No inline script in normal rendered pages.
- Do not persist shell, map, graph, or learner progress state.
- Do not use the reader preference to encode pedagogy, progress, answers, or
  source truth.
- Discovery/graph/search/practice/task/schedule surfaces may reuse the same
  local resources if they include the normal command bar later, but this slice
  targets normal reader pages.

## Test Strategy

- Contract tests prove `skin.css` emits both authored `data-raya-skin` selectors
  and root override selectors.
- Static builder tests prove the switcher command and local skin scripts are
  written without inline `localStorage`.
- Browser tests prove the button cycles to another skin, changes computed color
  tokens, preserves body `data-raya-skin`, persists through reload, and makes no
  external requests.

## Acceptance

- Render fixture normal pages expose a `Skin` command in the comfort group.
- Cycling the command changes `html[data-raya-skin-override]` and visible computed
  colors.
- The authored body `data-raya-skin` is unchanged after cycling.
- Local preview and static deployment use the same generated scripts and CSS.
- Focused e2e, static skin contract tests, and render-debug pass.
