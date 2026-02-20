/**
 * Tailwind CSS Configuration for glintstone.
 * Uses CSS custom properties for theming.
 */

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./glintstone/src/eleventy/_includes/**/*.{njk,html}",
    "./clase/**/*.md",
    "./clase-stage/**/*.{md,njk}",
    "./_site/**/*.html",
  ],
  safelist: [
    // Backgrounds
    'bg-bg', 'bg-bg-secondary', 'bg-bg-tertiary', 'bg-code-bg',
    'bg-bg/95', 'bg-black/50',
    // Text
    'text-text', 'text-text-muted', 'text-accent', 'text-accent-hover',
    'text-accent-secondary',
    'text-homework', 'text-exercise', 'text-prompt', 'text-example',
    'text-exam', 'text-project', 'text-quiz', 'text-embed',
    // Borders
    'border-border', 'border-homework', 'border-exercise',
    'border-exam', 'border-project', 'border-quiz', 'border-embed',
    // Hovers
    'hover:text-accent', 'hover:text-accent-hover', 'hover:text-text',
    'hover:bg-bg-secondary', 'hover:bg-bg-tertiary',
    // Layout essentials
    'font-sans', 'font-mono', 'antialiased',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'bg': 'var(--color-bg)',
        'bg-secondary': 'var(--color-bg-secondary)',
        'bg-tertiary': 'var(--color-bg-tertiary)',
        'text': 'var(--color-text)',
        'text-muted': 'var(--color-text-muted)',
        'accent': 'var(--color-accent)',
        'accent-hover': 'var(--color-accent-hover)',
        'accent-secondary': 'var(--color-accent-secondary)',
        'border': 'var(--color-border)',
        'code-bg': 'var(--color-code-bg)',
        'homework': 'var(--color-homework)',
        'exercise': 'var(--color-exercise)',
        'prompt': 'var(--color-prompt)',
        'example': 'var(--color-example)',
        'exam': 'var(--color-exam)',
        'project': 'var(--color-project)',
        'quiz': 'var(--color-quiz)',
        'embed': 'var(--color-embed)',
      },
      fontFamily: {
        'sans': ['var(--font-family-base)'],
        'mono': ['var(--font-family-mono)'],
        'dyslexic': ['OpenDyslexic', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
