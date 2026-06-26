# Computed Read Time Implementation Plan

**Goal:** Add a build-time estimated-read-time fallback for pages that do not
author `estimated_time`.

**Architecture:** Reuse public rendered article text already produced for local
search. Keep authored `estimated_time` authoritative. Render the fallback only
as reader orientation in the Page brief and right learning rail.

## Task 1: Contract Test

- [x] Add a contract test for a page without authored `estimated_time`.
- [x] Verify RED: the build succeeds but no estimated-time rail exists.

## Task 2: Builder Behavior

- [x] Add a helper that returns `("Estimated time", authored_value)` when
  authored metadata exists.
- [x] Compute `("Estimated read time", "N min read")` from public article text
  when authored metadata is absent.
- [x] Pass the display value to Page brief and right learning rail rendering.
- [x] Verify GREEN with focused contract tests.

## Task 3: Documentation And Verification

- [x] Update the foundation renderer contract.
- [x] Update English and Spanish student, professor, contributor, and agent
  guides.
- [x] Run focused tests, render-debug, and repository checks.
- [x] Request independent review.
- [x] Commit and push.
