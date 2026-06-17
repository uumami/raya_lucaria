# Repo Hygiene And Verification Hardening Design

## Purpose

Raya's current repository hygiene gate already rejects tracked generated output
and common untracked generated paths. The last verification loop exposed a
separate reliability problem: running host and Docker gates at the same time can
make both paths execute `npm ci` against the same mounted `node_modules/`
directory. That can leave the local MathJax install partially removed and make
later renderer checks fail for environmental reasons.

This loop should make cleanup and verification self-enforcing. The repository
should stay clean on GitHub, generated files should remain local and ignored,
and verification scripts should fail clearly instead of corrupting shared
dependency state.

## Scope

The cleanup scope is repository hygiene and verification workflow only:

- keep generated artifacts, dependency folders, local virtual environments,
  caches, render-debug reports, and screenshots out of Git;
- remove unwanted tracked generated files from Git if any are discovered;
- strengthen hygiene checks so future generated/debug files are caught before
  commit or push;
- prevent host and Docker verification from racing over shared dependency
  installation;
- document the safe verification order for contributors, collaborators, and
  coding agents.

This loop should not redesign package boundaries, renderer behavior, course
contracts, or the skin/profile system.

## Current Findings

The current branch has no tracked generated paths matching the existing hygiene
patterns. Local ignored outputs do exist, including `node_modules/`,
`.venv-local/`, `.pytest_cache/`, `.ruff_cache/`, Python `__pycache__/`
directories, and generated `artifact/` directories. Those are normal local
working files and should remain untracked.

The existing `.gitignore` already covers the main dependency, cache, and
artifact directories. The existing `scripts/check-hygiene.sh` rejects tracked
and visible untracked generated paths. The missing guard is concurrency:
`scripts/check.sh` and `scripts/check-docker.sh` both reach
`scripts/check-python.sh`, and `check-python.sh` runs `npm ci`.

## Verification Lock

Add a small repository-local verification lock around the dependency-mutating
part of `scripts/check-python.sh`. The lock should protect at least:

- `npm ci --ignore-scripts --no-audit --no-fund`;
- `npm run raya-render-math -- --self-test`;
- the subsequent `uv sync` when it writes the configured local environment.

Fail-fast behavior is preferred for agent workflows. If another verification is
already running, the script should exit nonzero with a concrete message:

```text
Another Raya verification is preparing dependencies.
Wait for it to finish, then rerun this command.
```

The lock must be cleaned up automatically when the process exits. It should not
require a daemon, external service, or global machine state. If the platform has
`flock`, use it; otherwise use an atomic directory lock with clear stale-lock
guidance.

## Hygiene Rules

Keep `.gitignore` and `scripts/check-hygiene.sh` aligned. Hygiene should reject
source pollution from:

- generated course and docs artifacts such as `artifact/`, `site/`, and
  `_site/`;
- dependency folders such as `node_modules/` and local Python environments;
- Python and tool caches;
- render-debug output directories and files such as `report.json`,
  `summary.json`, `index.html` beside screenshots, and desktop/mobile PNG
  captures when they appear in debug-output locations;
- logs and coverage outputs.

Rules should stay conservative. They should not reject authored course assets,
fixtures, source screenshots committed intentionally for documentation, or files
whose names only resemble generated output outside generated/debug directories.

If a generated file is already tracked, remove it from Git with
`git rm --cached` unless the file is an intentional source fixture. Do not
delete a user's local working copy unless cleanup explicitly requires it.

## Documentation

Update current guidance surfaces that tell humans and agents how to verify:

- `README.md`;
- `AGENTS.md`;
- English contributor and agent guides;
- Spanish collaborator and agent guides.

The guidance should state that `./scripts/check.sh` and
`./scripts/check-docker.sh` must be run sequentially because both prepare local
dependencies through `scripts/check-python.sh`. If the lock trips, the next
action is to wait for the active verification process to finish and rerun the
command.

## Testing And Verification

Implementation should include focused tests or shell checks for the new lock and
hygiene behavior where practical. At minimum, verification should run:

- `scripts/check-hygiene.sh`;
- focused tests or scripted checks for lock behavior;
- `./scripts/check.sh`;
- `./scripts/check-docker.sh` sequentially, not concurrently.

The final report should clearly distinguish any environmental failure from a
code failure. A prior concurrent-run failure does not count as final evidence.

## Non-Goals

This loop should not:

- rewrite the Docker Compose topology;
- introduce a separate package manager;
- make generated artifacts canonical source;
- add new renderer features;
- change course authoring contracts;
- change MathJax rendering behavior beyond protecting its dependency
  preparation path.
