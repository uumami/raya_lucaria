/**
 * Navigation expand/collapse state management.
 */

const NAV_STATE_KEY = 'glintstone-nav-expanded';

export function initNavState() {
  const navItems = document.querySelectorAll('[data-nav-path]');
  if (navItems.length === 0) return;

  // Expose global toggle function (called by onclick in nav template)
  window.toggleNavSection = function(sectionPath) {
    const item = document.querySelector(`[data-nav-path="${sectionPath}"]`);
    if (!item) return;

    const isExpanded = item.dataset.expanded === 'true';
    const newState = !isExpanded;

    // Accordion: collapse siblings when expanding
    if (newState) {
      const depth = item.dataset.depth;
      const parent = item.parentElement;
      if (parent) {
        parent.querySelectorAll(`:scope > [data-nav-path][data-depth="${depth}"]`).forEach(sibling => {
          if (sibling !== item && sibling.dataset.expanded === 'true') {
            sibling.dataset.expanded = 'false';
            sibling.setAttribute('aria-expanded', 'false');
          }
        });
      }
    }

    item.dataset.expanded = String(newState);
    item.setAttribute('aria-expanded', String(newState));
    saveExpandedSections();
  };

  // Expand ancestors of current page
  const currentItem = document.querySelector('[data-active="current"]');
  if (currentItem) {
    let parent = currentItem.closest('[data-nav-path]');
    while (parent) {
      parent.dataset.expanded = 'true';
      parent.setAttribute('aria-expanded', 'true');
      const grandparent = parent.parentElement;
      parent = grandparent ? grandparent.closest('[data-nav-path]') : null;
    }
  }

  // Also expand ancestors marked as "ancestor"
  document.querySelectorAll('[data-active="ancestor"]').forEach(ancestor => {
    const navItem = ancestor.closest('[data-nav-path]');
    if (navItem) {
      navItem.dataset.expanded = 'true';
      navItem.setAttribute('aria-expanded', 'true');
    }
  });

  // Restore saved expanded sections
  try {
    const saved = JSON.parse(localStorage.getItem(NAV_STATE_KEY)) || [];
    saved.forEach(path => {
      const item = document.querySelector(`[data-nav-path="${path}"]`);
      if (item && item.dataset.expanded !== 'true') {
        const depth = item.dataset.depth;
        const parent = item.parentElement;
        if (parent) {
          const expandedSibling = parent.querySelector(
            `:scope > [data-nav-path][data-depth="${depth}"][data-expanded="true"]`
          );
          if (!expandedSibling) {
            item.dataset.expanded = 'true';
            item.setAttribute('aria-expanded', 'true');
          }
        }
      }
    });
  } catch (e) { /* ignore */ }

  // Auto-scroll current page into view
  if (currentItem) {
    setTimeout(() => {
      const sidebarNav = document.getElementById('sidebar-nav');
      if (sidebarNav) {
        const link = currentItem.querySelector('a[aria-current="page"]') || currentItem.querySelector('a');
        if (link) {
          const navRect = sidebarNav.getBoundingClientRect();
          const linkRect = link.getBoundingClientRect();
          const isVisible = linkRect.top >= navRect.top && linkRect.bottom <= navRect.bottom;
          if (!isVisible) {
            link.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }
      }
    }, 150);
  }
}

function saveExpandedSections() {
  const expanded = [...document.querySelectorAll('[data-nav-path][data-expanded="true"]')]
    .map(el => el.dataset.navPath);
  localStorage.setItem(NAV_STATE_KEY, JSON.stringify(expanded));
}
