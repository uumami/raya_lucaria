# raya-cli

Python CLI for the first Raya Lucaria operational surface.

Baseline commands:

- `raya --help`
- `raya doctor`
- `raya validate <course>`
- `raya build <course>`
- `raya run <course> <target>`
- `raya course init <path>`
- `raya artifacts inspect <artifact>`

`raya run` is explicit local execution. It requires one target, supports `--dry-run`, `--refresh`, and `--docker`, and writes generated execution data under the artifact root. Validation, build, artifact inspection, and static serving remain non-executing.

The CLI orchestrates contracts and diagnostics. It does not own renderer internals, backend services, or pedagogy algorithms.
