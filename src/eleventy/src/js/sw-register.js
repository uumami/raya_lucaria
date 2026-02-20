/**
 * Service Worker registration.
 * Registers /sw.js with the appropriate scope.
 */

export function initServiceWorker() {
  if (!('serviceWorker' in navigator)) return;

  // Determine scope from PATH_PREFIX (embedded in the page's base URL)
  const scope = document.querySelector('link[rel="manifest"]')?.href
    ? new URL(document.querySelector('link[rel="manifest"]').href).pathname.replace('manifest.json', '')
    : '/';

  navigator.serviceWorker.register(scope + 'sw.js', { scope })
    .catch(() => { /* SW registration failed silently */ });
}
