---
id: math-authoring
title: Math Authoring Fixture
summary: Fixture page for current build-time MathJax authoring patterns.
status: ready
---

# Math Authoring Fixture

This is fixture material for renderer and documentation tests. It is not canonical pedagogy or architecture truth. Fixture authority remains in docs/foundation/.

This page demonstrates current valid math authoring patterns. Invalid examples belong in tests and diagnostics, not in copyable course notes.

## Inline And Display Math

Inline math such as $e^{i\pi} + 1 = 0$ should be typeset during build.

Display math uses delimiter lines on their own:

$$
\int_0^1 x^2\,dx = \frac{1}{3}
$$

Escaped currency stays text, such as \$10.

## Vectors And Matrices

Page-local vector notation can be defined before use:
$\newcommand{\rayaVec}[1]{\mathbf{#1}}$.

Vectors and matrices should render without raw TeX leakage:

$$
\begin{bmatrix}
1 & 2 \\
3 & 4
\end{bmatrix}
\rayaVec{x}
=
\rayaVec{y}
$$

## Page Local Macros

Define page-local macros before the expressions that use them:
$\newcommand{\fixtureNorm}[1]{\left\lVert #1 \right\rVert}\newcommand{\fixtureInner}[2]{\left\langle #1, #2 \right\rangle}$.

Norms and inner products should render as MathJax output:

$$
\fixtureNorm{\rayaVec{x}}^2 = \fixtureInner{\rayaVec{x}}{\rayaVec{x}}
$$

## Sets Logic And Functions

Set, logic, and function notation should render in ordinary course notes:

$$
f: A \to B,
\qquad
\forall x \in A,\ \exists y \in B \text{ such that } y = f(x)
$$

Sequences and limits should render before publication:

$$
(a_n)_{n\ge 1},
\qquad
\lim_{n\to\infty} a_n = L
$$

## Aligned Derivations And Optimization

Aligned derivations stay in one display block:

$$
\begin{aligned}
g(\theta)
  &= \sum_{i=1}^{n} \log p(x_i\mid\theta) \\
\hat{\theta}
  &= \operatorname*{arg\,max}_{\theta \in \Theta} g(\theta)
\end{aligned}
$$

Cases remain part of the accepted MathJax subset:

$$
h(x) =
\begin{cases}
x^2, & x \ge 0 \\
-x, & x < 0
\end{cases}
$$

## Numbered Objects And Math Authoring

Math authoring remains build-time MathJax: inline math, display math, and page-local macros are rendered before the static page is served. Numbered objects and references are current renderer behavior through fenced directives, `@id` shorthand references, and explicit `raya:ref/id` references. Detailed directive examples live on the [numbered object fixture page](../3_numbered_objects/0_index.md). Raya source references do not use LaTeX label/ref commands.

> [!NOTE]
> **Theorem.** This theorem-like block is authored Markdown. It is not an automatic theorem environment.
>
> If $a,b \in \mathbb{R}$, then
>
> $$
> (a+b)^2 = a^2 + 2ab + b^2.
> $$

**Proof.** Expand the product and collect terms:

$$
(a+b)(a+b) = a^2 + ab + ba + b^2.
$$

Proof blocks are rendered statically in the numbered object fixture page. They can
point to theorems, homework, or other numbered course objects while keeping math
pre-rendered at build time.

Render-debug evidence should confirm that numbered content and math are static,
local, and free of browser-side MathJax conversion.

## Macro Redefinition

Page-local redefinition is accepted when it remains local to the page:
$\newcommand{\fixtureUnit}{\mathrm{unit}}\renewcommand{\fixtureUnit}{\mathrm{u}}$.

The redefined macro should render before publication:

$$
\rayaVec{v}_{\fixtureUnit}
=
\begin{bmatrix}
5 \\
8
\end{bmatrix}
$$
