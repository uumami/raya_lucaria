---
title: Science-Backed Course Shell Design
date: 2026-06-17
status: approved-for-plan
---

# Science-Backed Course Shell Design

## Goal

Create a learning-science foundation and a static renderer course shell that
make Raya courses easier to navigate, easier to study, and harder to misread as
plain document dumps.

The selected scope is **Docs + Static Shell**. This loop preserves broad
learning-science principles in durable documentation, then implements only the
static renderer slice that Glintstone can honestly support now. Dynamic mastery,
analytics, adaptive review, personal study state, and spaced-review queues
remain future work.

## Current Context

Raya's current Glintstone renderer supports static pages, generated navigation,
page tables of contents, build-time MathJax, numbered objects, static
environments, skins, and a local OpenDyslexic toggle. It is technically useful
but still reads like a plain document surface:

- course navigation wraps in a shallow top nav;
- the reading column and page context are not arranged as a stable learning
  shell;
- the current default fixture skin is readable but not yet visually expressive;
- learning-science ideas are scattered across pedagogy, rendering, role docs,
  and conversation history instead of being a durable authority layer;
- static pages do not yet distinguish clearly between what can be implemented
  now and what requires future study state.

The next loop must improve the learning experience without breaking source
authority, static parity, or artifact contracts.

## Workflow Authority For This Loop

The user explicitly selected a Superpowers workflow for this loop and has not
switched back to OpenSpec. This design therefore does not create an OpenSpec
change, spec, task list, or archive entry.

That is a deliberate workflow exception, not a silent change to repository
authority. The implementation plan must update the guidance surfaces that still
present OpenSpec as the only active path when renderer behavior changes:

- `docs/foundation/13_truth_surfaces.md`;
- `docs/foundation/16_documentation_surfaces.md`;
- `docs/foundation/17_rendering_execution_plan.md`;
- `README.md`;
- `AGENTS.md`;
- `openspec/config.yaml`;
- affected role docs;
- documentation-surface tests that encode workflow wording.

The updated guidance should say that `docs/foundation/` remains the highest
source of seed truth, OpenSpec remains an accepted workflow for future contract
changes, and this renderer-learning-shell loop is being driven by committed
Superpowers design and plan documents because the user explicitly selected that
workflow. If the user later switches back to OpenSpec, the Superpowers design
can be mined into an OpenSpec proposal rather than treated as a competing
authority surface.

## Evidence Base

This design uses learning science as the primary decision source. UX/UI
patterns are used only to translate those principles into readable static pages.

### High-Confidence Principles

1. **Cognitive load management.**
   Working memory is limited; instruction should reduce extraneous load, expose
   relevant structure, and support schema formation. Renderer implication:
   stable regions, predictable navigation, compact support surfaces, and no
   decorative clutter that competes with the lesson.

2. **Coherence, signaling, and segmenting.**
   Learners benefit when extraneous material is removed, key organization is
   signaled, and material is served in manageable segments. Renderer
   implication: a course shell should signal page position, goals, prerequisites,
   object labels, next steps, and related practice without overwhelming the
   article.

3. **Retrieval practice.**
   Testing or active recall improves long-term retention more than rereading
   alone. Renderer implication: pages should support checkpoints, self-test
   prompts, and answer/hint/solution blocks. In the current static renderer,
   this is authored content and static reveal/presentation only; dynamic scoring
   is future work.

4. **Distributed practice and spacing.**
   Distributed practice has broad evidence for durable learning. Renderer
   implication: static pages should preserve prerequisites and related-review
   links now; dynamic review schedules are future study-state work.

5. **Interleaving and discrimination practice.**
   Mixed practice can improve learners' ability to choose methods, especially in
   math and problem-solving contexts. Renderer implication: problem sets should
   eventually support tags and mixed-review links. Static rendering can expose
   related problem families but should not claim adaptive interleaving.

6. **Worked examples and completion practice.**
   Worked examples reduce cognitive load for novice learners; a useful
   progression is concept, worked example, partially completed example,
   independent practice, and mixed review. Renderer implication: examples,
   hints, solutions, answers, and problem objects should be first-class,
   scannable page regions.

7. **Self-explanation prompts.**
   Learners benefit when they explain examples and steps to themselves.
   Renderer implication: pages should support prompts such as "why does this
   step follow?" or "what assumption changed?" as authored checkpoint blocks.

8. **Scannability and readability.**
   Web readers scan. Students with weak attention benefit from predictable
   headings, concise summaries, visible next actions, and legible line lengths.
   Renderer implication: top-level chrome, rails, headings, and block labels
   should make pages inspectable before reading every paragraph.

### Source References

- Sweller et al., cognitive load theory and instructional design:
  https://link.springer.com/article/10.1007/s10648-019-09465-5
- Cognitive load and worked examples overview:
  https://www.uky.edu/~gmswan3/544/Cognitive_Load_%26_ID.pdf
- Mayer multimedia learning principles, including coherence and signaling:
  https://www.cambridge.org/core/books/cambridge-handbook-of-multimedia-learning/principles-for-reducing-extraneous-processing-in-multimedia-learning-coherence-signaling-redundancy-spatial-contiguity-and-temporal-contiguity-principles/CD5B7AE1279A9AB81F8EEBB53DBEC86E
- Mayer multimedia learning overview:
  https://www.jsu.edu/online/faculty/MULTIMEDIA%20LEARNING%20by%20Richard%20E.%20Mayer.pdf
- Roediger and Karpicke, test-enhanced learning:
  https://pubmed.ncbi.nlm.nih.gov/16507066/
- Dunlosky et al., effective learning techniques:
  https://pubmed.ncbi.nlm.nih.gov/26173288/
- Dunlosky practitioner summary of high-utility strategies:
  https://www.aft.org/ae/fall2013/dunlosky
- Rohrer and Taylor, interleaving practice:
  https://link.springer.com/article/10.1007/s11251-007-9015-8
- Self-explanation and examples:
  https://asu.elsevierpure.com/en/publications/self-explanations-how-students-study-and-use-examples-in-learning/
- Nielsen Norman Group, scanning and web reading behavior:
  https://www.nngroup.com/articles/how-users-read-on-the-web/
- Nielsen Norman Group, readability:
  https://www.nngroup.com/articles/legibility-readability-comprehension/

## Design Principles

### Preserve Broad Science Without Forcing It Into Static HTML

Every learning-science principle gets one of three status labels:

| Status | Meaning |
| --- | --- |
| `current` | Supported by the static renderer or source contract in this loop. |
| `planned` | Designed now, but implemented in a later static-renderer loop. |
| `future` | Requires dynamic study state, accounts, analytics, adaptive review, or another package boundary. |

This prevents two failure modes:

- losing important science because it is not immediately implementable;
- pretending that static HTML can do adaptive mastery, personal progress, or
  spaced repetition without a future state layer.

### Course Navigation Is The Primary Workflow

The selected student workflow is whole-course orientation. A student should
always know:

- where they are in the course;
- what unit/page they are reading;
- why the page matters;
- what the immediate next action is;
- what explicitly authored or currently indexed practice, assignment, or review
  material exists.

Lesson reading and practice remain important, but they support this primary
orientation workflow.

### Theme Supports Attention, Not Decoration

The Eva Unit 02 default fixture skin should become a stronger visual proof for
the renderer, but the article body must remain calm. The theme belongs mainly
in chrome, rails, object headers, labels, dividers, status chips, and callout
accents. Paragraph text, math, code, and long reading surfaces must stay
legible and high contrast.

## Documentation Architecture

### Foundation Principles

Add `docs/foundation/19_learning_science_principles.md`.

Purpose:

- record evidence-backed learning principles;
- distinguish strong evidence, promising evidence, UX evidence, and local
  design decisions;
- classify each principle as `current`, `planned`, or `future`;
- make clear that Raya is learning-first without hardcoding one pedagogy;
- keep future dynamic features pointed at a durable learning target.

Proposed sections:

- status and authority;
- evidence confidence levels;
- cognitive load;
- segmentation and signaling;
- retrieval practice;
- distributed practice and spacing;
- interleaving;
- worked examples;
- self-explanation;
- motivation and attention;
- accessibility and readability;
- current/planned/future capability table;
- sources.

### Renderer Contract

Add `docs/foundation/20_learning_renderer_contract.md`.

Purpose:

- map learning principles to Glintstone static renderer behavior;
- define what the course shell does;
- define what the shell must not fake;
- explain which future capabilities belong to `study`, `graph`, `web`, or
  other package boundaries.

Proposed sections:

- course shell regions;
- student-default page priorities;
- article and rail responsibilities;
- static learning blocks;
- static course map;
- no fake dynamic progress;
- theme and accessibility boundaries;
- render-debug and screenshot verification;
- role-documentation impact.

### Foundation Index And Rendered Docs

Update:

- `docs/foundation/00_index.md`;
- `docs/render-content/1_foundation/0_index.md`;
- render-content links for new foundation pages.

The readable docs remain under `docs/foundation/`; render-content remains the
ordered render tree only.

### Role Docs

Update English and Spanish role docs:

- professors: how to structure pages for goals, prerequisites, examples,
  checkpoints, practice, and course orientation;
- students: how to use the course shell, rails, page position, checkpoints,
  and next-step cues;
- contributors/collaborators: how to evaluate renderer changes against
  learning principles and accessibility constraints;
- agents: how to verify source/renderer/artifact surfaces and avoid faking
  dynamic learning state.

## Static Course Shell

### Desktop Layout

The static course shell has four regions:

1. **Top command bar.**
   Contains course title, current unit/page label, current page status, and
   reader controls such as OpenDyslexic. Search is out of scope unless a
   concrete static search index is implemented in the same accepted change.
   Do not render a disabled or placeholder search box.

2. **Left course map.**
   Shows ordered course structure from existing page/navigation data. It should
   support units, pages, appendices, and later assignment/project links. It is a
   navigation surface, not artifact truth.

3. **Main article.**
   Keeps actual learning content readable. It owns headings, math, code,
   numbered objects, static environments, callouts, images, tables, and local
   assets.

4. **Right learning rail.**
   Shows page table of contents plus compact learning context from current
   source/artifact data. If metadata is missing, do not render empty or fake
   panels.

   Current right-rail sources:

   | Rail item | Current source | Missing behavior |
   | --- | --- | --- |
   | Page contents | generated heading tokens/table of contents | omit when the page has too few headings |
   | Summary | current normalized page `summary` artifact value | current model always has a normalized value; do not test raw frontmatter absence unless schema changes first |
   | Status | current normalized page `status` artifact value | current model defaults missing status to `ready`; do not test raw frontmatter absence unless schema changes first |
   | Estimated time | page frontmatter `estimated_time` | omit estimate |
   | Tags | page frontmatter `tags` | omit tags |
   | Prerequisites | page frontmatter `prerequisites` as stable page IDs resolved through the artifact page index | omit missing or unresolved prerequisites from the rail; if this loop adds prerequisite diagnostics, they must be validation/build diagnostics backed by tests, not browser-side warnings |
   | Previous/next | existing navigation order | omit missing edge |

   Goals/objectives are not a current frontmatter field. Do not infer goals
   from prose. In this loop, goals may appear only as authored page content
   using existing callouts or numbered/static constructs; a dedicated `goals`
   metadata field is planned for a later source-contract change.

   The implementation must not invent a raw-frontmatter presence signal for
   `summary` or `status` unless it deliberately changes the schema/page model
   and adds contract tests for that change. For this loop, `summary` and
   `status` are allowed because they are already normalized page-local artifact
   values. Prerequisite display is stricter: each entry must resolve to a page
   stable ID; display text should come from the resolved page `nav_title` or
   `title`, and the link should use the resolved page output path. Do not render
   free-text prerequisite labels.

### Mobile Layout

Mobile should collapse the rails rather than squeeze them:

- top bar remains compact;
- course map becomes a collapsed navigation region or top section;
- learning rail content moves below article heading or after article content,
  depending on readability;
- article text remains the priority;
- no horizontal overflow.

### Static Data Sources

Use existing artifact/build surfaces first:

- navigation/page indexes for course map;
- page headings for page table of contents;
- current normalized page artifact fields: `summary`, `status`, `estimated_time`,
  `tags`, and `prerequisites`;
- numbered object data only for labels/anchors already accepted by the current
  numbered-object contract;
- static previous/next links from navigation data.

Do not add new source metadata in the renderer implementation unless the
foundation/course contract is updated in the same loop. Do not infer related
practice from text, tags, or headings in this loop. "Related practice" is a
planned shell surface until an accepted data source exists.

Do not scrape rendered HTML as authority. Do not introduce a browser-side
resolver for navigation, references, numbering, or learning state.

## Pedagogical Blocks

This flow should define the renderer direction for learning blocks, but the
implementation may be split.

### Current Static Blocks

The current implementation slice should display existing constructs better in
the shell and article. It should not add a broad new block grammar.

Current accepted constructs:

- Markdown headings, paragraphs, lists, tables, images, code, footnotes, and
  links;
- build-time MathJax math;
- GitHub-style callouts: `NOTE`, `TIP`, `WARNING`, and `CAUTION`;
- numbered objects, including theorem-like objects, examples, exercises,
  equations, figures, tables, problems, homework, assignments, and configured
  families;
- static environments: `proof`, `solution`, `hint`, and `answer`.

These constructs may be styled and positioned to support learning, but their
source syntax and machine contracts remain the current accepted contracts.

### Planned Static Block Taxonomy

The learning-science docs should define a planned taxonomy for future authoring:

- goals or objectives;
- why this matters;
- prerequisite;
- intuition;
- formal statement;
- worked example;
- checkpoint;
- common mistake;
- problem/exercise;
- hint;
- answer;
- solution;
- next step.

The implementation plan must not overload an existing construct merely because
the planned label is useful. If a page wants a checkpoint today, it can author
one as normal prose, a callout, a numbered exercise/problem, or a static
environment where semantically appropriate. A dedicated checkpoint/goals/common
mistake syntax is planned, not current, unless a later accepted source contract
adds it.

### Future Dynamic Blocks

The following require future study state or service boundaries:

- personal completion;
- mastery status;
- adaptive next problem;
- spaced review queue;
- analytics-driven warnings;
- per-student recommendations.

Static pages may link to review/practice material, but they must not claim
personal progress.

## Eva Unit 02 Visual Direction

The fixture skin should become more clearly Eva Unit 02 while remaining
readable:

- deep red and orange/yellow accents in chrome;
- graphite or near-black control-panel strips where contrast is safe;
- angular borders and thin technical dividers;
- status-chip language for course/page context;
- strong object headers for theorem/problem/example blocks;
- warm pale reading surface for paragraphs and math;
- no dark full-page body for long reading;
- no animated or external assets.

This is a visual proof for the skin system, not a requirement that every course
use anime-inspired visual language. The skin framework remains semantic and
course-adaptable.

## Non-Goals

- No OpenSpec artifacts for this loop unless the user explicitly switches back.
  Instead, update guidance surfaces so the selected Superpowers workflow is
  explicit and not in conflict with current documentation.
- No dynamic progress, login, analytics, mastery, or adaptive review.
- No browser-side MathJax, numbering, references, or course-map resolver.
- No external fonts, CDN CSS, or remote scripts.
- No arbitrary course CSS injection.
- No generated artifact files committed as source truth.
- No role-documentation language mixing.
- No claim that visual theme changes course meaning or authority.
- No search UI unless a real static search index and tests are implemented.

## Testing And Verification

Implementation should use TDD.

Expected tests:

- documentation tests for the Superpowers/OpenSpec workflow wording update in
  relevant foundation docs, README, AGENTS, `openspec/config.yaml`, and role
  docs;
- contract tests for new foundation/render-content pages where documentation
  surface tests already exist;
- static builder tests for generated shell regions;
- static-read-path tests for relative links from root and nested pages;
- browser-driven layout checks for desktop and mobile shell behavior at fixed
  representative viewports, including `1280x900` and `390x844`;
- render-debug screenshots/report checks for no overflow, no external requests,
  local MathJax parity, and readable fixture pages;
- tests confirming missing metadata does not render fake goals, related
  practice, progress, or unresolved prerequisite labels;
- tests confirming the right rail uses only current artifact metadata fields and
  omits absent panels for fields that preserve absence today, such as
  `estimated_time`, `tags`, and unresolved `prerequisites`;
- accessibility tests or browser assertions for semantic landmarks and labels,
  including top command bar, course map navigation, main article, learning rail,
  keyboard-reachable collapsed controls, and visible focus states;
- contrast checks for skin tokens used by the shell, with at least WCAG AA
  contrast for normal text and interactive controls where measurable;
- docs validate/build/inspect;
- render fixture validate/build/inspect;
- hygiene checks.

Expected manual review:

- inspect render fixture in browser at desktop width;
- inspect mobile/narrow screenshot;
- verify OpenDyslexic still changes computed font;
- verify Eva Unit 02 theme is stronger in chrome but does not reduce article
  readability.

## Acceptance Criteria

Documentation:

- `docs/foundation/19_learning_science_principles.md` exists and cites the
  evidence base;
- `docs/foundation/20_learning_renderer_contract.md` exists and maps principles
  to current, planned, and future renderer behavior;
- `docs/foundation/00_index.md` lists both new pages;
- render-content includes the new foundation pages;
- English and Spanish role docs describe the course shell and learning-science
  responsibilities.

Renderer:

- normal student pages render named shell landmarks/regions on desktop:
  top command bar, course map, main article, and learning rail;
- the left course map uses current navigation data;
- the right rail shows only current page-local context from headings,
  `summary`, `status`, `estimated_time`, `tags`, `prerequisites`, and
  previous/next navigation data;
- `summary` and `status` use the current normalized artifact values unless a
  separate schema change preserves raw frontmatter presence;
- prerequisite rail entries render only when stable page IDs resolve through the
  artifact page index;
- absent metadata does not produce empty panels, inferred goals, inferred
  related practice, or personal-progress claims;
- top chrome includes reader controls without wrapping into an unstructured
  link pile;
- nested pages use deployment-neutral relative paths;
- mobile layout has no horizontal overflow at `390x844` or an equivalent
  fixed narrow viewport;
- desktop layout has no horizontal overflow at `1280x900` or an equivalent
  fixed desktop viewport and keeps the article readable beside the rails;
- Eva Unit 02 fixture skin uses named chrome/rail/object-header selectors for
  stronger red/orange/graphite theme accents while preserving AA contrast for
  article text and controls;
- shell controls have visible focus states and can be reached by keyboard;
- OpenDyslexic still changes computed body font when toggled;
- no external CSS, font, script, MathJax, or renderer requests are introduced.

Process:

- Superpowers design spec is committed before implementation planning;
- user reviews the spec before the writing-plans phase;
- implementation uses TDD and verification-before-completion;
- substantial implementation requests code review before merge/push.
