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
  const graphExpand = document.getElementById("graph-expand");
  const status = document.getElementById("graph-status");
  const groupFilters = Array.from(document.querySelectorAll("[data-raya-graph-group-filter]"));
  const detailEmpty = document.querySelector("[data-raya-graph-detail-empty]");
  const detailPanel = document.querySelector("[data-raya-graph-detail-panel]");
  const detailTitle = document.querySelector("[data-raya-graph-detail-title]");
  const detailMeta = document.querySelector("[data-raya-graph-detail-meta]");
  const detailNeighborhood = document.querySelector("[data-raya-graph-detail-neighborhood]");
  const detailLink = document.querySelector("[data-raya-graph-detail-link]");
  const detailOutgoing = document.querySelector("[data-raya-graph-detail-outgoing]");
  const detailIncoming = document.querySelector("[data-raya-graph-detail-incoming]");
  const detailClear = document.querySelector("[data-raya-graph-detail-clear]");

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
  const backlinks = graph.backlinks && typeof graph.backlinks === "object" ? graph.backlinks : {};
  const nodesById = new Map(nodes.map((node) => [node.id, node]));
  const groupsById = new Map(groups.map((group) => [group.id, group]));
  const hiddenGroups = new Set();
  let query = "";
  let selectedId = "";
  let matchIds = new Set();
  let pendingSelectTimer = 0;

  function normalize(value) {
    return String(value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }

  function levenshtein(a, b) {
    const left = normalize(a);
    const right = normalize(b);
    if (left.length === 0) return right.length;
    if (right.length === 0) return left.length;
    const previous = Array.from({ length: right.length + 1 }, (_, index) => index);
    const current = Array(right.length + 1).fill(0);
    for (let i = 1; i <= left.length; i += 1) {
      current[0] = i;
      for (let j = 1; j <= right.length; j += 1) {
        const cost = left[i - 1] === right[j - 1] ? 0 : 1;
        current[j] = Math.min(
          previous[j] + 1,
          current[j - 1] + 1,
          previous[j - 1] + cost
        );
      }
      for (let j = 0; j <= right.length; j += 1) {
        previous[j] = current[j];
      }
    }
    return previous[right.length];
  }

  function fuzzyMatch(queryText, targetText) {
    const needle = normalize(queryText);
    const haystack = normalize(targetText);
    if (!needle) return true;
    if (haystack.includes(needle)) return true;
    const words = haystack.split(/[\s_\/-]+/).filter(Boolean);
    if (words.some((word) => word.startsWith(needle))) return true;
    const threshold = needle.length <= 3 ? 1 : Math.floor(needle.length * 0.35);
    return words.some((word) => levenshtein(needle, word) <= threshold) ||
      (haystack.length <= 28 && levenshtein(needle, haystack) <= threshold);
  }

  function nodeSearchText(node) {
    const group = groupsById.get(node.group || "");
    return [
      node.title,
      node.nav_title,
      node.id,
      node.status,
      node.hierarchy_label,
      group ? group.title : "",
      Array.isArray(node.tags) ? node.tags.join(" ") : "",
    ].join(" ");
  }

  function matchesNode(node) {
    if (hiddenGroups.has(node.group || "")) return false;
    if (!query) return true;
    return fuzzyMatch(query, nodeSearchText(node));
  }

  function visibleNodes() {
    const directlyVisible = nodes.filter(matchesNode);
    matchIds = new Set(query ? directlyVisible.map((node) => node.id) : []);
    if (!query) {
      return directlyVisible;
    }
    const expandedIds = new Set(matchIds);
    directlyVisible.forEach((node) => {
      neighborsOf(node.id).forEach((id) => {
        const neighbor = nodesById.get(id);
        if (neighbor && !hiddenGroups.has(neighbor.group || "")) {
          expandedIds.add(id);
        }
      });
    });
    return nodes.filter((node) => expandedIds.has(node.id));
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

  function connectedNodeIds(nodeId) {
    const ids = neighborsOf(nodeId);
    ids.delete(nodeId);
    return ids;
  }

  function relationshipCountsFor(nodeId) {
    const connectedIds = new Set();
    let outgoingCount = 0;
    let incomingCount = 0;
    edges.forEach((edge) => {
      if (edge.from === nodeId) {
        outgoingCount += 1;
        connectedIds.add(edge.to);
      }
      if (edge.to === nodeId) {
        incomingCount += 1;
        connectedIds.add(edge.from);
      }
    });
    connectedIds.delete(nodeId);
    return {
      outgoingCount,
      incomingCount,
      connectedCount: connectedIds.size,
    };
  }

  function edgeLabel(edge) {
    const kind = edge && edge.kind ? edge.kind : "link";
    return kind.replace(/-/g, " ");
  }

  function renderDetailList(listEl, items, emptyText) {
    if (!listEl) return;
    listEl.replaceChildren();
    if (items.length === 0) {
      const empty = document.createElement("li");
      empty.textContent = emptyText;
      listEl.appendChild(empty);
      return;
    }
    items.forEach((item) => {
      const li = document.createElement("li");
      const link = document.createElement("a");
      link.href = item.url || "#";
      link.textContent = item.title || item.id || "Untitled page";
      const meta = document.createElement("span");
      meta.className = "raya-graph-detail-edge-kind";
      meta.textContent = ` ${item.kind || "link"}`;
      li.append(link, meta);
      listEl.appendChild(li);
    });
  }

  function renderDetail() {
    const node = selectedId ? nodesById.get(selectedId) : null;
    if (!node) {
      if (detailEmpty) detailEmpty.hidden = false;
      if (detailPanel) detailPanel.hidden = true;
      if (detailNeighborhood) detailNeighborhood.textContent = "";
      return;
    }
    const group = groupsById.get(node.group || "");
    if (detailEmpty) detailEmpty.hidden = true;
    if (detailPanel) detailPanel.hidden = false;
    if (detailTitle) detailTitle.textContent = node.title || node.nav_title || node.id;
    if (detailMeta) {
      detailMeta.textContent = [
        group ? `Group: ${group.title}` : "Group: Course",
        node.status ? `Status: ${node.status}` : "",
        Array.isArray(node.tags) && node.tags.length ? `Tags: ${node.tags.join(", ")}` : "",
      ].filter(Boolean).join("; ");
    }
    if (detailNeighborhood) {
      const counts = relationshipCountsFor(node.id);
      detailNeighborhood.textContent = `Neighborhood: ${counts.outgoingCount} outgoing link(s), ${counts.incomingCount} incoming link(s), ${counts.connectedCount} connected page(s).`;
    }
    if (detailLink) {
      detailLink.href = node.url;
      detailLink.textContent = "Open page";
    }
    const outgoing = edges
      .filter((edge) => edge.from === node.id)
      .map((edge) => {
        const target = nodesById.get(edge.to) || {};
        return {
          id: edge.to,
          title: target.title || edge.to,
          url: target.url || "#",
          kind: edgeLabel(edge),
        };
      });
    const incoming = Array.isArray(backlinks[node.id])
      ? backlinks[node.id].map((backlink) => ({
          id: backlink.from,
          title: backlink.title,
          url: backlink.url,
          kind: edgeLabel(backlink),
        }))
      : [];
    renderDetailList(detailOutgoing, outgoing, "No outgoing links.");
    renderDetailList(detailIncoming, incoming, "No incoming links.");
  }

  function selectGraphNode(nodeId) {
    selectedId = nodeId;
    renderDetail();
    render();
  }

  function clearGraphSelection() {
    selectedId = "";
    renderDetail();
    render();
  }

  function initialPageFocus() {
    try {
      const params = new URLSearchParams(window.location.search || "");
      const pageId = params.get("page") || "";
      return nodesById.has(pageId) ? pageId : "";
    } catch {
      return "";
    }
  }

  function renderList(activeIds) {
    const connectedIds = selectedId ? connectedNodeIds(selectedId) : new Set();
    list.querySelectorAll("[data-raya-graph-node]").forEach((item) => {
      const id = item.getAttribute("data-raya-graph-node") || "";
      item.hidden = !activeIds.has(id);
      item.classList.toggle("is-active", id === selectedId);
      item.classList.toggle("is-neighbor", connectedIds.has(id));
      item.classList.toggle("is-match", matchIds.has(id));
    });
  }

  function setGraphExpanded(nextExpanded) {
    root.dataset.rayaGraphExpanded = nextExpanded ? "true" : "false";
    root.setAttribute("data-raya-graph-expanded", nextExpanded ? "true" : "false");
    if (graphExpand) {
      graphExpand.setAttribute("aria-pressed", nextExpanded ? "true" : "false");
      graphExpand.textContent = nextExpanded ? "Compact graph" : "Expand graph";
    }
  }

  function render() {
    const mode = layout ? layout.value : "map";
    root.setAttribute("data-raya-graph-layout", mode);
    query = normalize(search ? search.value : "");
    const activeNodes = visibleNodes();
    const activeIds = new Set(activeNodes.map((node) => node.id));
    const activeEdges = visibleEdges(activeIds);
    if (selectedId && !activeIds.has(selectedId)) {
      selectedId = "";
      renderDetail();
    }
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
    const connectedIds = selectedId ? connectedNodeIds(selectedId) : new Set();
    const selectedCluster = selectedId ? new Set([selectedId, ...connectedIds]) : new Set();
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
      const active = !selectedId || selectedCluster.has(node.id);
      const isConnected = connectedIds.has(node.id);
      group.setAttribute(
        "class",
        [
          "raya-graph-node",
          active ? "" : "is-muted",
          node.id === selectedId ? "is-selected" : "",
          isConnected ? "is-neighbor" : "",
          matchIds.has(node.id) ? "is-match" : "",
        ].filter(Boolean).join(" ")
      );
      group.setAttribute("transform", `translate(${point.x} ${point.y})`);
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("r", node.id === selectedId ? "18" : "14");
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("y", "34");
      text.textContent = node.nav_title || node.title || node.id;
      group.append(circle, text);
      link.appendChild(group);
      link.addEventListener("click", (event) => {
        event.preventDefault();
        window.clearTimeout(pendingSelectTimer);
        pendingSelectTimer = window.setTimeout(() => {
          selectGraphNode(node.id);
        }, 180);
      });
      link.addEventListener("dblclick", (event) => {
        event.preventDefault();
        window.clearTimeout(pendingSelectTimer);
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
      setGraphExpanded(false);
      renderDetail();
      groupFilters.forEach((button) => {
        button.setAttribute("aria-pressed", "true");
      });
      render();
    });
  }
  if (graphExpand) {
    graphExpand.addEventListener("click", () => {
      setGraphExpanded(root.dataset.rayaGraphExpanded !== "true");
      render();
    });
  }
  if (detailClear) {
    detailClear.addEventListener("click", clearGraphSelection);
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
    if (!detailPanel || detailPanel.hidden) {
      selectedId = "";
    }
    render();
  });

  selectedId = initialPageFocus();
  setGraphExpanded(false);
  renderDetail();
  render();
})();
"""
