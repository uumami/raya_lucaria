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
      const target = document.querySelector(link.getAttribute("href"));
      return target ? { link, target } : null;
    })
    .filter(Boolean);

  if (!shell || !map || toggleButtons.length === 0) {
    return;
  }

  const stored = window.localStorage.getItem(STORAGE_KEY);
  const expanded = stored === "true";

  function updateMapLinkTabOrder(nextExpanded) {
    const hideLinks = !nextExpanded && desktopMapQuery.matches;
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

  if ("IntersectionObserver" in window && headings.length > 0) {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((left, right) => left.boundingClientRect.top - right.boundingClientRect.top)[0];
        if (!visible) {
          return;
        }
        tocLinks.forEach((link) => link.removeAttribute("aria-current"));
        const active = headings.find((item) => item.target === visible.target);
        if (active) {
          active.link.setAttribute("aria-current", "location");
        }
      },
      { rootMargin: "-20% 0px -65% 0px", threshold: [0, 1] }
    );
    headings.forEach((item) => observer.observe(item.target));
  }

  setExpanded(expanded, false);
})();
"""
