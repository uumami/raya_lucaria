---
id: docs-guides-es-agentes
title: Agentes
summary: Guia para agentes que trabajan mediante archivos, comandos, specs y diagnosticos.
status: ready
---
# Agentes

Los agentes operan mediante archivos, comandos, specs OpenSpec, diagnosticos y limites de autoridad explicitos. Los agentes heredan la autoridad del usuario y no reciben confianza especial.

Usa `docs/foundation/13_truth_surfaces.md` para el mapa de autoridad, specs OpenSpec aceptadas para contratos testeables y `AGENTS.md` para el flujo del repositorio.

Usa los check scripts canonicos de `README.md` y `AGENTS.md`: `./scripts/check.sh` para el gate host, `./scripts/check-docker.sh` para verificacion Python/Raya en el contenedor de referencia, y `./scripts/smoke-test.sh` para checks de portabilidad de cursos externos. Evita editar outputs generados, carpetas de dependencias, caches o output de sesiones locales. Mantiene capacidades diferidas en `docs/foundation/18_known_missing_work.md` hasta que un cambio OpenSpec aceptado las vuelva actuales.

Para contenido de curso, trata los archivos source como canonicos y los artifacts generados como reconstruibles. Preserva `source: course`, el arbol ordenado `course/`, `id` en frontmatter, links `raya:<id>`, privacidad de `_official/` y `_assets/` colocados, markers de indice generado y superficies de datos declaradas en manifest. No edites `artifact/` generado como source truth.

Para rich static rendering, preserva el limite de Glintstone: reescribe links mediante reglas Raya, genera anchors locales y tablas de contenido desde headings de source, pre-renderiza math MathJax aceptada durante build, mantiene archivos de soporte bajo `site/_raya/`, escapa raw HTML y no ejecutes bloques de codigo. Testea HTML generado, static read paths, math visible en browser, assets locales de math, ausencia de requests externos del renderer y overflow en desktop/mobile.

Para referencias de codigo y notebooks, clasifica archivos `.py` y `.ipynb` linkeados por extension y por pertenencia al quantum propio o a un ancestro aceptado. Trata nombres como `scripts/`, `labs/`, `code/` y `notebooks/` como elecciones ordinarias de autoria, bloquea referencias privadas o cross-quantum, copia solo archivos linkeados y validados a superficies de artifact y de browser, actualiza `references.json`, y nunca infieras ejecucion desde previews.

Para runtime metadata, trata `runtime/profiles.yaml`, `pyproject.toml` y `uv.lock` en la raiz como soporte source fuera del orden de aprendizaje. Valida y emite metadata de runtime, execution plan y cache, pero nunca llames `uv`, Docker, kernels, package installers, notebooks, scripts ni cache refreshes salvo que un contrato de ejecucion aceptado posterior lo diga explicitamente.

Para ejecucion local, usa `raya run <course> <target>` solo cuando la tarea pida explicitamente ejecutar un target. Prefiere `--dry-run` para inspeccionar el plan primero. Trata `artifact/data/execution-results.json`, `artifact/logs/`, `artifact/execution/` y `artifact/cache/results/` como output generado; no los edites ni los promociones como source truth.

Para reviewed execution output, trata `_reviewed/execution/<target>/` como soporte source controlado que requiere revision humana. Usa `raya outputs list <course>` para inspeccionar estado generado y revisado sin ejecucion. Usa `raya outputs freeze <course> <target>` solo para copiar un resultado generado exitoso y current hacia `_reviewed/`; no trates freeze como aprobacion institucional. `policy: frozen` valida metadata y archivos revisados, y no debe llamar `uv`, Docker, kernels, scripts, notebooks, package installers ni cache refreshes.

Para superficies renderizadas, no hagas scraping de HTML normal como autoridad y no pongas internals verbosos en paginas default. Usa `manifest.json`, `data/*.json`, archivos copiados y paginas estaticas `_raya/inspect/` para hashes, cache keys, rutas source, rutas de artifact, detalles de runtime y metadata de freshness de reviewed output.

Para preview renderizado, usa `raya preview <course> --dry-run` para inspeccionar el plan o `raya preview <course>` para servir el sitio estatico generado. Preview no ejecuta: puede validar, construir y servir `artifact/site/`, pero no debe llamar `raya run`, `raya outputs freeze`, Docker execution, kernels, package installers, scripts, notebooks, runtime profiles ni cache refreshes. Cambios de superficie renderizada necesitan static-read-path y checks visuales/layout.

Para documentacion del repositorio, `docs/raya.yaml` renderiza los docs actuales mediante `docs/render-content/`. Edita `docs/foundation/` y `docs/guides/` como source legible, actualiza el arbol ordenado de render cuando se agrega o reordena una pagina renderizada, y usa `raya validate docs` mas `raya build docs` antes de depender del artifact estatico de docs.

Cuando actualices documentacion, manten separadas las paginas de rol en ingles y espanol. Conserva identificadores tecnicos en ingles como `raya`, `raya.yaml`, `source`, `course/`, `_official/`, `_assets/`, `artifact/`, `packages/static` y `OpenSpec`.
