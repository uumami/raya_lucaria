---
id: render-root
title: Raya Lucaria Render Fixture
summary: Fixture root for Glintstone static rendering and resource tests.
status: ready
---

# Raya Lucaria Render Fixture

This is fixture material for renderer and e2e tests. It is not canonical pedagogy or architecture truth; use docs/foundation/ for authority.

Raya Lucaria is an open educational framework and commons. Glintstone keeps the static course path useful, Primeval Current names graph work, and Rennala names future study and mastery work.

Read the [static path page](raya:static-path) and inspect the [static path note](_assets/diagrams/static-path.txt).

External links such as [example](https://example.com), [mail](mailto:test@example.com), [phone](tel:123), and [fragment](#fixture) are present so render tests can prove they are not rewritten as local assets.

## Rich Static Baseline

This section is fixture material for the rich static renderer. It uses **strong text**, *emphasis*, `inline code`, and a footnote reference.[^fixture-note]

![Static path asset](_assets/diagrams/static-path.txt)

1. Ordered lists must render.
2. Local content links must still resolve to the [nested page](1_static_path/0_index.md).

- Unordered lists must render.
- Stable links must still resolve to [the nested page](raya:static-path).

> Ordinary blockquotes remain ordinary blockquotes.

> [!NOTE]
> Callouts are static fixture content.
> They can include links such as [Static Path](raya:static-path).

> [!WARNING]
> Warning callouts are visual guidance only; they do not introduce execution.

---

| Surface | Expected static behavior |
| --- | --- |
| Tables | Render semantic table cells. |
| Math | Preserve TeX such as $a^2 + b^2 = c^2$. |
| Assets | Rewrite colocated `_assets/` references. |

$$
\sum_{i=1}^{n} i = \frac{n(n+1)}{2}
$$

```python
def fixture_value() -> str:
    return "<rendered, not executed>"
```

```unknownlang
<script>not_executed()</script>
```

Raw HTML such as <script>alert('fixture')</script> must render safely as text.

## Duplicate Heading

The first duplicate heading receives the base anchor.

## Duplicate Heading

The second duplicate heading receives a suffix anchor.

<!-- raya:index -->

[^fixture-note]: This is a renderer fixture footnote, not canonical course guidance.
