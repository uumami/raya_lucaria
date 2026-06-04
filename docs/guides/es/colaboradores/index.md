---
id: docs-guides-es-colaboradores
title: Colaboradores
summary: Guia para cambiar codigo, contratos, docs y tests con seguridad.
status: ready
---
# Colaboradores

Empieza con `docs/foundation/15_system_overview.md`, despues `docs/foundation/13_truth_surfaces.md`, y despues las specs OpenSpec aceptadas para la capacidad que estas cambiando.

Usa los comandos Docker Compose y `uv` de `README.md` y `AGENTS.md` cuando cambies codigo, contratos, docs o tests. Mantiene rutas de paquetes, comandos, campos de schema e IDs estables en ingles.

Cuando cambies validacion o rendering de cursos, preserva el modelo convention-first: `source: course` apunta al arbol ordenado `course/`, los nombres ordenados definen el orden de autoria, `id` en frontmatter define identidad estable, `_official/` y `_assets/` colocados permanecen privados, y `navigation.json` junto con `indices.json` son datos generados del artifact. Los tests deben cubrir diagnosticos de source, export de objetos oficiales, copia de assets, schemas de artifact y rendering static-read-path.

La documentacion actual tambien es un curso de docs renderizable. Edita las paginas legibles en `docs/foundation/` y `docs/guides/`, manten alineado `docs/render-content/` para el orden renderizado, y trata `docs/artifact/` como output generado e ignorado. Usa `raya validate docs`, `raya build docs` y tests static-read-path cuando cambies el rendering de documentacion.

Para cambios sustanciales, declara el impacto de documentacion para colaboradores, profesores, estudiantes y agentes. Si cambia la documentacion de rol, manten separadas las paginas en ingles y espanol.
