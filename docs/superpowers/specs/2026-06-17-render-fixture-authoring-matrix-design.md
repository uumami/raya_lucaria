# Render Fixture Authoring Matrix Design

## Purpose

The existing `examples/courses/render-fixture` is strong as renderer coverage,
but it is split by technical concern: static path, math authoring, numbered
objects, and reader UX. The next improvement is to keep that fixture and add one
combined authoring page that demonstrates how those pieces work together in a
course-like source page.

The goal is not to create a new example course. The goal is to make the current
render fixture more useful as a copyable authoring matrix for professors,
contributors, and agents.

## Scope

In scope:

- Add a new render-fixture section under
  `examples/courses/render-fixture/course/5_authoring_matrix/`.
- Demonstrate one coherent mini-unit with math macros, numbered content,
  static environments, cross-references, a local figure, a table, and a section
  skin selector.
- Add focused tests that prove the page validates, builds, renders static
  labels/references, uses the expected skin, and does not leak raw TeX.
- Add a short role-doc pointer only where it helps people find the combined
  fixture.

Out of scope:

- Creating a separate `authoring-fixture` course.
- Changing renderer behavior or numbered-object semantics.
- Adding page-level skin override implementation.
- Adding new skin tokens, external fonts, arbitrary CSS, CDN requests, or
  browser-side resolvers.
- Reworking existing render-fixture pages beyond small navigation links.

## Fixture Shape

Add:

```text
examples/courses/render-fixture/course/5_authoring_matrix/
  0_index.md
  _raya/
    skin.yaml
```

The new page should be explicit fixture material, not pedagogy or architecture
truth. It should link back to the existing specialized pages and show the
minimum complete source shape a course author can copy.

The section selector should choose the existing `practice-lab` profile:

```yaml
render:
  skin: practice-lab
```

This keeps the fixture inside the current skin contract and gives static
read-path tests one more concrete section-skin example.

## Authoring Content

The page should use one small topic, such as a linear-algebra projection or
identity-matrix unit, and include:

- page-local macros defined before use;
- one theorem-like object with a stable ID;
- one proof targeting that object;
- one equation with display math;
- one figure using an existing local asset from `../_assets/diagrams/`;
- one table;
- one practice object such as `problem`, `homework`, or `activity`;
- `hint`, `solution`, and `answer` blocks targeting the practice object;
- both `@id` shorthand references and `raya:ref/id` links.

The content should stay compact. The page is a fixture matrix, not a textbook
chapter.

## Test Strategy

Use test-first changes for observable behavior. The most useful failing test is
an assertion that the render fixture build contains the new page and its
expected rendered signals before the fixture page exists.

Focused assertions should cover:

- the generated `authoring-matrix/index.html` page exists;
- visible text includes the new page title and key object labels;
- static references render as links rather than raw `@id` text;
- MathJax output exists and visible text does not contain raw matrix TeX;
- the page body activates `data-raya-skin="practice-lab"`;
- the page includes static environment output for hint, solution, and answer.

Existing render-fixture build tests are the natural home for this coverage.
Browser/e2e coverage should be added only if the current static read-path tests
need it to keep local/deployed parity explicit.

## Documentation Impact

Add a short pointer in role docs only if it improves discovery:

- professor/profesor docs may point to
  `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md` as the
  combined copyable authoring matrix;
- contributor/colaborador docs may point to it as the compact fixture to update
  when a change crosses math, numbered objects, skins, static environments, and
  static read-path behavior;
- agent/agente docs may point to it as the first fixture to inspect when a
  problem crosses math, numbered objects, skins, and static environments.

Do not duplicate the full fixture content in role docs. Keep English and Spanish
pages separate, with technical identifiers in English.

## Success Criteria

The loop is successful when:

- the existing render fixture has a combined authoring matrix page;
- the page builds into the static site with local resources only;
- tests prove the page's labels, references, math, static environments, and skin
  activation;
- role docs, if changed, point to the combined fixture without replacing the
  existing specialized fixture guidance;
- no production renderer behavior changes are included in this loop. If the
  fixture exposes a renderer gap, capture that as follow-up work instead of
  expanding this implementation.
