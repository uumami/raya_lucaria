/**
 * Pagefind search initialization.
 */

export function initSearch() {
  const searchWidget = document.querySelector('[data-pagefind-ui]');
  if (!searchWidget) return;

  // Wait for PagefindUI to be available
  const checkPagefind = setInterval(() => {
    if (typeof window.PagefindUI !== 'undefined') {
      clearInterval(checkPagefind);
      new window.PagefindUI({
        element: searchWidget,
        showSubResults: true,
        showImages: false,
      });
    }
  }, 100);

  setTimeout(() => clearInterval(checkPagefind), 5000);
}
