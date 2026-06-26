---
id: inline-practice-workspace-handoff
title: Inline Practice Workspace Handoff
status: active
---

# Inline Practice Workspace Handoff

## Context

The current renderer already supports two complementary official-practice
surfaces:

- inline `Official practice` sections at the end of reader pages;
- the generated `_raya/practice/` workspace, including accepted
  `?page=<page-id>` URL focus.

The page shell and course map can already link to page-scoped Practice. The
inline `Official practice` section itself only explains that support can be
revealed in place. Students who reach the inline section should also have a
clear static handoff into the filterable Practice workspace for the same page.

## Options Considered

### A. Keep the handoff only in the course map

This is already implemented, but it hides a useful action away from the place
where students are actually looking at official practice objects.

### B. Add object-level Practice workspace focus

This could be useful later, but it would add object-level URL state and script
behavior. It is too much for this loop.

### C. Add a page-scoped action row to inline Official practice

This is selected. The inline section will show a compact action row linking to
the existing page-focused Practice URL, such as
`../_raya/practice/index.html?page=reader-ux`. It reuses accepted URL focus,
adds no new data, and keeps the page article-first.

## Design

When a reader page has renderable official practice objects, the generated
section remains:

```html
<section class="raya-official-practice" id="raya-official-practice" aria-label="Official practice">
```

Immediately after the explanatory paragraph, it adds:

```html
<p class="raya-official-practice-actions">
  <a class="raya-official-practice-open" href="../_raya/practice/index.html?page=reader-ux">
    Open all page practice
  </a>
</p>
```

The URL is computed by `_render_page()` from the current page output path and
the existing `STATIC_PRACTICE_PATH`, then page-scoped with `_href_with_query()`.
The helper `_render_official_practice_section()` receives the already computed
href and only emits the action row when the section itself renders.

CSS uses existing skin tokens and the current official-practice visual language:
an inline action row, pill-like link, keyboard focus outline, and no layout
shift. No JavaScript is added.

## Boundaries

This loop does not add:

- object-level Practice focus;
- scoring, attempts, submissions, progress, mastery, recommendations, or
  analytics;
- browser storage, fetch, XHR, workers, or service workers;
- external renderer or CDN calls;
- new official-object schema fields or Markdown syntax.

## Testing

Add a failing contract assertion first against the minimal fixture:

- the inline official section contains `.raya-official-practice-actions`;
- the action link has class `.raya-official-practice-open`;
- the link points to the page-scoped Practice URL for the owning page;
- the normal no-private-path/no-fetch/no-storage assertions still hold.

Add or extend browser evidence against the render fixture:

- the action is visible on `reader-ux/index.html`;
- clicking or opening its URL lands on `_raya/practice/index.html?page=reader-ux`;
- the Practice workspace shows the page-focus notice and only reader-page
  official objects.

## Self-Review

- No placeholders remain.
- The design uses already accepted page-scoped Practice URL behavior.
- No new runtime state, data contract, or JavaScript behavior is introduced.
