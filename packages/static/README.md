# raya-static

`raya-static` owns the first Glintstone builder implementation.

It turns a validated source course into a portable artifact with:

- `site/`
- `site/_raya/assets/`
- `manifest.json`
- `data/pages.json`
- `data/quanta.json`
- `data/links.json`
- `data/official.json`
- `assets/`

`site/` is the browser static read path. Local assets referenced by rendered
HTML are copied under `site/_raya/assets/` and linked with deployment-neutral
relative URLs. `manifest.json`, `data/*.json`, and artifact-level `assets/`
remain artifact-root surfaces for inspection, agents, and future installations.

This package does not define a rich renderer, frontend stack, backend service,
identity provider, search engine, graph UI, math renderer, backlink UI,
wikilink support, heading-anchor validation, external link policy, or personal
study state. Those belong to later proposals after the artifact contract is
stable.
