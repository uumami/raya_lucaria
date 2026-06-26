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
  const collapseMedia = window.matchMedia("(min-width: 1280px)");

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

  function setPanelState(root, panelName, expanded) {
    const state = expanded ? "expanded" : "collapsed";
    const body = root.querySelector(`[data-raya-discovery-panel-body="${panelName}"]`);
    root.setAttribute(stateAttribute(panelName), state);
    root.dataset[stateDatasetName(panelName)] = state;
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
    root.querySelectorAll("[data-raya-discovery-toggle-panel]").forEach((button) => {
      const panelName = normalizePanelName(
        button.getAttribute("data-raya-discovery-toggle-panel") || ""
      );
      button.addEventListener("click", () => {
        if (!collapseMedia.matches) {
          setPanelState(root, panelName, true);
          return;
        }
        const expanded = root.getAttribute(stateAttribute(panelName)) !== "collapsed";
        setPanelState(root, panelName, !expanded);
      });
    });
  });

  function restoreSmallViewportPanels() {
    if (collapseMedia.matches) {
      return;
    }
    roots.forEach((root) => {
      setPanelState(root, "controls", true);
      setPanelState(root, "context", true);
    });
  }

  if (typeof collapseMedia.addEventListener === "function") {
    collapseMedia.addEventListener("change", restoreSmallViewportPanels);
  } else if (typeof collapseMedia.addListener === "function") {
    collapseMedia.addListener(restoreSmallViewportPanels);
  }
  restoreSmallViewportPanels();
})();
"""
