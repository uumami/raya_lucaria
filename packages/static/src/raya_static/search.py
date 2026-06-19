from __future__ import annotations

from dataclasses import dataclass


SEARCH_SCRIPT_NAME = "search.js"
SEARCH_RESOURCE_PATH = "_raya/render"


@dataclass(frozen=True)
class SearchResources:
    javascript: str


def search_resources() -> SearchResources:
    return SearchResources(javascript=_SEARCH_JAVASCRIPT)


_SEARCH_JAVASCRIPT = r"""
(() => {
  const root = document.querySelector("[data-raya-search-page]");
  const dataEl = document.getElementById("raya-search-data");
  const input = document.getElementById("raya-search-input");
  const status = document.getElementById("raya-search-status");
  const results = Array.from(document.querySelectorAll("[data-raya-search-result]"));
  const empty = document.getElementById("raya-search-empty");

  if (!root || !dataEl || !input || results.length === 0) {
    return;
  }

  let payload;
  try {
    payload = JSON.parse(dataEl.textContent || "{}");
  } catch {
    if (status) status.textContent = "Search data could not be read.";
    return;
  }

  function normalize(value) {
    return String(value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }

  const pages = Array.isArray(payload.pages) ? payload.pages : [];
  const pageText = new Map(
    pages.map((page) => [
      page.id,
      normalize([
        page.id,
        page.title,
        page.nav_title,
        page.summary,
        page.status,
        page.hierarchy_label,
        ...(Array.isArray(page.tags) ? page.tags : []),
      ].join(" ")),
    ])
  );

  function matches(text, query) {
    if (!query) return true;
    return text.includes(query) || text.split(/\s+/).some((word) => word.startsWith(query));
  }

  function render() {
    const query = normalize(input.value);
    let visible = 0;
    results.forEach((item) => {
      const id = item.getAttribute("data-raya-search-result") || "";
      const text = pageText.get(id);
      const matched = text ? matches(text, query) : false;
      item.hidden = !matched;
      if (matched) visible += 1;
    });
    if (empty) {
      empty.hidden = visible !== 0;
    }
    if (status) {
      status.textContent = `${visible} visible result(s).`;
    }
  }

  input.addEventListener("input", render);
  render();
})();
"""
