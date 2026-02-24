/**
 * Navigation expand/collapse state management.
 *
 * Ancestors of the current page are pre-expanded in the template (no flash).
 * This JS handles: toggle clicks, localStorage persistence, auto-scroll.
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

    // Accordion: collapse siblings at same depth when expanding
    if (newState) {
      const depth = item.dataset.depth;
      const parent = item.parentElement;
      if (parent) {
        parent.querySelectorAll(`:scope > .nav-item[data-depth="${depth}"]`).forEach(sibling => {
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

  // Restore additional user-expanded sections from localStorage
  // (template already expanded ancestors — this restores extra sections the user opened)
  try {
    const saved = JSON.parse(localStorage.getItem(NAV_STATE_KEY)) || [];
    saved.forEach(path => {
      const item = document.querySelector(`[data-nav-path="${path}"]`);
      if (item && item.dataset.expanded !== 'true') {
        // Respect accordion: don't expand if a sibling at same depth is already open
        const depth = item.dataset.depth;
        const parent = item.parentElement;
        if (parent) {
          const expandedSibling = parent.querySelector(
            `:scope > .nav-item[data-depth="${depth}"][data-expanded="true"]`
          );
          if (!expandedSibling) {
            item.dataset.expanded = 'true';
            item.setAttribute('aria-expanded', 'true');
          }
        }
      }
    });
  } catch (e) { /* ignore */ }

  // Save initial state (includes template pre-expanded + localStorage restored)
  saveExpandedSections();

  // Auto-scroll current page into view
  const currentItem = document.querySelector('[data-active="current"]');
  if (currentItem) {
    requestAnimationFrame(() => {
      const sidebarNav = document.getElementById('sidebar-nav');
      if (sidebarNav) {
        const link = currentItem.querySelector('a[aria-current="page"]') || currentItem.querySelector('a');
        if (link) {
          const navRect = sidebarNav.getBoundingClientRect();
          const linkRect = link.getBoundingClientRect();
          const isVisible = linkRect.top >= navRect.top && linkRect.bottom <= navRect.bottom;
          if (!isVisible) {
            link.scrollIntoView({ behavior: 'instant', block: 'center' });
          }
        }
      }
    });
  }
}

function saveExpandedSections() {
  const expanded = [...document.querySelectorAll('[data-nav-path][data-expanded="true"]')]
    .map(el => el.dataset.navPath);
  localStorage.setItem(NAV_STATE_KEY, JSON.stringify(expanded));
}
