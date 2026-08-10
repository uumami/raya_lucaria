---
id: docs-guides-es-colaboradores-publicar-cursos
title: Publicar Cursos Independientes
nav_title: Publicar Cursos
summary: Publica un curso como salida estatica portable sin perder la propiedad del equipo del curso.
status: ready
---
# Publicar Cursos Independientes

GitHub Actions y GitHub Pages son adaptadores opcionales para integracion
continua, hosting estatico y TLS. No cambian el contrato de Raya ni vuelven a
GitHub propietario del curso. El equipo del curso conserva la fuente canonica,
la politica de revision y la decision de publicar; GitHub guarda logs del flujo
y sirve artifacts generados publicos que se hayan subido.

## Construye primero; elige el host despues

`artifact/` es output reconstruible, nunca fuente canonica. Una publicacion
portable siempre se produce con el ciclo normal:

```bash
raya validate .
raya build .
raya artifacts inspect artifact
```

La ruta estatica publicable es `artifact/site/`. Para migrar a otro proveedor,
construye el mismo curso y sube ese directorio al nuevo host estatico. Para
revision local o autoalojada, sirvelo con cualquier servidor de archivos
estaticos ordinario:

```bash
raya build .
python3 -m http.server 8000 --directory artifact/site
```

Las cuotas, retencion, disponibilidad, funciones soportadas y precios del
proveedor son externos y pueden cambiar. Conserva la fuente del curso en su
propio repositorio y no versionas `artifact/`; asi la migracion y la recuperacion
no dependen de un proveedor.

## Adaptador de GitHub Pages

Para un curso de la organizacion `raya-lucaria`, usa el flujo reutilizable del
framework con un SHA completo de commit. El caller se mantiene pequeno y posee
solo sus triggers y autoridad de release:

```yaml
name: Verify and publish course
on:
  push:
  pull_request:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: pages
  cancel-in-progress: true
jobs:
  course-pages:
    uses: raya-lucaria/raya-lucaria.github.io/.github/workflows/reusable-course-pages.yml@FULL_FRAMEWORK_SHA
    with:
      course_path: .
```

Sustituye `FULL_FRAMEWORK_SHA` solamente mediante un pull request revisado. No
uses una rama ni un tag. El flujo reutilizable valida, construye, inspecciona y
sube solo `artifact/site/`. Verifica pull requests, pero despliega solo un push
a la rama principal del curso.

Configura GitHub Actions como origen de Pages antes del primer deploy. Protege
la rama principal y el environment `github-pages` antes de agregar el workflow
caller. Limita la autoridad de deployment a mantenedores de confianza del curso.

## Limite de origen compartido

Los project sites de la organizacion se sirven bajo `rayalucaria.org`, por
ejemplo `https://rayalucaria.org/ia_o26/`. Por tanto comparten un mismo origen
web publico. Trata a quien pueda publicar una rama protegida del curso como una
persona de confianza para ese origen. Exige revision en ramas principales,
prohibe force pushes y no alojes aplicaciones con cookies autenticadas, tokens
de navegador o credenciales en este dominio. Los sitios de cursos permanecen
material publico estatico.
