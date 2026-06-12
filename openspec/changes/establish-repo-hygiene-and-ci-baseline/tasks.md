## 1. Tests

- [ ] 1.1 Add contract tests for canonical check script help output, hygiene stale-guidance detection, and generated-output pollution detection.
- [ ] 1.2 Run the focused hygiene script tests and keep failures visible until the scripts exist.
- [x] 1.3 Add regression coverage for `scripts/check-docker.sh` Docker user default and override behavior.

## 2. Check Scripts

- [x] 2.1 Implement `scripts/check-hygiene.sh` for stale guidance, generated-output pollution, OpenSpec incomplete markers, fixture labeling, and command/source-layout drift scans.
- [x] 2.2 Implement `scripts/check-python.sh` for Python/Raya dependency sync, tests, fixture validation/build/inspection, and docs validation/build/inspection.
- [x] 2.3 Implement `scripts/check.sh` as the canonical host full check.
- [x] 2.4 Implement `scripts/check-docker.sh` as the Docker Compose verification path.
- [x] 2.5 Default `scripts/check-docker.sh` to the caller UID:GID while preserving explicit `RAYA_DOCKER_USER` overrides.

## 3. CI

- [x] 3.1 Add a CI workflow that installs accepted tools and calls repository check scripts.
- [x] 3.2 Document any CI Docker limitation if the accepted Docker verification path cannot run in CI.

## 4. Current Guidance

- [ ] 4.1 Clean stale current guidance in `README.md`, `AGENTS.md`, foundation docs, rendered docs, and OpenSpec config so commands and source layout agree with accepted contracts.
- [ ] 4.2 Add a known-missing-work document for deferred features and intentional gaps.
- [ ] 4.3 Update English and Spanish contributor and agent role guides for canonical checks, generated-output handling, and deferred work.
- [ ] 4.4 Update `.gitignore` and generated-output ignore rules so artifacts, static output, caches, dependency folders, and local session output do not appear as source changes.

## 5. Verification And Archive

- [ ] 5.1 Run local host verification with `./scripts/check.sh`.
- [ ] 5.2 Run Docker verification with `./scripts/check-docker.sh`.
- [ ] 5.3 Validate the active change and current specs with OpenSpec strict validation.
- [ ] 5.4 Archive the accepted change after implementation and sync delta specs into current specs.
