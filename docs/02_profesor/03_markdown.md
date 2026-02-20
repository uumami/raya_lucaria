---
title: "Markdown"
summary: "Referencia de formato Markdown para contenido"
---

# Markdown

## Frontmatter

Cada archivo Markdown puede tener un encabezado YAML opcional entre delimitadores `---`:

```yaml
---
title: "Titulo de la pagina"
summary: "Descripcion breve para tarjetas de indice"
tags: [python, datos]
layout: layouts/base.njk
order: 5
---
```

### Campos disponibles

| Campo | Tipo | Default | Descripcion |
|-------|------|---------|-------------|
| `title` | string | Del nombre del archivo | Titulo de la pagina |
| `summary` | string | null | Descripcion para tarjetas de indice |
| `tags` | lista | [] | Etiquetas de categorizacion |
| `layout` | string | `layouts/base.njk` | Template a usar |
| `order` | numero | Del prefijo del archivo | Orden de clasificacion |

Ninguno es obligatorio. Si omites `title`, se genera automaticamente a partir del nombre del archivo.

## Encabezados

Usa un solo `#` (H1) por pagina como titulo principal. Usa `##`, `###`, etc. para subsecciones:

```markdown
# Titulo principal (uno por pagina)

## Seccion

### Subseccion
```

Los encabezados `##` y `###` aparecen automaticamente en la tabla de contenidos (sidebar derecho).

## Formato de texto

```markdown
**Texto en negritas**
*Texto en italicas*
`codigo en linea`
~~texto tachado~~
```

## Listas

```markdown
- Elemento sin orden
- Otro elemento
  - Sub-elemento

1. Primer paso
2. Segundo paso
3. Tercer paso
```

## Bloques de codigo

Usa triple backtick con el lenguaje:

````markdown
```python
def hola():
    print("Hola mundo")
```
````

Lenguajes soportados: `python`, `javascript`, `java`, `c`, `cpp`, `sql`, `bash`, `html`, `css`, `json`, `yaml`, `markdown`, y muchos mas.

Cada bloque de codigo tiene un boton de copiar automatico.

## Enlaces

### Enlaces internos

Usa rutas relativas a otros archivos Markdown:

```markdown
[Texto del enlace](./otro_archivo.md)
[Enlace a otro capitulo](../02_capitulo/01_tema.md)
```

Las extensiones `.md` se convierten automaticamente a URLs limpias durante el build.

### Enlaces externos

```markdown
[Google](https://google.com)
```

## Imagenes

Coloca las imagenes en el subdirectorio `images/` del capitulo:

```markdown
![Descripcion de la imagen](./images/diagrama.png)
```

Formatos soportados: PNG, JPG, GIF, SVG, WebP.
