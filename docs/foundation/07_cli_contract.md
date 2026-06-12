---
id: docs-cli-contract
title: CLI Contract
summary: Stable command surface for humans and coding agents.
status: ready
---
# CLI Contract

The CLI is the stable operational interface for humans and coding agents. It should be boring, explicit, scriptable, and safe.

## Roles

The CLI operates in three contexts:

```text
framework repo     course repo       installation repo
source packages    course source     deployment config
templates          raya.yaml         installation.yaml
docs/specs         course/           registered courses
```

Unknown contexts should produce diagnostics, not guesses.

## First Commands

The first implementation should support the smallest useful loop:

```text
raya --help
raya doctor
raya validate <course>
raya build <course>
raya preview <course>
raya run <course> <target>
raya outputs list <course>
raya outputs freeze <course> <target>
raya artifacts inspect <artifact>
```

Next commands:

```text
raya course init
raya installation init
raya specs validate
```

Later commands:

```text
raya deploy
raya register
raya sync
raya upgrade
raya export
raya backup
```

## First Build Loop

```text
course source
     |
     v
raya validate
     |
     v
raya build
     |
     v
course artifact
```

The CLI may call package-owned behavior, but it should not own pedagogy, rendering internals, auth, study algorithms, or provider logic.

## Preview Command

`raya preview <course>` is the accepted local review path for generated static pages. It validates and builds the explicit source course, serves `artifact/site/` through a local static server, and prints the artifact path, student entrypoint URL, and `_raya/inspect/` URL when present.

Preview must stay static. It must not run `raya run`, `raya outputs freeze`, Docker execution, kernels, package installers, scripts, notebooks, runtime profiles, or cache refreshes. Use `--dry-run` to print the validate/build/serve plan and resolved paths without starting the server.

## Execution Commands

Execution commands are explicit and target-scoped:

- `raya run <course> <target>` may execute one validated target through the selected runtime profile.
- `raya run --dry-run` reports command shape without execution.
- `raya outputs list <course>` reports generated and reviewed output state without execution.
- `raya outputs freeze <course> <target>` copies a current successful generated result into `_reviewed/` source support without execution.
- `raya artifacts inspect <artifact>` reads manifest-declared artifact data without rebuilding or executing.

No command except `raya run` may run scripts, notebooks, kernels, `uv`, Docker, package installers, or cache refreshes. `raya preview` may validate, build, and serve static files, but it remains non-executing. `policy: frozen` validates current reviewed output and never executes.

## Diagnostics

Commands must:

- print concrete next actions,
- exit nonzero on failure,
- avoid hidden global state,
- identify detected context,
- identify files read and outputs written,
- remain usable by coding agents.

Machine-readable output can be added later, but human-readable diagnostics come first.

## Installation

The initial developer path should be simple:

```bash
python -m pip install -e packages/cli
raya --help
```

Future user paths may include `pipx`, release artifacts, or operating-system packages. The CLI must not require a hosted service.
