/**
 * Pagefind search integration.
 * Runs pagefind as an Eleventy "after" event (production builds only).
 * In dev mode, search index is built by build.sh separately.
 */

function registerSearch(eleventyConfig) {
  eleventyConfig.on('eleventy.after', async () => {
    // Skip pagefind in serve/watch mode -- it's slow and unnecessary for dev
    if (process.env.ELEVENTY_SERVE || process.argv.includes('--serve')) {
      return;
    }

    try {
      const { execSync } = require('child_process');
      execSync('pagefind --site _site --glob "**/*.html"', {
        stdio: 'inherit',
        cwd: process.cwd(),
      });
    } catch (e) {
      // Pagefind not available -- search won't work but build continues
      console.log('[glintstone] Pagefind not available, skipping search index');
    }
  });
}

module.exports = { registerSearch };
