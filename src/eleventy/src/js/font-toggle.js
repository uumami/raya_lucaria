/**
 * Font size toggle and OpenDyslexic font toggle.
 * Note: Saved size/dyslexic prefs are restored by the blocking inline script
 * in <head> to prevent flash. This module only handles the toggle buttons.
 */

const SIZES = ['normal', 'large', 'x-large'];
const root = document.documentElement;

export function initFontToggle() {
  const sizeBtn = document.getElementById('size-toggle');
  const fontBtn = document.getElementById('font-toggle');

  // Size toggle
  if (sizeBtn) {
    // Reflect current state in button
    const savedSize = localStorage.getItem('glintstone-size') || 'normal';
    if (savedSize !== 'normal') {
      sizeBtn.classList.add('text-accent', 'bg-bg-tertiary');
    }

    sizeBtn.addEventListener('click', () => {
      const current = localStorage.getItem('glintstone-size') || 'normal';
      const idx = SIZES.indexOf(current);
      const next = SIZES[(idx + 1) % SIZES.length];

      SIZES.forEach(s => root.classList.remove('size-' + s));
      if (next !== 'normal') {
        root.classList.add('size-' + next);
      }
      localStorage.setItem('glintstone-size', next);

      const isActive = next !== 'normal';
      sizeBtn.classList.toggle('text-accent', isActive);
      sizeBtn.classList.toggle('bg-bg-tertiary', isActive);
    });
  }

  // OpenDyslexic toggle (class applied on <html> by inline script and here)
  if (fontBtn) {
    if (root.classList.contains('font-dyslexic')) {
      fontBtn.classList.add('text-accent', 'bg-bg-tertiary');
    }

    fontBtn.addEventListener('click', () => {
      root.classList.toggle('font-dyslexic');
      const isDyslexic = root.classList.contains('font-dyslexic');
      localStorage.setItem('glintstone-dyslexic', isDyslexic);
      fontBtn.classList.toggle('text-accent', isDyslexic);
      fontBtn.classList.toggle('bg-bg-tertiary', isDyslexic);
    });
  }
}
