---
id: static-path
title: Static Path
summary: Nested fixture page for deployment-neutral static paths.
status: ready
aliases:
  - old-static-path
---

# Static Path

This nested fixture page checks deployment-neutral relative URLs from generated subdirectories.

Return to the [fixture root](raya:render-root), open the [same static path note](../_assets/diagrams/static-path.txt), and inspect the [local colocated note](_assets/local-static-path.txt).

## Nested Rich Content

Nested pages use the same renderer support resource through relative URLs.

> [!TIP]
> This nested callout proves rich rendering is not root-page only.

| Link kind | Fixture target |
| --- | --- |
| Stable ID | [root](raya:render-root) |
| Local Markdown | [root](../0_index.md) |
| Local asset | [local note](_assets/local-static-path.txt) |

Inline math $x_i$ and pre-rendered display math use the same local renderer resources:

$$
\bar{x} = \frac{1}{n}\sum_i x_i
$$

```python
print("display only")
```

## Nested Duplicate

First nested duplicate.

## Nested Duplicate

Second nested duplicate.
