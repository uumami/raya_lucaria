/**
 * HTML transforms: fix .md links and image paths.
 */

function registerTransforms(eleventyConfig) {
  eleventyConfig.addTransform("fixMdLinks", function(content, outputPath) {
    if (!outputPath || !outputPath.endsWith(".html")) return content;

    // Fix href="...*.md" -> href=".../"
    content = content.replace(
      /href="([^"]*?)\.md(#[^"]*)?"/g,
      (match, path, hash) => {
        if (path.startsWith('http://') || path.startsWith('https://')) return match;
        let newPath = path;
        if (newPath.startsWith('./')) {
          newPath = '../' + newPath.slice(2);
        }
        return `href="${newPath}/${hash || ''}"`;
      }
    );

    // Fix image paths: both ./images/ and images/ (without ./)
    content = content.replace(
      /src="(\.\/)?images\//g,
      'src="../images/'
    );

    return content;
  });
}

module.exports = { registerTransforms };
