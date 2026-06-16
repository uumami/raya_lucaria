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

Las paginas de curso pueden usar el baseline rich static aceptado: tablas, math MathJax en build, codigo mostrado, callouts, footnotes, heading anchors y tablas de contenido generadas por pagina. Escribe math inline con delimitadores de dolar y math display con delimitadores de doble dolar en lineas propias. Usa `\newcommand` o `\renewcommand` locales a la pagina para macros soportadas. Documentos LaTeX completos, delimitadores malformados, delimitadores anidados no soportados y macros desconocidas fallan antes de publicar. Los bloques de codigo solo se muestran en esta fase, raw HTML se escapa y los archivos de soporte renderizados se generan bajo `artifact/site/_raya/`.

Para notacion comun de curso, prefiere macros pequenas locales a la pagina como `\newcommand{\rayaVec}[1]{\mathbf{#1}}` y usalas consistentemente despues de definirlas. Matrices como `\begin{bmatrix} ... \end{bmatrix}`, ecuaciones alineadas, cases, derivadas, integrales, notacion de probabilidad, notacion de optimizacion y `\renewcommand` para ajustes locales de pagina estan cubiertas por fixtures. Mantiene las definiciones de macros cerca de la pagina que las usa para que los diagnosticos apunten al source relevante.

Usa `examples/courses/render-fixture/course/2_math_authoring/0_index.md` como referencia fixture actual para patrones copiables de MathJax en build. Cubre math inline y display, matrices `\begin{bmatrix}`, macros de vectores, `\newcommand`, `\renewcommand`, notacion de conjuntos y logica, normas, productos internos, derivaciones alineadas y notacion de optimizacion. Define macros antes de usarlas, mantenlas locales a la pagina y usa delimitadores `$$` en lineas propias para expresiones grandes.

Los objetos numerados son comportamiento actual en build. Configura familias y secuencias en `raya.yaml` con `render.numbered_objects.numbering`, `render.numbered_objects.sequences` y `render.numbered_objects.families`, y despues escribe objetos con fenced directives e IDs estables:

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

Theorem y corollary pueden compartir una secuencia de theorem; equation, figure, table, problem, homework y assignment pueden compartir o separar secuencias segun la configuracion. Usa shorthand `@id` o links `raya:ref/id` para referencias source. No escribas `\label` o `\ref` de LaTeX esperando cross-references de Raya.

Las paginas de curso tambien pueden linkear scripts y notebooks junto al quantum que apoyan, por ejemplo `scripts/clean.py`, `labs/explore.ipynb`, `code/helper.py` o `notebooks/overview.ipynb`. Glintstone valida archivos `.py` y `.ipynb` linkeados por extension y limite de propiedad, copia solo archivos linkeados para lectura y descarga, y los previsualiza estaticamente; no se ejecutan durante el build. Usa esto para trabajo de soporte transparente, no para contenido de pagina escondido ni objetos oficiales de aprendizaje.

Los cursos pueden declarar runtime metadata con `pyproject.toml`, `uv.lock` y `runtime/profiles.yaml` en la raiz. Esto ayuda a que futura ejecucion local o con Docker sea reproducible, pero el build actual solo registra perfiles, policies y cache keys; no ejecuta codigo, instala paquetes, refresca caches ni confia en outputs de notebooks.

Cuando un curso requiere computo real, usa targets explicitos. `raya run <course> <target>` ejecuta un script o notebook validado; `--dry-run` muestra el plan, `--refresh` vuelve a correr trabajo con policy `cache`, y `--docker` usa el servicio de clase declarado. Logs y outputs generados permanecen bajo `artifact/` y no deben confundirse con source revisado del curso ni respuestas oficiales.

Para publicar un resultado calculado como soporte revisado, primero ejecuta el target explicito, despues inspeccionalo con `raya outputs list <course>`, y despues usa `raya outputs freeze <course> <target>`. Freeze copia el resultado generado exitoso y current hacia `_reviewed/execution/<target>/` junto al quantum que lo posee. Revisa y commitea esos archivos como source normal del curso. Usa `policy: frozen` solo cuando ese output revisado deba ser requerido y validado sin volver a ejecutar codigo.

Las paginas para estudiantes deben permanecer enfocadas. Glintstone puede mostrar panels compactos de recursos o reviewed output, pero hashes, rutas, detalles de runtime profile, cache keys y freshness keys pertenecen a datos de artifact o paginas estaticas `_raya/inspect/` para auditoria.

Usa `raya preview <course>` para revisar localmente el sitio estatico generado antes de compartirlo o publicarlo. Preview reporta el entrypoint de estudiante y la pagina de inspeccion, pero no ejecuta scripts, notebooks, Docker, kernels, installs de paquetes ni cache refreshes. Ejecuta targets explicitos con `raya run` por separado cuando el curso requiera computo.

Las specs OpenSpec describen contratos aceptados. La documentacion de rol explica como trabajar con esos contratos, pero no tiene mas autoridad que foundation docs ni specs aceptadas.

La documentacion renderizada del repositorio es guia, no canon de curso. Se construye desde `docs/raya.yaml` y permanece separada del material de clase y de los artifacts oficiales de curso.
