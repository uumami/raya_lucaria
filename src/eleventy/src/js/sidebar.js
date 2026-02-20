/**
 * Sidebar collapse/expand and mobile menu behavior.
 */

export function initSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  const collapseBtn = document.getElementById('sidebar-collapse');
  const expandBtn = document.getElementById('sidebar-expand');
  const mobileMenuBtn = document.getElementById('mobile-menu');

  if (!sidebar) return;

  // Desktop collapse/expand
  function collapseSidebar() {
    sidebar.classList.add('collapsed');
    localStorage.setItem('glintstone-sidebar', 'collapsed');
  }

  function expandSidebar() {
    sidebar.classList.remove('collapsed');
    localStorage.setItem('glintstone-sidebar', 'expanded');
  }

  if (collapseBtn) collapseBtn.addEventListener('click', collapseSidebar);
  if (expandBtn) expandBtn.addEventListener('click', expandSidebar);

  // Mobile menu
  function openMobile() {
    sidebar.classList.remove('mobile-hidden');
    if (overlay) overlay.classList.remove('hidden');
  }

  function closeMobile() {
    sidebar.classList.add('mobile-hidden');
    if (overlay) overlay.classList.add('hidden');
  }

  if (mobileMenuBtn) mobileMenuBtn.addEventListener('click', openMobile);
  if (overlay) overlay.addEventListener('click', closeMobile);

  // Initialize state
  if (window.innerWidth < 1024) {
    sidebar.classList.add('mobile-hidden');
  }

  if (localStorage.getItem('glintstone-sidebar') === 'collapsed' && window.innerWidth >= 1024) {
    sidebar.classList.add('collapsed');
  }

  // Sidebar nav scroll persistence
  const sidebarNav = document.getElementById('sidebar-nav');
  if (sidebarNav) {
    const savedScroll = localStorage.getItem('glintstone-nav-scroll');
    if (savedScroll) {
      sidebarNav.scrollTop = parseInt(savedScroll, 10);
    }

    sidebarNav.addEventListener('click', (e) => {
      if (e.target.closest('a')) {
        localStorage.setItem('glintstone-nav-scroll', sidebarNav.scrollTop);
      }
    });

    let scrollTimeout;
    sidebarNav.addEventListener('scroll', () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        localStorage.setItem('glintstone-nav-scroll', sidebarNav.scrollTop);
      }, 100);
    });
  }
}
