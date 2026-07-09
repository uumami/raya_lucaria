from __future__ import annotations

from dataclasses import dataclass


SHELL_SCRIPT_NAME = "shell.js"
SHELL_RESOURCE_PATH = "_raya/render"


@dataclass(frozen=True)
class ShellResources:
    javascript: str


def shell_resources() -> ShellResources:
    return ShellResources(javascript=_SHELL_JAVASCRIPT)


_SHELL_JAVASCRIPT = r"""
(() => {
  const root = document.documentElement;
  const shell = document.querySelector(".raya-learning-shell");
  const map = document.querySelector("#raya-course-map");
  const article = document.querySelector("#raya-article");
  const skipLink = document.querySelector('.raya-skip-link[href="#raya-article"]');
  const mobileMapOpener = document.querySelector(".raya-mobile-course-map-open");
  const toggleButtons = Array.from(document.querySelectorAll("[data-raya-course-map-toggle]"));
  const learningRail = document.querySelector("#raya-learning-rail");
  const learningRailBody = document.querySelector("#raya-learning-rail-body");
  const learningRailCollapse = document.querySelector("[data-raya-learning-rail-collapse]");
  const learningRailExpand = document.querySelector("[data-raya-learning-rail-expand]");
  const learningRailDrawerBackdrop = document.querySelector(
    "[data-raya-learning-rail-drawer-backdrop]"
  );
  const learningRailToggleButtons = Array.from(
    document.querySelectorAll("[data-raya-learning-rail-toggle]")
  );
  const railToggleButtons = Array.from(document.querySelectorAll("[data-raya-rail-toggle]"));
  const mapNodeToggles = Array.from(document.querySelectorAll("[data-raya-map-node-toggle]"));
  const mapCloseButton = document.querySelector("[data-raya-course-map-close]");
  const mapDrawerBackdrop = document.querySelector("[data-raya-course-map-drawer-backdrop]");
  const mapFilter = document.querySelector("[data-raya-course-map-filter]");
  const mapFilterEmpty = document.querySelector("[data-raya-map-filter-empty]");
  const mapCompactPreview = document.querySelector("[data-raya-course-map-compact-preview]");
  const assetInspectButtons = Array.from(document.querySelectorAll("[data-raya-asset-inspect]"));
  const desktopMapQuery = window.matchMedia("(min-width: 1280px)");
  const structuralRailQuery = window.matchMedia("(min-width: 640px)");
  const compactStructuralRailQuery = window.matchMedia(
    "(min-width: 640px) and (max-width: 767px)"
  );
  const approvedRailGeometryQuery = window.matchMedia("(min-width: 894px)");
  const printQuery = window.matchMedia("print");
  const tocLinks = Array.from(document.querySelectorAll(".raya-page-toc a[href^='#']"));
  const currentSectionLinks = Array.from(
    document.querySelectorAll("[data-raya-current-section-link]")
  );
  const keyObjectLinks = Array.from(
    document.querySelectorAll(".raya-page-toc-objects a[data-raya-key-object-link]")
  );
  const keyObjectTargets = keyObjectLinks
    .map((link) => {
      const id = link.getAttribute("data-raya-key-object-link") || "";
      return id ? document.getElementById(id) : null;
    })
    .filter(Boolean);
  const headings = tocLinks
    .map((link) => {
      const href = link.getAttribute("href");
      if (!href || href === "#") {
        return null;
      }
      let id = href.slice(1);
      try {
        id = decodeURIComponent(id);
      } catch {
        id = href.slice(1);
      }
      const target = document.getElementById(id);
      return target ? { link, target } : null;
    })
    .filter(Boolean);

  if (!shell || !map || toggleButtons.length === 0) {
    return;
  }
  let courseMapDrawerOpener = null;
  let activeCompactPreviewLink = null;
  let focusedCompactPreviewLink = null;
  let hoveredCompactPreviewLink = null;
  let assetInspector = null;
  let assetInspectorOpener = null;
  let learningRailDrawerOpener = null;
  let courseMapTransitionTimer = 0;
  let learningRailTransitionTimer = 0;
  const SHELL_TRANSITION_MS = 240;

  function updateMapLinkTabOrder(nextExpanded) {
    const mapList = map.querySelector("#raya-course-map-list");
    const hideFullMapContent = structuralRailQuery.matches && !nextExpanded;
    if (mapList) {
      mapList.setAttribute("aria-hidden", hideFullMapContent ? "true" : "false");
      mapList.inert = hideFullMapContent;
      setFocusableDescendantsEnabled(mapList, !hideFullMapContent);
    }
    if (desktopMapQuery.matches) {
      map.removeAttribute("tabindex");
    } else {
      map.setAttribute("tabindex", "-1");
    }
    map.querySelectorAll("a").forEach((link) => {
      if (hideFullMapContent) {
        link.setAttribute("tabindex", "-1");
      } else {
        link.removeAttribute("tabindex");
      }
    });
    map
      .querySelectorAll(
        [
          ".raya-course-rail-tools",
          ".raya-course-map-filter-label",
          ".raya-course-map-filter",
          ".raya-map-filter-empty",
          ".raya-course-map-close",
        ].join(",")
      )
      .forEach((element) => {
        element.setAttribute("aria-hidden", hideFullMapContent ? "true" : "false");
        setElementInert(element, hideFullMapContent);
        setFocusableDescendantsEnabled(element, !hideFullMapContent);
      });
    map.querySelectorAll("[data-raya-course-map-toggle]").forEach((button) => {
      if (button.dataset.rayaPreviousTabindex === "__none__") {
        button.removeAttribute("tabindex");
        delete button.dataset.rayaPreviousTabindex;
      } else if (button.dataset.rayaPreviousTabindex) {
        button.setAttribute("tabindex", button.dataset.rayaPreviousTabindex);
        delete button.dataset.rayaPreviousTabindex;
      } else {
        button.removeAttribute("tabindex");
      }
    });
  }

  function isDesktopShell() {
    return desktopMapQuery.matches;
  }

  function isStructuralRailShell() {
    return structuralRailQuery.matches;
  }

  function isCompactStructuralRailShell() {
    return structuralRailQuery.matches && compactStructuralRailQuery.matches;
  }

  function isPhoneDrawerShell() {
    return !isStructuralRailShell() && !printQuery.matches;
  }

  function isMediumStructuralShell() {
    return isStructuralRailShell() && !isDesktopShell();
  }

  function defaultCourseMapExpanded() {
    return (
      !isStructuralRailShell() || isDesktopShell() || approvedRailGeometryQuery.matches
    );
  }

  function defaultLearningRailExpanded() {
    return (
      !isStructuralRailShell() || isDesktopShell() || approvedRailGeometryQuery.matches
    );
  }

  function setFocusableDescendantsEnabled(container, enabled) {
    container
      .querySelectorAll("a[href], button, input, select, textarea, summary, [tabindex]")
      .forEach((element) => {
        if (enabled) {
          if (element.dataset.rayaPreviousTabindex === "__none__") {
            element.removeAttribute("tabindex");
          } else if (element.dataset.rayaPreviousTabindex) {
            element.setAttribute("tabindex", element.dataset.rayaPreviousTabindex);
          }
          delete element.dataset.rayaPreviousTabindex;
          return;
        }
        if (!element.dataset.rayaPreviousTabindex) {
          element.dataset.rayaPreviousTabindex = element.hasAttribute("tabindex")
            ? element.getAttribute("tabindex")
            : "__none__";
        }
        element.setAttribute("tabindex", "-1");
      });
  }

  function setElementInert(element, inert) {
    if (inert) {
      element.setAttribute("inert", "");
    } else {
      element.removeAttribute("inert");
    }
    element.inert = inert;
  }

  function setAssistiveHidden(element, hidden) {
    if (!element) {
      return;
    }
    if (hidden) {
      element.setAttribute("aria-hidden", "true");
    } else {
      element.removeAttribute("aria-hidden");
    }
    setElementInert(element, hidden);
    setFocusableDescendantsEnabled(element, !hidden);
  }

  function syncCourseMapModalBackground(drawerOpen) {
    const hidden = drawerOpen;
    [skipLink, article, learningRail, mobileMapOpener].forEach((element) => {
      setAssistiveHidden(element, hidden);
    });
    if (!hidden && learningRail) {
      learningRail.setAttribute("aria-hidden", "false");
    }
  }

  function focusableElementsWithin(container) {
    return Array.from(
      container.querySelectorAll(
        "a[href], button, input, select, textarea, summary, [tabindex]"
      )
    ).filter((element) => {
      if (element.disabled || element.getAttribute("tabindex") === "-1") {
        return false;
      }
      const style = window.getComputedStyle(element);
      return (
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        element.getClientRects().length > 0
      );
    });
  }

  function trapCourseMapDrawerFocus(event) {
    if (
      event.key !== "Tab" ||
      root.dataset.rayaCourseMapDrawer !== "open" ||
      !isPhoneDrawerShell()
    ) {
      return false;
    }
    const focusable = focusableElementsWithin(map);
    if (focusable.length === 0) {
      event.preventDefault();
      map.focus();
      return true;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const activeElement = document.activeElement;
    if (!map.contains(activeElement)) {
      event.preventDefault();
      (event.shiftKey ? last : first).focus();
      return true;
    }
    if (event.shiftKey && activeElement === first) {
      event.preventDefault();
      last.focus();
      return true;
    }
    if (!event.shiftKey && activeElement === last) {
      event.preventDefault();
      first.focus();
      return true;
    }
    return false;
  }

  function trapLearningRailDrawerFocus(event) {
    if (
      event.key !== "Tab" ||
      root.dataset.rayaLearningRailDrawer !== "open" ||
      isDesktopShell() ||
      !learningRail
    ) {
      return false;
    }
    const focusable = focusableElementsWithin(learningRail);
    if (focusable.length === 0) {
      event.preventDefault();
      learningRail.focus();
      return true;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const activeElement = document.activeElement;
    if (!learningRail.contains(activeElement)) {
      event.preventDefault();
      (event.shiftKey ? last : first).focus();
      return true;
    }
    if (event.shiftKey && activeElement === first) {
      event.preventDefault();
      last.focus();
      return true;
    }
    if (!event.shiftKey && activeElement === last) {
      event.preventDefault();
      first.focus();
      return true;
    }
    return false;
  }

  function clearCourseMapFilter() {
    if (mapFilter && mapFilter.value) {
      mapFilter.value = "";
      applyCourseMapFilter();
    }
  }

  function syncCourseMapDrawerState() {
    const drawerOpen = root.dataset.rayaCourseMapDrawer === "open";
    const structuralShell = isStructuralRailShell();
    const modalDrawerOpen = drawerOpen && !structuralShell && isPhoneDrawerShell();
    const hidesCourseMapFilter =
      (!structuralShell && drawerOpen) || (structuralShell && !desktopMapQuery.matches);
    if (hidesCourseMapFilter) {
      clearCourseMapFilter();
    }
    const structuralExpanded = root.dataset.rayaCourseMap === "expanded";
    const commandExpanded = !structuralShell ? drawerOpen : structuralExpanded;
    root.setAttribute(
      "data-raya-course-map-scroll-lock",
      modalDrawerOpen ? "true" : "false"
    );
    toggleButtons
      .filter((button) => button.classList.contains("raya-command-map"))
      .forEach((button) => {
        button.setAttribute("aria-expanded", commandExpanded ? "true" : "false");
        button.setAttribute(
          "aria-label",
          !structuralShell
            ? commandExpanded
              ? "Close course map"
              : "Open course map"
            : commandExpanded
              ? "Collapse course map"
              : "Expand course map"
        );
    });
    if (mapDrawerBackdrop) {
      mapDrawerBackdrop.hidden = !modalDrawerOpen;
    }
    if (!structuralShell) {
      if (modalDrawerOpen) {
        const drawerTitle = map.querySelector(".raya-course-map-drawer-title");
        if (drawerTitle && !drawerTitle.id) {
          drawerTitle.id = "raya-course-map-drawer-title";
        }
        map.setAttribute("role", "dialog");
        map.setAttribute("aria-modal", "true");
        if (drawerTitle && drawerTitle.id) {
          map.setAttribute("aria-labelledby", drawerTitle.id);
        }
      } else {
        map.removeAttribute("role");
        map.removeAttribute("aria-modal");
        map.removeAttribute("aria-labelledby");
      }
      syncCourseMapModalBackground(modalDrawerOpen);
      setElementInert(map, !drawerOpen);
      setFocusableDescendantsEnabled(map, drawerOpen);
      map.setAttribute("aria-hidden", drawerOpen ? "false" : "true");
      return;
    }
    syncCourseMapModalBackground(false);
    map.removeAttribute("role");
    map.removeAttribute("aria-modal");
    map.removeAttribute("aria-labelledby");
    setElementInert(map, false);
    setFocusableDescendantsEnabled(map, true);
    map.setAttribute("aria-hidden", "false");
    updateMapLinkTabOrder(root.dataset.rayaCourseMap !== "collapsed");
    if (root.dataset.rayaCourseMapDrawer !== "closed") {
      root.dataset.rayaCourseMapDrawer = "closed";
    }
    root.setAttribute("data-raya-course-map-scroll-lock", "false");
    if (mapDrawerBackdrop) {
      mapDrawerBackdrop.hidden = true;
    }
  }

  function setExpanded(nextExpanded) {
    const previousExpanded = root.dataset.rayaCourseMap !== "collapsed";
    const desktopTransition = isStructuralRailShell() && previousExpanded !== nextExpanded;
    const desktopExpanding = desktopTransition && nextExpanded;
    if (!nextExpanded) {
      clearCourseMapFilter();
    } else {
      hideCourseMapCompactPreview();
    }
    if (desktopTransition) {
      window.clearTimeout(courseMapTransitionTimer);
      map.dataset.rayaCourseMapTransition = nextExpanded ? "expanding" : "collapsing";
      if (desktopExpanding) {
        updateMapLinkTabOrder(false);
      }
      courseMapTransitionTimer = window.setTimeout(() => {
        delete map.dataset.rayaCourseMapTransition;
        if (desktopExpanding && root.dataset.rayaCourseMap === "expanded") {
          updateMapLinkTabOrder(true);
        }
      }, SHELL_TRANSITION_MS);
    } else {
      window.clearTimeout(courseMapTransitionTimer);
      delete map.dataset.rayaCourseMapTransition;
    }
    root.dataset.rayaCourseMap = nextExpanded ? "expanded" : "collapsed";
    shell.dataset.rayaCourseMap = nextExpanded ? "expanded" : "collapsed";
    map.dataset.rayaCourseMap = nextExpanded ? "expanded" : "collapsed";
    toggleButtons.forEach((button) => {
      button.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
      button.setAttribute(
        "aria-label",
        nextExpanded ? "Collapse course map" : "Expand course map"
      );
      if (map.contains(button) && !button.classList.contains("raya-command-map")) {
        button.textContent = nextExpanded ? "Collapse map" : "Expand map";
      }
    });
    if (!desktopExpanding) {
      updateMapLinkTabOrder(nextExpanded);
    }
    syncCourseMapDrawerState();
    if (desktopExpanding) {
      const mapList = map.querySelector("#raya-course-map-list");
      if (mapList) {
        mapList.setAttribute("aria-hidden", "true");
        mapList.inert = true;
        setFocusableDescendantsEnabled(mapList, false);
      }
    }
  }

  function normalizeMapQuery(value) {
    return String(value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }

  function mapNodeText(node) {
    const link = node.querySelector(":scope > .raya-course-map-node-row a");
    return normalizeMapQuery(
      [
        link ? link.textContent : "",
        link ? link.getAttribute("data-raya-map-label") : "",
      ].join(" ")
    );
  }

  function courseMapBranchStorageKey() {
    const explicitKey = map.getAttribute("data-raya-course-map-storage-key") || "";
    return explicitKey || "raya:course-map:" + window.location.pathname.split("/").slice(0, -1).join("/");
  }

  function loadStoredCollapsedMapBranches() {
    try {
      const raw = window.sessionStorage.getItem(courseMapBranchStorageKey());
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed)
        ? new Set(parsed.filter((value) => typeof value === "string" && value))
        : new Set();
    } catch (_error) {
      return new Set();
    }
  }

  function mapNodeId(node) {
    return node && node.dataset ? node.dataset.rayaMapNode || "" : "";
  }

  function saveCollapsedMapBranches() {
    const collapsed = mapNodeToggles
      .map((button) => button.closest("[data-raya-map-node]"))
      .filter((node) => node && node.dataset.rayaMapExpanded !== "true")
      .map((node) => mapNodeId(node))
      .filter(Boolean);
    try {
      window.sessionStorage.setItem(
        courseMapBranchStorageKey(),
        JSON.stringify(collapsed)
      );
    } catch (_error) {
      return;
    }
  }

  function setMapNodeExpanded(node, nextExpanded, options = {}) {
    const toggle = node.querySelector(":scope > .raya-course-map-node-row [data-raya-map-node-toggle]");
    const childrenId = toggle ? toggle.getAttribute("aria-controls") : "";
    const children = childrenId ? document.getElementById(childrenId) : null;
    if (!toggle || !children) {
      return;
    }
    if (!options.temporary) {
      node.dataset.rayaMapExpanded = nextExpanded ? "true" : "false";
    }
    toggle.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
    children.hidden = !nextExpanded;
    children.setAttribute("aria-hidden", nextExpanded ? "false" : "true");
    if (!options.temporary && !options.skipPersist) {
      saveCollapsedMapBranches();
    }
  }

  function applyStoredMapExpansion(node) {
    setMapNodeExpanded(node, node.dataset.rayaMapExpanded === "true", {
      temporary: true,
    });
  }

  function filterMapNode(node, query) {
    const childNodes = Array.from(
      node.querySelectorAll(":scope > [data-raya-map-children] > [data-raya-map-node]")
    );
    const selfMatches = !query || mapNodeText(node).includes(query);
    const childMatches = childNodes.map((child) => filterMapNode(child, query));
    const descendantMatches = childMatches.some(Boolean);
    const visible = selfMatches || descendantMatches;
    node.hidden = !visible;
    if (query && descendantMatches) {
      setMapNodeExpanded(node, true, { temporary: true });
    } else if (!query) {
      applyStoredMapExpansion(node);
    }
    return visible;
  }

  function applyCourseMapFilter() {
    if (!mapFilter) {
      return;
    }
    const query = normalizeMapQuery(mapFilter.value);
    const topNodes = Array.from(
      map.querySelectorAll("#raya-course-map-list > ol > [data-raya-map-node]")
    );
    let visibleCount = 0;
    topNodes.forEach((node) => {
      if (filterMapNode(node, query)) {
        visibleCount += 1;
      }
    });
    if (mapFilterEmpty) {
      mapFilterEmpty.hidden = visibleCount !== 0;
    }
  }

  function isVisibleCourseMapElement(element) {
    if (!(element instanceof Element)) {
      return false;
    }
    const style = window.getComputedStyle(element);
    return (
      style.display !== "none" &&
      style.visibility !== "hidden" &&
      element.getClientRects().length > 0
    );
  }

  function courseMapLinkForNode(node) {
    return node
      ? node.querySelector(":scope > .raya-course-map-node-row a[href]")
      : null;
  }

  function visibleCourseMapLinks() {
    const mapList = map.querySelector("#raya-course-map-list");
    if (!mapList || !isVisibleCourseMapElement(mapList)) {
      return [];
    }
    return Array.from(
      mapList.querySelectorAll("[data-raya-map-node] > .raya-course-map-node-row a[href]")
    ).filter((link) => isVisibleCourseMapElement(link));
  }

  function focusedCourseMapNode() {
    const activeElement = document.activeElement;
    if (!(activeElement instanceof Element)) {
      return null;
    }
    const mapList = map.querySelector("#raya-course-map-list");
    if (!mapList || !mapList.contains(activeElement)) {
      return null;
    }
    return activeElement.closest("[data-raya-map-node]");
  }

  function parentCourseMapLink(node) {
    const parentNode = node && node.parentElement
      ? node.parentElement.closest("[data-raya-map-node]")
      : null;
    return parentNode ? courseMapLinkForNode(parentNode) : null;
  }

  function firstVisibleChildCourseMapLink(node) {
    if (!node) {
      return null;
    }
    const childLinks = Array.from(
      node.querySelectorAll(
        ":scope > [data-raya-map-children] > [data-raya-map-node] > .raya-course-map-node-row a[href]"
      )
    );
    return childLinks.find((link) => isVisibleCourseMapElement(link)) || null;
  }

  function focusCourseMapLinkAtOffset(offset) {
    const links = visibleCourseMapLinks();
    const activeElement = document.activeElement;
    const currentIndex = links.indexOf(activeElement);
    if (currentIndex === -1) {
      return false;
    }
    const nextIndex = Math.max(0, Math.min(links.length - 1, currentIndex + offset));
    const nextLink = links[nextIndex];
    if (!nextLink || nextLink === activeElement) {
      return false;
    }
    nextLink.focus();
    return true;
  }

  function focusCourseMapBoundary(boundary) {
    const links = visibleCourseMapLinks();
    const nextLink = boundary === "last" ? links[links.length - 1] : links[0];
    if (!nextLink || nextLink === document.activeElement) {
      return false;
    }
    nextLink.focus();
    return true;
  }

  function handleCourseMapKeyboardNavigation(event) {
    if (isEditableNavigationTarget(event.target)) {
      return false;
    }
    if (event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) {
      return false;
    }
    const node = focusedCourseMapNode();
    if (!node) {
      return false;
    }
    const mapNavigationKeys = new Set([
      "ArrowDown",
      "ArrowUp",
      "Home",
      "End",
      "ArrowRight",
      "ArrowLeft",
    ]);
    if (!mapNavigationKeys.has(event.key)) {
      return false;
    }
    let handled = false;
    if (event.key === "ArrowDown") {
      handled = focusCourseMapLinkAtOffset(1);
    } else if (event.key === "ArrowUp") {
      handled = focusCourseMapLinkAtOffset(-1);
    } else if (event.key === "Home") {
      handled = focusCourseMapBoundary("first");
    } else if (event.key === "End") {
      handled = focusCourseMapBoundary("last");
    } else if (event.key === "ArrowRight") {
      const toggle = node.querySelector(":scope > .raya-course-map-node-row [data-raya-map-node-toggle]");
      if (toggle && toggle.getAttribute("aria-expanded") !== "true") {
        setMapNodeExpanded(node, true);
        handled = true;
      } else {
        const childLink = firstVisibleChildCourseMapLink(node);
        if (childLink) {
          childLink.focus();
          handled = true;
        }
      }
    } else if (event.key === "ArrowLeft") {
      const toggle = node.querySelector(":scope > .raya-course-map-node-row [data-raya-map-node-toggle]");
      if (toggle && toggle.getAttribute("aria-expanded") === "true") {
        setMapNodeExpanded(node, false);
        handled = true;
      } else {
        const parentLink = parentCourseMapLink(node);
        if (parentLink && isVisibleCourseMapElement(parentLink)) {
          parentLink.focus();
          handled = true;
        }
      }
    }
    event.preventDefault();
    event.stopPropagation();
    return handled;
  }

  function orientCourseMapToCurrentPage(options = {}) {
    const mapList = map.querySelector("#raya-course-map-list");
    const currentLink = mapList
      ? mapList.querySelector('a[aria-current="page"]')
      : null;
    const scrollContainer = mapList;
    if (!mapList || !currentLink || !scrollContainer) {
      return false;
    }
    if (mapFilter && mapFilter.value && !options.force) {
      return false;
    }
    if (
      scrollContainer.dataset.rayaCourseMapOriented === "true" &&
      !options.force &&
      !options.repeat
    ) {
      return false;
    }
    const orientWithin = (container) => {
      const containerRect = container.getBoundingClientRect();
      const linkRect = currentLink.getBoundingClientRect();
      const isVisible =
        linkRect.top >= containerRect.top && linkRect.bottom <= containerRect.bottom;
      if (isVisible) {
        return;
      }
      const offset =
        container.scrollTop +
        linkRect.top -
        containerRect.top -
        container.clientHeight / 2 +
        currentLink.offsetHeight / 2;
      container.scrollTop = Math.max(0, offset);
      const adjustedContainerRect = container.getBoundingClientRect();
      const adjustedLinkRect = currentLink.getBoundingClientRect();
      if (adjustedLinkRect.top < adjustedContainerRect.top) {
        container.scrollTop = Math.max(
          0,
          container.scrollTop + adjustedLinkRect.top - adjustedContainerRect.top
        );
      } else if (adjustedLinkRect.bottom > adjustedContainerRect.bottom) {
        container.scrollTop = Math.max(
          0,
          container.scrollTop + adjustedLinkRect.bottom - adjustedContainerRect.bottom
        );
      }
    };
    orientWithin(scrollContainer);
    if (map !== scrollContainer) {
      orientWithin(map);
    }
    scrollContainer.dataset.rayaCourseMapOriented = "true";
    map.dataset.rayaCourseMapOriented = "true";
    return true;
  }

  function compactPreviewLabel(link) {
    return link ? link.getAttribute("data-raya-map-label") || link.textContent || "" : "";
  }

  function positionCourseMapCompactPreview(link) {
    if (!mapCompactPreview || !link || root.dataset.rayaCourseMap !== "collapsed") {
      hideCourseMapCompactPreview();
      return;
    }
    const label = compactPreviewLabel(link).trim();
    if (!label || !isDesktopShell()) {
      hideCourseMapCompactPreview();
      return;
    }
    const linkBox = link.getBoundingClientRect();
    const mapBox = map.getBoundingClientRect();
    const previewWidth = Math.min(288, Math.max(168, window.innerWidth - mapBox.right - 24));
    mapCompactPreview.textContent = label;
    mapCompactPreview.hidden = false;
    mapCompactPreview.style.width = `${previewWidth}px`;
    mapCompactPreview.style.left = `${Math.min(mapBox.right + 8, window.innerWidth - previewWidth - 8)}px`;
    mapCompactPreview.style.top = "0px";
    const previewHeight = mapCompactPreview.getBoundingClientRect().height;
    const idealTop = linkBox.top + linkBox.height / 2 - previewHeight / 2;
    const maxTop = Math.max(8, window.innerHeight - previewHeight - 8);
    const clampedTop = Math.max(8, Math.min(idealTop, maxTop));
    mapCompactPreview.style.top = `${clampedTop}px`;
  }

  function activeCourseMapCompactPreviewLink() {
    return hoveredCompactPreviewLink || focusedCompactPreviewLink;
  }

  function updateCourseMapCompactPreview() {
    const link = activeCourseMapCompactPreviewLink();
    if (
      !mapCompactPreview ||
      !link ||
      !map.contains(link) ||
      root.dataset.rayaCourseMap !== "collapsed" ||
      !isDesktopShell()
    ) {
      hideCourseMapCompactPreviewSurface();
      return;
    }
    activeCompactPreviewLink = link;
    positionCourseMapCompactPreview(link);
  }

  function hideCourseMapCompactPreviewSurface() {
    if (!mapCompactPreview) {
      return;
    }
    activeCompactPreviewLink = null;
    mapCompactPreview.hidden = true;
    mapCompactPreview.textContent = "";
    mapCompactPreview.removeAttribute("style");
  }

  function hideCourseMapCompactPreview() {
    focusedCompactPreviewLink = null;
    hoveredCompactPreviewLink = null;
    hideCourseMapCompactPreviewSurface();
  }

  function refreshCourseMapCompactPreview() {
    updateCourseMapCompactPreview();
  }

  function currentCourseMapNodes() {
    const currentLink = map.querySelector("#raya-course-map-list a[aria-current='page']");
    if (!currentLink) {
      return new Set();
    }
    const currentNode = currentLink.closest("[data-raya-map-node]");
    const nodes = new Set();
    let node = currentNode;
    while (node && map.contains(node)) {
      if (node.matches("[data-raya-map-node]")) {
        nodes.add(node);
      }
      node = node.parentElement ? node.parentElement.closest("[data-raya-map-node]") : null;
    }
    return nodes;
  }

  function expandCurrentCourseMapPath() {
    clearCourseMapFilter();
    const currentNodes = currentCourseMapNodes();
    mapNodeToggles.forEach((button) => {
      const node = button.closest("[data-raya-map-node]");
      if (node) {
        setMapNodeExpanded(node, currentNodes.has(node), {
          skipPersist: true,
        });
      }
    });
    orientCourseMapToCurrentPage({ force: true });
  }

  function openCourseMapDrawer(opener = null) {
    if (opener instanceof Element) {
      courseMapDrawerOpener = opener;
    }
    root.dataset.rayaCourseMapDrawer = "open";
    setExpanded(true);
    syncCourseMapDrawerState();
    window.requestAnimationFrame(() => {
      const focusTarget =
        map.querySelector("[data-raya-course-map-close]") ||
        map.querySelector("a, button");
      if (focusTarget) {
        focusTarget.focus();
      }
      orientCourseMapToCurrentPage({ repeat: true });
    });
  }

  function closeCourseMapDrawer(options = {}) {
    root.dataset.rayaCourseMapDrawer = "closed";
    hideCourseMapCompactPreview();
    syncCourseMapDrawerState();
    if (options.restoreFocus && courseMapDrawerOpener) {
      courseMapDrawerOpener.focus();
    }
  }

  window.rayaOrientCourseMapToCurrentPage = () =>
    orientCourseMapToCurrentPage({ force: true });
  window.rayaOrientCourseMapToCurrentPageAutomatic = () =>
    orientCourseMapToCurrentPage({ repeat: true });

  function syncLearningRailToggleButtons(nextExpanded) {
    const drawerOpen = root.dataset.rayaLearningRailDrawer === "open";
    const structuralShell = isStructuralRailShell();
    const commandExpanded = !structuralShell ? drawerOpen : nextExpanded;
    learningRailToggleButtons.forEach((button) => {
      button.setAttribute("aria-expanded", commandExpanded ? "true" : "false");
      button.setAttribute(
        "aria-label",
        !structuralShell
          ? commandExpanded
            ? "Close learning context"
            : "Open learning context"
          : nextExpanded
            ? "Hide learning context"
            : "Show learning context"
      );
    });
  }

  function syncLearningRailDrawerState() {
    if (!learningRail || !learningRailBody) {
      return;
    }
    const structuralShell = isStructuralRailShell();
    if (!structuralShell && root.dataset.rayaLearningRailDrawer !== "closed") {
      root.dataset.rayaLearningRailDrawer = "closed";
    }
    const drawerOpen = root.dataset.rayaLearningRailDrawer === "open";
    root.setAttribute(
      "data-raya-learning-rail-scroll-lock",
      drawerOpen && !structuralShell ? "true" : "false"
    );
    if (learningRailDrawerBackdrop) {
      learningRailDrawerBackdrop.hidden = !drawerOpen;
    }
    if (!structuralShell) {
      learningRail.setAttribute("aria-hidden", "false");
      setElementInert(learningRail, false);
      setFocusableDescendantsEnabled(learningRail, true);
      learningRailBody.setAttribute("aria-hidden", "false");
      setElementInert(learningRailBody, false);
      setFocusableDescendantsEnabled(learningRailBody, true);
      railToggleButtons.forEach((button) => {
        setRailPanelExpanded(button, button.getAttribute("aria-expanded") === "true");
      });
      syncLearningRailToggleButtons(root.dataset.rayaLearningRail !== "collapsed");
      return;
    }
    learningRail.setAttribute("aria-hidden", "false");
    setElementInert(learningRail, false);
    setFocusableDescendantsEnabled(learningRail, true);
    const railExpanded = root.dataset.rayaLearningRail !== "collapsed";
    learningRailBody.setAttribute("aria-hidden", railExpanded ? "false" : "true");
    setElementInert(learningRailBody, !railExpanded);
    setFocusableDescendantsEnabled(learningRailBody, railExpanded);
    if (root.dataset.rayaLearningRailDrawer !== "closed") {
      root.dataset.rayaLearningRailDrawer = "closed";
    }
    root.setAttribute("data-raya-learning-rail-scroll-lock", "false");
    if (learningRailDrawerBackdrop) {
      learningRailDrawerBackdrop.hidden = true;
    }
    syncLearningRailToggleButtons(root.dataset.rayaLearningRail !== "collapsed");
    if (railExpanded) {
      railToggleButtons.forEach((button) => {
        setRailPanelExpanded(button, button.getAttribute("aria-expanded") === "true");
      });
    }
  }

  function setLearningRailExpanded(nextExpanded) {
    if (!learningRail || !learningRailBody) {
      return;
    }
    const previousExpanded = root.dataset.rayaLearningRail !== "collapsed";
    const desktopTransition = isStructuralRailShell() && previousExpanded !== nextExpanded;
    const desktopExpanding = desktopTransition && nextExpanded;
    if (desktopTransition) {
      window.clearTimeout(learningRailTransitionTimer);
      learningRail.dataset.rayaLearningRailTransition = nextExpanded
        ? "expanding"
        : "collapsing";
      learningRailTransitionTimer = window.setTimeout(() => {
        delete learningRail.dataset.rayaLearningRailTransition;
      }, SHELL_TRANSITION_MS);
    } else {
      window.clearTimeout(learningRailTransitionTimer);
      delete learningRail.dataset.rayaLearningRailTransition;
    }
    root.dataset.rayaLearningRail = nextExpanded ? "expanded" : "collapsed";
    shell.dataset.rayaLearningRail = nextExpanded ? "expanded" : "collapsed";
    learningRail.dataset.rayaLearningRail = nextExpanded ? "expanded" : "collapsed";
    syncLearningRailToggleButtons(nextExpanded);
    learningRailBody.setAttribute("aria-hidden", nextExpanded ? "false" : "true");
    setElementInert(learningRailBody, !nextExpanded);
    setFocusableDescendantsEnabled(learningRailBody, nextExpanded);
    if (nextExpanded) {
      railToggleButtons.forEach((button) => {
        setRailPanelExpanded(button, button.getAttribute("aria-expanded") === "true");
      });
    }
    if (learningRailCollapse) {
      learningRailCollapse.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
    }
    if (learningRailExpand) {
      learningRailExpand.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
    }
    syncLearningRailDrawerState();
  }

  function openLearningRailDrawer(opener = null) {
    if (!learningRail || !learningRailBody) {
      return;
    }
    if (opener instanceof Element) {
      learningRailDrawerOpener = opener;
    }
    root.dataset.rayaLearningRailDrawer = "open";
    syncLearningRailDrawerState();
    window.requestAnimationFrame(() => {
      const focusTarget = learningRail.querySelector("button, a[href], summary");
      if (focusTarget) {
        focusTarget.focus();
      } else {
        learningRail.focus();
      }
    });
  }

  function closeLearningRailDrawer(options = {}) {
    root.dataset.rayaLearningRailDrawer = "closed";
    syncLearningRailDrawerState();
    if (options.restoreFocus && learningRailDrawerOpener) {
      learningRailDrawerOpener.focus();
    }
  }

  function setRailPanelExpanded(button, nextExpanded) {
    const bodyId = button.getAttribute("aria-controls");
    if (!bodyId) {
      return;
    }
    const body = document.getElementById(bodyId);
    const panel = button.closest(".raya-rail-panel");
    if (!body || !panel) {
      return;
    }
    panel.dataset.rayaRailPanelState = nextExpanded ? "expanded" : "collapsed";
    button.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
    body.setAttribute("aria-hidden", nextExpanded ? "false" : "true");
    setElementInert(body, !nextExpanded);
    setFocusableDescendantsEnabled(body, nextExpanded);
  }

  function isEditableNavigationTarget(target) {
    if (!(target instanceof Element)) {
      return false;
    }
    const tagName = target.tagName.toLowerCase();
    return (
      target.isContentEditable ||
      tagName === "input" ||
      tagName === "textarea" ||
      tagName === "select"
    );
  }

  function navigateToSequenceLink(selector) {
    const link = document.querySelector(selector);
    const href = link ? link.getAttribute("href") : "";
    if (!href) {
      return false;
    }
    window.location.href = href;
    return true;
  }

  function handleSequenceKeyboardNavigation(event) {
    if (isEditableNavigationTarget(event.target)) {
      return false;
    }
    if (event.ctrlKey || event.metaKey || event.shiftKey) {
      return false;
    }
    const previousRequested =
      (!event.altKey && event.key === "ArrowLeft") ||
      (event.altKey && event.key === "k");
    const nextRequested =
      (!event.altKey && event.key === "ArrowRight") ||
      (event.altKey && event.key === "j");
    if (!previousRequested && !nextRequested) {
      return false;
    }
    const selector = previousRequested
      ? "[data-raya-prev-page]"
      : "[data-raya-next-page]";
    if (!navigateToSequenceLink(selector)) {
      return false;
    }
    event.preventDefault();
    return true;
  }

  function resetCopyButton(button) {
    window.setTimeout(() => {
      button.textContent = "Copy";
      button.setAttribute("aria-label", "Copy code block");
      button.removeAttribute("data-raya-copy-state");
    }, 1600);
  }

  function copyWithFallback(text) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.top = "-1000px";
    document.body.appendChild(textarea);
    textarea.select();
    try {
      return document.execCommand("copy");
    } finally {
      textarea.remove();
    }
  }

  async function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
    return copyWithFallback(text);
  }

  function initializeCodeCopyControls() {
    document.querySelectorAll("[data-raya-copy-code]").forEach((button) => {
      button.addEventListener("click", async () => {
        const block = button.closest(".raya-code-block");
        const code = block ? block.querySelector("pre code") : null;
        if (!code) {
          return;
        }
        try {
          const copied = await copyText(code.textContent || "");
          button.textContent = copied ? "Copied" : "Copy failed";
          button.setAttribute(
            "aria-label",
            copied ? "Code block copied" : "Code block copy failed"
          );
          button.dataset.rayaCopyState = copied ? "copied" : "failed";
        } catch {
          button.textContent = "Copy failed";
          button.setAttribute("aria-label", "Code block copy failed");
          button.dataset.rayaCopyState = "failed";
        }
        resetCopyButton(button);
      });
    });
  }

  function ensureAssetInspector() {
    if (assetInspector) {
      return assetInspector;
    }
    assetInspector = document.createElement("div");
    assetInspector.className = "raya-asset-inspector";
    assetInspector.hidden = true;
    assetInspector.setAttribute("aria-hidden", "true");
    assetInspector.setAttribute("aria-modal", "true");
    assetInspector.setAttribute("data-raya-asset-inspector", "");
    assetInspector.setAttribute("role", "dialog");
    assetInspector.innerHTML = `
      <div class="raya-asset-inspector-panel" data-raya-asset-inspector-panel>
        <div class="raya-asset-inspector-header">
          <h2 id="raya-asset-inspector-title" data-raya-asset-inspector-title>Image</h2>
          <button class="raya-asset-inspector-close" type="button" data-raya-asset-inspector-close aria-label="Close image inspector">Close</button>
        </div>
        <figure class="raya-asset-inspector-figure">
          <img data-raya-asset-inspector-image alt="">
        </figure>
        <p class="raya-asset-inspector-actions">
          <a data-raya-asset-inspector-open href="">Open image file</a>
        </p>
      </div>
    `;
    assetInspector.setAttribute("aria-labelledby", "raya-asset-inspector-title");
    document.body.appendChild(assetInspector);
    assetInspector.addEventListener("click", (event) => {
      if (event.target === assetInspector) {
        closeAssetInspector({ restoreFocus: true });
      }
    });
    const close = assetInspector.querySelector("[data-raya-asset-inspector-close]");
    if (close) {
      close.addEventListener("click", () => closeAssetInspector({ restoreFocus: true }));
    }
    return assetInspector;
  }

  function assetInspectorIsOpen() {
    return Boolean(assetInspector && !assetInspector.hidden);
  }

  function trapAssetInspectorFocus(event) {
    if (!assetInspectorIsOpen() || event.key !== "Tab" || !assetInspector) {
      return false;
    }
    const focusable = focusableElementsWithin(assetInspector);
    if (focusable.length === 0) {
      event.preventDefault();
      assetInspector.focus();
      return true;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
      return true;
    }
    if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
      return true;
    }
    return false;
  }

  function openAssetInspector(button) {
    const inspector = ensureAssetInspector();
    const src = button.getAttribute("data-raya-asset-src") || "";
    const alt = button.getAttribute("data-raya-asset-alt") || "Image";
    const title = inspector.querySelector("[data-raya-asset-inspector-title]");
    const image = inspector.querySelector("[data-raya-asset-inspector-image]");
    const open = inspector.querySelector("[data-raya-asset-inspector-open]");
    assetInspectorOpener = button;
    if (title) title.textContent = alt;
    if (image) {
      image.setAttribute("src", src);
      image.setAttribute("alt", alt);
    }
    if (open) {
      open.setAttribute("href", src);
    }
    inspector.hidden = false;
    inspector.setAttribute("aria-hidden", "false");
    const close = inspector.querySelector("[data-raya-asset-inspector-close]");
    if (close) close.focus();
  }

  function closeAssetInspector({ restoreFocus } = { restoreFocus: false }) {
    if (!assetInspector) {
      return;
    }
    assetInspector.hidden = true;
    assetInspector.setAttribute("aria-hidden", "true");
    if (restoreFocus && assetInspectorOpener) {
      assetInspectorOpener.focus();
    }
    assetInspectorOpener = null;
  }

  function initializeAssetInspectorControls() {
    assetInspectButtons.forEach((button) => {
      button.addEventListener("click", () => openAssetInspector(button));
    });
  }

  function printableDisclosureElements() {
    return Array.from(
      document.querySelectorAll(
        ".raya-static-environment, .raya-official-reveal, .raya-connection-preview"
      )
    ).filter((element) => element instanceof HTMLDetailsElement);
  }

  function openPrintDisclosures() {
    printableDisclosureElements().forEach((details) => {
      if (details.open) {
        return;
      }
      details.dataset.rayaPrintOpened = "true";
      details.open = true;
    });
  }

  function restorePrintDisclosures() {
    printableDisclosureElements().forEach((details) => {
      if (details.dataset.rayaPrintOpened !== "true") {
        return;
      }
      details.open = false;
      delete details.dataset.rayaPrintOpened;
    });
  }

  function syncPrintDisclosureState() {
    if (printQuery.matches) {
      openPrintDisclosures();
    } else {
      restorePrintDisclosures();
    }
  }

  desktopMapQuery.addEventListener("change", () => {
    hideCourseMapCompactPreview();
    setExpanded(defaultCourseMapExpanded());
    updateMapLinkTabOrder(root.dataset.rayaCourseMap === "expanded");
    if (!desktopMapQuery.matches) {
      setLearningRailExpanded(defaultLearningRailExpanded());
    } else {
      setLearningRailExpanded(true);
      closeLearningRailDrawer();
    }
    syncCourseMapDrawerState();
    syncLearningRailDrawerState();
  });
  if (structuralRailQuery.addEventListener) {
    structuralRailQuery.addEventListener("change", () => {
      if (!structuralRailQuery.matches) {
        setExpanded(true);
        setLearningRailExpanded(true);
      } else {
        closeCourseMapDrawer();
        closeLearningRailDrawer();
        setExpanded(defaultCourseMapExpanded());
        setLearningRailExpanded(defaultLearningRailExpanded());
      }
      syncCourseMapDrawerState();
      syncLearningRailDrawerState();
    });
  } else if (structuralRailQuery.addListener) {
    structuralRailQuery.addListener(() => {
      if (!structuralRailQuery.matches) {
        setExpanded(true);
        setLearningRailExpanded(true);
      } else {
        closeCourseMapDrawer();
        closeLearningRailDrawer();
        setExpanded(defaultCourseMapExpanded());
        setLearningRailExpanded(defaultLearningRailExpanded());
      }
      syncCourseMapDrawerState();
      syncLearningRailDrawerState();
    });
  }
  const handleCompactStructuralRailChange = () => {
    if (!isStructuralRailShell()) {
      return;
    }
    closeCourseMapDrawer();
    closeLearningRailDrawer();
    setExpanded(defaultCourseMapExpanded());
    setLearningRailExpanded(defaultLearningRailExpanded());
    syncCourseMapDrawerState();
    syncLearningRailDrawerState();
  };
  if (compactStructuralRailQuery.addEventListener) {
    compactStructuralRailQuery.addEventListener("change", handleCompactStructuralRailChange);
  } else if (compactStructuralRailQuery.addListener) {
    compactStructuralRailQuery.addListener(handleCompactStructuralRailChange);
  }
  const handleApprovedRailGeometryChange = () => {
    if (!isStructuralRailShell()) {
      return;
    }
    closeCourseMapDrawer();
    closeLearningRailDrawer();
    setExpanded(defaultCourseMapExpanded());
    setLearningRailExpanded(defaultLearningRailExpanded());
    syncCourseMapDrawerState();
    syncLearningRailDrawerState();
  };
  if (approvedRailGeometryQuery.addEventListener) {
    approvedRailGeometryQuery.addEventListener("change", handleApprovedRailGeometryChange);
  } else if (approvedRailGeometryQuery.addListener) {
    approvedRailGeometryQuery.addListener(handleApprovedRailGeometryChange);
  }
  if (printQuery.addEventListener) {
    printQuery.addEventListener("change", syncPrintDisclosureState);
  } else if (printQuery.addListener) {
    printQuery.addListener(syncPrintDisclosureState);
  }
  window.addEventListener("beforeprint", openPrintDisclosures);
  window.addEventListener("afterprint", restorePrintDisclosures);

  toggleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (!isStructuralRailShell()) {
        if (root.dataset.rayaCourseMapDrawer === "open") {
          closeCourseMapDrawer({ restoreFocus: true });
        } else {
          openCourseMapDrawer(button);
        }
        return;
      }
      const nextExpanded = root.dataset.rayaCourseMap !== "expanded";
      if (nextExpanded && isMediumStructuralShell()) {
        setLearningRailExpanded(false);
      }
      setExpanded(nextExpanded);
      if (root.dataset.rayaCourseMap !== "collapsed") {
        hideCourseMapCompactPreview();
      }
      if (root.dataset.rayaCourseMap === "expanded") {
        window.requestAnimationFrame(() =>
          orientCourseMapToCurrentPage({ repeat: true })
        );
      }
    });
  });

  if (mapCloseButton) {
    mapCloseButton.addEventListener("click", () => {
      closeCourseMapDrawer({ restoreFocus: true });
    });
  }

  if (mapDrawerBackdrop) {
    mapDrawerBackdrop.addEventListener("click", () => {
      closeCourseMapDrawer({ restoreFocus: true });
    });
  }

  if (learningRailDrawerBackdrop) {
    learningRailDrawerBackdrop.addEventListener("click", () => {
      closeLearningRailDrawer({ restoreFocus: true });
    });
  }

  const storedCollapsedMapBranches = loadStoredCollapsedMapBranches();
  const hasStoredMapBranchState = storedCollapsedMapBranches.size > 0;
  mapNodeToggles.forEach((button) => {
    const node = button.closest("[data-raya-map-node]");
    if (!node) {
      return;
    }
    const nodeId = mapNodeId(node);
    const defaultExpanded = button.getAttribute("aria-expanded") === "true";
    const restoredExpanded = hasStoredMapBranchState
      ? !storedCollapsedMapBranches.has(nodeId)
      : defaultExpanded;
    node.dataset.rayaMapExpanded = restoredExpanded ? "true" : "false";
    setMapNodeExpanded(node, restoredExpanded, {
      temporary: true,
      skipPersist: true,
    });
    button.addEventListener("click", () => {
      if (mapFilter) {
        mapFilter.value = "";
      }
      setMapNodeExpanded(node, button.getAttribute("aria-expanded") !== "true");
      applyCourseMapFilter();
    });
  });

  if (mapFilter) {
    mapFilter.addEventListener("input", () => {
      applyCourseMapFilter();
    });
    applyCourseMapFilter();
  }

  map.querySelectorAll("#raya-course-map-list a[href]").forEach((link) => {
    link.addEventListener("focus", () => {
      focusedCompactPreviewLink = root.dataset.rayaCourseMap === "collapsed" ? link : null;
      updateCourseMapCompactPreview();
    });
    link.addEventListener("blur", () => {
      if (focusedCompactPreviewLink === link) {
        focusedCompactPreviewLink = null;
      }
      updateCourseMapCompactPreview();
    });
    link.addEventListener("pointerenter", () => {
      hoveredCompactPreviewLink = root.dataset.rayaCourseMap === "collapsed" ? link : null;
      updateCourseMapCompactPreview();
    });
    link.addEventListener("pointerleave", () => {
      if (hoveredCompactPreviewLink === link) {
        hoveredCompactPreviewLink = null;
      }
      updateCourseMapCompactPreview();
    });
  });

  map.addEventListener("scroll", refreshCourseMapCompactPreview, { passive: true });
  window.addEventListener("resize", refreshCourseMapCompactPreview);

  map.addEventListener("keydown", handleCourseMapKeyboardNavigation);

  railToggleButtons.forEach((button) => {
    setRailPanelExpanded(button, button.getAttribute("aria-expanded") === "true");
    button.addEventListener("click", () => {
      setRailPanelExpanded(button, button.getAttribute("aria-expanded") !== "true");
    });
  });

  if (learningRailCollapse) {
    learningRailCollapse.addEventListener("click", () => {
      if (!isStructuralRailShell()) {
        closeLearningRailDrawer({ restoreFocus: true });
        return;
      }
      setLearningRailExpanded(false);
      if (learningRailExpand) {
        learningRailExpand.focus();
      }
    });
  }

  if (learningRailExpand) {
    learningRailExpand.addEventListener("click", () => {
      if (isMediumStructuralShell()) {
        setExpanded(false);
      }
      setLearningRailExpanded(true);
      if (learningRailCollapse) {
        learningRailCollapse.focus();
      }
    });
  }

  learningRailToggleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (!isStructuralRailShell()) {
        if (root.dataset.rayaCourseMapDrawer === "open") {
          closeCourseMapDrawer({ restoreFocus: false });
        }
        return;
      }
      const nextExpanded = root.dataset.rayaLearningRail !== "expanded";
      if (nextExpanded && isMediumStructuralShell()) {
        setExpanded(false);
      }
      setLearningRailExpanded(nextExpanded);
    });
  });

  document.addEventListener("keydown", (event) => {
    if (assetInspectorIsOpen()) {
      if (event.key === "Escape") {
        event.preventDefault();
        closeAssetInspector({ restoreFocus: true });
        return;
      }
      if (trapAssetInspectorFocus(event)) {
        return;
      }
    }
    if (handleSequenceKeyboardNavigation(event)) {
      return;
    }
    if (trapCourseMapDrawerFocus(event)) {
      return;
    }
    if (trapLearningRailDrawerFocus(event)) {
      return;
    }
    if (event.key === "Escape" && root.dataset.rayaCourseMapDrawer === "open") {
      closeCourseMapDrawer({ restoreFocus: true });
      return;
    }
    if (event.key === "Escape" && root.dataset.rayaLearningRailDrawer === "open") {
      closeLearningRailDrawer({ restoreFocus: true });
      return;
    }
    if (event.key === "Escape" && root.dataset.rayaCourseMap === "expanded") {
      const activeElement = document.activeElement;
      const shouldMoveFocus =
        activeElement instanceof Element &&
        map.contains(activeElement) &&
        !activeElement.matches("[data-raya-course-map-toggle]");
      setExpanded(false);
      if (shouldMoveFocus) {
        const mapToggle = map.querySelector("[data-raya-course-map-toggle]");
        if (mapToggle) {
          mapToggle.focus();
        }
      }
    }
    if (
      event.key === "Escape" &&
      isStructuralRailShell() &&
      root.dataset.rayaLearningRail === "expanded"
    ) {
      const activeElement = document.activeElement;
      const shouldMoveFocus =
        activeElement instanceof Element &&
        learningRail &&
        learningRail.contains(activeElement);
      if (shouldMoveFocus) {
        setLearningRailExpanded(false);
        if (learningRailExpand) {
          learningRailExpand.focus();
        }
      }
    }
  });

  function updateActiveHeading() {
    if (headings.length === 0) {
      return;
    }
    const activationLine = window.innerHeight * 0.3;
    const active = headings.reduce((current, item) => {
      const top = item.target.getBoundingClientRect().top;
      if (top <= activationLine) {
        return item;
      }
      return current;
    }, headings[0]);
    tocLinks.forEach((link) => link.removeAttribute("aria-current"));
    active.link.setAttribute("aria-current", "location");
    syncCurrentSection(active.link);
  }

  function syncCurrentSection(activeLink) {
    if (currentSectionLinks.length === 0 || !activeLink) {
      return;
    }
    const href = activeLink.getAttribute("href") || "";
    if (href.startsWith("#raya-generated-")) {
      return;
    }
    const label = activeLink.textContent || "Current section";
    currentSectionLinks.forEach((currentSectionLink) => {
      const isCommandChip = currentSectionLink.classList.contains("raya-reading-context-section");
      const nextLabel = isCommandChip ? `Current section: ${label}` : label;
      if (currentSectionLink.getAttribute("href") !== href) {
        currentSectionLink.setAttribute("href", href);
      }
      if (isCommandChip) {
        const visibleLabel = currentSectionLink.querySelector(".raya-reading-context-section-label");
        if (visibleLabel && visibleLabel.textContent !== label) {
          visibleLabel.textContent = label;
        } else if (!visibleLabel && currentSectionLink.textContent !== `Now ${label}`) {
          currentSectionLink.textContent = `Now ${label}`;
        }
      } else if (currentSectionLink.textContent !== label) {
        currentSectionLink.textContent = label;
      }
      if (currentSectionLink.getAttribute("aria-label") !== nextLabel) {
        currentSectionLink.setAttribute("aria-label", nextLabel);
      }
    });
  }

  function setActiveKeyObject(id) {
    keyObjectLinks.forEach((link) => {
      const isActive = Boolean(id) && link.getAttribute("data-raya-key-object-link") === id;
      if (isActive) {
        link.setAttribute("aria-current", "location");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  }

  function initializeOfficialQuizControls() {
    const questions = Array.from(document.querySelectorAll("[data-raya-official-quiz-question]"));
    questions.forEach((question) => {
      const options = Array.from(
        question.querySelectorAll("[data-raya-official-quiz-option]")
      );
      const reset = question.querySelector("[data-raya-official-quiz-reset]");
      const feedback = question.querySelector("[data-raya-official-quiz-feedback]");
      if (options.length === 0 || !reset || !feedback) {
        return;
      }

      function setReady() {
        question.setAttribute("data-raya-official-quiz-state", "ready");
        options.forEach((option) => {
          option.disabled = false;
          option.removeAttribute("aria-pressed");
          option.removeAttribute("data-raya-official-quiz-selected");
          option.removeAttribute("data-raya-official-quiz-result");
        });
        reset.hidden = true;
        feedback.textContent = "Choose an option.";
      }

      options.forEach((option) => {
        option.addEventListener("click", () => {
          const isCorrect =
            option.getAttribute("data-raya-official-quiz-correct") === "true";
          question.setAttribute("data-raya-official-quiz-state", "answered");
          options.forEach((candidate) => {
            const candidateCorrect =
              candidate.getAttribute("data-raya-official-quiz-correct") === "true";
            candidate.disabled = true;
            candidate.setAttribute(
              "aria-pressed",
              candidate === option ? "true" : "false"
            );
            candidate.removeAttribute("data-raya-official-quiz-selected");
            candidate.removeAttribute("data-raya-official-quiz-result");
            if (candidate === option) {
              candidate.setAttribute("data-raya-official-quiz-selected", "true");
            }
            if (candidateCorrect) {
              candidate.setAttribute("data-raya-official-quiz-result", "correct");
            }
          });
          if (!isCorrect) {
            option.setAttribute("data-raya-official-quiz-result", "incorrect");
          }
          feedback.textContent = isCorrect
            ? "Correct."
            : "Try again. The correct option is available below.";
          reset.hidden = false;
        });
      });

      reset.addEventListener("click", setReady);
      setReady();
    });
  }

  if (headings.length > 0) {
    updateActiveHeading();
    window.addEventListener("scroll", updateActiveHeading, { passive: true });
    window.addEventListener("resize", updateActiveHeading);
  }
  if (keyObjectLinks.length > 0 && keyObjectTargets.length > 0 && "IntersectionObserver" in window) {
    const activeObjects = new Set();
    const objectObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          activeObjects.add(entry.target.id);
        } else {
          activeObjects.delete(entry.target.id);
        }
      });
      const activeTarget = keyObjectTargets.find((target) => activeObjects.has(target.id));
      setActiveKeyObject(activeTarget ? activeTarget.id : "");
    }, { rootMargin: "-20% 0px -55% 0px", threshold: 0 });
    keyObjectTargets.forEach((target) => objectObserver.observe(target));
  }

  setExpanded(defaultCourseMapExpanded());
  setLearningRailExpanded(defaultLearningRailExpanded());
  root.dataset.rayaLearningRailDrawer = "closed";
  window.requestAnimationFrame(() => orientCourseMapToCurrentPage());
  initializeCodeCopyControls();
  initializeAssetInspectorControls();
  initializeOfficialQuizControls();
  syncCourseMapDrawerState();
  syncLearningRailDrawerState();
  root.dataset.rayaShellReady = "true";
})();
"""
