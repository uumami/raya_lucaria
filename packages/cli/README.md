# raya-cli

Python CLI for the first Raya Lucaria operational surface.

Baseline commands:

- `raya --help`
- `raya doctor`
- `raya validate <course>`
- `raya build <course>`
- `raya preview <course>`
- `raya run <course> <target>`
- `raya outputs list <course>`
- `raya outputs freeze <course> <target>`
- `raya course init <path>`
- `raya artifacts inspect <artifact>`

`raya run` is explicit local execution. It requires one target, supports `--dry-run`, `--refresh`, and `--docker`, and writes generated execution data under the artifact root. `policy: frozen` validates reviewed source support and never executes.

`raya preview` validates and builds an explicit course, serves generated `artifact/site/`, and reports the student entrypoint plus `_raya/inspect/` URL when present. `--dry-run` prints the validate/build/serve plan without starting a server. Preview is a static review workflow, not a dynamic app.

`raya outputs list` and `raya outputs freeze` are non-executing reviewed-output commands. `list` reports generated/reviewed/frozen state. `freeze` copies a current successful generated result into colocated `_reviewed/` source support for human review and commit.

Validation, build, preview, artifact inspection, output listing, output freezing, and static serving remain non-executing.

The CLI orchestrates contracts and diagnostics. It does not own renderer internals, backend services, or pedagogy algorithms.
