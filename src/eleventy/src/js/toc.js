/**
 * Page table of contents with scroll tracking and collapse toggle.
 * Populates the right sidebar TOC from h2/h3 headings.
 */

const TOC_STORAGE_KEY = 'glintstone-toc-collapsed';

export function initToc() {
  const tocNav = document.getElementById('toc-nav');
  const tocAside = document.getElementById('page-toc');
  const collapseBtn = document.getElementById('toc-collapse-btn');
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

  // Restore collapsed state
  if (localStorage.getItem(TOC_STORAGE_KEY) === 'true') {
    tocNav.classList.add('toc-collapsed');
    if (collapseBtn) {
      collapseBtn.querySelector('.toc-collapse-icon').style.transform = 'rotate(-90deg)';
    }
  }

  // Collapse toggle
  if (collapseBtn) {
    collapseBtn.addEventListener('click', () => {
      const isCollapsed = tocNav.classList.toggle('toc-collapsed');
      localStorage.setItem(TOC_STORAGE_KEY, isCollapsed);
      collapseBtn.querySelector('.toc-collapse-icon').style.transform =
        isCollapsed ? 'rotate(-90deg)' : '';
    });
  }

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
