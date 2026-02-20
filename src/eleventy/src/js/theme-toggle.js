/**
 * Theme switching across 12 themes (6 families x dark/light).
 * Note: The saved theme is restored by a blocking inline script in <head>
 * to prevent flash-of-wrong-theme. This module only handles the toggle button.
 */

const THEMES = [
  'eva-02-dark',
  'eva-02-light',
  'eva-01-dark',
  'eva-01-light',
  'eva-00-dark',
  'eva-00-light',
  'eva-05-mari-dark',
  'eva-05-mari-light',
  'elden-ring-dark',
  'elden-ring-light',
  'elden-ring-raya-lucaria-dark',
  'elden-ring-raya-lucaria-light',
];

const STORAGE_KEY = 'glintstone-theme';
const DEFAULT_THEME = 'eva-02-dark';

export function initThemeToggle() {
  const toggleBtn = document.getElementById('theme-toggle');
  if (!toggleBtn) return;

  toggleBtn.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || DEFAULT_THEME;
    const currentIndex = THEMES.indexOf(current);
    const next = THEMES[(currentIndex + 1) % THEMES.length];
    applyTheme(next);
    localStorage.setItem(STORAGE_KEY, next);
  });
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);

  // Update theme stylesheet
  const stylesheet = document.getElementById('theme-stylesheet');
  if (stylesheet) {
    const currentHref = stylesheet.getAttribute('href');
    const basePath = currentHref.substring(0, currentHref.lastIndexOf('/') + 1);
    stylesheet.setAttribute('href', basePath + theme + '.css');
  }
}
