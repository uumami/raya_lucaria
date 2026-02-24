#!/bin/sh
set -e

# Glintstone Development Server
echo ""
echo "[*] Kindling site of grace (dev mode)..."
echo ""

# Add node_modules/.bin to PATH
export PATH="/app/glintstone/src/eleventy/node_modules/.bin:$PATH"

# Step 1: Preprocess
echo "[*] Studying at the academy..."
PYTHONPATH=/app/glintstone/src python3 -m preprocessing --verbose build
echo ""

# Step 1b: Create staging directory (clase/ is read-only, so we
# symlink its contents into a writable dir and add generated templates)
STAGE=/app/clase-stage
rm -rf "$STAGE"
mkdir -p "$STAGE"
for f in /app/clase/*; do
  base="$(basename "$f")"
  # Skip files handled separately by later build steps
  case "$base" in
    anuncios.md|calendario_temas.csv) continue ;;
  esac
  ln -s "$f" "$STAGE/$base"
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

# Step 1d: Generate calendario page (if CSV exists in content dir)
if [ -f clase/calendario_temas.csv ]; then
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

# Step 1e: Generate announcements page (if anuncios.md exists in content dir)
if [ -f clase/anuncios.md ]; then
  echo "[*] Inscribing announcements..."
  { echo "---"; echo 'title: "Anuncios"'; echo 'permalink: "/anuncios/"';
    echo "eleventyExcludeFromCollections: true"; echo "---"; echo "";
    cat clase/anuncios.md; } > "$STAGE/_anuncios.md"
  python3 -c "
import json, pathlib
f = pathlib.Path('glintstone/src/eleventy/_data/features.json')
d = json.loads(f.read_text()); d['anuncios'] = True
f.write_text(json.dumps(d, indent=2))"
  echo ""
fi

# Step 1f: Generate graph page (if enabled)
GRAPH_ENABLED=$(python3 -c "
import json, pathlib
try:
    f = json.loads(pathlib.Path('glintstone/src/eleventy/_data/features.json').read_text())
    print('true' if f.get('graph', True) else 'false')
except: print('true')
")
if [ "$GRAPH_ENABLED" = "true" ]; then
  echo "[*] Charting the primeval current..."
  cat > "$STAGE/_grafo.njk" << 'GRAFEOF'
---
layout: layouts/graph.njk
title: "Grafo del Curso"
permalink: /grafo/
eleventyExcludeFromCollections: true
---
GRAFEOF
fi

# Step 2: Build CSS once
echo "[*] Weaving golden threads..."
mkdir -p _site/css/themes
tailwindcss \
  -c glintstone/src/eleventy/tailwind.config.js \
  -i glintstone/src/eleventy/src/css/main.css \
  -o _site/css/styles.css
cp glintstone/src/eleventy/src/css/themes/*.css _site/css/themes/ 2>/dev/null || true
echo ""

# Step 2b: Service worker and manifest
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

# Step 2c: Bundle JavaScript
echo "[*] Forging armaments..."
mkdir -p _site/js
esbuild \
  glintstone/src/eleventy/src/js/main.js \
  --bundle --sourcemap \
  --outfile=_site/js/bundle.js \
  --format=iife \
  2>/dev/null || echo "    (no JS to bundle)"
echo ""

# Step 3: Copy static assets
if [ -d glintstone/src/eleventy/src/fonts ]; then
  cp -r glintstone/src/eleventy/src/fonts _site/fonts
fi
cp clase/favicon.ico clase/apple-touch-icon.png _site/ 2>/dev/null || true
touch _site/.nojekyll

# Step 4: Start Eleventy dev server (using staging dir as input)
SERVE_PORT=${PORT:-3000}
echo "[*] Site of grace kindled. Watching for changes..."
echo "    http://localhost:${SERVE_PORT}"
echo ""

GLINTSTONE_INPUT=clase-stage eleventy \
  --config=glintstone/src/eleventy/.eleventy.js \
  --serve \
  --port=${SERVE_PORT}
