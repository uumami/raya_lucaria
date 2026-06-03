## Context

Current foundation docs define truth surfaces and a newcomer system overview, and current root/package docs explain the first Docker/uv/Python baseline. OpenSpec config already requires representative fixtures for rendered-output changes. The missing rule is broader: every meaningful change should keep the people who use and maintain Raya Lucaria oriented.

The relevant audiences are:

- contributors/collaborators who change code, specs, docs, and tests,
- professors and course teams who own course material and official canon,
- students who read, study, export, and contribute work,
- agents that operate through explicit files, commands, specs, and diagnostics.

The current repository has examples as fixtures only. That remains correct, but documentation needs a separate surface so fixture content is not mistaken for pedagogy, architecture, or user guidance.

Raya Lucaria implementation work uses English for code, paths, commands, schemas, package names, and stable identifiers. Role documentation for contributors/collaborators, professors, students, and agents must be available as separate English and Spanish role directories with `index.md` pages so each language stays readable and each role can grow into multiple topics.

```text
                 current authority and explanation surfaces

docs/foundation/        OpenSpec specs          role docs/guides
seed truth              testable contracts      how people operate
       |                       |                       |
       +-----------+-----------+-----------------------+
                   |
                   v
           implementation and tests
                   |
          +--------+--------+
          |                 |
          v                 v
examples/fixtures     rendered docs fixture
test material         documentation rendering proof
not canon             not class/course canon
```

## Goals / Non-Goals

**Goals:**

- Make documentation a first-class truth surface below foundation/specs and above examples.
- Require changes to identify documentation impact for contributors/collaborators, professors, students, and agents.
- Require role documentation to use separate English and Spanish role directories while preserving English technical identifiers.
- Keep documentation separate from class/course content and examples.
- Allow rendered documentation or documentation fixtures to exercise Glintstone while preserving static-first behavior.
- Fix documentation hygiene gaps such as `Purpose: TBD` in current specs.
- Add compact OpenSpec config rules so this becomes repeatable for future changes.

**Non-Goals:**

- No new documentation site generator.
- No web UI, backend, identity, search, theme system, or hosted documentation service.
- No attempt to write full professor/student/agent manuals in this baseline.
- No localization framework, translation memory, language toggle UI, or renderer-level language negotiation yet.
- No requirement to add Spanish versions to every course fixture or repository example unless it is documentation for the four role audiences.
- No conversion of `docs/foundation/` into course content.
- No class pedagogy, official course canon, or Rennala study logic introduced by docs fixtures.

## Decisions

### Decision: documentation is a distinct truth surface

Documentation SHALL be listed in the foundation truth-surface hierarchy separately from examples. It explains current behavior and operating workflows, but it does not outrank foundation docs or specs.

Rationale: examples are intentionally fixtures. If documentation is folded into examples, tests can accidentally become user guidance or pedagogy. If documentation is folded only into specs, professors and students get contract language instead of operational help.

Alternative considered: keep root docs and package READMEs as informal guidance only. That keeps the repo smaller, but it does not create a repeatable rule for future changes.

### Decision: documentation impact is role-scoped

Every substantial proposal SHOULD state whether it affects contributors/collaborators, professors, students, or agents. Tasks SHALL include docs updates when those role audiences need new or changed guidance.

Rationale: the audiences use different surfaces. A CLI change may need contributor and agent docs; a course contract change may need professor and agent docs; a study workflow may need student and professor docs.

Alternative considered: one generic "update docs" task. That is too easy to satisfy with a token README edit.

### Decision: role documentation has separate English and Spanish directories

Role documentation SHALL be available as separate English and Spanish role directories, each starting with an `index.md` page. Code identifiers, package names, commands, schema fields, file paths, and stable IDs remain English unless a future localization proposal defines otherwise.

Rationale: the framework can be implemented in English while still serving Spanish-speaking professors, students, contributors/collaborators, and agents. Separate directories are easier to grow into topic pages than flat paired files. Keeping technical identifiers in English preserves current package and command stability.

Alternative considered: put English and Spanish in the same page or use flat paired files. Mixed pages are harder to scan and maintain, and flat files will not scale well as each role gains topics.

### Decision: docs remain readable before rendering

Role-oriented docs SHOULD remain plain Markdown and useful without a build step. English and Spanish versions should be separate role directories with `index.md` pages. Rendering may create a documentation artifact, but source docs must stay inspectable by humans and agents.

Rationale: Raya Lucaria is static-first and portable. Documentation should follow the same rule and remain useful in Git, local files, static artifacts, and coding-agent context.

Alternative considered: make rendered docs the primary documentation source. That would add unnecessary build dependence.

### Decision: rendered documentation is separate from class/course examples

If rendered documentation is added, it SHALL be labeled as documentation or fixture material and kept separate from class/course examples. It may exercise Glintstone capabilities, but it must not define course pedagogy or architecture by example.

Rationale: user documentation can be useful renderer content, but examples remain fixtures and course source remains class material.

Alternative considered: add docs content into `examples/courses/minimal` or `examples/courses/render-fixture`. That would blur the fixture boundary.

### Decision: documentation hygiene includes spec purpose text

Current and archived specs SHOULD have meaningful `Purpose` sections. This baseline SHALL fix existing current spec placeholders and add checks/tasks so future archives do not leave `Purpose: TBD`.

Rationale: specs are contributor and agent documentation as well as contracts. A placeholder purpose weakens navigation and makes future proposal work harder.

Alternative considered: leave purpose cleanup for unrelated housekeeping. The gap was discovered while defining documentation rules, so this change is the correct place to close it.

## Risks / Trade-offs

- [Documentation burden] Requiring docs on every change can become ceremony. Mitigation: require documentation impact analysis, not always new files; "no docs needed" is acceptable when justified.
- [Bilingual maintenance cost] English and Spanish docs can drift. Mitigation: keep baseline docs compact, use clearly named separate role directories, and add checks for both language versions where role docs are updated.
- [Audience sprawl] Four audiences could lead to repetitive guides. Mitigation: keep the baseline compact and update the smallest appropriate surface.
- [Docs becoming authority over foundation] Role docs may drift. Mitigation: truth hierarchy keeps foundation and specs above docs, and docs must reference the authority surface.
- [Rendered docs becoming course examples] A docs fixture could look like class material. Mitigation: label it clearly and keep it separate from `examples/courses/minimal`.
- [Premature docs site design] It is tempting to pick a richer docs stack. Mitigation: use Markdown and the existing Glintstone/static-read-path rules only.

## Migration Plan

1. Update foundation truth surfaces to include documentation and rendered documentation boundaries.
2. Update OpenSpec config rules for proposal/spec/design/task documentation coverage.
3. Add documentation-surface spec requirements and workflow/rendering spec deltas.
4. Fix current spec `Purpose: TBD` placeholders.
5. Backfill current role-documentation entrypoints with separate English and Spanish role directories.
6. Update root/agent/package guidance only where it reflects the new rule.
7. Add a compact rendered-doc source only if needed to test the boundary; if added, use separate English and Spanish role directories.
8. Validate OpenSpec specs strictly and run focused docs-hygiene checks.

Rollback is simple during reset: remove the added documentation rules and any docs fixture, then restore the prior truth-surface hierarchy.

## Open Questions

- Should the first rendered documentation source live under `docs/guides/` with a small `raya.yaml`, or under a separate `examples/docs/` fixture that references docs?
- Should docs hygiene be a script now, or only a documented check until more docs structure exists?
- Should future role topics use fixed names such as `overview.md`, `workflow.md`, and `faq.md`, or stay ad hoc until each role grows?
