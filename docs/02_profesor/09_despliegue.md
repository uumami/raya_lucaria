---
title: "Despliegue"
summary: "Publicar el sitio en GitHub Pages"
---

# Despliegue

## GitHub Pages

El sitio se despliega automaticamente a GitHub Pages con cada push a `main`.

### Paso 1: Crear tu repositorio

Usa este repositorio como **template** en GitHub:

1. Ve al repositorio de Raya Lucaria en GitHub
2. Click en **"Use this template" > "Create a new repository"**
3. Nombra tu repositorio (ejemplo: `mi-curso-stats`)

Tu sitio estara disponible en `https://{usuario}.github.io/{nombre-repo}/`.

### Paso 2: Habilitar GitHub Pages

1. Ve a **Settings > Pages** en tu nuevo repositorio
2. En **Source**, selecciona **GitHub Actions**
3. Listo — el workflow `.github/workflows/deploy.yaml` ya esta incluido

### Paso 3: Personalizar

1. Edita `glintstone.yaml` con el nombre de tu curso
2. Reemplaza el contenido de `clase/` con tus materiales
3. Push a `main` — el sitio se construye y despliega automaticamente

### Como funciona el despliegue

El workflow detecta automaticamente la estructura del repositorio y funciona en dos modos:

- **Modo template**: Framework en `src/` (cuando usas el template)
- **Modo submodulo**: Framework en `glintstone/` (cuando usas submodulo git)

El prefijo de ruta (`PATH_PREFIX`) se auto-detecta del nombre del repositorio. No necesitas configurar nada.

## Dominio personalizado

Para publicar en un dominio personalizado como `midominio.com/{nombre-repo}/`:

### Configuracion unica (a nivel de usuario u organizacion)

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

Una vez configurado, **todos** tus repositorios con GitHub Pages se sirven bajo ese dominio:

```
https://www.midominio.com/curso-stats/
https://www.midominio.com/curso-algebra/
https://www.midominio.com/curso-redes/
```

No necesitas configurar nada adicional en cada repositorio — todo es automatico.

Si **no** configuras un dominio personalizado, tus sitios se sirven en el dominio por defecto de GitHub:

```
https://{usuario}.github.io/curso-stats/
https://{usuario}.github.io/curso-algebra/
```

Ambos casos funcionan sin cambiar el workflow.

## Resolucion de problemas

### Pagina en blanco

- Verifica que **Settings > Pages > Source** sea **GitHub Actions**
- Revisa que el build se complete en la pestana **Actions**

### Assets faltantes (CSS, JS, imagenes)

- Abre la consola del navegador (F12) y busca errores 404
- Verifica que las rutas incluyan el prefijo correcto (`/{nombre-repo}/css/...`)

### El dominio personalizado no funciona

- Verifica que el repositorio `{usuario}.github.io` tiene el archivo `CNAME`
- Revisa DNS con `dig www.midominio.com`
- Espera hasta 24 horas para propagacion de DNS
- Habilita "Enforce HTTPS" en **Settings > Pages**
