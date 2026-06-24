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
  const summaryCount = document.querySelector("[data-raya-search-summary-count]");
  const contextTitle = document.querySelector("[data-raya-search-context-title]");
  const contextMeta = document.querySelector("[data-raya-search-context-meta]");
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
  const pagesById = new Map(pages.map((page) => [page.id, page]));
  let activeIndex = -1;
  let activePage = "";
  const pageText = new Map(
    pages.map((page) => [
      page.id,
      normalize([
        page.id,
        page.stable_id,
        page.title,
        page.nav_title,
        page.summary,
        page.status,
        page.hierarchy_label,
        page.link_counts
          ? `${page.link_counts.outgoing} ${page.link_counts.incoming} ${page.link_counts.connected}`
          : "",
        page.study_counts
          ? Object.keys(page.study_counts).join(" ")
          : "",
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

  function matchesPage(item) {
    return !activePage ||
      (item.getAttribute("data-raya-search-result") || "") === activePage;
  }

  function indexForResult(item) {
    return visibleResults().indexOf(item);
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
    updateContext();
  }

  function pageForResult(item) {
    if (!item) return null;
    const id = item.getAttribute("data-raya-search-result") || "";
    return pagesById.get(id) || null;
  }

  function bestContextItem(visible) {
    if (activeIndex >= 0) {
      return visible[activeIndex];
    }
    const query = normalize(input.value);
    if (!query) {
      return visible[0];
    }
    return visible.find((item) => {
      const page = pageForResult(item);
      if (!page) return false;
      return normalize([
        page.id,
        page.stable_id,
        page.title,
        page.nav_title,
      ].join(" ")).includes(query);
    }) || visible[0];
  }

  function updateContext() {
    const visible = visibleResults();
    const selectedItem = bestContextItem(visible);
    const page = pageForResult(selectedItem);
    if (summaryCount) {
      summaryCount.textContent = `${visible.length} visible result(s).`;
    }
    if (!page) {
      if (contextTitle) contextTitle.textContent = "No visible result.";
      if (contextMeta) contextMeta.textContent = "Try a different page title, stable ID, tag, or status.";
      return;
    }
    const counts = page.link_counts || {};
    const studyCounts = page.study_counts || {};
    const studyTotal = Object.keys(studyCounts).reduce(
      (total, key) => total + Number(studyCounts[key] || 0),
      0
    );
    if (contextTitle) {
      contextTitle.textContent = page.title || page.nav_title || page.id || "Visible page";
    }
    if (contextMeta) {
      contextMeta.textContent = [
        page.hierarchy_label || "",
        page.status ? `Status ${page.status}` : "",
        `Explicit links: ${counts.outgoing || 0} outgoing, ${counts.incoming || 0} incoming`,
        `Official objects: ${studyTotal}`,
      ].filter(Boolean).join(" | ");
    }
  }

  function clearSearch() {
    input.value = "";
    activePage = "";
    activeIndex = -1;
    render();
    input.focus();
  }

  function initialParams() {
    try {
      const params = new URLSearchParams(window.location.search || "");
      return {
        page: params.get("page") || "",
        query: params.get("q") || "",
      };
    } catch {
      return { page: "", query: "" };
    }
  }

  function render() {
    const query = normalize(input.value);
    let visible = 0;
    results.forEach((item) => {
      const id = item.getAttribute("data-raya-search-result") || "";
      const text = pageText.get(id);
      const matched = matchesPage(item) && (text ? fuzzyMatch(query, text) : false);
      item.hidden = !matched;
      if (matched) visible += 1;
    });
    if (activePage) {
      const visibleItems = visibleResults();
      activeIndex = visibleItems.findIndex((item) => (
        (item.getAttribute("data-raya-search-result") || "") === activePage
      ));
    }
    setActiveResult(Math.min(activeIndex, visible - 1));
    if (empty) {
      empty.hidden = visible !== 0;
    }
    if (status) {
      status.textContent = `${visible} visible result(s).`;
    }
  }

  results.forEach((item) => {
    item.addEventListener("focusin", () => {
      setActiveResult(indexForResult(item));
    });
    item.addEventListener("pointerenter", () => {
      setActiveResult(indexForResult(item));
    });
  });

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
  const params = initialParams();
  activePage = params.page;
  input.value = params.query;
  render();
})();
"""
