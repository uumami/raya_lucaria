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

Las paginas de curso pueden usar el baseline rich static aceptado: tablas, math MathJax en build, codigo mostrado, callouts, footnotes, heading anchors y tablas de contenido generadas por pagina. Escribe math inline con delimitadores de dolar y math display con delimitadores de doble dolar en lineas propias. Usa `\newcommand` o `\renewcommand` locales a la pagina para macros soportadas. Documentos LaTeX completos, delimitadores malformados, delimitadores anidados no soportados y macros desconocidas fallan antes de publicar. Los bloques de codigo solo se muestran en esta fase, raw HTML se escapa y los archivos de soporte renderizados se generan bajo `artifact/site/_raya/`.

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
`data/numbered-objects.json`.

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
`matrix-practice`; se renderizan en la pagina pero no crean registros en
`data/numbered-objects.json`.

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

Los archivos de skin definen tokens semanticos de color, font y densidad.
Mantiene alto el contraste, evita fuentes externas, y no uses skins para
cambiar contenido del curso, enlaces ni identidad de objetos numerados. Los
campos de fuente son `render.skin`, `skins/` y `_raya/skin.yaml`.

Las paginas de curso tambien pueden linkear scripts y notebooks junto al quantum que apoyan, por ejemplo `scripts/clean.py`, `labs/explore.ipynb`, `code/helper.py` o `notebooks/overview.ipynb`. Glintstone valida archivos `.py` y `.ipynb` linkeados por extension y limite de propiedad, copia solo archivos linkeados para lectura y descarga, y los previsualiza estaticamente; no se ejecutan durante el build. Usa esto para trabajo de soporte transparente, no para contenido de pagina escondido ni objetos oficiales de aprendizaje.

Los cursos pueden declarar runtime metadata con `pyproject.toml`, `uv.lock` y `runtime/profiles.yaml` en la raiz. Esto ayuda a que futura ejecucion local o con Docker sea reproducible, pero el build actual solo registra perfiles, policies y cache keys; no ejecuta codigo, instala paquetes, refresca caches ni confia en outputs de notebooks.

Cuando un curso requiere computo real, usa objetivos explicitos. `raya run <course> <target>` ejecuta un script o notebook validado; `--dry-run` muestra el plan, `--refresh` vuelve a correr trabajo con policy `cache`, y `--docker` usa el servicio de clase declarado. Logs y outputs generados permanecen bajo `artifact/` y no deben confundirse con fuente revisada del curso ni respuestas oficiales.

Para publicar un resultado calculado como soporte revisado, primero ejecuta el objetivo explicito, despues inspeccionalo con `raya outputs list <course>`, y despues usa `raya outputs freeze <course> <target>`. Freeze copia el resultado generado exitoso y vigente hacia `_reviewed/execution/<target>/` junto al quantum que lo posee. Revisa y commitea esos archivos como fuente normal del curso. Usa `policy: frozen` solo cuando ese output revisado deba ser requerido y validado sin volver a ejecutar codigo.

Las paginas para estudiantes deben permanecer enfocadas. Glintstone puede mostrar panels compactos de recursos o reviewed output, pero hashes, rutas, detalles de runtime profile, cache keys y freshness keys pertenecen a datos de artifact o paginas estaticas `_raya/inspect/` para auditoria.

Usa `raya preview <course>` para revisar localmente el sitio estatico generado antes de compartirlo o publicarlo. Preview reporta el entrypoint de estudiante y la pagina de inspeccion, pero no ejecuta scripts, notebooks, Docker, kernels, installs de paquetes ni cache refreshes. Ejecuta targets explicitos con `raya run` por separado cuando el curso requiera computo.

Las specs OpenSpec describen contratos aceptados. La documentacion de rol explica como trabajar con esos contratos, pero no tiene mas autoridad que foundation docs ni specs aceptadas.

La documentacion renderizada del repositorio es guia, no canon de curso. Se construye desde `docs/raya.yaml` y permanece separada del material de clase y de los artifacts oficiales de curso.
