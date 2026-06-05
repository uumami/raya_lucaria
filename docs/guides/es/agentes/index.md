---
id: docs-guides-es-agentes
title: Agentes
summary: Guia para agentes que trabajan mediante archivos, comandos, specs y diagnosticos.
status: ready
---
# Agentes

Los agentes operan mediante archivos, comandos, specs OpenSpec, diagnosticos y limites de autoridad explicitos. Los agentes heredan la autoridad del usuario y no reciben confianza especial.

Usa `docs/foundation/13_truth_surfaces.md` para el mapa de autoridad, specs OpenSpec aceptadas para contratos testeables y `AGENTS.md` para el flujo del repositorio.

Para contenido de curso, trata los archivos source como canonicos y los artifacts generados como reconstruibles. Preserva `source: course`, el arbol ordenado `course/`, `id` en frontmatter, links `raya:<id>`, privacidad de `_official/` y `_assets/` colocados, markers de indice generado y superficies de datos declaradas en manifest. No edites `artifact/` generado como source truth.

Para rich static rendering, preserva el limite de Glintstone: reescribe links mediante reglas Raya, genera anchors locales y tablas de contenido desde headings de source, mantiene archivos de soporte bajo `site/_raya/`, escapa raw HTML y no ejecutes bloques de codigo. Testea HTML generado y static read paths en vez de depender de un browser framework.

Para referencias de codigo y notebooks, trata `code/` y `notebooks/` como soporte source privado poseido por el quantum de aprendizaje mas cercano. Valida links antes del build, bloquea referencias privadas o cross-quantum, copia archivos referenciados a superficies de artifact y de browser, actualiza `references.json`, y nunca infieras ejecucion desde previews.

Para runtime metadata, trata `runtime/profiles.yaml`, `pyproject.toml` y `uv.lock` en la raiz como soporte source fuera del orden de aprendizaje. Valida y emite metadata de runtime, execution plan y cache, pero nunca llames `uv`, Docker, kernels, package installers, notebooks, scripts ni cache refreshes salvo que un contrato de ejecucion aceptado posterior lo diga explicitamente.

Para ejecucion local, usa `raya run <course> <target>` solo cuando la tarea pida explicitamente ejecutar un target. Prefiere `--dry-run` para inspeccionar el plan primero. Trata `artifact/data/execution-results.json`, `artifact/logs/`, `artifact/execution/` y `artifact/cache/results/` como output generado; no los edites ni los promociones como source truth.

Para documentacion del repositorio, `docs/raya.yaml` renderiza los docs actuales mediante `docs/render-content/`. Edita `docs/foundation/` y `docs/guides/` como source legible, actualiza el arbol ordenado de render cuando se agrega o reordena una pagina renderizada, y usa `raya validate docs` mas `raya build docs` antes de depender del artifact estatico de docs.

Cuando actualices documentacion, manten separadas las paginas de rol en ingles y espanol. Conserva identificadores tecnicos en ingles como `raya`, `raya.yaml`, `source`, `course/`, `_official/`, `_assets/`, `artifact/`, `packages/static` y `OpenSpec`.
