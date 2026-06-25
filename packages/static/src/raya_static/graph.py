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
  const fitSelection = document.getElementById("graph-fit-selection");
  const zoomIn = document.getElementById("graph-zoom-in");
  const zoomOut = document.getElementById("graph-zoom-out");
  const resetView = document.getElementById("graph-reset-view");
  const panButtons = Array.from(document.querySelectorAll("[data-raya-graph-pan]"));
  const reset = document.getElementById("graph-reset");
  const graphExpand = document.getElementById("graph-expand");
  const panelToggles = Array.from(document.querySelectorAll("[data-raya-graph-toggle-panel]"));
  const status = document.getElementById("graph-status");
  const hoverStatus = document.querySelector("[data-raya-graph-hover-status]");
  const inspectionPreview = document.querySelector("[data-raya-graph-inspection-preview]");
  const inspectionPreviewTitle = document.querySelector(
    "[data-raya-graph-inspection-preview-title]"
  );
  const inspectionPreviewMeta = document.querySelector(
    "[data-raya-graph-inspection-preview-meta]"
  );
  const inspectionPreviewSummary = document.querySelector(
    "[data-raya-graph-inspection-preview-summary]"
  );
  const inspectionPreviewCounts = document.querySelector(
    "[data-raya-graph-inspection-preview-counts]"
  );
  const inspectionPreviewSelect = document.querySelector(
    "[data-raya-graph-inspection-preview-select]"
  );
  const inspectionPreviewOpen = document.querySelector(
    "[data-raya-graph-inspection-preview-open]"
  );
  const groupFilters = Array.from(document.querySelectorAll("[data-raya-graph-group-filter]"));
  const edgeKindFilters = Array.from(
    document.querySelectorAll("[data-raya-graph-edge-kind-filter]")
  );
  const detailEmpty = document.querySelector("[data-raya-graph-detail-empty]");
  const detailPanel = document.querySelector("[data-raya-graph-detail-panel]");
  const detailTitle = document.querySelector("[data-raya-graph-detail-title]");
  const detailSummary = document.querySelector("[data-raya-graph-detail-summary]");
  const detailMeta = document.querySelector("[data-raya-graph-detail-meta]");
  const detailStudyCounts = document.querySelector("[data-raya-graph-detail-study-counts]");
  const detailStudyObjects = document.querySelector("[data-raya-graph-detail-study-objects]");
  const detailStudyObjectList = document.querySelector(
    "[data-raya-graph-detail-study-object-list]"
  );
  const detailNeighborhood = document.querySelector("[data-raya-graph-detail-neighborhood]");
  const detailRelationshipChips = document.querySelector(
    "[data-raya-graph-detail-relationship-chips]"
  );
  const detailRelationshipChipList = document.querySelector(
    "[data-raya-graph-detail-relationship-chip-list]"
  );
  const relationshipWalkthrough = document.querySelector(
    "[data-raya-graph-relationship-walkthrough]"
  );
  const relationshipWalkthroughList = document.querySelector(
    "[data-raya-graph-relationship-walkthrough-list]"
  );
  const relationshipFocusStatus = document.querySelector(
    "[data-raya-graph-relationship-focus-status]"
  );
  const detailLink = document.querySelector("[data-raya-graph-detail-link]");
  const detailSearchLink = document.querySelector("[data-raya-graph-detail-search-link]");
  const detailPracticeLink = document.querySelector("[data-raya-graph-detail-practice-link]");
  const detailTasksLink = document.querySelector("[data-raya-graph-detail-tasks-link]");
  const detailScheduleLink = document.querySelector("[data-raya-graph-detail-schedule-link]");
  const detailPreviousLink = document.querySelector("[data-raya-graph-detail-previous]");
  const detailCurrentLink = document.querySelector("[data-raya-graph-detail-current]");
  const detailNextLink = document.querySelector("[data-raya-graph-detail-next]");
  const focusNeighborhood = document.querySelector("[data-raya-graph-focus-neighborhood]");
  const detailOutgoing = document.querySelector("[data-raya-graph-detail-outgoing]");
  const detailIncoming = document.querySelector("[data-raya-graph-detail-incoming]");
  const detailClear = document.querySelector("[data-raya-graph-detail-clear]");
  const stateSelected = document.querySelector("[data-raya-graph-state-selected]");
  const stateQuery = document.querySelector("[data-raya-graph-state-query]");
  const stateLayout = document.querySelector("[data-raya-graph-state-layout]");
  const stateVisible = document.querySelector("[data-raya-graph-state-visible]");
  const stateHiddenGroups = document.querySelector("[data-raya-graph-state-hidden-groups]");
  const stateHiddenEdges = document.querySelector("[data-raya-graph-state-hidden-edges]");
  const stateNeighborhood = document.querySelector("[data-raya-graph-state-neighborhood]");
  const statePageFocus = document.querySelector("[data-raya-graph-state-page-focus]");
  const stateUrl = document.querySelector("[data-raya-graph-state-url]");
  const copyUrl = document.querySelector("[data-raya-graph-copy-url]");
  const copyStatus = document.querySelector("[data-raya-graph-copy-status]");
  const orientation = document.querySelector("[data-raya-graph-orientation]");
  const orientationCounts = document.querySelector("[data-raya-graph-orientation-counts]");
  const orientationLayout = document.querySelector("[data-raya-graph-orientation-layout]");
  const orientationSelected = document.querySelector("[data-raya-graph-orientation-selected]");
  const orientationPageFocus = document.querySelector("[data-raya-graph-orientation-page-focus]");
  const orientationQuery = document.querySelector("[data-raya-graph-orientation-query]");
  const orientationFilters = document.querySelector("[data-raya-graph-orientation-filters]");
  const orientationNeighborhood = document.querySelector("[data-raya-graph-orientation-neighborhood]");
  const orientationOpen = document.querySelector("[data-raya-graph-orientation-open]");
  const orientationNeighborhoodToggle = document.querySelector(
    "[data-raya-graph-orientation-neighborhood-toggle]"
  );
  const orientationClear = document.querySelector("[data-raya-graph-orientation-clear]");

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
  const hiddenEdgeKinds = new Set();
  const defaultLayout = "connections";
  const graphLayouts = new Set(["connections", "topology", "cluster", "map", "radial", "list"]);
  const graphEdgeKinds = new Set(["navigation", "content", "prerequisite", "parent"]);
  let query = "";
  let selectedId = "";
  let inspectedId = "";
  let activeResultId = "";
  let pageFocusId = "";
  let activeRelationshipFocus = "";
  let pendingInitialPageFit = false;
  let neighborhoodFocus = false;
  let matchIds = new Set();
  let pendingSelectTimer = 0;
  let fullViewBox = null;
  let graphViewBox = null;
  let graphPanStart = null;
  let graphNodeDrag = null;
  let suppressedNodeClick = { id: "", until: 0 };
  let graphNodeClickSequence = { id: "", time: 0 };
  let lastActiveNodes = [];
  let lastActiveEdges = [];
  let latestRenderedPositions = new Map();
  let latestRenderedEdges = [];
  const manualNodePositions = new Map();

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
      Array.isArray(node.study_objects)
        ? node.study_objects.map((item) => [
          item.type_label,
          item.title,
          item.preview,
          item.due,
          item.available,
        ].join(" ")).join(" ")
        : "",
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

  function visibleGraphEdges(visibleIds) {
    return edges.filter((edge) => (
      visibleIds.has(edge.from) &&
      visibleIds.has(edge.to) &&
      !hiddenEdgeKinds.has(edgeKind(edge))
    ));
  }

  function updateEdgeKindFilters() {
    edgeKindFilters.forEach((button) => {
      const kind = button.getAttribute("data-raya-graph-edge-kind-filter") || "";
      button.setAttribute("aria-pressed", hiddenEdgeKinds.has(kind) ? "false" : "true");
    });
  }

  function updateGroupFilters() {
    groupFilters.forEach((button) => {
      const group = button.getAttribute("data-raya-graph-group-filter") || "";
      button.setAttribute("aria-pressed", hiddenGroups.has(group) ? "false" : "true");
    });
  }

  function currentUrlParams() {
    try {
      return new URLSearchParams(window.location.search || "");
    } catch {
      return new URLSearchParams();
    }
  }

  function parseCommaList(value, allowedIds) {
    if (!value) return null;
    const parsed = String(value)
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
      .filter((item) => allowedIds.has(item));
    return parsed.length ? new Set(parsed) : null;
  }

  function allGroupIds() {
    return new Set(groups.map((group) => group.id).filter(Boolean));
  }

  function visibleGroupIds() {
    return groups
      .map((group) => group.id)
      .filter((id) => id && !hiddenGroups.has(id));
  }

  function visibleEdgeKinds() {
    return Array.from(graphEdgeKinds).filter((kind) => !hiddenEdgeKinds.has(kind));
  }

  function applyVisibleGroupsFromUrl(value) {
    const allowedGroups = allGroupIds();
    const visibleGroups = parseCommaList(value, allowedGroups);
    if (!visibleGroups) return;
    hiddenGroups.clear();
    allowedGroups.forEach((groupId) => {
      if (!visibleGroups.has(groupId)) {
        hiddenGroups.add(groupId);
      }
    });
    updateGroupFilters();
  }

  function applyVisibleEdgeKindsFromUrl(value) {
    const visibleKinds = parseCommaList(value, graphEdgeKinds);
    if (!visibleKinds) return;
    hiddenEdgeKinds.clear();
    graphEdgeKinds.forEach((kind) => {
      if (!visibleKinds.has(kind)) {
        hiddenEdgeKinds.add(kind);
      }
    });
    updateEdgeKindFilters();
  }

  function edgeKindLabel(kind) {
    if (kind === "navigation") return "Navigation";
    if (kind === "content") return "Content";
    if (kind === "prerequisite") return "Prerequisite";
    if (kind === "parent") return "Parent";
    return kind || "Edge";
  }

  function layoutLabel(value) {
    if (value === "connections") return "Connections";
    if (value === "topology") return "Topology";
    if (value === "cluster") return "Cluster";
    if (value === "map") return "Map";
    if (value === "radial") return "Radial";
    if (value === "list") return "List";
    return value || "Connections";
  }

  function hiddenGroupText() {
    if (hiddenGroups.size === 0) return "none";
    const labels = groups
      .filter((group) => hiddenGroups.has(group.id))
      .map((group) => group.title || group.id);
    return `${hiddenGroups.size} hidden: ${labels.join(", ")}`;
  }

  function hiddenEdgeText() {
    if (hiddenEdgeKinds.size === 0) return "none";
    const labels = Array.from(hiddenEdgeKinds).map(edgeKindLabel);
    return `${hiddenEdgeKinds.size} hidden: ${labels.join(", ")}`;
  }

  function updateGraphUrlState() {
    if (!window.history || !window.history.replaceState) return;
    const params = new URLSearchParams();
    const searchValue = search ? search.value.trim() : "";
    const layoutValue = layout ? layout.value : defaultLayout;
    if (selectedId) params.set("page", selectedId);
    if (searchValue) params.set("q", searchValue);
    if (layoutValue && layoutValue !== defaultLayout) params.set("layout", layoutValue);
    if (hiddenGroups.size > 0) params.set("groups", visibleGroupIds().join(","));
    if (hiddenEdgeKinds.size > 0) params.set("edges", visibleEdgeKinds().join(","));
    if (neighborhoodFocus && selectedId) params.set("neighborhood", "1");
    if (root.dataset.rayaGraphExpanded === "true") params.set("expanded", "1");
    if (root.getAttribute("data-raya-graph-list-state") === "collapsed") {
      params.set("list", "0");
    }
    if (root.getAttribute("data-raya-graph-inspector-state") === "collapsed") {
      params.set("inspector", "0");
    }
    const queryString = params.toString();
    const nextUrl = `${window.location.pathname}${queryString ? `?${queryString}` : ""}${window.location.hash || ""}`;
    window.history.replaceState(null, "", nextUrl);
  }

  function updateGraphStateReadout(activeNodes, activeEdges) {
    if (stateSelected) stateSelected.textContent = selectedId || "none";
    if (statePageFocus) statePageFocus.textContent = pageFocusId || "none";
    if (stateQuery) stateQuery.textContent = (search ? search.value.trim() : "") || "none";
    if (stateLayout) stateLayout.textContent = layout ? layout.value : defaultLayout;
    if (stateVisible) {
      stateVisible.textContent = `${activeNodes.length} visible node(s), ${activeEdges.length} visible edge(s)`;
    }
    if (stateHiddenGroups) stateHiddenGroups.textContent = hiddenGroupText();
    if (stateHiddenEdges) stateHiddenEdges.textContent = hiddenEdgeText();
    if (stateNeighborhood) stateNeighborhood.textContent = neighborhoodFocus ? "on" : "off";
    if (stateUrl) stateUrl.textContent = window.location.href;
  }

  function syncGraphStateReadout() {
    updateGraphUrlState();
    updateGraphStateReadout(lastActiveNodes, lastActiveEdges);
  }

  function updateGraphOrientation(activeNodes, activeEdges) {
    if (!orientation) return;
    const selected = selectedId ? nodesById.get(selectedId) : null;
    const focused = pageFocusId ? nodesById.get(pageFocusId) : null;
    if (orientationCounts) {
      orientationCounts.textContent = `${activeNodes.length} visible page(s), ${activeEdges.length} visible relationship(s)`;
    }
    if (orientationLayout) {
      orientationLayout.textContent = layoutLabel(layout ? layout.value : defaultLayout);
    }
    if (orientationSelected) {
      orientationSelected.textContent = selected
        ? selected.title || selected.nav_title || selected.id
        : "None";
    }
    if (orientationPageFocus) {
      orientationPageFocus.textContent = focused
        ? focused.title || focused.nav_title || focused.id
        : "None";
    }
    if (orientationQuery) {
      orientationQuery.textContent = (search ? search.value.trim() : "") || "None";
    }
    if (orientationFilters) {
      const pieces = [];
      if (hiddenGroups.size > 0) {
        const labels = groups
          .filter((group) => hiddenGroups.has(group.id))
          .map((group) => group.title || group.id);
        pieces.push(
          `${hiddenGroups.size} hidden group(s): ${labels.join(", ")}`
        );
      }
      if (hiddenEdgeKinds.size > 0) {
        const labels = Array.from(hiddenEdgeKinds).map(edgeKindLabel);
        pieces.push(
          `${hiddenEdgeKinds.size} hidden relationship kind(s): ${labels.join(", ")}`
        );
      }
      orientationFilters.textContent = pieces.length
        ? pieces.join("; ")
        : "All groups and relationships visible";
    }
    if (orientationNeighborhood) {
      orientationNeighborhood.textContent = neighborhoodFocus ? "On" : "Off";
    }
    if (orientationOpen) {
      if (selected && selected.url) {
        orientationOpen.href = selected.url;
        orientationOpen.hidden = false;
      } else {
        orientationOpen.hidden = true;
      }
    }
    if (orientationNeighborhoodToggle) {
      orientationNeighborhoodToggle.hidden = !selected;
      orientationNeighborhoodToggle.textContent = neighborhoodFocus
        ? "Show full graph"
        : "Focus neighborhood";
      orientationNeighborhoodToggle.setAttribute(
        "aria-pressed",
        neighborhoodFocus ? "true" : "false"
      );
    }
    if (orientationClear) orientationClear.hidden = !selected;
  }

  function copyTextFallback(value) {
    const textarea = document.createElement("textarea");
    textarea.value = value;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    textarea.style.top = "0";
    document.body.appendChild(textarea);
    textarea.select();
    try {
      return document.execCommand("copy");
    } catch {
      return false;
    } finally {
      textarea.remove();
    }
  }

  function copyGraphUrl() {
    const value = window.location.href;
    if (copyStatus) copyStatus.textContent = "";
    const copied = navigator.clipboard && navigator.clipboard.writeText
      ? navigator.clipboard.writeText(value).then(() => true, () => copyTextFallback(value))
      : Promise.resolve(copyTextFallback(value));
    copied.then((ok) => {
      if (copyStatus) {
        copyStatus.textContent = ok
          ? "Copied graph URL."
          : "Copy unavailable. Select the URL above.";
      }
    });
  }

  function hiddenEdgeKindStatusText() {
    const count = hiddenEdgeKinds.size;
    if (!count) return "";
    return `${count} edge kind${count === 1 ? "" : "s"} hidden.`;
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

  function edgeKind(edge) {
    const kind = normalize(edge && edge.kind ? edge.kind : "link")
      .replace(/[^a-z0-9-]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return kind || "link";
  }

  function relationshipChipLabel(kind, direction) {
    return `${edgeKindLabel(kind)} ${direction}`;
  }

  function relationshipFocusKey(kind, direction) {
    return `${edgeKind({ kind })}:${direction}`;
  }

  function syncRelationshipFocusDom() {
    if (detailRelationshipChipList) {
      detailRelationshipChipList
        .querySelectorAll("[data-raya-graph-relationship-chip]")
        .forEach((chip) => {
          const key = relationshipFocusKey(
            chip.getAttribute("data-raya-graph-relationship-kind") || "",
            chip.getAttribute("data-raya-graph-relationship-direction") || ""
          );
          chip.setAttribute(
            "aria-pressed",
            key === activeRelationshipFocus ? "true" : "false"
          );
        });
    }
    if (relationshipWalkthroughList) {
      relationshipWalkthroughList
        .querySelectorAll("[data-raya-graph-relationship-walkthrough-card]")
        .forEach((card) => {
          const key = relationshipFocusKey(
            card.getAttribute("data-raya-graph-relationship-kind") || "",
            card.getAttribute("data-raya-graph-relationship-direction") || ""
          );
          card.hidden = Boolean(activeRelationshipFocus && key !== activeRelationshipFocus);
        });
    }
    if (!relationshipFocusStatus) {
      return;
    }
    if (!activeRelationshipFocus) {
      relationshipFocusStatus.textContent = "";
      return;
    }
    const [kind, direction] = activeRelationshipFocus.split(":");
    relationshipFocusStatus.textContent = `Showing ${relationshipChipLabel(kind, direction)} relationships.`;
  }

  function clearRelationshipFocus() {
    activeRelationshipFocus = "";
    syncRelationshipFocusDom();
  }

  function setRelationshipFocus(kind, direction) {
    const nextKey = relationshipFocusKey(kind, direction);
    activeRelationshipFocus = activeRelationshipFocus === nextKey ? "" : nextKey;
    syncRelationshipFocusDom();
  }

  function relationshipChipCountsFor(nodeId) {
    const counts = new Map();
    edges.forEach((edge) => {
      const kind = edgeKind(edge);
      if (edge.from === nodeId) {
        const key = `${kind}:out`;
        counts.set(key, {
          kind,
          direction: "out",
          count: (counts.get(key)?.count || 0) + 1,
        });
      }
      if (edge.to === nodeId) {
        const key = `${kind}:in`;
        counts.set(key, {
          kind,
          direction: "in",
          count: (counts.get(key)?.count || 0) + 1,
        });
      }
    });
    const kindOrder = ["navigation", "content", "prerequisite", "parent"];
    const directionOrder = ["out", "in"];
    return Array.from(counts.values()).sort((left, right) => {
      const leftKind = kindOrder.indexOf(left.kind);
      const rightKind = kindOrder.indexOf(right.kind);
      const kindDelta = (leftKind < 0 ? kindOrder.length : leftKind) -
        (rightKind < 0 ? kindOrder.length : rightKind);
      if (kindDelta !== 0) return kindDelta;
      const directionDelta = directionOrder.indexOf(left.direction) -
        directionOrder.indexOf(right.direction);
      if (directionDelta !== 0) return directionDelta;
      return left.kind.localeCompare(right.kind);
    });
  }

  function relationshipWalkthroughTitle(kind, direction) {
    const label = edgeKindLabel(kind);
    return `${label} ${direction === "out" ? "from" : "to"} this page`;
  }

  function relationshipWalkthroughMeaning(kind, direction) {
    if (kind === "content" && direction === "out") {
      return "Use these pages to read the selected page's explicit content links.";
    }
    if (kind === "content" && direction === "in") {
      return "These pages explicitly link back to the selected page.";
    }
    if (kind === "navigation" && direction === "out") {
      return "These pages appear after the selected page in the generated course order.";
    }
    if (kind === "navigation" && direction === "in") {
      return "This page appears after these pages in the generated course order.";
    }
    if (kind === "parent" && direction === "out") {
      return "These pages are direct structural parents of the selected page.";
    }
    if (kind === "parent" && direction === "in") {
      return "These pages sit directly below the selected page in the course structure.";
    }
    if (kind === "prerequisite" && direction === "out") {
      return "These pages are explicit prerequisites of the selected page.";
    }
    if (kind === "prerequisite" && direction === "in") {
      return "These pages explicitly depend on the selected page as prior context.";
    }
    return "These are explicit generated graph relationships from course source links or order.";
  }

  function edgeKindClass(edge) {
    return `raya-graph-edge-kind-${edgeKind(edge)}`;
  }

  function edgeOffsetFor(edge) {
    return edgeKind(edge) === "parent" ? 6 : 0;
  }

  function edgeLinePoints(edge, from, to) {
    const offset = edgeOffsetFor(edge);
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    if (!length) return { x1: from.x, y1: from.y, x2: to.x, y2: to.y };
    const unitX = dx / length;
    const unitY = dy / length;
    const fromTrim = degreeRadiusFor(edge.from, edge.from === selectedId) + 4;
    const toTrim = degreeRadiusFor(edge.to, edge.to === selectedId) + 10;
    if (length <= fromTrim + toTrim + 8) {
      return { x1: from.x, y1: from.y, x2: to.x, y2: to.y };
    }
    const normalX = -dy / length;
    const normalY = dx / length;
    const offsetX = normalX * offset;
    const offsetY = normalY * offset;
    return {
      x1: from.x + unitX * fromTrim + offsetX,
      y1: from.y + unitY * fromTrim + offsetY,
      x2: to.x - unitX * toTrim + offsetX,
      y2: to.y - unitY * toTrim + offsetY,
    };
  }

  function compareNodesByOrder(a, b) {
    const aOrder = Number(a.order || 0);
    const bOrder = Number(b.order || 0);
    const aTitle = String(a.title || a.nav_title || a.id);
    const bTitle = String(b.title || b.nav_title || b.id);
    const aId = String(a.id);
    const bId = String(b.id);
    return aOrder - bOrder ||
      (aTitle < bTitle ? -1 : aTitle > bTitle ? 1 : 0) ||
      (aId < bId ? -1 : aId > bId ? 1 : 0);
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

  function topologyEdgesFor(activeNodes, activeEdges) {
    const activeIds = new Set(activeNodes.map((node) => node.id));
    const seen = new Set();
    const topologyEdges = [];
    activeEdges.forEach((edge) => {
      if (!activeIds.has(edge.from) || !activeIds.has(edge.to)) return;
      const key = `${edge.from}\u0000${edge.to}\u0000${edgeKind(edge)}`;
      if (seen.has(key)) return;
      seen.add(key);
      topologyEdges.push(edge);
    });
    return topologyEdges;
  }

  function clampTopologyPosition(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function topologyPositionsFor(activeNodes, activeEdges) {
    const width = 960;
    const height = 560;
    const safePadding = 42;
    const centerX = width / 2;
    const centerY = height / 2;
    const orderedNodes = activeNodes.slice().sort(compareNodesByOrder);
    const positions = new Map();
    if (orderedNodes.length === 0) {
      return { width, height, positions };
    }
    if (orderedNodes.length === 1) {
      positions.set(orderedNodes[0].id, { x: centerX, y: centerY });
      return { width, height, positions };
    }

    const radius = Math.min(width - safePadding * 2, height - safePadding * 2) * 0.42;
    orderedNodes.forEach((node, index) => {
      const angle = (Math.PI * 2 * index) / orderedNodes.length - Math.PI / 2;
      positions.set(node.id, {
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
      });
    });

    const nodeIds = orderedNodes.map((node) => node.id);
    const topologyEdges = topologyEdgesFor(orderedNodes, activeEdges);
    const forces = new Map();
    const resetForces = () => {
      forces.clear();
      nodeIds.forEach((id) => forces.set(id, { x: 0, y: 0 }));
    };
    const addForce = (id, x, y) => {
      const force = forces.get(id);
      if (!force) return;
      force.x += x;
      force.y += y;
    };

    for (let iteration = 0; iteration < 70; iteration += 1) {
      resetForces();
      for (let leftIndex = 0; leftIndex < nodeIds.length; leftIndex += 1) {
        for (let rightIndex = leftIndex + 1; rightIndex < nodeIds.length; rightIndex += 1) {
          const leftId = nodeIds[leftIndex];
          const rightId = nodeIds[rightIndex];
          const left = positions.get(leftId);
          const right = positions.get(rightId);
          const dx = right.x - left.x;
          const dy = right.y - left.y;
          const distanceSquared = Math.max(64, dx * dx + dy * dy);
          const distance = Math.sqrt(distanceSquared);
          const strength = 5200 / distanceSquared;
          const fx = (dx / distance) * strength;
          const fy = (dy / distance) * strength;
          addForce(leftId, -fx, -fy);
          addForce(rightId, fx, fy);
        }
      }

      topologyEdges.forEach((edge) => {
        const from = positions.get(edge.from);
        const to = positions.get(edge.to);
        if (!from || !to) return;
        const dx = to.x - from.x;
        const dy = to.y - from.y;
        const distance = Math.max(1, Math.sqrt(dx * dx + dy * dy));
        const desired = edgeKind(edge) === "parent" ? 145 : 118;
        const strength = (distance - desired) * 0.016;
        const fx = (dx / distance) * strength;
        const fy = (dy / distance) * strength;
        addForce(edge.from, fx, fy);
        addForce(edge.to, -fx, -fy);
      });

      nodeIds.forEach((id) => {
        const position = positions.get(id);
        addForce(id, (centerX - position.x) * 0.004, (centerY - position.y) * 0.004);
      });

      const cooling = 0.94 - iteration * 0.008;
      nodeIds.forEach((id) => {
        const position = positions.get(id);
        const force = forces.get(id);
        positions.set(id, {
          x: clampTopologyPosition(position.x + force.x * cooling, safePadding, width - safePadding),
          y: clampTopologyPosition(position.y + force.y * cooling, safePadding, height - safePadding),
        });
      });
    }

    return { width, height, positions };
  }

  function positionsFor(activeNodes, mode, activeEdges = []) {
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
    if (mode === "topology") {
      return topologyPositionsFor(activeNodes, activeEdges);
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

  function shouldShowGraphLabel(id, selectedConnectedIds, inspectedConnectedIds, searchContext) {
    return (
      id === selectedId ||
      id === inspectedId ||
      id === activeResultId ||
      selectedConnectedIds.has(id) ||
      inspectedConnectedIds.has(id) ||
      matchIds.has(id) ||
      searchContext.has(id) ||
      degreeFor(id) >= 5
    );
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

  function paddedPointExtent(points, padding) {
    if (!points.length || !fullViewBox) return null;
    const xs = points.map((point) => point.x);
    const ys = points.map((point) => point.y);
    const minX = Math.min(...xs) - padding;
    const maxX = Math.max(...xs) + padding;
    const minY = Math.min(...ys) - padding;
    const maxY = Math.max(...ys) + padding;
    return {
      width: Math.max(120, maxX - minX),
      height: Math.max(96, maxY - minY),
      centerX: (minX + maxX) / 2,
      centerY: (minY + maxY) / 2,
    };
  }

  function paddedGraphBounds(points, padding, limits = {}) {
    const extent = paddedPointExtent(points, padding);
    if (!extent || !fullViewBox) return null;
    const maxWidth = Number(limits.maxWidth || fullViewBox.width);
    const maxHeight = Number(limits.maxHeight || fullViewBox.height);
    const nextWidth = Math.min(fullViewBox.width, maxWidth, extent.width);
    const nextHeight = Math.min(fullViewBox.height, maxHeight, extent.height);
    const x = Math.max(
      fullViewBox.x,
      Math.min(fullViewBox.x + fullViewBox.width - nextWidth, extent.centerX - nextWidth / 2)
    );
    const y = Math.max(
      fullViewBox.y,
      Math.min(fullViewBox.y + fullViewBox.height - nextHeight, extent.centerY - nextHeight / 2)
    );
    return { x, y, width: nextWidth, height: nextHeight };
  }

  function selectedFitPoints() {
    if (!selectedId) return [];
    const selectedPoint = latestRenderedPositions.get(selectedId);
    if (!selectedPoint) return [];
    const connectedPoints = [];
    latestRenderedEdges.forEach((edge) => {
      if (edge.from !== selectedId && edge.to !== selectedId) return;
      const neighborId = edge.from === selectedId ? edge.to : edge.from;
      const point = latestRenderedPositions.get(neighborId);
      if (!point) return;
      const dx = point.x - selectedPoint.x;
      const dy = point.y - selectedPoint.y;
      connectedPoints.push({ point, distance: Math.sqrt(dx * dx + dy * dy) });
    });
    connectedPoints.sort((left, right) => left.distance - right.distance);

    const maxWidth = fullViewBox.width * 0.72;
    const maxHeight = fullViewBox.height * 0.76;
    const points = [selectedPoint];
    connectedPoints.forEach((candidate) => {
      const candidatePoints = [...points, candidate.point];
      const extent = paddedPointExtent(candidatePoints, 72);
      if (extent && extent.width <= maxWidth && extent.height <= maxHeight) {
        points.push(candidate.point);
      }
    });
    return points;
  }

  function selectedNeighborhoodBounds() {
    if (!selectedId || !fullViewBox || root.getAttribute("data-raya-graph-layout") === "list") {
      return null;
    }
    const points = selectedFitPoints();
    return paddedGraphBounds(points, 72, {
      maxWidth: fullViewBox.width * 0.72,
      maxHeight: fullViewBox.height * 0.76,
    });
  }

  function setFitSelectionEnabled() {
    if (!fitSelection) return;
    const enabled = Boolean(
      selectedId &&
      fullViewBox &&
      root.getAttribute("data-raya-graph-layout") !== "list" &&
      latestRenderedPositions.has(selectedId)
    );
    fitSelection.disabled = !enabled;
  }

  function constrainedZoomBox(factor, anchor = null) {
    if (!graphViewBox || !fullViewBox || root.getAttribute("data-raya-graph-layout") === "list") {
      return null;
    }
    const minWidth = fullViewBox.width * 0.32;
    const maxWidth = fullViewBox.width * 1.75;
    const minHeight = fullViewBox.height * 0.32;
    const maxHeight = fullViewBox.height * 1.75;
    const nextWidth = Math.max(minWidth, Math.min(maxWidth, graphViewBox.width * factor));
    const nextHeight = Math.max(minHeight, Math.min(maxHeight, graphViewBox.height * factor));
    const centerX = graphViewBox.x + graphViewBox.width / 2;
    const centerY = graphViewBox.y + graphViewBox.height / 2;
    if (!anchor) {
      return {
        x: centerX - nextWidth / 2,
        y: centerY - nextHeight / 2,
        width: nextWidth,
        height: nextHeight,
      };
    }
    return {
      x: anchor.x - anchor.ratioX * nextWidth,
      y: anchor.y - anchor.ratioY * nextHeight,
      width: nextWidth,
      height: nextHeight,
    };
  }

  function fitSelectedGraphContext() {
    const box = selectedNeighborhoodBounds();
    if (!box) return;
    setGraphViewBox(box);
    canvas.scrollIntoView({ block: "nearest", inline: "nearest" });
  }

  function fitInitialPageFocus() {
    if (!pendingInitialPageFit) return;
    pendingInitialPageFit = false;
    if (!selectedId || root.getAttribute("data-raya-graph-layout") === "list") return;
    const box = selectedNeighborhoodBounds();
    if (box) {
      setGraphViewBox(box);
      canvas.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
    setFitSelectionEnabled();
  }

  function setGraphViewportControlsEnabled(enabled) {
    [zoomIn, zoomOut, resetView, ...panButtons].forEach((button) => {
      if (button) button.disabled = !enabled;
    });
    setFitSelectionEnabled();
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
    const nextBox = constrainedZoomBox(factor);
    if (nextBox) setGraphViewBox(nextBox);
  }

  function graphPointFromClientPoint(clientX, clientY) {
    if (!canvas || !graphViewBox) return null;
    const matrix = canvas.getScreenCTM ? canvas.getScreenCTM() : null;
    if (matrix && canvas.createSVGPoint) {
      const point = canvas.createSVGPoint();
      point.x = clientX;
      point.y = clientY;
      const mapped = point.matrixTransform(matrix.inverse());
      return {
        x: mapped.x,
        y: mapped.y,
      };
    }
    const rect = canvas.getBoundingClientRect();
    const ratioX = Math.max(0, Math.min(1, (clientX - rect.left) / Math.max(1, rect.width)));
    const ratioY = Math.max(0, Math.min(1, (clientY - rect.top) / Math.max(1, rect.height)));
    return {
      x: graphViewBox.x + graphViewBox.width * ratioX,
      y: graphViewBox.y + graphViewBox.height * ratioY,
    };
  }

  function zoomGraphViewAtClientPoint(factor, clientX, clientY) {
    if (!canvas || !graphViewBox) return;
    const graphPoint = graphPointFromClientPoint(clientX, clientY);
    if (!graphPoint) return;
    const ratioX = Math.max(0, Math.min(1, (graphPoint.x - graphViewBox.x) / Math.max(1, graphViewBox.width)));
    const ratioY = Math.max(0, Math.min(1, (graphPoint.y - graphViewBox.y) / Math.max(1, graphViewBox.height)));
    const anchor = {
      ratioX,
      ratioY,
      x: graphPoint.x,
      y: graphPoint.y,
    };
    const nextBox = constrainedZoomBox(factor, anchor);
    if (nextBox) setGraphViewBox(nextBox);
  }

  function wheelZoomGraphView(event) {
    if (!graphViewBox || !fullViewBox || root.getAttribute("data-raya-graph-layout") === "list") {
      return;
    }
    if (event.deltaY === 0 || Math.abs(event.deltaY) < Math.abs(event.deltaX || 0)) {
      return;
    }
    event.preventDefault();
    const factor = event.deltaY < 0 ? 0.88 : 1.14;
    zoomGraphViewAtClientPoint(factor, event.clientX, event.clientY);
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

  function constrainGraphPoint(point, box = fullViewBox) {
    if (!box) return point;
    const margin = 36;
    return {
      x: Math.max(
        box.x + margin,
        Math.min(box.x + box.width - margin, point.x)
      ),
      y: Math.max(
        box.y + margin,
        Math.min(box.y + box.height - margin, point.y)
      ),
    };
  }

  function updateVisibleEdgeGeometryForNode(nodeId) {
    canvas.querySelectorAll(".raya-graph-edge").forEach((line) => {
      const fromId = line.getAttribute("data-raya-graph-from") || "";
      const toId = line.getAttribute("data-raya-graph-to") || "";
      if (fromId !== nodeId && toId !== nodeId) return;
      const edge = latestRenderedEdges.find((candidate) => (
        candidate.from === fromId &&
        candidate.to === toId &&
        edgeKind(candidate) === (line.getAttribute("data-raya-graph-kind") || "")
      ));
      const from = latestRenderedPositions.get(fromId);
      const to = latestRenderedPositions.get(toId);
      if (!edge || !from || !to) return;
      const linePoints = edgeLinePoints(edge, from, to);
      line.setAttribute("x1", String(linePoints.x1));
      line.setAttribute("y1", String(linePoints.y1));
      line.setAttribute("x2", String(linePoints.x2));
      line.setAttribute("y2", String(linePoints.y2));
    });
  }

  function updateVisibleNodePosition(nodeId, point) {
    const nextPoint = constrainGraphPoint(point);
    latestRenderedPositions.set(nodeId, nextPoint);
    manualNodePositions.set(nodeId, nextPoint);
    canvas.querySelectorAll("[data-raya-graph-node]").forEach((link) => {
      if ((link.getAttribute("data-raya-graph-node") || "") !== nodeId) return;
      const group = link.querySelector("g");
      if (group) {
        group.setAttribute("transform", `translate(${nextPoint.x} ${nextPoint.y})`);
        group.classList.add("is-dragging");
      }
    });
    updateVisibleEdgeGeometryForNode(nodeId);
    setFitSelectionEnabled();
  }

  function startGraphNodeDrag(event, nodeId) {
    if (
      graphNodeDrag ||
      !nodeId ||
      !latestRenderedPositions.has(nodeId) ||
      root.getAttribute("data-raya-graph-layout") === "list" ||
      (event.type.startsWith("pointer") && event.pointerType && event.pointerType !== "mouse") ||
      event.button !== 0
    ) {
      return;
    }
    const graphPoint = graphPointFromClientPoint(event.clientX, event.clientY);
    const nodePoint = latestRenderedPositions.get(nodeId);
    if (!graphPoint || !nodePoint) return;
    graphNodeDrag = {
      pointerId: event.pointerId ?? "mouse",
      nodeId,
      startClientX: event.clientX,
      startClientY: event.clientY,
      startGraphPoint: graphPoint,
      startNodePoint: { ...nodePoint },
      moved: false,
      captured: false,
    };
    if (event.pointerId !== undefined && canvas.setPointerCapture) {
      canvas.setPointerCapture(event.pointerId);
      graphNodeDrag.captured = true;
    }
    canvas.classList.add("is-dragging-node");
    if (hoverStatus) hoverStatus.textContent = `Repositioning ${nodesById.get(nodeId)?.title || nodeId}.`;
    event.preventDefault();
    event.stopPropagation();
  }

  function moveGraphNodeDrag(event) {
    const pointerId = event.type.startsWith("mouse") && graphNodeDrag
      ? graphNodeDrag.pointerId
      : event.pointerId ?? "mouse";
    if (!graphNodeDrag || graphNodeDrag.pointerId !== pointerId) return false;
    const graphPoint = graphPointFromClientPoint(event.clientX, event.clientY);
    if (!graphPoint) return true;
    const dx = graphPoint.x - graphNodeDrag.startGraphPoint.x;
    const dy = graphPoint.y - graphNodeDrag.startGraphPoint.y;
    if (
      Math.abs(event.clientX - graphNodeDrag.startClientX) > 4 ||
      Math.abs(event.clientY - graphNodeDrag.startClientY) > 4
    ) {
      graphNodeDrag.moved = true;
    }
    updateVisibleNodePosition(graphNodeDrag.nodeId, {
      x: graphNodeDrag.startNodePoint.x + dx,
      y: graphNodeDrag.startNodePoint.y + dy,
    });
    event.preventDefault();
    event.stopPropagation();
    return true;
  }

  function endGraphNodeDrag(event) {
    const pointerId = event.type.startsWith("mouse") && graphNodeDrag
      ? graphNodeDrag.pointerId
      : event.pointerId ?? "mouse";
    if (!graphNodeDrag || graphNodeDrag.pointerId !== pointerId) return false;
    const nodeId = graphNodeDrag.nodeId;
    if (graphNodeDrag.moved) {
      suppressedNodeClick = { id: nodeId, until: Date.now() + 500 };
    }
    const moved = graphNodeDrag.moved;
    const captured = graphNodeDrag.captured;
    canvas.querySelectorAll("[data-raya-graph-node] g.is-dragging").forEach((group) => {
      group.classList.remove("is-dragging");
    });
    graphNodeDrag = null;
    canvas.classList.remove("is-dragging-node");
    if (hoverStatus) hoverStatus.textContent = "";
    if (captured && event.pointerId !== undefined && canvas.releasePointerCapture) {
      try {
        canvas.releasePointerCapture(event.pointerId);
      } catch {
        // Pointer capture may already be released by the browser.
      }
    }
    if (!moved) {
      const now = Date.now();
      const opensNode = graphNodeClickSequence.id === nodeId &&
        now - graphNodeClickSequence.time <= 360;
      graphNodeClickSequence = { id: nodeId, time: now };
      window.clearTimeout(pendingSelectTimer);
      if (opensNode) {
        graphNodeClickSequence = { id: "", time: 0 };
        openGraphNode(nodeId);
      } else {
        pendingSelectTimer = window.setTimeout(() => {
          selectGraphNode(nodeId);
        }, 180);
      }
    }
    event.preventDefault();
    event.stopPropagation();
    return true;
  }

  function shouldSuppressGraphNodeClick(nodeId) {
    return suppressedNodeClick.id === nodeId && Date.now() <= suppressedNodeClick.until;
  }

  function inspectionTextFor(nodeId) {
    const node = nodesById.get(nodeId);
    if (!node) return "";
    const group = groupsById.get(node.group || "");
    const counts = relationshipCountsFor(nodeId);
    return `Inspecting ${node.title || node.nav_title || node.id}: ${group ? group.title : "Course"}; ${counts.outgoingCount} outgoing link(s), ${counts.incomingCount} incoming link(s), ${counts.connectedCount} connected page(s).`;
  }

  function inspectionPreviewTextFor(node) {
    const group = groupsById.get(node.group || "");
    return [
      group ? group.title : "",
      node.hierarchy_label || "",
      node.status ? `Status: ${node.status}` : "",
    ].filter(Boolean).join(" · ");
  }

  function inspectionPreviewCountTextFor(nodeId) {
    const counts = relationshipCountsFor(nodeId);
    return `${counts.outgoingCount} outgoing · ${counts.incomingCount} incoming · ${counts.connectedCount} connected`;
  }

  function renderInspectionPreview(nodeId) {
    if (!inspectionPreview) return;
    const node = nodesById.get(nodeId);
    if (!node) {
      inspectionPreview.hidden = true;
      if (inspectionPreviewSelect) inspectionPreviewSelect.dataset.rayaGraphNode = "";
      if (inspectionPreviewOpen) inspectionPreviewOpen.removeAttribute("href");
      return;
    }
    if (inspectionPreviewTitle) {
      inspectionPreviewTitle.textContent = node.title || node.nav_title || node.id;
    }
    if (inspectionPreviewMeta) {
      inspectionPreviewMeta.textContent = inspectionPreviewTextFor(node);
    }
    if (inspectionPreviewSummary) {
      inspectionPreviewSummary.textContent = node.summary || "No summary available.";
    }
    if (inspectionPreviewCounts) {
      inspectionPreviewCounts.textContent = inspectionPreviewCountTextFor(node.id);
    }
    if (inspectionPreviewSelect) {
      inspectionPreviewSelect.dataset.rayaGraphNode = node.id;
    }
    if (inspectionPreviewOpen) {
      inspectionPreviewOpen.href = node.url || "#";
    }
    inspectionPreview.hidden = false;
  }

  function updateInspectionDom() {
    renderInspectionPreview(inspectedId);
    const inspectedConnectedIds = inspectedId ? connectedNodeIds(inspectedId) : new Set();
    const inspectedSpotlightIds = inspectedId
      ? new Set([inspectedId, ...inspectedConnectedIds])
      : new Set();
    const searchSpotlight = searchSpotlightIds();
    const searchContext = searchContextNodeIds();
    const selectedConnectedIds = selectedId ? connectedNodeIds(selectedId) : new Set();
    canvas.querySelectorAll("[data-raya-graph-node] g").forEach((nodeGroup) => {
      const link = nodeGroup.closest("[data-raya-graph-node]");
      const id = link ? link.getAttribute("data-raya-graph-node") || "" : "";
      nodeGroup.classList.toggle("is-inspected", id === inspectedId);
      nodeGroup.classList.toggle("is-inspected-neighbor", inspectedConnectedIds.has(id));
      nodeGroup.classList.toggle(
        "is-label-visible",
        shouldShowGraphLabel(id, selectedConnectedIds, inspectedConnectedIds, searchContext)
      );
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
    canvas.querySelectorAll(".raya-graph-edge, .raya-graph-arrow-marker").forEach((edgeMark) => {
      const from = edgeMark.getAttribute("data-raya-graph-from") || "";
      const to = edgeMark.getAttribute("data-raya-graph-to") || "";
      edgeMark.classList.toggle(
        "is-inspected",
        Boolean(inspectedId) && (from === inspectedId || to === inspectedId)
      );
      edgeMark.classList.toggle(
        "is-dimmed",
        Boolean(inspectedId) && !(from === inspectedId || to === inspectedId)
      );
      edgeMark.classList.toggle(
        "is-search-context",
        Boolean(query) && (matchIds.has(from) || matchIds.has(to))
      );
      edgeMark.classList.toggle(
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

  function inspectGraphNode(nodeId, options = {}) {
    if (query && document.activeElement === search && !options.force) {
      return;
    }
    inspectedId = nodesById.has(nodeId) ? nodeId : "";
    if (hoverStatus) hoverStatus.textContent = inspectedId ? inspectionTextFor(inspectedId) : "";
    renderInspectionPreview(inspectedId);
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
      pageFocusId = "";
      pendingInitialPageFit = false;
      clearRelationshipFocus();
      selectedId = activeResultId;
      inspectedId = activeResultId;
      renderDetail();
      renderInspectionPreview(inspectedId);
      updateInspectionDom();
      syncGraphStateReadout();
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
        renderInspectionPreview(inspectedId);
        updateInspectionDom();
        return;
      }
      inspectedId = "";
      if (hoverStatus) hoverStatus.textContent = "";
      renderInspectionPreview("");
      updateInspectionDom();
    };
    if (nodeId) {
      window.setTimeout(applyClear, 0);
    } else {
      applyClear();
    }
  }

  function edgeLabel(edge) {
    return edgeKindLabel(edgeKind(edge));
  }

  function focusGraphDetailNode(nodeId) {
    if (!nodesById.has(nodeId)) return;
    graphViewBox = null;
    selectGraphNode(nodeId);
  }

  function safeGraphMarkerFragment(value) {
    return String(value || "")
      .replace(/[^A-Za-z0-9_-]+/g, "-")
      .replace(/^-+|-+$/g, "") || "edge";
  }

  function graphArrowMarkerId(edge, edgeIndex) {
    return [
      "raya-graph-arrow",
      String(edgeIndex),
      safeGraphMarkerFragment(edge.from),
      safeGraphMarkerFragment(edge.to),
      safeGraphMarkerFragment(edgeKind(edge)),
    ].join("-");
  }

  function graphArrowMarkerUrl(edge, edgeIndex) {
    return `url(#${graphArrowMarkerId(edge, edgeIndex)})`;
  }

  function edgeStateClassNames(edge) {
    return [
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
    ].filter(Boolean);
  }

  function appendGraphArrowMarkers(activeEdges) {
    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    activeEdges.forEach((edge, edgeIndex) => {
      const markerId = graphArrowMarkerId(edge, edgeIndex);
      const marker = document.createElementNS("http://www.w3.org/2000/svg", "marker");
      marker.setAttribute("id", markerId);
      marker.setAttribute("data-raya-graph-from", edge.from);
      marker.setAttribute("data-raya-graph-to", edge.to);
      marker.setAttribute("data-raya-graph-kind", edgeKind(edge));
      marker.setAttribute(
        "class",
        [
          "raya-graph-arrow-marker",
          edgeKindClass(edge),
          ...edgeStateClassNames(edge),
        ].filter(Boolean).join(" ")
      );
      marker.setAttribute("markerWidth", "8");
      marker.setAttribute("markerHeight", "8");
      marker.setAttribute("refX", "7");
      marker.setAttribute("refY", "4");
      marker.setAttribute("orient", "auto");
      marker.setAttribute("markerUnits", "strokeWidth");
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", "M 0 0 L 8 4 L 0 8 z");
      path.style.setProperty("--raya-graph-edge-color", edgeColorFor(edge));
      marker.appendChild(path);
      defs.appendChild(marker);
    });
    canvas.appendChild(defs);
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

  function titleForUrl(url) {
    if (!url) return "";
    const target = nodes.find((candidate) => candidate.url === url);
    return target ? (target.title || target.nav_title || target.id) : "";
  }

  function previousPageTitle(node) {
    return titleForUrl(node.previous_url) || "previous page";
  }

  function nextPageTitle(node) {
    return titleForUrl(node.next_url) || "next page";
  }

  function setOptionalDetailLink(link, href, text) {
    if (!link) return;
    if (href) {
      link.href = href;
      link.textContent = text;
      link.hidden = false;
    } else {
      link.hidden = true;
      link.removeAttribute("href");
      link.textContent = text;
    }
  }

  function studyCountsText(counts) {
    if (!counts || typeof counts !== "object") return "";
    return Object.keys(counts).sort().map((key) => {
      const value = counts[key];
      const label = value === 1 ? key : `${key}s`;
      return `${label.charAt(0).toUpperCase()}${label.slice(1)}: ${value}`;
    }).join(", ");
  }

  function renderDetailStudyObjects(node) {
    if (!detailStudyObjects || !detailStudyObjectList) return;
    detailStudyObjectList.replaceChildren();
    const objects = Array.isArray(node && node.study_objects) ? node.study_objects : [];
    if (!objects.length) {
      detailStudyObjects.hidden = true;
      return;
    }
    objects.forEach((item) => {
      const li = document.createElement("li");
      const link = document.createElement("a");
      link.href = item.url || node.url || "#";
      link.textContent = (
        item.title ||
        item.preview ||
        item.id ||
        item.type_label ||
        "Study object"
      );
      const meta = document.createElement("span");
      meta.className = "raya-graph-detail-study-object-meta";
      const dateText = item.due
        ? `Due ${item.due}`
        : (item.available ? `Available ${item.available}` : "");
      meta.textContent = [item.type_label || item.type || "Study object", dateText]
        .filter(Boolean)
        .join(" · ");
      li.appendChild(link);
      li.appendChild(meta);
      if (item.preview && item.preview !== link.textContent) {
        const preview = document.createElement("span");
        preview.className = "raya-graph-detail-study-object-preview";
        preview.textContent = item.preview;
        li.appendChild(preview);
      }
      detailStudyObjectList.appendChild(li);
    });
    detailStudyObjects.hidden = false;
  }

  function renderRelationshipChips(nodeId) {
    if (!detailRelationshipChips || !detailRelationshipChipList) return;
    detailRelationshipChipList.replaceChildren();
    if (!nodeId) {
      detailRelationshipChips.hidden = true;
      return;
    }
    const chips = relationshipChipCountsFor(nodeId);
    if (!chips.length) {
      detailRelationshipChips.hidden = true;
      return;
    }
    chips.forEach((chip) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "raya-graph-detail-relationship-chip";
      item.setAttribute("data-raya-graph-relationship-chip", "");
      item.setAttribute("data-raya-graph-relationship-kind", chip.kind);
      item.setAttribute("data-raya-graph-relationship-direction", chip.direction);
      item.setAttribute("aria-pressed", "false");
      item.textContent = `${relationshipChipLabel(chip.kind, chip.direction)} ${chip.count}`;
      item.addEventListener("click", () =>
        setRelationshipFocus(chip.kind, chip.direction)
      );
      detailRelationshipChipList.appendChild(item);
    });
    syncRelationshipFocusDom();
    detailRelationshipChips.hidden = false;
  }

  function relationshipWalkthroughGroupsFor(nodeId) {
    const groupsByKey = new Map();
    const addItem = (kind, direction, item) => {
      const normalizedKind = edgeKind({ kind });
      const key = `${normalizedKind}:${direction}`;
      if (!groupsByKey.has(key)) {
        groupsByKey.set(key, {
          kind: normalizedKind,
          direction,
          items: [],
        });
      }
      groupsByKey.get(key).items.push(item);
    };
    edges.forEach((edge) => {
      if (edge.from === nodeId) {
        const target = nodesById.get(edge.to);
        addItem(edge.kind, "out", {
          id: edge.to,
          title: target ? (target.title || target.nav_title || edge.to) : edge.to,
          url: target ? target.url : "#",
        });
      }
      if (edge.to === nodeId) {
        const source = nodesById.get(edge.from);
        addItem(edge.kind, "in", {
          id: edge.from,
          title: source ? (source.title || source.nav_title || edge.from) : edge.from,
          url: source ? source.url : "#",
        });
      }
    });
    const kindOrder = ["navigation", "content", "prerequisite", "parent"];
    const directionOrder = ["out", "in"];
    return Array.from(groupsByKey.values()).sort((left, right) => {
      const leftKind = kindOrder.indexOf(left.kind);
      const rightKind = kindOrder.indexOf(right.kind);
      const kindDelta = (leftKind < 0 ? kindOrder.length : leftKind) -
        (rightKind < 0 ? kindOrder.length : rightKind);
      if (kindDelta !== 0) return kindDelta;
      const directionDelta = directionOrder.indexOf(left.direction) -
        directionOrder.indexOf(right.direction);
      if (directionDelta !== 0) return directionDelta;
      return left.kind.localeCompare(right.kind);
    }).map((group) => ({
      ...group,
      items: group.items.sort((left, right) => {
        const leftNode = nodesById.get(left.id);
        const rightNode = nodesById.get(right.id);
        if (leftNode && rightNode) return compareNodesByOrder(leftNode, rightNode);
        return String(left.title || left.id).localeCompare(String(right.title || right.id));
      }),
    }));
  }

  function renderRelationshipWalkthrough(nodeId) {
    if (!relationshipWalkthrough || !relationshipWalkthroughList) return;
    relationshipWalkthroughList.replaceChildren();
    if (!nodeId) {
      relationshipWalkthrough.hidden = true;
      return;
    }
    const groupsForNode = relationshipWalkthroughGroupsFor(nodeId);
    if (!groupsForNode.length) {
      relationshipWalkthrough.hidden = true;
      return;
    }
    groupsForNode.forEach((group) => {
      const card = document.createElement("section");
      card.className = "raya-graph-relationship-walkthrough-card";
      card.setAttribute("data-raya-graph-relationship-walkthrough-card", "");
      card.setAttribute("data-raya-graph-relationship-kind", group.kind);
      card.setAttribute("data-raya-graph-relationship-direction", group.direction);

      const title = document.createElement("h4");
      title.textContent = relationshipWalkthroughTitle(group.kind, group.direction);
      const meaning = document.createElement("p");
      meaning.textContent = relationshipWalkthroughMeaning(group.kind, group.direction);
      const listEl = document.createElement("ul");
      group.items.forEach((item) => {
        const li = document.createElement("li");
        const link = document.createElement("a");
        link.href = item.url || "#";
        link.textContent = item.title || item.id || "Untitled page";
        li.appendChild(link);
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
      card.append(title, meaning, listEl);
      relationshipWalkthroughList.appendChild(card);
    });
    syncRelationshipFocusDom();
    relationshipWalkthrough.hidden = false;
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

  function explicitRelationshipsFor(nodeId, direction) {
    return edges
      .filter((edge) => (direction === "out" ? edge.from === nodeId : edge.to === nodeId))
      .map((edge) => {
        const otherId = direction === "out" ? edge.to : edge.from;
        const target = nodesById.get(otherId) || {};
        return {
          id: otherId,
          title: target.title || otherId,
          url: target.url || "#",
          kind: edgeLabel(edge),
        };
      });
  }

  function renderDetail() {
    const node = selectedId ? nodesById.get(selectedId) : null;
    if (!node) {
      setGraphNeighborhoodFocus(false);
      clearRelationshipFocus();
      if (detailEmpty) detailEmpty.hidden = false;
      if (detailPanel) detailPanel.hidden = true;
      if (detailSummary) detailSummary.textContent = "";
      if (detailStudyCounts) detailStudyCounts.textContent = "";
      renderDetailStudyObjects(null);
      renderRelationshipChips("");
      if (detailNeighborhood) detailNeighborhood.textContent = "";
      setOptionalDetailLink(detailTasksLink, "", "Open tasks");
      setOptionalDetailLink(detailScheduleLink, "", "Open schedule");
      setOptionalDetailLink(detailPreviousLink, "", "Previous");
      renderRelationshipWalkthrough("");
      if (detailCurrentLink) {
        detailCurrentLink.href = "#";
        detailCurrentLink.textContent = "Selected page";
      }
      setOptionalDetailLink(detailNextLink, "", "Next");
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
    renderDetailStudyObjects(node);
    renderRelationshipChips(node.id);
    renderRelationshipWalkthrough(node.id);
    if (detailNeighborhood) {
      const counts = relationshipCountsFor(node.id);
      detailNeighborhood.textContent = `Explicit links: ${counts.outgoingCount} outgoing, ${counts.incomingCount} incoming, ${counts.connectedCount} connected.`;
    }
    if (detailLink) {
      detailLink.href = node.url;
      detailLink.textContent = "Open selected page";
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
    setOptionalDetailLink(detailTasksLink, node.tasks_url || "", "Open tasks");
    setOptionalDetailLink(detailScheduleLink, node.schedule_url || "", "Open schedule");
    setOptionalDetailLink(
      detailPreviousLink,
      node.previous_url || "",
      node.previous_url ? "Previous: " + previousPageTitle(node) : "Previous"
    );
    if (detailCurrentLink) {
      detailCurrentLink.href = node.url;
      detailCurrentLink.textContent = "Selected: " + (node.title || node.nav_title || node.id);
    }
    setOptionalDetailLink(
      detailNextLink,
      node.next_url || "",
      node.next_url ? "Next: " + nextPageTitle(node) : "Next"
    );
    const outgoing = explicitRelationshipsFor(node.id, "out");
    const incoming = explicitRelationshipsFor(node.id, "in");
    renderDetailList(detailOutgoing, outgoing, "No outgoing links.");
    renderDetailList(detailIncoming, incoming, "No incoming links.");
  }

  function selectGraphNode(nodeId) {
    clearRelationshipFocus();
    neighborhoodFocus = false;
    pageFocusId = "";
    pendingInitialPageFit = false;
    selectedId = nodeId;
    renderDetail();
    render();
  }

  function openGraphNode(nodeId) {
    const node = nodesById.get(nodeId);
    if (!node || !node.url) return;
    window.location.href = node.url;
  }

  function clearGraphSelection() {
    window.clearTimeout(pendingSelectTimer);
    pendingSelectTimer = 0;
    clearRelationshipFocus();
    selectedId = "";
    inspectedId = "";
    activeResultId = "";
    pageFocusId = "";
    pendingInitialPageFit = false;
    if (hoverStatus) hoverStatus.textContent = "";
    renderInspectionPreview("");
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

  function initializeGraphStateFromUrl() {
    const params = currentUrlParams();
    clearRelationshipFocus();
    const pageId = params.get("page") || "";
    selectedId = nodesById.has(pageId) ? pageId : "";
    pageFocusId = selectedId;
    pendingInitialPageFit = Boolean(selectedId);
    const queryText = params.get("q") || "";
    if (search && queryText) {
      search.value = queryText;
    }
    const layoutParam = params.get("layout") || "";
    if (layout && graphLayouts.has(layoutParam)) {
      layout.value = layoutParam;
    } else if (layout) {
      layout.value = defaultLayout;
    }
    applyVisibleGroupsFromUrl(params.get("groups") || "");
    applyVisibleEdgeKindsFromUrl(params.get("edges") || "");
    if (params.get("expanded") === "1") {
      setGraphExpanded(true);
    }
    if (params.get("list") === "0") {
      setGraphPanelState("list", false);
    }
    if (params.get("inspector") === "0") {
      setGraphPanelState("inspector", false);
    }
    if (params.get("neighborhood") === "1" && selectedId) {
      setGraphNeighborhoodFocus(true);
    }
  }

  function renderList(activeIds) {
    list.querySelector("[data-raya-graph-empty]")?.remove();
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
    if (query && activeIds.size === 0) {
      const empty = document.createElement("li");
      empty.className = "raya-graph-empty";
      empty.setAttribute("data-raya-graph-empty", "");
      const text = document.createElement("p");
      text.textContent = `No graph pages match "${search ? search.value.trim() : query}".`;
      const button = document.createElement("button");
      button.type = "button";
      button.setAttribute("data-raya-graph-clear-search", "");
      button.textContent = "Clear search";
      button.addEventListener("click", () => {
        if (search) search.value = "";
        activeResultId = "";
        inspectedId = "";
        pageFocusId = "";
        pendingInitialPageFit = false;
        graphViewBox = null;
        if (hoverStatus) hoverStatus.textContent = "";
        renderDetail();
        render();
        if (search) search.focus();
      });
      empty.append(text, button);
      list.appendChild(empty);
      setPanelFocusable(
        graphPanelBody("list"),
        root.getAttribute("data-raya-graph-list-state") !== "collapsed"
      );
    }
  }

  function setGraphExpanded(nextExpanded) {
    root.dataset.rayaGraphExpanded = nextExpanded ? "true" : "false";
    root.setAttribute("data-raya-graph-expanded", nextExpanded ? "true" : "false");
    if (graphExpand) {
      graphExpand.setAttribute("aria-pressed", nextExpanded ? "true" : "false");
      graphExpand.setAttribute(
        "aria-label",
        nextExpanded ? "Leave graph focus mode" : "Expand graph focus mode"
      );
      graphExpand.textContent = nextExpanded ? "Compact" : "Focus";
    }
    if (nextExpanded) {
      setGraphPanelState("list", false);
      setGraphPanelState("inspector", false);
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
      pageFocusId = "";
      pendingInitialPageFit = false;
      renderDetail();
      listNodes = visibleListNodes();
      listIds = new Set(listNodes.map((node) => node.id));
    }
    const activeNodes = visibleGraphNodes(listNodes);
    const activeIds = new Set(activeNodes.map((node) => node.id));
    const activeEdges = visibleGraphEdges(activeIds);
    lastActiveNodes = activeNodes;
    lastActiveEdges = activeEdges;
    updateGraphOrientation(activeNodes, activeEdges);
    if (activeResultId && !listIds.has(activeResultId)) {
      activeResultId = "";
    }
    if (inspectedId && !activeIds.has(inspectedId)) {
      inspectedId = "";
      if (hoverStatus) hoverStatus.textContent = "";
    }
    renderList(listIds);
    if (status) {
      const statusPrefix = neighborhoodFocus ? "Neighborhood focus: " : "";
      const edgeKindText = hiddenEdgeKindStatusText();
      if (query) {
        const contextCount = Math.max(0, listNodes.length - matchIds.size);
        const baseStatusText = `${statusPrefix}${matchIds.size} match(es), ${contextCount} connected page(s) shown; ${activeNodes.length} visible node(s) in graph, ${activeEdges.length} visible edge(s) in graph.`;
        status.textContent = [baseStatusText, edgeKindText].filter(Boolean).join(" ");
      } else {
        const baseStatusText = `${statusPrefix}${activeNodes.length} visible node(s), ${activeEdges.length} visible edge(s).`;
        status.textContent = [baseStatusText, edgeKindText].filter(Boolean).join(" ");
      }
    }
    syncGraphStateReadout();
    if (mode === "list") {
      canvas.setAttribute("hidden", "hidden");
      canvas.replaceChildren();
      fullViewBox = null;
      graphViewBox = null;
      pendingInitialPageFit = false;
      latestRenderedPositions = new Map();
      latestRenderedEdges = [];
      setGraphViewportControlsEnabled(false);
      setFitSelectionEnabled();
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
    const geometry = positionsFor(activeNodes, mode, activeEdges);
    const nextFullViewBox = { x: 0, y: 0, width: geometry.width, height: geometry.height };
    latestRenderedPositions = geometry.positions;
    activeNodes.forEach((node) => {
      const manualPoint = manualNodePositions.get(node.id);
      if (manualPoint) {
        latestRenderedPositions.set(node.id, constrainGraphPoint(manualPoint, nextFullViewBox));
      }
    });
    latestRenderedEdges = activeEdges;

    fullViewBox = nextFullViewBox;
    if (!graphViewBox) {
      setGraphViewBox({ ...fullViewBox });
    } else {
      canvas.setAttribute("viewBox", viewBoxString(graphViewBox));
    }
    fitInitialPageFocus();
    setGraphViewportControlsEnabled(true);
    canvas.replaceChildren();
    appendGraphArrowMarkers(activeEdges);

    activeEdges.forEach((edge, edgeIndex) => {
      const from = latestRenderedPositions.get(edge.from);
      const to = latestRenderedPositions.get(edge.to);
      if (!from || !to) return;
      const linePoints = edgeLinePoints(edge, from, to);
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", String(linePoints.x1));
      line.setAttribute("y1", String(linePoints.y1));
      line.setAttribute("x2", String(linePoints.x2));
      line.setAttribute("y2", String(linePoints.y2));
      line.setAttribute("data-raya-graph-from", edge.from);
      line.setAttribute("data-raya-graph-to", edge.to);
      line.setAttribute("data-raya-graph-kind", edgeKind(edge));
      line.setAttribute("marker-end", graphArrowMarkerUrl(edge, edgeIndex));
      line.style.setProperty("--raya-graph-edge-color", edgeColorFor(edge));
      line.setAttribute(
        "class",
        [
          "raya-graph-edge",
          edgeKindClass(edge),
          ...edgeStateClassNames(edge),
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
      const isLabelVisible = shouldShowGraphLabel(
        node.id,
        connectedIds,
        inspectedConnectedIds,
        searchContext
      );
      group.setAttribute(
        "class",
        [
          "raya-graph-node",
          active ? "" : "is-muted",
          isLabelVisible ? "is-label-visible" : "",
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
      text.setAttribute("class", "raya-graph-node-label");
      text.setAttribute("y", String(radius + 20));
      text.textContent = node.nav_title || node.title || node.id;
      group.append(hitTarget, circle, text);
      link.appendChild(group);
      link.addEventListener("click", (event) => {
        event.preventDefault();
        if (shouldSuppressGraphNodeClick(node.id)) {
          suppressedNodeClick = { id: "", until: 0 };
          return;
        }
        window.clearTimeout(pendingSelectTimer);
        pendingSelectTimer = window.setTimeout(() => {
          selectGraphNode(node.id);
        }, 180);
      });
      link.addEventListener("dblclick", (event) => {
        event.preventDefault();
        window.clearTimeout(pendingSelectTimer);
        openGraphNode(node.id);
      });
      link.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") return;
        event.preventDefault();
        window.clearTimeout(pendingSelectTimer);
        openGraphNode(node.id);
      });
      link.addEventListener("mouseenter", () => inspectGraphNode(node.id));
      link.addEventListener("mouseleave", () => clearGraphInspection(node.id));
      link.addEventListener("focus", () => inspectGraphNode(node.id, { force: true }));
      link.addEventListener("blur", () => clearGraphInspection(node.id));
      link.addEventListener("pointerdown", (event) => startGraphNodeDrag(event, node.id));
      link.addEventListener("mousedown", (event) => startGraphNodeDrag(event, node.id));
      canvas.appendChild(link);
    });
    if (activeResultId) setActiveResult(activeResultId, { scroll: false });
    updateInspectionDom();
    setFitSelectionEnabled();
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
      pageFocusId = "";
      pendingInitialPageFit = false;
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
      manualNodePositions.clear();
      render();
    });
  }
  if (fit) {
    fit.addEventListener("click", () => {
      graphViewBox = null;
      render();
    });
  }
  if (fitSelection) {
    fitSelection.addEventListener("click", fitSelectedGraphContext);
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
  canvas.addEventListener("wheel", wheelZoomGraphView, { passive: false });
  canvas.addEventListener("pointerdown", startGraphPan);
  canvas.addEventListener("pointermove", (event) => {
    if (!moveGraphNodeDrag(event)) moveGraphPan(event);
  });
  canvas.addEventListener("pointerup", (event) => {
    if (!endGraphNodeDrag(event)) endGraphPan(event);
  });
  canvas.addEventListener("pointercancel", (event) => {
    if (!endGraphNodeDrag(event)) endGraphPan(event);
  });
  canvas.addEventListener("mousedown", startGraphPan);
  canvas.addEventListener("mousemove", (event) => {
    if (!moveGraphNodeDrag(event)) moveGraphPan(event);
  });
  canvas.addEventListener("mouseup", (event) => {
    if (!endGraphNodeDrag(event)) endGraphPan(event);
  });
  canvas.addEventListener("mouseleave", (event) => {
    if (!endGraphNodeDrag(event)) endGraphPan(event);
  });
  if (reset) {
    reset.addEventListener("click", () => {
      if (search) search.value = "";
      if (layout) layout.value = "connections";
      hiddenGroups.clear();
      hiddenEdgeKinds.clear();
      manualNodePositions.clear();
      suppressedNodeClick = { id: "", until: 0 };
      graphNodeClickSequence = { id: "", time: 0 };
      clearRelationshipFocus();
      updateEdgeKindFilters();
      selectedId = "";
      inspectedId = "";
      activeResultId = "";
      pageFocusId = "";
      pendingInitialPageFit = false;
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
      setGraphPanelState("inspector", !nextExpanded);
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
      const nextExpanded = root.getAttribute(attr) === "collapsed";
      if (nextExpanded && root.dataset.rayaGraphExpanded === "true") {
        setGraphExpanded(false);
      }
      setGraphPanelState(panelName, nextExpanded);
      syncGraphStateReadout();
    });
  });
  if (detailClear) {
    detailClear.addEventListener("click", clearGraphSelection);
  }
  if (orientationClear) {
    orientationClear.addEventListener("click", clearGraphSelection);
  }
  if (orientationNeighborhoodToggle) {
    orientationNeighborhoodToggle.addEventListener("click", () => {
      if (!selectedId) return;
      setGraphNeighborhoodFocus(!neighborhoodFocus);
      graphViewBox = null;
      render();
    });
  }
  if (copyUrl) {
    copyUrl.addEventListener("click", copyGraphUrl);
  }
  if (inspectionPreviewSelect) {
    inspectionPreviewSelect.addEventListener("click", () => {
      const nodeId = inspectionPreviewSelect.dataset.rayaGraphNode || "";
      if (nodeId) selectGraphNode(nodeId);
    });
  }
  if (focusNeighborhood) {
    focusNeighborhood.addEventListener("click", () => {
      setGraphNeighborhoodFocus(!neighborhoodFocus);
      graphViewBox = null;
      render();
    });
  }
  edgeKindFilters.forEach((button) => {
    button.addEventListener("click", () => {
      const kind = button.getAttribute("data-raya-graph-edge-kind-filter") || "";
      if (!kind) return;
      if (hiddenEdgeKinds.has(kind)) {
        hiddenEdgeKinds.delete(kind);
      } else {
        hiddenEdgeKinds.add(kind);
      }
      updateEdgeKindFilters();
      render();
    });
  });
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
    inspectGraphNode(item.getAttribute("data-raya-graph-node") || "", { force: true });
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
      inspectGraphNode(item.getAttribute("data-raya-graph-node") || "", { force: true });
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

  root.setAttribute("data-raya-graph-neighborhood-focus", "false");
  setGraphPanelState("list", true);
  setGraphPanelState("inspector", true);
  setGraphExpanded(false);
  updateEdgeKindFilters();
  updateGroupFilters();
  initializeGraphStateFromUrl();
  renderDetail();
  render();
})();
"""
