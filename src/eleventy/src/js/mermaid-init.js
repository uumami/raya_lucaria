/**
 * Mermaid diagram initialization.
 * Listens for 'mermaid-loaded' custom event from ESM CDN loader in base.njk.
 * Falls back to polling. Wraps diagrams in scrollable containers with click-to-expand.
 */

export function initMermaid() {
  // Check if any mermaid code blocks exist
  const codeBlocks = document.querySelectorAll('pre code.language-mermaid');
  if (codeBlocks.length === 0) return;

  // Listen for mermaid-loaded event from ESM import in base.njk
  if (typeof window.mermaid !== 'undefined') {
    setupMermaid();
  } else {
    window.addEventListener('mermaid-loaded', () => setupMermaid(), { once: true });

    // Polling fallback (in case event fires before listener attached)
    const checkMermaid = setInterval(() => {
      if (typeof window.mermaid !== 'undefined') {
        clearInterval(checkMermaid);
        setupMermaid();
      }
    }, 200);
    setTimeout(() => clearInterval(checkMermaid), 10000);
  }
}

function setupMermaid() {
  const style = getComputedStyle(document.documentElement);
  const bgHex = style.getPropertyValue('--color-bg').trim();
  const isDark = bgHex.startsWith('#0') || bgHex.startsWith('#1');

  window.mermaid.initialize({
    startOnLoad: false,
    theme: isDark ? 'dark' : 'default',
    themeVariables: isDark ? {
      primaryColor: style.getPropertyValue('--color-accent-secondary').trim(),
      primaryTextColor: style.getPropertyValue('--color-text').trim(),
      primaryBorderColor: style.getPropertyValue('--color-border').trim(),
      lineColor: style.getPropertyValue('--color-accent').trim(),
      secondaryColor: style.getPropertyValue('--color-bg-secondary').trim(),
      tertiaryColor: style.getPropertyValue('--color-bg-tertiary').trim(),
    } : {},
  });

  // Convert mermaid code blocks to diagrams
  document.querySelectorAll('pre code.language-mermaid').forEach((block) => {
    const pre = block.parentElement;
    const container = document.createElement('div');
    container.className = 'mermaid-container my-4';
    container.title = 'Click para expandir';

    const mermaidDiv = document.createElement('div');
    mermaidDiv.className = 'mermaid';
    mermaidDiv.textContent = block.textContent;
    container.appendChild(mermaidDiv);

    // Click to expand
    container.addEventListener('click', () => {
      openMermaidModal(container.querySelector('.mermaid'));
    });

    pre.replaceWith(container);
  });

  window.mermaid.run();
}

function openMermaidModal(mermaidEl) {
  if (!mermaidEl) return;

  const overlay = document.createElement('div');
  overlay.className = 'mermaid-modal-overlay';

  const modal = document.createElement('div');
  modal.className = 'mermaid-modal';

  const closeBtn = document.createElement('button');
  closeBtn.className = 'mermaid-modal-close';
  closeBtn.innerHTML = '&times;';
  closeBtn.title = 'Cerrar (Esc)';

  const content = document.createElement('div');
  content.className = 'mermaid-modal-content';
  content.innerHTML = mermaidEl.innerHTML;

  modal.appendChild(closeBtn);
  modal.appendChild(content);
  overlay.appendChild(modal);
  document.body.appendChild(overlay);

  // Prevent body scroll
  document.body.style.overflow = 'hidden';

  const close = () => {
    overlay.remove();
    document.body.style.overflow = '';
  };

  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) close();
  });
  document.addEventListener('keydown', function handler(e) {
    if (e.key === 'Escape') {
      close();
      document.removeEventListener('keydown', handler);
    }
  });
}
