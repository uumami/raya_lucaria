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
  const zoomIn = document.getElementById("graph-zoom-in");
  const zoomOut = document.getElementById("graph-zoom-out");
  const resetView = document.getElementById("graph-reset-view");
  const panButtons = Array.from(document.querySelectorAll("[data-raya-graph-pan]"));
  const reset = document.getElementById("graph-reset");
  const graphExpand = document.getElementById("graph-expand");
  const panelToggles = Array.from(document.querySelectorAll("[data-raya-graph-toggle-panel]"));
  const status = document.getElementById("graph-status");
  const hoverStatus = document.querySelector("[data-raya-graph-hover-status]");
  const groupFilters = Array.from(document.querySelectorAll("[data-raya-graph-group-filter]"));
  const detailEmpty = document.querySelector("[data-raya-graph-detail-empty]");
  const detailPanel = document.querySelector("[data-raya-graph-detail-panel]");
  const detailTitle = document.querySelector("[data-raya-graph-detail-title]");
  const detailSummary = document.querySelector("[data-raya-graph-detail-summary]");
  const detailMeta = document.querySelector("[data-raya-graph-detail-meta]");
  const detailStudyCounts = document.querySelector("[data-raya-graph-detail-study-counts]");
  const detailNeighborhood = document.querySelector("[data-raya-graph-detail-neighborhood]");
  const detailLink = document.querySelector("[data-raya-graph-detail-link]");
  const detailSearchLink = document.querySelector("[data-raya-graph-detail-search-link]");
  const detailPracticeLink = document.querySelector("[data-raya-graph-detail-practice-link]");
  const focusNeighborhood = document.querySelector("[data-raya-graph-focus-neighborhood]");
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
  let inspectedId = "";
  let activeResultId = "";
  let neighborhoodFocus = false;
  let matchIds = new Set();
  let pendingSelectTimer = 0;
  let fullViewBox = null;
  let graphViewBox = null;
  let graphPanStart = null;

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
      node.stable_id,
      node.status,
      node.hierarchy_label,
      node.summary,
      group ? group.title : "",
      node.study_counts ? Object.keys(node.study_counts).join(" ") : "",
      Array.isArray(node.tags) ? node.tags.join(" ") : "",
    ].join(" ");
  }

  function matchesNode(node) {
    if (hiddenGroups.has(node.group || "")) return false;
    if (!query) return true;
    return fuzzyMatch(query, nodeSearchText(node));
  }

  function groupVisibleNodes() {
    return nodes.filter((node) => !hiddenGroups.has(node.group || ""));
  }

  function visibleListNodes() {
    const directlyVisible = nodes.filter(matchesNode);
    matchIds = new Set(query ? directlyVisible.map((node) => node.id) : []);
    if (!query) {
      return applyNeighborhoodFocus(directlyVisible);
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
    return applyNeighborhoodFocus(nodes.filter((node) => expandedIds.has(node.id)));
  }

  function visibleGraphNodes(listNodes) {
    if (!query) return listNodes;
    return applyNeighborhoodFocus(groupVisibleNodes());
  }

  function searchSpotlightIds() {
    if (!query || matchIds.size === 0) return new Set();
    const ids = new Set(matchIds);
    matchIds.forEach((id) => {
      neighborsOf(id).forEach((neighborId) => {
        const neighbor = nodesById.get(neighborId);
        if (neighbor && !hiddenGroups.has(neighbor.group || "")) {
          ids.add(neighborId);
        }
      });
    });
    return ids;
  }

  function searchContextNodeIds() {
    if (!query || matchIds.size === 0) return new Set();
    const ids = searchSpotlightIds();
    matchIds.forEach((id) => ids.delete(id));
    return ids;
  }

  function applyNeighborhoodFocus(activeNodes) {
    if (!neighborhoodFocus || !selectedId) return activeNodes;
    const focusIds = neighborsOf(selectedId);
    return activeNodes.filter((node) => focusIds.has(node.id));
  }

  function visibleEdges(visibleIds) {
    return edges.filter((edge) => visibleIds.has(edge.from) && visibleIds.has(edge.to));
  }

  function groupTitle(groupId) {
    const group = groups.find((item) => item.id === groupId);
    return group ? group.title : "Course";
  }

  function groupColorIndex(groupId) {
    const index = groups.findIndex((group) => group.id === groupId);
    return index >= 0 ? (index % 8) + 1 : 1;
  }

  function edgeColorFor(edge) {
    const source = nodesById.get(edge.from);
    if (!source) return "var(--raya-color-border)";
    return `var(--raya-graph-group-${groupColorIndex(source.group || "")})`;
  }

  function compareNodesByOrder(a, b) {
    const aOrder = Number(a.order || 0);
    const bOrder = Number(b.order || 0);
    return aOrder - bOrder ||
      String(a.title || a.nav_title || a.id).localeCompare(String(b.title || b.nav_title || b.id)) ||
      String(a.id).localeCompare(String(b.id));
  }

  function layoutEdgesFor(activeNodes) {
    const activeIds = new Set(activeNodes.map((node) => node.id));
    const seen = new Set();
    const layoutEdges = [];
    edges.forEach((edge) => {
      if (!activeIds.has(edge.from) || !activeIds.has(edge.to)) return;
      if (edge.kind === "parent") return;
      const fromNode = nodesById.get(edge.from);
      const toNode = nodesById.get(edge.to);
      const fromOrder = Number(fromNode ? fromNode.order || 0 : 0);
      const toOrder = Number(toNode ? toNode.order || 0 : 0);
      let from = edge.from;
      let to = edge.to;
      if (fromOrder > toOrder) {
        if (edge.kind !== "content" && edge.kind !== "prerequisite") return;
        from = edge.to;
        to = edge.from;
      }
      const key = `${from}\u0000${to}`;
      if (seen.has(key)) return;
      seen.add(key);
      layoutEdges.push({ from, to });
    });
    return layoutEdges;
  }

  function sortedGroupIdsFor(activeNodes) {
    const activeGroupIds = Array.from(new Set(activeNodes.map((node) => node.group || "")));
    return activeGroupIds.sort((a, b) => {
      const aGroup = groups.find((group) => group.id === a);
      const bGroup = groups.find((group) => group.id === b);
      const aOrder = Number(aGroup ? aGroup.order || 0 : 0);
      const bOrder = Number(bGroup ? bGroup.order || 0 : 0);
      return aOrder - bOrder || groupTitle(a).localeCompare(groupTitle(b)) || a.localeCompare(b);
    });
  }

  function connectionDepthsFor(activeNodes) {
    const incomingByNode = new Map(activeNodes.map((node) => [node.id, []]));
    const outgoingByNode = new Map(activeNodes.map((node) => [node.id, []]));
    const layoutEdges = layoutEdgesFor(activeNodes);
    layoutEdges.forEach((edge) => {
      incomingByNode.get(edge.to).push(edge.from);
      outgoingByNode.get(edge.from).push(edge.to);
    });

    const orderedNodes = activeNodes.slice().sort(compareNodesByOrder);
    let roots = orderedNodes.filter((node) => (incomingByNode.get(node.id) || []).length === 0);
    if (roots.length === 0 && orderedNodes.length > 0) {
      roots = [orderedNodes[0]];
    }

    const depths = new Map();
    roots.forEach((node) => depths.set(node.id, 0));
    const queue = roots.map((node) => node.id);
    while (queue.length > 0) {
      const id = queue.shift();
      const baseDepth = depths.get(id) || 0;
      (outgoingByNode.get(id) || []).forEach((targetId) => {
        if (!depths.has(targetId)) {
          depths.set(targetId, baseDepth + 1);
          queue.push(targetId);
        }
      });
    }

    for (let pass = 0; pass < activeNodes.length; pass += 1) {
      let changed = false;
      layoutEdges.forEach((edge) => {
        if (!depths.has(edge.from)) return;
        const nextDepth = (depths.get(edge.from) || 0) + 1;
        const currentDepth = depths.has(edge.to) ? depths.get(edge.to) : -1;
        if (nextDepth > currentDepth && nextDepth <= activeNodes.length) {
          depths.set(edge.to, nextDepth);
          changed = true;
        }
      });
      if (!changed) break;
    }

    orderedNodes.forEach((node) => {
      if (depths.has(node.id)) return;
      const incomingDepths = (incomingByNode.get(node.id) || [])
        .filter((id) => depths.has(id))
        .map((id) => (depths.get(id) || 0) + 1);
      depths.set(node.id, incomingDepths.length ? Math.min(...incomingDepths) : 0);
    });

    return { depths, incomingByNode, outgoingByNode };
  }

  function positionsFor(activeNodes, mode) {
    const width = 960;
    const height = 560;
    const positions = new Map();
    if (mode === "connections") {
      const { depths } = connectionDepthsFor(activeNodes);
      const byDepth = new Map();
      activeNodes.forEach((node) => {
        const depth = depths.get(node.id) || 0;
        if (!byDepth.has(depth)) byDepth.set(depth, []);
        byDepth.get(depth).push(node);
      });
      const orderedDepths = Array.from(byDepth.keys()).sort((a, b) => a - b);
      const sidePadding = 64;
      const availableWidth = Math.max(1, width - sidePadding * 2);
      const columnGap = orderedDepths.length <= 1
        ? 0
        : availableWidth / (orderedDepths.length - 1);
      orderedDepths.forEach((depth, depthIndex) => {
        const columnNodes = (byDepth.get(depth) || []).slice().sort(compareNodesByOrder);
        const topPadding = 76;
        const bottomPadding = 76;
        const availableHeight = Math.max(1, height - topPadding - bottomPadding);
        const rowGap = columnNodes.length <= 1
          ? 0
          : availableHeight / (columnNodes.length - 1);
        columnNodes.forEach((node, nodeIndex) => {
          positions.set(node.id, {
            x: orderedDepths.length <= 1
              ? width / 2
              : sidePadding + depthIndex * columnGap,
            y: columnNodes.length <= 1
              ? height / 2
              : topPadding + nodeIndex * rowGap,
          });
        });
      });
      return { width, height, positions };
    }
    if (mode === "cluster") {
      const centerX = width / 2;
      const centerY = height / 2;
      const sidePadding = 92;
      const topPadding = 88;
      const availableWidth = Math.max(1, width - sidePadding * 2);
      const availableHeight = Math.max(1, height - topPadding * 2);
      const centerRingRadius = Math.min(availableWidth, availableHeight) * 0.38;
      const groupIds = sortedGroupIdsFor(activeNodes);
      const nodesByGroup = new Map(groupIds.map((groupId) => [groupId, []]));
      activeNodes.forEach((node) => {
        const groupId = node.group || "";
        if (!nodesByGroup.has(groupId)) nodesByGroup.set(groupId, []);
        nodesByGroup.get(groupId).push(node);
      });
      groupIds.forEach((groupId, groupIndex) => {
        const angle = groupIds.length <= 1
          ? -Math.PI / 2
          : (Math.PI * 2 * groupIndex) / groupIds.length - Math.PI / 2;
        const groupCenter = {
          x: groupIds.length <= 1 ? centerX : centerX + Math.cos(angle) * centerRingRadius,
          y: groupIds.length <= 1 ? centerY : centerY + Math.sin(angle) * centerRingRadius,
        };
        const groupNodes = (nodesByGroup.get(groupId) || []).slice().sort(compareNodesByOrder);
        const maxRadiusX = Math.max(0, Math.min(groupCenter.x - 44, width - groupCenter.x - 44));
        const maxRadiusY = Math.max(0, Math.min(groupCenter.y - 44, height - groupCenter.y - 44));
        const clusterRingRadius = groupNodes.length <= 1
          ? 0
          : Math.min(42, Math.max(22, Math.min(maxRadiusX, maxRadiusY)));
        groupNodes.forEach((node, nodeIndex) => {
          if (clusterRingRadius === 0) {
            positions.set(node.id, groupCenter);
            return;
          }
          const nodeAngle = (Math.PI * 2 * nodeIndex) / groupNodes.length - Math.PI / 2;
          positions.set(node.id, {
            x: groupCenter.x + Math.cos(nodeAngle) * clusterRingRadius,
            y: groupCenter.y + Math.sin(nodeAngle) * clusterRingRadius,
          });
        });
      });
      return { width, height, positions };
    }
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
    const node = nodesById.get(nodeId);
    if (node && node.link_counts) {
      return {
        outgoingCount: Number(node.link_counts.outgoing || 0),
        incomingCount: Number(node.link_counts.incoming || 0),
        connectedCount: Number(node.link_counts.connected || 0),
      };
    }
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

  function degreeFor(nodeId) {
    return edges.reduce((count, edge) => {
      return count + (edge.from === nodeId ? 1 : 0) + (edge.to === nodeId ? 1 : 0);
    }, 0);
  }

  function degreeRadiusFor(nodeId, selected) {
    if (selected) return 19;
    return 14 + Math.min(8, Math.sqrt(degreeFor(nodeId)) * 2);
  }

  function viewBoxString(box) {
    return `${box.x} ${box.y} ${box.width} ${box.height}`;
  }

  function setGraphViewBox(box) {
    graphViewBox = box;
    if (canvas && box) canvas.setAttribute("viewBox", viewBoxString(box));
  }

  function resetGraphView() {
    if (!fullViewBox) return;
    setGraphViewBox({ ...fullViewBox });
  }

  function setGraphViewportControlsEnabled(enabled) {
    [zoomIn, zoomOut, resetView, ...panButtons].forEach((button) => {
      if (button) button.disabled = !enabled;
    });
  }

  function focusablePanelElements(body) {
    if (!body) return [];
    return Array.from(body.querySelectorAll(
      "a[href], button, input, select, textarea, summary, [tabindex]"
    ));
  }

  function setPanelFocusable(body, enabled) {
    focusablePanelElements(body).forEach((element) => {
      if (!enabled) {
        if (!element.hasAttribute("data-raya-graph-original-tabindex")) {
          element.setAttribute(
            "data-raya-graph-original-tabindex",
            element.hasAttribute("tabindex") ? element.getAttribute("tabindex") : ""
          );
        }
        element.setAttribute("tabindex", "-1");
        return;
      }
      const original = element.getAttribute("data-raya-graph-original-tabindex");
      if (original === null) return;
      if (original === "") {
        element.removeAttribute("tabindex");
      } else {
        element.setAttribute("tabindex", original);
      }
      element.removeAttribute("data-raya-graph-original-tabindex");
    });
  }

  function graphPanelBody(panelName) {
    return document.querySelector(`[data-raya-graph-panel-body="${panelName}"]`);
  }

  function graphPanelLabel(panelName) {
    return panelName === "inspector" ? "inspector" : "list";
  }

  function setGraphPanelState(panelName, expanded) {
    const label = graphPanelLabel(panelName);
    const state = expanded ? "expanded" : "collapsed";
    const attr = panelName === "inspector"
      ? "data-raya-graph-inspector-state"
      : "data-raya-graph-list-state";
    root.setAttribute(attr, state);
    root.dataset[panelName === "inspector" ? "rayaGraphInspectorState" : "rayaGraphListState"] = state;
    const body = graphPanelBody(panelName);
    if (body) {
      body.setAttribute("aria-hidden", expanded ? "false" : "true");
      setPanelFocusable(body, expanded);
    }
    panelToggles
      .filter((button) => button.getAttribute("data-raya-graph-toggle-panel") === panelName)
      .forEach((button) => {
        button.setAttribute("aria-expanded", expanded ? "true" : "false");
        button.textContent = `${expanded ? "Collapse" : "Expand"} ${label}`;
      });
  }

  function zoomGraphView(factor) {
    if (!graphViewBox || !fullViewBox || root.getAttribute("data-raya-graph-layout") === "list") {
      return;
    }
    const minWidth = fullViewBox.width * 0.32;
    const maxWidth = fullViewBox.width * 1.75;
    const minHeight = fullViewBox.height * 0.32;
    const maxHeight = fullViewBox.height * 1.75;
    const nextWidth = Math.max(minWidth, Math.min(maxWidth, graphViewBox.width * factor));
    const nextHeight = Math.max(minHeight, Math.min(maxHeight, graphViewBox.height * factor));
    const centerX = graphViewBox.x + graphViewBox.width / 2;
    const centerY = graphViewBox.y + graphViewBox.height / 2;
    setGraphViewBox({
      x: centerX - nextWidth / 2,
      y: centerY - nextHeight / 2,
      width: nextWidth,
      height: nextHeight,
    });
  }

  function panGraphView(dxRatio, dyRatio) {
    if (!graphViewBox || !fullViewBox || root.getAttribute("data-raya-graph-layout") === "list") {
      return;
    }
    setGraphViewBox({
      x: graphViewBox.x + graphViewBox.width * dxRatio,
      y: graphViewBox.y + graphViewBox.height * dyRatio,
      width: graphViewBox.width,
      height: graphViewBox.height,
    });
  }

  function startGraphPan(event) {
    if (
      graphPanStart ||
      !graphViewBox ||
      event.button !== 0 ||
      root.getAttribute("data-raya-graph-layout") === "list"
    ) {
      return;
    }
    if (event.target.closest && event.target.closest("[data-raya-graph-node]")) {
      return;
    }
    const rect = canvas.getBoundingClientRect();
    graphPanStart = {
      pointerId: event.pointerId ?? "mouse",
      clientX: event.clientX,
      clientY: event.clientY,
      rectWidth: Math.max(1, rect.width),
      rectHeight: Math.max(1, rect.height),
      box: { ...graphViewBox },
    };
    if (event.pointerId !== undefined && canvas.setPointerCapture) {
      canvas.setPointerCapture(event.pointerId);
    }
    canvas.classList.add("is-panning");
  }

  function moveGraphPan(event) {
    const pointerId = event.pointerId ?? "mouse";
    if (!graphPanStart || graphPanStart.pointerId !== pointerId) return;
    const dx = ((event.clientX - graphPanStart.clientX) / graphPanStart.rectWidth) * graphPanStart.box.width;
    const dy = ((event.clientY - graphPanStart.clientY) / graphPanStart.rectHeight) * graphPanStart.box.height;
    setGraphViewBox({
      x: graphPanStart.box.x - dx,
      y: graphPanStart.box.y - dy,
      width: graphPanStart.box.width,
      height: graphPanStart.box.height,
    });
  }

  function endGraphPan(event) {
    const pointerId = event.pointerId ?? "mouse";
    if (!graphPanStart || graphPanStart.pointerId !== pointerId) return;
    graphPanStart = null;
    canvas.classList.remove("is-panning");
    if (event.pointerId !== undefined && canvas.releasePointerCapture) {
      try {
        canvas.releasePointerCapture(event.pointerId);
      } catch {
        // Pointer capture may already be released by the browser.
      }
    }
  }

  function inspectionTextFor(nodeId) {
    const node = nodesById.get(nodeId);
    if (!node) return "";
    const group = groupsById.get(node.group || "");
    const counts = relationshipCountsFor(nodeId);
    return `Inspecting ${node.title || node.nav_title || node.id}: ${group ? group.title : "Course"}; ${counts.outgoingCount} outgoing link(s), ${counts.incomingCount} incoming link(s), ${counts.connectedCount} connected page(s).`;
  }

  function updateInspectionDom() {
    const inspectedConnectedIds = inspectedId ? connectedNodeIds(inspectedId) : new Set();
    const inspectedSpotlightIds = inspectedId
      ? new Set([inspectedId, ...inspectedConnectedIds])
      : new Set();
    const searchSpotlight = searchSpotlightIds();
    const searchContext = searchContextNodeIds();
    canvas.querySelectorAll("[data-raya-graph-node] g").forEach((nodeGroup) => {
      const link = nodeGroup.closest("[data-raya-graph-node]");
      const id = link ? link.getAttribute("data-raya-graph-node") || "" : "";
      nodeGroup.classList.toggle("is-inspected", id === inspectedId);
      nodeGroup.classList.toggle("is-inspected-neighbor", inspectedConnectedIds.has(id));
      nodeGroup.classList.toggle(
        "is-search-context",
        searchContext.has(id) && id !== inspectedId
      );
      nodeGroup.classList.toggle(
        "is-search-dimmed",
        Boolean(query) && !searchSpotlight.has(id) && id !== inspectedId
      );
      nodeGroup.classList.toggle(
        "is-dimmed",
        Boolean(inspectedId) && !inspectedSpotlightIds.has(id)
      );
    });
    canvas.querySelectorAll(".raya-graph-edge").forEach((edge) => {
      const from = edge.getAttribute("data-raya-graph-from") || "";
      const to = edge.getAttribute("data-raya-graph-to") || "";
      edge.classList.toggle(
        "is-inspected",
        Boolean(inspectedId) && (from === inspectedId || to === inspectedId)
      );
      edge.classList.toggle(
        "is-dimmed",
        Boolean(inspectedId) && !(from === inspectedId || to === inspectedId)
      );
      edge.classList.toggle(
        "is-search-context",
        Boolean(query) && (matchIds.has(from) || matchIds.has(to))
      );
      edge.classList.toggle(
        "is-search-dimmed",
        Boolean(query) &&
          !(matchIds.has(from) || matchIds.has(to)) &&
          !(from === inspectedId || to === inspectedId)
      );
    });
    list.querySelectorAll("[data-raya-graph-node]").forEach((item) => {
      const id = item.getAttribute("data-raya-graph-node") || "";
      item.classList.toggle("is-inspected", id === inspectedId);
      item.classList.toggle("is-inspected-neighbor", inspectedConnectedIds.has(id));
    });
  }

  function inspectGraphNode(nodeId) {
    inspectedId = nodesById.has(nodeId) ? nodeId : "";
    if (hoverStatus) hoverStatus.textContent = inspectedId ? inspectionTextFor(inspectedId) : "";
    updateInspectionDom();
  }

  function focusedInspectionNodeId() {
    const active = document.activeElement;
    if (!active || typeof active.closest !== "function") return "";
    const item = active.closest("[data-raya-graph-node]");
    if (!item || item.hidden) return "";
    return item.getAttribute("data-raya-graph-node") || "";
  }

  function currentVisibleListIds() {
    return Array.from(list.querySelectorAll("[data-raya-graph-node]"))
      .filter((item) => !item.hidden)
      .map((item) => item.getAttribute("data-raya-graph-node") || "")
      .filter(Boolean);
  }

  function currentActiveResultIds() {
    const visibleIds = currentVisibleListIds();
    if (!query) return visibleIds;
    return visibleIds.filter((id) => matchIds.has(id));
  }

  function activeResultUrl() {
    if (!activeResultId) return "";
    const item = Array.from(list.querySelectorAll("[data-raya-graph-node]"))
      .find((candidate) => (
        !candidate.hidden &&
        candidate.getAttribute("data-raya-graph-node") === activeResultId
      ));
    const link = item ? item.querySelector("a") : null;
    return link ? link.href : "";
  }

  function setActiveResult(nodeId, options = {}) {
    const visibleIds = currentActiveResultIds();
    activeResultId = visibleIds.includes(nodeId) ? nodeId : "";
    list.querySelectorAll("[data-raya-graph-node]").forEach((item) => {
      const id = item.getAttribute("data-raya-graph-node") || "";
      const active = id === activeResultId;
      item.classList.toggle("is-active-result", active);
      const link = item.querySelector("a");
      if (link) {
        if (active) {
          link.setAttribute("aria-current", "true");
        } else {
          link.removeAttribute("aria-current");
        }
      }
      if (active && options.scroll !== false) {
        item.scrollIntoView({ block: "nearest" });
      }
    });
    if (activeResultId) {
      selectedId = activeResultId;
      inspectedId = activeResultId;
      renderDetail();
      updateInspectionDom();
    } else {
      clearGraphInspection();
    }
  }

  function moveActiveResult(delta) {
    const visibleIds = currentActiveResultIds();
    if (visibleIds.length === 0) {
      setActiveResult("");
      return;
    }
    const currentIndex = activeResultId ? visibleIds.indexOf(activeResultId) : -1;
    const baseIndex = currentIndex >= 0 ? currentIndex : (delta > 0 ? -1 : 0);
    const nextIndex = (baseIndex + delta + visibleIds.length) % visibleIds.length;
    setActiveResult(visibleIds[nextIndex]);
  }

  function clearGraphInspection(nodeId) {
    const applyClear = () => {
      const focusedNodeId = focusedInspectionNodeId();
      if (focusedNodeId) {
        inspectGraphNode(focusedNodeId);
        return;
      }
      if (nodeId && inspectedId !== nodeId) return;
      if (activeResultId && query && nodesById.has(activeResultId)) {
        inspectedId = activeResultId;
        if (hoverStatus) hoverStatus.textContent = inspectionTextFor(inspectedId);
        updateInspectionDom();
        return;
      }
      inspectedId = "";
      if (hoverStatus) hoverStatus.textContent = "";
      updateInspectionDom();
    };
    if (nodeId) {
      window.setTimeout(applyClear, 0);
    } else {
      applyClear();
    }
  }

  function edgeLabel(edge) {
    const kind = edge && edge.kind ? edge.kind : "link";
    return kind.replace(/-/g, " ");
  }

  function focusGraphDetailNode(nodeId) {
    if (!nodesById.has(nodeId)) return;
    graphViewBox = null;
    selectGraphNode(nodeId);
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
      if (nodesById.has(item.id)) {
        const focus = document.createElement("button");
        focus.type = "button";
        focus.className = "raya-graph-detail-focus-node";
        focus.setAttribute("data-raya-graph-focus-node", item.id);
        focus.textContent = "Focus";
        focus.addEventListener("click", () => focusGraphDetailNode(item.id));
        li.appendChild(focus);
      }
      listEl.appendChild(li);
    });
  }

  function studyCountsText(counts) {
    if (!counts || typeof counts !== "object") return "";
    return Object.keys(counts).sort().map((key) => {
      const value = counts[key];
      const label = value === 1 ? key : `${key}s`;
      return `${label.charAt(0).toUpperCase()}${label.slice(1)}: ${value}`;
    }).join(", ");
  }

  function setGraphNeighborhoodFocus(enabled) {
    neighborhoodFocus = Boolean(enabled && selectedId);
    root.setAttribute(
      "data-raya-graph-neighborhood-focus",
      neighborhoodFocus ? "true" : "false"
    );
    if (focusNeighborhood) {
      focusNeighborhood.hidden = !selectedId;
      focusNeighborhood.textContent = neighborhoodFocus
        ? "Show full graph"
        : "Focus neighborhood";
      focusNeighborhood.setAttribute("aria-pressed", neighborhoodFocus ? "true" : "false");
    }
  }

  function renderDetail() {
    const node = selectedId ? nodesById.get(selectedId) : null;
    if (!node) {
      setGraphNeighborhoodFocus(false);
      if (detailEmpty) detailEmpty.hidden = false;
      if (detailPanel) detailPanel.hidden = true;
      if (detailSummary) detailSummary.textContent = "";
      if (detailStudyCounts) detailStudyCounts.textContent = "";
      if (detailNeighborhood) detailNeighborhood.textContent = "";
      return;
    }
    const group = groupsById.get(node.group || "");
    if (detailEmpty) detailEmpty.hidden = true;
    if (detailPanel) detailPanel.hidden = false;
    setGraphNeighborhoodFocus(neighborhoodFocus);
    if (detailTitle) detailTitle.textContent = node.title || node.nav_title || node.id;
    if (detailSummary) detailSummary.textContent = node.summary || "";
    if (detailMeta) {
      detailMeta.textContent = [
        `Stable ID: ${node.stable_id || node.id}`,
        group ? `Group: ${group.title}` : "Group: Course",
        node.hierarchy_label ? `Hierarchy: ${node.hierarchy_label}` : "",
        node.status ? `Status: ${node.status}` : "",
        Array.isArray(node.tags) && node.tags.length ? `Tags: ${node.tags.join(", ")}` : "",
      ].filter(Boolean).join("; ");
    }
    if (detailStudyCounts) {
      const countsText = studyCountsText(node.study_counts);
      detailStudyCounts.textContent = countsText ? `Official objects: ${countsText}` : "";
    }
    if (detailNeighborhood) {
      const counts = relationshipCountsFor(node.id);
      detailNeighborhood.textContent = `Explicit links: ${counts.outgoingCount} outgoing, ${counts.incomingCount} incoming, ${counts.connectedCount} connected.`;
    }
    if (detailLink) {
      detailLink.href = node.url;
      detailLink.textContent = "Open page";
    }
    if (detailSearchLink) {
      detailSearchLink.href = node.search_url || "../search/index.html";
      detailSearchLink.textContent = "Find in search";
    }
    if (detailPracticeLink) {
      if (node.practice_url) {
        detailPracticeLink.href = node.practice_url;
        detailPracticeLink.hidden = false;
      } else {
        detailPracticeLink.href = "../practice/index.html";
        detailPracticeLink.hidden = true;
      }
      detailPracticeLink.textContent = "Open practice";
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
    neighborhoodFocus = false;
    selectedId = nodeId;
    renderDetail();
    render();
  }

  function clearGraphSelection() {
    window.clearTimeout(pendingSelectTimer);
    pendingSelectTimer = 0;
    selectedId = "";
    inspectedId = "";
    activeResultId = "";
    if (hoverStatus) hoverStatus.textContent = "";
    setGraphNeighborhoodFocus(false);
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
    const inspectedConnectedIds = inspectedId ? connectedNodeIds(inspectedId) : new Set();
    list.querySelectorAll("[data-raya-graph-node]").forEach((item) => {
      const id = item.getAttribute("data-raya-graph-node") || "";
      item.hidden = !activeIds.has(id);
      item.classList.toggle("is-active", id === selectedId);
      item.classList.toggle("is-active-result", id === activeResultId);
      item.classList.toggle("is-neighbor", connectedIds.has(id));
      item.classList.toggle("is-inspected", id === inspectedId);
      item.classList.toggle("is-inspected-neighbor", inspectedConnectedIds.has(id));
      item.classList.toggle("is-match", matchIds.has(id));
      const link = item.querySelector("a");
      if (link) {
        if (id === activeResultId && activeIds.has(id)) {
          link.setAttribute("aria-current", "true");
        } else {
          link.removeAttribute("aria-current");
        }
      }
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
    let listNodes = visibleListNodes();
    let listIds = new Set(listNodes.map((node) => node.id));
    if (selectedId && !listIds.has(selectedId)) {
      selectedId = "";
      renderDetail();
      listNodes = visibleListNodes();
      listIds = new Set(listNodes.map((node) => node.id));
    }
    const activeNodes = visibleGraphNodes(listNodes);
    const activeIds = new Set(activeNodes.map((node) => node.id));
    const activeEdges = visibleEdges(activeIds);
    const listEdges = visibleEdges(listIds);
    if (activeResultId && !listIds.has(activeResultId)) {
      activeResultId = "";
    }
    renderList(listIds);
    if (status) {
      const statusPrefix = neighborhoodFocus ? "Neighborhood focus: " : "";
      if (query) {
        const contextCount = Math.max(0, listNodes.length - matchIds.size);
        status.textContent = `${statusPrefix}${matchIds.size} match(es), ${contextCount} connected page(s) shown; ${activeNodes.length} visible node(s) in graph, ${activeEdges.length} visible edge(s) in graph.`;
      } else {
        status.textContent = `${statusPrefix}${activeNodes.length} visible node(s), ${listEdges.length} visible edge(s).`;
      }
    }
    if (mode === "list") {
      canvas.setAttribute("hidden", "hidden");
      canvas.replaceChildren();
      fullViewBox = null;
      graphViewBox = null;
      setGraphViewportControlsEnabled(false);
      if (activeResultId) setActiveResult(activeResultId, { scroll: false });
      return;
    }
    canvas.removeAttribute("hidden");
    const connectedIds = selectedId ? connectedNodeIds(selectedId) : new Set();
    const selectedCluster = selectedId ? new Set([selectedId, ...connectedIds]) : new Set();
    const inspectedConnectedIds = inspectedId ? connectedNodeIds(inspectedId) : new Set();
    const inspectedSpotlightIds = inspectedId
      ? new Set([inspectedId, ...inspectedConnectedIds])
      : new Set();
    const searchSpotlight = searchSpotlightIds();
    const searchContext = searchContextNodeIds();
    const geometry = positionsFor(activeNodes, mode);

    fullViewBox = { x: 0, y: 0, width: geometry.width, height: geometry.height };
    if (!graphViewBox) {
      setGraphViewBox({ ...fullViewBox });
    } else {
      canvas.setAttribute("viewBox", viewBoxString(graphViewBox));
    }
    setGraphViewportControlsEnabled(true);
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
      line.setAttribute("data-raya-graph-from", edge.from);
      line.setAttribute("data-raya-graph-to", edge.to);
      line.style.setProperty("--raya-graph-edge-color", edgeColorFor(edge));
      line.setAttribute(
        "class",
        [
          "raya-graph-edge",
          selectedId && (edge.from === selectedId || edge.to === selectedId) ? "is-active" : "",
          inspectedId && (edge.from === inspectedId || edge.to === inspectedId)
            ? "is-inspected"
            : "",
          inspectedId && !(edge.from === inspectedId || edge.to === inspectedId)
            ? "is-dimmed"
            : "",
          query && (matchIds.has(edge.from) || matchIds.has(edge.to))
            ? "is-search-context"
            : "",
          query && !(matchIds.has(edge.from) || matchIds.has(edge.to))
            && !(edge.from === inspectedId || edge.to === inspectedId)
            ? "is-search-dimmed"
            : "",
        ].filter(Boolean).join(" ")
      );
      canvas.appendChild(line);
    });

    activeNodes.forEach((node) => {
      const point = geometry.positions.get(node.id);
      if (!point) return;
      const link = document.createElementNS("http://www.w3.org/2000/svg", "a");
      link.setAttribute("href", node.url);
      link.setAttribute("class", "raya-graph-node-link");
      link.setAttribute("aria-label", inspectionTextFor(node.id));
      link.dataset.rayaGraphNode = node.id;
      const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const active = !selectedId || selectedCluster.has(node.id);
      const isConnected = connectedIds.has(node.id);
      const isInspected = node.id === inspectedId;
      const isInspectedNeighbor = inspectedConnectedIds.has(node.id);
      group.setAttribute(
        "class",
        [
          "raya-graph-node",
          active ? "" : "is-muted",
          node.id === selectedId ? "is-selected" : "",
          isConnected ? "is-neighbor" : "",
          isInspected ? "is-inspected" : "",
          isInspectedNeighbor ? "is-inspected-neighbor" : "",
          inspectedId && !inspectedSpotlightIds.has(node.id) ? "is-dimmed" : "",
          matchIds.has(node.id) ? "is-match" : "",
          searchContext.has(node.id) && node.id !== inspectedId ? "is-search-context" : "",
          query && !searchSpotlight.has(node.id) && node.id !== inspectedId ? "is-search-dimmed" : "",
        ].filter(Boolean).join(" ")
      );
      group.setAttribute("transform", `translate(${point.x} ${point.y})`);
      group.style.setProperty(
        "--raya-graph-node-color",
        `var(--raya-graph-group-${groupColorIndex(node.group || "")})`
      );
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      const radius = degreeRadiusFor(node.id, node.id === selectedId);
      const hitTarget = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      hitTarget.setAttribute("class", "raya-graph-node-hit");
      hitTarget.setAttribute("r", String(Math.max(30, radius + 8)));
      circle.setAttribute("r", String(radius));
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("y", String(radius + 20));
      text.textContent = node.nav_title || node.title || node.id;
      group.append(hitTarget, circle, text);
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
      link.addEventListener("mouseenter", () => inspectGraphNode(node.id));
      link.addEventListener("mouseleave", () => clearGraphInspection(node.id));
      link.addEventListener("focus", () => inspectGraphNode(node.id));
      link.addEventListener("blur", () => clearGraphInspection(node.id));
      canvas.appendChild(link);
    });
    updateInspectionDom();
    if (activeResultId) setActiveResult(activeResultId, { scroll: false });
  }

  if (search) {
    search.addEventListener("input", () => {
      const previousActiveResultId = activeResultId;
      let clearedActiveSelection = false;
      if (previousActiveResultId && selectedId === previousActiveResultId) {
        selectedId = "";
        clearedActiveSelection = true;
      }
      if (previousActiveResultId && inspectedId === previousActiveResultId) {
        inspectedId = "";
      }
      activeResultId = "";
      graphViewBox = null;
      if (clearedActiveSelection) {
        renderDetail();
      }
      render();
      const visibleIds = currentActiveResultIds();
      if (query && visibleIds.length > 0) {
        setActiveResult(visibleIds[0], { scroll: false });
      }
    });
    search.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        moveActiveResult(1);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        moveActiveResult(-1);
      } else if (event.key === "Enter") {
        const href = activeResultUrl();
        if (href) {
          event.preventDefault();
          window.location.href = href;
        }
      }
    });
  }
  if (layout) {
    layout.addEventListener("change", () => {
      graphViewBox = null;
      render();
    });
  }
  if (fit) {
    fit.addEventListener("click", () => {
      graphViewBox = null;
      render();
    });
  }
  if (zoomIn) zoomIn.addEventListener("click", () => zoomGraphView(0.82));
  if (zoomOut) zoomOut.addEventListener("click", () => zoomGraphView(1.22));
  if (resetView) resetView.addEventListener("click", resetGraphView);
  panButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const direction = button.getAttribute("data-raya-graph-pan") || "";
      if (direction === "left") panGraphView(-0.16, 0);
      if (direction === "right") panGraphView(0.16, 0);
      if (direction === "up") panGraphView(0, -0.16);
      if (direction === "down") panGraphView(0, 0.16);
    });
  });
  canvas.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      panGraphView(-0.12, 0);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      panGraphView(0.12, 0);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      panGraphView(0, -0.12);
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      panGraphView(0, 0.12);
    }
  });
  canvas.addEventListener("pointerdown", startGraphPan);
  canvas.addEventListener("pointermove", moveGraphPan);
  canvas.addEventListener("pointerup", endGraphPan);
  canvas.addEventListener("pointercancel", endGraphPan);
  canvas.addEventListener("mousedown", startGraphPan);
  canvas.addEventListener("mousemove", moveGraphPan);
  canvas.addEventListener("mouseup", endGraphPan);
  canvas.addEventListener("mouseleave", endGraphPan);
  if (reset) {
    reset.addEventListener("click", () => {
      if (search) search.value = "";
      if (layout) layout.value = "connections";
      hiddenGroups.clear();
      selectedId = "";
      inspectedId = "";
      activeResultId = "";
      setGraphNeighborhoodFocus(false);
      graphViewBox = null;
      if (hoverStatus) hoverStatus.textContent = "";
      setGraphExpanded(false);
      setGraphPanelState("list", true);
      setGraphPanelState("inspector", true);
      renderDetail();
      groupFilters.forEach((button) => {
        button.setAttribute("aria-pressed", "true");
      });
      render();
    });
  }
  if (graphExpand) {
    graphExpand.addEventListener("click", () => {
      const nextExpanded = root.dataset.rayaGraphExpanded !== "true";
      setGraphExpanded(nextExpanded);
      setGraphPanelState("list", !nextExpanded);
      render();
    });
  }
  panelToggles.forEach((button) => {
    button.addEventListener("click", () => {
      const panelName = button.getAttribute("data-raya-graph-toggle-panel") || "";
      if (!panelName) return;
      const attr = panelName === "inspector"
        ? "data-raya-graph-inspector-state"
        : "data-raya-graph-list-state";
      setGraphPanelState(panelName, root.getAttribute(attr) === "collapsed");
    });
  });
  if (detailClear) {
    detailClear.addEventListener("click", clearGraphSelection);
  }
  if (focusNeighborhood) {
    focusNeighborhood.addEventListener("click", () => {
      setGraphNeighborhoodFocus(!neighborhoodFocus);
      graphViewBox = null;
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
      if (activeResultId && hiddenGroups.has(nodesById.get(activeResultId)?.group || "")) {
        activeResultId = "";
      }
      graphViewBox = null;
      render();
    });
  });
  list.addEventListener("focusin", (event) => {
    const item = event.target.closest("[data-raya-graph-node]");
    if (!item || item.hidden) return;
    inspectGraphNode(item.getAttribute("data-raya-graph-node") || "");
  });
  list.addEventListener("focusout", (event) => {
    const item = event.target.closest("[data-raya-graph-node]");
    clearGraphInspection(item ? item.getAttribute("data-raya-graph-node") || "" : "");
  });
  list.addEventListener("pointerover", (event) => {
    const item = event.target.closest("[data-raya-graph-node]");
    if (!item || item.hidden) return;
    inspectGraphNode(item.getAttribute("data-raya-graph-node") || "");
  });
  list.addEventListener("pointerout", (event) => {
    if (!list.contains(event.relatedTarget)) {
      clearGraphInspection();
    }
  });
  list.querySelectorAll("[data-raya-graph-node] a").forEach((link) => {
    link.addEventListener("focus", () => {
      const item = link.closest("[data-raya-graph-node]");
      if (!item || item.hidden) return;
      inspectGraphNode(item.getAttribute("data-raya-graph-node") || "");
    });
    link.addEventListener("blur", () => {
      const item = link.closest("[data-raya-graph-node]");
      clearGraphInspection(item ? item.getAttribute("data-raya-graph-node") || "" : "");
    });
  });
  canvas.addEventListener("mouseleave", () => {
    if (!detailPanel || detailPanel.hidden) {
      selectedId = "";
    }
    clearGraphInspection(inspectedId);
    render();
  });

  selectedId = initialPageFocus();
  root.setAttribute("data-raya-graph-neighborhood-focus", "false");
  setGraphPanelState("list", true);
  setGraphPanelState("inspector", true);
  setGraphExpanded(false);
  renderDetail();
  render();
})();
"""
