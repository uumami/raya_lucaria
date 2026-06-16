---
id: docs-guides-en-professors
title: Professors
summary: Guidance for owning course source, official material, review, and publishing decisions.
status: ready
---
# Professors

Course teams own course source, official material, review, and publishing decisions. Start with `docs/foundation/05_course_contract.md`, `docs/foundation/04_ownership_permissions.md`, and `docs/foundation/03_pedagogy.md`.

Examples are fixtures unless a course team explicitly accepts them as course material. Official cards, quizzes, prompts, examples, assignments, exams, projects, and tasks must remain distinguishable from personal, shared, and generated material.

Course source uses `source: course` and visible order inside `course/`: `0_index.md`, `1_foundations/`, `2_practice/`, and `A_reference/`. Put manual introductions in `0_index.md`; Glintstone renders generated child indexes and study counts from page summaries and official objects without overwriting source. Put official learning objects under `_official/` beside the topic they support, and local topic assets under `_assets/`. Use stable frontmatter `id` values and `raya:<id>` links for references that should survive renumbering or moving pages.

Course pages may use the accepted rich static baseline: tables, build-time MathJax math, displayed code, callouts, footnotes, heading anchors, and generated page tables of contents. Write inline math with single dollar delimiters and display math with double-dollar delimiter lines on their own. Use page-local `\newcommand` or `\renewcommand` for supported macros. Full LaTeX documents, malformed delimiters, unsupported nested delimiters, and unknown macros fail before publication. Code blocks are display-only in this phase, raw HTML is escaped, and rendered support files are generated under `artifact/site/_raya/`.

For common course notation, prefer small page-local macros such as `\newcommand{\rayaVec}[1]{\mathbf{#1}}` and use them consistently after definition. Matrices such as `\begin{bmatrix} ... \end{bmatrix}`, aligned equations, cases, derivatives, integrals, probability notation, optimization notation, and `\renewcommand` for page-local adjustments are fixture-tested. Keep macro definitions close to the page that uses them so diagnostics point to the relevant source page.

Use `examples/courses/render-fixture/course/2_math_authoring/0_index.md` as the current fixture reference for copyable build-time MathJax patterns. It covers inline and display math, `\begin{bmatrix}` matrices, vector macros, `\newcommand`, `\renewcommand`, set and logic notation, norms, inner products, aligned derivations, and optimization notation. Define macros before use, keep them page-local, and use `$$` delimiter lines for larger expressions.

Numbered objects are current build-time behavior. Configure family and sequence behavior in `raya.yaml` with `render.numbered_objects.numbering`, `render.numbered_objects.sequences`, and `render.numbered_objects.families`, then author objects with fenced directives and stable IDs:

```markdown
::: theorem {#compactness title="Compactness Criterion"}
Every open cover has a finite subcover.
:::

::: corollary {#finite-subcover}
This follows from @compactness.
:::

::: equation {#risk}
$$
R(f)=\mathbb{E}[\ell(f(X),Y)]
$$
:::

::: figure {#pipeline title="Training Pipeline"}
![Pipeline](_assets/pipeline.png)
:::

::: homework {#hw-compactness title="Homework"}
Use [the compactness criterion](raya:ref/compactness) in your proof.
:::
```

Theorem, corollary, and built-in `remark` objects may share a theorem-family sequence. The default reader presentation uses `scannable` for theorem-like objects, examples, exercises, and assignments; figures and tables keep `caption` presentation, and equations keep `equation` presentation. The course-level customization surface lives in `raya.yaml` under `render.numbered_objects`; page/section style overrides are future work. Use `@id` shorthand or `raya:ref/id` links for source references. Do not write LaTeX `\label` or `\ref` expecting Raya cross-references.

Use the numbered-content matrix pattern when checking a course: include theorem-like, equation, figure/table, and practice objects with stable IDs. Build diagnostics should point to the source file and line for bad IDs, unknown references, malformed directives, and proof targets that do not exist.

Proof blocks can point to theorems, homework, problems, figures, tables, equations, definitions, and activities while keeping each object independently numbered. Use `of` to name the numbered object being proved; the proof renders as a static environment and does not create another numbered object.

Use static environments for support around numbered objects. `proof`,
`solution`, `hint`, and `answer` render during build and may use
`of="object-id"` to target a theorem, problem, activity, homework, assignment,
figure, table, or equation. They are not numbered objects and do not create
records in `data/numbered-objects.json`.

```markdown
::: theorem {#main-theorem title="Fixture theorem"}
For every vector $\vect{v}$, the identity map returns $\vect{v}$.
:::

::: proof {#proof-main of="main-theorem" title="Identity"}
The equality follows component by component:
$$
I\vect{v}=\vect{v}.
$$
:::
```

Course pages may also link to scripts and notebooks beside the learning quantum they support, for example `scripts/clean.py`, `labs/explore.ipynb`, `code/helper.py`, or `notebooks/overview.ipynb`. Glintstone validates linked `.py` and `.ipynb` files by extension and ownership boundary, copies only linked files for reading and download, and previews them statically; they are not executed during build. Use this for transparent supporting work, not for hidden page content or official learning objects.

Courses may declare runtime metadata with root `pyproject.toml`, `uv.lock`, and `runtime/profiles.yaml`. This helps future local or Docker execution stay reproducible, but the current build only records profiles, policies, and cache keys; it does not run code, install packages, refresh caches, or trust notebook outputs.

When a course requires real computation, use explicit targets. `raya run <course> <target>` runs one validated script or notebook; `--dry-run` shows the plan, `--refresh` reruns cache-policy work, and `--docker` uses the declared classroom service. Generated execution logs and outputs stay under `artifact/` and should not be confused with reviewed course source or official answers.

To publish a computed result as reviewed support, first run the explicit target, then inspect it with `raya outputs list <course>`, then use `raya outputs freeze <course> <target>`. Freeze copies the current successful generated result into `_reviewed/execution/<target>/` beside the owning quantum. Review and commit those files like normal course source. Set or keep `policy: frozen` only when the reviewed output should be required and validated without rerunning code.

Student pages should stay focused. Glintstone may show compact resource or reviewed-output panels, but detailed hashes, paths, runtime profile internals, cache keys, and freshness keys belong in artifact data or static `_raya/inspect/` pages for audit.

Use `raya preview <course>` to review the generated static site locally before sharing or publishing it. Preview reports the student entrypoint and inspection page, but it does not execute scripts, notebooks, Docker, kernels, package installs, or cache refreshes. Run explicit `raya run` targets separately when computation is required.

OpenSpec specs describe accepted contracts. Role documentation explains how to work with those contracts, but it does not outrank foundation docs or accepted specs.

Rendered repository documentation is guidance, not course canon. It is built from `docs/raya.yaml` and remains separate from class material and official course artifacts.
