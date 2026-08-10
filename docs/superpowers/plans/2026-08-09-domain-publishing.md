# Raya Lucaria Domain Publishing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the framework at `https://rayalucaria.org/` and let each Raya Lucaria course repository publish its own static artifact at `https://rayalucaria.org/<course_id>/`.

**Architecture:** A GitHub organization owns the public repository namespace. Its organization Pages repository hosts the framework root and carries the verified custom domain; each project repository retains its own GitHub Pages deployment and inherits that domain as a path. Namecheap is the registrar, Cloudflare is DNS-only authoritative DNS, and GitHub Pages serves static content and TLS.

**Tech Stack:** GitHub organization and GitHub Pages, GitHub Actions, Namecheap, Cloudflare DNS/DNSSEC, Raya CLI static artifacts.

## Global Constraints

- `docs/foundation/` remains the highest authority; deployment must preserve course source/artifact ownership.
- Attach `rayalucaria.org` only to the organization Pages repository; course repositories must not set individual custom domains.
- Course repository names are durable public course IDs, including `ia_o26`.
- Use DNS-only Cloudflare records for GitHub Pages; do not use wildcard DNS or a Cloudflare Worker.
- Do not place Namecheap, Cloudflare, or domain-management credentials in any repository or GitHub Actions secret.
- Require two-factor authentication for organization members and keep two owners where practical.

---

## File Structure

| Path | Responsibility |
| --- | --- |
| `docs/superpowers/specs/2026-08-09-domain-publishing-design.md` | Approved architecture and operating constraints. |
| `.github/workflows/deploy.yml` | Existing framework workflow that builds `docs/artifact/site` and deploys the organization Pages root. |
| `docs/guides/en/`, `docs/guides/es/` | Future course-publishing instructions, added with the first real course. |

### Task 1: Establish secure provider ownership

**Files:** No repository files.

**Interfaces:** Consumes Namecheap ownership and GitHub user `uumami`. Produces a secure `raya-lucaria` organization and an undelegated Cloudflare zone.

- [x] **Step 1: Create the GitHub organization**

The `raya-lucaria` organization already exists at `https://github.com/raya-lucaria` and `uumami` is an owner. Do not create a second organization.

- [ ] **Step 2: Secure the organization**

In organization Settings → Authentication security, require two-factor authentication. In People, add a second trusted owner if one is available; otherwise record that a second owner is required before course-team collaborators are invited.

- [ ] **Step 3: Add the domain to Cloudflare without changing DNS**

In Cloudflare, add the `rayalucaria.org` zone using the Free plan. Copy every existing Namecheap DNS record into Cloudflare’s import/review screen. Record the two assigned Cloudflare nameservers; do not change Namecheap nameservers yet.

- [ ] **Step 4: Protect the registrar account**

At Namecheap, enable auto-renewal, registrar lock, and two-factor authentication. Confirm the recovery email is not an address under `rayalucaria.org`.

- [ ] **Step 5: Verify the prerequisite state**

Confirm the GitHub organization exists, Cloudflare reports the zone is awaiting nameserver delegation, and Namecheap still lists its current nameservers. No public request should be affected yet.

### Task 2: Move the framework repository into the organization Pages role

**Files:**
- Modify: GitHub repository ownership and name; no source-file change expected.
- Verify: `.github/workflows/deploy.yml`.

**Interfaces:** Consumes the new organization and `uumami/raya_lucaria`. Produces `raya-lucaria/raya-lucaria.github.io`, the organization Pages repository.

- [x] **Step 1: Inspect the workflow and repository**

Run:

```bash
gh repo view uumami/raya_lucaria --json nameWithOwner,defaultBranchRef,isPrivate,url
sed -n '1,140p' .github/workflows/deploy.yml
```

Expected: the repository is public and the existing workflow deploys `docs/artifact/site` with GitHub Pages actions.

- [x] **Step 2: Transfer the repository**

Run with the authenticated `uumami` GitHub CLI session:

```bash
gh repo transfer uumami/raya_lucaria raya-lucaria
```

After GitHub confirms the transfer, run:

```bash
git remote set-url origin https://github.com/raya-lucaria/raya_lucaria.git
git fetch origin --prune
```

- [x] **Step 3: Rename it into the organization Pages repository**

In GitHub repository Settings → General → Repository name, rename `raya_lucaria` to `raya-lucaria.github.io`. Then run:

```bash
git remote set-url origin https://github.com/raya-lucaria/raya-lucaria.github.io.git
git ls-remote --exit-code origin HEAD
gh repo view raya-lucaria/raya-lucaria.github.io --json nameWithOwner,url,isPrivate
```

Expected: the remote resolves and GitHub reports a public `raya-lucaria/raya-lucaria.github.io` repository.

- [x] **Step 4: Enable and verify root Pages deployment**

In repository Settings → Pages, select GitHub Actions as source. Manually run `Deploy Docs to GitHub Pages`; wait for success. Open `https://raya-lucaria.github.io/` in a private browser window and confirm documentation navigation and static assets load.

### Task 3: Verify ownership and delegate DNS

**Files:** No repository files.

**Interfaces:** Consumes the live organization root and Cloudflare nameservers. Produces GitHub-verified domain ownership and Cloudflare authoritative DNS.

- [ ] **Step 1: Verify the domain in GitHub first**

In GitHub organization Settings → Pages, start verification for `rayalucaria.org`. GitHub supplies a TXT host/value. Create that exact DNS-only TXT record in Cloudflare, then continue verification until GitHub reports verified.

- [ ] **Step 2: Delegate at Namecheap**

In Namecheap Domain List → Manage → Nameservers, choose Custom DNS and enter exactly Cloudflare’s two assigned nameservers. Save. Do not delete the Cloudflare zone or alter copied records.

- [ ] **Step 3: Activate DNSSEC after delegation**

Wait until Cloudflare shows the zone as Active. Enable DNSSEC in Cloudflare, then enter Cloudflare’s DS values in Namecheap’s DNSSEC configuration for `rayalucaria.org`.

- [ ] **Step 4: Confirm delegation**

Run:

```bash
dig NS rayalucaria.org +short
```

Expected: the query returns the two Cloudflare nameservers. Confirm the GitHub verification TXT record at the exact host GitHub supplied.

### Task 4: Bind the root domain to GitHub Pages

**Files:** Cloudflare DNS and GitHub Pages settings only.

**Interfaces:** Consumes verified domain, active Cloudflare zone, and live root Pages site. Produces HTTPS service at `rayalucaria.org` with canonical `www` redirect behavior.

- [ ] **Step 1: Add GitHub Pages records in Cloudflare**

Create DNS-only apex `A` records for `@` with `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, and `185.199.111.153`. Create a DNS-only `CNAME` record for `www` pointing to `raya-lucaria.github.io`. Preserve the GitHub verification TXT record.

- [ ] **Step 2: Set the GitHub Pages custom domain**

In `raya-lucaria/raya-lucaria.github.io` Settings → Pages, set Custom domain to `rayalucaria.org`. Wait until GitHub reports DNS is correct, then enable Enforce HTTPS.

- [ ] **Step 3: Verify root traffic**

Run:

```bash
curl -I https://rayalucaria.org/
curl -I https://www.rayalucaria.org/
```

Expected: apex returns `200`; `www` redirects to apex through HTTPS. Confirm in a private browser window that the certificate is valid.

- [ ] **Step 4: Record rollback data**

Privately save prior Namecheap nameservers, Cloudflare DNS export, the successful Pages run URL, and the domain-verification date. If the root Pages site is disabled, remove or reassign its custom domain/DNS records immediately.

### Task 5: Prove independent course publishing before creating `ia_o26`

**Files:**
- Create then delete: public `raya-lucaria/pages-path-probe` repository.

**Interfaces:** Consumes the root custom domain. Produces evidence that project repositories publish independently beneath the domain path.

- [ ] **Step 1: Create and deploy a disposable Pages project**

Create public repository `raya-lucaria/pages-path-probe` with an `index.html` that contains `Raya Lucaria Pages path probe` and a standard GitHub Actions Pages deployment workflow. The workflow uploads its repository root and has only `contents: read`, `pages: write`, and `id-token: write` permissions. Do not configure a custom domain in this repository.

- [ ] **Step 2: Verify both project paths**

After its workflow succeeds, run:

```bash
curl --fail --location https://raya-lucaria.github.io/pages-path-probe/
curl --fail --location https://rayalucaria.org/pages-path-probe/
```

Expected: both responses contain `Raya Lucaria Pages path probe`.

- [ ] **Step 3: Delete the probe**

Record the successful URLs and deployment run, then delete `raya-lucaria/pages-path-probe`. Confirm that `https://rayalucaria.org/pages-path-probe/` no longer serves. This avoids reserving a misleading course ID.

### Task 6: Establish the real course convention when `ia_o26` is ready

**Files:**
- Create later: `raya-lucaria/ia_o26/.github/workflows/deploy.yml`, `raya.yaml`, and course tree.
- Modify later: relevant English and Spanish professor/contributor guides.

**Interfaces:** Consumes verified project-path behavior. Produces a self-owned course artifact at `https://rayalucaria.org/ia_o26/`.

- [ ] **Step 1: Create the course repository**

Create public `raya-lucaria/ia_o26` only when its course source is ready. Keep the repository name exactly `ia_o26`: it is the stable learner-facing path.

- [ ] **Step 2: Add the self-contained Pages workflow**

Use `raya validate` and `raya build` in the course repository, then upload that course’s `artifact/site` to GitHub Pages. Use only `contents: read`, `pages: write`, and `id-token: write` permissions; no domain-provider credentials.

- [ ] **Step 3: Verify the real course**

Open `https://rayalucaria.org/ia_o26/` in a private browser window. Verify its landing page, navigation, images, local MathJax resources when applicable, inspection pages, and deployment-neutral relative links.

- [ ] **Step 4: Document the repeating workflow**

Add concise English and Spanish role-guide instructions: course teams release through their own Pages workflows, and the framework repository never copies, rehosts, or approves generated course artifacts.

## Self-Review

- Spec coverage: Tasks 1–4 cover provider ownership, security, verification, DNS, root hosting, TLS, and rollback. Task 5 proves inherited project paths. Task 6 preserves course repository ownership.
- Placeholder scan: no `TBD`, `TODO`, or unspecified technical procedure remains; provider-generated nameservers and verification tokens are explicitly obtained at the required dashboard step.
- Consistency: `raya-lucaria/raya-lucaria.github.io` is the root repository, `rayalucaria.org` is the root host, and project repositories retain self-owned deployment at `/<course_id>/`.
