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

The reusable workflow owns toolchain setup, CLI invocation, validation, build,
inspection, artifact upload, and deployment. The course workflow owns only its
triggers, concurrency group, explicit `course_path: .` input, and the pinned
framework SHA. It must never contain Namecheap, Cloudflare, or custom-domain
credentials.

## Versioning

Course workflows use an exact full commit SHA from
`raya-lucaria/raya-lucaria.github.io`, not a branch. This is immutable and
auditable. A later framework release tag may replace the SHA once the project
adopts a release process; tags must be signed/protected before becoming the
default consumer reference.

Updating a course to a newer framework version is a visible one-line pull
request that updates the pinned SHA and reruns the verification workflow.

## Permissions and Events

The course caller workflow grants `contents: read`, `pages: write`, and
`id-token: write`. The reusable workflow validates/builds for `pull_request`
and `push`; it deploys only when the caller event is a `push` to the caller
repository's default branch. Pull requests must never publish course material.

Course Pages visibility is public. The GitHub organization root custom domain
supplies the eventual `rayalucaria.org/ia_o26/` path; `ia_o26` does not set a
custom domain of its own.

## Error Handling and Verification

- A malformed course fails at `raya validate` before build/deploy.
- A build or artifact-contract failure fails the workflow and never uploads a
  Pages artifact.
- The scaffold is created by the actual `raya course init` command, then
  validated, built, and inspected locally before it is committed.
- The framework adds workflow-fixture tests proving the reusable workflow runs
  validation/build/inspection and distinguishes pull-request verification from
  default-branch deployment.
- After `ia_o26` deploys, verification covers both its default Pages URL and
  `https://rayalucaria.org/ia_o26/`, including relative static links.

## Scope

This change creates only `ia_o26`. `fdd_o26` reuses the same workflow in a
separate later change after the first independent course deployment is proven.
No course content, custom frontend, backend service, dynamic identity, or
domain-provider automation is included.
