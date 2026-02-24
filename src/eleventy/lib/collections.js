/**
 * Eleventy collection definitions.
 */

const INPUT_DIR = process.env.SELLEN_INPUT || 'clase';

function getOrderFromPath(path) {
  const parts = path.split('/').filter(p => p && p !== '.' && p !== 'clase' && p !== INPUT_DIR);
  let order = 0;
  parts.forEach((part, i) => {
    const weight = Math.pow(100, parts.length - i);
    if (part.match(/^z_/i)) { order += 90 * weight; return; }
    const letterMatch = part.match(/^([a-z])_/i);
    if (letterMatch) {
      order += (50 + letterMatch[1].toLowerCase().charCodeAt(0) - 97) * weight;
      return;
    }
    const numMatch = part.match(/^(\d+)/);
    if (numMatch) { order += parseInt(numMatch[1], 10) * weight; return; }
    order += 99 * weight;
  });
  return order;
}

function registerCollections(eleventyConfig) {
  eleventyConfig.addCollection("content", function(collectionApi) {
    return collectionApi.getFilteredByGlob(INPUT_DIR + "/**/*.md")
      .filter(item => {
        if (item.inputPath.includes('/docs/')) return false;
        if (item.inputPath.includes('b_libros')) return false;
        if (item.inputPath.includes('README_FLOW')) return false;
        if (item.inputPath.includes('README.md')) return false;
        if (item.inputPath.includes('task-pages')) return false;
        if (item.inputPath.includes('_task-pages')) return false;
        if (item.inputPath.includes('_calendario')) return false;
        if (item.inputPath.includes('_anuncios')) return false;
        if (item.inputPath.includes('??_')) return false;
        return true;
      })
      .sort((a, b) => {
        const orderA = a.data.order || getOrderFromPath(a.inputPath);
        const orderB = b.data.order || getOrderFromPath(b.inputPath);
        return orderA - orderB;
      });
  });

  eleventyConfig.addCollection("docs", function(collectionApi) {
    return collectionApi.getFilteredByGlob(INPUT_DIR + "/docs/**/*.md")
      .filter(item => !item.inputPath.includes('??_'))
      .sort((a, b) => {
        const orderA = a.data.order || getOrderFromPath(a.inputPath);
        const orderB = b.data.order || getOrderFromPath(b.inputPath);
        return orderA - orderB;
      });
  });
}

module.exports = { registerCollections, getOrderFromPath };
