/**
 * Computed data for all pages.
 * Provides prev/next navigation, breadcrumbs, and heading extraction for TOC.
 */

function getHierarchyNumber(inputPath) {
  if (!inputPath) return '';
  const clean = inputPath
    .replace(/^\.?\/?(?:clase(?:-stage)?\/)?(?:docs\/)?/, '')
    .replace(/\.md$/, '')
    .replace(/\/00_index$/, '');
  const parts = clean.split('/');
  const numbers = [];
  for (const part of parts) {
    const letterMatch = part.match(/^([a-z])_/i);
    if (letterMatch) { numbers.push(letterMatch[1].toUpperCase()); continue; }
    const numMatch = part.match(/^(\d+)[_-]/);
    if (numMatch) {
      const num = parseInt(numMatch[1], 10);
      if (num > 0) numbers.push(num.toString());
    }
  }
  return numbers.join('.');
}

function cleanTitle(title) {
  if (!title) return '';
  return title
    .replace(/^M\u00f3dulo\s*\d+\s*[:\-]\s*/i, '')
    .replace(/^Module\s*\d+\s*[:\-]\s*/i, '')
    .replace(/^Cap\u00edtulo\s*\d+\s*[:\-]\s*/i, '')
    .replace(/^Chapter\s*\d+\s*[:\-]\s*/i, '')
    .replace(/^\?\?\s*/, '')
    .trim();
}

function getNavTitle(item, metadata) {
  const hierarchy = getHierarchyNumber(item.inputPath);
  const rawTitle = item.data?.title || 'Sin titulo';
  const title = cleanTitle(rawTitle);
  return hierarchy ? `${hierarchy} ${title}` : title;
}

function getBreadcrumbs(inputPath, hierarchy) {
  if (!inputPath || !hierarchy || !hierarchy.children) return [];
  const clean = inputPath.replace(/^\.?\/?(?:clase(?:-stage)?\/)?/, '').replace(/\.md$/, '');
  const parts = clean.split('/');
  const crumbs = [];

  let current = hierarchy;
  for (let i = 0; i < parts.length - 1; i++) {
    const part = parts[i];
    if (!current.children) break;
    const child = current.children.find(c => c.name === part || c.name === part + '.md');
    if (child) {
      let url = null;
      if (child.type === 'directory' && child.has_index) {
        url = '/' + child.path + '/00_index/';
      } else if (child.type === 'directory' && child.children && child.children.length > 0) {
        const first = child.children[0];
        url = '/' + (first.path || '').replace('.md', '') + '/';
      }
      crumbs.push({ title: child.title, url: url });
      current = child;
    }
  }
  return crumbs;
}

module.exports = {
  prevPage: function(data) {
    const isDoc = data.page?.inputPath?.includes('/docs/');
    const coll = isDoc ? data.collections?.docs : data.collections?.content;
    if (!coll || !data.page) return null;
    const idx = coll.findIndex(item => item.url === data.page.url);
    if (idx > 0) {
      const prev = coll[idx - 1];
      return { url: prev.url, title: getNavTitle(prev, data.metadata) };
    }
    return null;
  },

  nextPage: function(data) {
    const isDoc = data.page?.inputPath?.includes('/docs/');
    const coll = isDoc ? data.collections?.docs : data.collections?.content;
    if (!coll || !data.page) return null;
    const idx = coll.findIndex(item => item.url === data.page.url);
    if (idx >= 0 && idx < coll.length - 1) {
      const next = coll[idx + 1];
      return { url: next.url, title: getNavTitle(next, data.metadata) };
    }
    return null;
  },

  readingTime: function(data) {
    if (!data.page || !data.page.rawInput) return null;
    const content = data.page.rawInput.replace(/^---[\s\S]*?---/, '');
    const text = content.replace(/<[^>]*>/g, '').replace(/[#*`~\[\]()!|]/g, '');
    const words = text.split(/\s+/).filter(w => w.length > 0).length;
    return Math.max(1, Math.ceil(words / 200));
  },

  breadcrumbs: function(data) {
    if (data.page?.inputPath?.includes('/docs/')) {
      const adjusted = data.page.inputPath.replace(/\/docs\//, '/');
      const crumbs = getBreadcrumbs(adjusted, data.hierarchy_docs);
      crumbs.unshift({ title: 'Documentacion', url: '/docs/' });
      return crumbs;
    }
    return getBreadcrumbs(data.page?.inputPath, data.hierarchy);
  },
};
