---
id: docs-guides-es-colaboradores
title: Colaboradores
summary: Guia para cambiar codigo, contratos, docs y tests con seguridad.
status: ready
---
# Colaboradores

Empieza con `docs/foundation/15_system_overview.md`, despues `docs/foundation/13_truth_surfaces.md`, y despues las specs OpenSpec aceptadas para la capacidad que estas cambiando.

OpenSpec sigue disponible para cambios futuros de contrato. Cuando la persona usuaria selecciona explicitamente un flujo Superpowers, los documentos de diseno y plan de Superpowers versionados pueden guiar ese ciclo, pero `docs/foundation/` sigue siendo la fuente superior de verdad inicial y la implementacion debe actualizar las superficies afectadas de foundation, rol, test y contrato.

Usa los comandos Docker Compose y `uv` de `README.md` y `AGENTS.md` cuando cambies codigo, contratos, docs o tests. Ejecuta `./scripts/check.sh` antes de archivar o commitear, ejecuta `./scripts/check-docker.sh` cuando cambie comportamiento Docker, y conserva `./scripts/smoke-test.sh` para smoke checks de cursos externos cuando cambie la portabilidad de comandos o cursos. Ejecuta `./scripts/check.sh` y `./scripts/check-docker.sh` en secuencia, no en paralelo. Ambos preparan dependencias locales Node/MathJax mediante `scripts/check-python.sh`, por eso los scripts fallan de forma clara si otra verificacion ya esta preparando dependencias. Espera a que termine el proceso activo y vuelve a ejecutar el comando bloqueado. Mantiene capacidades diferidas en `docs/foundation/18_known_missing_work.md` hasta que un cambio OpenSpec aceptado las vuelva actuales. Mantiene rutas de paquetes, comandos, campos de schema e IDs duraderos en ingles.

Cuando cambies validacion o rendering de cursos, preserva el modelo convention-first: `source: course` apunta al arbol ordenado `course/`, los nombres ordenados definen el orden de autoria, `id` en frontmatter define identidad estable, `_official/` y `_assets/` colocados permanecen privados, y `navigation.json` junto con `indices.json` son datos generados del artifact. Los tests deben cubrir diagnosticos de fuente, export de objetos oficiales, copia de assets, schemas de artifact y rendering static-read-path.

Los wikilinks locales del curso son sintaxis de autoria en build, no
comportamiento del browser. La validacion resuelve `[[target]]` y
`[[target|label]]` contra las paginas del curso actual, falla targets faltantes
o ambiguos, y el rendering emite enlaces estaticos locales normales mas edges
explicitos de contenido en el grafo. No agregues resolucion de wikilinks en el
browser, servicios externos de grafo/busqueda ni fugas de rutas de fuente.

El rich static rendering pertenece a Glintstone. Mantiene parser, highlighter y MathJax detras de `packages/static`; los contratos de fuente deben describir comportamiento de autoria, no detalles internos de librerias. La math aceptada usa math inline con delimitadores de dolar, bloques display con delimitadores de doble dolar en lineas propias, macros locales por pagina, recursos locales bajo `site/_raya/render/math/`, diagnosticos estrictos y ninguna dependencia de renderer solo en browser. Cambios de renderer necesitan fixtures representativos, diagnosticos invalidos cuando aplique, tests de contrato, tests e2e/static-read-path, checks Chromium de math visible/sin requests externos, checks de overflow desktop/mobile y actualizaciones de documentacion de rol.

Los bloques de codigo fenced renderizan controles locales de copiado. Preserva el texto exacto copiado desde `pre code`, botones accesibles por teclado, fallback HTML estatico y la regla de no storage, no fetch y no scripts externos al cambiar este comportamiento.

Los controles de comodidad lectora viven en recursos locales de accesibilidad.
`Text size` y `OpenDyslexic` pueden persistir preferencias locales del browser,
pero no deben cambiar skins del curso, datos fuente, datos del grafo, identidad
de objetos numerados, progreso, respuestas, dominio ni recomendaciones.

Los handouts Print/PDF son comportamiento del renderer sobre paginas generadas
en `artifact/site/`. Mantenlos acotados a media print: oculta chrome y
controles, conserva contenido del articulo, MathJax, codigo, tablas, practica
oficial, objetos numerados y disclosures de soporte, y evita fetch, storage,
assets externos, lenguaje de estado del estudiante o fugas de rutas de fuente.

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
`REQUIRED_GRAPH_TOKENS`, `REQUIRED_FONT_TOKENS`, `ALLOWED_DENSITIES` y
`ALLOWED_FONT_STACKS` en `packages/static/src/raya_static/skins.py`. Los tokens
opcionales de grafo deben seguir siendo colores categoricos validados para las
variables generadas `--raya-graph-group-*`; no los conviertas en CSS arbitrario,
logica de tema en el browser, autoridad de datos del grafo, progreso, ranking
ni recomendaciones. Los tests deben cubrir selectores desconocidos, IDs
duplicados, desajustes entre nombre de archivo e `id`, campos de token no
soportados, colores malformados, colores de grafo malformados, contraste bajo,
densidad invalida, fuentes no seguras, `skin.css` generado, variables CSS de
paleta de grafo e herencia de la seccion mas cercana.
Los tokens de densidad pueden cambiar el espaciado de cards y controles de
workspaces generados mediante variables CSS del renderer. No deben convertirse
en controles de tipografia del articulo ni en logica de override de skin en el
browser.

Usa `examples/courses/render-fixture/course/2_math_authoring/0_index.md` cuando cambies rendering de math o guia de autoria. Es el fixture target para ejemplos validos actuales: `\begin{bmatrix}`, macros de vectores, `\newcommand`, `\renewcommand`, notacion de conjuntos y logica, normas, productos internos, derivaciones alineadas, notacion de optimizacion y Markdown de objetos numerados. Mantiene ejemplos invalidos de math en tests para que docs de profesores y estudiantes sigan siendo copiables.

Usa `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md` como fixture compacto cuando un cambio cruce math, objetos numerados, skins, entornos estaticos, assets locales y comportamiento de static read path.

El soporte de objetos numerados es comportamiento actual del renderer. Preserva el modelo de configuracion `render.numbered_objects` para numeracion y ajustes de secuencias/familias a nivel de curso; valida directivas fenced, IDs duraderos de objeto, referencias abreviadas `@id` y referencias explicitas `raya:ref/id`; y emite el index `data/numbered-objects.json` declarado en manifest con IDs de objeto, etiquetas, numeros, rutas de fuente, rutas de salida de pagina, anchors, hrefs y texto de referencia. Preserva el soporte incorporado de `remark` y la presentacion lectora predeterminada: secuencias tipo teorema, ejemplo, ejercicio y tarea usan `scannable`, figuras y tablas usan `caption`, y ecuaciones usan `equation`. Las paginas estaticas deben renderizar etiquetas y enlaces sin requests externos del renderer o CDN y sin MathJax en el navegador ni resolver de referencias en el browser. Fixtures y checks debug deben cubrir `remark` y el fixture reader-ux cuando cambie la experiencia lectora de contenido numerado.

Cuando cambies comportamiento de contenido numerado, manten los diagnosticos CLI/build y `data/numbered-objects.json` como autoridad. Render-debug puede resumir objetos, referencias, encabezados de prueba y capturas, pero es evidencia de inspeccion, no un contrato de datos de reemplazo.

Los bloques de prueba son superficies de render estatico, no registros del index numerado. Pueden resolver `of` contra cualquier familia de objeto numerado, renderizar un encabezado y cuerpo de prueba, y permanecer ausentes de `data/numbered-objects.json`.

Los entornos estaticos estan separados de los objetos numerados. Preserva
`proof`, `solution`, `hint` y `answer` como bloques renderizados durante el
build cuyo objetivo opcional `of` se resuelve contra
`data/numbered-objects.json`; no los agregues al index numerado ni exijas un
resolver de referencias en el navegador. Manten las pruebas abiertas y manten
`hint`, `solution` y `answer` como disclosures nativos cerrados por defecto. No
agregues scoring, progreso guardado, requests `fetch`, assets externos ni
browser-side MathJax a esos disclosures.

El contrato del renderizador de aprendizaje divide la estructura del curso en
categorias `current`, `planned` y `future`. El trabajo `current` puede usar
navegacion existente, contenido de autoria, assets locales, MathJax en build,
metadata de pagina y prerrequisitos estables. El trabajo `planned` necesita
datos aceptados de fuente y artifact. El trabajo `future`, como progreso
personal, analiticas, repaso adaptativo y colas espaciadas, necesita estado
dinamico de estudio fuera del renderizador estatico. Conserva las reglas: sin
MathJax en el browser, sin assets externos, sin metas inferidas y sin practica
relacionada inventada desde la prosa.

sessionStorage en la misma pestana puede restaurar solo identificadores de ramas
plegadas con scope de curso y el par explicito de estado visual de los rieles
estructurales izquierdo/derecho. El estado del drawer, filtro, foco, scroll,
contexto activo, progreso, dominio, recomendacion y personalizacion sigue siendo
no persistente.

La seccion de practica oficial es una superficie actual de rendering estatico
para objetos de nivel pagina desde datos `_official/` colocados junto a su
pagina. Implementala y revisala como conveniencia de lectura sobre autoridad de
fuente y artifact existente: `_official/` sigue siendo fuente de verdad, mientras
`data/official.json` y `manifest.json` siguen siendo superficies machine-readable.
La verificacion debe cubrir cards, prompts, quizzes, campos genericos de objetos
oficiales, texto escapado, controles nativos `details` cuando correspondan,
orden determinista y limites de privacidad/rutas de fuente. Los controles de
quizzes multiple-choice deben ser botones nativos locales a la pagina sobre
datos de opciones aceptados, conservar el reveal fallback y resetear sin
storage. No agregues scoring, grading, submissions, attempts, progreso, dominio,
recomendaciones, llamadas a backend, `fetch` en runtime,
localStorage/sessionStorage, requests externos/CDN del renderer ni MathJax en
el browser. Los cambios en esta superficie deben incluir cobertura
static-read-path, asserts enfocados de escaping/privacidad, checks
no-storage/no-fetch e impacto de docs de rol para estudiantes, profesores,
colaboradores y agentes.

El workspace Official Tasks tambien es comportamiento actual del renderer
estatico. Revisalo como superficie generada de planeacion sobre objetos
oficiales `assignment`, `project`, `exam` y `task`, no como servicio de
calendario ni sistema de estado del estudiante. La verificacion debe cubrir
`data/tasks.json`, declaracion en `manifest.json`, `_raya/tasks/index.html`,
el recurso local `tasks.js`, campos publicos de planeacion bajo `content`,
anchors de pagina propietaria, links de foco en grafo, filtros, ordenamiento,
inspeccion por teclado, layout desktop/movil, sin requests externos, sin
`fetch` en runtime, sin browser storage y sin lenguaje de grading, entregas,
progreso, dominio o recomendaciones.

El workspace Official Schedule tambien es comportamiento actual del renderer
estatico sobre los mismos objetos aceptados de familia task cuando incluyen
`content.due` o `content.available`. Revisalo como vista fechada de browser
sobre la semantica de `data/tasks.json`, no como nuevo index de artifact,
calendar feed, sincronizacion de calendario, sistema de recordatorios ni
superficie de estado del estudiante. La verificacion debe cubrir
`_raya/schedule/index.html`, el recurso local `schedule.js`, filtrado solo de
objetos fechados, anchors de pagina propietaria, links de foco en grafo, sin
rutas privadas, sin `fetch` en runtime, sin browser storage y sin lenguaje de
grading, entregas, progreso, dominio o recomendaciones.

Revisa los controles de la shell como superficies de accesibilidad. El lector
actual usa un mapa del curso expandido, renderizado como un mapa jerarquico del
curso expandido por defecto en escritorio,
puede filtrar etiquetas renderizadas del mapa localmente, puede colapsarse con
click explicito a un opener minimo flotante Map. El drawer de telefono y otros
estados transitorios de la shell siguen siendo no persistentes; el par explicito
de estado visual de los rieles estructurales puede persistir en sessionStorage
en la misma pestana bajo el contrato con scope de curso anterior. El mapa del
curso se colapsa con click explicito, no por hover, usa `aria-expanded`, y debe
servirse desde recursos locales del renderer sin scripts ni estilos externos.
Las cards Previous/Next al final del articulo se generan desde el mismo orden del
curso que los links compactos de secuencia. Mantenlas estaticas, accesibles con
teclado, responsivas, y sin lenguaje de progreso, dominio, recomendacion o
siguiente paso personal.

Revisa el Page brief como orientacion estatica inicial sobre metadata ya
aceptada. Puede mostrar resumen, status, posicion estructural de pagina, tiempo
estimado escrito por el curso o estimacion aproximada de lectura, tags,
prerrequisitos resueltos, conteos de enlaces explicitos del grafo y conteos de
practica oficial. Debe usar solo enlaces y anchors locales, ser responsivo y
evitar rutas de fuente, rutas privadas, fetches, storage del
browser, progreso, dominio, recomendaciones, evaluacion o personalizacion.

Revisa el Course graph como una superficie estatica de artifact. La busqueda del
grafo, los detalles de pagina seleccionada, filtros de grupo, controles SVG de
viewport y workspace expandido del grafo deben usar solo datos embebidos del
artifact y recursos locales del renderer. Zoom in, Zoom out, Fit y Reset view
pueden cambiar el viewport SVG visual, pero no deben persistir estado, pedir
datos del grafo ni limpiar el contexto de pagina seleccionada. Los atajos del
grafo pueden enfocar busqueda, ajustar la vista SVG o resetear filtros y
seleccion, pero no deben interceptar escritura en campos. No agregues
motores de grafo CDN, fetches runtime, estado persistente del grafo ni lenguaje
de recomendaciones/progreso. Los relationship walkthroughs de pagina
seleccionada deben construirse solo desde edges explicitos generados del grafo
y enlaces locales. Los relationship chips pueden actuar como filtros con
botones nativos para ese walkthrough, con `aria-pressed`, sin mutar la URL, sin
storage del navegador y con limpieza cuando cambia la seleccion del grafo. El reveal contextual de labels puede ocultar visualmente
labels SVG de bajo contexto, pero los anchors de pagina y texto `aria-label`
deben seguir disponibles. El contexto de URL generado puede enfocar una pagina,
pero debe seguir siendo transitorio. Los previews de conexion solo pueden
etiquetar tipo y direccion de relacion, como `Content` y `From this page`,
desde contexto explicito generado del grafo.
El readout de estado/debug del grafo y el control de copiar URL pueden estar
dentro de un disclosure nativo cerrado por defecto; mantenlo sincronizado,
local y sin storage del grafo.

Revisa Course Search como companero de navegacion del grafo. Coincidencia
aproximada, controles de limpiar y movimiento con teclado por resultados son
validos sobre metadata publica embebida de paginas y prosa publica renderizada
del articulo. No indexes rutas de fuente, rutas de artifact, rutas privadas de
soporte, internos de MathJax, TeX crudo, cache keys, contenido solo de
respuestas/soporte ni estado del estudiante. El contexto de consulta generado
puede precargar la caja de busqueda sin convertirse en estado guardado. Los
records de busqueda pueden incluir anchors y snippets publicos generados de
secciones u objetos como subresultados, pero deben seguir siendo ayudas publicas
sanitizadas para escanear, no recomendaciones ni autoridad alterna. Los
enlaces graph-focus de resultados de busqueda deben generarse solo desde stable
IDs y URLs locales del grafo; conserva lenguaje estructural como `View in
graph`. Los workspaces de descubrimiento Search y Practice pueden usar regiones
de controles, resultados y contexto en desktop. Search, Practice, Tasks y
Schedule pueden mostrar una franja compartida de pagina de curso enfocada para
un handoff valido `?page=<page-id>`, con links a Search, Graph, Practice, Tasks
y Schedule enfocados en la misma pagina. Search, Practice, Tasks y Schedule
tambien pueden mostrar avisos compactos de foco de pagina en sus regiones de
control. La franja y los avisos deben ocultarse cuando el foco falta o no es
valido y despues de que Clear/Escape restaura el workspace completo. Esas
regiones deben quedarse publicas, ser responsivas y no guardar estado de
descubrimiento.

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

Las cards generadas de entrada de seccion son parte del indice generado normal.
Deben derivarse solo de paginas hijas, resumenes, tiempo estimado y conteos de
objetos de estudio escritos. No las uses para recomendaciones, finalizacion,
dominio, progreso personal ni acciones inferidas.

Usa `raya preview <course>` para revisar localmente paginas estaticas generadas. Preview valida, construye, sirve `artifact/site/` y reporta el entrypoint de estudiante mas la URL `_raya/inspect/` cuando exista. Cambios de preview necesitan tests CLI, regresiones no-execution, cobertura static-read-path y asserts visuales/layout para viewports representativos desktop y mobile.

La documentacion actual tambien es un curso de docs renderizable. Edita las paginas legibles en `docs/foundation/` y `docs/guides/`, manten alineado `docs/render-content/` para el orden renderizado, y trata `docs/artifact/` como output generado e ignorado. Usa `raya validate docs`, `raya build docs` y tests static-read-path cuando cambies el rendering de documentacion.

Para cambios sustanciales, declara el impacto de documentacion para colaboradores, profesores, estudiantes y agentes. Si cambia la documentacion de rol, manten separadas las paginas en ingles y espanol.

Search, Graph, Practice, Tasks y Schedule usan el mapa de curso persistente con
links relativos generados y recursos locales de shell. Revisa el mosaico del
workspace activo, ningun enlace actual del arbol del curso y la ausencia del
Context lector junto con filtros, resultados y la franja de pagina enfocada.
Estas interacciones son volatiles: no deben hacer fetch de recursos externos ni
escribir estado de estudiante, fuente, artifact o preferencias no relacionadas.
