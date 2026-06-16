# Static Environments And Content Objects Design

## Purpose

Raya already supports numbered objects, references, and proof blocks. The next
renderer quality loop should make the broader content-object model explicit:
numbered objects create referenceable records, while static environments render
reader-facing support around those objects without creating numbered records.

This keeps `data/numbered-objects.json` clean for numbered content while giving
professors, students, contributors, and agents a clear way to author and debug
proofs, solutions, hints, and answers.

## Authoring Model

Numbered objects remain fenced directives that create entries in
`data/numbered-objects.json`. They receive numbers, anchors, reference text, and
static links. Existing families such as `theorem`, `definition`, `remark`,
`example`, `problem`, `homework`, `activity`, `assignment`, `figure`, `table`,
and `equation` remain the numbered-object surface.

Static environments are fenced directives that render as course content but do
not create numbered-object records. The initial static environments are:

- `proof`
- `solution`
- `hint`
- `answer`

`proof` keeps its current behavior and may target a numbered object with
`of="object-id"`. `solution`, `hint`, and `answer` may also target a numbered
object with `of="object-id"`, especially for problems, activities, homework,
and assignments. If `of` is omitted, the environment renders as a standalone
static environment.

## Labels And References

When a static environment targets a numbered object, the heading is generated at
build time from the target object's reference text:

- `Proof of Theorem 2.1`
- `Solution of Problem 3.1`
- `Hint for Activity 4.1`
- `Answer to Homework 5.1`

When `of` is omitted, the heading uses the environment label alone:

- `Proof`
- `Solution`
- `Hint`
- `Answer`

Static environments may have stable IDs, such as:

```md
::: solution {#solution-problem-1 of="problem-1"}
Use the normal equations and simplify.
:::
```

The rendered anchor belongs to the static environment, but the environment does
not appear in `data/numbered-objects.json`. Source references to numbered
objects continue to use `@id` shorthand or `raya:ref/id` links. This loop does
not add a reference index for static environments.

## Diagnostics

Build diagnostics should remain actionable for humans and agents:

- Unknown `of` targets fail build with the source file, line, field, and a next
  action that tells the author to use an existing numbered object ID.
- Malformed static-environment attributes fail build.
- Duplicate static-environment IDs fail build.
- Static-environment IDs must not collide with numbered object IDs in the same
  course.
- Nested static environments and numbered objects inside static environments
  remain invalid unless a later contract explicitly supports them.

The diagnostic flow should identify the authored source directive first, then
the target lookup or ID collision that caused the failure.

## Rendering

This loop should not become a full admonition or collapsible-callout system.
Rendering stays simple and static.

`proof` keeps its current proof environment styling and classes. The new
environments use a shared static-environment renderer family with distinct
classes:

- `raya-static-environment`
- `raya-static-environment--solution`
- `raya-static-environment--hint`
- `raya-static-environment--answer`

The heading and target reference text are generated during build. Static pages
must not require browser-side MathJax, a browser-side reference resolver, a
backend, or external renderer/CDN requests.

## Fixture Coverage

The render fixture should include a realistic practice flow that shows:

- a numbered problem or activity;
- a `hint` targeting it;
- a `solution` targeting it;
- an `answer` targeting it;
- a standalone environment without `of`;
- matrix/vector/math content inside at least one static environment;
- static links and rendered reference text that work in local preview and
  deployed static paths.

The existing `reader-ux` fixture is the preferred place to extend this coverage
because it already demonstrates realistic numbered content, proof headings,
matrix/vector math, and render-debug screenshots.

## Documentation

Role documentation should explain the separation clearly.

Professors need copyable authoring examples for `proof`, `solution`, `hint`,
and `answer`, including when to use `of` and why these blocks are not numbered
objects.

Students need to know that solutions, hints, answers, and proofs are rendered
as static course content and that their headings and links are generated during
build.

Contributors need the contract boundary: numbered objects belong in
`data/numbered-objects.json`; static environments do not. Changes must preserve
static rendering without browser-side MathJax or reference resolution.

Agents need a debugging order: source directive, build diagnostic,
`data/numbered-objects.json` target record, rendered anchor and heading, then
render-debug screenshot/report evidence.

English and Spanish role docs remain separate. Technical identifiers such as
`proof`, `solution`, `hint`, `answer`, `of`, `data/numbered-objects.json`,
`@id`, and `raya:ref/id` remain in English.

## Non-Goals

This loop does not add:

- page-level or section-level style overrides;
- collapsible environments;
- browser-side reference resolution;
- a separate static-environment data index;
- a broad callout/admonition taxonomy;
- many new numbered-object aliases.

If alias expansion is needed later, it should happen after the static
environment contract is stable.

## Testing Strategy

Testing should cover the contract at multiple levels:

- parser/contract tests for static-environment directives, target resolution,
  IDs, and diagnostics;
- static-builder tests for rendered headings, anchors, classes, and absence
  from `data/numbered-objects.json`;
- fixture assertions for the `reader-ux` page;
- browser/static-read-path tests proving headings and links work without
  browser-side reference resolution or external renderer requests;
- role-doc tests for English and Spanish guidance.

The loop should use TDD: first add failing tests for the missing `solution`,
`hint`, and `answer` behavior, then implement the smallest static renderer and
diagnostic changes needed to pass.
