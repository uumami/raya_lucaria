---
title: "Despliegue"
summary: "Publicar el sitio en GitHub Pages"
---

# Despliegue

## GitHub Pages

El sitio se despliega automaticamente a GitHub Pages usando GitHub Actions.

### Configuracion del repositorio

1. Ve a **Settings > Pages** en tu repositorio de GitHub
2. En **Source**, selecciona **GitHub Actions**
3. No necesitas seleccionar una rama especifica

### Archivo de GitHub Actions

Crea `.github/workflows/deploy.yml` en tu repositorio:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true

      - name: Build site
        run: docker compose -f glintstone/docker/docker-compose.yaml up build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: _site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
    steps:
      - name: Deploy to GitHub Pages
        uses: actions/deploy-pages@v4
```

### Variable PATH_PREFIX

Para que los enlaces funcionen correctamente en GitHub Pages, el prefijo de ruta se configura automaticamente desde el nombre del repositorio. Si necesitas un prefijo diferente, configura la variable de entorno `PATH_PREFIX`:

```yaml
env:
  PATH_PREFIX: /mi-curso
```

## Dominio personalizado

Para usar un dominio personalizado:

1. Ve a **Settings > Pages > Custom domain**
2. Ingresa tu dominio
3. Agrega los registros DNS correspondientes
4. Cuando uses un dominio personalizado, `PATH_PREFIX` debe ser `/`

## Resolucion de problemas

### Pagina en blanco

- Verifica que `PATH_PREFIX` este configurado correctamente
- Revisa que el build de Docker se complete sin errores

### Assets faltantes (CSS, JS)

- Verifica que el prefijo de ruta coincida con el nombre del repositorio
- Revisa la consola del navegador para ver errores 404

### Submodulo no se clona

- Asegura que el checkout de GitHub Actions use `submodules: true`
- Verifica que el submodulo apunte a un repositorio accesible
