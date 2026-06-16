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

Las paginas estaticas pueden incluir math pre-renderizada, codigo resaltado, tablas, callouts, footnotes, heading anchors y contenidos de pagina. La math debe aparecer ya compuesta en la pagina generada y no debe requerir CDN, cuenta, backend ni conversion MathJax en el browser. El codigo mostrado no se ejecuta en la pagina estatica salvo que un curso futuro agregue un workflow de ejecucion aceptado.

Si la math aparece como comandos TeX crudos como `\begin{bmatrix}` o una macro desconocida en una pagina publicada, tratalo como un problema de rendering para reportar al equipo del curso, no como un paso que debas arreglar en tu browser.

Matrices renderizadas, vectores, notacion de conjuntos, notas tipo theorem y pruebas deben aparecer como texto normal del curso mas matematica compuesta. Si ves `\begin{bmatrix}` crudo, una macro desconocida, matematica visible con delimitadores de dolar, o una pagina que pide cargar browser-side MathJax, reportalo al equipo del curso con la URL o titulo de la pagina.

Las paginas de curso pueden incluir objetos numerados y referencias estaticas. Un resultado puede aparecer como `Teorema 2.3.1`, una imagen como `Figura 2.3.1`, y el trabajo de practica como referencia de tarea, problema, actividad o assignment. Los objetos numerados deben aparecer como contenido de curso escaneable cuando corresponda: objetos tipo teorema, ejemplos, ejercicios y tareas usan `scannable` de forma predeterminada, mientras figuras y tablas conservan `caption` y ecuaciones conservan `equation`. Estos numeros, etiquetas, anchors y referencias se generan durante el build y se publican como enlaces estaticos; tu browser no deberia calcularlos ni cargar un servicio vivo de referencias.

El contenido numerado aparece como etiquetas y enlaces estaticos, por ejemplo `Theorem 3.1`, `Figure 3.1` o `Activity 3.3`. Los encabezados de prueba como `Proof of Activity 3.3` se generan durante build; el browser no calcula referencias.

Los encabezados de prueba renderizados nombran el objeto que se esta probando, y la matematica dentro de la prueba debe aparecer ya compuesta durante el build. La pagina no deberia necesitar un request de browser-side MathJax para mostrar la prueba. Si ves sintaxis de fuente cruda o TeX crudo en vez de una prueba renderizada, reportalo al equipo del curso con la URL o titulo de la pagina.

Las pruebas, soluciones, pistas y respuestas deben aparecer como contenido
estatico del curso. Cuando nombran un teorema, problema, actividad, tarea,
figura, tabla o ecuacion, ese encabezado ya debe estar resuelto antes de que la
pagina llegue al navegador.

Algunas paginas pueden incluir scripts o notebooks enlazados. Se copian como archivos legibles y pueden mostrar previsualizaciones de fuente, pero el build estatico los etiqueta como `not-executed`. Los archivos fuente no enlazados no forman parte del artifact de la pagina. Usa las instrucciones del curso cuando una clase espere que ejecutes codigo localmente, en Docker, o mediante un futuro workflow aceptado.

Algunos cursos incluyen runtime metadata para futura ejecucion local o con Docker. En el artifact estatico actual, esa metadata solo explica perfiles previstos, policies y cache keys. No significa que la pagina web ya ejecuto el codigo.

Cuando un curso te pida ejecutar codigo, usa el target exacto indicado por el equipo del curso, por ejemplo `raya run . manual-script` desde la raiz del curso o el comando Docker que provean. `--dry-run` muestra que se ejecutaria antes de ejecutarlo. Targets con policy `cache` pueden reutilizar output generado previo salvo que el curso pida `--refresh`.

Algunas paginas pueden mostrar paneles de output revisado. Ese output es soporte de curso que el equipo congelo dentro de revision de fuente, por eso puede mostrarse estaticamente sin volver a ejecutar codigo. Es diferente de tu trabajo personal y de logs generados localmente. Si el output revisado esta desactualizado o falta, el artifact del curso debe fallar antes de publicarlo como vigente.

Las paginas estaticas muestran una vista de lectura enfocada. Hashes internos, cache keys, rutas de fuente, rutas de artifact y detalles de runtime quedan fuera del flujo normal; son para profesores, colaboradores, agentes o herramientas que inspeccionan el artifact.

Si un profesor comparte una URL local de preview, es el mismo sitio estatico generado servido desde `artifact/site/`. Abrir una pagina de preview no ejecuta codigo ni notebooks del curso. Sigue instrucciones explicitas del curso cuando el computo sea parte de la clase.

Usa la documentacion de rol como guia. Usa las paginas de curso y objetos oficiales de aprendizaje como material de curso. Si documentacion y material de curso entran en conflicto, el equipo de curso y la autoridad aceptada de specs OpenSpec o `docs/foundation/` deciden que cambia.

La documentacion renderizada del repositorio puede leerse como paginas estaticas, pero sigue siendo guia sobre el framework. No es la misma superficie de autoridad que un artifact oficial de curso.
