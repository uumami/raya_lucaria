---
title: Raya Lucaria Domain and Static Publishing Design
date: 2026-08-09
status: approved
---

# Raya Lucaria Domain and Static Publishing Design

## Decision

`rayalucaria.org` will use GitHub Pages as its initial static host. Namecheap
remains the registrar. Cloudflare provides authoritative DNS and DNSSEC, but
does not proxy the GitHub Pages origin.

The public GitHub namespace will be a `rayalucaria` organization. The existing
framework repository will move into that organization and become
`rayalucaria/rayalucaria.github.io`, the organization Pages repository. It
serves the framework's main public surface at `https://rayalucaria.org/`.

Each course remains an independently owned source repository under the same
organization. A course repository such as `rayalucaria/ia_o26` builds and
deploys its own static Raya artifact through its own GitHub Actions workflow.
GitHub Pages serves it at `https://rayalucaria.org/ia_o26/` without a per-course
custom domain, DNS entry, central artifact store, or routing proxy.

## Rationale

This preserves the foundation's source/artifact ownership boundary: course
teams own portable source and publish their own public read-only artifacts.
The domain is a stable discovery boundary, not a central hosting application.

GitHub Pages organization-site custom domains automatically apply to project
sites owned by that organization. This supplies the desired path routing while
keeping deployment infrastructure small and avoiding a Cloudflare Worker,
per-course custom hosts, or an aggregation repository.

## Public URL Contract

| Surface | GitHub repository | Public URL |
| --- | --- | --- |
| Framework home and documentation | `rayalucaria/rayalucaria.github.io` | `https://rayalucaria.org/` |
| AI course, autumn 2026 | `rayalucaria/ia_o26` | `https://rayalucaria.org/ia_o26/` |
| Future course `<course_id>` | `rayalucaria/<course_id>` | `https://rayalucaria.org/<course_id>/` |

Repository names used for course publication are durable public course IDs.
Course pages must use deployment-neutral relative links so they work at their
project-site path, local preview, and another future static host.

## Operations and Security

- Enable automatic renewal and registrar lock at Namecheap; maintain a
  recovery contact outside the domain mailbox.
- Delegate nameservers to Cloudflare only after inventorying any existing DNS
  records. Enable DNSSEC after the delegation is healthy.
- Configure the GitHub Pages apex and `www` DNS records in Cloudflare as
  DNS-only records. GitHub Pages owns TLS for this static origin.
- Verify `rayalucaria.org` in the GitHub organization before assigning it to
  Pages. Do not use wildcard DNS records.
- Make `rayalucaria.org` the GitHub Pages custom domain only for the
  organization Pages repository. Course repositories must not set their own
  custom domains.
- Require two-factor authentication for organization members. Keep at least
  two organization owners where practical, and grant course teams only the
  repository access they need.
- Each course workflow uses GitHub's built-in Pages permissions only. No
  Namecheap, Cloudflare, or domain-management credential belongs in a course
  repository.

## Failure Handling and Verification

- Before DNS changes, verify the domain on GitHub and record all existing
  Namecheap DNS records.
- After delegation, confirm the apex and `www` DNS records resolve to GitHub
  Pages; enable HTTPS only after GitHub reports the certificate ready.
- Publish the framework root first and verify `https://rayalucaria.org/` and
  its `www` redirect in a private browser window.
- Create a disposable public test project in the organization to verify the
  inherited path model before creating the real `ia_o26` course repository.
  Confirm both its project URL and its custom-domain path return the same
  artifact with working relative navigation.
- A disabled Pages site with live DNS is a takeover risk. If a site is removed,
  remove or reassign its DNS/custom-domain configuration immediately.

## Non-Goals

- No dynamic backend, authentication service, Cloudflare Worker, or central
  course-artifact aggregation is part of this rollout.
- No DNS wildcard routing or per-course custom domains.
- No Cloudflare API or Namecheap API credentials are needed for initial setup.
