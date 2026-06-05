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
- `data/runtime.json`
- `data/execution.json`
- `data/cache.json`
- `assets/`
- `files/`

`site/` is the browser static read path. Local assets referenced by rendered
HTML are copied under `site/_raya/assets/` and linked with deployment-neutral
relative URLs. `manifest.json`, `data/*.json`, and artifact-level `assets/`
remain artifact-root surfaces for inspection, agents, and future installations.

This package renders rich static Markdown and copies referenced code/notebook
files for reading, but it does not execute scripts, notebooks, `uv`, Docker,
kernels, package installers, or cache refreshes. Local execution belongs to the
explicit `raya run` CLI path and writes generated execution results under the
artifact root.
