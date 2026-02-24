/**
 * Primeval Current — Knowledge Graph Visualization
 * d3.js force-directed graph. Only runs on the /grafo/ page.
 */

export function initGraph() {
  const data = window.__GRAPH_DATA__;
  if (!data || !data.nodes || !data.nodes.length || typeof d3 === 'undefined') return;

  const container = document.getElementById('graph-svg');
  if (!container) return;

  const prefix = (window.__PATH_PREFIX__ || '/').replace(/\/$/, '');

  function nodeHref(url) { return prefix + url; }

  // Read theme colors from CSS custom properties
  const root = document.documentElement;
  const PALETTE = [
    '--color-homework', '--color-exercise', '--color-exam',
    '--color-project', '--color-prompt', '--color-accent',
    '--color-accent-secondary',
  ].map(v => getComputedStyle(root).getPropertyValue(v).trim()).filter(Boolean);

  if (PALETTE.length === 0) PALETTE.push('#6ea8d9', '#e84040', '#50c878', '#d4a017', '#c084fc');

  function chapterColor(idx) { return PALETTE[idx % PALETTE.length]; }

  // Build lookup structures
  const nodeById = new Map();
  data.nodes.forEach(n => nodeById.set(n.id, n));

  // Compute degree for sizing
  const degree = new Map();
  data.nodes.forEach(n => degree.set(n.id, 0));
  data.edges.forEach(e => {
    degree.set(e.source, (degree.get(e.source) || 0) + 1);
    degree.set(e.target, (degree.get(e.target) || 0) + 1);
  });

  // Node sizing
  const BASE_RADIUS = 5;
  const SCALE = 2;
  function nodeRadius(id) {
    return BASE_RADIUS + Math.sqrt(degree.get(id) || 0) * SCALE;
  }

  // Dimensions
  const rect = container.getBoundingClientRect();
  let width = rect.width || 800;
  let height = rect.height || 500;

  // Create SVG
  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', [0, 0, width, height]);

  // Arrow markers
  svg.append('defs').append('marker')
    .attr('id', 'arrowhead')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 15)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', 'var(--color-text-muted, #888)');

  // Main group for zoom/pan
  const g = svg.append('g');

  // Zoom behavior
  const zoom = d3.zoom()
    .scaleExtent([0.1, 5])
    .on('zoom', (event) => g.attr('transform', event.transform));

  svg.call(zoom);

  // Edges
  const linkGroup = g.append('g').attr('class', 'links');
  const link = linkGroup.selectAll('line')
    .data(data.edges)
    .join('line')
    .attr('stroke', 'var(--color-border, #333)')
    .attr('stroke-opacity', 0.4)
    .attr('stroke-width', 1)
    .attr('marker-end', 'url(#arrowhead)');

  // Nodes
  const nodeGroup = g.append('g').attr('class', 'nodes');
  const node = nodeGroup.selectAll('circle')
    .data(data.nodes)
    .join('circle')
    .attr('r', d => nodeRadius(d.id))
    .attr('fill', d => chapterColor(d.chapter_index))
    .attr('stroke', 'var(--color-bg, #000)')
    .attr('stroke-width', 1.5)
    .style('cursor', 'pointer');

  // Labels (shown for high-degree nodes)
  const labelGroup = g.append('g').attr('class', 'labels');
  const label = labelGroup.selectAll('text')
    .data(data.nodes)
    .join('text')
    .text(d => d.title)
    .attr('font-size', 10)
    .attr('fill', 'var(--color-text-muted, #aaa)')
    .attr('text-anchor', 'middle')
    .attr('dy', d => -nodeRadius(d.id) - 4)
    .attr('opacity', d => (degree.get(d.id) || 0) >= 2 ? 0.8 : 0)
    .style('pointer-events', 'none');

  // Tooltip
  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('padding', '6px 10px')
    .style('background', 'var(--color-bg-secondary, #222)')
    .style('border', '1px solid var(--color-border, #444)')
    .style('border-radius', '6px')
    .style('font-size', '12px')
    .style('color', 'var(--color-text, #eee)')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('z-index', 10);

  // Force simulation
  const simulation = d3.forceSimulation(data.nodes)
    .force('link', d3.forceLink(data.edges)
      .id(d => d.id)
      .distance(80))
    .force('charge', d3.forceManyBody().strength(-150))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collide', d3.forceCollide().radius(d => nodeRadius(d.id) + 4));

  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);

    node
      .attr('cx', d => d.x)
      .attr('cy', d => d.y);

    label
      .attr('x', d => d.x)
      .attr('y', d => d.y);
  });

  // Drag behavior
  const drag = d3.drag()
    .on('start', (event, d) => {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    })
    .on('drag', (event, d) => {
      d.fx = event.x;
      d.fy = event.y;
    })
    .on('end', (event, d) => {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    });

  node.call(drag);

  // Interactions: hover
  node
    .on('mouseover', (event, d) => {
      // Highlight neighbors
      const neighbors = new Set();
      data.edges.forEach(e => {
        const src = typeof e.source === 'object' ? e.source.id : e.source;
        const tgt = typeof e.target === 'object' ? e.target.id : e.target;
        if (src === d.id) neighbors.add(tgt);
        if (tgt === d.id) neighbors.add(src);
      });
      neighbors.add(d.id);

      node.attr('opacity', n => neighbors.has(n.id) ? 1 : 0.15);
      link.attr('stroke-opacity', e => {
        const src = typeof e.source === 'object' ? e.source.id : e.source;
        const tgt = typeof e.target === 'object' ? e.target.id : e.target;
        return src === d.id || tgt === d.id ? 0.8 : 0.05;
      });
      label.attr('opacity', n => neighbors.has(n.id) ? 1 : 0);

      // Tooltip
      tooltip
        .html(`<strong>${d.title}</strong><br><span style="opacity:0.7">${d.chapter}</span>`)
        .style('opacity', 1)
        .style('left', (event.offsetX + 15) + 'px')
        .style('top', (event.offsetY - 10) + 'px');
    })
    .on('mousemove', (event) => {
      tooltip
        .style('left', (event.offsetX + 15) + 'px')
        .style('top', (event.offsetY - 10) + 'px');
    })
    .on('mouseout', () => {
      node.attr('opacity', 1);
      link.attr('stroke-opacity', 0.4);
      label.attr('opacity', d => (degree.get(d.id) || 0) >= 2 ? 0.8 : 0);
      tooltip.style('opacity', 0);
    });

  // Click: navigate
  node.on('click', (event, d) => {
    window.location.href = nodeHref(d.url);
  });

  // Search
  const searchInput = document.getElementById('graph-search');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const query = searchInput.value.toLowerCase().trim();
      if (!query) {
        node.attr('opacity', 1);
        label.attr('opacity', d => (degree.get(d.id) || 0) >= 2 ? 0.8 : 0);
        return;
      }
      node.attr('opacity', d => d.title.toLowerCase().includes(query) ? 1 : 0.1);
      label.attr('opacity', d => d.title.toLowerCase().includes(query) ? 1 : 0);
    });
  }

  // Fit button
  const fitBtn = document.getElementById('graph-fit');
  if (fitBtn) {
    fitBtn.addEventListener('click', () => {
      svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity);
    });
  }

  // Legend
  const legendEl = document.getElementById('graph-legend');
  if (legendEl) {
    const chapters = new Map();
    data.nodes.forEach(n => {
      if (!chapters.has(n.chapter_index)) {
        chapters.set(n.chapter_index, n.chapter);
      }
    });
    chapters.forEach((name, idx) => {
      const item = document.createElement('span');
      item.className = 'flex items-center gap-1 cursor-pointer';
      item.innerHTML = `<span class="w-3 h-3 rounded-full inline-block" style="background:${chapterColor(idx)}"></span>${name}`;
      item.addEventListener('click', () => {
        const visible = item.style.opacity !== '0.3';
        item.style.opacity = visible ? '0.3' : '1';
        node.attr('opacity', d => {
          if (d.chapter_index === idx) return visible ? 0.1 : 1;
          return node.filter(n => n === d).attr('opacity');
        });
      });
      legendEl.appendChild(item);
    });
  }

  // Handle empty graph (nodes but no edges)
  if (data.edges.length === 0 && data.nodes.length > 0) {
    const cols = Math.ceil(Math.sqrt(data.nodes.length));
    const spacing = Math.min(width, height) / (cols + 1);
    data.nodes.forEach((n, i) => {
      n.fx = spacing + (i % cols) * spacing;
      n.fy = spacing + Math.floor(i / cols) * spacing;
    });
    simulation.alpha(0.01).restart();
  }

  // Responsive
  window.addEventListener('resize', () => {
    const r = container.getBoundingClientRect();
    width = r.width || 800;
    height = r.height || 500;
    svg.attr('width', width).attr('height', height)
       .attr('viewBox', [0, 0, width, height]);
    simulation.force('center', d3.forceCenter(width / 2, height / 2));
    simulation.alpha(0.3).restart();
  });
}
