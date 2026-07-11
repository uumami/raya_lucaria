# Reader Rail Session Persistence Design

## Status And Authority

The committed foundation currently defines course-map branch expansion as the
only accepted same-tab shell-storage exception and prohibits persistence for
course-map shell collapse and right-rail context state. The user-approved
decision for this Superpowers loop is to replace that rule with a narrow second
exception for explicit left and right structural rail display state.

This design is a proposed foundation contract change, not evidence that the
change was already current. Implementation must update the smallest affected
foundation contract, every affected English and Spanish role surface, contract
tests, and browser tests before the new behavior is considered accepted. This
decision supersedes the no-shell-storage constraint in the earlier reader-rail
rebuild and space-reclaim designs only for the state described here.

## Context

The rebuilt reader shell lets readers explicitly expand or collapse the left
course rail and right learning rail. Resetting those display choices on every
same-tab page navigation interrupts reading. An initial working-tree follow-up
restores them from `sessionStorage`, but uses origin-global keys and does not
define medium-width conflict handling, first-paint restoration, or complete
failure behavior.

The static artifact must remain useful without storage or JavaScript. Rail
display state is structural UI state, not source truth, artifact truth, learner
state, progress, mastery, recommendation, or personalization.

## Goal

Preserve explicit structural reader rail display choices across refresh and
same-tab page navigation for one stable course without leaking them to another
course or durable storage surface. Keep phone drawers, filters, orientation,
focus, scroll position, active context, and learner state non-persistent.

## Canonical Course Scope

The storage namespace must use the validated `course_id` from `raya.yaml`.
Foundation defines `course_id` as stable course identity across repository
renames and redeployments, and its schema limits it to the collision-safe
pattern `^[a-z0-9][a-z0-9._-]*$`.

The builder will pass `course_id` into reader-page rendering and expose it as
escaped generated markup. It must not derive storage scope from a root page ID,
course title, URL, deployment path, or lossy normalization.

Distinct courses served from one origin must use distinct `course_id` values.
Artifacts that intentionally reuse one `course_id` address the same tab-session
namespace; version-specific isolation would require `course_version_id` and is
outside this change.

The versioned keys are:

```text
raya:reader-shell:v1:<course_id>
raya:course-map-branches:v1:<course_id>
```

The reader-shell key stores one JSON record so coordinated rail changes are
atomic:

```json
{"courseMap":"expanded","learningRail":"collapsed"}
```

For the reader-shell record, only the exact fields and values above are
accepted. Missing keys, malformed JSON, extra or missing fields, and values
other than `expanded` or `collapsed` use responsive defaults without rewriting
storage during initialization.

The branch key stores a JSON array of unique non-empty current-course branch
node IDs whose branches are collapsed. A present `[]` is valid stored state and
means every current branch is expanded; it is distinct from a missing key,
which uses generated authored defaults. A non-array value, malformed JSON, or
any non-string or empty item invalidates the record and uses generated defaults.
Duplicate identifiers are de-duplicated in memory, unknown identifiers are
ignored so course evolution does not invalidate known state, and neither case
causes a read-time rewrite. An explicit branch change writes one de-duplicated
array of current branch IDs in generated map order.

The branch key replaces the existing root-page-derived branch key because that
key has the same cross-course collision defect. Existing root-derived branch
keys and origin-global reader-shell keys are ignored and never migrated or
deleted. They expire with their tab session. The shell never enumerates,
rewrites, or removes unrelated storage keys.

If generated course identity is missing, empty, or malformed at runtime, both
rail and branch persistence fail closed: no storage read or write occurs,
responsive defaults apply, and all controls remain operable.

## Stored Preference And Effective State

The stored record is the last valid explicit structural rail pair. Effective
state may temporarily differ when responsive safety requires it.

At `894px` and wider, both rails may be expanded and the stored pair is applied
directly. An explicit rail control changes that rail, keeps the other rail's
effective state, and writes the resulting pair once.

At `640px` through `893px`, the article-first overlay geometry permits at most
one expanded rail. Opening one rail explicitly collapses the other and writes
the coordinated resulting pair once. Collapsing the open rail writes the
resulting collapsed pair once. If a stored wider-layout pair contains both
rails expanded, effective state becomes both collapsed at this narrower width
without rewriting the stored pair. The next explicit rail action establishes
and stores a valid medium-width pair.

Below `640px`, the phone course-map drawer and always-visible phone learning
context remain non-persistent. This change does not introduce a phone learning
rail drawer. Phone initialization, course-map drawer open or close actions,
backdrop or Escape closure, and phone-to-structural normalization never write
rail state. Returning to structural geometry restores the saved pair under the
rules above.

Escape that explicitly collapses a structural rail is a saved reader action and
writes the coordinated resulting pair once. Escape used for a phone drawer or
another transient surface never writes rail state.

Responsive media-query callbacks must converge through one idempotent
reconciliation path. Whenever responsive reconciliation would hide or inert the
active element, in either breakpoint direction, focus moves first to the
corresponding visible opener or the article. This includes an open phone drawer
becoming structural, focused rail content at `894px` becoming unsafe at
`893px`, and focused structural openers crossing below `640px`.
Reconciliation must preserve correct `aria-hidden`, `aria-expanded`, `inert`,
tabindex, backdrop, and scroll-lock state without writing storage.

## First Paint

Reader pages render escaped `data-raya-course-id`, generated default
`data-raya-course-map` and `data-raya-learning-rail` attributes, and
`data-raya-shell-prepaint="pending"` on `<html>`. They load a small exception-
safe shell prepaint resource synchronously before reader stylesheets, without
`defer` or `async`.

The prepaint resource performs the only initialization read. It validates the
course-scoped record, records the raw valid preference in
`data-raya-course-map-preference` and
`data-raya-learning-rail-preference`, applies the width-safe effective rail
attributes, and sets `data-raya-shell-prepaint` to exactly `valid`, `missing`,
`invalid`, or `unavailable`. It performs no writes or network requests beyond
loading the static resource itself. Reader CSS honors the prepaint marker and
effective attributes, including a valid one-expanded medium state, before
`data-raya-shell-ready="true"`.

The deferred shell adopts this DOM snapshot without rereading storage during
initialization, then completes focus, inertness, and control synchronization.
This prevents a one-shot prepaint read failure followed by a successful deferred
read from causing a late layout change.

Missing storage, invalid state, or any storage exception leaves the generated
responsive defaults in place. The accepted implementation must not flash a
saved-collapsed desktop rail as expanded or a saved medium rail in an unsafe
overlapping state while `shell.js` is delayed.

On a back-forward-cache `pageshow` restoration, the shell performs a fresh
exception-safe, no-write read and reconciles the current stored preference with
the current width and focus rules. Normal initialization and non-persisted
`pageshow` do not perform a second read.

## Storage And Tab Semantics

All storage access is exception-safe. A throwing `window.sessionStorage`
accessor, failed `getItem`, failed `setItem` or quota write, and unavailable
storage must not prevent shell readiness or accessible rail operation.

The shell uses standard `sessionStorage` semantics. It does not synchronize
subsequent changes between tabs and does not use `localStorage`, cookies,
network services, source files, or generated artifact data for rail state. An
opener-created or duplicated browsing context may receive the browser-provided
initial session-storage snapshot; subsequent mutations remain isolated. An
independently created tab session starts from its own state.

## Documentation Boundary

The foundation contract will explicitly identify course-scoped branch state and
the versioned structural rail pair as the only same-tab reader-shell storage
exceptions. The term `volatile` may still describe drawers, filters, active
content context, focus, scroll position, and other transient state, but must not
describe the accepted structural rail display preference.

English and Spanish contributor, professor, student, and agent guidance must
state the same boundary. Guidance that categorically calls rail choice or shell
collapse non-persistent, says rail changes add no storage, or describes all
right-rail Context behavior as volatile must be narrowed or removed. Durable
comfort preferences remain limited to accepted text-size and `OpenDyslexic`
keys.

## Verification

Contract and browser coverage will prove:

- generated reader pages use exact versioned keys derived from `course_id`;
- every page in one course uses the same keys across deployment paths;
- two same-origin courses with identical root page IDs and different
  `course_id` values do not share rail or branch state;
- explicit rail choices survive reload and same-tab page navigation with exact
  stored JSON and no `localStorage` changes;
- Back and Forward navigation reconciles BFCache-restored DOM with the current
  stored pair without writes;
- missing, malformed, incomplete, extra-field, and invalid-value records use
  responsive defaults without writes;
- branch storage distinguishes a missing key from valid `[]`, ignores unknown
  IDs, de-duplicates repeated IDs, and rejects malformed or non-string payloads;
- inaccessible `sessionStorage`, failed reads, and failed or quota-limited
  writes independently leave the shell ready, operable, and accessible;
- a failed write still changes the effective accessible UI while leaving the
  prior stored record unchanged;
- the `639/640`, `893/894`, and `1279/1280` boundaries converge without storage
  writes, overlap, focus loss, stale inertness, or scroll lock;
- a both-expanded stored pair becomes effectively both-collapsed at
  `640px`-`893px` until an explicit action stores a valid coordinated pair;
- phone drawer actions never write rail state;
- exact root attributes and synchronous resource order let delayed `shell.js`
  show the width-safe saved state on first paint without a second read;
- independently created tabs do not share subsequent state, while an
  opener-created tab follows the documented initial-copy semantics;
- tab tests use separate top-level pages in one Playwright `BrowserContext` and
  create the opener case with `window.open`, rather than using separate browser
  contexts that trivially isolate storage;
- stale origin-global and root-derived keys are ignored and unrelated storage
  remains untouched;
- foundation and all English and Spanish role docs contain the accepted
  exception and reject the superseded contradictory wording.

The implementation plan must record red-green checkpoints with exact test
names, commands, and expected failure reasons. Final verification runs focused
contract and browser tests, `./scripts/check-render-debug.sh` for explicit
first-paint evidence, `./scripts/check.sh`, `./scripts/smoke-test.sh`, and
`./scripts/check-docker.sh` sequentially. The plan must use explicit staging
pathspecs and verify the staged-file allowlist so the unrelated modified Tiny
Tray plan cannot enter a persistence commit.

## Non-Goals

- No new source course field, artifact data shape, or package boundary.
- No persistence in `localStorage`, cookies, network services, source course
  files, or generated artifact data.
- No live cross-tab synchronization or durable migration of tab-session state.
- No persistence for drawers, filters, current-page orientation, active
  context, focus, scroll position, progress, mastery, recommendations, or
  personalization.
- No new visual design, responsive breakpoint, or transition duration.
