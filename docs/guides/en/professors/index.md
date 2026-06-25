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

For shorter authoring, use course-local wikilinks such as `[[First Topic]]` or
`[[First Topic|the first topic]]`. They resolve during validation/build to
normal static links and graph edges when the target uniquely matches a page ID,
alias, title, navigation title, filename stem, or source path. Missing or
ambiguous targets fail validation; use stable IDs for durable links.

Generated child indexes render as section landing cards. Keep summaries,
estimated time, and official objects honest so the cards help students scan
course structure without implying personal progress, mastery, completion, or
recommendations.

Course pages may use the accepted rich static baseline: tables, build-time MathJax math, displayed code with local copy buttons, callouts, footnotes, heading anchors, and generated page tables of contents. Write inline math with single dollar delimiters and display math with double-dollar delimiter lines on their own. Use page-local `\newcommand` or `\renewcommand` for supported macros. Full LaTeX documents, malformed delimiters, unsupported nested delimiters, and unknown macros fail before publication. Code blocks are display-only in this phase, raw HTML is escaped, and rendered support files are generated under `artifact/site/_raya/`.

For common course notation, prefer small page-local macros such as `\newcommand{\rayaVec}[1]{\mathbf{#1}}` and use them consistently after definition. Matrices such as `\begin{bmatrix} ... \end{bmatrix}`, aligned equations, cases, derivatives, integrals, probability notation, optimization notation, and `\renewcommand` for page-local adjustments are fixture-tested. Keep macro definitions close to the page that uses them so diagnostics point to the relevant source page.

Use `examples/courses/render-fixture/course/2_math_authoring/0_index.md` as the current fixture reference for copyable build-time MathJax patterns. It covers inline and display math, `\begin{bmatrix}` matrices, vector macros, `\newcommand`, `\renewcommand`, set and logic notation, norms, inner products, aligned derivations, and optimization notation. Define macros before use, keep them page-local, and use `$$` delimiter lines for larger expressions.

Use `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md` when you want one compact source page that combines math macros, numbered content, references, static environments, local assets, and a section skin.

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
`of="object-id"` to target any numbered object, including theorem-like objects,
practice objects, figures, tables, equations, and configured course families.
They are not numbered objects and do not create records in
`data/numbered-objects.json`. Proofs stay expanded in the argument flow.
`hint`, `solution`, and `answer` render as closed native disclosures by default,
so students reveal them when ready without submitting answers, storing progress,
or loading a browser-side renderer.

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

::: problem {#matrix-practice title="Matrix practice"}
Compute $A\vect{x}$ for
$$
A=\begin{bmatrix}1&2\\0&1\end{bmatrix},
\qquad
\vect{x}=\begin{bmatrix}x_1\\x_2\end{bmatrix}.
$$
:::

::: hint {#hint-matrix-practice of="matrix-practice" title="Start"}
Multiply one row at a time.
:::

::: solution {#solution-matrix-practice of="matrix-practice" title="Worked solution"}
The product is
$$
A\vect{x}=\begin{bmatrix}x_1+2x_2\\x_2\end{bmatrix}.
$$
:::

::: answer {#answer-matrix-practice of="matrix-practice"}
$\begin{bmatrix}x_1+2x_2\\x_2\end{bmatrix}$
:::
```

The `hint`, `solution`, and `answer` blocks above support
`matrix-practice`; they render as spoiler-safe disclosures on the page but do
not create records in `data/numbered-objects.json`.

Use course skins for visual identity and section skins to emphasize units,
labs, appendices, practice sections, or review sections.

Put the course default in `raya.yaml`:

```yaml
render:
  skin: warm-academic
```

Put profile tokens in `skins/warm-academic.yaml`:

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

Put the section selector in `course/<section>/_raya/skin.yaml`. It selects a
profile for that section and its descendants:

```yaml
render:
  skin: warm-academic
```

The selector file does not define colors or fonts; it only names a profile that
already exists under `skins/`.

Skin files define semantic color, font, and density tokens. Keep contrast high,
avoid external fonts, and do not use skins to change course content, links, or
numbered object identity. The source fields are `render.skin`, `skins/`, and
`_raya/skin.yaml`; there are no external fonts in the accepted static contract.
The render fixture uses `eva-unit-02` as its readable default skin example;
copy its pattern when you want a stronger visual identity without reducing
contrast or changing course meaning.

Reader comfort controls such as `Text size` and `OpenDyslexic` are local display
preferences. They do not replace course skins and should not be used to encode
course meaning, level, grading, progress, or official status.

Generated pages can also be printed or saved to PDF as static handouts. Print
mode hides navigation chrome and keeps authored content, MathJax, code, tables,
official practice, numbered objects, and support disclosures readable. Treat
those handouts as generated artifact views, not source truth, grading records,
progress, mastery, or personalized recommendations.

The learning-science course shell works best when source pages give the static
renderer honest structure. Write concise page summaries, stable prerequisites,
clear checkpoints as authored content, worked examples, retrieval practice
prompts, and practice links that students can use without fake progress. Use
checkpoints and goals as visible teaching material until a later source contract
accepts them as metadata.

Rendered pages may show a Page brief near the start of the article. It is built
from accepted metadata such as summary, status, structural page position,
estimated time, tags, resolved prerequisites, explicit graph-link counts, and
official-practice counts. Keep those fields accurate; the brief is orientation
for students, not grading, progress, mastery, personalization, or a
recommendation engine.

The static official practice renderer shows page-level objects from
colocated `_official/` files on their owning page in an `Official practice`
section. Author official cards, prompts, quizzes, and generic official object
fields as plain fields for now. Treat the rendered section as reader-facing
convenience; the authored `_official/` files remain course source authority, and
machine surfaces such as `data/official.json` and `manifest.json` remain the
contract surfaces for tools. Do not design these objects around scoring,
grading, submissions, attempts, progress, mastery, recommendations, backend
calls, browser-side fetching, storage, external renderers, or browser-side
MathJax.

The Official Practice workspace is generated from the same accepted
official objects. Author objects once under the owning page's `_official/`
directory; Glintstone can render both the page section and a static
`_raya/practice/index.html` discovery surface from `data/official.json`. Keep
object labels, summaries, tags, status, and stable IDs useful for scanning, and
expect Practice links to return students to owning page anchors such as
`#raya-official-<id>`. The generated workspace may organize controls, results,
and public context summaries for scanning. Search or Graph may open it focused
on one owning page with a visible page-focus notice and Clear/Escape reset, but
it should not expose hidden answers. Do not author duplicate hidden answers for the workspace or frame it as
adaptive, recommended, scored, graded, submitted, attempted, personal progress,
mastery, stored learner state, runtime fetching, external requests, or a private
source-path view.

Assignments, projects, exams, and tasks also feed a generated Official Tasks
workspace at `_raya/tasks/index.html` and the manifest-declared
`data/tasks.json` index. Put each object in the matching `_official/`
family directory, for example `_official/assignments/` or `_official/exams/`,
and put public planning fields under `content`:

```yaml
id: ps1
type: assignment
authority: official
scope:
  quantum: first-topic
content:
  title: Problem Set 1
  instructions: Practice matrix multiplication.
  due: "2026-09-15"
  points: 10 pts
  weight: 15%
  status: published
  tags:
    - retrieval
```

The tasks workspace helps students scan work by type, text, and due date, then
return to the owning page anchor. Search or Graph may open it focused on one
page with a visible notice and Clear/Escape reset to all visible tasks. It is
not a submission system, gradebook,
personal calendar sync, progress tracker, recommendation engine, or hidden
answer surface.

The Official Schedule workspace at `_raya/schedule/index.html` is generated
from the same accepted task-family objects when they include `content.due` or
`content.available`. It helps students scan dated official work and return to
the owning page anchor. Search or Graph may open it focused on one page with a
visible notice and Clear/Escape reset to all visible dated items. It is not a separate calendar source, personal
calendar sync, reminder system, submission system, gradebook, progress tracker,
or recommendation engine.

Rendered pages now use an expanded course map, rendered as an expanded
hierarchical course map by default, and let
students filter visible page labels or collapse the map to an operable compact map rail
for more reading space. On desktop, `Focus reading` may collapse both the map
and right learning rail as temporary display state. Course-map state, reader
focus, and filter text are
non-persistent UI state. The shell may show structure such as `Page N of M`;
treat that as course position, not personal progress or completion.
Pages may also end with larger Previous/Next cards generated from the authored
course order. You do not author these cards separately; keep the page order and
titles clear, and treat the cards as static navigation, not recommendations.

The generated Course graph can help students inspect explicit page
relationships through local fuzzy search, selected-page details, and an expanded
graph workspace. Students may also use Zoom in, Zoom out, Fit, and Reset view to
inspect dense visual graph areas without changing course data or saved state.
Selected-page details may include a Relationship walkthrough that explains
explicit link kinds and directions with local page and graph-focus controls.
Relationship chips may temporarily narrow that walkthrough for reading, but
they do not create recommendations, progress, saved filters, or new course data.
The graph may hide low-context labels until selection, search, hover, or
keyboard focus makes them useful.
Graph debug state and share URL controls may sit inside a closed native
disclosure by default so students see the graph workflow first.
Treat it as course structure from current artifact data, not as analytics,
recommendations, mastery, or personal progress. Generated page links may open
the graph focused on the current page.

Course Search is a static public discovery surface. It can match titles,
navigation labels, summaries, tags, status, hierarchy labels, stable IDs, and
public rendered article prose approximately, but it does not index hidden source
paths, private support paths, MathJax internals, raw TeX, answer/support-only
content, or personal learner state. Generated page links may preload a
temporary query, but the renderer does not store it. Search results may also
include `View in graph` links generated from stable page IDs so students can
inspect where a found page sits in the course graph. The Search workspace may
show control, results, and context regions from public metadata and public
match snippets. A valid page handoff may show a visible page-focus notice with
the focused public page and visible count until Clear or Escape restores all
results. Those summaries are structural scanning aids, not rankings or
recommendations.

Course pages may also link to scripts and notebooks beside the learning quantum they support, for example `scripts/clean.py`, `labs/explore.ipynb`, `code/helper.py`, or `notebooks/overview.ipynb`. Glintstone validates linked `.py` and `.ipynb` files by extension and ownership boundary, copies only linked files for reading and download, and previews them statically; they are not executed during build. Use this for transparent supporting work, not for hidden page content or official learning objects.

Courses may declare runtime metadata with root `pyproject.toml`, `uv.lock`, and `runtime/profiles.yaml`. This helps future local or Docker execution stay reproducible, but the current build only records profiles, policies, and cache keys; it does not run code, install packages, refresh caches, or trust notebook outputs.

When a course requires real computation, use explicit targets. `raya run <course> <target>` runs one validated script or notebook; `--dry-run` shows the plan, `--refresh` reruns cache-policy work, and `--docker` uses the declared classroom service. Generated execution logs and outputs stay under `artifact/` and should not be confused with reviewed course source or official answers.

To publish a computed result as reviewed support, first run the explicit target, then inspect it with `raya outputs list <course>`, then use `raya outputs freeze <course> <target>`. Freeze copies the current successful generated result into `_reviewed/execution/<target>/` beside the owning quantum. Review and commit those files like normal course source. Set or keep `policy: frozen` only when the reviewed output should be required and validated without rerunning code.

Student pages should stay focused. Glintstone may show compact resource or reviewed-output panels, but detailed hashes, paths, runtime profile internals, cache keys, and freshness keys belong in artifact data or static `_raya/inspect/` pages for audit.

Use `raya preview <course>` to review the generated static site locally before sharing or publishing it. Preview reports the student entrypoint and inspection page, but it does not execute scripts, notebooks, Docker, kernels, package installs, or cache refreshes. Run explicit `raya run` targets separately when computation is required.

OpenSpec specs describe accepted contracts. Role documentation explains how to work with those contracts, but it does not outrank foundation docs or accepted specs.

Rendered repository documentation is guidance, not course canon. It is built from `docs/raya.yaml` and remains separate from class material and official course artifacts.
