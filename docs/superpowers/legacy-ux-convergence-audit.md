---
id: legacy-ux-convergence-audit
title: Legacy UX Convergence Audit
status: active
---
# Legacy UX Convergence Audit

## Authority

This audit supports the active Superpowers UX/UI fusion goal. It is a working
inventory, not architecture authority. `docs/foundation/` remains the highest
current source of truth, especially:

- `docs/foundation/13_truth_surfaces.md` for legacy-reference discipline;
- `docs/foundation/17_rendering_execution_plan.md` for renderer and skin
  boundaries;
- `docs/foundation/20_learning_renderer_contract.md` for current static
  learning renderer behavior.

Legacy `main` branch files are historical evidence. Their user experience can
inspire current work, but their Eleventy/Tailwind/runtime architecture must not
be copied into the reset renderer.

## Legacy Evidence Inspected

The legacy `main` branch evidence inspected for this audit:

- `src/eleventy/_includes/layouts/graph.njk` showed a graph page with search,
  layout select, fit/reset, expand, legend, and a controls disclosure.
- `src/eleventy/src/js/graph.js` showed Cytoscape graph behavior: fuzzy search,
  force/hierarchy/circular/grid layouts, degree-scaled nodes, directed arrows,
  hover neighborhood spotlighting, click-to-open nodes, fit/reset,
  expand/contract, node dragging, and chapter filter chips.
- `src/eleventy/src/js/sidebar.js` showed collapsible desktop sidebar,
  mobile sidebar overlay, and saved sidebar/nav scroll state.
- `src/eleventy/src/js/nav-state.js` showed expandable navigation sections,
  accordion behavior, current-page auto-scroll, and saved expanded sections.
- `src/eleventy/src/js/theme-toggle.js` showed browser-side theme cycling over
  dark/light theme stylesheets.
- `src/eleventy/src/js/font-toggle.js` showed text-size and OpenDyslexic
  comfort toggles.
- `src/eleventy/src/css/main.css` showed reader typography, sidebar layout,
  component blocks, quiz styling, tables, code blocks, and responsive embeds.
- `src/eleventy/src/css/themes/*.css` showed old visual themes such as Eva
  Unit 02 dark/light.
- `src/eleventy/src/js/copy-code.js`, `keyboard-nav.js`, `search-init.js`,
  `quiz.js`, `toc.js`, `theme-toggle.js`, `sw.js`, and `mermaid-init.js`
  identify additional legacy frontend capabilities or experiments.

## Convergence Inventory

| Legacy capability | Legacy evidence | Current status | Decision | Next action |
| --- | --- | --- | --- | --- |
| Graph page as a first-class workspace | `layouts/graph.njk` | Current `_raya/graph/index.html` generated from artifact graph data | Converged and expanded | Keep improving current static graph only |
| Graph search | `graph.js` fuzzy search | Current graph has local search, spotlight, keyboard result flow, and URL state | Converged | Keep tests focused on local-only behavior |
| Graph layouts | `force`, `hierarchy`, `circular`, `grid` in legacy graph | Current graph has Connections, Topology, Cluster, Map, Radial, and List layouts | Adapted | Prefer current deterministic layouts over force simulation |
| Graph fit/reset | `graph-fit`, `graph-reset` | Current graph has Fit, Fit selection, Reset view, Reset graph | Converged | No legacy import needed |
| Graph expand/contract | `graph-expand` height toggle | Current graph focus mode collapses side panels and supports `expanded=1` URL state | Adapted | Treat current focus mode as the replacement |
| Graph pan/zoom | Cytoscape wheel/pan | Current graph has zoom buttons, pan buttons, keyboard pan, pointer pan, and reset view | Converged | Maintain browser e2e coverage |
| Graph node dragging | Cytoscape node dragging and help text | Current graph accepts constrained desktop mouse SVG node repositioning as transient readability state; tests cover edge geometry updates, no storage, no URL mutation, touch refusal, and reset behavior | Adapted | Keep it non-persistent, bounded, mouse-only, and documented as visual cleanup rather than layout editing |
| Graph hover neighborhood spotlight | `mouseover` highlights neighborhood and fades unrelated elements | Current graph has hover/focus inspection, preview bubble, dimming, and connected states | Adapted | Continue improving clarity without ranking language |
| Graph chapter/group color chips | Legacy chapter legend chips hide/show nodes | Current graph group filters hide/show generated course groups and graph palette comes from validated skin tokens | Adapted | Current group filters are the accepted model |
| Graph degree and directional cues | `graph.js` sizes nodes by degree, reveals labels for higher-degree nodes, colors edges by source chapter, and draws target arrows; `graph.njk` explains hierarchy direction | Current graph has degree-based node radius, contextual label reveal, generated arrow markers, edge colors, and explicit relationship-kind classes | Adapted and expanded | Keep these as structure readability cues only, not importance, progress, or ranking |
| Graph relationship types | Legacy graph had directional edges but no authored relationship-kind filters | Current graph distinguishes navigation, parent, content, and prerequisite relationships, with filters and selected-page chips | Current branch exceeds legacy | Continue relationship comprehension work only if needed |
| Graph help disclosure | `Controles del grafo` in graph layout | Current graph has `Graph controls` native disclosure with current controls and non-progress language | Converged | Keep wording aligned with current contracts |
| Sidebar collapse | `sidebar.js` desktop collapse | Current course map collapses into an operable map rail; right rail collapses into an operable context tab | Adapted | Do not restore hover-first or saved shell state |
| Mobile sidebar overlay | `sidebar.js` mobile menu and overlay | Current course map opens as a mobile drawer with backdrop, Escape close, and scroll lock | Adapted | Current drawer is the accepted model |
| Navigation accordion | `nav-state.js` expandable sections | Current course map supports nested collapse/expand, current path, expand all, less/current controls, and filter | Adapted | Keep current accessible map behavior |
| Saved nav/sidebar state | `localStorage` keys for sidebar and nav expanded paths | Current contract forbids shell/navigation persistence | Rejected | Do not port saved shell state |
| Current-page auto-scroll | `nav-state.js` scrolls current item into view | Current course map auto-orients current page into visible region | Converged | Keep non-persistent orientation |
| Theme cycling | `theme-toggle.js` swaps theme stylesheet and stores theme | Current course and section skins are source-selected profiles under `skins/`; browser-side skin authority is forbidden | Rejected | Do not add browser-side skin switching |
| Eva visual identity | `eva-02-light.css`, `eva-02-dark.css`, other theme CSS | Current render fixture uses course-local Eva Unit 01/02/03 and Ghost In The Shell skin profiles with validated tokens | Adapted | Improve skins only through source profiles and validation |
| OpenDyslexic | `font-toggle.js` | Current static renderer copies local OpenDyslexic resources and exposes reader/workspace controls | Converged | Keep as local comfort preference |
| Text size comfort | `font-toggle.js` size classes | Current reader/discovery controls expose text-size comfort behavior | Converged | Keep as local comfort preference |
| Computed reading effort hint | `eleventyComputed.js` `readingTime`; `base.njk` reading-time display | Current renderer supports authored `estimated_time`; current Superpowers slice adds build-time `Estimated read time` fallback from public article text when authored metadata is absent | Adapted | Keep authored `estimated_time` authoritative and treat fallback as approximate orientation only |
| Copyable code | `copy-code.js` | Current renderer has copyable fenced code blocks | Converged | Maintain no-execution contract |
| Keyboard page navigation | `keyboard-nav.js` | Current renderer supports previous/next keyboard navigation from generated sequence links | Converged | Keep static course-order semantics |
| Search workspace | `search-init.js` and old search components | Current generated Search workspace uses local script and generated search index | Adapted and expanded | Keep section/object subresults and graph handoffs |
| Table/code/blockquote/article typography | `main.css` base styles | Current renderer owns rich Markdown, syntax highlighting, math, print, and responsive shell CSS | Converged | Future work should refine current CSS, not port Tailwind |
| Component block families | `main.css` component colors for homework, exercise, prompt, example, exam, project, quiz, and embed plus component labels/badges | Current renderer separates static environments, numbered objects, official practice cards, accepted official tasks, assignments, exams, projects, and schedule items | Adapted and expanded | Keep object families explicit in current source contracts and generated workspaces instead of porting generic legacy component wrappers |
| Quiz interactivity | `quiz.js` and quiz CSS | Current static official quizzes render as safe official objects, not scored browser attempts | Rejected as legacy behavior | Do not add scoring, attempts, or learner-state quiz logic |
| Mermaid browser init | `mermaid-init.js` | Current renderer forbids external renderer/CDN requests and browser-side rendering dependencies | Rejected | Use static authored assets or future accepted renderer contracts |
| Browser-side KaTeX init | `katex-init.js` | Current math is build-time MathJax with local artifact resources | Rejected | Do not add browser-side math conversion |
| Service worker/offline behavior | `sw.js`, `sw-register.js` | Current static deployment parity does not include service worker caching | Out of scope for UX convergence | Requires separate foundation/security/deployment design before any renderer implementation |
| Slides | Legacy layouts/scripts mention slides | Current renderer scope is static learning pages and workspaces | Deferred | Requires a separate source/artifact contract |

## Rejected Legacy Behaviors

Do not port these behaviors into the current renderer:

- CDN graph libraries or external renderer scripts. The old graph loaded
  Cytoscape from a CDN; the current graph must stay local and static.
- Browser-side MathJax, KaTeX, Mermaid, or other renderer conversion.
  Build-time rendering and local artifact resources are current authority.
- Browser-side theme stylesheet cycling as skin authority. Current skins are
  source-selected course/section profiles and generated `skin.css` variables.
- Saved shell/navigation state in browser storage. The current shell allows
  storage only for explicit comfort preferences such as text size and
  OpenDyslexic, not course map state, graph state, reader focus, or rail state.
- Quiz scoring, attempts, submissions, grading, progress, mastery, or
  recommendation behavior in static browser pages.
- Legacy Eleventy, Tailwind, old source paths, or old generated JSON shapes as
  implementation architecture.

## Remaining Candidate Subgoals

1. **Convergence cleanup pass.** Remove or rewrite stale Superpowers wording
   that implies legacy behavior is still missing when it is now converged.
   This is documentation housekeeping, not renderer behavior.

2. **Skin polish through source profiles.** Improve course-local skin examples
   and documentation through validated `skins/*.yaml` profiles only. Avoid
   browser-side skin switching.

3. **Graph learning affordance polish.** Continue improving current graph
   affordances only where they help students interpret explicit relationships:
   orientation text, selected-page detail language, preview bubble clarity, and
   graph help wording. Do not add inferred recommendations.

4. **Discovery workspace comfort parity.** Compare Search, Practice, Tasks, and
   Schedule controls against Graph's newer grouped control style and bring
   useful consistency to those surfaces.

5. **Housecleaning.** After another convergence pass, clean docs and ignored
   local evidence files so current guidance, examples, and Superpowers records
   do not drift.

## Out Of Scope Until Foundation Decision

- Static offline/service-worker behavior. Legacy `sw.js` and `sw-register.js`
  are rejected as implementation sources. Offline support may be valuable later,
  but it needs a separate deployment and security foundation decision before it
  becomes renderer work.

## Suggested Next Loop

The best next implementation loop is **Discovery Workspace Comfort Parity**.
The Graph workspace now has the most mature control grouping and context
language. Search, Practice, Tasks, and Schedule should be inspected for the
same usability qualities: grouped controls, clear active context, visible reset
paths, stable keyboard behavior, and no storage or external requests.

This is more useful than theme switching because it improves daily student
workflow without violating skin authority. It is also more immediately useful
than offline support because it builds on current static workspaces and can be
verified with existing e2e/static-read-path patterns.

## Verification For Future Loops

Future frontend/graph loops should keep using:

- focused contract tests for generated HTML attributes and local scripts;
- browser e2e tests for actual interaction, no storage, no external requests,
  no overflow, and no broken keyboard behavior;
- `./scripts/check-render-debug.sh` for visible renderer/site parity;
- `./scripts/check.sh` and `./scripts/check-docker.sh` before commit/push;
- independent review with at least one reviewer checking current foundation
  contracts and one reviewer checking legacy-feature fidelity when legacy UX is
  part of the loop.
