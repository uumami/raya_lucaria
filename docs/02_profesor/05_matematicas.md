---
title: "Matematicas"
summary: "Ecuaciones y formulas con KaTeX"
---

# Matematicas

El sitio soporta ecuaciones matematicas usando la sintaxis de LaTeX, renderizadas por [KaTeX](https://katex.org/docs/supported).

## Matematicas en linea

Usa signos de dolar simples para formulas dentro del texto:

```markdown
La energia se define como $E = mc^2$ segun Einstein.
```

Resultado: La energia se define como $E = mc^2$ segun Einstein.

## Matematicas en bloque

Usa doble signo de dolar en lineas separadas:

```markdown
$$
\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
$$
```

$$
\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
$$

## Ejemplos utiles

### Fracciones y raices

```markdown
$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$
```

### Matrices

```markdown
$$
A = \begin{pmatrix}
a_{11} & a_{12} \\
a_{21} & a_{22}
\end{pmatrix}
$$
```

### Sumatorias y productos

```markdown
$$
\sum_{i=1}^{n} i = \frac{n(n+1)}{2}
$$
```

## Cosas a tener en cuenta

- `$5` por si solo **no** es matematicas (signo de dolar seguido de digito)
- `--` **no** se convierte en guion largo (el tipografo esta desactivado)
- Las matematicas dentro de bloques de codigo no se renderizan
- Para una referencia completa de funciones soportadas, consulta la [documentacion de KaTeX](https://katex.org/docs/supported)
