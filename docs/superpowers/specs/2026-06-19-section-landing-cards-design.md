# Section Landing Cards Design

## Context

The legacy `main` branch rendered child pages on section landing pages as
`Contenido` cards. That pattern is useful because unit pages become a readable
map of what comes next instead of a plain list. The old implementation depended
on Eleventy/Tailwind and legacy hierarchy data, so only the affordance should be
adapted.

The reset renderer already inserts a generated index into pages with children.
This slice upgrades that existing generated index instead of adding another
navigation surface.

## Goal

Render generated child-page indexes as static learning cards derived from the
current content hierarchy. Cards should help readers scan child pages, summaries,
estimated time, and authored study-object counts without implying progress,
recommendations, mastery, or personal state.

## Behavior

For any page with child pages:

- keep one generated index section in the article;
- label the section `Course Index` for the root page and `Topics` for nested
  section pages;
- render child pages as card-like links with stable class names;
- include the child display label/title, summary when present, estimated time
  when present, and aggregate authored study-object counts when present;
- use normal static links rewritten relative to the current page;
- expose semantic list markup so the card grid remains accessible.

If a page has no children but has aggregate authored study-object counts, keep
the compact `Study` summary behavior.

## Constraints

- No browser fetch, XHR, framework, CDN, external icon, or runtime renderer.
- No localStorage or persistent state.
- No wording such as recommendation, progress, mastery, completion, adaptive, or
  next best action.
- Do not duplicate the course map, graph page, or right rail.
- Generated index data remains derived from current course source and artifact
  builder data.

## Files

- `packages/static/src/raya_static/builder.py`: enrich generated index markup.
- `packages/static/src/raya_static/rendering.py`: style the generated index as a
  responsive card grid using existing skin tokens.
- `tests/contracts/test_static_builder.py`: assert card markup and banned
  wording/dependencies.
- `tests/e2e/test_preview_static_read_path.py`: assert cards render on desktop
  and mobile without overflow and links navigate normally.
- `docs/foundation/20_learning_renderer_contract.md`: document generated child
  indexes as current static course structure.
- English and Spanish role docs: explain the index cards as structure, not
  progress or recommendations.

## Testing

Use TDD:

- contract test fails first on missing card classes/metadata;
- browser test fails first on missing card layout/link behavior;
- implementation then makes both pass;
- run render-debug and the full host gate before committing.
