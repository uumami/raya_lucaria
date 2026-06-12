---
id: render-root
title: Raya Lucaria Render Fixture
summary: Fixture root for Glintstone static rendering and resource tests.
status: ready
---

# Raya Lucaria Render Fixture

This is fixture material for renderer and e2e tests. It is not canonical pedagogy or architecture truth. Fixture authority remains in docs/foundation/.

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
| Math | Build-time MathJax typesets inline math such as $a^2 + b^2 = c^2$. |
| Assets | Rewrite colocated `_assets/` references. |

Page-local macros are fixture material too:
$\newcommand{\rayaVec}[1]{\mathbf{#1}}\newcommand{\argmax}{\operatorname*{arg\,max}}$.

Escaped dollar signs stay text, such as \$5 and \$x\$.

## Linear Algebra Fixture

Inline vectors use a page-local macro such as $\rayaVec{x}_i$.

$$
\begin{bmatrix}
1 & 0 \\
0 & 1
\end{bmatrix}
\rayaVec{x}
=
\rayaVec{x}
$$

Aligned equations stay in one display block:

$$
\begin{aligned}
\sum_{i=1}^{n} i &= \frac{n(n+1)}{2} \\
\lim_{n\to\infty}\frac{1}{n}\sum_{i=1}^{n} x_i &= \operatorname{E}[X]
\end{aligned}
$$

## Probability and Statistics Fixture

Piecewise, calculus, probability, statistics, and optimization notation should
all be rendered before publication:

$$
f(x) =
\begin{cases}
x^2, & x \ge 0 \\
-x, & x < 0
\end{cases}
$$

$$
\frac{\partial}{\partial \theta}
\int_0^1 p(x\mid\theta)\,dx = 0,
\qquad
\hat{\theta} = \argmax_{\theta \in \Theta} \prod_{i=1}^{n} p(x_i\mid\theta)
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
