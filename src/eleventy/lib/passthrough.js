/**
 * Passthrough copy configuration.
 * Uses globs instead of hardcoded prefixes.
 */

const INPUT_DIR = process.env.SELLEN_INPUT || 'clase';

function configurePassthrough(eleventyConfig) {
  // CSS
  eleventyConfig.addPassthroughCopy({
    "../glintstone/src/eleventy/src/css": "css"
  });

  // Self-hosted fonts
  eleventyConfig.addPassthroughCopy({
    "../glintstone/src/eleventy/src/fonts": "fonts"
  });

  // All images from content (scoped to input dir to avoid matching _site/)
  eleventyConfig.addPassthroughCopy(INPUT_DIR + "/**/images/**");

  // All PDFs from content
  eleventyConfig.addPassthroughCopy(INPUT_DIR + "/**/*.pdf");

  // Favicon files
  eleventyConfig.addPassthroughCopy(INPUT_DIR + "/*.ico");
  eleventyConfig.addPassthroughCopy(INPUT_DIR + "/apple-touch-icon.png");
  eleventyConfig.addPassthroughCopy(INPUT_DIR + "/favicon*.png");

  // .nojekyll
  eleventyConfig.addPassthroughCopy(".nojekyll");
}

module.exports = { configurePassthrough };
