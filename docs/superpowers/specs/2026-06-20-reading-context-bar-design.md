# Reading Context Bar Design

## Purpose

The static learning shell already has a sticky command bar with course tools, but
it does not keep the current page context visible while a reader scrolls through
long material. This slice adds a compact static reading-context strip to the
command bar so students can keep orientation without opening the course map or
right rail.

## Scope

Add generated context inside the existing top command bar:

- course title;
- current page title;
- structural page position such as `Page 5 of 6`;
- compact previous and next page links when those pages exist;
- existing Search, Graph, Course map, Text size, and OpenDyslexic controls.

The links use the same generated sequence navigation already used by the article
and right rail. The graph and search command links remain page-aware.

## UX Rules

- The page title must be visible in the sticky chrome on desktop.
- The page position is structural course position, not personal progress.
- Previous and next links are compact affordances with accessible labels.
- On narrow screens the context may wrap above the tools, but it must not cause
  horizontal overflow.
- The article remains the primary reading surface; this is orientation chrome,
  not a new content panel.

## Constraints

- Use only current `ContentPage` and `ContentModel` data.
- Do not persist command-bar state.
- Do not add browser storage, fetches, external libraries, CDN resources,
  recommendations, mastery, completion, or learner-progress wording.
- Do not change course source contracts or artifact data shapes.
- Do not remove article-level previous/next links or breadcrumbs in this slice.

## Testing

Tests should prove:

- rendered HTML includes a `raya-reading-context` region with page title and
  structural page position;
- previous and next links use deployment-neutral relative URLs;
- root/last pages omit unavailable previous/next links without placeholders;
- desktop and mobile command bars avoid horizontal overflow;
- the visible text still avoids learner-state wording.
