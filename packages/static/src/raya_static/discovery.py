from __future__ import annotations

from dataclasses import dataclass


DISCOVERY_SCRIPT_NAME = "discovery.js"
DISCOVERY_RESOURCE_PATH = "_raya/render"


@dataclass(frozen=True)
class DiscoveryResources:
    javascript: str


def discovery_resources() -> DiscoveryResources:
    return DiscoveryResources(javascript=_DISCOVERY_JAVASCRIPT)


_DISCOVERY_JAVASCRIPT = r"""
(() => {
  const roots = Array.from(document.querySelectorAll("[data-raya-discovery-page]"));

  if (roots.length === 0) {
    return;
  }

  function normalizePanelName(value) {
    return value === "context" ? "context" : "controls";
  }

  function stateAttribute(panelName) {
    return panelName === "context"
      ? "data-raya-discovery-context-state"
      : "data-raya-discovery-controls-state";
  }

  function stateDatasetName(panelName) {
    return panelName === "context"
      ? "rayaDiscoveryContextState"
      : "rayaDiscoveryControlsState";
  }

  function setPanelFocusable(body, expanded) {
    if (!body) {
      return;
    }
    const focusable = Array.from(
      body.querySelectorAll("a[href], button, input, select, textarea, summary, [tabindex]")
    );
    focusable.forEach((node) => {
      if (expanded) {
        if (node.dataset.rayaDiscoveryPreviousTabindex !== undefined) {
          const previous = node.dataset.rayaDiscoveryPreviousTabindex;
          if (previous === "") {
            node.removeAttribute("tabindex");
          } else {
            node.setAttribute("tabindex", previous);
          }
          delete node.dataset.rayaDiscoveryPreviousTabindex;
        }
        return;
      }
      if (node.dataset.rayaDiscoveryPreviousTabindex === undefined) {
        node.dataset.rayaDiscoveryPreviousTabindex = node.getAttribute("tabindex") || "";
      }
      node.setAttribute("tabindex", "-1");
    });
  }

  function panelRailSummaryText(body, panelName) {
    if (!body) {
      return panelName === "context" ? "Context ready." : "Controls ready.";
    }
    const source = panelName === "context"
      ? body.querySelector(
          "[data-raya-search-context-title], " +
          "[data-raya-practice-context-title], " +
          "[data-raya-tasks-context-title], " +
          "[data-raya-schedule-context-title]"
        )
      : body.querySelector(".raya-discovery-summary");
    const text = source ? source.textContent.trim() : "";
    if (text) {
      return text;
    }
    return panelName === "context" ? "Context ready." : "Controls ready.";
  }

  function updatePanelRailSummary(root, panelName) {
    const body = root.querySelector(`[data-raya-discovery-panel-body="${panelName}"]`);
    const collapsed = root.getAttribute(stateAttribute(panelName)) === "collapsed";
    root
      .querySelectorAll(`[data-raya-discovery-panel-rail-summary="${panelName}"]`)
      .forEach((summary) => {
        summary.textContent = panelRailSummaryText(body, panelName);
        summary.setAttribute("aria-hidden", collapsed ? "false" : "true");
      });
  }

  function setPanelState(root, panelName, expanded) {
    const state = expanded ? "expanded" : "collapsed";
    const body = root.querySelector(`[data-raya-discovery-panel-body="${panelName}"]`);
    root.setAttribute(stateAttribute(panelName), state);
    root.dataset[stateDatasetName(panelName)] = state;
    updatePanelRailSummary(root, panelName);
    if (body) {
      body.setAttribute("aria-hidden", expanded ? "false" : "true");
      setPanelFocusable(body, expanded);
    }
    root
      .querySelectorAll(`[data-raya-discovery-toggle-panel="${panelName}"]`)
      .forEach((button) => {
        button.setAttribute("aria-expanded", expanded ? "true" : "false");
        button.setAttribute(
          "aria-label",
          `${expanded ? "Collapse" : "Expand"} ${panelName} panel`
        );
        button.textContent = expanded ? "Collapse" : "Expand";
      });
  }

  roots.forEach((root) => {
    const railBody = root.querySelector("[data-raya-discovery-course-rail-body]");
    const railToggle = root.querySelector("[data-raya-discovery-toggle-rail]");
    const railPageLinks = Array.from(
      root.querySelectorAll("[data-raya-discovery-course-page]")
    );
    const railPageFocus = root.querySelector("[data-raya-discovery-rail-page-focus]");
    const railPageFocusTitle = root.querySelector(
      "[data-raya-discovery-rail-page-focus-title]"
    );
    const railPageHandoffs = Array.from(
      root.querySelectorAll("[data-raya-discovery-rail-page-handoff]")
    );
    const focusStrip = root.querySelector("[data-raya-discovery-focus-strip]");
    const focusTitle = root.querySelector("[data-raya-discovery-focus-title]");
    const focusPageLink = root.querySelector("[data-raya-discovery-focus-page-link]");
    const focusHandoffs = Array.from(
      root.querySelectorAll("[data-raya-discovery-focus-handoff]")
    );
    const desktopRailQuery = window.matchMedia
      ? window.matchMedia("(min-width: 1280px)")
      : null;
    let activeRailPage = "";
    function hideFocusStrip() {
      if (!focusStrip) {
        return;
      }
      focusStrip.hidden = true;
      if (focusTitle) {
        focusTitle.textContent = "";
      }
      if (focusPageLink) {
        focusPageLink.setAttribute("href", "#");
      }
      focusHandoffs.forEach((link) => {
        link.setAttribute("href", "#");
      });
    }
    function setRailExpanded(expanded) {
      root.setAttribute(
        "data-raya-discovery-rail-state",
        expanded ? "expanded" : "collapsed"
      );
      if (railBody) {
        railBody.setAttribute("aria-hidden", expanded ? "false" : "true");
        setPanelFocusable(railBody, expanded);
      }
      if (railToggle) {
        railToggle.setAttribute("aria-expanded", expanded ? "true" : "false");
        railToggle.setAttribute(
          "aria-label",
          expanded ? "Collapse course workspace" : "Expand course workspace"
        );
      }
    }
    function syncRailViewport() {
      if (desktopRailQuery && !desktopRailQuery.matches) {
        setRailExpanded(true);
      }
    }
    if (railBody && railToggle) {
      setRailExpanded(true);
      railToggle.addEventListener("click", () => {
        setRailExpanded(
          root.getAttribute("data-raya-discovery-rail-state") === "collapsed"
        );
      });
      syncRailViewport();
      if (desktopRailQuery) {
        if (typeof desktopRailQuery.addEventListener === "function") {
          desktopRailQuery.addEventListener("change", syncRailViewport);
        } else if (typeof desktopRailQuery.addListener === "function") {
          desktopRailQuery.addListener(syncRailViewport);
        }
      }
    }
    try {
      activeRailPage = new URLSearchParams(window.location.search || "").get("page") || "";
    } catch {
      activeRailPage = "";
    }
    if (activeRailPage && railPageLinks.length > 0) {
      const focused = railPageLinks.find(
        (link) => link.getAttribute("data-raya-discovery-course-page") === activeRailPage
      );
      if (focused) {
        focused.setAttribute("data-raya-rail-page-focus", "true");
        const title = focused.querySelector("strong")?.textContent?.trim() || activeRailPage;
        if (railPageFocusTitle) {
          railPageFocusTitle.textContent = title;
        }
        if (railPageFocus) {
          railPageFocus.hidden = false;
        }
        railPageHandoffs.forEach((link) => {
          const base = link.getAttribute("data-raya-handoff-base") || "";
          if (!base) return;
          link.setAttribute("href", `${base}?page=${encodeURIComponent(activeRailPage)}`);
        });
        const pageHref = focused.getAttribute("href") || "#";
        if (focusTitle) {
          focusTitle.textContent = title;
        }
        if (focusPageLink) {
          focusPageLink.setAttribute("href", pageHref);
        }
        focusHandoffs.forEach((link) => {
          const base = link.getAttribute("data-raya-handoff-base") || "";
          if (!base) return;
          link.setAttribute("href", `${base}?page=${encodeURIComponent(activeRailPage)}`);
        });
        if (focusStrip) {
          focusStrip.hidden = false;
        }
      }
    }
    ["controls", "context"].forEach((panelName) => {
      const body = root.querySelector(`[data-raya-discovery-panel-body="${panelName}"]`);
      updatePanelRailSummary(root, panelName);
      if (body && typeof MutationObserver === "function") {
        new MutationObserver(() => updatePanelRailSummary(root, panelName)).observe(
          body,
          {
            attributes: true,
            attributeFilter: ["hidden"],
            characterData: true,
            childList: true,
            subtree: true,
          }
        );
      }
    });
    root.querySelectorAll("[data-raya-discovery-toggle-panel]").forEach((button) => {
      const panelName = normalizePanelName(
        button.getAttribute("data-raya-discovery-toggle-panel") || ""
      );
      button.addEventListener("click", () => {
        const expanded = root.getAttribute(stateAttribute(panelName)) !== "collapsed";
        setPanelState(root, panelName, !expanded);
      });
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        hideFocusStrip();
      }
    });
  });
})();
"""
