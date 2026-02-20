/**
 * Copy button for code blocks.
 */

export function initCopyCode() {
  document.querySelectorAll('pre code').forEach(block => {
    const pre = block.parentElement;
    if (!pre || pre.querySelector('.copy-code-btn')) return;

    const btn = document.createElement('button');
    btn.className = 'copy-code-btn';
    btn.textContent = 'Copiar';
    btn.title = 'Copiar codigo';

    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      try {
        await navigator.clipboard.writeText(block.textContent);
        btn.textContent = 'Copiado!';
        setTimeout(() => { btn.textContent = 'Copiar'; }, 2000);
      } catch (err) {
        btn.textContent = 'Error';
        setTimeout(() => { btn.textContent = 'Copiar'; }, 2000);
      }
    });

    pre.style.position = 'relative';
    pre.appendChild(btn);
  });
}
