## Context

The foundation already says a course must be understandable as source files, directories and pages are learning quanta, and generated indexes should feed future study and agent domains. Current specs validate Markdown content and build readable static pages, but they do not yet define how source order becomes navigation, how section indexes are generated, or how references survive moves and renumbering.

This change makes Glintstone's baseline authoring model convention-first:

```text
content/
  0_index.md
  1_foundations/
    0_index.md
    1_limits.md
    2_derivatives.md
  2_practice/
    0_index.md
    1_optimization.md
  A_reference/
    0_index.md
```

The tree is for creators and agents. Rendered pages are for students and should expose clean labels, URLs, generated indexes, breadcrumbs, and study hooks without showing filename mechanics.

## Goals / Non-Goals

**Goals:**
- Make source order visible and easy to inspect without requiring a parallel outline file for normal courses.
- Keep rendered URLs, stable IDs, and generated navigation independent from order prefixes.
- Generate local indexes, master indexes, breadcrumbs, previous/next links, and artifact data from source truth.
- Keep manual index prose in source while rendering generated index sections into artifacts only.
- Make published learning pages stable enough for official learning objects, future Rennala study state, Primeval Current graph data, and Sellen context assembly.
- Keep English and Spanish role documentation separate when this authoring model is documented.

**Non-Goals:**
- No full graph UI, search engine, glossary extraction, cross-course graph, or personal progress UI.
- No spaced repetition scheduling or personal study state.
- No required explicit `outline.yaml` baseline. Explicit outlines can be added later for alternate curricula, reused content, or translation-specific sequencing.
- No dependency on a specific static-site generator, JavaScript framework, backend, or hosted service.
- No generated source-file rewrites; generated sections stay in artifacts.

## Decisions

### Convention-first order

Use ordered filename and directory prefixes as the baseline source-order contract. Numeric prefixes define the main sequence, and letter prefixes define appendices/anexos. Glintstone parses prefixes numerically, so `10_` follows `2_`.

Alternative considered: frontmatter `order`. Rejected for the baseline because order becomes hidden across many files and duplicate or missing order values are harder for professors and agents to review.

Alternative considered: required `_outline.yaml`. Rejected for the baseline because it creates a second truth for ordinary courses. It remains a good future override for alternate course maps.

### One source style, strict diagnostics

Scaffolds should use unpadded prefixes: `0_index.md`, `1_topic.md`, `2_topic.md`. Validation may accept padded equivalents such as `00_index.md` or `01_topic.md`, but a sibling set must not mix prefix widths among main ordered entries and duplicate normalized order values must fail.

This balances the user's preferred simple names with existing fixture compatibility and clear diagnostics.

### Section landing pages

Each rendered directory must have a section landing page named by normalized order zero, canonically `0_index.md`. The landing page contains manual prose and metadata for the directory quantum. Directory metadata files are not required.

### Stable identity and links

Published pages and section landing pages use frontmatter `id` as the stable reference. Source links may use `raya:<id>`, which validation resolves to the current page regardless of order prefix or path moves. Normal Markdown links remain valid, but diagnostics should recommend `raya:` links when durable course references are intended.

Order prefixes are never stable identity. Slugs come from stripped filenames unless explicitly overridden later by a separate proposal.

### Generated indexes are artifact-only

Source index pages keep manual prose. Glintstone renders generated child, appendix, and study summaries into the artifact:

```markdown
# Foundations

This unit gives the conceptual base.

<!-- raya:index -->
```

If the marker is absent, the default generated index is appended after manual prose in a predictable location. Generated sections are never written back into source.

### Metadata baseline

Use YAML frontmatter because it is familiar from Jekyll-style systems and easy for humans and agents to edit. The minimum stable baseline is:

- `id`: stable page or section identity.
- `title`: full display title, with H1 fallback when safe.
- `nav_title`: optional short navigation label.
- `summary`: generated index preview, with first-paragraph fallback for draft material.
- `status`: draft, ready, archived, or deprecated.
- `estimated_time`: optional student planning signal.
- `tags`: optional search/filter/graph hints.
- `prerequisites`: stable IDs for prerequisite learning quanta.
- `aliases`: prior IDs or routes that should resolve to the current page.

The implementation can start with validation and data export for these fields before richer UI uses all of them.

### Generated data surfaces

The build emits normalized machine surfaces:

```text
data/navigation.json
data/indices.json
data/pages.json
data/quanta.json
data/links.json
```

`navigation.json` owns tree order, labels, breadcrumbs, previous/next, parent/children, clean URLs, and appendix placement. `indices.json` owns generated local/master index entries, summary cards, and study counts. Future dynamic domains read the manifest and data indexes, not rendered HTML.

### Hierarchy labels

Course configuration may name hierarchy levels, for example Unit/Topic or Chapter/Section. The source tree still defines containment and order; labels only affect rendered vocabulary and data fields. Defaults should remain conservative so courses do not need configuration for basic use.

## Risks / Trade-offs

- Filename prefixes can cause rename churn when reordering -> Stable `id` and `raya:` links preserve references; future CLI commands can move/renumber safely.
- Prefix variants can confuse authors -> Scaffolds use one style; validation fails duplicate normalized order and mixed widths in one sibling set.
- Generated index placement can surprise authors -> Support `<!-- raya:index -->` and use a documented append fallback when absent.
- Requiring IDs adds authoring work -> IDs protect future cards, graph edges, study state, translations, and aliases; scaffolds and diagnostics should make them easy.
- Students may see source mechanics -> Rendered labels and URLs strip prefixes and expose hierarchy labels, titles, summaries, and study context instead.
- Automatic summaries may be poor -> Prefer frontmatter `summary`; use first paragraph only as fallback and warn for missing or weak summaries on published pages.
- Appendix ordering can overfit one academic style -> Support A/B/C and AA/AB only as a separate appendix sequence after main content; courses can label it Appendix or Anexo.
