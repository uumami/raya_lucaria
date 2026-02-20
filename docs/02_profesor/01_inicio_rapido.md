---
title: "Inicio rapido"
summary: "Primeros pasos para crear tu sitio de curso"
---

# Inicio rapido

## Prerequisitos

- [Docker](https://docs.docker.com/get-docker/) instalado en tu computadora
- [Git](https://git-scm.com/) instalado
- Una cuenta de GitHub (para despliegue)

## Configuracion inicial

### 1. Crea tu repositorio de curso

Crea un nuevo repositorio en GitHub para tu curso.

### 2. Agrega glintstone como submodulo

```bash
git submodule add <url-del-repo-raya-lucaria> glintstone
```

### 3. Crea el archivo de configuracion

Crea un archivo `glintstone.yaml` en la raiz de tu repositorio:

```yaml
site:
  name: "Mi Curso - ITAM"
  description: "Semestre Primavera 2026"
  language: "es"
  author: "ITAM"

features:
  search: true
  math: true
  mermaid: true
```

### 4. Crea tu primer contenido

```bash
mkdir -p clase
```

Crea el archivo `clase/00_index.md`:

```markdown
---
title: "Bienvenida"
layout: layouts/chapter.njk
---

# Bienvenido al curso

Este es el sitio web del curso.
```

### 5. Construye el sitio

```bash
docker compose -f glintstone/docker/docker-compose.yaml up build
```

El sitio generado estara en `_site/`.

### 6. Servidor de desarrollo

Para ver cambios en tiempo real:

```bash
docker compose -f glintstone/docker/docker-compose.yaml up dev
```

Abre `http://localhost:3000` en tu navegador.
