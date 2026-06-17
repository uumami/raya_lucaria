---
id: docs-guides-es-colaboradores
title: Colaboradores
summary: Guia para cambiar codigo, contratos, docs y tests con seguridad.
status: ready
---
# Colaboradores

Empieza con `docs/foundation/15_system_overview.md`, despues `docs/foundation/13_truth_surfaces.md`, y despues las specs OpenSpec aceptadas para la capacidad que estas cambiando.

Usa los comandos Docker Compose y `uv` de `README.md` y `AGENTS.md` cuando cambies codigo, contratos, docs o tests. Ejecuta `./scripts/check.sh` antes de archivar o commitear, ejecuta `./scripts/check-docker.sh` cuando cambie comportamiento Docker, y conserva `./scripts/smoke-test.sh` para smoke checks de cursos externos cuando cambie la portabilidad de comandos o cursos. Ejecuta `./scripts/check.sh` y `./scripts/check-docker.sh` en secuencia, no en paralelo. Ambos preparan dependencias locales Node/MathJax mediante `scripts/check-python.sh`, por eso los scripts fallan de forma clara si otra verificacion ya esta preparando dependencias. Espera a que termine el proceso activo y vuelve a ejecutar el comando bloqueado. Mantiene capacidades diferidas en `docs/foundation/18_known_missing_work.md` hasta que un cambio OpenSpec aceptado las vuelva actuales. Mantiene rutas de paquetes, comandos, campos de schema e IDs duraderos en ingles.

Cuando cambies validacion o rendering de cursos, preserva el modelo convention-first: `source: course` apunta al arbol ordenado `course/`, los nombres ordenados definen el orden de autoria, `id` en frontmatter define identidad estable, `_official/` y `_assets/` colocados permanecen privados, y `navigation.json` junto con `indices.json` son datos generados del artifact. Los tests deben cubrir diagnosticos de fuente, export de objetos oficiales, copia de assets, schemas de artifact y rendering static-read-path.

El rich static rendering pertenece a Glintstone. Mantiene parser, highlighter y MathJax detras de `packages/static`; los contratos de fuente deben describir comportamiento de autoria, no detalles internos de librerias. La math aceptada usa math inline con delimitadores de dolar, bloques display con delimitadores de doble dolar en lineas propias, macros locales por pagina, recursos locales bajo `site/_raya/render/math/`, diagnosticos estrictos y ninguna dependencia de renderer solo en browser. Cambios de renderer necesitan fixtures representativos, diagnosticos invalidos cuando aplique, tests de contrato, tests e2e/static-read-path, checks Chromium de math visible/sin requests externos, checks de overflow desktop/mobile y actualizaciones de documentacion de rol.

Los cambios de skin deben preservar validacion de tokens semanticos y output
estatico generado. Los perfiles locales del curso bajo `skins/` definen tokens
semanticos. `render.skin` del curso y los selectores `_raya/skin.yaml` de
seccion eligen uno de esos perfiles; no definen tokens. El rendering emite
`_raya/render/skin.css` y marca paginas con `data-raya-skin`. El archivo CSS
generado es `skin.css` bajo la ruta de soporte del renderer. La regla es no
CSS arbitrario, no fuentes externas, no requests CDN y no resolver de skin en el browser.
Cubre cambios de skin con evidencia render-debug cuando puedan fallar CSS generado,
atributos de pagina, recursos locales o layout visual. Cuando cambies este
contrato, manten docs alineadas con `REQUIRED_COLOR_TOKENS`,
`REQUIRED_FONT_TOKENS`, `ALLOWED_DENSITIES` y `ALLOWED_FONT_STACKS` en
`packages/static/src/raya_static/skins.py`. Los tests deben cubrir selectores
desconocidos, IDs duplicados, desajustes entre nombre de archivo e `id`, campos
de token no soportados, colores malformados, contraste bajo, densidad invalida,
fuentes no seguras, `skin.css` generado e herencia de la seccion mas cercana.

Usa `examples/courses/render-fixture/course/2_math_authoring/0_index.md` cuando cambies rendering de math o guia de autoria. Es el fixture target para ejemplos validos actuales: `\begin{bmatrix}`, macros de vectores, `\newcommand`, `\renewcommand`, notacion de conjuntos y logica, normas, productos internos, derivaciones alineadas, notacion de optimizacion y Markdown de objetos numerados. Mantiene ejemplos invalidos de math en tests para que docs de profesores y estudiantes sigan siendo copiables.

El soporte de objetos numerados es comportamiento actual del renderer. Preserva el modelo de configuracion `render.numbered_objects` para numeracion y ajustes de secuencias/familias a nivel de curso; valida directivas fenced, IDs duraderos de objeto, referencias abreviadas `@id` y referencias explicitas `raya:ref/id`; y emite el index `data/numbered-objects.json` declarado en manifest con IDs de objeto, etiquetas, numeros, rutas de fuente, rutas de salida de pagina, anchors, hrefs y texto de referencia. Preserva el soporte incorporado de `remark` y la presentacion lectora predeterminada: secuencias tipo teorema, ejemplo, ejercicio y tarea usan `scannable`, figuras y tablas usan `caption`, y ecuaciones usan `equation`. Las paginas estaticas deben renderizar etiquetas y enlaces sin requests externos del renderer o CDN y sin MathJax en el navegador ni resolver de referencias en el browser. Fixtures y checks debug deben cubrir `remark` y el fixture reader-ux cuando cambie la experiencia lectora de contenido numerado.

Cuando cambies comportamiento de contenido numerado, manten los diagnosticos CLI/build y `data/numbered-objects.json` como autoridad. Render-debug puede resumir objetos, referencias, encabezados de prueba y capturas, pero es evidencia de inspeccion, no un contrato de datos de reemplazo.

Los bloques de prueba son superficies de render estatico, no registros del index numerado. Pueden resolver `of` contra cualquier familia de objeto numerado, renderizar un encabezado y cuerpo de prueba, y permanecer ausentes de `data/numbered-objects.json`.

Los entornos estaticos estan separados de los objetos numerados. Preserva
`proof`, `solution`, `hint` y `answer` como bloques renderizados durante el
build cuyo objetivo opcional `of` se resuelve contra
`data/numbered-objects.json`; no los agregues al index numerado ni exijas un
resolver de referencias en el navegador.

```markdown
::: theorem {#main-theorem title="Teorema de ejemplo"}
Para cada vector $\vect{v}$, la identidad devuelve $\vect{v}$.
:::

::: proof {#proof-main of="main-theorem" title="Identidad"}
La igualdad se verifica componente por componente:
$$
I\vect{v}=\vect{v}.
$$
:::
```

Antes de cambiar comportamiento del renderizador, ejecuta la compuerta enfocada con `scripts/check-render-debug.sh`. Construye y previsualiza `examples/courses/render-fixture`, captura evidencia desktop/mobile y falla si hay TeX crudo visible, requests externos del renderizador, capturas faltantes, overflow o dependencias MathJax ejecutadas en el browser. El gate escribe `report.json` e `index.html` junto a las capturas. Cuando falle, inspecciona primero `index.html` y usa `report.json` para ubicar pagina, viewport, path de archivo y diagnosticos del copied site. Para una regresion de un curso especifico, usa `raya preview <course> --render-debug /tmp/raya-render-debug`. Trata esos archivos solo como evidencia local; no los incluyas en commits ni los trates como autoridad del artifact.

Las referencias de codigo y notebooks son soporte de fuente estatico en el baseline actual. Valida archivos `.py` y `.ipynb` enlazados por extension y por pertenencia al quantum propio o a un ancestro aceptado, no por nombres de directorio requeridos. Copia solo archivos enlazados y validados a `artifact/files/` y `artifact/site/_raya/files/`, mantiene `references.json` como superficie de datos, y conserva el estado `not-executed` hasta que una propuesta de ejecucion acepte runtimes y caches.

Los runtime profiles son solo metadata. Mantiene `runtime/profiles.yaml`, `pyproject.toml` y `uv.lock` fuera del arbol ordenado `course/`; valida policies, rutas de perfiles, cache inputs y los outputs `runtime.json`, `execution.json` y `cache.json` sin llamar `uv`, Docker, kernels ni archivos fuente.

La ejecucion local es explicita. `raya run <course> <target>` puede ejecutar un script o notebook validado mediante el profile `uv` seleccionado, con `--docker` solo cuando se pide y esta configurado. Cambios de ejecucion necesitan tests de CLI para dry-run, policies, cache reuse, refresh, logs, outputs, preservacion de fuente de notebook, forma de comando Docker, artifact inspection y regresiones no-execution para validate/build/inspect/static serving.

Reviewed execution output es el camino frozen con fuente controlada. Mantiene archivos revisados bajo `_reviewed/execution/<target>/`, valida `reviewed.yaml` contra hashes actuales de fuente/runtime/input/review/files, y expone output revisado vigente mediante `data/reviewed-outputs.json`, `artifact/reviewed/`, `site/_raya/reviewed/`, metadata de referencias y paneles estaticos. Cambios necesitan tests para `raya outputs list`, `raya outputs freeze`, metadata desactualizada, archivos faltantes, `policy: frozen`, artifact inspection, static read paths y regresiones no-execution.

Las paginas renderizadas usan disciplina de superficie. Mantiene paginas normales enfocadas en contenido, navegacion, indices generados, paneles compactos de recursos/estado y enlaces deployment-neutral. Pon hashes, cache keys, rutas de fuente, rutas de artifact e internos de frescura de reviewed output en `manifest.json`, `data/*.json` o paginas estaticas `_raya/inspect/`.

Usa `raya preview <course>` para revisar localmente paginas estaticas generadas. Preview valida, construye, sirve `artifact/site/` y reporta el entrypoint de estudiante mas la URL `_raya/inspect/` cuando exista. Cambios de preview necesitan tests CLI, regresiones no-execution, cobertura static-read-path y asserts visuales/layout para viewports representativos desktop y mobile.

La documentacion actual tambien es un curso de docs renderizable. Edita las paginas legibles en `docs/foundation/` y `docs/guides/`, manten alineado `docs/render-content/` para el orden renderizado, y trata `docs/artifact/` como output generado e ignorado. Usa `raya validate docs`, `raya build docs` y tests static-read-path cuando cambies el rendering de documentacion.

Para cambios sustanciales, declara el impacto de documentacion para colaboradores, profesores, estudiantes y agentes. Si cambia la documentacion de rol, manten separadas las paginas en ingles y espanol.
