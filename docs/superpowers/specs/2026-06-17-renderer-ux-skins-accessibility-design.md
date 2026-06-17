---
title: Renderer UX Skins And Accessibility Design
date: 2026-06-17
status: approved-for-plan
---

# Renderer UX Skins And Accessibility Design

## Goal

Improve the default rendered course experience for desktop reading while keeping
the mobile layout usable. Add more expressive fixture skins, make
`eva-unit-02` the render fixture default, and add a local OpenDyslexic reading
toggle.

This is renderer presentation work only. It must not change source authority,
content order, numbered-object identity, references, math rendering, artifact
data, execution behavior, or preview/deployment parity.

## Current Context

Raya already has a build-time skin system:

- course-local profiles live under `skins/<id>.yaml`;
- a course selects a default through `render.skin` in `raya.yaml`;
- sections may select a skin through `course/**/_raya/skin.yaml`;
- generated pages activate a skin with `data-raya-skin`;
- `_raya/render/skin.css` contains generated CSS variables;
- `rich.css` owns renderer structure and component styling.

The foundation contract forbids arbitrary skin CSS, external fonts, CDN
requests, and browser-side skin resolution. This loop keeps that boundary.

## Requirements

1. The render fixture default skin is `eva-unit-02`.
2. The default skin is inspired by Evangelion Unit 02 but remains easy to read:
   light page/surface tokens, dark text, high contrast, and red/orange accents.
3. Add course-local skins:
   - `eva-unit-02`;
   - `eva-unit-01`;
   - `eva-unit-03`;
   - `ghost-in-the-shell`.
4. Existing section-level examples continue to work.
5. Desktop pages use more horizontal space than the current narrow reading
   column while preserving mobile behavior below the existing narrow breakpoint.
6. Borders and panels look more deliberate: clearer separation, tokenized
   borders, and less phone-first compression on desktop.
7. Add an OpenDyslexic toggle in the top page chrome.
8. The OpenDyslexic toggle uses only local static resources. It must not load
   fonts, scripts, CSS, or renderer logic from a CDN or external origin.
9. The toggle is a reader preference only. It does not change artifact truth or
   generated data.
10. Local preview and copied static deployment use the same files and relative
    links.

## Non-Goals

- No new arbitrary CSS fields in skin YAML.
- No page-level skin overrides in this loop.
- No redesign of the content object system.
- No browser-side MathJax or browser-side numbering/reference resolver.
- No external font provider.
- No hidden dependency on a dynamic backend.

## Approach

### Skin Profiles

Add new YAML profiles in `examples/courses/render-fixture/skins/`. The profiles
use the existing semantic token set: `color`, `font`, and `density`.

The palettes should be expressive but readable:

- `eva-unit-02`: red/orange accent, warm soft accent, light surface, dark text.
- `eva-unit-01`: purple/green accent pairing with light surfaces and dark text.
- `eva-unit-03`: black/white/red signal with a light reading surface and dark
  text.
- `ghost-in-the-shell`: cyan/blue-green accent over a restrained light surface
  for cybernetic signal without a dark neon reading page.

The render fixture course default changes from `warm-academic` to
`eva-unit-02`. Existing `warm-academic` and `practice-lab` profiles remain so
existing section examples and docs do not break.

### Desktop Layout

Update `rich_render_css()` so the desktop layout gives the article more room.
The intended desktop shape is:

- wider constrained page chrome;
- main grid with a wide article column and a narrower support column;
- article and support surfaces that use skin tokens for borders/surfaces;
- stable mobile collapse at the current `720px` breakpoint.

The CSS should use explicit max-width and grid constraints, not viewport-scaled
font sizes.

### OpenDyslexic Toggle

Add local renderer accessibility resources under
`artifact/site/_raya/render/accessibility/` during build:

- a CSS file defining the OpenDyslexic font face and the active document rule;
- a small static JavaScript file that toggles the preference and persists it in
  `localStorage`;
- local font files if available in the repository or dependency cache.

Rendered student pages link these resources with deployment-neutral relative
URLs and include a compact header button. The button should be available on
normal rendered pages. Inspection pages may remain on the default renderer font
unless adding the same toggle is trivial and does not clutter inspection output.

If local OpenDyslexic font files are not already available, the implementation
must not fall back to a remote URL. It should add local font assets to the
repository in a small, explicit renderer asset directory or fail the plan before
claiming the toggle is implemented.

### Documentation

Update role docs in English and Spanish where this changes author/reader
workflow:

- professors: select a course skin with `render.skin`; skins remain readable
  semantic profiles;
- contributors/collaborators: add or review skins through token YAML, not
  arbitrary CSS;
- students: use the OpenDyslexic toggle as a local reading preference;
- agents: verify no external skin/font requests and preserve static parity.

## Testing

Use TDD. Start with failing tests before production edits.

Expected coverage:

- contract tests for the render fixture default skin and generated selectors;
- static-read-path tests for local accessibility CSS/JS links and toggle markup;
- CSS assertions for wider desktop layout constraints and mobile breakpoint
  retention;
- build/validate/artifact inspection for `examples/courses/render-fixture`;
- render-debug or browser-driven checks for no external font/renderer requests
  when practical in the local environment.

## Acceptance Criteria

- `examples/courses/render-fixture/raya.yaml` selects `eva-unit-02`.
- Generated fixture HTML contains `data-raya-skin="eva-unit-02"` on default
  pages and preserves section skin overrides.
- Generated `skin.css` contains selectors for all new skins.
- Desktop CSS uses a wider main layout than the previous narrow default and
  retains the mobile collapse.
- Normal rendered pages expose a top OpenDyslexic toggle.
- Toggle CSS, script, and font assets are local static files under `_raya/`.
- No external renderer, CSS, font, or CDN requests are introduced.
- English and Spanish role docs mention the new skin/accessibility behavior.
- Focused tests, fixture build, and artifact inspection pass before merge or
  push.
