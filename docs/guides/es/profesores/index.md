---
id: docs-guides-es-profesores
title: Profesores
summary: Guia para poseer fuente de curso, material oficial, revision y publicacion.
status: ready
---
# Profesores

Los equipos de curso poseen la fuente del curso, el material oficial, la revision y las decisiones de publicacion. Empieza con `docs/foundation/05_course_contract.md`, `docs/foundation/04_ownership_permissions.md` y `docs/foundation/03_pedagogy.md`.

Los ejemplos son fixtures salvo que un equipo de curso los acepte explicitamente como material de curso. Cards, quizzes, prompts, ejemplos, tareas, examenes y proyectos oficiales deben seguir distinguiendose de material personal, compartido y generado.

La fuente del curso usa `source: course` y orden visible dentro de `course/`: `0_index.md`, `1_foundations/`, `2_practice/` y `A_reference/`. Escribe las introducciones manuales en `0_index.md`; Glintstone renderiza indices de hijos y conteos de estudio desde resumenes y objetos oficiales sin sobrescribir la fuente. Pon objetos oficiales de aprendizaje bajo `_official/` junto al tema que apoyan, y assets locales del tema bajo `_assets/`. Usa `id` estable en frontmatter y enlaces `raya:<id>` para referencias que deben sobrevivir renumeracion o movimientos.

Para autoria mas breve, usa wikilinks locales del curso como `[[First Topic]]`
o `[[First Topic|the first topic]]`. Se resuelven durante validacion/build a
enlaces estaticos normales y edges del grafo cuando el target coincide de forma
unica con un page ID, alias, titulo, titulo de navegacion, stem de archivo o
ruta de fuente. Targets faltantes o ambiguos fallan validacion; usa IDs
estables para enlaces duraderos.

Las paginas de curso pueden usar el baseline rich static aceptado: tablas, math MathJax en build, codigo mostrado con botones locales de copiado, callouts, footnotes, heading anchors y tablas de contenido generadas por pagina. Escribe math inline con delimitadores de dolar y math display con delimitadores de doble dolar en lineas propias. Usa `\newcommand` o `\renewcommand` locales a la pagina para macros soportadas. Documentos LaTeX completos, delimitadores malformados, delimitadores anidados no soportados y macros desconocidas fallan antes de publicar. Los bloques de codigo solo se muestran en esta fase, raw HTML se escapa y los archivos de soporte renderizados se generan bajo `artifact/site/_raya/`.

Los indices generados de paginas hijas se renderizan como cards de entrada de
seccion. Mantiene resumenes, tiempo estimado y objetos oficiales honestos para
que las cards ayuden a escanear estructura sin implicar progreso personal,
dominio, finalizacion ni recomendaciones.

Para notacion comun de curso, prefiere macros pequenas locales a la pagina como `\newcommand{\rayaVec}[1]{\mathbf{#1}}` y usalas consistentemente despues de definirlas. Matrices como `\begin{bmatrix} ... \end{bmatrix}`, ecuaciones alineadas, casos, derivadas, integrales, notacion de probabilidad, notacion de optimizacion y `\renewcommand` para ajustes locales de pagina estan cubiertas por fixtures. Mantiene las definiciones de macros cerca de la pagina que las usa para que los diagnosticos apunten a la fuente relevante.

Usa `examples/courses/render-fixture/course/2_math_authoring/0_index.md` como referencia fixture actual para patrones copiables de MathJax en build. Cubre math inline y display, matrices `\begin{bmatrix}`, macros de vectores, `\newcommand`, `\renewcommand`, notacion de conjuntos y logica, normas, productos internos, derivaciones alineadas y notacion de optimizacion. Define macros antes de usarlas, mantenlas locales a la pagina y usa delimitadores `$$` en lineas propias para expresiones grandes.

Usa `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md` cuando quieras una pagina fuente compacta que combine macros de math, contenido numerado, referencias, entornos estaticos, assets locales y una skin de seccion.

Los objetos numerados son comportamiento actual en build. Configura familias y secuencias en `raya.yaml` con `render.numbered_objects.numbering`, `render.numbered_objects.sequences` y `render.numbered_objects.families`, y despues escribe objetos con directivas fenced e IDs duraderos:

```markdown
::: theorem {#compactness title="Compactness Criterion"}
Every open cover has a finite subcover.
:::

::: corollary {#finite-subcover}
This follows from @compactness.
:::

::: equation {#risk}
$$
R(f)=\mathbb{E}[\ell(f(X),Y)]
$$
:::

::: figure {#pipeline title="Flujo de entrenamiento"}
![Flujo](_assets/pipeline.png)
:::

::: homework {#hw-compactness title="Tarea"}
Usa [el criterio de compacidad](raya:ref/compactness) en tu demostracion.
:::
```

Theorem, corollary y el objeto incorporado `remark` pueden compartir una secuencia de familia theorem. La presentacion lectora predeterminada usa `scannable` para objetos tipo teorema, ejemplos, ejercicios y tareas; figuras y tablas conservan presentacion `caption`, y ecuaciones conservan presentacion `equation`. La personalizacion a nivel de curso vive en `raya.yaml` bajo `render.numbered_objects`; los ajustes por pagina/seccion son trabajo futuro. Usa la forma abreviada `@id` o enlaces `raya:ref/id` para referencias en la fuente. No escribas `\label` o `\ref` de LaTeX esperando referencias cruzadas de Raya.

Usa el patron de matriz de contenido numerado al revisar un curso: incluye objetos tipo teorema, ecuacion, figura/tabla y practica con IDs duraderos. Los diagnosticos de build deben apuntar al archivo fuente y linea para IDs incorrectos, referencias desconocidas, directivas malformadas y objetivos de prueba que no existen.

Los bloques de prueba pueden apuntar a teoremas, tareas, problemas, figuras, tablas, ecuaciones, definiciones y actividades mientras cada objeto conserva su numeracion independiente. Usa `of` para nombrar el objeto numerado que se esta probando; la prueba se renderiza como entorno estatico y no crea otro objeto numerado.

Usa entornos estaticos para apoyo alrededor de objetos numerados. `proof`,
`solution`, `hint` y `answer` se renderizan durante el build y pueden usar
`of="object-id"` para apuntar a cualquier objeto numerado, incluidos objetos
tipo teorema, objetos de practica, figuras, tablas, ecuaciones y familias
configuradas del curso; no son objetos numerados y no crean registros en
`data/numbered-objects.json`. Las pruebas permanecen abiertas en el flujo del
argumento. `hint`, `solution` y `answer` se renderizan cerrados por defecto como
disclosures nativos, para que estudiantes los abran cuando esten listos sin
enviar respuestas, guardar progreso ni cargar un renderer en el browser.

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

::: problem {#matrix-practice title="Practica de matrices"}
Calcula $A\vect{x}$ para
$$
A=\begin{bmatrix}1&2\\0&1\end{bmatrix},
\qquad
\vect{x}=\begin{bmatrix}x_1\\x_2\end{bmatrix}.
$$
:::

::: hint {#hint-matrix-practice of="matrix-practice" title="Inicio"}
Multiplica una fila a la vez.
:::

::: solution {#solution-matrix-practice of="matrix-practice" title="Solucion desarrollada"}
El producto es
$$
A\vect{x}=\begin{bmatrix}x_1+2x_2\\x_2\end{bmatrix}.
$$
:::

::: answer {#answer-matrix-practice of="matrix-practice"}
$\begin{bmatrix}x_1+2x_2\\x_2\end{bmatrix}$
:::
```

Los bloques `hint`, `solution` y `answer` anteriores apoyan
`matrix-practice`; se renderizan como disclosures contra spoilers en la pagina
pero no crean registros en `data/numbered-objects.json`.

Usa skins de curso para identidad visual y skins de seccion para enfatizar
unidades, labs, apendices, secciones de practica o secciones de repaso.

Pon el perfil predeterminado del curso en `raya.yaml`:

```yaml
render:
  skin: warm-academic
```

Pon los tokens del perfil en `skins/warm-academic.yaml`:

```yaml
id: warm-academic
name: Warm Academic
tokens:
  color:
    page: "#ffffff"
    surface: "#f6f8fa"
    text: "#1f2328"
    muted: "#57606a"
    accent: "#0969da"
    accent_soft: "#ddf4ff"
    border: "#d0d7de"
    success: "#1a7f37"
    warning: "#9a6700"
    danger: "#cf222e"
  graph:
    group_1: "#0969da"
    group_2: "#1a7f37"
    group_3: "#8250df"
    group_4: "#9a6700"
    group_5: "#006d77"
    group_6: "#cf222e"
    group_7: "#57606a"
    group_8: "#6f42c1"
  font:
    body: "system-ui"
    heading: "system-ui"
    mono: "ui-monospace"
  density: comfortable
```

Pon el selector de seccion en `course/<section>/_raya/skin.yaml`. Selecciona un
perfil para esa seccion y sus descendientes:

```yaml
render:
  skin: warm-academic
```

El selector no define colores ni fuentes; solo nombra un perfil que ya existe bajo `skins/`.

Los archivos de skin definen tokens semanticos de color, paleta opcional de
grafo, font y densidad. Los valores opcionales `tokens.graph.group_1` hasta
`group_8` colorean grupos del grafo, leyendas, nodos, aristas y flechas despues
de reconstruir. Mantiene alto el contraste, evita fuentes externas, y no uses
skins para cambiar contenido del curso, enlaces, datos del grafo, progreso,
ranking, recomendaciones ni identidad de objetos numerados. Los campos de
fuente son `render.skin`, `skins/` y `_raya/skin.yaml`.
El render fixture usa `eva-unit-02` como ejemplo de skin predeterminada legible;
copia ese patron cuando quieras una identidad visual mas fuerte sin bajar
contraste ni cambiar el significado del curso.

Los controles de comodidad lectora como `Text size` y `OpenDyslexic` son
preferencias locales de visualizacion. No reemplazan las skins del curso y no
deben usarse para codificar significado del curso, nivel, evaluacion, progreso
ni estado oficial.

Las paginas generadas tambien pueden imprimirse o guardarse como PDF como
handouts estaticos. El modo print oculta la chrome de navegacion y mantiene
legibles el contenido autorado, MathJax, codigo, tablas, practica oficial,
objetos numerados y disclosures de soporte. Trata esos handouts como vistas
generadas del artifact, no como verdad de fuente, registros de evaluacion,
progreso, dominio ni recomendaciones personalizadas.

La estructura del curso basada en ciencia del aprendizaje funciona mejor cuando
las paginas fuente dan estructura honesta al renderizador estatico. Escribe
resumenes breves, prerrequisitos estables, checkpoints como contenido visible,
ejemplos desarrollados, prompts de practica de recuperacion y enlaces de
practica que estudiantes puedan usar sin progreso falso. Usa checkpoints y
metas como material docente visible hasta que un contrato futuro los acepte como
metadata.

Las paginas renderizadas pueden mostrar un Page brief cerca del inicio del
articulo. Se construye desde metadata aceptada como resumen, status, posicion
estructural de pagina, tiempo estimado, tags, prerrequisitos resueltos, conteos
de enlaces explicitos del grafo y conteos de practica oficial. Mantiene esos
campos precisos; el brief orienta a estudiantes, pero no es evaluacion,
progreso, dominio, personalizacion ni motor de recomendaciones.

El renderizador estatico de practica oficial muestra objetos de nivel
pagina desde archivos `_official/` colocados junto a su pagina en una seccion
`Official practice`. Por ahora, escribe cards, prompts, quizzes y campos
genericos de objetos oficiales como campos planos. Trata la seccion renderizada
como conveniencia para lectura; los archivos `_official/` autorados siguen
siendo autoridad de fuente del curso, y superficies machine-readable como
`data/official.json` y `manifest.json` siguen siendo las superficies de contrato
para herramientas. No disenes estos objetos alrededor de scoring, grading,
submissions, attempts, progreso, dominio, recomendaciones, llamadas a backend,
fetching en el browser, storage, renderers externos ni MathJax en el browser.

El workspace Official Practice se genera desde los mismos objetos
oficiales aceptados. Escribe cada objeto una vez bajo `_official/` junto a la
pagina que lo posee; Glintstone puede renderizar la seccion de pagina y una
superficie estatica de descubrimiento `_raya/practice/index.html` desde
`data/official.json`. Mantiene labels, resumenes, tags, status e IDs estables
utiles para escanear, y espera que los links de Practice devuelvan a estudiantes
a anchors de la pagina propietaria como `#raya-official-<id>`. El workspace
generado puede organizar controles, resultados y resumenes publicos de contexto
para escanear. Search o Graph pueden abrirlo enfocado en una pagina propietaria
con un aviso visible de foco de pagina y reset por Clear/Escape, pero no debe
exponer respuestas ocultas. No escribas respuestas
ocultas duplicadas para el workspace ni lo presentes como adaptativo,
recomendado, con scoring, evaluado, entregado, intentado, progreso personal,
dominio, estado guardado del estudiante, fetching en runtime, requests externos
o vista de rutas privadas de fuente.

Assignments, projects, exams y tasks tambien alimentan el workspace generado
Official Tasks en `_raya/tasks/index.html` y el index declarado en manifest
`data/tasks.json`. Pon cada objeto en el directorio de familia `_official/`
correcto, por ejemplo `_official/assignments/` o `_official/exams/`, y escribe
los campos publicos de planeacion bajo `content`:

```yaml
id: ps1
type: assignment
authority: official
scope:
  quantum: first-topic
content:
  title: Problem Set 1
  instructions: Practica multiplicacion de matrices.
  due: "2026-09-15"
  points: 10 pts
  weight: 15%
  status: published
  tags:
    - retrieval
```

El workspace de tasks ayuda a estudiantes a escanear trabajo por tipo, texto y
fecha de entrega, y despues volver al anchor de la pagina propietaria. Search o
Graph pueden abrirlo enfocado en una pagina con un aviso visible y reset por
Clear/Escape a todos los tasks visibles. No es
sistema de entregas, gradebook, sincronizacion de calendario personal, registro
de progreso, motor de recomendaciones ni superficie de respuestas ocultas.

El workspace Official Schedule en `_raya/schedule/index.html` se genera desde
los mismos objetos aceptados de familia task cuando incluyen `content.due` o
`content.available`. Ayuda a estudiantes a escanear trabajo oficial fechado y
volver al anchor de la pagina propietaria. Search o Graph pueden abrirlo
enfocado en una pagina con un aviso visible y reset por Clear/Escape a todos los
items fechados visibles. No es una fuente de calendario
separada, sincronizacion de calendario personal, sistema de recordatorios,
sistema de entregas, gradebook, registro de progreso ni motor de
recomendaciones.

Las paginas renderizadas usan un mapa del curso expandido, renderizado como un
mapa jerarquico del curso expandido por defecto,
y permiten filtrar etiquetas visibles de paginas o colapsarlo a un riel compacto
operable para dar mas espacio de lectura. En desktop, `Focus reading` puede
colapsar juntos el mapa y el riel derecho como estado visual temporal. El estado
del mapa, el foco lector y el texto del filtro son UI no persistente. La shell puede mostrar estructura como `Page N of M`;
eso es posicion dentro del curso y no es progreso personal ni finalizacion.
Las paginas tambien pueden terminar con cards Previous/Next generadas desde el
orden autorado del curso. No las escribas por separado; manten claro el orden y
los titulos de pagina, y tratalas como navegacion estatica, no recomendaciones.

El Course graph generado puede ayudar a estudiantes a inspeccionar relaciones
explicitas entre paginas mediante busqueda local aproximada, detalles de pagina
seleccionada y workspace expandido del grafo. Los detalles de pagina seleccionada
pueden incluir un Relationship walkthrough que explica tipos y direcciones de
enlaces explicitos con controles locales de pagina y foco en grafo. Los
previews de conexion pueden etiquetar tipo y direccion de relacion, como
`Content` y `From this page`, usando solo contexto explicito generado del grafo.
Los relationship chips pueden reducir temporalmente ese walkthrough para lectura,
pero no crean recomendaciones, progreso, filtros guardados ni datos nuevos del
curso. El grafo
puede ocultar labels de bajo contexto hasta que una seleccion, busqueda,
hover o foco de teclado los vuelva utiles. Los detalles de debug `Graph state`
pueden estar cerrados por defecto en un disclosure nativo. Estudiantes tambien pueden usar
Zoom in, Zoom out, Fit y Reset view para inspeccionar zonas visuales densas del
grafo sin cambiar datos del curso ni estado guardado. Tratalo como estructura
del curso desde datos actuales de artifact, no como analiticas,
recomendaciones, dominio o progreso personal. Los links generados de pagina
pueden abrir el grafo enfocado en la pagina actual.

Course Search es una superficie estatica de descubrimiento publico. Puede
coincidir aproximadamente con titulos, etiquetas de navegacion, resumenes,
tags, status, etiquetas de jerarquia, stable IDs y prosa publica renderizada
del articulo, pero no indexa rutas ocultas de fuente, rutas privadas de soporte,
internos de MathJax, TeX crudo, contenido solo de respuestas/soporte ni estado
personal del estudiante. Los links generados de pagina pueden precargar una
consulta temporal, pero el renderer no la guarda. Los resultados tambien pueden
incluir links `View in graph` generados desde stable IDs para que estudiantes
inspeccionen donde queda una pagina encontrada dentro del grafo del curso. El
workspace de Search puede mostrar regiones de controles, resultados y contexto
desde metadata publica y snippets publicos de coincidencia. Un handoff valido
de pagina puede mostrar un aviso visible con la pagina publica enfocada y el
conteo visible hasta que Clear o Escape restaure todos los resultados. Esos
resumenes son ayudas estructurales para escanear, no rankings ni
recomendaciones.

Las paginas de curso tambien pueden linkear scripts y notebooks junto al quantum que apoyan, por ejemplo `scripts/clean.py`, `labs/explore.ipynb`, `code/helper.py` o `notebooks/overview.ipynb`. Glintstone valida archivos `.py` y `.ipynb` linkeados por extension y limite de propiedad, copia solo archivos linkeados para lectura y descarga, y los previsualiza estaticamente; no se ejecutan durante el build. Usa esto para trabajo de soporte transparente, no para contenido de pagina escondido ni objetos oficiales de aprendizaje.

Los cursos pueden declarar runtime metadata con `pyproject.toml`, `uv.lock` y `runtime/profiles.yaml` en la raiz. Esto ayuda a que futura ejecucion local o con Docker sea reproducible, pero el build actual solo registra perfiles, policies y cache keys; no ejecuta codigo, instala paquetes, refresca caches ni confia en outputs de notebooks.

Cuando un curso requiere computo real, usa objetivos explicitos. `raya run <course> <target>` ejecuta un script o notebook validado; `--dry-run` muestra el plan, `--refresh` vuelve a correr trabajo con policy `cache`, y `--docker` usa el servicio de clase declarado. Logs y outputs generados permanecen bajo `artifact/` y no deben confundirse con fuente revisada del curso ni respuestas oficiales.

Para publicar un resultado calculado como soporte revisado, primero ejecuta el objetivo explicito, despues inspeccionalo con `raya outputs list <course>`, y despues usa `raya outputs freeze <course> <target>`. Freeze copia el resultado generado exitoso y vigente hacia `_reviewed/execution/<target>/` junto al quantum que lo posee. Revisa y commitea esos archivos como fuente normal del curso. Usa `policy: frozen` solo cuando ese output revisado deba ser requerido y validado sin volver a ejecutar codigo.

Las paginas para estudiantes deben permanecer enfocadas. Glintstone puede mostrar panels compactos de recursos o reviewed output, pero hashes, rutas, detalles de runtime profile, cache keys y freshness keys pertenecen a datos de artifact o paginas estaticas `_raya/inspect/` para auditoria.

Usa `raya preview <course>` para revisar localmente el sitio estatico generado antes de compartirlo o publicarlo. Preview reporta el entrypoint de estudiante y la pagina de inspeccion, pero no ejecuta scripts, notebooks, Docker, kernels, installs de paquetes ni cache refreshes. Ejecuta targets explicitos con `raya run` por separado cuando el curso requiera computo.

Las specs OpenSpec describen contratos aceptados. La documentacion de rol explica como trabajar con esos contratos, pero no tiene mas autoridad que foundation docs ni specs aceptadas.

La documentacion renderizada del repositorio es guia, no canon de curso. Se construye desde `docs/raya.yaml` y permanece separada del material de clase y de los artifacts oficiales de curso.
