/**
 * Glintstone -- Frontend JS Entry Point
 * Compiled by esbuild into a single bundle.
 */

import { initSidebar } from './sidebar.js';
import { initThemeToggle } from './theme-toggle.js';
import { initFontToggle } from './font-toggle.js';
import { initNavState } from './nav-state.js';
import { initKeyboardNav } from './keyboard-nav.js';
import { initCopyCode } from './copy-code.js';
import { initToc } from './toc.js';
import { initMermaid } from './mermaid-init.js';
import { initKatex } from './katex-init.js';
import { initSearch } from './search-init.js';
import { initQuiz } from './quiz.js';
import { initServiceWorker } from './sw-register.js';
import { initGraph } from './graph.js';

// Initialize all modules when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initThemeToggle();
  initFontToggle();
  initNavState();
  initKeyboardNav();
  initCopyCode();
  initToc();
  initMermaid();
  initKatex();
  initSearch();
  initQuiz();
  initServiceWorker();
  initGraph();
});
