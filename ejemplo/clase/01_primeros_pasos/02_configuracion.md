---
title: "Configuracion"
summary: "Configuracion del entorno de trabajo"
---

# Configuracion del Entorno

## Requisitos

- Docker instalado
- Git configurado
- Editor de texto

## Prompt para ChatGPT

:::prompt{title="Generar README" for="ChatGPT"}

Genera un README.md para un curso universitario de ciencia de datos.
Incluye: descripcion del curso, requisitos, calendario tentativo,
y politicas de evaluacion.

:::

## Ejemplo de Configuracion

:::example{title="glintstone.yaml basico"}

```yaml
site:
  name: "Mi Curso - ITAM"
  description: "Primavera 2026"
  language: "es"

source:
  content_dir: "clase"

theme:
  default: "raya-lucaria"
```

Este es el archivo minimo necesario para configurar Glintstone.

:::

## Formulas Matematicas

El framework soporta matematicas con KaTeX. Por ejemplo, la formula cuadratica:

$$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$

Y expresiones en linea como $E = mc^2$ o $\sum_{i=1}^{n} i = \frac{n(n+1)}{2}$.
