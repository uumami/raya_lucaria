# Course And Section Skin Profiles Design

## Purpose

Raya's static renderer currently owns a single hardcoded visual treatment in
`rich.css`. That is useful for a baseline, but it makes course identity,
unit-level emphasis, accessibility requirements, and future visual maintenance
too tightly coupled to renderer internals.

This loop should introduce a small skin profile system: course authors select a
named skin for the whole course, and sections may select another named skin for
their subtree. The renderer keeps semantic HTML and layout classes; skin files
provide validated visual tokens. This separates rendering logic from visual
identity while keeping static deployment, preview, and render-debug behavior
boring and inspectable.

## Core Model

Skin resolution is layered:

```text
built-in framework skin
  -> course default skin from raya.yaml
    -> nearest section skin from course/<section>/_raya/skin.yaml
      -> future page-level override
```

The first implementation should support the first three layers:

- built-in fallback skin;
- course default selected in `raya.yaml`;
- section override selected by a `_raya/skin.yaml` file beside a section
  `0_index.md`.

Page-level overrides are reserved for a later loop. The contract should not
block them, but implementation should not add them yet.

## Authoring UX

Course-level selection is a single keyword:

```yaml
render:
  skin: warm-academic
```

Course-local skin definitions live at the course root:

```text
skins/
  warm-academic.yaml
  practice-lab.yaml
  high-contrast.yaml
```

Skin files are not learning-order content and should not use numeric ordering
prefixes. Their stable identity comes from the `id` field:

```yaml
id: practice-lab
name: Practice Lab
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

Section-level emphasis uses a selector file beside a section index:

```text
course/
  2_practice/
    0_index.md
    _raya/
      skin.yaml
```

```yaml
render:
  skin: practice-lab
```

The section selection applies to that section and its descendants until a
descendant section selects another skin.

## File Contract

Course-local skin definitions:

- live under root `skins/`;
- are YAML files;
- carry an `id` that matches the referenced skin ID;
- define required semantic tokens;
- are source support, not rendered pages and not assets.

Section skin selectors:

- live only at `course/**/_raya/skin.yaml`;
- may only appear beside a directory page's `0_index.md`;
- select a skin ID but do not define token values;
- inherit downward through authored page order;
- are source support and should not render as pages.

The `_raya/` directory is a private source support directory for Raya-authored
metadata. It should not be confused with generated `artifact/site/_raya/`
browser resources.

## Skin Tokens

Skins define semantic tokens, not arbitrary CSS. V1 tokens should cover the
current rendered surface without exposing every CSS property:

- colors: `page`, `surface`, `text`, `muted`, `accent`, `accent_soft`,
  `border`, `success`, `warning`, and `danger`;
- fonts: `body`, `heading`, `mono`;
- density: `comfortable`, `compact`, or `spacious`.

The renderer converts these tokens into CSS variables:

```css
:root {
  --raya-color-page: #ffffff;
  --raya-color-text: #1f2328;
  --raya-color-accent: #0969da;
  --raya-font-body: system-ui;
}
```

`rich.css` should consume the variables instead of hardcoded colors and font
stacks. HTML remains semantic and class-based. Skins must not change source
truth, page order, numbered object IDs, references, artifact data, or build
execution behavior.

## Rendering Resources

Generated site resources should stay static and deployment-neutral:

```text
artifact/site/_raya/render/
  rich.css
  skin.css
  math/mathjax.css
```

`rich.css` owns structural renderer styles and semantic class rules. `skin.css`
owns generated CSS variables for built-in and course-local skins. Pages should
carry the resolved skin ID in an inspectable attribute:

```html
<body data-raya-skin="practice-lab">
```

`skin.css` should contain one static variable block per available skin:

```css
[data-raya-skin="practice-lab"] {
  --raya-color-page: #ffffff;
  --raya-color-text: #1f2328;
}
```

Pages activate the resolved skin only through `data-raya-skin`. This keeps
copied static-site parity simple and avoids browser-side skin resolution.

## Validation

Validation should fail before publishing unreadable or ambiguous skin output.

Required diagnostics:

- unknown `render.skin` values in `raya.yaml`;
- unknown section skin IDs in `_raya/skin.yaml`;
- duplicate course-local skin IDs;
- skin file `id` that does not match its filename stem, for example
  `skins/practice-lab.yaml` must contain `id: practice-lab`;
- missing required token groups or token values;
- invalid hex color values;
- invalid density value;
- unsafe or unsupported font declarations;
- `_raya/skin.yaml` outside a valid section directory;
- arbitrary CSS fields in v1 skin files.

Accessibility checks should include at least:

- `text` on `page`;
- `accent` on `page`;
- `text` on `accent_soft`.

Diagnostics must name the file, field, detected value, and a concrete next
action. They should list available skin IDs when a selector is unknown.

## Documentation And Style Guide

Documentation is part of the feature, not follow-up cleanup.

`docs/foundation/17_rendering_execution_plan.md` should define the skin
contract, authority boundary, and non-goals for this loop. A separate
foundation file can be considered in a later documentation-structure cleanup if
skin guidance grows beyond the rendering plan.

Role docs must be updated in English and Spanish:

- professors: how to select a course skin, define course-local skins, apply a
  section skin, and use skins to emphasize units, labs, appendices, practice
  sections, or review sections;
- contributors/collaborators: token validation, renderer boundaries, generated
  resources, tests, and no arbitrary CSS in v1;
- agents: debugging order from `raya.yaml` or `_raya/skin.yaml`, through skin
  definitions, diagnostics, generated CSS, rendered body attribute, and
  render-debug evidence;
- students: skins change visual presentation only; they do not change source
  authority, object identity, links, or official/generated labels.

Copyable guide examples should include:

- `render.skin` in `raya.yaml`;
- `skins/<id>.yaml`;
- `course/<section>/_raya/skin.yaml`;
- a note that `_raya/skin.yaml` selects a skin rather than defining tokens.

Style guide rules should say:

- define semantic tokens, not random CSS;
- keep skin IDs stable and descriptive;
- keep course-local skins under root `skins/`;
- use `_raya/skin.yaml` for section emphasis;
- maintain contrast;
- avoid external fonts and CDNs;
- do not use skins to change content order, object IDs, references, execution,
  or artifact authority.

## Testing Strategy

Testing should cover the feature at contract, builder, browser, and docs
levels:

- schema/contract tests for skin file loading and validation;
- invalid fixture tests for unknown skin, duplicate skin ID, bad color, missing
  token, low contrast, invalid density, unsafe font, and invalid selector
  location;
- builder tests proving course default skin and section inheritance resolve to
  the expected page skin IDs;
- static site tests proving generated CSS resources are local and
  deployment-neutral;
- browser/static-read-path or render-debug checks proving active skin IDs are
  visible in rendered pages and copied static previews;
- docs contract tests requiring EN/ES role guidance for `render.skin`,
  `skins/`, `_raya/skin.yaml`, contrast, and no external fonts or CDNs;
- local `./scripts/check.sh` and Docker `./scripts/check-docker.sh` gates.

The render fixture should include at least two skins and one section override
so agents and humans can inspect visual differences without needing a real
course.

## Non-Goals

V1 does not add:

- arbitrary course CSS;
- external fonts or CDN loading;
- JavaScript-based theme switching;
- per-user dark mode;
- page-level skin frontmatter;
- layout templates;
- skin-driven numbering, references, object identity, navigation, execution, or
  artifact data changes;
- image/logo branding beyond tokenized visual treatment.

These can be revisited after the token contract, validation, and section
inheritance model are stable.

## Housekeeping Relationship

Housekeeping should happen before implementation or as explicit preparatory
tasks, but it should serve this skin-system design. Relevant cleanup includes:

- moving hardcoded renderer CSS out of `rendering.py` only where needed for
  tokenization;
- checking ignored generated files and dependency/cache artifacts;
- ensuring generated `artifact/`, `node_modules/`, `.venv*`, `__pycache__/`,
  and local brainstorm/debug files are not committed;
- avoiding broad unrelated refactors.

The skin loop should not become a general repository cleanup loop. General
GitHub and ignore hygiene can follow as its own Superpowers loop if needed.
