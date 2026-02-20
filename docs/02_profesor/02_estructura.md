---
title: "Estructura de contenido"
summary: "Como organizar archivos y directorios del curso"
---

# Estructura de contenido

## Directorio `clase/`

Todo el contenido del curso vive en el directorio `clase/`. Cada subdirectorio representa un capitulo o seccion del curso.

## Convenciones de nombres

Los prefijos de archivos y directorios determinan como aparecen en la navegacion:

| Prefijo | Significado | En la nav | Ejemplo |
|---------|-------------|-----------|---------|
| `00_` | Indice de seccion | Oculto (el padre se muestra) | `00_index.md` |
| `01_`, `02_`, ... | Contenido numerado | 1, 2, ... | `01_intro.md` |
| `a_`, `b_`, ... | Apendices | A, B, ... | `a_apendice/` |
| `z_` | Documentacion | Z (al final) | `z_docs/` |
| `??_` | Trabajo en progreso | Excluido del build | `??_borrador/` |

## El archivo `00_index.md`

Cada directorio **debe** tener un archivo `00_index.md`. Este archivo:

- Sirve como pagina de entrada del capitulo
- Debe usar `layout: layouts/chapter.njk` para mostrar tarjetas de navegacion hacia sus hijos
- Su titulo aparece en la barra lateral como nombre del capitulo

## Ejemplo de estructura

```
clase/
├── 00_index.md              # Pagina raiz del curso
├── 01_introduccion/
│   ├── 00_index.md          # Indice del capitulo 1
│   ├── 01_bienvenida.md     # Seccion 1.1
│   ├── 02_temario.md        # Seccion 1.2
│   └── images/              # Imagenes del capitulo
│       └── diagrama.png
├── 02_fundamentos/
│   ├── 00_index.md          # Indice del capitulo 2
│   ├── 01_conceptos.md      # Seccion 2.1
│   └── 02_practica.md       # Seccion 2.2
├── a_apendice/
│   ├── 00_index.md
│   └── 01_referencias.md
└── calendario_temas.csv      # Calendario opcional
```

## Como la numeracion se refleja en la navegacion

- `01_introduccion/` aparece como **1 Introduccion** en la barra lateral
- `01_bienvenida.md` dentro de ese directorio aparece como **1.1 Bienvenida**
- `a_apendice/` aparece como **A Apendice**

## Directorio de imagenes

Las imagenes de cada capitulo se colocan en un subdirectorio `images/` dentro del capitulo correspondiente. Se referencian en markdown con rutas relativas:

```markdown
![Descripcion](./images/foto.png)
```
