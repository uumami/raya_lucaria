# Independent Course Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide a pinned reusable GitHub Pages workflow that proves the Raya CLI can build an independently owned Spanish `ia_o26` course repository and publish its static artifact.

**Architecture:** The framework owns a reusable workflow that checks out the caller course and immutable framework revision, then validates, builds, inspects, and conditionally deploys. `ia_o26` contains only CLI-generated source and a thin workflow pinned to that same framework SHA.

**Tech Stack:** GitHub Actions reusable workflows, GitHub Pages, Python 3.10, Node 22, uv, Raya CLI, pytest.

## Global Constraints

- Course source uses `source: course`; generated `artifact/` is ignored.
- The caller uses an exact full framework commit SHA, never a branch or mutable tag.
- `framework_ref` is identical to the reusable-workflow SHA.
- Pull requests verify only; only default-branch pushes deploy.
- Workflows use `contents: read`, `pages: write`, and `id-token: write` only.
- `ia_o26` is public, Spanish, and titled `Inteligencia Artificial — Otoño 2026 (ITAM)`.

---

## File Structure

| Path | Responsibility |
| --- | --- |
| `.github/workflows/reusable-course-pages.yml` | Framework reusable verification and Pages deployment. |
| `tests/contracts/test_reusable_course_pages_workflow.py` | Static workflow contract test. |
| `ia_o26/raya.yaml` | CLI-generated course identity. |
| `ia_o26/course/0_index.md` | Replaceable Spanish course root. |
| `ia_o26/.github/workflows/pages.yml` | Thin caller workflow. |

### Task 1: Add and test reusable course workflow

**Files:**
- Create: `tests/contracts/test_reusable_course_pages_workflow.py`
- Create: `.github/workflows/reusable-course-pages.yml`

**Interfaces:** Consumes `course_path` and `framework_ref`; produces validated, built, inspected course artifacts and a default-branch-only Pages deployment.

- [ ] **Step 1: Write the failing workflow contract test**

Create a test that reads `.github/workflows/reusable-course-pages.yml` and asserts it includes `on.workflow_call`, `course_path`, `framework_ref`, checkout of `raya-lucaria/raya-lucaria.github.io` at `${{ inputs.framework_ref }}`, `uv run raya validate`, `uv run raya build`, `uv run raya artifacts inspect`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`, and a deployment condition containing both `github.event_name == 'push'` and `github.event.repository.default_branch == github.ref_name`.

- [ ] **Step 2: Prove the test fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_reusable_course_pages_workflow.py
```

Expected: failure because the reusable workflow does not exist.

- [ ] **Step 3: Implement the reusable workflow**

Create a `workflow_call` workflow with `course_path` and `framework_ref` string inputs. Its verify job checks out the caller source, then checks out `raya-lucaria/raya-lucaria.github.io` to `.raya-framework` at `${{ inputs.framework_ref }}`, sets up Node 22, Python 3.10, and uv, runs `npm ci` plus `uv sync --python 3.10 --all-packages --dev` in `.raya-framework`, and executes:

```bash
course_root="${GITHUB_WORKSPACE}/${{ inputs.course_path }}"
uv run --directory .raya-framework raya validate "$course_root"
uv run --directory .raya-framework raya build "$course_root"
uv run --directory .raya-framework raya artifacts inspect "$course_root/artifact"
```

The deploy job needs verify, uses only Pages permissions, is guarded by the two expressions from Step 1, uploads `$course_root/artifact/site`, and deploys with `actions/deploy-pages@v4`.

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

**Interfaces:** Consumes Task 1 checked commit; produces full merged `FRAMEWORK_SHA` used by `ia_o26`.

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

### Task 3: Create and prove the empty IA course with the real CLI

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
rm -rf "$course_root/artifact"
gh repo create raya-lucaria/ia_o26 --public --description "Inteligencia Artificial — Otoño 2026 (ITAM)"
git init -b main "$course_root"
git -C "$course_root" add raya.yaml course .gitignore
git -C "$course_root" commit -m "Initialize IA O26 course"
git -C "$course_root" remote add origin https://github.com/raya-lucaria/ia_o26.git
git -C "$course_root" push -u origin main
```

Expected: all Raya commands exit 0; generated artifact is absent before Git commit.

### Task 4: Create `ia_o26` and configure independent pinned CI/CD

**Files:**
- Create: `raya-lucaria/ia_o26/.github/workflows/pages.yml`
- Create: public GitHub repository `raya-lucaria/ia_o26`.

**Interfaces:** Consumes Task 2 exact `FRAMEWORK_SHA` and Task 3 source; produces independent GitHub Pages deployment.

- [ ] **Step 1: Clone the independently owned source repository**

```bash
caller_workspace=$(mktemp -d)
course_root="$caller_workspace/ia_o26"
git clone https://github.com/raya-lucaria/ia_o26.git "$course_root"
```

- [ ] **Step 2: Add thin immutable caller**

Create `.github/workflows/pages.yml` using this exact shape, substituting the Task 2 full SHA for both occurrences of `FRAMEWORK_SHA`:

```yaml
name: Verify and publish course
on:
  push:
    branches: [main]
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
      framework_ref: FRAMEWORK_SHA
```

Commit, push, then set `ia_o26` Settings → Pages source to GitHub Actions.

- [ ] **Step 3: Verify deployment**

Watch `Verify and publish course` to success. Verify its default Pages URL, then after custom-domain DNS activation verify `https://rayalucaria.org/ia_o26/`. Confirm `artifact/` is not Git-tracked.

## Self-Review

- Spec coverage: Task 1 centralizes CLI mechanics and tests the workflow contract; Task 2 emits the immutable version; Task 3 proves the real CLI outside the framework checkout; Task 4 creates the independent repository and deploys it.
- Placeholder scan: the only dynamic value is produced explicitly by Task 2 before Task 4 uses it.
- Consistency: the exact `FRAMEWORK_SHA` is both the reusable workflow reference and the toolchain checkout ref; only `main` pushes deploy in `ia_o26`.
