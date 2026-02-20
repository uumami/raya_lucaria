#!/bin/sh
set -e

# Glintstone Slide Generator
# Converts Markdown files with `slides: true` frontmatter into reveal.js presentations.

echo ""
echo "[*] Generating slide decks..."
echo ""

SLIDES_DIR="_site/slides"
mkdir -p "$SLIDES_DIR"

python3 << 'PYEOF'
import os, re, pathlib

REVEAL_CDN = 'https://cdn.jsdelivr.net/npm/reveal.js@5.1.0'
SLIDES_DIR = '_site/slides'

def has_slides_flag(content):
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, '', content
    fm = match.group(1)
    body = content[match.end():]
    title = ''
    for line in fm.split('\n'):
        if line.strip().startswith('title:'):
            title = line.split(':', 1)[1].strip().strip('"').strip("'")
    if re.search(r'slides:\s*true', fm, re.IGNORECASE):
        return True, title, body
    return False, '', content

def split_slides(body):
    slides = []
    current = []
    for line in body.split('\n'):
        if line.startswith('## ') and current:
            slides.append('\n'.join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        slides.append('\n'.join(current))
    return slides

def md_to_html_basic(md):
    lines = md.split('\n')
    html = []
    in_list = False
    in_code = False
    for line in lines:
        if line.startswith('```'):
            if in_code:
                html.append('</code></pre>')
                in_code = False
            else:
                html.append('<pre><code>')
                in_code = True
            continue
        if in_code:
            html.append(line)
            continue
        if line.startswith('### '):
            html.append(f'<h3>{line[4:]}</h3>')
        elif line.startswith('## '):
            html.append(f'<h2>{line[3:]}</h2>')
        elif line.startswith('# '):
            html.append(f'<h1>{line[2:]}</h1>')
        elif line.startswith('- '):
            if not in_list:
                html.append('<ul>')
                in_list = True
            html.append(f'<li>{line[2:]}</li>')
        elif line.strip() == '' and in_list:
            html.append('</ul>')
            in_list = False
            html.append('')
        elif line.startswith('**') and line.endswith('**'):
            html.append(f'<strong>{line[2:-2]}</strong>')
        elif line.strip():
            html.append(f'<p>{line}</p>')
        else:
            html.append('')
    if in_list:
        html.append('</ul>')
    return '\n'.join(html)

def generate_reveal_html(title, slides):
    sections = []
    for slide in slides:
        slide_html = md_to_html_basic(slide.strip())
        if slide_html.strip():
            sections.append(f'        <section>\n{slide_html}\n        </section>')

    return f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="{REVEAL_CDN}/dist/reveal.css">
  <link rel="stylesheet" href="{REVEAL_CDN}/dist/theme/black.css">
  <style>
    .reveal h1, .reveal h2, .reveal h3 {{ text-transform: none; }}
    .reveal pre {{ font-size: 0.6em; }}
    .reveal ul {{ text-align: left; }}
  </style>
</head>
<body>
  <div class="reveal">
    <div class="slides">
{chr(10).join(sections)}
    </div>
  </div>
  <script src="{REVEAL_CDN}/dist/reveal.js"></script>
  <script>Reveal.initialize({{ hash: true }});</script>
</body>
</html>'''

# Scan for markdown files with slides: true
count = 0
for root, dirs, files in os.walk('clase'):
    for f in files:
        if not f.endswith('.md'):
            continue
        filepath = os.path.join(root, f)
        content = pathlib.Path(filepath).read_text(encoding='utf-8')
        has_flag, title, body = has_slides_flag(content)
        if not has_flag:
            continue
        if not title:
            title = f.replace('.md', '').replace('_', ' ').title()
        slides = split_slides(body)
        html = generate_reveal_html(title, slides)
        slug = f.replace('.md', '')
        out_path = os.path.join(SLIDES_DIR, slug + '.html')
        pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(out_path).write_text(html, encoding='utf-8')
        count += 1
        print(f'    {slug}.html ({len(slides)} slides)')

if count == 0:
    print('    No slides to generate (add slides: true to frontmatter)')
else:
    print(f'    {count} presentation(s) generated')
PYEOF

echo ""
echo "[*] Slide generation complete."
echo ""
