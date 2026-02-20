---
title: "Diagramas"
summary: "Diagramas con Mermaid"
---

# Diagramas

El sitio soporta diagramas usando [Mermaid](https://mermaid.js.org/), que genera graficos a partir de texto.

## Sintaxis

Usa un bloque de codigo con el lenguaje `mermaid`:

````markdown
```mermaid
graph TD
    A[Inicio] --> B[Fin]
```
````

## Tipos de diagramas

### Diagrama de flujo

````markdown
```mermaid
graph TD
    A[Inicio] --> B{Condicion?}
    B -->|Si| C[Accion 1]
    B -->|No| D[Accion 2]
    C --> E[Fin]
    D --> E
```
````

### Diagrama de secuencia

````markdown
```mermaid
sequenceDiagram
    participant C as Cliente
    participant S as Servidor
    C->>S: Solicitud HTTP
    S-->>C: Respuesta 200 OK
```
````

### Diagrama de clases

````markdown
```mermaid
classDiagram
    class Animal {
        +String nombre
        +int edad
        +comer()
    }
    class Perro {
        +ladrar()
    }
    Animal <|-- Perro
```
````

### Diagrama de Gantt

````markdown
```mermaid
gantt
    title Cronograma del proyecto
    dateFormat YYYY-MM-DD
    section Fase 1
    Investigacion :a1, 2026-01-01, 14d
    Diseno        :a2, after a1, 7d
    section Fase 2
    Implementacion :b1, after a2, 21d
    Pruebas        :b2, after b1, 7d
```
````

## Adaptacion al tema

Los diagramas se adaptan automaticamente a los colores del tema activo. No necesitas configurar colores manualmente.
