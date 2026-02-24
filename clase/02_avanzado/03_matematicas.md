---
title: "Matematicas"
summary: "Ejemplos de formulas matematicas con KaTeX"
---

# Matematicas con KaTeX

## Expresiones en Linea

La derivada de $f(x) = x^n$ es $f'(x) = nx^{n-1}$.

El teorema de Pitagoras establece que $a^2 + b^2 = c^2$.

La probabilidad condicional se define como $P(A|B) = \frac{P(A \cap B)}{P(B)}$.

## Expresiones en Bloque

La integral de Gauss:

$$\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}$$

La ecuacion de Euler:

$$e^{i\pi} + 1 = 0$$

Serie de Taylor:

$$f(x) = \sum_{n=0}^{\infty} \frac{f^{(n)}(a)}{n!}(x-a)^n$$

Matriz de transformacion:

$$A = \begin{pmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{pmatrix}$$

## Transformada de Fourier

La transformada de Fourier de una funcion $f(t)$ se define como:

$$\hat{f}(\omega) = \int_{-\infty}^{\infty} f(t) \, e^{-i\omega t} \, dt$$

Y su inversa:

$$f(t) = \frac{1}{2\pi} \int_{-\infty}^{\infty} \hat{f}(\omega) \, e^{i\omega t} \, d\omega$$

## Limites

$$\lim_{n \to \infty} \left(1 + \frac{1}{n}\right)^n = e$$

$$\lim_{x \to 0} \frac{\sin x}{x} = 1$$

Para la configuracion inicial del entorno, ve [[configuracion]].

## Ejercicio

:::exercise{title="Derivadas" difficulty="2"}

Calcula las siguientes derivadas:

1. $\frac{d}{dx}(3x^2 + 2x - 5)$
2. $\frac{d}{dx}(\sin(x) \cdot e^x)$
3. $\frac{d}{dx}\left(\frac{x^2 + 1}{x - 1}\right)$

:::

:::prompt{title="Reflexion sobre limites"}

Explica intuitivamente por que $\lim_{x \to 0} \frac{\sin x}{x} = 1$. Piensa en la geometria del circulo unitario y la relacion entre el arco y la cuerda cuando el angulo es pequeno.

:::
