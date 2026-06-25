# Reader Section Context Design

## Context

The reset renderer already generates a page table of contents and the shell
marks the active heading while a student scrolls. The useful signal is present,
but it is easy to miss because it only changes a link style inside the Page
contents panel. Long mathematical pages need a clearer orientation cue that
answers "what section am I reading now?" without becoming a personal progress
bar or analytics surface.

The old `main` branch emphasized persistent side navigation and active location
states. This design adapts that learning value into the current static renderer
by exposing the active heading as compact structural context in the right rail.

## Goals

- Show a compact `Current section` cue on normal article pages when a generated
  page TOC exists.
- Keep the cue derived only from existing rendered heading anchors and TOC
  links.
- Keep the cue structural: it names the active section and links to that
  section, but does not show percentage read, completion, mastery, or progress.
- Preserve current active-TOC behavior, mobile article-first layout, right-rail
  collapse behavior, and no-storage/no-fetch renderer constraints.

## Non-Goals

- Do not add personal reading progress, scroll percentage, completion state, or
  analytics.
- Do not create a new source schema, artifact data file, or inspection surface.
- Do not persist active section state in browser storage or URL parameters.
- Do not infer importance or recommendations from heading order.

## Design

The builder will render a small current-section strip above the existing Page
contents panel when `toc_html` is present. It will contain a static label and a
link placeholder initialized to the first TOC entry. The shell already builds a
list of TOC links and heading targets. `updateActiveHeading()` will also update
the current-section strip whenever the active TOC link changes.

The strip uses these attributes:

- `data-raya-current-section` on the container.
- `data-raya-current-section-link` on the link.

The link remains a normal anchor to the active heading. It is keyboard reachable
only when the right rail body is expanded, because existing rail collapse logic
already manages focusability and `inert` for the rail body.

## Accessibility And UX

The cue is intentionally text-first and small. It should sit near Page contents
so it reinforces section orientation without competing with the article. It
uses `aria-live="polite"` on the link so screen-reader users can hear section
changes without focus being moved.

On mobile, the rail appears after the article in the existing layout; the cue
remains visible there as a compact summary. On desktop, it helps the right rail
feel useful even when the full TOC is collapsed or partially below the fold.

## Testing

Contract tests should prove the generated page contains the current-section
container, link, and shell update hooks only when a page TOC exists.

Browser tests should prove that scrolling to different headings updates both:

- `.raya-page-toc a[aria-current="location"]`
- `[data-raya-current-section-link]`

The same checks should verify no `localStorage`, `sessionStorage`, `fetch`, or
`XMLHttpRequest` calls are introduced in `shell.js`.

## Documentation

Update the learning renderer contract to state that the right learning rail may
show the current article section derived from generated heading anchors. Update
English and Spanish student and agent guides because students use the cue and
agents must verify it without treating it as progress.

## Self-Review

- Placeholder scan: no TBD/TODO placeholders remain.
- Scope check: one renderer affordance only; no new schema or artifact surface.
- Ambiguity check: the cue is structural section context, not progress or
  recommendation language.
