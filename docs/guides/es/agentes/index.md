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

Para problemas de wikilinks, inspecciona tokens fuente `[[target]]` o
`[[target|label]]`, page IDs, aliases, titulos, nav titles, rutas de fuente,
diagnosticos de validacion, HTML renderizado, `data/links.json` y
`data/graph.json`. El resolver es local al curso y ocurre durante build; texto
wikilink crudo en HTML renderizado, edges de contenido faltantes,
resolucion en el browser o requests externos de grafo/busqueda son regresiones.

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
Para problemas de paleta del grafo, inspecciona los `tokens.graph.group_1`
hasta `group_8` opcionales en la skin seleccionada, las variables generadas
`--raya-graph-group-*` en `skin.css`, las variables inline de chips de grupo,
las custom properties de nodos y aristas SVG, y los paths de marcadores de
flecha. Trata los colores del grafo solo como pistas visuales de legibilidad,
nunca como progreso, ranking, recomendacion ni autoridad del grafo.

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

Para cambios de handout Print/PDF, emula media print en un test de browser.
Verifica que barras de comandos, mapas del curso, rieles de contexto, controles
de workspace, inspectores, filtros y canvas del grafo se oculten solo en print,
mientras contenido del articulo, Page brief, MathJax, codigo, tablas, practica
oficial, objetos numerados y disclosures de soporte sigan legibles. La apertura
temporal de disclosures para print debe restaurarse al volver a media screen y
no debe usar storage, fetch, assets externos ni conversion MathJax en el
browser.

Para checks de autoria de math, usa `examples/courses/render-fixture/course/2_math_authoring/0_index.md` como fixture de fuente enfocado. Verifica paginas de fuente en vez de archivos generados bajo `artifact/`, y usa evidencia de render-debug para confirmar que no hay TeX crudo visible, conversion browser-side MathJax ni requests externos del renderer. El soporte de objeto numerado es comportamiento actual: inspecciona directivas fenced, IDs duraderos, anclas renderizadas, referencias abreviadas `@id`, referencias explicitas `raya:ref/id` y el index `data/numbered-objects.json` declarado en manifest en vez de buscar soporte LaTeX `\label` o `\ref`.

Cuando un problema de rendering cruce math, objetos numerados, skins, referencias, entornos estaticos y assets locales, inspecciona primero `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md`, despues pasa a la pagina fixture especializada de la superficie que falla.

Para la estructura del curso basada en ciencia del aprendizaje, conserva
restricciones de fuente y autoridad actual del artifact. El articulo principal
puede terminar con un bloque Page connections generado desde contexto explicito
del grafo de enlaces de contenido entrantes y salientes. El riel derecho puede
renderizar contenidos de pagina actuales, metadata normalizada, prerrequisitos
por ID estable, enlaces anterior/siguiente, contexto de seccion actual derivado
de anchors de heading activos, resumenes estaticos de Connections
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
en grafo solo cuando exista contexto de grafo. Verifica las regiones de
workspace de controles, resultados y contexto en desktop y movil. Confirma que
no haya rutas privadas de fuente, rutas de soporte, duplicados ocultos de
respuestas, requests externos, `fetch` en runtime, localStorage/sessionStorage
de estado de practica, scoring, submissions, attempts, grading, progreso,
dominio, recomendacion, adaptacion ni lenguaje de estado del estudiante. Las
preferencias compartidas Text size y `OpenDyslexic` pueden usar solo el recurso
local de accesibilidad.
Cuando cambie este workspace, verifica tambien la paridad de inspeccion de
objeto activo: los objetos visibles exponen `data-raya-practice-active`, hover
y foco en links existentes del item actualizan el panel de contexto, el
movimiento de teclado desde el input de busqueda selecciona un objeto visible,
Enter abre el link `.raya-practice-open` de ese objeto, los handoffs
`?page=<page-id>` desde Search o Graph muestran inicialmente solo objetos
propiedad de esa pagina, y Clear/Escape reinician el estado activo transitorio
y el foco de pagina. No hagas que las cards de objeto sean tab stops extra solo
para soportar inspeccion.

Para el workspace Official Tasks, inspecciona objetos aceptados bajo
`_official/assignments/`, `_official/projects/`, `_official/exams/` y
`_official/tasks/`, despues compara `data/tasks.json`, `manifest.json`,
`_raya/tasks/index.html` y el script local `tasks.js`. La metadata publica de
planeacion debe venir de campos `content` del objeto como `due`, `available`,
`points`, `weight`, `status` y `tags`. Verifica anchors de pagina, links de
foco en grafo, filtros, ordenamiento, Enter por teclado para abrir, paneles
responsivos, sin rutas privadas, sin `fetch` en runtime, sin requests externos,
sin browser storage y sin lenguaje de grading, entregas, progreso, dominio,
recomendacion o estado del estudiante.

Para el workspace Official Schedule, inspecciona los mismos objetos aceptados
de familia task y verifica que solo objetos con `content.due` o
`content.available` publico aparezcan en `_raya/schedule/index.html`. Compara
el payload embebido con la semantica de `data/tasks.json` y el script local
`schedule.js`. Verifica filtros por tipo y evento, busqueda, Enter por teclado
para abrir, anchors de pagina propietaria, links de foco en grafo, paneles
responsivos, sin rutas privadas, sin `fetch` en runtime, sin requests externos,
sin browser storage, y sin sincronizacion de calendario, recordatorios,
grading, entregas, progreso, dominio, recomendacion o lenguaje de estado del
estudiante.

Al cambiar la shell, verifica el mapa del curso expandido por defecto, incluida
la estructura de mapa jerarquico del curso expandido, los numeros estructurales
generados del mapa,
la orientacion de pagina actual dentro del mapa, el comportamiento del filtro
del mapa, el contexto superior de lectura, los links compactos
anterior/siguiente, las breadcrumbs lectoras, las cards Previous/Next al final
del articulo, la metadata del riel compacto operable, la salida de render-debug,
el comportamiento movil sin overflow y sin solicitudes externas. Las
breadcrumbs deben mostrar home del curso, paginas ancestro y pagina actual con
markup de navegacion accesible, links estaticos neutrales al despliegue, marca
de pagina actual, sin rutas de fuente y sin rutas privadas de soporte. El estado
del mapa del curso, el texto
del filtro y el contexto de lectura son UI no persistente; la orientacion de
pagina actual en el mapa tambien debe seguir no persistente y no debe restaurar
storage de navegacion legacy. Trata la posicion de pagina en la barra superior y
en las cards de secuencia como orientacion estructural del curso, no como
progreso del estudiante.
Si la shell expone contexto de seccion actual, verifica que se genere desde los
contenidos de pagina y anchors de heading, que se actualice con el heading activo
en tests de browser, que siga siendo un enlace local normal, que no escriba
storage del browser y que no use lenguaje de porcentaje leido, finalizacion,
dominio, recomendacion o progreso.
Si una pagina no tiene `estimated_time` escrito, verifica que cualquier
`Estimated read time` mostrado en el Page brief o riel derecho se calcule
durante build desde texto publico del articulo, no use storage del browser ni
fetch runtime, y siga siendo orientacion aproximada, no progreso, dominio,
recomendacion ni personalizacion. Cuando exista `estimated_time`, debe tener
precedencia como `Estimated time`.
Si la shell expone `Focus reading`, verifica que sea accesible por teclado,
colapse juntos en desktop el mapa del curso y el riel derecho, pueda volver al
layout expandido, no cambie el estado de URL y no escriba storage del browser.
Si la shell expone un comando superior `Context`, verifica que alterne solo el
riel derecho en desktop, mantenga disponible el mapa del curso, sincronice
`aria-expanded` y labels con los controles del riel, permanezca oculto en tablet
y movil, y no escriba storage del browser ni estado de progreso o recomendacion.
Para cambios responsivos de la shell, revisa juntos los viewports desktop,
tablet y movil. En desktop el riel derecho de aprendizaje puede colapsar a una
pestana compacta de contexto, pero en tablet y movil el cuerpo del riel debe
seguir visible y alcanzable por tecnologias asistivas cuando los controles de
colapso estan ocultos. Presionar Escape dentro del riel en movil no debe dejar
`aria-hidden`, `inert` ni contenido enfocable oculto. El estado de colapso u
orientacion de la shell no debe escribir `localStorage` ni `sessionStorage`;
solo preferencias explicitas de comodidad como tamano de texto u
`OpenDyslexic` pueden persistir.
Cuando cambie el drawer Course map en tablet/movil, verifica chrome visible del
drawer, posicion estructural de pagina cuando exista, boton de cierre, cierre
por backdrop, cierre por Escape, restauracion de foco al opener, contencion de
foco mientras esta abierto, estado cerrado con `aria-hidden`/`inert`, scroll
lock de fondo solo mientras esta abierto, limpieza del scroll lock al cerrar o
al volver a desktop, sin escrituras de storage, sin requests externos y
disponibilidad del articulo y riel derecho despues de cerrar.
Cuando cambien los rieles lectores colapsados, verifica que las pestanas
desktop Map y Context usen labels visuales horizontales estables, sigan siendo
operables por teclado mediante sus controles existentes, aumenten el ancho del
articulo, permanezcan ocultas en tablet/movil cuando sus controles desktop
esten ocultos, y no agreguen storage, fetch, progreso, recomendacion ni estado
del estudiante. Cuando cambien controles de comodidad del shell, verifica que
reduced-motion desactive transiciones no esenciales y que las regiones
colapsadas de escritorio salgan de la navegacion por teclado y asistiva como se
especifica.
Al cambiar las cards de atajo Course workspace, verifica etiquetas, badges
estructurales, hrefs neutrales al despliegue, hrefs de Practice enfocados en
pagina solo cuando haya propiedad directa de objetos oficiales, hrefs de
Schedule y badges de tareas fechadas solo desde tasks oficiales fechadas
directas, ocultamiento en
mapa colapsado, comportamiento desktop/movil sin overflow, y ausencia de
storage, fetch, progreso, ranking, recomendacion o lenguaje de estado del
estudiante.

El Page brief es parte de la shell lectora. Verifica que aparezca antes del
contenido autorado cuando exista metadata publica, que use resumen/status/tags
escapados, links de prerrequisitos resueltos, links de grafo enfocados en la
pagina y anchors de practica oficial, y que no exponga rutas de fuente, rutas
privadas, `fetch` en runtime, storage del browser, progreso, dominio,
recomendaciones, evaluacion, personalizacion ni lenguaje de estado del
estudiante.

Al cambiar indices generados de seccion, verifica markup de cards de entrada,
navegacion normal con enlaces locales, comportamiento desktop/mobile sin
overflow y ausencia de lenguaje de recomendaciones/progreso/dominio dentro de la
superficie del indice generado.

Al cambiar el grafo del curso, verifica busqueda aproximada, detalles de pagina
seleccionada, resumenes de vecindario de pagina seleccionada, estados visuales
de paginas conectadas, filtros de grupo, semantica de color por grupo, colores
de arista por grupo de pagina fuente, atenuacion transitoria por spotlight
hover/foco, spotlight transitorio de busqueda sobre paginas coincidentes y
contexto directamente conectado, tamano de nodo acotado por grado, estado de inspeccion por hover/foco, paridad de
inspeccion con teclado, modo de foco de vecindario seleccionado, controles de paginas
conectadas en el detalle que cambian la seleccion del grafo sin reemplazar los
enlaces normales de pagina, cards de relationship walkthrough de pagina seleccionada que
explican tipo y direccion de edge explicitos sin lenguaje de recomendacion,
botones relationship chip que enfocan transitoriamente esas cards por tipo y
direccion con `aria-pressed` y sin escribir URL ni storage,
reveal contextual de labels SVG para paginas seleccionadas, inspeccionadas,
vecinas, de busqueda, resultado activo, arrastre y alto grado,
layout determinista `Connections` por defecto,
layouts alternos `Topology`, `Cluster`, `Map`, `Radial` y `List`, estado de area de trabajo
expandida del grafo, controles SVG de viewport incluyendo botones de pan,
pan con `Arrow keys` cuando el grafo tiene foco, atajos del grafo para `/`
enfocar busqueda, `F` ajustar y `R` resetear sin interceptar escritura en
campos, pan por arrastre del puntero, chrome compartido de
descubrimiento, chrome movil compacto, comportamiento movil sin overflow y sin
solicitudes externas despues de cargar la pagina. El
estado UI del grafo es no persistente y debe venir de datos de grafo embebidos
del artifact, no de HTML scrapeado ni almacenamiento del navegador. El estado
del grafo en la URL puede codificar pagina seleccionada, busqueda, layout,
grupos visibles, tipos de edge visibles, foco de vecindario seleccionado, modo
expandido y estado de paneles. Verifica que el readout compacto de estado del
grafo y la URL del navegador se mantengan sincronizados despues de cambios de
controles, que usen solo estado estructural publico, que puedan vivir dentro de
un disclosure nativo cerrado por defecto, y que no escriban `localStorage` ni
`sessionStorage`. El contexto de URL generado puede seleccionar una pagina solo cuando resuelve a un nodo embebido
del grafo. Los conteos de vecindario deben derivarse de edges del grafo
generado, y los resaltados de pagina conectada deben excluir el nodo
seleccionado. El foco de vecindario seleccionado puede reducir el grafo y la lista
visibles a la pagina seleccionada mas paginas directamente conectadas, pero debe
seguir transitorio, reversible y sin almacenamiento de estado del grafo, llamadas `fetch`,
librerias externas de grafo, lenguaje de recomendacion, progreso, ranking o
dominio. Las posiciones de la disposicion del grafo son solo ayudas de lectura sobre
datos generados explicitos. `Topology` es una vista estatica de lectura sobre
relaciones explicitas generadas del grafo y el conjunto actual de edges visibles;
las posiciones no deben venir de librerias externas de grafo ni
implicar recomendacion, progreso, ranking, importancia, dominio o autoridad.
Los conteos del riel Connections deben venir solo de contexto
explicito del grafo. Los enlaces de foco al grafo en el riel deben apuntar solo
a prerequisitos explicitos o contexto de grafo entrante/saliente.
Zoom in, Zoom out, Fit, Fit selection, Reset view y la activacion del minimapa
pueden cambiar el `viewBox` SVG; no deben pedir datos del grafo, persistir
estado del grafo, limpiar detalles de pagina seleccionada ni quedar habilitados
cuando el grafo SVG esta oculto por el layout de lista. Cuando cambie la
activacion del minimapa, verifica que click y teclado muevan el viewport del
canvas principal sin limpiar seleccion, filtros, URL ni storage. Para el ajuste de pagina seleccionada, verifica
que `Fit selection` este deshabilitado sin pagina seleccionada y en layout de
lista, se habilite despues de seleccionar una pagina, mantenga intactos
detalles de pagina seleccionada, busqueda, filtros y estado de URL, encuadre la
pagina seleccionada mas al menos una arista conectada visible cuando exista, y
lleve el canvas del grafo al viewport visible del navegador cuando el canvas
haya quedado debajo del area visible inicial.
Los conteos y enlaces de Page connections del articulo tambien deben venir solo
de contexto explicito del grafo de enlaces de contenido entrantes/salientes,
permanecer dentro del articulo y evitar rutas de fuente, rutas privadas de
soporte, URLs externas, requests fetch, llamadas a storage, progreso, dominio,
recomendaciones y lenguaje de ranking.
Las vistas previas de Page connections en el riel y el articulo deben usar solo
metadatos publicos generados de pagina: titulo, resumen, estado, URL local de
la pagina, URL de foco en grafo, tipo y direccion explicitos de relacion, y
conteos explicitos entrantes/salientes. Los previews de conexion pueden
etiquetar tipo y direccion de relacion, como `Content` y `From this page`,
usando solo contexto explicito generado del grafo. Verifica comportamiento de
controles nativos de despliegue, texto escapado, sin rutas privadas, sin
almacenamiento del navegador, sin fetch, sin solicitudes externas y sin
lenguaje de recomendacion, avance o maestria.
Trata color, color de arista por grupo fuente, tamano, spotlight de busqueda,
atenuacion de spotlight y texto de inspeccion del grafo como pistas de legibilidad estructural;
no introduzcas progreso, dominio, recomendaciones, rankings, estado persistente
del grafo, librerias externas de grafo, requests fetch ni payloads de grafo en
runtime.
Para handoffs desktop de Graph enfocados por pagina como `?page=<page-id>`,
verifica que el nodo SVG seleccionado y al menos una arista sean realmente
visibles dentro del canvas del grafo en el primer render. No aceptes solo
checks del DOM que pasan aunque el canvas este tan alto que el grafo aparece
fuera del area visible inicial.
Tambien verifica la banda de orientacion del grafo cuando cambies Graph. Sus
conteos visibles, layout, pagina seleccionada, foco de pagina, busqueda,
filtros, foco de vecindario y acciones de pagina seleccionada deben derivarse
de datos embebidos del grafo y estado transitorio del DOM. La banda no debe usar
storage, hacer fetch de datos de grafo en runtime ni introducir lenguaje de
progreso, dominio, ranking, recomendacion o personalizacion. Las listas de
enlaces entrantes/salientes de pagina seleccionada, chips de relacion y cards
del walkthrough deben coincidir sobre los tipos explicitos de aristas generadas.
Al cambiar Graph, verifica movimiento con teclado en graph search sobre
resultados de pagina visibles, inspeccion de active result, Enter para abrir,
seleccion por click simple en nodos SVG del grafo sin navegar de pagina,
apertura de pagina por doble click en nodos SVG del grafo, Enter para abrir
nodos SVG del grafo con foco, link primario para abrir la pagina seleccionada,
pan del viewport del grafo y detalles de pagina seleccionada como ayudas
locales y transitorias de navegacion solamente.

Al cambiar Course Search, verifica coincidencia aproximada, movimiento con
teclado por resultados, inspeccion de resultado activo por hover/foco, Enter
para abrir, controles de limpiar, chrome compartido de descubrimiento, regiones
de workspace de controles, resultados y contexto, chrome movil compacto, sin solicitudes externas y sin estado
persistente de busqueda. Los payloads de busqueda pueden incluir metadata
publica generada y prosa publica renderizada del articulo, pero deben excluir
rutas de fuente, rutas privadas de soporte, rutas de artifact, internos de
MathJax, TeX crudo, cache keys, contenido solo de respuestas/soporte y estado
del estudiante. El contexto de consulta generado y los resumenes del panel de
contexto deben permanecer transitorios. El foco exacto de pagina Search desde
`?page=<page-id>` puede reducir inicialmente los resultados visibles a un ID
publico de pagina; Clear y Escape deben restaurar todos los resultados visibles
sin escribir storage del navegador ni cambiar autoridad de fuente, incluso
cuando el foco esta en un link de resultado visible o una accion de contexto en
vez del input de busqueda. Los enlaces
graph-focus de resultados de busqueda deben venir de stable IDs y URLs locales
generadas del grafo, preservar Enter para abrir la pagina, y evitar lenguaje de
recomendacion o progreso. Las paginas de descubrimiento Search, Graph, Practice
y Tasks pueden cargar recursos locales de accesibilidad para Text size y
`OpenDyslexic`, pero no deben cargar `shell.js`, un toggle de mapa del curso,
assets externos de workspace ni estado persistente de graph/search/practice/tasks.
Cuando cambie Course Search, verifica subresultados de seccion ademas de
resultados de pagina. Los records generados pueden apuntar a anchors publicos de
headings u objetos numerados renderizados, pero no deben incluir TeX crudo,
MathJax CHTML, rutas privadas, texto de respuestas/soporte, internos de artifact
ni lenguaje de estado del estudiante.

Al cambiar Tasks o Schedule, verifica handoffs solo por URL
`?page=<page-id>` desde Search o Graph. El workspace destino puede reducir
inicialmente los objetos publicos de la familia task a la pagina solicitada,
mostrar un aviso compacto con el titulo publico de la pagina y el conteo
visible, pero Clear y Escape deben ocultar ese aviso y restaurar el workspace
estatico completo sin escribir storage del navegador ni cambiar la autoridad de
fuente. Escape debe funcionar desde links de resultados o acciones de contexto
enfocados, no solo desde el input de busqueda. Trata el query de pagina como
contexto transitorio de navegacion, no como progreso,
recomendacion, dominio, calificacion ni estado personal de fechas.

Al cambiar cards de descubrimiento de Search o Graph, verifica que los payloads
embebidos y las cards visibles usen solo datos publicos generados: titulo de
pagina, nav title, stable ID, hierarchy label, status, summary, tags, prosa
publica renderizada del articulo para Search, anchors y snippets publicos
generados de secciones u objetos para subresultados de Search, enlaces
anterior/siguiente del orden del curso, conteos explicitos de enlaces del grafo,
conteos de objetos oficiales aceptados y enlaces relativos a paginas propietarias o workspaces
generados. Confirma que no haya rutas de fuente, `_official/`, `_assets/`,
`_reviewed/`, internos de artifact, cache keys, internos de MathJax, TeX crudo,
contenido de respuestas/soporte, `fetch` en runtime, storage de search/graph,
requests externos, recomendacion, progreso, dominio, completion, ranking ni
lenguaje falso de practica relacionada. Enter en Search debe seguir abriendo la
pagina del resultado, mientras los detalles de pagina seleccionada en Graph
pueden ofrecer enlaces separados hacia Search y Practice. Los enlaces de
handoff a Search deben incluir `?page=<page-id>` para foco exacto en una pagina
publica. Los enlaces de handoff a Practice deben incluir `?page=<page-id>` solo
cuando la pagina posee objetos oficiales aceptados, y ese foco de pagina debe
permanecer como estado solo de URL.

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
