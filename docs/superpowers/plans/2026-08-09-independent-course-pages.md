# Independent Course Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide a pinned reusable GitHub Pages workflow that proves the Raya CLI can build an independently owned Spanish `ia_o26` course repository and publish its static artifact.

**Architecture:** The framework owns a reusable implementation adapter that checks out the caller course and its own immutable workflow revision, then validates, builds, inspects, and packages the static read path. Each course owns its release policy and protected Pages environment; `ia_o26` contains only CLI-generated source and a thin caller pinned to one framework SHA.

**Tech Stack:** GitHub Actions reusable workflows, GitHub Pages, Python 3.10, Node 22, uv, Raya CLI, pytest.

## Global Constraints

- Course source uses `source: course`; generated `artifact/` is ignored.
- The caller uses an exact full framework commit SHA, never a branch or mutable tag.
- The reusable workflow checks out its own `job.workflow_repository` at `job.workflow_sha`; callers do not supply a second framework ref.
- Pull requests verify only; only default-branch pushes deploy.
- Verify jobs explicitly use `contents: read`; only the protected deployment job receives `pages: write` and `id-token: write`.
- Every third-party action is pinned to a reviewed full commit SHA; organization-level SHA enforcement is enabled only after existing framework workflows are migrated.
- GitHub Pages is an optional adapter; `artifact/site` must also pass neutral local static-serving verification.
- `ia_o26` is public, Spanish, and titled `Inteligencia Artificial — Otoño 2026 (ITAM)`.

---

## File Structure

| Path | Responsibility |
| --- | --- |
| `.github/workflows/reusable-course-pages.yml` | Framework reusable verification and Pages deployment. |
| `tests/contracts/test_reusable_course_pages_workflow.py` | Static workflow contract test. |
| `docs/guides/en/contributors/publishing-courses.md` | GitHub Pages adapter, migration, local-hosting, and shared-origin guidance. |
| `docs/guides/es/colaboradores/publicar-cursos.md` | Spanish equivalent contributor guidance. |
| `docs/guides/en/contributors/index.md` | English guide index entry. |
| `docs/guides/es/colaboradores/index.md` | Spanish guide index entry. |
| `ia_o26/raya.yaml` | CLI-generated course identity. |
| `ia_o26/course/0_index.md` | Replaceable Spanish course root. |
| `ia_o26/.github/workflows/pages.yml` | Thin caller workflow. |

### Task 1: Add and test reusable course workflow

**Files:**
- Create: `tests/contracts/test_reusable_course_pages_workflow.py`
- Create: `.github/workflows/reusable-course-pages.yml`

**Interfaces:** Consumes `course_path`; checks out the defining workflow repository/SHA; produces a verified Pages artifact and a default-branch-only Pages deployment.

- [ ] **Step 1: Write the failing workflow contract test**

Create a test that reads `.github/workflows/reusable-course-pages.yml` and asserts: `on.workflow_call`; `course_path`; checkout of `${{ job.workflow_repository }}` at `${{ job.workflow_sha }}`; `uv sync --locked`; validation/build/inspection commands; a read-only `verify` job; `upload-pages-artifact` inside `verify` with path `${{ github.workspace }}/${{ inputs.course_path }}/artifact/site`; a separate `deploy` job with `needs: verify`, `github-pages` environment, Pages-only permissions, and the default-branch-push condition; and all external `uses:` references match a full 40-character SHA rather than a tag.

- [ ] **Step 2: Prove the test fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_reusable_course_pages_workflow.py
```

Expected: failure because the reusable workflow does not exist.

- [ ] **Step 3: Implement the reusable workflow**

Create a `workflow_call` workflow with only a `course_path` string input. Its `verify` job has `permissions: {contents: read}`, checks out caller source, then checks out `${{ job.workflow_repository }}` to `.raya-framework` at `${{ job.workflow_sha }}`, sets up Node 22, Python 3.10, and uv through these reviewed SHA pins: `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803`, `actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020`, `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065`, and `astral-sh/setup-uv@d4b2f3b6ecc6e67c4457f6d3e41ec42d3d0fcb86`. It runs `npm ci` and `uv sync --locked --python 3.10 --all-packages --dev` in `.raya-framework`, then executes:

```bash
course_root="${GITHUB_WORKSPACE}/${{ inputs.course_path }}"
uv run --directory .raya-framework raya validate "$course_root"
uv run --directory .raya-framework raya build "$course_root"
uv run --directory .raya-framework raya artifacts inspect "$course_root/artifact"
```

In `verify`, conditionally upload only `${{ github.workspace }}/${{ inputs.course_path }}/artifact/site` with `actions/upload-pages-artifact@7b1f4a764d45c48632c6b24a0339c27f5614fb0b` when the caller event is a default-branch push. The separate `deploy` job needs `verify`, has the same condition, has only `pages: write` and `id-token: write`, targets `environment: {name: github-pages, url: ${{ steps.deployment.outputs.page_url }}}`, and runs `actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e`.

- [ ] **Step 4: Verify and commit**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_reusable_course_pages_workflow.py
./scripts/check.sh
git add .github/workflows/reusable-course-pages.yml tests/contracts/test_reusable_course_pages_workflow.py
git commit -m "Add reusable course Pages workflow"
```

Expected: focused test and host archive gate pass.

### Task 2: Merge and capture immutable framework SHA

**Files:** GitHub pull request and default branch only.

**Interfaces:** Consumes Task 1 checked commit; produces full merged `FRAMEWORK_SHA` used only as the caller's reusable-workflow reference.

- [ ] **Step 1: Push and open pull request**

```bash
git push -u origin chore/domain-publishing
gh pr create --repo raya-lucaria/raya-lucaria.github.io --base new_rayalucaria --head chore/domain-publishing --title "Add reusable course Pages workflow" --body "Adds pinned reusable course verification and deployment."
gh pr checks --repo raya-lucaria/raya-lucaria.github.io --watch
```

Expected: all required checks pass.

- [ ] **Step 2: Merge and print the immutable revision**

```bash
gh pr merge --repo raya-lucaria/raya-lucaria.github.io --merge --delete-branch
git fetch origin new_rayalucaria
git rev-parse origin/new_rayalucaria
```

Expected: the last command prints the exact 40-character `FRAMEWORK_SHA` containing the workflow.

### Task 3: Document the optional GitHub adapter and course-origin boundary

**Files:**
- Create: `docs/guides/en/contributors/publishing-courses.md`
- Create: `docs/guides/es/colaboradores/publicar-cursos.md`

**Interfaces:** Consumes the accepted GitHub Pages workflow design; produces portable operational guidance without making GitHub a framework dependency.

- [ ] **Step 1: Write the English and Spanish guides**

Document GitHub Actions/Pages as optional CI/static-hosting/TLS adapters; source/artifact ownership; GitHub Pages public-hosting limits and plan dependency; migration by building the same `artifact/site` for another host; local/self-hosted serving with `raya build` plus a standard static file server; that `artifact/` is rebuildable/non-canonical; and the `rayalucaria.org` shared-origin rule forbidding authenticated cookies/tokens and requiring protected default branches.

- [ ] **Step 2: Link guides from language indexes and verify**

Add each guide to its language index, then run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate docs
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build docs
```

Expected: the rendered documentation course validates and builds.

### Task 4: Create and prove the empty IA course with the real CLI

**Files:**
- Create: external `ia_o26/raya.yaml`, `ia_o26/course/0_index.md`, source support directories, `.gitignore`.

**Interfaces:** Consumes the framework CLI; produces valid portable course source.

- [ ] **Step 1: Run the real CLI in a new external directory**

```bash
course_workspace=$(mktemp -d)
course_root="$course_workspace/ia_o26"
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya course init "$course_root" --course-id ia_o26 --title "Inteligencia Artificial — Otoño 2026 (ITAM)" --description "Curso de Inteligencia Artificial del ITAM, Otoño 2026." --language es
```

Expected: `Course scaffold created` and valid `source: course` layout.

- [ ] **Step 2: Add output exclusions and prove the lifecycle**

Create `.gitignore` containing:

```gitignore
artifact/
.venv/
.venv-local/
```

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate "$course_root"
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build "$course_root"
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya artifacts inspect "$course_root/artifact"
python3 -m http.server 8765 --directory "$course_root/artifact/site" >/tmp/ia_o26_static_server.log 2>&1 &
static_server_pid=$!
curl --fail http://127.0.0.1:8765/
kill "$static_server_pid"
rm -rf "$course_root/artifact"
gh repo create raya-lucaria/ia_o26 --public --description "Inteligencia Artificial — Otoño 2026 (ITAM)"
git init -b main "$course_root"
git -C "$course_root" add raya.yaml course .gitignore
git -C "$course_root" commit -m "Initialize IA O26 course"
git -C "$course_root" remote add origin https://github.com/raya-lucaria/ia_o26.git
git -C "$course_root" push -u origin main
```

Expected: all Raya commands exit 0; generated artifact is absent before Git commit.

### Task 5: Create `ia_o26` and configure independent pinned CI/CD

**Files:**
- Create: `raya-lucaria/ia_o26/.github/workflows/pages.yml`
- Create: public GitHub repository `raya-lucaria/ia_o26`.

**Interfaces:** Consumes Task 2 exact `FRAMEWORK_SHA` and Task 4 source; produces independent GitHub Pages deployment.

- [ ] **Step 1: Clone the independently owned source repository**

```bash
caller_workspace=$(mktemp -d)
course_root="$caller_workspace/ia_o26"
git clone https://github.com/raya-lucaria/ia_o26.git "$course_root"
```

- [ ] **Step 2: Protect course release authority before adding deploy code**

In `raya-lucaria/ia_o26` Settings, require pull requests and at least one approving review for `main`, disallow force pushes, and restrict direct pushes to trusted course maintainers. In Settings → Environments, configure `github-pages` to allow deployments only from `main`. These controls are required because all project sites share the public `rayalucaria.org` origin.

- [ ] **Step 3: Add thin immutable caller**

Before pushing this workflow, set `ia_o26` Settings → Pages source to GitHub Actions and configure its `github-pages` environment to permit only `main`. Create `.github/workflows/pages.yml` using this exact shape, substituting the Task 2 full SHA for `FRAMEWORK_SHA`:

```yaml
name: Verify and publish course
on:
  push:
  pull_request:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: pages
  cancel-in-progress: true
jobs:
  course-pages:
    uses: raya-lucaria/raya-lucaria.github.io/.github/workflows/reusable-course-pages.yml@FRAMEWORK_SHA
    with:
      course_path: .
```

Commit and push. The reusable workflow is the sole default-branch deployment gate.

- [ ] **Step 4: Verify deployment**

Watch `Verify and publish course` to success. Verify its default Pages URL, then after custom-domain DNS activation verify `https://rayalucaria.org/ia_o26/`. Confirm `artifact/` is not Git-tracked.

## Self-Review

- Spec coverage: Task 1 centralizes CLI mechanics and tests the workflow contract; Task 2 emits the immutable version; Task 3 proves the real CLI outside the framework checkout; Task 4 creates the independent repository and deploys it.
- Placeholder scan: the only dynamic value is produced explicitly by Task 2 before Task 4 uses it.
- Consistency: the caller has one immutable `FRAMEWORK_SHA`; the reusable workflow checks out its own defining SHA; only the caller default branch deploys.
