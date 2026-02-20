---
title: "Calendario"
summary: "Calendario de temas del curso"
---

# Calendario

El calendario de temas es una tabla que muestra las fechas y temas del curso a lo largo del semestre.

## Formato del CSV

Crea un archivo `calendario_temas.csv` en la raiz del repositorio del curso. El formato es:

```csv
semana,fecha,tema,notas
1,2026-01-13,Introduccion al curso,
2,2026-01-20,Fundamentos,Lectura capitulo 1
3,2026-01-27,Estructuras de datos,"Tarea 1 (ver /tareas/)"
```

## Columnas

| Columna | Descripcion |
|---------|-------------|
| `semana` | Numero de semana |
| `fecha` | Fecha de la clase (YYYY-MM-DD) |
| `tema` | Tema o titulo de la sesion |
| `notas` | Notas adicionales (entregas, lecturas, etc.) |

## Renderizado

El calendario aparece como una tabla con formato en la ruta `/calendario/` del sitio. Tambien se agrega automaticamente al menu lateral bajo la seccion "Curso".

## Condicional

El calendario solo se muestra si el archivo `calendario_temas.csv` existe. Si no existe, la entrada no aparece en el menu lateral.
