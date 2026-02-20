---
title: "Configuracion"
summary: "Referencia completa de glintstone.yaml"
---

# Configuracion

Toda la configuracion del sitio se define en el archivo `glintstone.yaml` en la raiz del repositorio del curso.

## Referencia completa

### site (requerido)

```yaml
site:
  name: "Mi Curso - ITAM"        # Titulo del sitio (requerido)
  description: "Semestre 2026"    # Subtitulo/descripcion
  language: "es"                  # Idioma del contenido (BCP 47)
  author: "ITAM"                 # Autor/institucion
```

| Campo | Tipo | Default | Requerido |
|-------|------|---------|-----------|
| `name` | string | -- | Si |
| `description` | string | `""` | No |
| `language` | string | `"es"` | No |
| `author` | string | `""` | No |

### repository

```yaml
repository:
  name: "mi-curso"                # Nombre del repo (auto-detectado de git)
  org: "mi-org"                   # Organizacion de GitHub
  url: "git@github.com:org/repo"  # URL completa del repositorio
```

Se auto-detecta desde `git remote` si no se especifica. El `name` se usa como prefijo de ruta para GitHub Pages.

### source

```yaml
source:
  content_dir: "clase"            # Directorio de contenido
  exclude:                        # Patrones a excluir
    - "b_libros"
    - "README_FLOW.md"
```

### theme

```yaml
theme:
  default: "raya-lucaria"         # Tema por defecto
  available:                      # Temas disponibles
    - raya-lucaria
    - leyndell
    - eva-02-dark
    - eva-02-light
```

### build

```yaml
build:
  output_dir: "_site"             # Directorio de salida
```

### navigation

```yaml
navigation:
  show_breadcrumbs: true          # Mostrar ruta de navegacion
  show_sidebar: true              # Mostrar barra lateral
  show_prev_next: true            # Mostrar botones anterior/siguiente
  show_toc: true                  # Mostrar tabla de contenidos
```

### features

```yaml
features:
  search: true                    # Busqueda con Pagefind
  theme_toggle: true              # Selector de temas
  font_toggle: true               # Opciones de fuente
  copy_code_button: true          # Boton de copiar en bloques de codigo
  math: true                      # Ecuaciones con KaTeX
  mermaid: true                   # Diagramas con Mermaid
  docs: true                      # Documentacion integrada
```

### tasks

```yaml
tasks:
  pages:
    - type: homework
      title: "Tareas"
      slug: "tareas"
    - type: exam
      title: "Examenes"
      slug: "examenes"
    - type: project
      title: "Proyectos"
      slug: "proyectos"
```

Define las paginas de agregacion de tareas. Los tipos validos son: `homework`, `exam`, `project`.
