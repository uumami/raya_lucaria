# Numbered Content Diagnostics And Coverage Design

## Goal

Harden numbered content as a current Glintstone renderer pillar by improving
diagnostics, fixture coverage, and render-debug evidence for course-wide
numbered objects, references, and proof relationships.

The primary authority remains machine-readable build output:

- CLI validation/build diagnostics;
- `manifest.json`;
- `data/numbered-objects.json`;
- rendered static HTML produced from those sources.

Render-debug is the inspection and evidence layer. It should help humans and
agents see what the renderer produced, locate failures, and compare visual
desktop/mobile output, but it must not become the canonical source of numbered
content truth.

## Current Context

The renderer already supports:

- fenced numbered-object directives;
- configurable numbering, sequences, and families under
  `render.numbered_objects`;
- theorem-like, visual, equation, and practice object families;
- `@id` shorthand references and explicit `raya:ref/id` links;
- `data/numbered-objects.json` as manifest-declared artifact data;
- proof blocks that can point to any numbered object with `of="object-id"`;
- build-time MathJax with local static resources only;
- render-debug screenshots, report JSON, and HTML inspection output;
- host and Docker gates that include the render-debug parity path.

The remaining risk is not basic rendering support. The risk is whether authors
and coding agents can diagnose complex course content quickly when numbering,
references, family configuration, proof targets, anchors, or visual output are
wrong.

## Scope

This loop covers numbered-content diagnostics and representative coverage for:

- theorem;
- corollary;
- definition;
- equation;
- figure;
- table;
- problem;
- homework;
- activity;
- assignment;
- proof blocks that target numbered objects.

The fixture should show valid examples only. Invalid authoring examples belong
in tests so role docs and fixture pages remain copyable.

## Numbered Content Matrix Fixture

Add or extend a compact page in `examples/courses/render-fixture` that acts as
a numbered-content matrix. The page should include one small example from each
supported family and enough cross-family references to prove labels, numbers,
anchors, hrefs, and reference text remain stable.

The matrix should include:

- shared sequence behavior for theorem and corollary;
- separate sequence behavior for equation, figure, and table;
- configured practice-family behavior for problem, homework, activity, and
  assignment;
- references using both `@id` and `raya:ref/id`;
- proof blocks targeting at least one theorem-like object and one practice
  object;
- body content that includes Markdown and build-time MathJax;
- local visual/table content that stays static and deployment-neutral.

The page must stay compact. It is a renderer fixture, not pedagogy.

## Diagnostics Contract

Diagnostics should be actionable for humans and coding agents. When possible,
they should include:

- the file read;
- the line or field;
- the bad ID, family, sequence, reference, or target;
- the concrete next action;
- whether the failure occurred during validation, build, or render-debug
  inspection.

Strengthen or confirm diagnostics for:

- unknown numbered-object family directives;
- invalid numbered-object IDs;
- duplicate numbered-object IDs across pages;
- unknown shorthand `@id` references;
- unknown explicit `raya:ref/id` references;
- malformed numbered-object directive attributes;
- unknown proof `of` targets;
- duplicate proof IDs;
- malformed proof directive attributes;
- unsupported or inconsistent `render.numbered_objects` family/sequence
  configuration.

Malformed source should fail before writing a successful new artifact. If a
build fails after an older artifact exists, tests should confirm the old
artifact is not silently replaced by partial success output.

## Render-Debug Evidence

Render-debug should summarize numbered content for captured pages without
becoming authoritative. Its report JSON and inspection HTML should make it easy
to answer:

- which numbered objects were expected on the page;
- which labels and numbers were rendered;
- which anchors and hrefs were present;
- which proof blocks were rendered;
- which proof target each targeted proof resolved to;
- whether raw visible TeX leaked;
- whether browser-side MathJax or external renderer/CDN requests appeared;
- whether screenshots exist for desktop and mobile viewports.

The render-debug gate should continue to fail on missing/empty screenshots,
external renderer requests, browser-side MathJax dependencies, raw visible TeX
outside allowed attributes, and layout evidence problems already covered by the
current gate.

## Documentation Impact

Update role docs in English and Spanish, keeping each language in its own role
directory.

Professor docs should explain:

- how to author the supported object families;
- how family/sequence configuration affects labels;
- how to use `@id` and `raya:ref/id`;
- how to attach proofs with `of="object-id"`;
- what diagnostics to expect for common mistakes.

Student docs should explain only rendered behavior:

- numbered labels;
- static anchors and links;
- proof headings such as `Proof of Theorem 3.1`;
- no browser-side reference resolver or MathJax conversion.

Contributor docs should describe:

- the data and artifact contract;
- expected tests and fixtures;
- render-debug gate expectations;
- no external renderer/CDN requests.

Agent docs should describe:

- the debugging workflow;
- how to compare source directives, `data/numbered-objects.json`, rendered
  anchors, reference text, proof headings, and screenshots;
- when to use CLI/build diagnostics versus render-debug evidence.

Spanish docs should keep technical identifiers such as `@id`, `raya:ref/id`,
`render.numbered_objects`, family names, IDs, commands, paths, and schema fields
in English.

## Testing Strategy

Use TDD for implementation. Start with failing tests that expose the missing
diagnostic or coverage behavior before changing production code.

Expected test coverage:

- contract tests for family/sequence config diagnostics;
- contract tests for invalid directives, duplicate IDs, and unknown references;
- contract tests for proof target diagnostics when mixed with numbered content;
- render fixture build assertions for the numbered-content matrix;
- static read path or browser tests for rendered labels, anchors, hrefs,
  proofs, local assets, and no browser-side MathJax;
- render-debug report tests for numbered-content evidence fields;
- render-debug parity gate tests for screenshots and local/static parity;
- host `./scripts/check.sh`;
- Docker `./scripts/check-docker.sh`.

## Out Of Scope

This loop does not add:

- new numbered-object families beyond the current configured set;
- theorem/proof dependency graphs;
- `data/proofs.json`;
- proof numbering;
- student personalization or study state;
- search, graph UI, slides, or rich interactivity;
- browser-side reference resolution;
- browser-side MathJax conversion;
- external renderer/CDN requests.

Those can be considered later after diagnostics and fixture coverage are
reliable.

## Self-Review

- No open markers remain.
- CLI/data authority and render-debug evidence are separated explicitly.
- The fixture scope is representative but compact.
- Invalid examples are restricted to tests, not copyable docs.
- English and Spanish role documentation impact is explicit.
- Host and Docker verification paths are included.
