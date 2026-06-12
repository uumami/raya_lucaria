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

Course pages may use the accepted rich static baseline: tables, math, displayed code, callouts, footnotes, heading anchors, and generated page tables of contents. Code blocks are display-only in this phase, raw HTML is escaped, and rendered support files are generated under `artifact/site/_raya/`.

Course pages may also link to scripts and notebooks beside the learning quantum they support, for example `scripts/clean.py`, `labs/explore.ipynb`, `code/helper.py`, or `notebooks/overview.ipynb`. Glintstone validates linked `.py` and `.ipynb` files by extension and ownership boundary, copies only linked files for reading and download, and previews them statically; they are not executed during build. Use this for transparent supporting work, not for hidden page content or official learning objects.

Courses may declare runtime metadata with root `pyproject.toml`, `uv.lock`, and `runtime/profiles.yaml`. This helps future local or Docker execution stay reproducible, but the current build only records profiles, policies, and cache keys; it does not run code, install packages, refresh caches, or trust notebook outputs.

When a course requires real computation, use explicit targets. `raya run <course> <target>` runs one validated script or notebook; `--dry-run` shows the plan, `--refresh` reruns cache-policy work, and `--docker` uses the declared classroom service. Generated execution logs and outputs stay under `artifact/` and should not be confused with reviewed course source or official answers.

To publish a computed result as reviewed support, first run the explicit target, then inspect it with `raya outputs list <course>`, then use `raya outputs freeze <course> <target>`. Freeze copies the current successful generated result into `_reviewed/execution/<target>/` beside the owning quantum. Review and commit those files like normal course source. Set or keep `policy: frozen` only when the reviewed output should be required and validated without rerunning code.

Student pages should stay focused. Glintstone may show compact resource or reviewed-output panels, but detailed hashes, paths, runtime profile internals, cache keys, and freshness keys belong in artifact data or static `_raya/inspect/` pages for audit.

OpenSpec specs describe accepted contracts. Role documentation explains how to work with those contracts, but it does not outrank foundation docs or accepted specs.

Rendered repository documentation is guidance, not course canon. It is built from `docs/raya.yaml` and remains separate from class material and official course artifacts.
