/**
 * Keyboard navigation: arrow keys for prev/next page.
 */

export function initKeyboardNav() {
  document.addEventListener('keydown', (e) => {
    // Don't navigate if user is typing in an input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
      return;
    }

    if (e.key === 'ArrowLeft' || (e.key === 'k' && e.altKey)) {
      const prev = document.querySelector('a[data-prev]');
      if (prev) { e.preventDefault(); prev.click(); }
    }

    if (e.key === 'ArrowRight' || (e.key === 'j' && e.altKey)) {
      const next = document.querySelector('a[data-next]');
      if (next) { e.preventDefault(); next.click(); }
    }
  });
}
