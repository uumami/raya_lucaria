---
title: "Despliegue"
summary: "Publicar el sitio en GitHub Pages"
---

# Despliegue

## GitHub Pages

El sitio se despliega automaticamente a GitHub Pages usando GitHub Actions.

### Paso 1: Configurar el repositorio

1. Ve a **Settings > Pages** en tu repositorio de GitHub
2. En **Source**, selecciona **GitHub Actions**
3. No necesitas seleccionar una rama especifica

### Paso 2: Copiar el workflow

Copia el archivo `glintstone/.github/workflows/deploy.yaml` a tu repositorio:

```bash
mkdir -p .github/workflows
cp glintstone/.github/workflows/deploy.yaml .github/workflows/deploy.yaml
```

Este workflow:
- Se ejecuta automaticamente en cada push a `main`
- Se puede ejecutar manualmente desde la pestana **Actions**
- Auto-detecta el nombre del repositorio para el prefijo de ruta
- Funciona con cualquier dominio personalizado sin configuracion adicional

### Paso 3: Push

```bash
git add .github/workflows/deploy.yaml
git commit -m "Add GitHub Pages deployment"
git push
```

El sitio estara disponible en `https://{usuario}.github.io/{nombre-repo}/`.

## Dominio personalizado

Para publicar en un dominio personalizado como `midominio.com/{nombre-repo}/`:

### Configuracion unica (a nivel de organizacion o usuario)

1. Crea un repositorio llamado `{usuario}.github.io` (o `{org}.github.io`)
2. Agrega un archivo `CNAME` con tu dominio:
   ```
   www.midominio.com
   ```
3. Configura DNS:
   - **Registro A** apuntando a las IPs de GitHub Pages:
     ```
     185.199.108.153
     185.199.109.153
     185.199.110.153
     185.199.111.153
     ```
   - **Registro CNAME** para `www`: `{usuario}.github.io`

### Como funciona

Una vez configurado el dominio a nivel de usuario/organizacion, **todos** tus repositorios con GitHub Pages se sirven automaticamente bajo ese dominio:

```
https://www.midominio.com/repo-1/
https://www.midominio.com/repo-2/
https://www.midominio.com/curso-stats/
```

No necesitas configurar nada adicional en cada repositorio. El workflow auto-detecta el nombre del repositorio y lo usa como prefijo de ruta.

### Variable PATH_PREFIX

El prefijo de ruta se configura automaticamente. Solo necesitas sobreescribirlo si:
- Quieres un prefijo diferente al nombre del repositorio
- Tu dominio personalizado sirve el sitio en la raiz (`/`)

Para sobreescribir, edita el workflow:

```yaml
env:
  PATH_PREFIX: /mi-prefijo-custom/
```

## Resolucion de problemas

### Pagina en blanco

- Verifica que **Settings > Pages > Source** sea **GitHub Actions**
- Revisa que el build se complete sin errores en la pestana **Actions**
- Verifica que `PATH_PREFIX` coincida con el nombre del repositorio

### Assets faltantes (CSS, JS, imagenes)

- Abre la consola del navegador (F12) y busca errores 404
- Verifica que las rutas incluyan el prefijo correcto (`/{nombre-repo}/css/...`)
- Si usas dominio personalizado, asegura que el DNS este configurado correctamente

### Submodulo no se clona

- El workflow usa `submodules: recursive` — verifica que el submodulo apunte a un repositorio publico o accesible
- Si el submodulo es privado, configura un deploy key en el repositorio

### El dominio personalizado no funciona

- Verifica que el repositorio `{usuario}.github.io` existe y tiene el archivo `CNAME`
- Revisa la configuracion DNS con `dig www.midominio.com` — debe apuntar a GitHub Pages
- Espera hasta 24 horas para la propagacion de DNS
- En **Settings > Pages**, verifica que "Enforce HTTPS" este habilitado
