/**
 * Component type registry and render functions.
 *
 * Adding a new component type:
 * 1. Add entry to REGISTRY
 * 2. Create _includes/components/{type}.njk template
 * That's it.
 */

const COMPONENT_TYPES = ['homework', 'exercise', 'prompt', 'example', 'exam', 'project', 'quiz', 'embed'];

const REGISTRY = {
  homework: {
    label: 'TAREA',
    colorVar: '--color-homework',
    attrs: { required: ['id', 'title'], optional: ['due', 'points'] },
  },
  exercise: {
    label: 'EJERCICIO',
    colorVar: '--color-exercise',
    attrs: { required: ['title'], optional: ['difficulty'] },
  },
  prompt: {
    label: 'PROMPT',
    colorVar: '--color-prompt',
    attrs: { required: ['title'], optional: ['for'] },
  },
  example: {
    label: 'EJEMPLO',
    colorVar: '--color-example',
    attrs: { required: ['title'], optional: [] },
  },
  exam: {
    label: 'EXAMEN',
    colorVar: '--color-exam',
    attrs: { required: ['id', 'title'], optional: ['date', 'location', 'duration', 'points'] },
  },
  project: {
    label: 'PROYECTO',
    colorVar: '--color-project',
    attrs: { required: ['id', 'title'], optional: ['due', 'points', 'team_size'] },
  },
  quiz: {
    label: 'QUIZ',
    colorVar: '--color-quiz',
    attrs: { required: ['title'], optional: [] },
  },
  embed: {
    label: 'RECURSO',
    colorVar: '--color-embed',
    attrs: { required: ['src'], optional: ['title', 'type'] },
  },
};

/**
 * Parse attributes from string like {id="foo" title="bar"}
 */
function parseAttributes(str) {
  const attrs = {};
  if (!str) return attrs;
  const regex = /(\w+)=["']([^"']*?)["']/g;
  let match;
  while ((match = regex.exec(str)) !== null) {
    attrs[match[1]] = match[2];
  }
  return attrs;
}

/**
 * Render a component container opening/closing tag.
 */
function renderComponent(tokens, idx, type, md) {
  const token = tokens[idx];
  const info = REGISTRY[type];

  if (token.nesting === 1) {
    // Opening tag
    const match = token.info.trim().match(new RegExp(`^${type}\\s*(.*)$`));
    const attrsStr = match ? match[1] : '';
    const attrs = parseAttributes(attrsStr);

    const dataAttrs = Object.entries(attrs)
      .map(([k, v]) => `data-${k}="${v}"`)
      .join(' ');

    // Build badge HTML
    let badges = '';
    if (attrs.due) {
      badges += `<span class="component__badge component__badge--due">${attrs.due}</span>`;
    }
    if (attrs.date) {
      badges += `<span class="component__badge component__badge--date">${attrs.date}</span>`;
    }
    if (attrs.points) {
      badges += `<span class="component__badge component__badge--points">${attrs.points} pts</span>`;
    }
    if (attrs.difficulty) {
      const stars = '\u2605'.repeat(parseInt(attrs.difficulty) || 1);
      badges += `<span class="component__badge component__badge--difficulty">${stars}</span>`;
    }
    if (attrs.duration) {
      badges += `<span class="component__badge component__badge--duration">${attrs.duration}</span>`;
    }
    if (attrs.location) {
      badges += `<span class="component__badge component__badge--location">${attrs.location}</span>`;
    }

    // Embed component: render iframe instead of standard body
    if (type === 'embed') {
      const iframeSrc = attrs.src || '';
      const iframeTitle = attrs.title || 'Recurso externo';
      return `<div class="component component--embed" ${dataAttrs}>
  <div class="component__header">
    <span class="component__label">[${info.label}]</span>
    <span class="component__title">${attrs.title || ''}</span>
  </div>
  <div class="embed__wrapper">
    <iframe class="embed__iframe" src="${iframeSrc}" title="${iframeTitle}" allowfullscreen loading="lazy"></iframe>
  </div>
  <div class="component__body">\n`;
    }

    return `<div class="component component--${type}" ${dataAttrs}>
  <div class="component__header">
    <span class="component__label">[${info.label}]</span>
    <span class="component__title">${attrs.title || ''}</span>
    ${badges ? `<div class="component__badges">${badges}</div>` : ''}
  </div>
  <div class="component__body">\n`;
  } else {
    // Closing tag
    return '  </div>\n</div>\n';
  }
}

module.exports = { COMPONENT_TYPES, REGISTRY, parseAttributes, renderComponent };
