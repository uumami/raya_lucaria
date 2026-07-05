# Reader Shell Rail Repair Plan

## Goal

Restore the reader shell behavior that made notes large and readable while keeping the current no-top-bar direction.

## Decisions

- Do not bring back a reader top bar.
- Keep reader commands owned by the left course rail.
- Keep the canonical desktop shell breakpoint at 1280px.
- Keep course map state, drawer state, and right-rail state non-persistent.
- Make the right learning rail a normal readable surface below 1280px, not a modal/collapsed drawer.
- Remove blur-based obscuring when the course map opens on tablet-sized reader layouts.

## Steps

1. Add regression tests for tablet course-map opening, mobile/tablet right-rail availability, and desktop context command ownership.
2. Update shell behavior so only phone-sized course-map drawers are modal; tablet drawers do not inert or blur the article/learning rail.
3. Hide/neutralize the right-rail collapse command below desktop and make accidental activation scroll to the existing rail instead of opening a drawer.
4. Adjust CSS so the mobile course-map opener is not a top-left content overlay and drawer backdrops do not blur content.
5. Run focused browser/static tests, then the canonical checks that are feasible in this dirty checkout.
