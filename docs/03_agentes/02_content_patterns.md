---
title: "Content Patterns"
summary: "Naming rules, sort keys, frontmatter, and link resolution"
---

# Content Patterns

## Sort Key Logic

The `get_sort_key()` function (in `generate_hierarchy.py`) and `getOrderFromPath()` (in `collections.js`) determine content ordering:

1. Numeric prefix (`01_`, `02_`) -- Sorted by number
2. Letter prefix (`a_`, `b_`) -- Sorted after numbers (50 + char code offset)
3. `z_` prefix -- Sorted last (weight 90)
4. `??_` prefix -- Excluded from build entirely
5. `00_` prefix -- Index files, hidden from nav but used as section landing page

The sort uses a weighted position system where each path segment gets a weight of `100^(depth)`, creating a hierarchical sort order.

## Frontmatter Schema

All fields are optional:

```yaml
---
title: "Page Title"          # string, generated from filename if omitted
summary: "Brief description" # string, used in chapter index cards
tags: [tag1, tag2]          # list of strings
layout: layouts/base.njk    # string, template path
order: 5                    # number, overrides filename-based ordering
---
```

The `extract_metadata.py` module reads frontmatter using `yaml.safe_load()` and builds a dict keyed by relative file path.

## Component Regex

Components use markdown-it-container with this pattern:

```
:::type{key="value" key2="value2"}
content
:::
```

The attribute parsing regex in `components.js`:
```javascript
/(\w+)="([^"]*)"/g
```

This extracts key-value pairs from the opening fence. The component type is matched against the REGISTRY object in `components.js`.

## Link Resolution

- Internal `.md` links are converted to clean URLs by a markdown-it plugin
- `./file.md` becomes `/chapter/file/`
- `../other_chapter/file.md` is resolved relative to the current file

## Image Resolution

- Images referenced as `./images/photo.png` are resolved relative to the source file
- The build copies image directories via glob patterns
- Supported formats: PNG, JPG, GIF, SVG, WebP

## The 00_index.md Convention

Every directory should have a `00_index.md` file:
- It serves as the landing page for that section
- It should use `layout: layouts/chapter.njk` to show child cards
- Its title becomes the section name in navigation
- It's hidden from nav (the parent directory entry links to it instead)
