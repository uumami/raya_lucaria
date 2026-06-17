# Default Branch Security Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move GitHub's default/security evaluation surface away from legacy `main` Eleventy files and onto verified `new_rayalucaria`.

**Architecture:** This is an operations-focused cleanup. The current branch remains the source of truth; implementation verifies that `new_rayalucaria` has no legacy `src/eleventy` surface, pushes the plan commit, changes the GitHub default branch, and confirms Dependabot alerts no longer point at the abandoned renderer stack. If GitHub refuses the default-branch change, the fallback is a separate cleanup branch against `main` that removes `src/eleventy/`.

**Tech Stack:** Git, GitHub CLI/API, npm audit, Raya verification scripts, Superpowers workflow.

---

## File Structure

- Modify: `docs/superpowers/plans/2026-06-17-default-branch-security-cleanup.md`
  - This implementation plan and checklist.
- No production source files should be modified in the primary path.
- No `src/eleventy` files should be created, restored, edited, or upgraded.
- Possible fallback only: a separate cleanup branch based on `main` may delete `src/eleventy/` if default-branch switching is blocked.

## Task 1: Baseline Safety Checks

**Files:**
- No file changes.

- [ ] **Step 1: Confirm branch and clean status**

Run:

```bash
git status --short --branch
git branch --show-current
git rev-parse --short HEAD
```

Expected:

```text
## new_rayalucaria...origin/new_rayalucaria [ahead 2]
new_rayalucaria
```

The third command should print the current 7-character commit SHA.
If status shows modified or untracked files other than this plan before it is
committed, stop and inspect before continuing.

- [ ] **Step 2: Confirm default branch and permissions**

Run:

```bash
gh api repos/uumami/raya_lucaria --jq '{default_branch, permissions}'
gh api repos/uumami/raya_lucaria/branches/main --jq '{name, protected}'
gh api repos/uumami/raya_lucaria/branches/new_rayalucaria --jq '{name, protected}'
```

Expected:

```text
default_branch is main.
permissions.admin is true or permissions.maintain is true.
main protected is false.
new_rayalucaria protected is false.
```

If `permissions.admin` or `permissions.maintain` is not true, stop and report
that the default-branch change needs a repository administrator.

- [ ] **Step 3: Confirm alert root cause**

Run:

```bash
npm audit --json
git ls-tree -r origin/new_rayalucaria | rg '^src/eleventy/' || true
gh api 'repos/uumami/raya_lucaria/dependabot/alerts?state=open&per_page=100' \
  --jq 'group_by(.dependency.manifest_path)[] | {manifest: .[0].dependency.manifest_path, count: length}'
```

For the `git ls-tree` command, expected output is empty. For `npm audit`, the
JSON metadata should report zero vulnerabilities. For the GitHub alert query,
open alerts should be grouped under `src/eleventy/package.json` and/or
`src/eleventy/package-lock.json` before the default branch is changed.

- [ ] **Step 4: Commit this plan**

Run:

```bash
git add docs/superpowers/plans/2026-06-17-default-branch-security-cleanup.md
git commit -m "Plan default branch security cleanup implementation"
```

Expected:

```text
[new_rayalucaria COMMIT_SHA] Plan default branch security cleanup implementation
```

## Task 2: Verify And Push `new_rayalucaria`

**Files:**
- No file changes.

- [ ] **Step 1: Run focused hygiene and dependency checks**

Run:

```bash
scripts/check-hygiene.sh
npm audit --json
git ls-tree -r origin/new_rayalucaria | rg '^src/eleventy/' || true
```

Expected:

```text
hygiene: passed
```

The `npm audit` JSON should report zero vulnerabilities. The `git ls-tree`
command should produce no `src/eleventy` output.

- [ ] **Step 2: Push the planning commits**

Run:

```bash
git push origin new_rayalucaria
```

Expected:

```text
new_rayalucaria -> new_rayalucaria
```

GitHub may still print vulnerability notices at this point because `main` is
still the default branch. Treat that notice as pre-change evidence, not as a
failure of the current branch.

- [ ] **Step 3: Confirm branch is synced**

Run:

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/new_rayalucaria
```

Expected:

```text
## new_rayalucaria...origin/new_rayalucaria
```

The two `git rev-parse` commands must print identical full commit SHAs.

## Task 3: Change GitHub Default Branch

**Files:**
- No file changes.

- [ ] **Step 1: Change the default branch to `new_rayalucaria`**

Run:

```bash
gh api repos/uumami/raya_lucaria \
  --method PATCH \
  --field default_branch=new_rayalucaria \
  --jq '{default_branch}'
```

Expected:

```json
{"default_branch":"new_rayalucaria"}
```

If GitHub rejects the request, do not retry blindly. Capture the exact error
and use Task 5 fallback planning.

- [ ] **Step 2: Confirm remote HEAD follows the new default**

Run:

```bash
git remote set-head origin -a
git ls-remote --symref origin HEAD
gh api repos/uumami/raya_lucaria --jq '{default_branch}'
```

Expected:

```text
origin/HEAD set to new_rayalucaria
ref: refs/heads/new_rayalucaria	HEAD
{"default_branch":"new_rayalucaria"}
```

## Task 4: Post-Change Security Verification

**Files:**
- No file changes.

- [ ] **Step 1: Re-query Dependabot alerts**

Run:

```bash
gh api 'repos/uumami/raya_lucaria/dependabot/alerts?state=open&per_page=100' \
  --jq '[.[] | select(.dependency.manifest_path | startswith("src/eleventy/"))] | length'
```

Expected:

```text
0
```

If GitHub still reports `src/eleventy` alerts immediately after switching the
default branch, wait briefly and rerun once:

```bash
sleep 20
gh api 'repos/uumami/raya_lucaria/dependabot/alerts?state=open&per_page=100' \
  --jq '[.[] | select(.dependency.manifest_path | startswith("src/eleventy/"))] | length'
```

If the count remains nonzero, record the count and alert manifest paths in the
final report. Do not mark them resolved by assumption.

- [ ] **Step 2: Verify current branch dependency and hygiene state**

Run:

```bash
npm audit --json
scripts/check-hygiene.sh
git status --short --branch
```

Expected:

```text
hygiene: passed
## new_rayalucaria...origin/new_rayalucaria
```

The `npm audit` JSON should report zero vulnerabilities.

- [ ] **Step 3: Decide whether full gates are required**

If only GitHub repository settings changed after the last full verification,
full `./scripts/check.sh` and `./scripts/check-docker.sh` do not need to be
rerun. If any repository file changed after Task 2, run:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected:

```text
check: passed
check-docker: passed
```

These commands must be sequential, not concurrent.

## Task 5: Fallback If Default-Branch Change Is Blocked

**Files:**
- No primary-path file changes.
- Fallback branch only: delete `src/eleventy/` from a branch based on `main`.

- [ ] **Step 1: Capture the blocker**

Run:

```bash
gh api repos/uumami/raya_lucaria --jq '{default_branch, permissions}'
```

Expected: output showing why the default branch did not change, alongside the
exact error captured from Task 3 Step 1.

- [ ] **Step 2: Create a separate cleanup branch from `main`**

Run only if Task 3 is blocked:

```bash
git fetch origin main
git switch -c cleanup-retire-eleventy origin/main
git rm -r src/eleventy
git commit -m "Remove legacy Eleventy renderer"
git push origin cleanup-retire-eleventy
```

Expected:

```text
[cleanup-retire-eleventy COMMIT_SHA] Remove legacy Eleventy renderer
cleanup-retire-eleventy -> cleanup-retire-eleventy
```

Do not run this fallback if Task 3 succeeds.

## Task 6: Final Review And Report

**Files:**
- No file changes.

- [ ] **Step 1: Request final review**

Dispatch a code/repository reviewer with:

```text
Review the default-branch security cleanup. Verify that no src/eleventy files
were reintroduced to new_rayalucaria, that GitHub default_branch now points to
new_rayalucaria or that fallback cleanup is clearly documented, and that local
npm audit plus hygiene checks passed.
```

Expected: reviewer returns no Critical or Important findings. Address any valid
finding before final reporting.

- [ ] **Step 2: Final status report**

Report:

```text
default_branch: value from `gh api repos/uumami/raya_lucaria --jq .default_branch`
new_rayalucaria synced: yes only if local HEAD equals origin/new_rayalucaria
src/eleventy alerts remaining: integer from the Dependabot filtered query
npm audit vulnerabilities: integer from npm audit metadata.vulnerabilities.total
hygiene: passed only if `scripts/check-hygiene.sh` exits 0
full gates rerun: yes or no, with the reason
```

If GitHub still shows alerts after the default branch changes, state that the
repository source is clean and GitHub alert refresh is pending; include the
exact remaining alert count from the API.
