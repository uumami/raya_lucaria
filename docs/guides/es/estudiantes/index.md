---
id: docs-guides-es-estudiantes
title: Estudiantes
summary: Guia para leer artifacts estaticos, estudiar, mantener trabajo portable y entender autoridad.
status: ready
---
# Estudiantes

Los estudiantes deben poder leer artifactos estaticos de curso, estudiar con objetos oficiales de aprendizaje, mantener portable su trabajo personal y entender si un material es oficial, personal, compartido, generado o aceptado.

Las paginas estaticas de curso son utiles sin cuentas. Estado dinamico de estudio, colas de repaso y colaboracion son mejoras progresivas futuras.

Los cursos renderizados ocultan la mecanica de nombres de archivo. Los estudiantes deben ver titulos limpios, etiquetas de jerarquia, resumenes, breadcrumbs, enlaces anterior/siguiente, indices generados de seccion, anexos, prerequisitos y conteos de objetos oficiales de estudio cuando el curso provee esa metadata.

Los indices generados de seccion aparecen como cards de entrada para paginas
hijas. Son un mapa de estructura del curso desde el artifact actual, no progreso
personal, finalizacion, dominio ni recomendaciones sobre que estudiar despues.

Las paginas estaticas pueden incluir math pre-renderizada, codigo resaltado, botones de copiado en bloques de codigo fenced, tablas, callouts, footnotes, heading anchors y contenidos de pagina. La math debe aparecer ya compuesta en la pagina generada y no debe requerir CDN, cuenta, backend ni conversion MathJax en el browser. El codigo mostrado no se ejecuta en la pagina estatica salvo que un curso futuro agregue un workflow de ejecucion aceptado.

Algunas paginas muestran un Page brief cerca del inicio. Resume metadata publica
del curso como resumen, status, posicion de pagina, tiempo estimado escrito por
el equipo del curso o una estimacion aproximada de lectura, tags,
prerrequisitos, conexiones explicitas de pagina y practica oficial disponible.
Usalo para orientarte rapido. No es registro de progreso, recomendacion, nota,
estimacion de dominio ni siguiente paso personalizado.

Algunos cursos usan skins para presentacion visual o para enfatizar una unidad,
lab, apendice, seccion de practica o seccion de repaso. Una skin no cambia la
autoridad de fuente, etiquetas, enlaces, estado oficial/generado, tareas ni el
trabajo que el curso te pide completar. Si dos secciones se ven diferentes, usa
el titulo de pagina, enlaces y etiquetas como significado del curso; la skin solo
es enfasis visual.

Las paginas renderizadas pueden incluir botones `Text size` y `OpenDyslexic` en
la parte superior. Son preferencias de lectura locales que guarda tu navegador
para ese sitio estatico; cambian la escala del texto o la fuente para facilitar
lectura. Cada preferencia de lectura no cambia contenido, evaluacion, enlaces,
identidad de skin ni
etiquetas de autoridad.

Puedes imprimir una pagina generada o guardarla como PDF cuando quieras un
handout para leer o anotar sin conexion. El modo print quita la chrome del
curso y mantiene legibles el contenido, la math, el codigo, las tablas, la
practica oficial y las notas de soporte. No envia trabajo, no guarda progreso,
no estima dominio ni contacta servicios externos.

La estructura actual del curso es una ayuda de lectura estatica. En escritorio,
el mapa del curso expandido se renderiza como un mapa jerarquico del curso
expandido y puede mostrar numeros estructurales de secuencia del orden del
curso. Da orientacion por defecto, la barra superior mantiene visibles el
titulo del curso, el titulo de la pagina actual y la posicion estructural de la
pagina, el articulo principal sigue siendo la leccion, y el riel de aprendizaje
ofrece contenidos de pagina y contexto cercano. Puedes colapsar el mapa a un
riel compacto operable cuando quieras mas espacio de lectura; esa eleccion es
no persistente y no guarda ni muestra progreso personal. En desktop, los rieles
colapsados de mapa y contexto aparecen como pestanas compactas para que puedas
restaurarlos sin perder el articulo. Los controles Map, Focus reading y Context
son herramientas de comodidad de lectura. Pueden ampliar el articulo o restaurar
el contexto alrededor sin guardar un estado personal de avance.
Cuando una pagina tiene tabla de contenidos, el riel de aprendizaje tambien
puede mostrar la seccion actual del articulo mientras haces scroll. Esa etiqueta
solo orienta por encabezados de la pagina; no es porcentaje leido, marca de
finalizacion ni registro de progreso.
Cuando un mapa largo se abre, la pagina puede mover el enlace de la pagina
actual a la parte visible del mapa. Esa orientacion es contexto temporal de
lectura, no estado guardado.

La barra superior tambien puede incluir un campo pequeno de busqueda del curso.
Escribir ahi abre el workspace generado Course Search con tu consulta; la pagina
de lectura no crea un segundo indice, no hace fetch de resultados ni guarda el
texto como estado de estudio. Usalo como salto rapido cuando recuerdes una
frase, teorema, titulo de pagina o stable ID mientras lees.

Usa el boton del mapa del curso para colapsar o expandir la navegacion cuando
necesites otro foco. En desktop, `Focus reading` puede colapsar juntos el mapa y
el riel derecho para dar mas espacio al articulo; es estado visual temporal y no
guarda progreso. En desktop, `Context` puede ocultar o restaurar solo el riel
derecho mientras deja disponible el mapa del curso; tambien es estado temporal
de layout, no progreso ni personalizacion. En tablet y movil, el boton Course
map abre un drawer temporal con titulo propio, posicion de pagina, filtro,
atajos de workspace y boton de cierre. Mientras el drawer esta abierto, la
pagina de fondo pausa el scroll para que el mapa sea mas facil de usar; cierralo
con el boton de cierre, el backdrop o Escape para volver el foco a la lectura.
Usa el filtro del mapa para limitar etiquetas de paginas
visibles dentro de la jerarquia estatica actual. Usa Anterior y Siguiente en el
articulo, en el contexto superior de lectura o en las cards al final de pagina
para moverte por el material ordenado, y usa Text size u OpenDyslexic cuando
esos ajustes sean mas comodos. Las cards al final de pagina son enlaces del
orden del curso; no son recomendaciones ni marcadores de progreso.
El mapa expandido del curso tambien puede mostrar enlaces estaticos a Course
Search, Course Graph, Official Practice, Official Tasks y Official Schedule. Son atajos a
workspaces generados, no progreso, ranking ni guia personalizada. Algunas cards
de atajo incluyen badges estructurales pequenos como alcance de curso, conteos
de enlaces explicitos, conteos de objetos oficiales aceptados o conteos de
tareas aceptadas o tareas oficiales fechadas para la pagina actual. Esos badges describen estructura
estatica autorada del curso; no son senales de finalizacion, importancia, nota
ni recomendacion.

Usa el Course graph para inspeccionar relaciones generadas entre paginas. Su
busqueda, filtros, detalles de pagina seleccionada, Zoom in, Zoom out, Fit,
Reset view y workspace expandido del grafo son herramientas locales de lectura
sobre la estructura actual del curso. No guardan progreso, no recomiendan que
estudiar despues y no cambian la autoridad del curso. Fit y Reset view solo
cambian la vista visual del grafo; la lista y los detalles de pagina
seleccionada siguen disponibles. Abrirlo desde una pagina del curso puede
enfocar esa pagina para ver primero sus enlaces explicitos. El riel de
aprendizaje tambien puede mostrar un panel Connections con conteos de enlaces
que salen de la pagina actual y enlaces que apuntan a ella; esos conteos
describen relaciones estaticas autoradas, no recomendaciones ni progreso
personal. Los detalles `Graph state` y share URL pueden estar dentro de un
disclosure para que el flujo principal del grafo mantenga foco en busqueda,
canvas y contexto de pagina seleccionada.
La barra del grafo agrupa controles como `Find pages`, `Relationship filters`,
`Canvas view`, `Move canvas` y `Workspace`. Usa `Find pages` para buscar o
cambiar layout, `Relationship filters` para mostrar u ocultar tipos de enlaces
explicitos, `Canvas view` y `Move canvas` para ajustar la vista SVG, y
`Workspace` para resetear o enfocar la superficie del grafo. Son herramientas
temporales de inspeccion; no reescriben enlaces del curso ni guardan estado de
estudio.
Cuando no estas escribiendo en un campo, `/` enfoca la busqueda del grafo, `F`
ajusta la vista actual y `R` resetea filtros y seleccion del grafo.
En pantallas anchas con mouse, tambien puedes reposicionar nodos visibles del grafo
para desenredar la vista actual. Es solo limpieza visual temporal:
Reset graph restaura el layout generado, Fit y zoom mantienen legible la vista
movida, y el movimiento no es un editor de layout, cambio de datos del curso,
preferencia guardada, recomendacion, progreso, dominio ni senal de autoridad.
El grafo tambien puede mostrar una banda de orientacion cerca del canvas.
Nombra el layout actual, pagina seleccionada, foco de pagina, contexto de
busqueda y filtros, y si el foco de vecindario esta activo. Usa sus acciones
Open page, Focus neighborhood, Show full graph y Clear selection como controles
locales del grafo; la banda no es progreso guardado, ranking, dominio ni
recomendacion.
En pantallas anchas, pasar el puntero sobre un nodo del grafo o enfocarlo puede
mostrar una vista previa pequena cerca del nodo con titulo de pagina, contexto
estatico, resumen y conteos de enlaces explicitos. Usala como ayuda rapida de
lectura; el panel inspector y los enlaces normales de pagina siguen siendo la
forma estable de inspeccionar o abrir la pagina.
Algunas paginas tambien pueden terminar con un bloque Page connections dentro
del articulo. Usa los mismos datos estaticos de relaciones para mostrar paginas
enlazadas desde la leccion, paginas que enlazan de vuelta a ella, y un enlace
Open in course graph. Los elementos de conexion pueden abrir vistas previas
nativas con el resumen, estado y conteos de enlaces explicitos de la pagina
enlazada cuando el curso tiene esos metadatos. Tambien pueden etiquetar tipo y
direccion de relacion, como `Content` y `From this page`, usando solo contexto
explicito generado del grafo. Usalos como mapa de lectura despues de terminar
la pagina; no son un registro de avance, ranking ni motor de recomendaciones.
Las paginas Search, Graph, Practice, Tasks y Schedule usan la misma barra estatica de
descubrimiento para volver al curso, cambiar entre esos workspaces y mantener
disponibles Text size u OpenDyslexic para la pagina actual. Search, Practice y
Tasks y Schedule tambien pueden mostrar controles, resultados y un panel de contexto en
pantallas anchas. Esos controles son de comodidad de lectura y escaneo; los
workspaces no guardan tu consulta, nodo seleccionado, layout del grafo, filtros
de practica, filtros de tareas ni filtros de Schedule como estado de estudio.
Los filtros de texto pueden tolerar errores pequenos de escritura al comparar
titulos publicos, tags, resumenes, labels y texto visible de objetos. Esa
coincidencia es comportamiento local de la pagina, no ranking, personalizacion
ni recomendacion.
Cuando uno de esos workspaces abre enfocado en una pagina, puede mostrar un
aviso pequeno con el nombre de esa pagina y el numero de resultados visibles.
Clear o Escape quitan ese foco y vuelven al workspace estatico completo,
incluso cuando el foco de teclado esta en un resultado visible o una accion de
contexto en vez del campo de busqueda. El aviso no es progreso guardado ni una
recomendacion.
Los paneles de contexto tambien pueden mostrar links estaticos directos para el
resultado, objeto, task o item de Schedule activo, como Open page, View graph u
otro workspace enfocado en la misma pagina. Son atajos de navegacion sobre datos
publicos generados del curso, no recomendaciones ni estado de estudio guardado.
Cuando una pagina esta seleccionada en el grafo, las paginas conectadas pueden
resaltarse y resumirse como enlaces salientes, enlaces entrantes y paginas
conectadas. Esos numeros describen el grafo estatico actual, no tu avance.
Los detalles de pagina seleccionada tambien pueden mostrar un Relationship
walkthrough que agrupa enlaces por tipo de relacion y direccion. Usalo para ver
por que una pagina esta conectada y para enfocar otra pagina conectada sin salir
del workspace del grafo. Los relationship chips pueden reducir temporalmente
ese walkthrough a un tipo y direccion de enlace, incluyendo las listas de
enlaces de la pagina seleccionada y las aristas visibles que coinciden.
Presionar el mismo chip o `Show all relationships` restaura el walkthrough
completo. Si `Relationship filters` oculta globalmente un tipo, el chip de la
pagina seleccionada puede mostrar que ese tipo esta oculto por el filtro actual;
es estado temporal de inspeccion, no estado de estudio guardado.
Los colores del grafo agrupan paginas por la estructura actual del curso, el
tamano del nodo puede mostrar cuantos enlaces explicitos tocan una pagina, y el
grafo puede mantener visibles solo labels de alto contexto hasta que selecciones,
busques, hagas hover o enfoques paginas cercanas con teclado. El hover o foco de teclado puede inspeccionar temporalmente una pagina y sus
paginas conectadas. Los equipos de curso pueden elegir una paleta de grafo
mediante la skin del curso, asi que los colores pueden verse distintos entre
cursos o secciones manteniendo el mismo significado estructural. Son pistas
estaticas de legibilidad, no rankings de
importancia, progreso, dominio, recomendaciones ni senales de evaluacion.

Usa Course Search cuando recuerdes un titulo, tag, status, frase de resumen,
stable ID o frase del articulo publico. Busca metadata publica generada y prosa
publica renderizada del articulo, soporta coincidencias aproximadas e
inspeccion con teclado, hover y foco de resultados visibles, y no busca rutas
ocultas de fuente, rutas privadas de soporte, internos de MathJax, respuestas
ni tu estado personal. Los resultados pueden mostrar coincidencias de seccion
que saltan a anchors publicos generados de la pagina, incluidos objetos
numerados como theorem, figure, table, homework o assignment cuando el curso los
renderizo. Abrirlo desde una pagina del curso puede precargar el
titulo de esa pagina como consulta temporal, y el campo de busqueda de la barra
superior puede abrirlo con el texto que escribiste. Un resultado tambien puede ofrecer
`View in graph`, que abre Course Graph enfocado en esa misma pagina para
inspeccionar su posicion en el curso y sus enlaces explicitos. El panel de
contexto de Search resume contexto publico del resultado que inspeccionas; no
es un ranking ni una recomendacion. Cuando un resultado tiene practica oficial
aceptada, tambien puede abrir Official Practice enfocada en esa pagina. Ese
foco de pagina es solo contexto de URL; limpiar Practice o presionar Escape
vuelve a todos los objetos oficiales visibles.

Si la math aparece como comandos TeX crudos como `\begin{bmatrix}` o una macro desconocida en una pagina publicada, tratalo como un problema de rendering para reportar al equipo del curso, no como un paso que debas arreglar en tu browser.

Matrices renderizadas, vectores, notacion de conjuntos, notas tipo theorem y pruebas deben aparecer como texto normal del curso mas matematica compuesta. Si ves `\begin{bmatrix}` crudo, una macro desconocida, matematica visible con delimitadores de dolar, o una pagina que pide cargar browser-side MathJax, reportalo al equipo del curso con la URL o titulo de la pagina.

Las paginas de curso pueden incluir objetos numerados y referencias estaticas. Un resultado puede aparecer como `Teorema 2.3.1`, una imagen como `Figura 2.3.1`, y el trabajo de practica como referencia de tarea, problema, actividad o assignment. Los objetos numerados deben aparecer como contenido de curso escaneable cuando corresponda: objetos tipo teorema, ejemplos, ejercicios y tareas usan `scannable` de forma predeterminada, mientras figuras y tablas conservan `caption` y ecuaciones conservan `equation`. Estos numeros, etiquetas, anchors y referencias se generan durante el build y se publican como enlaces estaticos; tu browser no deberia calcularlos ni cargar un servicio vivo de referencias.

El contenido numerado aparece como etiquetas y enlaces estaticos, por ejemplo `Theorem 3.1`, `Figure 3.1` o `Activity 3.3`. Los encabezados de prueba como `Proof of Activity 3.3` se generan durante build; el browser no calcula referencias.

Algunos equipos de curso escriben enlaces internos con sintaxis `[[...]]`. En
el curso publicado, deben aparecer como enlaces normales de pagina antes de que
veas la pagina. Si aparece texto crudo `[[target]]` en una pagina publicada,
reporta el titulo o URL de la pagina al equipo del curso.

Los encabezados de prueba renderizados nombran el objeto que se esta probando, y la matematica dentro de la prueba debe aparecer ya compuesta durante el build. La pagina no deberia necesitar un request de browser-side MathJax para mostrar la prueba. Si ves sintaxis de fuente cruda o TeX crudo en vez de una prueba renderizada, reportalo al equipo del curso con la URL o titulo de la pagina.

Las pruebas, soluciones, pistas y respuestas deben aparecer como contenido
estatico del curso. Las pruebas permanecen abiertas cuando forman parte de la
explicacion. Las pistas, soluciones y respuestas pueden iniciar colapsadas para
que las abras solo cuando quieras apoyo. Abrir una no envia una respuesta, no
guarda progreso, no contacta un backend y no pide al browser renderizar MathJax.
Cuando un bloque nombra un teorema, problema, actividad, tarea, figura, tabla o
ecuacion, ese encabezado ya debe estar resuelto antes de que la pagina llegue al
navegador.

Algunas paginas pueden incluir una seccion `Official practice` renderizada desde
el material `_official/` propio de esa pagina. Cards, prompts, quizzes y otros
campos oficiales se muestran como apoyo estatico de lectura en la pagina que los
posee. Los controles de revelar son controles locales del browser; abrir uno no
envia trabajo, no guarda respuestas, no crea attempts, no actualiza progreso, no
cambia dominio, no contacta un backend, no hace fetch de mas datos y no pide al
browser renderizar MathJax.

Algunos cursos tambien pueden incluir un workspace Official Practice bajo
`_raya/practice/`. Usalo para encontrar cards, prompts, quizzes, tasks y otros
objetos oficiales aceptados en todo el curso, y despues vuelve a la pagina que
los posee para ver el contexto. Los items de Practice deben enlazar a anchors
de pagina como `#raya-official-<id>` y pueden ofrecer links `View in graph`.
Puedes inspeccionar items visibles de Practice con movimiento de teclado, hover
o foco en los links del item; el panel de contexto sigue esa seleccion
temporal. El workspace es una superficie estatica de descubrimiento con
filtros, resultados y resumenes publicos de contexto, y Search o Graph pueden
abrirlo ya filtrado a una pagina con `?page=<page-id>`. Clear o Escape quitan
ese foco temporal de pagina; no se guarda como estado de estudio. Cuando un
workspace se abre enfocado en una pagina, puede mostrar un aviso pequeno con el
titulo publico de esa pagina y el conteo visible. Ese aviso desaparece con
Clear o Escape; no es progreso guardado ni recomendacion. No es un
motor de recomendaciones, registro de progreso, sistema de entregas, sistema de
evaluacion, scoring, registro de attempts, estimacion de dominio, estado de
practica guardado, workflow de requests externos, visor de rutas privadas de
fuente ni cola personal de repaso.

Algunos cursos tambien pueden incluir un workspace Official Tasks bajo
`_raya/tasks/`. Usalo para escanear assignments, projects, exams y tasks
aceptados por texto, coincidencia aproximada de texto, tipo, orden del curso o
fecha de entrega, y despues abre la pagina que los posee para ver el contexto completo. Puede mostrar campos
publicos de planeacion como titulo, pagina, fecha de entrega, puntos, status y
tags cuando el equipo del curso los escribio. Search o Graph pueden abrir Tasks
enfocado en una pagina, con un aviso visible y reset por Clear o Escape a todos
los tasks visibles. No es registro de progreso
personal, sistema de entregas, gradebook, pagina adaptativa de recomendaciones,
sincronizacion de calendario ni superficie de respuestas ocultas.

Algunos cursos tambien pueden incluir un workspace Official Schedule bajo
`_raya/schedule/`. Usalo para escanear assignments, projects, exams y tasks
aceptados que tienen fechas `due` o `available` por texto, coincidencia
aproximada de texto, tipo de evento o tipo de task, y despues abre la pagina que
los posee para ver el contexto completo. Es una vista estatica fechada sobre
metadata del curso. Search o Graph pueden abrir Schedule enfocado en una
pagina, con un aviso visible y reset por Clear o Escape a todos los items
fechados visibles; no es calendario personal, sistema de recordatorios,
registro de progreso, pagina de recomendaciones, sistema de entregas ni
gradebook.

Algunas paginas pueden incluir scripts o notebooks enlazados. Se copian como archivos legibles y pueden mostrar previsualizaciones de fuente, pero el build estatico los etiqueta como `not-executed`. Los archivos fuente no enlazados no forman parte del artifact de la pagina. Usa las instrucciones del curso cuando una clase espere que ejecutes codigo localmente, en Docker, o mediante un futuro workflow aceptado.

Los ejemplos de codigo fenced pueden incluir un boton `Copy`. Copiar pone el texto de codigo mostrado en tu clipboard; no ejecuta el codigo, no guarda progreso ni contacta un backend.

Algunos cursos incluyen runtime metadata para futura ejecucion local o con Docker. En el artifact estatico actual, esa metadata solo explica perfiles previstos, policies y cache keys. No significa que la pagina web ya ejecuto el codigo.

Cuando un curso te pida ejecutar codigo, usa el target exacto indicado por el equipo del curso, por ejemplo `raya run . manual-script` desde la raiz del curso o el comando Docker que provean. `--dry-run` muestra que se ejecutaria antes de ejecutarlo. Targets con policy `cache` pueden reutilizar output generado previo salvo que el curso pida `--refresh`.

Algunas paginas pueden mostrar paneles de output revisado. Ese output es soporte de curso que el equipo congelo dentro de revision de fuente, por eso puede mostrarse estaticamente sin volver a ejecutar codigo. Es diferente de tu trabajo personal y de logs generados localmente. Si el output revisado esta desactualizado o falta, el artifact del curso debe fallar antes de publicarlo como vigente.

Las paginas estaticas muestran una vista de lectura enfocada. Hashes internos, cache keys, rutas de fuente, rutas de artifact y detalles de runtime quedan fuera del flujo normal; son para profesores, colaboradores, agentes o herramientas que inspeccionan el artifact.

Si un profesor comparte una URL local de preview, es el mismo sitio estatico generado servido desde `artifact/site/`. Abrir una pagina de preview no ejecuta codigo ni notebooks del curso. Sigue instrucciones explicitas del curso cuando el computo sea parte de la clase.

Usa la documentacion de rol como guia. Usa las paginas de curso y objetos oficiales de aprendizaje como material de curso. Si documentacion y material de curso entran en conflicto, el equipo de curso y la autoridad aceptada de specs OpenSpec o `docs/foundation/` deciden que cambia.

La documentacion renderizada del repositorio puede leerse como paginas estaticas, pero sigue siendo guia sobre el framework. No es la misma superficie de autoridad que un artifact oficial de curso.
