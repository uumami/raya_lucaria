---
id: numbered-objects
title: Numbered Objects
---

# Numbered Objects

This fixture references @main-theorem, @vector-corollary, @basis-definition, @matrix-equation, @fixture-figure, @fixture-table, @practice-problem, @homework-one, @activity-one, and @assignment-one from one course-global shorthand sentence.

::: theorem {#main-theorem title="Fixture theorem"}
Let $\newcommand{\vect}[1]{\mathbf{#1}}A = \begin{bmatrix}1 & 0 \\ 0 & 1\end{bmatrix}$ and $\vec{x} = \begin{bmatrix}x_1 \\ x_2\end{bmatrix}$. Then $A\vec{x} = \vec{x}$.
:::

::: proof {#proof-main of="main-theorem" title="Fixture proof"}
Let $\vect{v}=\begin{bmatrix}1\\0\end{bmatrix}$ and compare the components of
$A\vect{v}$ with the stated basis relation. The local macros and matrix render
through the same build-time MathJax path used by the theorem.
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

::: activity {#activity-one title="Activity fixture"}
Compare @practice-problem with [the homework](raya:ref/homework-one), then record
one invariant preserved by @matrix-equation.
:::

::: assignment {#assignment-one title="Assignment fixture"}
Use @activity-one and @main-theorem to write a two-line explanation for the
identity matrix case.
:::

::: proof {of="homework-one" title="Solution sketch"}
The reviewed structure is the same static page surface as theorem references:
the proof can point to homework while homework keeps its own numbered identity.
:::

::: proof {of="assignment-one" title="Solution sketch"}
The assignment reduces to the matrix equality in @matrix-equation, so its
numbered target stays a practice object while the proof remains unnumbered.
:::
