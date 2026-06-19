from __future__ import annotations

from dataclasses import dataclass


GRAPH_SCRIPT_NAME = "graph.js"
GRAPH_RESOURCE_PATH = "_raya/render"


@dataclass(frozen=True)
class GraphResources:
    javascript: str


def graph_resources() -> GraphResources:
    return GraphResources(javascript=_GRAPH_JAVASCRIPT)


_GRAPH_JAVASCRIPT = r"""
(() => {
  const root = document.querySelector("[data-raya-graph-page]");
  const dataEl = document.getElementById("raya-graph-data");
  const canvas = document.getElementById("raya-graph-canvas");
  const list = document.getElementById("raya-graph-list");
  const search = document.getElementById("graph-search");
  const layout = document.getElementById("graph-layout");
  const fit = document.getElementById("graph-fit");
  const reset = document.getElementById("graph-reset");
  const status = document.getElementById("graph-status");
  const groupFilters = Array.from(document.querySelectorAll("[data-raya-graph-group-filter]"));

  if (!root || !dataEl || !canvas || !list) {
    return;
  }

  let graph;
  try {
    graph = JSON.parse(dataEl.textContent || "{}");
  } catch {
    if (status) status.textContent = "Graph data could not be read.";
    return;
  }

  const nodes = Array.isArray(graph.nodes) ? graph.nodes : [];
  const edges = Array.isArray(graph.edges) ? graph.edges : [];
  const groups = Array.isArray(graph.groups) ? graph.groups : [];
  const hiddenGroups = new Set();
  let query = "";
  let selectedId = "";

  function normalize(value) {
    return String(value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }

  function matchesNode(node) {
    if (hiddenGroups.has(node.group || "")) return false;
    if (!query) return true;
    const haystack = normalize([node.title, node.nav_title, node.id].join(" "));
    return haystack.includes(query) || haystack.split(/\s+/).some((word) => word.startsWith(query));
  }

  function visibleNodes() {
    return nodes.filter(matchesNode);
  }

  function visibleEdges(visibleIds) {
    return edges.filter((edge) => visibleIds.has(edge.from) && visibleIds.has(edge.to));
  }

  function groupTitle(groupId) {
    const group = groups.find((item) => item.id === groupId);
    return group ? group.title : "Course";
  }

  function positionsFor(activeNodes, mode) {
    const width = 960;
    const height = 560;
    const positions = new Map();
    if (mode === "radial") {
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = Math.min(width, height) * 0.36;
      activeNodes.forEach((node, index) => {
        const angle = (Math.PI * 2 * index) / Math.max(activeNodes.length, 1) - Math.PI / 2;
        positions.set(node.id, {
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius,
        });
      });
      return { width, height, positions };
    }

    const byGroup = new Map();
    activeNodes.forEach((node) => {
      const group = node.group || "";
      if (!byGroup.has(group)) byGroup.set(group, []);
      byGroup.get(group).push(node);
    });
    const orderedGroups = Array.from(byGroup.keys()).sort((a, b) => {
      const aOrder = groups.find((group) => group.id === a)?.order || 0;
      const bOrder = groups.find((group) => group.id === b)?.order || 0;
      return aOrder - bOrder || groupTitle(a).localeCompare(groupTitle(b));
    });
    const columnWidth = width / Math.max(orderedGroups.length, 1);
    orderedGroups.forEach((groupId, groupIndex) => {
      const groupNodes = byGroup.get(groupId) || [];
      groupNodes.forEach((node, nodeIndex) => {
        positions.set(node.id, {
          x: columnWidth * groupIndex + columnWidth / 2,
          y: 80 + nodeIndex * Math.max(58, (height - 140) / Math.max(groupNodes.length, 1)),
        });
      });
    });
    return { width, height, positions };
  }

  function neighborsOf(nodeId) {
    const ids = new Set([nodeId]);
    edges.forEach((edge) => {
      if (edge.from === nodeId) ids.add(edge.to);
      if (edge.to === nodeId) ids.add(edge.from);
    });
    return ids;
  }

  function renderList(activeIds) {
    list.querySelectorAll("[data-raya-graph-node]").forEach((item) => {
      const id = item.getAttribute("data-raya-graph-node") || "";
      item.hidden = !activeIds.has(id);
      item.classList.toggle("is-active", id === selectedId);
    });
  }

  function render() {
    const mode = layout ? layout.value : "map";
    root.setAttribute("data-raya-graph-layout", mode);
    query = normalize(search ? search.value : "");
    const activeNodes = visibleNodes();
    const activeIds = new Set(activeNodes.map((node) => node.id));
    const activeEdges = visibleEdges(activeIds);
    renderList(activeIds);
    if (status) {
      status.textContent = `${activeNodes.length} visible node(s), ${activeEdges.length} visible edge(s).`;
    }
    if (mode === "list") {
      canvas.setAttribute("hidden", "hidden");
      canvas.replaceChildren();
      return;
    }
    canvas.removeAttribute("hidden");
    const selectedNeighbors = selectedId ? neighborsOf(selectedId) : new Set();
    const geometry = positionsFor(activeNodes, mode);

    canvas.setAttribute("viewBox", `0 0 ${geometry.width} ${geometry.height}`);
    canvas.replaceChildren();

    activeEdges.forEach((edge) => {
      const from = geometry.positions.get(edge.from);
      const to = geometry.positions.get(edge.to);
      if (!from || !to) return;
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", String(from.x));
      line.setAttribute("y1", String(from.y));
      line.setAttribute("x2", String(to.x));
      line.setAttribute("y2", String(to.y));
      line.setAttribute(
        "class",
        selectedId && (edge.from === selectedId || edge.to === selectedId)
          ? "raya-graph-edge is-active"
          : "raya-graph-edge"
      );
      canvas.appendChild(line);
    });

    activeNodes.forEach((node) => {
      const point = geometry.positions.get(node.id);
      if (!point) return;
      const link = document.createElementNS("http://www.w3.org/2000/svg", "a");
      link.setAttribute("href", node.url);
      link.setAttribute("class", "raya-graph-node-link");
      link.dataset.rayaGraphNode = node.id;
      const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const active = !selectedId || selectedNeighbors.has(node.id);
      group.setAttribute("class", active ? "raya-graph-node" : "raya-graph-node is-muted");
      group.setAttribute("transform", `translate(${point.x} ${point.y})`);
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("r", node.id === selectedId ? "18" : "14");
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("y", "34");
      text.textContent = node.nav_title || node.title || node.id;
      group.append(circle, text);
      link.appendChild(group);
      link.addEventListener("mouseenter", () => {
        selectedId = node.id;
        render();
      });
      link.addEventListener("focus", () => {
        selectedId = node.id;
        render();
      });
      link.addEventListener("click", (event) => {
        event.preventDefault();
        window.location.href = node.url;
      });
      canvas.appendChild(link);
    });
  }

  if (search) search.addEventListener("input", render);
  if (layout) layout.addEventListener("change", render);
  if (fit) fit.addEventListener("click", render);
  if (reset) {
    reset.addEventListener("click", () => {
      if (search) search.value = "";
      if (layout) layout.value = "map";
      hiddenGroups.clear();
      selectedId = "";
      groupFilters.forEach((button) => {
        button.setAttribute("aria-pressed", "true");
      });
      render();
    });
  }
  groupFilters.forEach((button) => {
    button.addEventListener("click", () => {
      const group = button.getAttribute("data-raya-graph-group-filter") || "";
      if (hiddenGroups.has(group)) {
        hiddenGroups.delete(group);
        button.setAttribute("aria-pressed", "true");
      } else {
        hiddenGroups.add(group);
        button.setAttribute("aria-pressed", "false");
      }
      render();
    });
  });
  canvas.addEventListener("mouseleave", () => {
    selectedId = "";
    render();
  });

  render();
})();
"""
