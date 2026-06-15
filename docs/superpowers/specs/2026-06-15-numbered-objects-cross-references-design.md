# Numbered Objects And Cross-References Design

## Goal

Add a generalized numbered-object and cross-reference system for rendered course content. The feature must support theorem-like math writing, figures, tables, equations, examples, exercises, homework, assignments, projects, tasks, and course-defined object families without making rendered HTML the authority surface.

The system should be static, rebuildable, and course-adaptable: a course team changes `raya.yaml`, rebuilds, and rendered labels, numbering streams, styles, references, and artifact data update without editing generated artifacts.

## Decisions

- Use fenced directive blocks for authoring numbered/referenceable objects.
- Use course-global object labels.
- Use page-hierarchy numbering by default, based on the rendered course/page display path.
- Use separate numbering sequences by object sequence, not one global counter.
- Collapse related default families into shared sequences, such as theorem-like objects sharing the `theorem` sequence.
- Let courses override and add object families in `raya.yaml`.
- Keep generated numbers as artifact/render output, not source truth.
- Support both automatic references with `@label` and explicit links with `raya:ref/label`.
- Render references and numbers at build time with no browser-side numbering or client-side resolver.
- Write manifest-declared object data under `artifact/data/numbered-objects.json`.

## Authoring Syntax

Authors use fenced directives:

```markdown
::: theorem {#pythagorean title="Pythagorean theorem"}
If $a,b,c$ form a right triangle, then $a^2+b^2=c^2$.
:::

As shown in @pythagorean, the diagonal length follows.

See [the main result](raya:ref/pythagorean).
```

The directive name is the object family. The `#label` is course-global and stable. The optional `title` is rendered beside the generated label when present.

For figures:

```markdown
::: figure {#unit-circle title="Unit circle"}
![Unit circle](_assets/unit-circle.svg)
:::
```

For assignments:

```markdown
::: homework {#derivative-homework title="Derivative practice"}
Compute the derivative of $x^3$ and explain the power rule.
:::
```

For equations:

```markdown
::: equation {#energy-identity}
$$
E = mc^2
$$
:::
```

Proofs are authored as directive blocks too:

```markdown
::: proof
Expand the product and collect terms.
:::
```

By default, proof blocks are unnumbered and visually attached to the nearest preceding theorem-like object when adjacent. A proof may later become referenceable if a course configures the `proof` family as numbered/referenceable, but that is not the default.

## Course Configuration

Courses may configure numbered objects in `raya.yaml`:

```yaml
render:
  numbered_objects:
    numbering: page-hierarchy
    default_style: margin
    sequences:
      theorem:
        style: margin
      example:
        style: margin
      exercise:
        style: banded
      assignment:
        style: banded
      figure:
        style: caption
      table:
        style: caption
      equation:
        style: equation
    families:
      theorem:
        label: Theorem
        sequence: theorem
      lemma:
        label: Lemma
        sequence: theorem
      proposition:
        label: Proposition
        sequence: theorem
      corollary:
        label: Corollary
        sequence: theorem
      definition:
        label: Definition
        sequence: theorem
      example:
        label: Example
        sequence: example
      worked-example:
        label: Worked Example
        sequence: example
      exercise:
        label: Exercise
        sequence: exercise
      problem:
        label: Problem
        sequence: exercise
      homework:
        label: Homework
        sequence: assignment
      assignment:
        label: Assignment
        sequence: assignment
      project:
        label: Project
        sequence: assignment
      figure:
        label: Figure
        sequence: figure
        style: caption
      table:
        label: Table
        sequence: table
        style: caption
      equation:
        label: Equation
        sequence: equation
        style: equation
```

Built-in defaults make common math and course-work objects work without config. Course config may override labels, styles, numbering behavior, and sequence grouping. For example, a Spanish course can change `theorem.label` to `Teorema`; a design course can add `studio-brief` and map it to the `assignment` sequence.

Family and sequence are intentionally separate:

- `family` is the authoring directive name.
- `sequence` controls which numbering stream the object uses.

This allows `theorem`, `lemma`, and `corollary` to share one sequence, while `example`, `exercise`, `figure`, and `equation` keep separate sequences.

Built-in sequence names are `theorem`, `example`, `exercise`, `assignment`, `figure`, `table`, and `equation`. A custom family may use a built-in sequence or a course-declared custom sequence. A custom sequence name that is not built in and not declared under `sequences` is a configuration error.

## Numbering Model

Default numbering is `page-hierarchy`. The numeric prefix comes from the rendered page display path, and the suffix is the sequence count for that sequence on that page.

If a page has visible display path `2.3`, rendered objects on that page become:

```text
Theorem 2.3.1
Lemma 2.3.2
Corollary 2.3.3

Example 2.3.1
Worked Example 2.3.2

Exercise 2.3.1
Problem 2.3.2

Homework 2.3.1
Project 2.3.2

Figure 2.3.1
Table 2.3.1
Equation (2.3.1)
```

Related families share sequence numbers but retain their own labels. The reference target preserves the object family:

```markdown
@pythagorean -> Theorem 2.3.1
@pythagorean-corollary -> Corollary 2.3.3
```

Markdown headings do not affect numbering in this first version. Headings remain page-local reading structure and anchor conveniences. Later work may add explicit numbered sections, but this loop should avoid heading-based renumbering churn.

## Rendering

Generated HTML is static output. Numbering and reference text are resolved during build.

Default styles:

- `margin`: default for theorem-like objects, definitions, examples, and worked examples. The object label and number appear in a left label column on larger screens and collapse above the body on mobile.
- `caption`: default for figures and tables. The caption includes the generated label, number, and optional title.
- `equation`: default for equations. The equation number renders as `(2.3.1)`, positioned to the right when layout allows and below or beside the equation on narrow screens.
- `banded`: default for homework, assignments, projects, exams, tasks, exercises, and problems when a stronger practice/work visual treatment is helpful.

Every numbered/referenceable object gets a stable HTML anchor:

```html
id="raya-object-pythagorean"
```

Reference rendering:

```markdown
As shown in @pythagorean, ...
```

renders as:

```html
As shown in <a href="#raya-object-pythagorean">Theorem 2.3.1</a>, ...
```

Explicit reference links:

```markdown
See [the main result](raya:ref/pythagorean).
```

render as a normal link using the author-provided text and the same target anchor.

## Artifact Data

The build writes `artifact/data/numbered-objects.json` and declares it in `manifest.json`.

Each item includes:

- object label ID,
- family,
- configured display label,
- sequence,
- generated number,
- generated reference text,
- page ID,
- source path,
- source line when available,
- output page path,
- HTML anchor,
- title when present,
- style used,
- numbered/referenceable flags.

This data is the machine-readable surface for agents, future graph tools, inspection pages, and future object indexes. Tools must not scrape rendered HTML as authority.

## Diagnostics

The implementation must fail with actionable diagnostics for:

- duplicate object labels across the course,
- missing object labels on numbered/referenceable objects,
- unknown object family unless configured,
- malformed directive attributes,
- broken `@label` references,
- broken `raya:ref/label` links,
- nested numbered directive blocks, which are unsupported in v1,
- invalid numbered-object config values,
- unknown style names,
- custom sequence references that are neither built in nor declared under `sequences`.

Diagnostics should identify the source file, label or family, and next action.

## Fixtures And Tests

Add a dedicated fixture page:

```text
examples/courses/render-fixture/course/3_numbered_objects/0_index.md
```

It must demonstrate:

- theorem, lemma, corollary, proposition, and definition sharing the theorem sequence,
- example and worked example sharing the example sequence,
- exercise and problem sharing the exercise sequence,
- homework, assignment, project, exam, and task sharing or using assignment/work sequences,
- figure and table caption numbering,
- equation numbering,
- proof block behavior,
- `@label` automatic references,
- `[text](raya:ref/label)` explicit references,
- course config overrides for at least one label/style/sequence case.

Invalid examples belong in tests and diagnostics, not in copyable course content.

Tests should cover:

- parser behavior for directive blocks and inline refs,
- object collection across pages,
- course-global duplicate labels,
- page-hierarchy numbering,
- sequence grouping,
- config overrides,
- rendered HTML and anchors,
- automatic and explicit references,
- `numbered-objects.json`,
- manifest declaration,
- static read path,
- browser/render-debug no raw directive syntax, no unresolved `@label`, no overflow,
- no browser-side numbering or external requests,
- role documentation coverage.

## Documentation

Update role documentation in English and Spanish:

- Professors/profesores: author fenced directive objects, choose stable course-global labels, configure families/sequences/styles, and understand generated numbering as rebuildable output.
- Students/estudiantes: read references such as `Theorem 2.3.1`, `Figure 2.3.1`, and `Equation (2.3.1)`; report broken links, raw directive syntax, unresolved `@label`, or inconsistent numbering.
- Contributors/colaboradores: maintain fixture coverage, diagnostics, artifact data, render-debug gates, and no browser-side numbering.
- Agents/agentes: debug from source and `artifact/data/numbered-objects.json`, avoid editing generated artifacts, verify static-read-path and render-debug evidence.

Update foundation guidance where the source and artifact contracts become current:

- `docs/foundation/17_rendering_execution_plan.md` for numbered object rendering in the rich static baseline.
- `docs/foundation/06_artifact_contract.md` for `numbered-objects.json`.
- `docs/foundation/05_course_contract.md` for fenced directive source syntax as current course source behavior.

## Scope

In scope for this loop:

- fenced directive numbered/referenceable objects,
- course-global object labels,
- built-in grouped families,
- course config overrides and custom families,
- page-hierarchy numbering,
- static rendered labels and references,
- `@label` references,
- `raya:ref/label` links,
- `artifact/data/numbered-objects.json`,
- fixtures, tests, render-debug coverage, and role docs.

Out of scope for this loop:

- heading-based section numbering,
- automatic LaTeX `\label`, `\ref`, or `\eqref` inside math,
- bibliography and citations,
- numbered object indexes or glossaries,
- cross-course references,
- visual config editor,
- student assignment state, grading, or submissions,
- interactive figures or widgets,
- browser-side reference resolution.

## Open Follow-Up

After this loop, the next likely design should cover explicit numbered sections if course teams want heading-derived numbering such as `2.3.4.1`. That should be separate because current headings are page-local convenience anchors, not durable course structure.
