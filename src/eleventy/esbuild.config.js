/**
 * esbuild configuration for glintstone JS bundle.
 */
const esbuild = require('esbuild');

esbuild.build({
  entryPoints: ['src/eleventy/src/js/main.js'],
  bundle: true,
  minify: true,
  sourcemap: true,
  outfile: '_site/js/bundle.js',
  format: 'iife',
  target: ['es2020'],
}).catch(() => process.exit(1));
