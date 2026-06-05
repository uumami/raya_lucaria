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

Algunas paginas pueden incluir scripts o notebooks referenciados. Se copian como archivos legibles y pueden mostrar previews de source, pero el build estatico los etiqueta como `not-executed`. Usa las instrucciones del curso cuando una clase espere que ejecutes codigo localmente, en Docker, o mediante un futuro workflow aceptado.

Algunos cursos incluyen runtime metadata para futura ejecucion local o con Docker. En el artifact estatico actual, esa metadata solo explica perfiles previstos, policies y cache keys. No significa que la pagina web ya ejecuto el codigo.

Usa la documentacion de rol como guia. Usa las paginas de curso y objetos oficiales de aprendizaje como material de curso. Si documentacion y material de curso entran en conflicto, el equipo de curso y la autoridad aceptada de specs OpenSpec o `docs/foundation/` deciden que cambia.

La documentacion renderizada del repositorio puede leerse como paginas estaticas, pero sigue siendo guia sobre el framework. No es la misma superficie de autoridad que un artifact oficial de curso.
