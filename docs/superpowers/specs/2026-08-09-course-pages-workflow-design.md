---
title: Independent Course Pages Workflow Design
date: 2026-08-09
status: approved
---

# Independent Course Pages Workflow Design

## Decision

The framework repository will publish one reusable GitHub Actions workflow for
Raya course validation, build, inspection, and GitHub Pages deployment. Course
repositories call that workflow by immutable framework commit SHA.

The first consumer is public repository `raya-lucaria/ia_o26`. It is an empty,
valid Spanish course scaffold with this metadata:

```yaml
course_id: ia_o26
title: "Inteligencia Artificial — Otoño 2026 (ITAM)"
language: "es"
source: course
artifact: artifact
```

It will publish at `https://rayalucaria.org/ia_o26/` after the root custom
domain is active. Its GitHub Pages deployment remains independently owned by
the course repository.

## Workflow Boundary

```text
course pull request/default branch
        |
        v
course workflow: pinned reusable framework workflow
        |
        +--> checkout caller course source
        +--> checkout pinned framework toolchain
        +--> raya validate .
        +--> raya build .
        +--> raya artifacts inspect artifact
        |
        +--> pull request: stop after verification
        +--> default branch: upload artifact/site and deploy Pages
```

The framework owns a versioned reusable implementation adapter: toolchain
setup, CLI invocation, validation, build, inspection, and the standard Pages
artifact/deployment steps. The course repository owns release policy and
authorization: branch protection, reviewer access, Pages environment rules,
visibility, triggers, concurrency, and whether it invokes that adapter. It
must never contain Namecheap, Cloudflare, or custom-domain credentials.

## Versioning

Course workflows use an exact full commit SHA from
`raya-lucaria/raya-lucaria.github.io`, not a branch. This is immutable and
auditable. The reusable workflow checks out its co-located framework source at
the platform-supplied `job.workflow_repository` and `job.workflow_sha`, so
there is no caller-controlled second toolchain reference. A later framework
release tag may replace the SHA once the project adopts a release process; tags
must be signed/protected before becoming the default consumer reference.

Updating a course to a newer framework version is a visible one-line pull
request that updates the pinned SHA and reruns the verification workflow.

## Permissions and Events

The course caller grants the maximum permissions required by the called
workflow: `contents: read`, `pages: write`, and `id-token: write`. The reusable
verify job explicitly narrows itself to `contents: read`, so untrusted pull
request source cannot receive a Pages write token or OIDC token. Only the
protected deployment job receives `pages: write` and `id-token: write`. The
workflow validates/builds for `pull_request` and `push`; it uploads/deploys
only when the caller event is a `push` whose full ref equals
`refs/heads/<default branch>`. Pull requests and tags must never publish course
material.

Course Pages visibility is public. The GitHub organization root custom domain
supplies the eventual `rayalucaria.org/ia_o26/` path; `ia_o26` does not set a
custom domain of its own. Project sites share the `rayalucaria.org` web origin:
default branches therefore require review protection, course maintainers are
trusted with that shared public origin, and this domain must never host a
cookie- or token-bearing authenticated application.

## Error Handling and Verification

- A malformed course fails at `raya validate` before build/deploy.
- A build or artifact-contract failure fails the workflow and never uploads a
  Pages artifact.
- The read-only verify job uploads only `${course_root}/artifact/site`, after
  validation/build/inspection, and only for a default-branch push. The
  deployment job consumes that Pages artifact through the `github-pages`
  environment; it does not rebuild or read source files.
- The scaffold is created by the actual `raya course init` command, then
  validated, built, and inspected locally before it is committed.
- The framework adds workflow-contract tests proving job permissions, action
  SHA pinning, toolchain identity, `artifact/site` upload placement, and the
  pull-request/default-branch boundary. It also proves the artifact through a
  neutral local static read path mounted under a non-root prefix before
  adapter-level Pages verification. That proof retrieves the course root,
  inspection page, and a generated local CSS/JavaScript resource.
- After `ia_o26` deploys, verification covers both its default Pages URL and
  `https://rayalucaria.org/ia_o26/`, including relative static links.

## Provider Adapter Documentation

GitHub Actions and GitHub Pages are optional managed-provider adapters, not a
Raya contract. Contributor documentation must state that GitHub supplies CI,
workflow logs, uploaded/deployed public artifacts, static hosting, and TLS;
that its plan limits and pricing are external and changeable; that canonical
course source remains course-team owned while generated artifacts are
rebuildable; that migration is `raya build` followed by uploading the same
static read path to another host; and that the local/self-hosted equivalent is
`raya build` plus a standard static file server. The guide must also state the
shared-origin trust boundary above.

## Scope

This change creates only `ia_o26`. `fdd_o26` reuses the same workflow in a
separate later change after the first independent course deployment is proven.
No course content, custom frontend, backend service, dynamic identity, or
domain-provider automation is included.
