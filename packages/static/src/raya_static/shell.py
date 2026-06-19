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
  const railToggleButtons = Array.from(document.querySelectorAll("[data-raya-rail-toggle]"));
  const desktopMapQuery = window.matchMedia("(min-width: 901px)");
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
      .querySelectorAll("a[href], button, input, select, textarea, [tabindex]")
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

  function setExpanded(nextExpanded) {
    root.dataset.rayaCourseMap = nextExpanded ? "expanded" : "collapsed";
    shell.dataset.rayaCourseMap = nextExpanded ? "expanded" : "collapsed";
    map.dataset.rayaCourseMap = nextExpanded ? "expanded" : "collapsed";
    toggleButtons.forEach((button) => {
      button.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
      button.setAttribute(
        "aria-label",
        nextExpanded ? "Collapse course map" : "Expand course map"
      );
      if (map.contains(button)) {
        button.textContent = nextExpanded ? "Collapse map" : "Expand map";
      }
    });
    updateMapLinkTabOrder(nextExpanded);
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
    body.inert = !nextExpanded;
    setFocusableDescendantsEnabled(body, nextExpanded);
  }

  desktopMapQuery.addEventListener("change", () => {
    updateMapLinkTabOrder(root.dataset.rayaCourseMap === "expanded");
  });

  toggleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setExpanded(root.dataset.rayaCourseMap !== "expanded");
    });
  });

  railToggleButtons.forEach((button) => {
    setRailPanelExpanded(button, button.getAttribute("aria-expanded") === "true");
    button.addEventListener("click", () => {
      setRailPanelExpanded(button, button.getAttribute("aria-expanded") !== "true");
    });
  });

  document.addEventListener("keydown", (event) => {
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
  root.dataset.rayaShellReady = "true";
})();
"""
