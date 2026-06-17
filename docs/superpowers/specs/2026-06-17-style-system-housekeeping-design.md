# Style System Housekeeping Design

## Purpose

Raya now has a real course and section skin system, but the surrounding style
framework should be easier for humans and agents to understand before more
visual customization is added. The next loop should do a balanced pass: clean
only style-adjacent drift, then codify the skin/style rules that already exist
and are safe to build from.

The goal is not a new theme engine. The goal is a clear, inspectable style
framework for course authors, contributors, and agents.

## Current State

The current Glintstone static renderer already supports:

- course-local skin profiles under root `skins/<id>.yaml`;
- course default selection through `render.skin` in `raya.yaml`;
- section selection through `course/**/_raya/skin.yaml`;
- inheritance from course default to the nearest section selector;
- generated `_raya/render/skin.css`;
- rendered `data-raya-skin` attributes;
- semantic color, font, and density tokens;
- allowed built-in font stacks only;
- contrast validation for important color pairs;
- no arbitrary CSS fields in skin profiles;
- no external fonts, CDN requests, or browser-side skin resolution.

The existing docs already mention skins in the foundation rendering plan and
English/Spanish role guides. The next improvement is coherence: make the style
guide explicit, make examples easy to copy, and remove or correct any
style-adjacent guidance that still makes future skin work harder.

## Chosen Approach

Use a balanced pass:

1. audit current skin docs, fixtures, tests, and generated CSS contracts;
2. clean style-adjacent drift only;
3. codify the style guide around the existing model;
4. add small validation, fixture, or doc tests only when the audit finds a real
   contract gap.

This keeps momentum without turning housekeeping into a broad refactor.

## Scope

In scope:

- style and skin guidance in foundation docs;
- English and Spanish role docs for professors/profesores, contributors/
  colaboradores, students/estudiantes, and agents/agentes when relevant;
- render-fixture skin examples if they need clearer style-guide coverage;
- tests for skin contract behavior if a documented rule is not enforced;
- hygiene checks only if style/debug artifacts can currently leak into source;
- concise cleanup of stale style wording or contradictory guidance.

Out of scope:

- page-level skin override implementation;
- a new renderer theme engine;
- arbitrary CSS authoring in skin files;
- external font loading;
- CDN or browser-side skin resolution;
- redesigning `rich.css` unrelated to current skin tokens;
- changing numbered-object styles except where docs need to distinguish them
  from visual skins;
- OpenSpec artifacts for this loop.

## Style Framework Contract

The style framework should be documented as semantic tokens, not arbitrary CSS.

Skin identities:

- skin IDs use lowercase letters, digits, and hyphens;
- a skin file name must match its `id`;
- root `skins/<id>.yaml` defines token values;
- `render.skin` and `_raya/skin.yaml` select existing skins;
- selector files never define token values.

Tokens:

- colors: `page`, `surface`, `text`, `muted`, `accent`, `accent_soft`,
  `border`, `success`, `warning`, and `danger`;
- fonts: `body`, `heading`, and `mono`;
- density: `comfortable`, `compact`, or `spacious`;
- colors use `#rrggbb` hex values;
- fonts use approved local/system stacks only.

Accessibility:

- contrast must stay readable for `text` on `page`, `accent` on `page`, and
  `text` on `accent_soft`;
- diagnostics should identify the file, field, token pair, and next action;
- docs should teach authors to adjust semantic tokens rather than patch CSS.

Generated resources:

- `rich.css` remains renderer structure and component styling;
- `skin.css` remains generated token variables;
- pages activate skins only through `data-raya-skin`;
- static preview and deployed static files use the same local resources.

## Authoring UX

The style guide should make the common path obvious:

```yaml
render:
  skin: warm-academic
```

```yaml
id: warm-academic
name: Warm Academic
tokens:
  color:
    page: "#ffffff"
    surface: "#f6f8fa"
    text: "#1f2328"
    muted: "#57606a"
    accent: "#0969da"
    accent_soft: "#ddf4ff"
    border: "#d0d7de"
    success: "#1a7f37"
    warning: "#9a6700"
    danger: "#cf222e"
  font:
    body: "system-ui"
    heading: "system-ui"
    mono: "ui-monospace"
  density: comfortable
```

```yaml
render:
  skin: practice-lab
```

The docs should clearly say where each snippet lives:

- `raya.yaml` selects the course default;
- `skins/warm-academic.yaml` defines tokens;
- `course/<section>/_raya/skin.yaml` selects a section skin for that subtree.

## Cleanup Rules

Housekeeping in this loop should be targeted. Clean or clarify only when it
directly supports the style framework:

- stale references to old theme systems;
- confusing language that treats skins as content authority;
- missing distinction between numbered-object reader styles and visual skins;
- role-doc drift between English and Spanish;
- fixture examples that are too thin to demonstrate current behavior;
- ignored/generated style-debug output if hygiene misses it.

Do not clean unrelated areas just because they are nearby.

## Testing And Verification

If the loop changes docs only, verification should include:

- `git diff --check`;
- `scripts/check-hygiene.sh`;
- targeted rendered-doc or role-doc checks if existing tests cover them.

If validation, fixture, or renderer code changes, use test-driven development:

- write the focused failing skin contract or builder test first;
- verify the failure;
- implement the smallest fix;
- verify the focused test passes;
- run the relevant skin/static-read-path/render-debug tests.

Representative commands may include:

- `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_skins.py -q`;
- `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q`;
- `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -q`;
- `scripts/check-hygiene.sh`.

Run full `./scripts/check.sh` and `./scripts/check-docker.sh` sequentially if
implementation touches renderer code, validation contracts, or shared
verification behavior.

## Documentation Impact

This loop should strengthen current docs rather than create a separate large
manual unless the audit proves one is needed.

Expected doc surfaces:

- foundation rendering plan: authoritative contract and non-goals;
- professor/profesor docs: copyable authoring examples and usage guidance;
- contributor/colaborador docs: validation, token, generated-resource, and
  testing expectations;
- agent/agente docs: debugging order from selector to CSS and render-debug
  evidence;
- student/estudiante docs: skins change presentation only, not source truth,
  labels, links, object identity, or official content.

Spanish pages should keep the existing ASCII/no-accent style. Technical
identifiers stay in English.

## Success Criteria

The loop is successful when:

- the current skin contract is documented in one coherent style-guide path;
- English and Spanish role docs agree on the same source surfaces and
  non-goals;
- examples identify the exact files where snippets belong;
- any discovered enforcement gap has a focused test and fix;
- hygiene passes and no generated/debug artifacts are committed;
- no new browser-side skin logic, external fonts, CDN requests, or arbitrary
  CSS authoring surface is introduced.
