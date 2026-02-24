/**
 * Glintstone -- Eleventy Configuration
 * Thin orchestrator that delegates to lib/ modules.
 */

const { configureMarkdown } = require('./lib/markdown');
const { registerFilters } = require('./lib/filters');
const { registerCollections } = require('./lib/collections');
const { registerTransforms } = require('./lib/transforms');
const { configurePassthrough } = require('./lib/passthrough');
const { registerSearch } = require('./lib/search');
const { resolvePathPrefix } = require('./lib/path-prefix');

module.exports = function(eleventyConfig) {
  // Markdown pipeline (markdown-it + dollarmath + containers + anchors)
  const md = configureMarkdown();
  eleventyConfig.setLibrary("md", md);

  // Nunjucks filters
  registerFilters(eleventyConfig, md);

  // Content collections
  registerCollections(eleventyConfig);

  // HTML transforms (fix links, fix images)
  registerTransforms(eleventyConfig);

  // Passthrough copy (assets, fonts, vendor)
  configurePassthrough(eleventyConfig);

  // Search (pagefind in after event)
  registerSearch(eleventyConfig);

  // Default layout
  eleventyConfig.addGlobalData("layout", "layouts/base.njk");

  // Disable gitignore-based ignoring: the repo .gitignore lists clase-stage/
  // (the staging directory used as GLINTSTONE_INPUT in CI), which would cause
  // Eleventy to ignore all templates in its own input directory.
  eleventyConfig.setUseGitIgnore(false);

  // Watch targets
  eleventyConfig.addWatchTarget("./src/");

  // Ignore output
  eleventyConfig.ignores.add("../_site/**");

  // Dev server config
  eleventyConfig.setServerOptions({
    liveReload: true,
    port: parseInt(process.env.PORT) || 3000,
    // Bind to all interfaces so Docker port mapping works
    showAllHosts: true,
  });

  // BrowserSync fallback config (Eleventy 2.x)
  eleventyConfig.setBrowserSyncConfig({
    open: false,
    host: "0.0.0.0",
    ui: false,
  });

  // Path prefix
  const pathPrefix = resolvePathPrefix();

  // GLINTSTONE_INPUT allows build scripts to use a staging directory
  // that merges read-only clase/ content with generated templates
  const inputDir = process.env.GLINTSTONE_INPUT || "clase";

  // GLINTSTONE_ROOT: "glintstone" (submodule mode) or "." (template mode, framework at repo root)
  const glintstoneRoot = process.env.GLINTSTONE_ROOT || "glintstone";
  const rootPrefix = glintstoneRoot === "." ? "" : glintstoneRoot + "/";

  return {
    dir: {
      input: inputDir,
      includes: `../${rootPrefix}src/eleventy/_includes`,
      data: `../${rootPrefix}src/eleventy/_data`,
      output: "_site"
    },
    templateFormats: ["md", "njk", "html"],
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk",
    pathPrefix: pathPrefix
  };
};
