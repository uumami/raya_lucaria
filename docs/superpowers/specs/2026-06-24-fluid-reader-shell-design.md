# Fluid Reader Shell Design

## Goal

Make the static reader shell feel like a modern desktop learning workspace while preserving the reset framework's article-first, static, local-only contract.

## Current Context

The reset shell already has the right architecture: a sticky command bar, a left course map, a main article, and a right learning rail. It also already has explicit course-map collapse, right-rail collapse, local text-size and OpenDyslexic controls, graph/search/practice handoff links, no browser-side MathJax, and no runtime data fetching. The gap is visual and ergonomic: rails look like heavy boxes, collapsed controls can read as cramped text, and the article does not feel sufficiently centered and spacious on desktop.

The legacy `main` branch has useful affordances: a persistent left navigation rail, compact collapsed mode, a top context bar, smooth width changes, and icon-forward controls. Those ideas should be adapted, not copied. Legacy dependencies such as Eleventy, Tailwind, Pagefind, external fonts, CDN math, service workers, and persisted navigation state remain out of scope.

## Design

The shell stays a three-region generated static page. Desktop uses a calmer workspace frame:

- course map and learning rail become lighter sticky panels with subtle borders, less visual weight, and bounded scroll;
- the main article gets a wider reading surface and better max-width behavior for prose versus wide content;
- the top command bar stays sticky but becomes denser and more tool-like, with consistent square icon buttons and compact labels;
- collapsed course map and learning rail become clear compact rails with symbolic labels (`Map`, `Info`) and stable hit targets;
- expanded course map links show their generated structural sequence number from existing `data-raya-map-index` attributes so readers can scan location without treating it as personal progress;
- rail panel disclosure animations use the existing grid-row pattern but with smoother opacity/spacing and no layout jumps.

Mobile remains article-first. The command bar may wrap, but must not overflow horizontally or occupy unreasonable height. Course map and learning rail appear below the article and remain readable when expanded.

## Behavior

- Course map starts expanded after the shell script runs.
- Course map collapse is explicit click or Escape, never hover.
- Collapsed course map remains operable: visible compact map links are real links.
- Learning rail collapse hides its body from keyboard and screen-reader navigation through existing `inert` and focus handling.
- Shell state remains transient. Do not add `localStorage`, `sessionStorage`, cookies, fetch/XHR, external assets, or personal progress signals.
- Reader comfort preferences may continue using the shared local accessibility script.

## Implementation Scope

This loop may change:

- `packages/static/src/raya_static/rendering.py` for shell CSS;
- `packages/static/src/raya_static/shell.py` only if needed for accessibility attributes or reduced-motion class hooks;
- `tests/contracts/test_static_builder.py` and `tests/e2e/test_preview_static_read_path.py` for targeted visual/layout assertions;
- `docs/foundation/20_learning_renderer_contract.md` and role docs if the contract language needs a small clarification.

This loop must not change course source contracts, artifact data shape, schema validation, graph/search/practice runtime behavior, official practice authority, scoring, progress, recommendations, or dynamic study state.

## Test Strategy

Add tests before implementation for:

- desktop shell proportions at a wide viewport;
- compact command bar and command button geometry;
- collapsed course map rail uses stable compact targets without wrapped text;
- collapsed learning rail uses a stable compact `Info` target and hides its body from keyboard navigation;
- expanded course map renders structural numbers from existing static map metadata;
- rail disclosure transitions are present in generated CSS;
- no horizontal overflow on desktop and mobile.

Then run focused e2e and contract tests, followed by render-debug and the canonical host/Docker gates before claiming completion.
