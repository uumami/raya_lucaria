---
id: docs-guides-es-colaboradores
title: Colaboradores
summary: Guia para cambiar codigo, contratos, docs y tests con seguridad.
status: ready
---
# Colaboradores

Empieza con `docs/foundation/15_system_overview.md`, despues `docs/foundation/13_truth_surfaces.md`, y despues las specs OpenSpec aceptadas para la capacidad que estas cambiando.

Usa los comandos Docker Compose y `uv` de `README.md` y `AGENTS.md` cuando cambies codigo, contratos, docs o tests. Ejecuta `./scripts/check.sh` antes de archivar o commitear, ejecuta `./scripts/check-docker.sh` cuando cambie comportamiento Docker, y conserva `./scripts/smoke-test.sh` para smoke checks de cursos externos cuando cambie la portabilidad de comandos o cursos. Mantiene capacidades diferidas en `docs/foundation/18_known_missing_work.md` hasta que un cambio OpenSpec aceptado las vuelva actuales. Mantiene rutas de paquetes, comandos, campos de schema e IDs estables en ingles.

Cuando cambies validacion o rendering de cursos, preserva el modelo convention-first: `source: course` apunta al arbol ordenado `course/`, los nombres ordenados definen el orden de autoria, `id` en frontmatter define identidad estable, `_official/` y `_assets/` colocados permanecen privados, y `navigation.json` junto con `indices.json` son datos generados del artifact. Los tests deben cubrir diagnosticos de source, export de objetos oficiales, copia de assets, schemas de artifact y rendering static-read-path.

El rich static rendering pertenece a Glintstone. Mantiene parser, highlighter y MathJax detras de `packages/static`; los contratos de source deben describir comportamiento de autoria, no detalles internos de librerias. La math aceptada usa math inline con delimitadores de dolar, bloques display con delimitadores de doble dolar en lineas propias, macros locales por pagina, recursos locales bajo `site/_raya/render/math/`, diagnosticos estrictos y ninguna dependencia de renderer solo en browser. Cambios de renderer necesitan fixtures representativos, diagnosticos invalidos cuando aplique, tests de contrato, tests e2e/static-read-path, checks Chromium de math visible/sin requests externos, checks de overflow desktop/mobile y actualizaciones de documentacion de rol.

Usa `examples/courses/render-fixture/course/2_math_authoring/0_index.md` cuando cambies rendering de math o guia de autoria. Es el fixture target para ejemplos validos actuales: `\begin{bmatrix}`, macros de vectores, `\newcommand`, `\renewcommand`, notacion de conjuntos y logica, normas, productos internos, derivaciones alineadas, notacion de optimizacion y Markdown de objetos numerados. Mantiene ejemplos invalidos de math en tests para que docs de profesores y estudiantes sigan siendo copiables.

El soporte de objetos numerados es comportamiento actual del renderer. Preserva el modelo de configuracion `render.numbered_objects` para numbering, sequences y families; valida fenced directives, IDs estables de objeto, referencias shorthand `@id` y referencias explicitas `raya:ref/id`; y emite el index `data/numbered-objects.json` declarado en manifest con object IDs, labels, numbers, source paths, page output paths, anchors, hrefs y reference text. Las paginas estaticas deben renderizar labels y links sin requests externos del renderer o CDN y sin MathJax en el navegador ni resolver de referencias en el browser. Fixtures y checks debug deben cubrir theorem, corollary, equation, figure, table, problem, homework y assignment cuando cambie el contrato.

Los bloques de proof son superficies de render estatico, no registros del index numerado. Pueden resolver `of` contra cualquier familia de objeto numerado, renderizar un heading y body de proof, y permanecer ausentes de `data/numbered-objects.json`.

```markdown
::: theorem {#teorema-principal title="Teorema de ejemplo"}
Para cada vector $\vect{v}$, la identidad devuelve $\vect{v}$.
:::

::: proof {#prueba-principal of="teorema-principal" title="Identidad"}
La igualdad se verifica componente por componente:
$$
I\vect{v}=\vect{v}.
$$
:::
```

Antes de cambiar comportamiento del renderizador, ejecuta la compuerta enfocada con `scripts/check-render-debug.sh`. Construye y previsualiza `examples/courses/render-fixture`, captura evidencia desktop/mobile y falla si hay TeX crudo visible, requests externos del renderizador, screenshots faltantes, overflow o dependencias MathJax ejecutadas en el browser. El gate escribe `report.json` e `index.html` junto a los screenshots. Cuando falle, inspecciona primero `index.html` y usa `report.json` para ubicar pagina, viewport, path de archivo y diagnosticos del copied site. Para una regresion de un curso especifico, usa `raya preview <course> --render-debug /tmp/raya-render-debug`. Trata esos archivos solo como evidencia local; no los confirmes en git ni los trates como autoridad del artifact.

Las referencias de codigo y notebooks son soporte source estatico en el baseline actual. Valida archivos `.py` y `.ipynb` linkeados por extension y por pertenencia al quantum propio o a un ancestro aceptado, no por nombres de directorio requeridos. Copia solo archivos linkeados y validados a `artifact/files/` y `artifact/site/_raya/files/`, mantiene `references.json` como superficie de datos, y conserva el estado `not-executed` hasta que una propuesta de ejecucion acepte runtimes y caches.

Los runtime profiles son solo metadata. Mantiene `runtime/profiles.yaml`, `pyproject.toml` y `uv.lock` fuera del arbol ordenado `course/`; valida policies, rutas de perfiles, cache inputs y los outputs `runtime.json`, `execution.json` y `cache.json` sin llamar `uv`, Docker, kernels ni archivos source.

La ejecucion local es explicita. `raya run <course> <target>` puede ejecutar un script o notebook validado mediante el profile `uv` seleccionado, con `--docker` solo cuando se pide y esta configurado. Cambios de ejecucion necesitan tests de CLI para dry-run, policies, cache reuse, refresh, logs, outputs, preservacion de notebook source, forma de comando Docker, artifact inspection y regresiones no-execution para validate/build/inspect/static serving.

Reviewed execution output es el camino frozen con source controlado. Mantiene archivos revisados bajo `_reviewed/execution/<target>/`, valida `reviewed.yaml` contra hashes actuales de source/runtime/input/review/files, y expone output revisado current mediante `data/reviewed-outputs.json`, `artifact/reviewed/`, `site/_raya/reviewed/`, metadata de referencias y panels estaticos. Cambios necesitan tests para `raya outputs list`, `raya outputs freeze`, metadata stale, archivos faltantes, `policy: frozen`, artifact inspection, static read paths y regresiones no-execution.

Las paginas renderizadas usan disciplina de superficie. Mantiene paginas normales enfocadas en contenido, navegacion, indices generados, panels compactos de recursos/estado y links deployment-neutral. Pon hashes, cache keys, rutas source, rutas de artifact e internos de freshness de reviewed output en `manifest.json`, `data/*.json` o paginas estaticas `_raya/inspect/`.

Usa `raya preview <course>` para revisar localmente paginas estaticas generadas. Preview valida, construye, sirve `artifact/site/` y reporta el entrypoint de estudiante mas la URL `_raya/inspect/` cuando exista. Cambios de preview necesitan tests CLI, regresiones no-execution, cobertura static-read-path y asserts visuales/layout para viewports representativos desktop y mobile.

La documentacion actual tambien es un curso de docs renderizable. Edita las paginas legibles en `docs/foundation/` y `docs/guides/`, manten alineado `docs/render-content/` para el orden renderizado, y trata `docs/artifact/` como output generado e ignorado. Usa `raya validate docs`, `raya build docs` y tests static-read-path cuando cambies el rendering de documentacion.

Para cambios sustanciales, declara el impacto de documentacion para colaboradores, profesores, estudiantes y agentes. Si cambia la documentacion de rol, manten separadas las paginas en ingles y espanol.
