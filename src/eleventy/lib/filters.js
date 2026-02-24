/**
 * Nunjucks filters for glintstone.
 */

function registerFilters(eleventyConfig, md) {
  // Render markdown content
  eleventyConfig.addFilter("renderMarkdown", function(content) {
    if (!content) return '';
    return md.render(content);
  });

  // Format date in Spanish (Mexico City timezone)
  eleventyConfig.addFilter("formatDate", function(date) {
    if (!date) return '';
    const d = new Date(date + 'T12:00:00');
    return d.toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      timeZone: 'America/Mexico_City'
    });
  });

  // Format date as short relative badge
  eleventyConfig.addFilter("formatDateRelative", function(date) {
    if (!date) return '';
    const d = new Date(date + 'T12:00:00');
    const now = new Date();
    const diff = d - now;
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));

    if (days < 0) return 'Pasado';
    if (days === 0) return 'Hoy';
    if (days === 1) return 'Ma\u00f1ana';
    if (days <= 7) return `${days} dias`;
    if (days <= 30) return `${Math.ceil(days / 7)} sem`;
    return d.toLocaleDateString('es-MX', { month: 'short', day: 'numeric' });
  });

  // Check if date is overdue
  eleventyConfig.addFilter("isOverdue", function(date) {
    if (!date) return false;
    const d = new Date(date + 'T23:59:59');
    return d < new Date();
  });

  // Extract title from filename
  eleventyConfig.addFilter("titleFromFilename", function(filename) {
    if (!filename) return 'Sin titulo';
    const name = filename.split('/').pop().replace(/\.\w+$/, '');
    const withoutPrefix = name.replace(/^\d+[_-]?/, '').replace(/^[a-zA-Z]_/, '');
    return withoutPrefix
      .replace(/[_-]/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase()) || 'Sin titulo';
  });

  // Get navigation number from filename
  eleventyConfig.addFilter("getNavNumber", function(name, prefix, index) {
    if (!name) return '';
    // z_ prefix
    if (name.match(/^z_/i)) return 'Z';
    // Letter prefix
    const letterMatch = name.match(/^([a-z])_/i);
    if (letterMatch) return letterMatch[1].toUpperCase();
    // Numeric prefix
    const numMatch = name.match(/^(\d+)[_-]/);
    if (numMatch) {
      const num = parseInt(numMatch[1], 10);
      return prefix + num;
    }
    return prefix + (index + 1);
  });

  // Clean navigation title
  eleventyConfig.addFilter("cleanNavTitle", function(title) {
    if (!title) return '';
    return title
      .replace(/^\?\?\s*/, '')
      .replace(/^M\u00f3dulo\s*\d+\s*[:\-]\s*/i, '')
      .replace(/^Module\s*\d+\s*[:\-]\s*/i, '')
      .replace(/^Cap\u00edtulo\s*\d+\s*[:\-]\s*/i, '')
      .replace(/^Chapter\s*\d+\s*[:\-]\s*/i, '')
      .trim() || title;
  });

  // Check if string starts with prefix
  eleventyConfig.addFilter("startsWith", function(str, prefix) {
    return str ? str.startsWith(prefix) : false;
  });

  // Get sort order from filename
  eleventyConfig.addFilter("getOrder", function(filename) {
    if (!filename) return 999;
    const match = filename.match(/^(\d+)/);
    return match ? parseInt(match[1], 10) : 999;
  });
}

module.exports = { registerFilters };
