# Fluid Reader Shell Design

## Goal

Make the static reader shell feel continuous, modern, and comfortable on desktop while preserving the current static-renderer contract: no backend, no runtime fetches, no persistent learner state, no browser-side MathJax, and no external renderer/CDN dependencies.

## Context

The old `main` branch had useful UX instincts: a dense top bar, theme-aware visual rhythm, collapsible navigation, graph controls, and interaction that felt more like an application than a raw document. The current reset branch has rebuilt those ideas with stronger contracts: generated course map, command bar, right learning rail, graph workspace, OpenDyslexic/text-size controls, local scripts, local assets, and browser tests.

The current pain is comfort and continuity. The shell already has collapsible course map and learning rail behavior, but the affordances are too quiet, the panel transitions can feel abrupt, and desktop reading does not yet make the controls feel like one coordinated workspace. Students should be able to scan the page, collapse context, reopen it, and keep reading without the layout feeling cramped or jumpy.

## Approaches Considered

### A. Large Visual Redesign

Replace the reader shell with a new app-like layout and restyle the navigation, rail, article, command bar, and graph at once.

This could move fastest visually, but it has high regression risk because the renderer currently has many static-read-path, accessibility, and no-storage guarantees. It would also blur which UX change caused any e2e failure.

### B. Fluid Shell Pass

Improve the existing shell affordances in place: clearer command states, smoother collapse/expand transitions, more stable desktop widths, better rail-panel disclosure styling, and reduced-motion behavior.

This is the recommended path. It directly addresses the visible discomfort without replacing the current architecture. It also keeps tests focused on concrete behavior: no overflow, no vertical wrapped controls, visible collapsed tabs, accessible hidden state, and smooth-state CSS that disables under reduced motion.

### C. Graph-First Pass

Spend the next loop on graph interaction polish only: denser toolbar, better selected-node detail, and more visual feedback.

This is valuable later, but the reader shell is the surface students use before they decide to open the graph. Fixing the shell first improves every page and reduces the sense that the framework is a narrow mobile layout stretched onto desktop.

## Design

Implement a bounded fluid shell pass over the existing generated reader HTML, CSS, and local shell script:

- keep the current command bar, course map, article, and right rail regions;
- make desktop grid transitions explicit and smooth only after `data-raya-shell-ready="true"`;
- preserve `prefers-reduced-motion: reduce` by disabling nonessential transitions;
- make collapsed map and collapsed context tabs visually intentional, with stable width and no vertical word wrapping;
- improve rail panel disclosure styling so collapsed panels read as real controls, not broken headings;
- keep rail panel content hidden from keyboard and assistive navigation when collapsed;
- keep tablet and mobile article-first behavior, with the course map opened as an intentional drawer;
- avoid layout shifts that push the article under controls or resize buttons unpredictably;
- keep command-bar controls visibly grouped and keyboard-focusable.

The change should use current skin tokens rather than hard-coded theme colors. Evangelion-style or other course skins can make the shell more expressive, but this slice should improve the reusable shell mechanics first.

## Boundaries

- Do not add a frontend framework, Tailwind, Eleventy, Cytoscape, CDN, service worker, runtime fetch, or browser-side MathJax.
- Do not persist shell, rail, graph, font, or search state to browser storage.
- Do not add learner progress, completion, mastery, ranking, recommendation, or personalization wording.
- Do not change course source contracts or artifact data schemas.
- Do not import old `main` files wholesale; adapt only the useful interaction principles to the current renderer.
- Do not make mobile the primary layout at desktop widths. Desktop should use available horizontal space with article-first balance.

## Documentation

Update `docs/foundation/20_learning_renderer_contract.md` to clarify that the reader shell may use coordinated, reduced-motion-aware transitions and visually intentional collapsed rails/tabs as static display state.

Update English and Spanish student and agent role docs. Students should understand the shell controls as reading comfort tools. Agents should verify accessible hidden state, reduced-motion behavior, no storage, no external requests, and no source/private path leakage.

## Tests

Contract tests should verify that generated HTML still exposes the required shell controls, state attributes, and collapsed-tab affordances.

Browser tests should verify:

- desktop starts expanded and uses a wider article-centered layout;
- collapsing the map and context produces stable compact rails/tabs with no vertical wrapped text;
- rail panel toggles update `aria-expanded`, `aria-hidden`, `inert`, and keyboard reachability;
- repeated collapse/expand does not create measurable article overlap or horizontal overflow;
- reduced-motion mode disables shell/panel transitions;
- mobile keeps the article readable and opens/closes the course-map drawer without hiding the learning rail from accessibility.

Render-debug should continue checking desktop/mobile screenshots, overflow, local resources, raw TeX, and static-site parity.

## Self-Review

- No placeholders remain.
- Scope is a single implementation loop over existing reader-shell mechanics.
- The design advances the main-branch UX fusion goal without importing legacy architecture.
- The design remains compatible with current foundation constraints and static renderer boundaries.
