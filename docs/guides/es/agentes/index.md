---
id: docs-guides-es-agentes
title: Agentes
summary: Guia para agentes que trabajan mediante archivos, comandos, specs y diagnosticos.
status: ready
---
# Agentes

Los agentes operan mediante archivos, comandos, specs OpenSpec, diagnosticos y limites de autoridad explicitos. Los agentes heredan la autoridad del usuario y no reciben confianza especial.

Usa `docs/foundation/13_truth_surfaces.md` para el mapa de autoridad, specs OpenSpec aceptadas para contratos testeables y `AGENTS.md` para el flujo del repositorio.

OpenSpec sigue disponible para cambios futuros de contrato. Cuando la persona usuaria selecciona explicitamente un flujo Superpowers, los documentos de diseno y plan de Superpowers versionados pueden guiar ese ciclo, pero `docs/foundation/` sigue siendo la fuente superior de verdad inicial y la implementacion debe actualizar las superficies afectadas de foundation, rol, test y contrato.

Usa los check scripts canonicos de `README.md` y `AGENTS.md`: `./scripts/check.sh` para el gate host, `./scripts/check-docker.sh` para verificacion Python/Raya en el contenedor de referencia, y `./scripts/smoke-test.sh` para checks de portabilidad de cursos externos. Ejecuta `./scripts/check.sh` y `./scripts/check-docker.sh` en secuencia, no en paralelo. Ambos preparan dependencias locales Node/MathJax mediante `scripts/check-python.sh`, por eso el lock fail-fast del repositorio informa cuando otra verificacion Raya ya esta preparando dependencias. Espera a que termine el proceso activo y vuelve a ejecutar el comando bloqueado. Evita editar outputs generados, carpetas de dependencias, caches o output de sesiones locales. Mantiene capacidades diferidas en `docs/foundation/18_known_missing_work.md` hasta que un cambio OpenSpec aceptado las vuelva actuales.

Para contenido de curso, trata los archivos fuente como canonicos y los artifacts generados como reconstruibles. Preserva `source: course`, el arbol ordenado `course/`, `id` en frontmatter, enlaces `raya:<id>`, privacidad de `_official/` y `_assets/` colocados, marcadores de indice generado y superficies de datos declaradas en manifest. No edites `artifact/` generado como fuente de verdad.

Para rich static rendering, preserva el limite de Glintstone: reescribe enlaces mediante reglas Raya, genera anchors locales y tablas de contenido desde headings de fuente, pre-renderiza math MathJax aceptada durante build, mantiene archivos de soporte bajo `site/_raya/`, escapa raw HTML y no ejecutes bloques de codigo. Testea HTML generado, static read paths, math visible en browser, assets locales de math, ausencia de requests externos del renderer y overflow en desktop/mobile.

Para bloques de codigo copiables, inspecciona el markup `.raya-code-block` renderizado, el handler local en `shell.js` y el texto copiado desde `pre code`. El control de copiado puede usar Clipboard API o fallback local, pero no debe ejecutar codigo, persistir estado lector, hacer fetch de datos ni cargar scripts externos.

Para depurar skins, inspecciona superficies en este orden: el selector en
`raya.yaml` o `_raya/skin.yaml`, el archivo de skin seleccionado, diagnosticos
de build, `_raya/render/skin.css` generado, el atributo renderizado
`data-raya-skin` de la pagina, el nombre de archivo `skin.css` y el reporte
render-debug. No infieras autoridad de fuente desde la presentacion visual ni
desde HTML scrapeado. Cuando aparezca un problema de skin, primero clasifica si
la fuente es un problema de selector, un problema de tokens de perfil, output
CSS generado o activacion de pagina renderizada. No infieras estado de skin solo
desde screenshots; compara el selector fuente, perfil cargado, diagnosticos,
`skin.css`, `data-raya-skin` y reporte render-debug.

Para el toggle lector `OpenDyslexic`, verifica los assets estaticos generados
bajo `_raya/render/accessibility/`, el archivo local de fuente, el script local
del toggle y la paridad estatica entre preview y despliegue copiado. Trata
cualquier request de fuente externa como regresion; el toggle puede usar un
script local, pero no debe introducir MathJax en el browser ni un renderer
externo.

Para el toggle lector `Text size`, verifica la misma ruta local de recursos de
accesibilidad, `data-raya-text-size` en la raiz del documento, labels de la barra
de comandos, tamano de texto computado del articulo y persistencia tras recargar.
Tratalo solo como preferencia local de comodidad; no debe cambiar
`data-raya-skin`, contenido fuente, datos del grafo, progreso, respuestas,
dominio ni recomendaciones.

Para checks de autoria de math, usa `examples/courses/render-fixture/course/2_math_authoring/0_index.md` como fixture de fuente enfocado. Verifica paginas de fuente en vez de archivos generados bajo `artifact/`, y usa evidencia de render-debug para confirmar que no hay TeX crudo visible, conversion browser-side MathJax ni requests externos del renderer. El soporte de objeto numerado es comportamiento actual: inspecciona directivas fenced, IDs duraderos, anclas renderizadas, referencias abreviadas `@id`, referencias explicitas `raya:ref/id` y el index `data/numbered-objects.json` declarado en manifest en vez de buscar soporte LaTeX `\label` o `\ref`.

Cuando un problema de rendering cruce math, objetos numerados, skins, referencias, entornos estaticos y assets locales, inspecciona primero `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md`, despues pasa a la pagina fixture especializada de la superficie que falla.

Para la estructura del curso basada en ciencia del aprendizaje, conserva
restricciones de fuente y autoridad actual del artifact. El articulo principal
puede terminar con un bloque Page connections generado desde contexto explicito
del grafo de enlaces de contenido entrantes y salientes. El riel derecho puede
renderizar contenidos de pagina actuales, metadata normalizada, prerrequisitos
por ID estable, enlaces anterior/siguiente, resumenes estaticos de Connections
para contexto explicito de grafo entrante y saliente, y enlaces de foco en grafo
para esas relaciones explicitas. Mantiene el limite: sin metas inferidas, sin
practica relacionada falsa, sin progreso personal y sin MathJax en el browser.
Usa checks render-debug cuando puedan fallar layout de la estructura del curso,
recursos locales, capturas, overflow o math visible.

Para el rendering de practica oficial, inspecciona el objeto fuente
`_official/`, la entrada generada en `data/official.json`, la pagina renderizada
que lo posee y `manifest.json` en vez de tratar HTML normal como autoridad.
Verifica que cards, prompts, quizzes y campos genericos se rendericen solo en la
pagina propietaria como texto escapado, con controles nativos `details` cuando
corresponda y sin rutas privadas de fuente. Confirma que la pagina no agregue
scoring, grading, submissions, attempts, progreso, dominio, recomendaciones,
llamadas a backend, `fetch` en runtime, localStorage/sessionStorage, requests
externos/CDN del renderer ni MathJax en el browser. Cuando cambie esta
superficie, incluye checks static-read-path, checks de escaping/privacidad,
inspeccion no-storage/no-fetch e impacto de docs de rol.

Para el workspace Official Practice, inspecciona los mismos objetos
fuente `_official/`, `data/official.json`, `manifest.json`,
`_raya/practice/index.html` y el script local del workspace. Verifica que el
workspace liste solo objetos oficiales aceptados, enlace cada item de vuelta al
anchor de su pagina propietaria como `#raya-official-<id>` y use links de foco
en grafo solo cuando exista contexto de grafo. Confirma que no haya rutas
privadas de fuente, rutas de soporte, duplicados ocultos de respuestas,
requests externos, `fetch` en runtime, localStorage/sessionStorage, scoring,
submissions, attempts, grading, progreso, dominio, recomendacion, adaptacion ni
lenguaje de estado del estudiante.

Al cambiar la shell, verifica el mapa del curso expandido por defecto, incluida
la estructura de mapa jerarquico del curso expandido,
la orientacion de pagina actual dentro del mapa, el comportamiento del filtro
del mapa, el contexto superior de lectura, los links compactos
anterior/siguiente, las cards Previous/Next al final del articulo, la metadata
del riel compacto operable, la salida de render-debug, el comportamiento movil
sin overflow y sin solicitudes externas. El estado del mapa del curso, el texto
del filtro y el contexto de lectura son UI no persistente; la orientacion de
pagina actual en el mapa tambien debe seguir no persistente y no debe restaurar
storage de navegacion legacy. Trata la posicion de pagina en la barra superior y
en las cards de secuencia como orientacion estructural del curso, no como
progreso del estudiante.

Al cambiar indices generados de seccion, verifica markup de cards de entrada,
navegacion normal con enlaces locales, comportamiento desktop/mobile sin
overflow y ausencia de lenguaje de recomendaciones/progreso/dominio dentro de la
superficie del indice generado.

Al cambiar el Course graph, verifica busqueda aproximada, detalles de pagina
seleccionada, resumenes de vecindario de pagina seleccionada, estados visuales
de paginas conectadas, filtros de grupo, semantica de color por grupo, tamano de
nodo acotado por grado, estado de inspeccion por hover/foco, paridad de
inspeccion con teclado, estado de workspace expandido del grafo, controles SVG
de viewport, chrome compartido de descubrimiento, chrome movil compacto,
comportamiento movil sin overflow y sin solicitudes externas despues de cargar
la pagina. El
estado UI del grafo es no persistente y debe venir de datos de grafo embebidos
del artifact, no de HTML scrapeado ni browser storage. El contexto de URL
generado puede seleccionar una pagina solo cuando resuelve a un nodo embebido
del grafo. Los conteos de vecindario deben derivarse de edges del grafo
generado, y los resaltados de pagina conectada deben excluir el nodo
seleccionado. Los conteos del riel Connections deben venir solo de contexto
explicito del grafo. Los enlaces de foco al grafo en el riel deben apuntar solo
a prerequisitos explicitos o contexto de grafo entrante/saliente.
Zoom in, Zoom out, Fit y Reset view pueden cambiar el `viewBox` SVG; no deben
pedir datos del grafo, persistir estado del grafo, limpiar detalles de pagina
seleccionada ni quedar habilitados cuando el grafo SVG esta oculto por el layout
de lista.
Los conteos y enlaces de Page connections del articulo tambien deben venir solo
de contexto explicito del grafo de enlaces de contenido entrantes/salientes,
permanecer dentro del articulo y evitar rutas de fuente, rutas privadas de
soporte, URLs externas, requests fetch, llamadas a storage, progreso, dominio,
recomendaciones y lenguaje de ranking.
Las vistas previas de Page connections en el riel y el articulo deben usar solo
metadatos publicos generados de pagina: titulo, resumen, estado, URL local de
la pagina, URL de foco en grafo y conteos explicitos entrantes/salientes.
Verifica comportamiento de controles nativos de despliegue, texto escapado, sin
rutas privadas, sin almacenamiento del navegador, sin fetch, sin solicitudes
externas y sin lenguaje de recomendacion, avance o maestria.
Trata color, tamano y texto de inspeccion del grafo como pistas de legibilidad
estructural;
no introduzcas progreso, dominio, recomendaciones, rankings, estado persistente
del grafo, librerias externas de grafo, requests fetch ni payloads de grafo en
runtime.

Al cambiar Course Search, verifica coincidencia aproximada, movimiento con
teclado por resultados, Enter para abrir, controles de limpiar, chrome
compartido de descubrimiento, chrome movil compacto, sin solicitudes externas y
sin estado persistente de busqueda. Los payloads de busqueda siguen siendo solo
metadata, y el contexto de consulta generado debe permanecer transitorio. Los
enlaces graph-focus de resultados de busqueda deben venir de stable IDs y URLs
locales generadas del grafo, preservar Enter para abrir la pagina, y evitar
lenguaje de recomendacion o progreso. Las paginas de descubrimiento Search y
Graph pueden cargar recursos locales de accesibilidad para Text size y
`OpenDyslexic`, pero no deben cargar `shell.js`, un toggle de mapa del curso,
assets externos de workspace ni estado persistente de graph/search.

Para depurar renderizado, usa `scripts/check-render-debug.sh` cuando necesites la compuerta enfocada de paridad del fixture que tambien corre en la verificacion host/Docker. El gate escribe `report.json` e `index.html` junto a las capturas. Cuando falle, inspecciona primero `index.html` y usa `report.json` para ubicar pagina, viewport, path de archivo y diagnosticos del sitio copiado. Usa `raya preview <course> --render-debug /tmp/raya-render-debug` cuando diagnostiques un curso especifico. Ambos caminos inspeccionan paginas estaticas generadas; ninguno ejecuta codigo del curso ni depende de conversion MathJax en el browser. Usa esa salida como evidencia para fallas de layout/math, fuga de TeX visible, requests externos y overflow, pero conserva la autoridad en los archivos fuente, `manifest.json` y los `data/*.json` declarados por el manifest. Trata archivos render-debug solo como evidencia local; no los incluyas en commits.

Para diagnosticos de objeto numerado, compara la directiva en la fuente, la entrada en `data/numbered-objects.json`, el ancla renderizada de la pagina, el href estatico, el texto visible de referencia y la evidencia de captura/reporte de render-debug. Incluye el fixture reader-ux y casos de familia theorem como `remark` incorporado cuando fallen etiquetas, secuencias compartidas o presentacion. Anota si los objetos usan el estilo esperado `scannable`, `caption` o `equation`. Usa la ruta render-debug para generar capturas y output de inspeccion, pero conserva el contrato machine-readable en datos declarados por el manifest en vez de HTML scrapeado.

Para fallas de contenido numerado, compara en este orden: la directiva en la fuente, el diagnostico de build, `data/numbered-objects.json`, el ancla/enlace renderizado y la evidencia de render-debug.

Para bloques de prueba, valida objetivos `of` contra `data/numbered-objects.json`; no introduzcas `\label`, `\ref`, `\begin{proof}` de LaTeX ni browser-side MathJax. Las pruebas se renderizan como entornos estaticos abiertos y no deben aparecer como registros del index numerado.

Para fallas de entornos estaticos, inspecciona la directiva en la fuente, el
diagnostico de build, el registro objetivo en `data/numbered-objects.json` si `of` esta presente,
el encabezado/ancla renderizado y la evidencia de render-debug del fixture
`reader-ux`. `hint`, `solution` y `answer` deben ser disclosures nativos
cerrados por defecto; no deben requerir storage, fetch, scoring, assets externos
ni browser-side MathJax.

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

Para referencias de codigo y notebooks, clasifica archivos `.py` y `.ipynb` linkeados por extension y por pertenencia al quantum propio o a un ancestro aceptado. Trata nombres como `scripts/`, `labs/`, `code/` y `notebooks/` como elecciones ordinarias de autoria, bloquea referencias privadas o cross-quantum, copia solo archivos linkeados y validados a superficies de artifact y de browser, actualiza `references.json`, y nunca infieras ejecucion desde previews.

Para runtime metadata, trata `runtime/profiles.yaml`, `pyproject.toml` y `uv.lock` en la raiz como soporte de fuente fuera del orden de aprendizaje. Valida y emite metadata de runtime, execution plan y cache, pero nunca llames `uv`, Docker, kernels, package installers, notebooks, scripts ni cache refreshes salvo que un contrato de ejecucion aceptado posterior lo diga explicitamente.

Para ejecucion local, usa `raya run <course> <target>` solo cuando la tarea pida explicitamente ejecutar un target. Prefiere `--dry-run` para inspeccionar el plan primero. Trata `artifact/data/execution-results.json`, `artifact/logs/`, `artifact/execution/` y `artifact/cache/results/` como output generado; no los edites ni los promociones como fuente de verdad.

Para reviewed execution output, trata `_reviewed/execution/<target>/` como soporte de fuente controlado que requiere revision humana. Usa `raya outputs list <course>` para inspeccionar estado generado y revisado sin ejecucion. Usa `raya outputs freeze <course> <target>` solo para copiar un resultado generado exitoso y vigente hacia `_reviewed/`; no trates freeze como aprobacion institucional. `policy: frozen` valida metadata y archivos revisados, y no debe llamar `uv`, Docker, kernels, scripts, notebooks, package installers ni cache refreshes.

Para superficies renderizadas, no hagas scraping de HTML normal como autoridad y no pongas internos verbosos en paginas predeterminadas. Usa `manifest.json`, `data/*.json`, archivos copiados y paginas estaticas `_raya/inspect/` para hashes, cache keys, rutas de fuente, rutas de artifact, detalles de runtime y metadata de frescura de reviewed output.

Para preview renderizado, usa `raya preview <course> --dry-run` para inspeccionar el plan o `raya preview <course>` para servir el sitio estatico generado. Preview no ejecuta: puede validar, construir y servir `artifact/site/`, pero no debe llamar `raya run`, `raya outputs freeze`, Docker execution, kernels, package installers, scripts, notebooks, runtime profiles ni cache refreshes. Cambios de superficie renderizada necesitan static-read-path y checks visuales/layout.

Para documentacion del repositorio, `docs/raya.yaml` renderiza los docs actuales mediante `docs/render-content/`. Edita `docs/foundation/` y `docs/guides/` como fuente legible, actualiza el arbol ordenado de render cuando se agrega o reordena una pagina renderizada, y usa `raya validate docs` mas `raya build docs` antes de depender del artifact estatico de docs.

Cuando actualices documentacion, manten separadas las paginas de rol en ingles y espanol. Conserva identificadores tecnicos en ingles como `raya`, `raya.yaml`, `source`, `course/`, `_official/`, `_assets/`, `artifact/`, `packages/static` y `OpenSpec`.
