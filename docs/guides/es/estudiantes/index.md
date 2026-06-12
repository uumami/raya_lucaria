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

Las paginas estaticas pueden incluir math, codigo resaltado, tablas, callouts, footnotes, heading anchors y contenidos de pagina. Todo debe leerse sin cuentas ni backend. El codigo mostrado no se ejecuta en la pagina estatica salvo que un curso futuro agregue un workflow de ejecucion aceptado.

Algunas paginas pueden incluir scripts o notebooks linkeados. Se copian como archivos legibles y pueden mostrar previews de source, pero el build estatico los etiqueta como `not-executed`. Los archivos source no linkeados no forman parte del artifact de la pagina. Usa las instrucciones del curso cuando una clase espere que ejecutes codigo localmente, en Docker, o mediante un futuro workflow aceptado.

Algunos cursos incluyen runtime metadata para futura ejecucion local o con Docker. En el artifact estatico actual, esa metadata solo explica perfiles previstos, policies y cache keys. No significa que la pagina web ya ejecuto el codigo.

Cuando un curso te pida ejecutar codigo, usa el target exacto indicado por el equipo del curso, por ejemplo `raya run . manual-script` desde la raiz del curso o el comando Docker que provean. `--dry-run` muestra que se ejecutaria antes de ejecutarlo. Targets con policy `cache` pueden reutilizar output generado previo salvo que el curso pida `--refresh`.

Algunas paginas pueden mostrar panels de reviewed output. Ese output es soporte de curso que el equipo congelo dentro de revision de source, por eso puede mostrarse estaticamente sin volver a ejecutar codigo. Es diferente de tu trabajo personal y de logs generados localmente. Si el reviewed output esta stale o falta, el artifact del curso debe fallar antes de publicarlo como current.

Las paginas estaticas muestran una vista de lectura enfocada. Hashes internos, cache keys, rutas source, rutas de artifact y detalles de runtime quedan fuera del flujo normal; son para profesores, colaboradores, agentes o herramientas que inspeccionan el artifact.

Si un profesor comparte una URL local de preview, es el mismo sitio estatico generado servido desde `artifact/site/`. Abrir una pagina de preview no ejecuta codigo ni notebooks del curso. Sigue instrucciones explicitas del curso cuando el computo sea parte de la clase.

Usa la documentacion de rol como guia. Usa las paginas de curso y objetos oficiales de aprendizaje como material de curso. Si documentacion y material de curso entran en conflicto, el equipo de curso y la autoridad aceptada de specs OpenSpec o `docs/foundation/` deciden que cambia.

La documentacion renderizada del repositorio puede leerse como paginas estaticas, pero sigue siendo guia sobre el framework. No es la misma superficie de autoridad que un artifact oficial de curso.
