---
title: "Diagramas"
summary: "Ejemplos de diagramas con Mermaid"
---

# Diagramas con Mermaid

## Diagrama de Flujo

```mermaid
graph TD
    A[Inicio] --> B{Tiene Docker?}
    B -->|Si| C[Clonar repo]
    B -->|No| D[Instalar Docker]
    D --> C
    C --> E[docker compose up dev]
    E --> F[Abrir localhost:3000]
    F --> G[Listo!]
```

## Diagrama de Secuencia

```mermaid
sequenceDiagram
    participant E as Estudiante
    participant S as Glintstone
    participant G as GitHub Pages

    E->>S: Escribe contenido en clase/
    S->>S: Preprocesamiento Python
    S->>S: Build Eleventy
    S->>S: Build Tailwind CSS
    S->>G: Deploy a GitHub Pages
    G->>E: Sitio disponible
```

## Diagrama de Clases

```mermaid
classDiagram
    class GlintstoneConfig {
        +SiteConfig site
        +SourceConfig source
        +ThemeConfig theme
        +load(path)
        +validate()
    }
    class Preprocessor {
        +extract_metadata()
        +generate_hierarchy()
        +aggregate_tasks()
    }
    GlintstoneConfig --> Preprocessor
```

## Diagrama de Gantt

```mermaid
gantt
    title Plan del Semestre
    dateFormat  YYYY-MM-DD
    section Modulo 1
    Introduccion           :done,    m1a, 2026-02-02, 7d
    Configuracion          :done,    m1b, after m1a, 7d
    Markdown               :active,  m1c, after m1b, 7d
    section Modulo 2
    Componentes            :         m2a, after m1c, 7d
    Matematicas            :         m2b, after m2a, 7d
    Primer Parcial         :crit,    m2c, 2026-03-16, 1d
    section Modulo 3
    Diagramas              :         m3a, after m2c, 7d
    Temas                  :         m3b, after m3a, 7d
    Proyecto               :         m3c, after m3b, 21d
    Segundo Parcial        :crit,    m3d, 2026-05-11, 1d
```

:::example{title="Tip: Mermaid y Temas"}

Los diagramas de Mermaid se adaptan automaticamente al tema seleccionado.
Prueba cambiar entre los temas usando el boton en la barra lateral.
Haz click en cualquier diagrama para verlo en pantalla completa.

:::
