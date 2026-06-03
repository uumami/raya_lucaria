# raya-static

`raya-static` owns the first Glintstone builder implementation.

It turns a validated source course into a portable artifact with:

- `site/`
- `manifest.json`
- `data/pages.json`
- `data/quanta.json`
- `data/links.json`
- `data/official.json`
- `assets/`

This package does not define a rich renderer, frontend stack, backend service,
identity provider, search engine, graph UI, or personal study state. Those
belong to later proposals after the artifact contract is stable.
