---
id: numbered-objects
title: Numbered Objects
---

# Numbered Objects

This fixture references @main-theorem, @vector-corollary, @basis-definition, @matrix-equation, @fixture-figure, @fixture-table, @practice-problem, and @homework-one from one course-global shorthand sentence.

::: theorem {#main-theorem title="Fixture theorem"}
Let $A = \begin{bmatrix}1 & 0 \\ 0 & 1\end{bmatrix}$ and $\vec{x} = \begin{bmatrix}x_1 \\ x_2\end{bmatrix}$. Then $A\vec{x} = \vec{x}$.
:::

::: corollary {#vector-corollary}
By @main-theorem, every vector $\vec{x}$ is fixed by the identity matrix.
:::

::: definition {#basis-definition title="Basis"}
A basis is an ordered list of vectors that spans the space and is linearly independent.
:::

::: equation {#matrix-equation}
$$
\begin{bmatrix}
1 & 0 \\
0 & 1
\end{bmatrix}
\vec{x}
=
\vec{x}
$$
:::

::: figure {#fixture-figure title="Fixture diagram"}
![Static path diagram](../_assets/diagrams/static-path.svg)
:::

::: table {#fixture-table title="Fixture values"}
| Vector | Value |
| --- | --- |
| $\vec{e}_1$ | $1$ |
| $\vec{e}_2$ | $1$ |
:::

::: problem {#practice-problem}
Use @matrix-equation to explain why the identity matrix preserves $\vec{x}$.
:::

::: homework {#homework-one title="Homework fixture"}
Review [the theorem](raya:ref/main-theorem), @fixture-figure, and @fixture-table before writing a short solution.
:::
