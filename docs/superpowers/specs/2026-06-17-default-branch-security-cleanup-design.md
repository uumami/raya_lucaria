# Default Branch Security Cleanup Design

## Purpose

GitHub reported 40 Dependabot vulnerabilities after the latest push to
`new_rayalucaria`. Local investigation shows the current branch is not the
source of those alerts. The active reset branch has a small root
`package.json` for build-time MathJax rendering, and `npm audit --json` reports
zero vulnerabilities for that dependency tree.

The alerts are attached to legacy Eleventy manifests on the repository default
branch `main`: `src/eleventy/package.json` and
`src/eleventy/package-lock.json`. That renderer stack is already absent from
`new_rayalucaria` and is not part of the current Glintstone static renderer
baseline.

This loop should close the security gap by retiring the stale default-branch
surface, not by upgrading or reviving the abandoned Eleventy stack.

## Evidence

The current branch state is:

- `new_rayalucaria` is synced to `origin/new_rayalucaria`;
- `origin/new_rayalucaria` has no tracked `src/eleventy/` files;
- root `npm audit --json` reports zero vulnerabilities;
- root `package.json` depends only on `@mathjax/src` plus the current
  `@xmldom/xmldom` override;
- GitHub Dependabot open alerts all reference `src/eleventy/package.json` or
  `src/eleventy/package-lock.json`;
- GitHub reports `main` as the repository default branch.

The open alert distribution observed during brainstorming was:

- 38 alerts for `src/eleventy/package-lock.json`;
- 2 alerts for `src/eleventy/package.json`;
- severity mix: 4 critical, 18 high, 16 medium, 2 low.

## Recommended Approach

Treat `new_rayalucaria` as the intended replacement baseline and move the
repository default/security surface to that branch when the team is ready.
That is the cleanest fix because it removes the vulnerable legacy renderer tree
from the branch GitHub evaluates by default.

The implementation should not patch `src/eleventy` dependency versions inside
`new_rayalucaria`. That directory is intentionally gone from the reset branch,
and upgrading it would reintroduce a non-canonical renderer surface.

## Alternative Approaches

### Upgrade Legacy Eleventy On `main`

This would update vulnerable packages in `src/eleventy/package.json` and
`src/eleventy/package-lock.json` on `main`.

Trade-off: it may close Dependabot alerts, but it spends engineering effort on
a renderer stack the reset explicitly abandoned. It also risks implying
Eleventy remains a supported architecture.

### Delete Only `src/eleventy` From `main`

This would create a cleanup change directly against `main` that removes the
legacy renderer files while leaving the rest of `main` in place.

Trade-off: it is narrower than switching the default branch, but it leaves two
branch baselines with different authority surfaces. That can confuse humans,
agents, GitHub alerts, and future cleanup work.

### Replace `main` With `new_rayalucaria`

This makes the reset branch the default baseline and lets GitHub evaluate the
current repository shape.

Trade-off: it is the most coherent long-term fix, but it should be done
deliberately because it changes the repository's default branch surface. Before
that change, the branch must stay verified and pushed, and any branch-protection
or deployment expectations tied to `main` must be checked.

## Design

The cleanup path has two phases.

First, keep `new_rayalucaria` as the canonical working branch and verify that it
does not contain the vulnerable legacy manifests. This phase is already
supported by local evidence: `npm audit` is clean and
`git ls-tree -r origin/new_rayalucaria` has no `src/eleventy/` entries.

Second, retire the default-branch legacy surface. The preferred operation is to
make `new_rayalucaria` the repository default branch or otherwise merge/replace
`main` with the reset baseline through the repository's accepted GitHub
workflow. After the default surface changes, rerun GitHub Dependabot alert
inspection and confirm no open alerts remain for `src/eleventy`.

If repository settings or branch protections make an immediate default-branch
switch unsafe, the fallback is a targeted cleanup branch against `main` that
removes `src/eleventy/` and any stale Eleventy-specific workflow/docs that are
still visible on `main`. That fallback should be treated as transitional, not
as a revival of `main` as the canonical baseline.

## Documentation Impact

This design does not require immediate edits to user-facing role docs. The
current `new_rayalucaria` guidance already rejects stale Eleventy assumptions
outside the domain-language reset boundary and describes the current
MathJax-backed static renderer.

If the implementation changes GitHub branch defaults or adds a temporary
default-branch cleanup process, update repository-maintenance guidance in the
smallest relevant surface. Do not add Eleventy troubleshooting or dependency
upgrade guidance to current role docs.

## Testing And Verification

The implementation should verify the current branch and the GitHub alert source
before changing branch/default state:

- `git status --short --branch`;
- `npm audit --json`;
- `git ls-tree -r origin/new_rayalucaria | rg '^src/eleventy/' || true`;
- `gh api 'repos/uumami/raya_lucaria/dependabot/alerts?state=open&per_page=100'`
  filtered by manifest path;
- `scripts/check-hygiene.sh`;
- `./scripts/check.sh`;
- `./scripts/check-docker.sh` sequentially if any repository files change.

After the default surface changes, rerun the Dependabot alert query. The
success condition is that open alerts no longer point at `src/eleventy` on the
active default branch.

## Non-Goals

This loop should not:

- reintroduce `src/eleventy`;
- upgrade abandoned Eleventy dependencies as a supported path;
- change current MathJax rendering behavior;
- add browser-side MathJax;
- add external renderer or CDN requests;
- move generated artifacts into source control;
- use OpenSpec artifacts for this loop.
