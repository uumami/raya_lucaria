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
  const STORAGE_KEY = "raya.courseMapExpanded";
  const root = document.documentElement;
  const shell = document.querySelector(".raya-learning-shell");
  const map = document.querySelector("#raya-course-map");
  const toggleButtons = Array.from(document.querySelectorAll("[data-raya-course-map-toggle]"));
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

  const stored = window.localStorage.getItem(STORAGE_KEY);
  const expanded = stored === "true";

  function updateMapLinkTabOrder(nextExpanded) {
    const hideLinks = !nextExpanded;
    if (desktopMapQuery.matches) {
      map.removeAttribute("tabindex");
    } else {
      map.setAttribute("tabindex", "-1");
    }
    map.querySelectorAll("a").forEach((link) => {
      if (hideLinks) {
        link.setAttribute("tabindex", "-1");
      } else {
        link.removeAttribute("tabindex");
      }
    });
  }

  function setExpanded(nextExpanded, persist = true) {
    root.dataset.rayaCourseMap = nextExpanded ? "expanded" : "collapsed";
    shell.dataset.rayaCourseMap = nextExpanded ? "expanded" : "collapsed";
    map.dataset.rayaCourseMap = nextExpanded ? "expanded" : "collapsed";
    toggleButtons.forEach((button) => {
      button.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
    });
    updateMapLinkTabOrder(nextExpanded);
    if (persist) {
      window.localStorage.setItem(STORAGE_KEY, nextExpanded ? "true" : "false");
    }
  }

  desktopMapQuery.addEventListener("change", () => {
    updateMapLinkTabOrder(root.dataset.rayaCourseMap === "expanded");
  });

  toggleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setExpanded(root.dataset.rayaCourseMap !== "expanded");
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && root.dataset.rayaCourseMap === "expanded") {
      setExpanded(false);
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

  setExpanded(expanded, false);
})();
"""
