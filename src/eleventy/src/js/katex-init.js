/**
 * KaTeX initialization for math rendering.
 * Works with markdown-it-dollarmath which emits <span class="math-inline"> and <div class="math-display">.
 */

export function initKatex() {
  const katexScript = document.querySelector('script[data-katex-autorender]');
  if (!katexScript) return;

  // Wait for KaTeX to load
  const checkKatex = setInterval(() => {
    if (typeof window.katex !== 'undefined' && typeof window.renderMathInElement !== 'undefined') {
      clearInterval(checkKatex);
      renderMath();
    }
  }, 100);

  setTimeout(() => clearInterval(checkKatex), 5000);
}

function renderMath() {
  // Render math-inline and math-display elements from dollarmath
  document.querySelectorAll('.math-inline').forEach(el => {
    try {
      window.katex.render(el.textContent, el, { displayMode: false, throwOnError: false });
    } catch (e) { /* leave as-is */ }
  });

  document.querySelectorAll('.math-display').forEach(el => {
    try {
      window.katex.render(el.textContent, el, { displayMode: true, throwOnError: false });
    } catch (e) { /* leave as-is */ }
  });

  // Also handle any remaining $...$ via auto-render as fallback
  try {
    window.renderMathInElement(document.body, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '$', right: '$', display: false },
      ],
      throwOnError: false,
      ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code', 'svg'],
    });
  } catch (e) { /* ignore */ }
}
