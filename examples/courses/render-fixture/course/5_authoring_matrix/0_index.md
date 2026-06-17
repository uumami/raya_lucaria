---
id: authoring-matrix
title: Authoring Matrix Fixture
summary: Combined fixture page for copyable authoring patterns across math, numbered content, skins, and static environments.
status: ready
---

# Authoring Matrix Fixture

This page is fixture material for renderer and documentation tests. It is a
combined authoring matrix, not canonical pedagogy or architecture truth.

Use the specialized pages for focused coverage: [math authoring](../2_math_authoring/0_index.md),
[numbered objects](../3_numbered_objects/0_index.md), and
[reader UX](../4_reader_ux/0_index.md). Use this page when a change crosses
math, numbered objects, skins, static environments, references, and local assets.

We define page-local notation before use:
$\newcommand{\mat}[1]{\mathbf{#1}}\newcommand{\vect}[1]{\mathbf{#1}}\newcommand{\norm}[1]{\left\lVert #1 \right\rVert}$.

::: theorem {#authoring-theorem title="Matrix norm fixture"}
Let
$$
\mat{I}=\begin{bmatrix}1&0\\0&1\end{bmatrix}
$$
and let $\vect{x}\in\mathbb{R}^2$. Then $\mat{I}\vect{x}=\vect{x}$ and
$\norm{\mat{I}\vect{x}}=\norm{\vect{x}}$.
:::

::: proof {#proof-authoring-theorem of="authoring-theorem" title="Identity proof"}
The matrix multiplication is componentwise:

$$
\begin{bmatrix}
1&0\\
0&1
\end{bmatrix}
\begin{bmatrix}
x_1\\
x_2
\end{bmatrix}
=
\begin{bmatrix}
x_1\\
x_2
\end{bmatrix}.
$$

The norm equality follows from the same vector equality.
:::

::: equation {#authoring-equation}
$$
\mat{I}\vect{x}=\vect{x}
$$
:::

::: figure {#authoring-figure title="Fixture asset path"}
![Static path diagram](../_assets/diagrams/static-path.svg)
:::

::: table {#authoring-table title="Authoring surfaces"}
| Surface | Source pattern |
| --- | --- |
| Math | Page-local macros before use |
| Numbered content | Fenced directives with stable IDs |
| References | `@id` shorthand or `raya:ref/id` links |
| Skin | Section selector under `_raya/skin.yaml` |
:::

::: activity {#authoring-activity title="Authoring check"}
Use @authoring-theorem, @authoring-equation, @authoring-figure, and
[the source reference](raya:ref/authoring-table) to explain why this page is a
combined fixture rather than a separate example course.
:::

::: hint {#hint-authoring-activity of="authoring-activity"}
Start by checking which parts are source files and which parts are generated
artifact output.
:::

::: solution {#solution-authoring-activity of="authoring-activity" title="Fixture path"}
The source page, local asset reference, section skin selector, and fenced
directives are authored source. Static labels, anchors, links, MathJax HTML,
`data-raya-skin`, and copied assets are generated artifact output.
:::

::: answer {#answer-authoring-activity of="authoring-activity"}
This page combines existing authoring patterns so tests can inspect their
rendered output together.
:::
