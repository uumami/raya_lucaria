# Proof Blocks Design

## Goal

Add current, static proof authoring to Glintstone so mathematical exposition can
show proofs that optionally point back to numbered objects such as theorems,
corollaries, propositions, definitions, equations, figures, tables, problems,
or homework prompts.

This loop is intentionally smaller than a full theorem environment system.
Numbered objects already provide labels, numbers, anchors, hrefs, and
`data/numbered-objects.json`. Proof blocks should use that existing index when
they cite an object, but proofs themselves are not numbered objects.

## Current Context

The renderer now supports:

- fenced numbered-object directives such as `::: theorem {#main-theorem}`;
- course configuration under `render.numbered_objects`;
- course-global shorthand references such as `@main-theorem`;
- explicit links such as `raya:ref/main-theorem`;
- build-time MathJax only, with local static resources and no browser-side
  MathJax conversion;
- render-debug screenshots and inspection for math/numbered-object parity.

The current math authoring fixture still treats `Proof` as authored prose. This
design makes proof blocks current renderer behavior without adding proof
numbering or LaTeX proof environments.

## Authoring Contract

Proofs use fenced directives:

```markdown
::: proof
Expand both sides and simplify.
:::
```

Proofs may point to an existing numbered object:

```markdown
::: proof {of="main-theorem"}
Use the identity matrix calculation from @matrix-equation.
:::
```

Proofs may also declare a stable page-local anchor:

```markdown
::: proof {#main-theorem-proof of="main-theorem"}
The proof body may contain Markdown and build-time MathJax.
:::
```

Accepted proof attributes:

- `#id`: optional stable proof block anchor for rendered HTML.
- `of="object-id"`: optional numbered-object ID that the proof explains.
- `title="..."`: optional explicit title override for special prose such as
  `Sketch of proof`; if present with `of`, the rendered heading still includes
  the referenced object.

Rejected proof attributes should produce actionable diagnostics. Proof IDs use
the same ID character contract as numbered objects.

## Rendered Behavior

Plain proof:

```text
Proof.
<rendered body>
□
```

Proof linked to a numbered object:

```text
Proof of Theorem 3.1.
<rendered body>
□
```

The referenced object text comes from the numbered-object index, so custom
families and labels render correctly, for example `Proof of Activity 3.1.` or
`Proof of Corollary A.2.1.`.

Proof body rendering uses the same Markdown and build-time MathJax pipeline as
ordinary content and numbered-object bodies. No course code, notebooks, Docker,
`uv`, kernels, package installers, runtime profiles, or cache refreshes run
during proof rendering.

Proof blocks should be styled distinctly but quietly:

- a compact heading;
- a readable body;
- an end-of-proof marker `□`;
- mobile-safe layout with no horizontal clipping.

Proofs may have rendered page-local anchors when `#id` is present. They do not
enter `data/numbered-objects.json`, do not receive numbers, and are not targets
for `@id` or `raya:ref/id` in this loop.

## Diagnostics

Build or validation should fail with actionable diagnostics for:

- malformed proof attributes;
- invalid proof IDs;
- unknown `of="..."` targets;
- missing closing `:::` lines;
- nested proof blocks when unsupported;
- nested numbered-object blocks inside proof blocks when unsupported;
- authored text that conflicts with reserved generated proof tokens, if
  generated tokens are used internally.

Directive-looking text inside fenced code, list-item fenced code, and
blockquote fenced code must remain literal text. Proof parsing should share or
mirror the hardened fenced-code behavior already used by numbered objects and
schema link validation.

## Artifact Contract

Proofs are rendered page content. They are not new machine-authority data in
this loop.

Artifacts continue to expose numbered-object truth through
`data/numbered-objects.json`. Proof blocks may link to those objects in rendered
HTML, but no `data/proofs.json` is introduced yet.

A future loop may add proof metadata if graph, dependency, or learning tools
need machine-readable proof relationships. This design deliberately avoids that
until there is a concrete consumer.

## Documentation And Fixture Impact

Update the render fixture with proof examples:

- a plain proof;
- a proof of a theorem;
- a proof of a corollary or equation;
- a proof body containing matrix/vector MathJax;
- code-fence examples proving directive-looking text stays literal.

Update English and Spanish role docs:

- professors: how to author `::: proof` and `of="..."`;
- students: what “Proof of Theorem 3.1” means in static pages;
- contributors: parsing/rendering boundaries and no browser-side MathJax;
- agents: diagnostics and how to inspect proof rendering alongside
  `data/numbered-objects.json`.

Technical identifiers remain English in Spanish docs.

## Testing Strategy

Use TDD. Start with failing tests for:

- parsing plain proof blocks;
- parsing proof blocks with `of` and optional `#id`;
- rejecting malformed attrs and unknown `of` targets;
- rendering `Proof.` and `Proof of Theorem 3.1.`;
- ensuring proofs do not appear in `data/numbered-objects.json`;
- preserving build-time MathJax inside proof bodies;
- ignoring proof directives inside fenced code, list-item fences, and blockquote
  fences;
- render fixture browser checks for no browser-side MathJax, no raw visible TeX,
  local static parity, and no horizontal overflow.

Focused verification should include contract tests, render fixture build,
browser/static-read-path tests, `./scripts/check.sh`, and `./scripts/check-docker.sh`
before merge or push.

## Out Of Scope

This loop does not add:

- proof numbering;
- `@proof-id` or `raya:ref/proof-id` references;
- `data/proofs.json`;
- LaTeX `\begin{proof}` / `\end{proof}` parsing;
- LaTeX `\qed`, `\label`, or `\ref` support;
- collapsible proofs;
- proof dependency graphs;
- executable proof checking.

Those can be considered later if a concrete course or tool needs them.

## Self-Review

- No unfinished markers or deferred work markers remain.
- Proofs are scoped as rendered content, not numbered objects.
- The design reuses existing numbered-object references without changing their
  artifact contract.
- Browser/static parity, MathJax locality, diagnostics, English/Spanish docs,
  and fixture coverage are explicit.
