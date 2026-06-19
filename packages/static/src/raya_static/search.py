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
  const clear = document.getElementById("raya-search-clear");
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
  let activeIndex = -1;
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

  function visibleResults() {
    return results.filter((item) => !item.hidden);
  }

  function setActiveResult(nextIndex) {
    const visible = visibleResults();
    if (visible.length === 0) {
      activeIndex = -1;
    } else {
      activeIndex = Math.max(-1, Math.min(nextIndex, visible.length - 1));
    }
    results.forEach((item) => {
      item.dataset.rayaSearchActive = "false";
      item.setAttribute("data-raya-search-active", "false");
    });
    if (activeIndex >= 0 && visible[activeIndex]) {
      visible[activeIndex].dataset.rayaSearchActive = "true";
      visible[activeIndex].setAttribute("data-raya-search-active", "true");
    }
  }

  function clearSearch() {
    input.value = "";
    activeIndex = -1;
    render();
    input.focus();
  }

  function render() {
    const query = normalize(input.value);
    let visible = 0;
    results.forEach((item) => {
      const id = item.getAttribute("data-raya-search-result") || "";
      const text = pageText.get(id);
      const matched = text ? fuzzyMatch(query, text) : false;
      item.hidden = !matched;
      if (matched) visible += 1;
    });
    setActiveResult(Math.min(activeIndex, visible - 1));
    if (empty) {
      empty.hidden = visible !== 0;
    }
    if (status) {
      status.textContent = `${visible} visible result(s).`;
    }
  }

  input.addEventListener("input", () => {
    activeIndex = -1;
    render();
  });
  input.addEventListener("keydown", (event) => {
    const visible = visibleResults();
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveResult(visible.length === 0 ? -1 : (activeIndex + 1) % visible.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      const next = activeIndex <= 0 ? visible.length - 1 : activeIndex - 1;
      setActiveResult(visible.length === 0 ? -1 : next);
    } else if (event.key === "Enter" && activeIndex >= 0 && visible[activeIndex]) {
      const link = visible[activeIndex].querySelector("a");
      if (link && link.href) {
        event.preventDefault();
        window.location.href = link.href;
      }
    } else if (event.key === "Escape") {
      event.preventDefault();
      clearSearch();
    }
  });
  if (clear) {
    clear.addEventListener("click", clearSearch);
  }
  render();
})();
"""
