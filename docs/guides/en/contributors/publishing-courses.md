---
id: docs-guides-en-contributors-publishing-courses
title: Publishing Independent Courses
nav_title: Publishing Courses
summary: Publish a course as portable static output while preserving course-team ownership.
status: ready
---
# Publishing Independent Courses

GitHub Actions and GitHub Pages are optional adapters for continuous integration,
static hosting, and TLS. They do not change Raya's course contract or make GitHub
the owner of a course. A course team owns its canonical source, review policy,
and publication decision; GitHub stores workflow logs and serves uploaded public
generated artifacts.

## Build first, then choose a host

`artifact/` is rebuildable output, never canonical source. A portable release is
always produced with the normal lifecycle:

```bash
raya validate .
raya build .
raya artifacts inspect artifact
```

The publishable static read path is `artifact/site/`. To migrate to another
provider, build the same course and upload that directory to the new static host.
For local or self-hosted review, serve it with any ordinary static-file server:

```bash
raya build .
python3 -m http.server 8000 --directory artifact/site
```

Provider quotas, retention, availability, supported features, and pricing are
external and may change. Keep course source in its own repository and do not
commit `artifact/`; that keeps migration and recovery independent of a provider.

## GitHub Pages adapter

For a course in the `raya-lucaria` organization, use the framework reusable
workflow by a full commit SHA. The caller stays small and owns only its triggers
and release authority:

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
    uses: raya-lucaria/raya-lucaria.github.io/.github/workflows/reusable-course-pages.yml@FULL_FRAMEWORK_SHA
    with:
      course_path: .
```

Replace `FULL_FRAMEWORK_SHA` only through a reviewed pull request. Do not use a
branch or tag. The reusable workflow validates, builds, inspects, and uploads
only `artifact/site/`. It verifies pull requests but deploys only a push to the
course default branch.

Set the repository Pages source to GitHub Actions before the first deployment.
Protect the default branch and the `github-pages` environment before adding the
caller workflow. Limit deployment authority to trusted course maintainers.

## Shared-origin boundary

Organization project sites are served beneath `rayalucaria.org`, for example
`https://rayalucaria.org/ia_o26/`. They therefore share one public web origin.
Treat anyone who can publish a protected course branch as trusted with that
origin. Require review on default branches, disallow force pushes, and do not
host applications using authenticated cookies, browser tokens, or credentials on
this domain. Course sites remain static public material.
