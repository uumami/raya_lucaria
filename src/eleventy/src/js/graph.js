/**
 * Primeval Current — Knowledge Graph Visualization
 * Cytoscape.js interactive graph. Only runs on the /grafo/ page.
 */

export function initGraph() {
  var data = window.__GRAPH_DATA__;
  var container = document.getElementById('graph-canvas');
  var statusEl = document.getElementById('graph-status');

  function showStatus(msg) {
    if (statusEl) statusEl.textContent = msg;
  }

  if (!container) return;
  if (typeof cytoscape === 'undefined') {
    showStatus('Error: Cytoscape no cargado');
    return;
  }
  if (!data || !data.nodes || !data.nodes.length) {
    showStatus('Sin datos para el grafo');
    return;
  }

  try {
    _buildGraph(data, container, statusEl);
  } catch (err) {
    console.error('[graph] init failed:', err);
    showStatus('Error: ' + err.message);
  }
}

// --- Fuzzy search utilities ---

/** Normalize: lowercase, strip accents, trim */
function normalize(s) {
  return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();
}

/** Levenshtein distance between two strings */
function levenshtein(a, b) {
  if (a.length === 0) return b.length;
  if (b.length === 0) return a.length;
  var matrix = [];
  for (var i = 0; i <= b.length; i++) matrix[i] = [i];
  for (var j = 0; j <= a.length; j++) matrix[0][j] = j;
  for (var i = 1; i <= b.length; i++) {
    for (var j = 1; j <= a.length; j++) {
      var cost = b.charAt(i - 1) === a.charAt(j - 1) ? 0 : 1;
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,
        matrix[i][j - 1] + 1,
        matrix[i - 1][j - 1] + cost
      );
    }
  }
  return matrix[b.length][a.length];
}

/**
 * Fuzzy match: returns true if query approximately matches target.
 * - Exact substring match (accent-insensitive)
 * - Levenshtein distance within threshold for short queries
 * - Any word in target starts with query
 */
function fuzzyMatch(query, target) {
  var q = normalize(query);
  var t = normalize(target);
  if (!q) return true;

  // Exact substring (accent-normalized)
  if (t.indexOf(q) >= 0) return true;

  // Prefix match on any word
  var words = t.split(/[\s_\-\/]+/);
  for (var i = 0; i < words.length; i++) {
    if (words[i].indexOf(q) === 0) return true;
  }

  // Levenshtein on each word (for typos)
  var threshold = q.length <= 3 ? 1 : Math.floor(q.length * 0.35);
  for (var i = 0; i < words.length; i++) {
    if (words[i].length > 0 && levenshtein(q, words[i]) <= threshold) return true;
  }

  // Levenshtein on full target (for short targets)
  if (t.length <= 20 && levenshtein(q, t) <= threshold) return true;

  return false;
}


function _buildGraph(data, container, statusEl) {
  var prefix = (window.__PATH_PREFIX__ || '/').replace(/\/$/, '');

  // --- Color palette ---
  var root = document.documentElement;
  var cs = getComputedStyle(root);

  var seeds = [
    '--color-homework', '--color-exercise', '--color-exam',
    '--color-project', '--color-prompt', '--color-accent',
    '--color-accent-secondary',
  ].map(function(v) { return cs.getPropertyValue(v).trim(); }).filter(Boolean);

  if (seeds.length === 0) seeds.push('#6ea8d9', '#e84040', '#50c878', '#d4a017', '#c084fc');

  function isColorDark(color) {
    var temp = document.createElement('div');
    temp.style.color = color;
    document.body.appendChild(temp);
    var computed = getComputedStyle(temp).color;
    document.body.removeChild(temp);
    var m = computed.match(/(\d+)/g);
    if (!m) return true;
    var r = Number(m[0]), g = Number(m[1]), b = Number(m[2]);
    return (r * 299 + g * 587 + b * 114) / 1000 < 128;
  }

  function buildPalette(numChapters) {
    if (numChapters <= seeds.length) return seeds.slice(0, numChapters);
    var bg = cs.getPropertyValue('--color-bg').trim();
    var isDark = !isColorDark(bg);
    var sat = isDark ? 65 : 55;
    var lit = isDark ? 60 : 45;
    var extended = seeds.slice();
    for (var i = seeds.length; i < numChapters; i++) {
      var hue = (i * 137.5) % 360;
      extended.push('hsl(' + hue + ', ' + sat + '%, ' + lit + '%)');
    }
    return extended;
  }

  // Collect chapters
  var chapterMap = new Map();
  data.nodes.forEach(function(n) {
    if (!chapterMap.has(n.chapter_index)) {
      chapterMap.set(n.chapter_index, n.chapter);
    }
  });
  var palette = buildPalette(chapterMap.size);

  function chapterColor(idx) { return palette[idx % palette.length]; }

  // --- Compute degree ---
  var degreeMap = new Map();
  data.nodes.forEach(function(n) { degreeMap.set(n.id, 0); });
  data.edges.forEach(function(e) {
    degreeMap.set(e.source, (degreeMap.get(e.source) || 0) + 1);
    degreeMap.set(e.target, (degreeMap.get(e.target) || 0) + 1);
  });

  var nodeById = new Map();
  data.nodes.forEach(function(n) { nodeById.set(n.id, n); });

  // --- Build Cytoscape elements ---
  var BASE_SIZE = 16;
  var SCALE = 7;

  var cyNodes = data.nodes.map(function(n) {
    var deg = degreeMap.get(n.id) || 0;
    return {
      data: {
        id: n.id,
        label: n.title,
        url: n.url,
        chapter: n.chapter,
        chapter_index: n.chapter_index,
        degree: deg,
        nodeSize: BASE_SIZE + Math.sqrt(deg) * SCALE,
        nodeColor: chapterColor(n.chapter_index),
      }
    };
  });

  var cyEdges = data.edges.map(function(e, i) {
    var srcNode = nodeById.get(e.source);
    return {
      data: {
        id: 'e' + i,
        source: e.source,
        target: e.target,
        edgeColor: srcNode ? chapterColor(srcNode.chapter_index) : palette[0],
      }
    };
  });

  var textColor = cs.getPropertyValue('--color-text').trim() || '#eee';
  var bgColor = cs.getPropertyValue('--color-bg').trim() || '#111';

  // --- Layouts with generous spacing ---
  var LAYOUTS = {
    force: {
      name: 'cose',
      animate: true,
      animationDuration: 600,
      nodeRepulsion: function() { return 20000; },
      idealEdgeLength: function() { return 120; },
      edgeElasticity: function() { return 100; },
      gravity: 0.15,
      numIter: 2000,
      padding: 40,
      nodeOverlap: 30,
      randomize: true,
    },
    hierarchy: {
      name: 'breadthfirst',
      directed: true,
      animate: true,
      animationDuration: 400,
      spacingFactor: 1.8,
      padding: 40,
    },
    circular: {
      name: 'circle',
      animate: true,
      animationDuration: 400,
      padding: 40,
    },
    grid: {
      name: 'grid',
      animate: true,
      animationDuration: 400,
      padding: 40,
      avoidOverlap: true,
    },
  };

  // --- Initialize Cytoscape ---
  var cy = cytoscape({
    container: container,
    elements: cyNodes.concat(cyEdges),
    style: [
      {
        selector: 'node',
        style: {
          'width': 'data(nodeSize)',
          'height': 'data(nodeSize)',
          'background-color': 'data(nodeColor)',
          'label': 'data(label)',
          'font-size': 11,
          'font-weight': 'bold',
          'color': textColor,
          'text-valign': 'top',
          'text-halign': 'center',
          'text-margin-y': -6,
          'text-opacity': 0,
          'text-outline-color': bgColor,
          'text-outline-width': 2,
          'text-max-width': '100px',
          'text-wrap': 'ellipsis',
          'min-zoomed-font-size': 8,
        }
      },
      {
        selector: 'node[degree >= 2]',
        style: {
          'text-opacity': 0.9,
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 1.5,
          'line-color': 'data(edgeColor)',
          'line-opacity': 0.4,
          'target-arrow-color': 'data(edgeColor)',
          'target-arrow-shape': 'triangle',
          'arrow-scale': 0.8,
          'curve-style': 'bezier',
        }
      },
      {
        selector: '.highlighted',
        style: {
          'line-opacity': 0.85,
          'z-index': 10,
        }
      },
      {
        selector: '.faded',
        style: {
          'opacity': 0.1,
        }
      },
      {
        selector: '.search-match',
        style: {
          'border-width': 3,
          'border-color': textColor,
          'text-opacity': 1,
        }
      },
    ],
    layout: { name: 'grid' },
    wheelSensitivity: 0.3,
    minZoom: 0.2,
    maxZoom: 4,
  });

  // Run force layout after a frame (ensures container dimensions)
  if (data.edges.length > 0) {
    requestAnimationFrame(function() {
      cy.layout(LAYOUTS.force).run();
    });
  }

  // --- Tooltip ---
  var tooltip = document.createElement('div');
  tooltip.style.cssText =
    'position:absolute;padding:6px 10px;border-radius:6px;font-size:12px;' +
    'pointer-events:none;opacity:0;z-index:10;transition:opacity 0.15s;' +
    'background:var(--color-bg-secondary,#222);border:1px solid var(--color-border,#444);' +
    'color:var(--color-text,#eee);max-width:250px;white-space:nowrap;';
  container.style.position = 'relative';
  container.appendChild(tooltip);

  // --- Interactions ---
  cy.on('mouseover', 'node', function(evt) {
    var node = evt.target;
    var neighborhood = node.closedNeighborhood();
    cy.elements().not(neighborhood).addClass('faded');
    neighborhood.connectedEdges().addClass('highlighted');
    neighborhood.nodes().style('text-opacity', 1);

    var pos = evt.renderedPosition || evt.position;
    tooltip.innerHTML =
      '<strong>' + node.data('label') + '</strong><br>' +
      '<span style="opacity:0.7">' + node.data('chapter') + '</span>';
    tooltip.style.opacity = '1';
    tooltip.style.left = (pos.x + 15) + 'px';
    tooltip.style.top = (pos.y - 10) + 'px';
  });

  cy.on('mousemove', 'node', function(evt) {
    var pos = evt.renderedPosition || evt.position;
    tooltip.style.left = (pos.x + 15) + 'px';
    tooltip.style.top = (pos.y - 10) + 'px';
  });

  cy.on('mouseout', 'node', function() {
    cy.elements().removeClass('faded highlighted');
    cy.nodes().forEach(function(n) {
      n.style('text-opacity', n.data('degree') >= 2 ? 0.9 : 0);
    });
    tooltip.style.opacity = '0';
  });

  cy.on('tap', 'node', function(evt) {
    var url = evt.target.data('url');
    if (url) window.location.href = prefix + url;
  });

  cy.on('mouseover', 'node', function() { container.style.cursor = 'pointer'; });
  cy.on('mouseout', 'node', function() { container.style.cursor = 'default'; });

  // --- Status ---
  function updateStatus() {
    if (!statusEl) return;
    var vn = cy.nodes(':visible').length;
    var ve = cy.edges(':visible').length;
    statusEl.textContent = 'Nodos: ' + vn + '  |  Aristas: ' + ve + '  |  Click en un nodo para navegar';
  }
  updateStatus();

  // --- Fuzzy search ---
  var searchInput = document.getElementById('graph-search');
  if (searchInput) {
    searchInput.addEventListener('input', function() {
      var q = searchInput.value.trim();
      cy.nodes().removeClass('search-match');
      if (!q) {
        cy.elements().removeClass('faded');
        updateStatus();
        return;
      }
      var matches = cy.nodes().filter(function(n) {
        return fuzzyMatch(q, n.data('label'));
      });
      cy.elements().addClass('faded');
      matches.removeClass('faded').addClass('search-match');
      matches.connectedEdges().removeClass('faded');
      // Also show neighbors of matches (dimmed less)
      matches.neighborhood().nodes().removeClass('faded').style('opacity', 0.5);
      updateStatus();
    });
  }

  // --- Layout switcher ---
  var layoutSelect = document.getElementById('graph-layout');
  if (layoutSelect) {
    layoutSelect.addEventListener('change', function() {
      var name = layoutSelect.value;
      cy.layout(LAYOUTS[name] || LAYOUTS.force).run();
    });
  }

  // --- Fit ---
  var fitBtn = document.getElementById('graph-fit');
  if (fitBtn) {
    fitBtn.addEventListener('click', function() {
      cy.fit(cy.elements(':visible'), 40);
    });
  }

  // --- Reset ---
  var resetBtn = document.getElementById('graph-reset');
  if (resetBtn) {
    resetBtn.addEventListener('click', function() {
      if (searchInput) searchInput.value = '';
      cy.nodes().removeClass('search-match');
      cy.elements().removeClass('faded hidden');
      cy.elements().style('display', 'element');
      cy.nodes().style('opacity', 1);
      var legendContainer = document.getElementById('graph-legend');
      if (legendContainer) {
        legendContainer.querySelectorAll('[data-chapter]').forEach(function(chip) {
          chip.style.opacity = '1';
          chip.dataset.active = 'true';
        });
      }
      if (layoutSelect) layoutSelect.value = 'force';
      cy.layout(LAYOUTS.force).run();
      updateStatus();
    });
  }

  // --- Expand / Fullscreen toggle ---
  var expandBtn = document.getElementById('graph-expand');
  var graphContainer = document.getElementById('graph-container');
  var isExpanded = false;
  if (expandBtn && graphContainer) {
    expandBtn.addEventListener('click', function() {
      isExpanded = !isExpanded;
      if (isExpanded) {
        graphContainer.style.height = 'calc(100vh - 4rem)';
        graphContainer.style.position = 'relative';
        graphContainer.style.zIndex = '20';
        expandBtn.innerHTML = '&#x26F6; Contraer';
      } else {
        graphContainer.style.height = 'calc(100vh - 14rem)';
        graphContainer.style.position = '';
        graphContainer.style.zIndex = '';
        expandBtn.innerHTML = '&#x26F6; Expandir';
      }
      // Let Cytoscape recalculate after resize
      setTimeout(function() {
        cy.resize();
        cy.fit(cy.elements(':visible'), 40);
      }, 350);
    });
  }

  // --- Legend / Chapter filter chips ---
  var legendEl = document.getElementById('graph-legend');
  if (legendEl) {
    var sortedChapters = Array.from(chapterMap.entries()).sort(function(a, b) { return a[0] - b[0]; });
    sortedChapters.forEach(function(entry) {
      var idx = entry[0];
      var name = entry[1];
      var chip = document.createElement('span');
      chip.className = 'flex items-center gap-1 cursor-pointer select-none transition-opacity';
      chip.dataset.chapter = idx;
      chip.dataset.active = 'true';
      chip.innerHTML =
        '<span class="w-3 h-3 rounded-full inline-block flex-shrink-0" style="background:' + chapterColor(idx) + '"></span>' + name;

      chip.addEventListener('click', function() {
        var isActive = chip.dataset.active === 'true';
        chip.dataset.active = isActive ? 'false' : 'true';
        chip.style.opacity = isActive ? '0.3' : '1';

        var chapterNodes = cy.nodes('[chapter_index = ' + idx + ']');
        if (isActive) {
          chapterNodes.addClass('hidden').style('display', 'none');
        } else {
          chapterNodes.removeClass('hidden').style('display', 'element');
        }
        cy.edges().forEach(function(e) {
          var srcVis = e.source().style('display') !== 'none';
          var tgtVis = e.target().style('display') !== 'none';
          e.style('display', (srcVis && tgtVis) ? 'element' : 'none');
        });
        updateStatus();
      });

      legendEl.appendChild(chip);
    });
  }

  // --- Responsive ---
  window.addEventListener('resize', function() { cy.resize(); });
}
