/**
 * Page table of contents with scroll tracking and full sidebar collapse.
 * Populates the right sidebar TOC from h2/h3 headings.
 */

const TOC_STORAGE_KEY = 'glintstone-toc-collapsed';

export function initToc() {
  const tocNav = document.getElementById('toc-nav');
  const tocAside = document.getElementById('page-toc');
  const tocExpanded = document.getElementById('toc-expanded');
  const tocCollapsedTab = document.getElementById('toc-collapsed-tab');
  const collapseBtn = document.getElementById('toc-collapse-btn');
  const expandBtn = document.getElementById('toc-expand-btn');
  if (!tocNav || !tocAside) return;

  // Find all h2 and h3 headings in main content
  const main = document.getElementById('main-content');
  if (!main) return;

  const headings = main.querySelectorAll('h2[id], h3[id]');
  if (headings.length < 2) {
    tocAside.classList.add('hidden');
    tocAside.classList.remove('xl:block');
    return;
  }

  // Build TOC links
  headings.forEach(heading => {
    const link = document.createElement('a');
    link.href = '#' + heading.id;
    link.textContent = heading.textContent.replace(/^#\s*/, '');
    link.className = 'block py-0.5 text-text-muted hover:text-accent transition-colors truncate';

    if (heading.tagName === 'H3') {
      link.classList.add('pl-3', 'text-xs');
    } else {
      link.classList.add('text-sm');
    }

    link.dataset.tocTarget = heading.id;
    tocNav.appendChild(link);
  });

  function collapse() {
    tocAside.classList.add('toc-sidebar-collapsed');
    if (tocExpanded) tocExpanded.classList.add('hidden');
    if (tocCollapsedTab) tocCollapsedTab.classList.remove('hidden');
    localStorage.setItem(TOC_STORAGE_KEY, 'true');
  }

  function expand() {
    tocAside.classList.remove('toc-sidebar-collapsed');
    if (tocExpanded) tocExpanded.classList.remove('hidden');
    if (tocCollapsedTab) tocCollapsedTab.classList.add('hidden');
    localStorage.setItem(TOC_STORAGE_KEY, 'false');
  }

  // Restore collapsed state
  if (localStorage.getItem(TOC_STORAGE_KEY) === 'true') {
    collapse();
  }

  // Collapse/expand handlers
  if (collapseBtn) collapseBtn.addEventListener('click', collapse);
  if (expandBtn) expandBtn.addEventListener('click', expand);

  // Scroll tracking with IntersectionObserver
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const id = entry.target.id;
          tocNav.querySelectorAll('a').forEach(a => {
            a.classList.toggle('text-accent', a.dataset.tocTarget === id);
            a.classList.toggle('text-text-muted', a.dataset.tocTarget !== id);
          });
        }
      });
    },
    { rootMargin: '-80px 0px -70% 0px', threshold: 0 }
  );

  headings.forEach(h => observer.observe(h));
}
