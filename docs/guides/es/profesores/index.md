---
id: docs-guides-es-profesores
title: Profesores
summary: Guia para poseer source de curso, material oficial, revision y publicacion.
status: ready
---
# Profesores

Los equipos de curso poseen el source del curso, el material oficial, la revision y las decisiones de publicacion. Empieza con `docs/foundation/05_course_contract.md`, `docs/foundation/04_ownership_permissions.md` y `docs/foundation/03_pedagogy.md`.

Los ejemplos son fixtures salvo que un equipo de curso los acepte explicitamente como material de curso. Cards, quizzes, prompts, ejemplos, tareas, examenes y proyectos oficiales deben seguir distinguiendose de material personal, compartido y generado.

El source del curso usa `source: course` y orden visible dentro de `course/`: `0_index.md`, `1_foundations/`, `2_practice/` y `A_reference/`. Escribe las introducciones manuales en `0_index.md`; Glintstone renderiza indices de hijos y conteos de estudio desde summaries y objetos oficiales sin sobrescribir el source. Pon objetos oficiales de aprendizaje bajo `_official/` junto al tema que apoyan, y assets locales del tema bajo `_assets/`. Usa `id` estable en frontmatter y links `raya:<id>` para referencias que deben sobrevivir renumeracion o movimientos.

Las paginas de curso pueden usar el baseline rich static aceptado: tablas, math, codigo mostrado, callouts, footnotes, heading anchors y tablas de contenido generadas por pagina. Los bloques de codigo solo se muestran en esta fase, raw HTML se escapa y los archivos de soporte renderizados se generan bajo `artifact/site/_raya/`.

Las paginas de curso tambien pueden linkear scripts en directorios `code/` colocados junto al tema y notebooks en directorios `notebooks/` colocados junto al tema. Esos archivos se validan, se copian para lectura y descarga, y se previsualizan estaticamente; no se ejecutan durante el build. Usa esto para trabajo de soporte transparente, no para contenido de pagina escondido ni objetos oficiales de aprendizaje.

Los cursos pueden declarar runtime metadata con `pyproject.toml`, `uv.lock` y `runtime/profiles.yaml` en la raiz. Esto ayuda a que futura ejecucion local o con Docker sea reproducible, pero el build actual solo registra perfiles, policies y cache keys; no ejecuta codigo, instala paquetes, refresca caches ni confia en outputs de notebooks.

Las specs OpenSpec describen contratos aceptados. La documentacion de rol explica como trabajar con esos contratos, pero no tiene mas autoridad que foundation docs ni specs aceptadas.

La documentacion renderizada del repositorio es guia, no canon de curso. Se construye desde `docs/raya.yaml` y permanece separada del material de clase y de los artifacts oficiales de curso.
