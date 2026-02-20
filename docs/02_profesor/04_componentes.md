---
title: "Componentes"
summary: "Tareas, ejercicios, ejemplos, examenes, proyectos, quizzes y embeds"
---

# Componentes

Los componentes son bloques especiales de contenido con estilos y funcionalidades propias. Hay ocho tipos disponibles.

## Sintaxis general

```markdown
:::tipo{atributo="valor" otro="valor"}

Contenido en Markdown aqui.

:::
```

**Reglas importantes:**

- La linea de apertura `:::tipo{...}` debe estar sola en su linea
- La linea de cierre `:::` debe estar sola en su linea (solo tres dos puntos)
- Los atributos usan comillas dobles: `clave="valor"`
- El contenido entre las marcas se renderiza como Markdown

## Tipos de componentes

### homework (Tarea)

```markdown
:::homework{id="tarea-01" title="Nombre de la tarea" due="2026-03-01" points="10"}

Instrucciones de la tarea aqui.

:::
```

| Atributo | Requerido | Descripcion |
|----------|-----------|-------------|
| `id` | Si | Identificador unico (se agrega a la pagina de tareas) |
| `title` | Si | Nombre a mostrar |
| `due` | No | Fecha de entrega (formato YYYY-MM-DD) |
| `points` | No | Valor en puntos |

### exercise (Ejercicio)

```markdown
:::exercise{title="Nombre del ejercicio" difficulty="2"}

Instrucciones del ejercicio.

:::
```

| Atributo | Requerido | Descripcion |
|----------|-----------|-------------|
| `title` | Si | Nombre a mostrar |
| `difficulty` | No | Dificultad 1-5 (se muestra como estrellas) |

### prompt

```markdown
:::prompt{title="Nombre del prompt" for="ChatGPT"}

Tu texto del prompt aqui.

:::
```

| Atributo | Requerido | Descripcion |
|----------|-----------|-------------|
| `title` | Si | Nombre a mostrar |
| `for` | No | Herramienta de IA destino |

### example (Ejemplo)

```markdown
:::example{title="Nombre del ejemplo"}

Contenido del ejemplo.

:::
```

| Atributo | Requerido | Descripcion |
|----------|-----------|-------------|
| `title` | Si | Nombre a mostrar |

### exam (Examen)

```markdown
:::exam{id="parcial-01" title="Nombre del examen" date="2026-03-15" location="Salon 101" duration="2h"}

Detalles del examen.

:::
```

| Atributo | Requerido | Descripcion |
|----------|-----------|-------------|
| `id` | Si | Identificador unico |
| `title` | Si | Nombre a mostrar |
| `date` | No | Fecha del examen (YYYY-MM-DD) |
| `location` | No | Ubicacion fisica |
| `duration` | No | Duracion |

### project (Proyecto)

```markdown
:::project{id="proy-01" title="Nombre del proyecto" due="2026-05-01" points="100"}

Descripcion del proyecto.

:::
```

| Atributo | Requerido | Descripcion |
|----------|-----------|-------------|
| `id` | Si | Identificador unico |
| `title` | Si | Nombre a mostrar |
| `due` | No | Fecha de entrega (YYYY-MM-DD) |
| `points` | No | Valor en puntos |

### quiz (Quiz interactivo)

```markdown
:::quiz{title="Verificacion de conceptos"}

- [ ] Opcion incorrecta
- [x] Opcion correcta
- [ ] Otra opcion incorrecta

:::
```

| Atributo | Requerido | Descripcion |
|----------|-----------|-------------|
| `title` | Si | Nombre a mostrar |

El quiz transforma la lista de opciones en botones interactivos. Las opciones marcadas con `[x]` se consideran correctas. Al hacer clic, se muestra retroalimentacion visual (verde/rojo) y un boton "Reintentar".

### embed (Recurso externo)

```markdown
:::embed{src="https://www.youtube.com/embed/VIDEO_ID" title="Video tutorial"}

Descripcion opcional del recurso.

:::
```

| Atributo | Requerido | Descripcion |
|----------|-----------|-------------|
| `src` | Si | URL del recurso (iframe) |
| `title` | No | Titulo del recurso |
| `type` | No | Tipo de recurso |

El componente embed renderiza un iframe responsivo en formato 16:9. Ideal para videos de YouTube, presentaciones de Google Slides, o cualquier recurso embebible.

## Agregacion de tareas

Los componentes `homework`, `exam` y `project` con atributo `id` se agregan automaticamente a sus paginas respectivas (`/tareas/`, `/examenes/`, `/proyectos/`). Esto permite que los estudiantes vean todas las tareas, examenes o proyectos en un solo lugar.

## Errores comunes

- **Olvidar cerrar con `:::`** -- El componente se extiende hasta el final del archivo
- **Comillas simples en atributos** -- Usa siempre comillas dobles: `title="correcto"` no `title='incorrecto'`
- **IDs duplicados** -- Cada `id` debe ser unico en todo el curso
- **Formato de fecha incorrecto** -- Usa siempre `YYYY-MM-DD`
