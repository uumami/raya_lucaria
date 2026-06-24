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
  const toggleButtons = Array.from(document.querySelectorAll("[data-raya-course-map-toggle]"));
  const learningRail = document.querySelector("#raya-learning-rail");
  const learningRailBody = document.querySelector("#raya-learning-rail-body");
  const learningRailCollapse = document.querySelector("[data-raya-learning-rail-collapse]");
  const learningRailExpand = document.querySelector("[data-raya-learning-rail-expand]");
  const railToggleButtons = Array.from(document.querySelectorAll("[data-raya-rail-toggle]"));
  const mapNodeToggles = Array.from(document.querySelectorAll("[data-raya-map-node-toggle]"));
  const mapFilter = document.querySelector("[data-raya-course-map-filter]");
  const mapFilterEmpty = document.querySelector("[data-raya-map-filter-empty]");
  const desktopMapQuery = window.matchMedia("(min-width: 1280px)");
  const tocLinks = Array.from(document.querySelectorAll(".raya-page-toc a[href^='#']"));
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

  function updateMapLinkTabOrder(nextExpanded) {
    const mapList = map.querySelector("#raya-course-map-list");
    if (mapList) {
      mapList.setAttribute("aria-hidden", "false");
      mapList.inert = false;
    }
    if (desktopMapQuery.matches) {
      map.removeAttribute("tabindex");
    } else {
      map.setAttribute("tabindex", "-1");
    }
    map.querySelectorAll("a").forEach((link) => {
      link.removeAttribute("tabindex");
    });
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

  function setExpanded(nextExpanded) {
    if (!nextExpanded && mapFilter && mapFilter.value) {
      mapFilter.value = "";
      applyCourseMapFilter();
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
    updateMapLinkTabOrder(nextExpanded);
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
        node.getAttribute("data-raya-map-node") || "",
      ].join(" ")
    );
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

  function orientCourseMapToCurrentPage(options = {}) {
    const mapList = map.querySelector("#raya-course-map-list");
    const currentLink = mapList
      ? mapList.querySelector('a[aria-current="page"]')
      : null;
    const scrollContainer = map;
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
    const containerRect = scrollContainer.getBoundingClientRect();
    const linkRect = currentLink.getBoundingClientRect();
    const isVisible =
      linkRect.top >= containerRect.top && linkRect.bottom <= containerRect.bottom;
    if (!isVisible) {
      const offset =
        scrollContainer.scrollTop +
        linkRect.top -
        containerRect.top -
        scrollContainer.clientHeight / 2 +
        currentLink.offsetHeight / 2;
      scrollContainer.scrollTop = Math.max(0, offset);
      const adjustedContainerRect = scrollContainer.getBoundingClientRect();
      const adjustedLinkRect = currentLink.getBoundingClientRect();
      if (adjustedLinkRect.top < adjustedContainerRect.top) {
        scrollContainer.scrollTop = Math.max(
          0,
          scrollContainer.scrollTop + adjustedLinkRect.top - adjustedContainerRect.top
        );
      } else if (adjustedLinkRect.bottom > adjustedContainerRect.bottom) {
        scrollContainer.scrollTop = Math.max(
          0,
          scrollContainer.scrollTop + adjustedLinkRect.bottom - adjustedContainerRect.bottom
        );
      }
    }
    scrollContainer.dataset.rayaCourseMapOriented = "true";
    return true;
  }

  window.rayaOrientCourseMapToCurrentPage = () =>
    orientCourseMapToCurrentPage({ force: true });
  window.rayaOrientCourseMapToCurrentPageAutomatic = () =>
    orientCourseMapToCurrentPage({ repeat: true });

  function setLearningRailExpanded(nextExpanded) {
    if (!learningRail || !learningRailBody) {
      return;
    }
    root.dataset.rayaLearningRail = nextExpanded ? "expanded" : "collapsed";
    shell.dataset.rayaLearningRail = nextExpanded ? "expanded" : "collapsed";
    learningRail.dataset.rayaLearningRail = nextExpanded ? "expanded" : "collapsed";
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

  desktopMapQuery.addEventListener("change", () => {
    updateMapLinkTabOrder(root.dataset.rayaCourseMap === "expanded");
    if (!desktopMapQuery.matches) {
      setLearningRailExpanded(true);
    }
  });

  toggleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setExpanded(root.dataset.rayaCourseMap !== "expanded");
      if (root.dataset.rayaCourseMap === "expanded") {
        window.requestAnimationFrame(() =>
          orientCourseMapToCurrentPage({ repeat: true })
        );
      }
    });
  });

  mapNodeToggles.forEach((button) => {
    const node = button.closest("[data-raya-map-node]");
    if (!node) {
      return;
    }
    node.dataset.rayaMapExpanded = button.getAttribute("aria-expanded") === "true" ? "true" : "false";
    button.addEventListener("click", () => {
      if (mapFilter) {
        mapFilter.value = "";
      }
      setMapNodeExpanded(node, button.getAttribute("aria-expanded") !== "true");
      applyCourseMapFilter();
    });
  });

  if (mapFilter) {
    mapFilter.addEventListener("input", applyCourseMapFilter);
    applyCourseMapFilter();
  }

  railToggleButtons.forEach((button) => {
    setRailPanelExpanded(button, button.getAttribute("aria-expanded") === "true");
    button.addEventListener("click", () => {
      setRailPanelExpanded(button, button.getAttribute("aria-expanded") !== "true");
    });
  });

  if (learningRailCollapse) {
    learningRailCollapse.addEventListener("click", () => {
      setLearningRailExpanded(false);
      if (learningRailExpand) {
        learningRailExpand.focus();
      }
    });
  }

  if (learningRailExpand) {
    learningRailExpand.addEventListener("click", () => {
      setLearningRailExpanded(true);
      if (learningRailCollapse) {
        learningRailCollapse.focus();
      }
    });
  }

  document.addEventListener("keydown", (event) => {
    if (handleSequenceKeyboardNavigation(event)) {
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
    if (event.key === "Escape" && root.dataset.rayaLearningRail === "expanded") {
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
  }

  if (headings.length > 0) {
    updateActiveHeading();
    window.addEventListener("scroll", updateActiveHeading, { passive: true });
    window.addEventListener("resize", updateActiveHeading);
  }

  setExpanded(true);
  setLearningRailExpanded(true);
  window.requestAnimationFrame(() => orientCourseMapToCurrentPage());
  initializeCodeCopyControls();
  root.dataset.rayaShellReady = "true";
})();
"""
