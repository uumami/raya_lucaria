---
id: superpowers-collapsed-rail-polish-design
title: Collapsed Rail Polish Design
status: active
created: 2026-06-30
---
# Collapsed Rail Polish Design

## Context

The current course-first shell already renders an expanded desktop course map,
an authored article, and a right learning rail. The current foundation and
renderer contract accept explicit click collapse into compact desktop rails:
the left course map becomes an operable `Map` rail and the right learning rail
becomes an operable `Context` rail. Tablet and mobile must keep the right
learning rail body available and use the course map drawer instead of hiding
normal reading content.

Older Superpowers design notes disagreed about collapsed rail direction and
whether the shell should favor compact labels or icon-only rails. This loop
chooses the current contract direction: collapsed desktop rails use horizontal
tab labels, not vertical text, hover expansion, stored layout state, or hidden
decorative markers.

## Selected Approach

Use a focused polish pass over the existing shell instead of redesigning the
layout. The other approaches considered were:

- Icon-only rails. This would reduce width but make orientation weaker and
  require new icon semantics for page position and context.
- Vertical writing-mode tabs. This would be compact, but it conflicts with the
  current goal's readable-tab preference and the existing browser assertions.
- Horizontal readable tabs. This keeps the current contract, works with the
  existing `Map` and `Context` labels, and can be measured through article
  width gain, focus safety, and mobile parity.

The selected design is the horizontal readable-tab approach.

## UX Contract

Surface: reader shell collapsed rails.

Fixture/page: `examples/courses/render-fixture` at `reader-ux/index.html`.

Measurable assertion: at a desktop viewport, collapsing only the right learning
rail while the course map remains expanded must materially widen the article,
then collapsing the course map too must widen the article again while both
collapsed controls remain horizontal, operable, and accessible. At a mobile
viewport, the same right rail body must remain visible and not become inert
when desktop collapse controls are hidden.

Verification command for the first failing test:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_collapsed_reader_rails_expand_article_width_independently
```

Expected RED result before implementation: the new assertion fails because the
current focused regression does not require rail-only and then combined
collapse to meet a named independent width-gain invariant in one reader flow.

## Behavior

Desktop first paint stays expanded. A reader can then choose:

- collapse `Context` only, preserving the full course map and widening the
  article;
- collapse `Map` only, preserving the learning rail and widening the article;
- collapse both rails through reader focus or explicit controls, giving the
  article the widest shell state while keeping `Map` and `Context` visible as
  horizontal tabs.

Collapsed rail bodies must be hidden from the visual layout and from keyboard
and assistive navigation only in desktop collapsed states. Collapsed tabs remain
real controls with visible focus, accurate `aria-expanded`, and accessible
labels. Current page context remains visible in the left rail's current chip,
and current page/status context remains visible in the right rail's context
chip.

Tablet and mobile layouts must not inherit the desktop hidden right-rail body.
When the command-bar context control is hidden, the right rail remains visible,
non-inert, and available in normal reading order. The course map remains a
drawer on mobile.

## Implementation Boundaries

Implementation stays in the Glintstone static renderer:

- `packages/static/src/raya_static/rendering.py` for shared shell CSS;
- `packages/static/src/raya_static/shell.py` only if state synchronization
  needs adjustment;
- `tests/e2e/test_preview_static_read_path.py` for the browser regression;
- role/foundation docs only if current guidance does not already describe the
  accepted behavior.

No source schema changes, backend, browser-side renderer, external assets,
storage persistence, hover-triggered expansion, or personal progress language
are part of this loop.

## Role And Tutorial Impact

This is a visible reader UX polish pass. Check these role-guide paths before
completion:

- `docs/guides/en/students/index.md`;
- `docs/guides/en/professors/index.md`;
- `docs/guides/en/contributors/index.md`;
- `docs/guides/en/agents/index.md`;
- `docs/guides/es/estudiantes/index.md`;
- `docs/guides/es/profesores/index.md`;
- `docs/guides/es/colaboradores/index.md`;
- `docs/guides/es/agentes/index.md`.

Update them only if they describe stale collapsed rail behavior. If they do not
name collapsed rails, record the no-impact rationale in the implementation plan
and goal ledger.

## Verification

Use TDD:

1. Add the focused Playwright regression named above and watch it fail for the
   missing width-gain invariant.
2. Make the smallest renderer change that satisfies the test while preserving
   current shell behavior.
3. Run the focused rail tests, render-debug, host check, and Docker check
   sequentially because this loop touches browser-visible renderer behavior.
4. Request adversarial review before claiming completion.

Final verification must include desktop and mobile layout evidence, no
horizontal overflow, keyboard/accessibility state for collapsed rail bodies,
render-debug, and the canonical host/Docker gates.
