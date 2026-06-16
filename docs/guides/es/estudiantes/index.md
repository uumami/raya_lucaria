---
id: docs-guides-es-estudiantes
title: Estudiantes
summary: Guia para leer artifacts estaticos, estudiar, mantener trabajo portable y entender autoridad.
status: ready
---
# Estudiantes

Los estudiantes deben poder leer artifactos estaticos de curso, estudiar con objetos oficiales de aprendizaje, mantener portable su trabajo personal y entender si un material es oficial, personal, compartido, generado o aceptado.

Las paginas estaticas de curso son utiles sin cuentas. Estado dinamico de estudio, colas de repaso y colaboracion son mejoras progresivas futuras.

Los cursos renderizados ocultan la mecanica de nombres de archivo. Los estudiantes deben ver titulos limpios, etiquetas de jerarquia, summaries, breadcrumbs, links anterior/siguiente, indices generados de seccion, anexos, prerequisitos y conteos de objetos oficiales de estudio cuando el curso provee esa metadata.

Las paginas estaticas pueden incluir math pre-renderizada, codigo resaltado, tablas, callouts, footnotes, heading anchors y contenidos de pagina. La math debe aparecer ya compuesta en la pagina generada y no debe requerir CDN, cuenta, backend ni conversion MathJax en el browser. El codigo mostrado no se ejecuta en la pagina estatica salvo que un curso futuro agregue un workflow de ejecucion aceptado.

Si la math aparece como comandos TeX crudos como `\begin{bmatrix}` o una macro desconocida en una pagina publicada, tratalo como un problema de rendering para reportar al equipo del curso, no como un paso que debas arreglar en tu browser.

Matrices renderizadas, vectores, notacion de conjuntos, notas tipo theorem y proofs deben aparecer como texto normal del curso mas math compuesta. Si ves `\begin{bmatrix}` crudo, una macro desconocida, math visible con delimitadores de dolar, o una pagina que pide cargar browser-side MathJax, reportalo al equipo del curso con la URL o titulo de la pagina.

Las paginas de curso pueden incluir objetos numerados y referencias estaticas. Un resultado puede aparecer como `Teorema 2.3.1`, una imagen como `Figura 2.3.1`, y el trabajo de practica como referencia de homework, problem, activity o assignment. Estos numeros, etiquetas, anchors y referencias se generan durante el build y se publican como links estaticos; tu browser no deberia calcularlos ni cargar un servicio vivo de referencias.

Los bloques de proof muestran en el heading renderizado que objeto se esta probando, y la math dentro del proof se renderiza durante el build. La pagina no deberia necesitar un request de MathJax en el browser para mostrar el proof.

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

Algunas paginas pueden incluir scripts o notebooks linkeados. Se copian como archivos legibles y pueden mostrar previews de source, pero el build estatico los etiqueta como `not-executed`. Los archivos source no linkeados no forman parte del artifact de la pagina. Usa las instrucciones del curso cuando una clase espere que ejecutes codigo localmente, en Docker, o mediante un futuro workflow aceptado.

Algunos cursos incluyen runtime metadata para futura ejecucion local o con Docker. En el artifact estatico actual, esa metadata solo explica perfiles previstos, policies y cache keys. No significa que la pagina web ya ejecuto el codigo.

Cuando un curso te pida ejecutar codigo, usa el target exacto indicado por el equipo del curso, por ejemplo `raya run . manual-script` desde la raiz del curso o el comando Docker que provean. `--dry-run` muestra que se ejecutaria antes de ejecutarlo. Targets con policy `cache` pueden reutilizar output generado previo salvo que el curso pida `--refresh`.

Algunas paginas pueden mostrar panels de reviewed output. Ese output es soporte de curso que el equipo congelo dentro de revision de source, por eso puede mostrarse estaticamente sin volver a ejecutar codigo. Es diferente de tu trabajo personal y de logs generados localmente. Si el reviewed output esta stale o falta, el artifact del curso debe fallar antes de publicarlo como current.

Las paginas estaticas muestran una vista de lectura enfocada. Hashes internos, cache keys, rutas source, rutas de artifact y detalles de runtime quedan fuera del flujo normal; son para profesores, colaboradores, agentes o herramientas que inspeccionan el artifact.

Si un profesor comparte una URL local de preview, es el mismo sitio estatico generado servido desde `artifact/site/`. Abrir una pagina de preview no ejecuta codigo ni notebooks del curso. Sigue instrucciones explicitas del curso cuando el computo sea parte de la clase.

Usa la documentacion de rol como guia. Usa las paginas de curso y objetos oficiales de aprendizaje como material de curso. Si documentacion y material de curso entran en conflicto, el equipo de curso y la autoridad aceptada de specs OpenSpec o `docs/foundation/` deciden que cambia.

La documentacion renderizada del repositorio puede leerse como paginas estaticas, pero sigue siendo guia sobre el framework. No es la misma superficie de autoridad que un artifact oficial de curso.
