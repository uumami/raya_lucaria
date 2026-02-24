#!/bin/sh
set -e

# Glintstone Build Pipeline
# "Primal glintstone sorcery is the study of the stars themselves."

echo ""
echo "[*] Kindling site of grace..."
echo ""

# Add node_modules/.bin to PATH so all tools are available from /app
export PATH="/app/glintstone/src/eleventy/node_modules/.bin:$PATH"

# Step 0: Clean previous build output
rm -rf _site/*

# Step 1: Python preprocessing
echo "[*] Studying at the academy..."
PYTHONPATH=/app/glintstone/src python3 -m preprocessing build
echo ""

# Step 1b: Create staging directory (clase/ is read-only, so we
# symlink its contents into a writable dir and add generated templates)
STAGE=/app/clase-stage
rm -rf "$STAGE"
mkdir -p "$STAGE"
for f in /app/clase/*; do
  ln -s "$f" "$STAGE/$(basename "$f")"
done

# Symlink framework docs (if enabled and dir exists)
DOCS_ENABLED=$(python3 -c "
import json, pathlib
try:
    f = json.loads(pathlib.Path('glintstone/src/eleventy/_data/features.json').read_text())
    print('true' if f.get('docs', True) else 'false')
except: print('true')
")
if [ "$DOCS_ENABLED" = "true" ] && [ -d /app/glintstone/docs ]; then
  echo "[*] Linking documentation scrolls..."
  ln -s /app/glintstone/docs "$STAGE/docs"
fi

# Step 1c: Generate individual task page templates from taskPages.json
echo "[*] Inscribing task pages..."
python3 -c "
import json, pathlib
data = json.loads(pathlib.Path('glintstone/src/eleventy/_data/taskPages.json').read_text())
for p in data:
    tt = 'exams' if p['type'] == 'exam' else ('homework' if p['type'] == 'homework' else 'projects')
    pathlib.Path('$STAGE/_task-' + p['slug'] + '.njk').write_text(
        '---\nlayout: layouts/task-list.njk\ntitle: \"' + p['title'] + '\"\npermalink: /' + p['slug'] + '/\ntaskType: ' + tt + '\neleventyExcludeFromCollections: true\n---\n')
    print('    /' + p['slug'] + '/')
"
echo ""

# Step 1d: Generate calendario page (if CSV exists)
if [ -f calendario_temas.csv ]; then
  echo "[*] Charting the calendar..."
  PYTHONPATH=/app/glintstone/src python3 -m preprocessing.process_calendar
  cat > "$STAGE/_calendario.njk" << 'CALEOF'
---
layout: layouts/calendario.njk
title: "Calendario"
permalink: "/calendario/"
eleventyExcludeFromCollections: true
---
CALEOF
  echo ""
fi

# Step 1e: Generate announcements page (if anuncios.md exists)
if [ -f anuncios.md ]; then
  echo "[*] Inscribing announcements..."
  { echo "---"; echo 'title: "Anuncios"'; echo 'permalink: "/anuncios/"';
    echo "eleventyExcludeFromCollections: true"; echo "---"; echo "";
    cat anuncios.md; } > "$STAGE/_anuncios.md"
  python3 -c "
import json, pathlib
f = pathlib.Path('glintstone/src/eleventy/_data/features.json')
d = json.loads(f.read_text()); d['anuncios'] = True
f.write_text(json.dumps(d, indent=2))"
  echo ""
fi

# Step 2: Eleventy build (using staging dir as input)
echo "[*] Channeling glintstone sorcery..."
cd /app
GLINTSTONE_INPUT=clase-stage eleventy --config=glintstone/src/eleventy/.eleventy.js
echo ""

# Step 3: Tailwind CSS
echo "[*] Weaving golden threads..."
tailwindcss \
  -c glintstone/src/eleventy/tailwind.config.js \
  -i glintstone/src/eleventy/src/css/main.css \
  -o _site/css/styles.css \
  --minify
echo ""

# Step 4: JS bundle (esbuild)
echo "[*] Binding glintstone..."
esbuild \
  glintstone/src/eleventy/src/js/main.js \
  --bundle \
  --minify \
  --sourcemap \
  --outfile=_site/js/bundle.js \
  --format=iife \
  2>/dev/null || echo "    (no JS to bundle)"
echo ""

# Step 4b: Service worker and manifest
echo "[*] Preparing offline sorcery..."
cp glintstone/src/eleventy/src/sw.js _site/sw.js 2>/dev/null || true
python3 -c "
import json, pathlib
try:
    site = json.loads(pathlib.Path('glintstone/src/eleventy/_data/site.json').read_text())
except: site = {}
manifest = {
    'name': site.get('name', 'Course Site'),
    'short_name': site.get('name', 'Course')[:12],
    'start_url': '.',
    'display': 'standalone',
    'background_color': '#180a0a',
    'theme_color': '#e84040',
    'icons': [
        {'src': 'apple-touch-icon.png', 'sizes': '180x180', 'type': 'image/png'}
    ]
}
pathlib.Path('_site/manifest.json').write_text(json.dumps(manifest, indent=2))
" 2>/dev/null || true
echo ""

# Step 5: Copy static assets
echo "[*] Gathering runes..."
# Theme CSS files
mkdir -p _site/css/themes
cp glintstone/src/eleventy/src/css/themes/*.css _site/css/themes/ 2>/dev/null || true
# Self-hosted fonts
if [ -d glintstone/src/eleventy/src/fonts ]; then
  cp -r glintstone/src/eleventy/src/fonts _site/fonts
fi
# Favicon
cp clase/favicon.ico clase/apple-touch-icon.png _site/ 2>/dev/null || true
# .nojekyll for GitHub Pages
touch _site/.nojekyll
echo ""

# Step 6: Pagefind search index
echo "[*] Indexing the academy library..."
pagefind --site _site --glob "**/*.html" 2>/dev/null || echo "    (pagefind not available, skipping search index)"
echo ""

# Cleanup staging directory
rm -rf "$STAGE"

# Count pages
PAGE_COUNT=$(find _site -name "*.html" 2>/dev/null | wc -l | tr -d ' ')

echo ""
echo "  +-------------------------------------------+"
echo "  |                                           |"
echo "  |   -- Site of grace discovered --          |"
echo "  |                                           |"
echo "  |   Build complete. ${PAGE_COUNT} pages generated.     |"
echo "  |                                           |"
echo "  +-------------------------------------------+"
echo ""
