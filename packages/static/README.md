# raya-static

`raya-static` owns the first Glintstone builder implementation.

It turns a validated source course into a portable artifact with:

- `site/`
- `site/_raya/assets/`
- `manifest.json`
- `data/pages.json`
- `data/quanta.json`
- `data/links.json`
- `data/navigation.json`
- `data/indices.json`
- `data/official.json`
- `data/references.json`
- `data/reviewed-outputs.json`
- `data/runtime.json`
- `data/execution.json`
- `data/cache.json`
- `assets/`
- `files/`
- `reviewed/`

`site/` is the browser static read path. Local assets referenced by rendered
HTML are copied under `site/_raya/assets/` and linked with deployment-neutral
relative URLs. Reviewed output files are copied under `site/_raya/reviewed/`
and linked with deployment-neutral relative URLs. `manifest.json`,
`data/*.json`, artifact-level `assets/`, `files/`, and `reviewed/` remain
artifact-root surfaces for inspection, agents, and future installations.

This package renders rich static Markdown and copies validated linked
code/notebook files for reading. It also renders compact reviewed-output panels from current
`_reviewed/` source support. It does not execute scripts, notebooks, `uv`,
Docker, kernels, package installers, or cache refreshes. Local execution belongs
to the explicit `raya run` CLI path and writes generated execution results under
the artifact root.
