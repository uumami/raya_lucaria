from __future__ import annotations

from dataclasses import dataclass


PRACTICE_SCRIPT_NAME = "practice.js"
PRACTICE_RESOURCE_PATH = "_raya/render"


@dataclass(frozen=True)
class PracticeResources:
    javascript: str


def practice_resources() -> PracticeResources:
    return PracticeResources(javascript=_PRACTICE_JAVASCRIPT)


_PRACTICE_JAVASCRIPT = r"""
(() => {
  const root = document.querySelector("[data-raya-practice-page]");
  const dataEl = document.getElementById("raya-practice-data");
  const input = document.getElementById("raya-practice-search");
  const clear = document.getElementById("raya-practice-clear");
  const status = document.getElementById("raya-practice-status");
  const empty = document.getElementById("raya-practice-empty");
  const summaryCount = document.querySelector("[data-raya-practice-summary-count]");
  const pageFocusNotice = document.querySelector("[data-raya-practice-page-focus]");
  const contextTitle = document.querySelector("[data-raya-practice-context-title]");
  const contextMeta = document.querySelector("[data-raya-practice-context-meta]");
  const contextActions = document.querySelector("[data-raya-practice-context-actions]");
  const filters = Array.from(document.querySelectorAll("[data-raya-practice-filter]"));
  const objects = Array.from(document.querySelectorAll("[data-raya-practice-object]"));
  const groups = Array.from(document.querySelectorAll("[data-raya-practice-group]"));

  if (!root || !dataEl || !input) {
    return;
  }

  let payload;
  try {
    payload = JSON.parse(dataEl.textContent || "{}");
  } catch {
    if (status) status.textContent = "Practice data could not be read.";
    return;
  }

  function normalize(value) {
    return String(value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }

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

  function fuzzyTermMatch(term, words, haystack) {
    if (words.some((word) => word.startsWith(term))) return true;
    const threshold = term.length <= 3 ? 1 : Math.floor(term.length * 0.35);
    return words.some((word) => levenshtein(term, word) <= threshold) ||
      (haystack.length <= 28 && levenshtein(term, haystack) <= threshold);
  }

  function fuzzyMatch(queryText, targetText) {
    const needle = normalize(queryText);
    const haystack = normalize(targetText);
    if (!needle) return true;
    if (haystack.includes(needle)) return true;
    const words = haystack.split(/[\s_\/-]+/).filter(Boolean);
    const terms = needle.split(/\s+/).filter(Boolean);
    if (terms.length > 1) {
      return terms.every((term) => fuzzyTermMatch(term, words, haystack));
    }
    return fuzzyTermMatch(needle, words, haystack);
  }

  const items = Array.isArray(payload.objects) ? payload.objects : [];
  const itemsById = new Map(items.map((item) => [item.id, item]));
  const searchableText = new Map(
    items.map((item) => [
      item.id,
      normalize([
        item.id,
        item.type,
        item.type_label,
        item.authority,
        item.page_id,
        item.page_title,
        item.preview,
      ].join(" ")),
    ])
  );

  let activeType = "all";
  let activePage = "";
  let activeIndex = -1;

  try {
    activePage = new URLSearchParams(window.location.search || "").get("page") || "";
  } catch {
    activePage = "";
  }

  function matchesPage(item) {
    return !activePage || item.dataset.rayaPracticePage === activePage;
  }

  function matchesType(item) {
    return activeType === "all" || item.dataset.rayaPracticeType === activeType;
  }

  function matchesSearch(item, query) {
    if (!query) return true;
    const id = item.getAttribute("data-raya-practice-object") || "";
    const haystack = searchableText.get(id) || normalize(item.textContent);
    return fuzzyMatch(query, haystack);
  }

  function updateGroups() {
    groups.forEach((group) => {
      const visible = group.querySelectorAll("[data-raya-practice-object]:not([hidden])").length;
      group.hidden = visible === 0;
    });
  }

  function updateFilters() {
    filters.forEach((button) => {
      const pressed = (button.getAttribute("data-raya-practice-filter") || "all") === activeType;
      button.setAttribute("aria-pressed", pressed ? "true" : "false");
    });
  }

  function itemForObject(object) {
    if (!object) return null;
    const id = object.getAttribute("data-raya-practice-object") || "";
    return itemsById.get(id) || null;
  }

  function pageTitleForActivePage() {
    if (!activePage) return "";
    const item = items.find((candidate) => candidate.page_id === activePage);
    return item ? (item.page_title || activePage) : "";
  }

  function updatePageFocusNotice(visibleCount) {
    if (!pageFocusNotice) return;
    const title = pageTitleForActivePage();
    if (!activePage || !title) {
      pageFocusNotice.hidden = true;
      pageFocusNotice.textContent = "";
      return;
    }
    pageFocusNotice.hidden = false;
    pageFocusNotice.textContent =
      `Focused on page ${title}. ${visibleCount} visible practice object(s). Use Clear to show all.`;
  }

  function visibleObjects() {
    return objects.filter((object) => !object.hidden);
  }

  function indexForObject(object) {
    return visibleObjects().indexOf(object);
  }

  function bestContextObject(visible) {
    if (activeIndex >= 0 && visible[activeIndex]) {
      return visible[activeIndex];
    }
    return visible[0];
  }

  function setActiveObject(nextIndex) {
    const visible = visibleObjects();
    if (visible.length === 0) {
      activeIndex = -1;
    } else {
      activeIndex = Math.max(-1, Math.min(nextIndex, visible.length - 1));
    }
    objects.forEach((object) => {
      object.dataset.rayaPracticeActive = "false";
      object.setAttribute("data-raya-practice-active", "false");
    });
    if (activeIndex >= 0 && visible[activeIndex]) {
      visible[activeIndex].dataset.rayaPracticeActive = "true";
      visible[activeIndex].setAttribute("data-raya-practice-active", "true");
    }
    updateContext();
  }

  function updateContextActions(actions, contextLabel) {
    if (!contextActions) return;
    contextActions.replaceChildren();
    const visibleActions = actions.filter((action) => action.href);
    contextActions.hidden = visibleActions.length === 0;
    visibleActions.forEach((action) => {
      const link = document.createElement("a");
      link.href = action.href;
      link.textContent = action.label;
      link.tabIndex = 0;
      if (contextLabel) {
        link.setAttribute("aria-label", `${action.label}: ${contextLabel}`);
      }
      contextActions.appendChild(link);
    });
  }

  function updateContext() {
    const visible = visibleObjects();
    const item = itemForObject(bestContextObject(visible));
    if (summaryCount) {
      summaryCount.textContent = `${visible.length} visible practice object(s).`;
    }
    if (!item) {
      if (contextTitle) contextTitle.textContent = "No visible practice object.";
      if (contextMeta) contextMeta.textContent = "Clear the search or choose another object type.";
      updateContextActions([]);
      return;
    }
    const title = item.preview || item.id || "Official object";
    if (contextTitle) {
      contextTitle.textContent = title;
    }
    if (contextMeta) {
      contextMeta.textContent = [
        item.type_label || item.type || "Practice",
        item.page_title ? `From ${item.page_title}` : "",
        item.authority ? `Authority ${item.authority}` : "",
        item.id ? `ID ${item.id}` : "",
      ].filter(Boolean).join(" | ");
    }
    if (activeIndex < 0) {
      updateContextActions([]);
      return;
    }
    updateContextActions([
      { label: "Open page", href: item.page_url },
      { label: "View graph", href: item.graph_url },
    ], title);
  }

  function render() {
    const query = normalize(input.value);
    let visible = 0;
    objects.forEach((item) => {
      const matched = matchesPage(item) && matchesType(item) && matchesSearch(item, query);
      item.hidden = !matched;
      if (matched) visible += 1;
    });
    updateGroups();
    updateFilters();
    if (empty) {
      empty.hidden = visible !== 0;
    }
    if (status) {
      status.textContent = `${visible} visible practice object(s).`;
    }
    updatePageFocusNotice(visible);
    const nextIndex = activePage && visible > 0 && activeIndex < 0
      ? 0
      : Math.min(activeIndex, visible - 1);
    setActiveObject(nextIndex);
  }

  filters.forEach((button) => {
    button.addEventListener("click", () => {
      activeType = button.getAttribute("data-raya-practice-filter") || "all";
      activeIndex = -1;
      render();
    });
  });

  objects.forEach((object) => {
    object.addEventListener("focusin", () => {
      const index = indexForObject(object);
      if (index >= 0) setActiveObject(index);
    });
    object.addEventListener("pointerenter", () => {
      const index = indexForObject(object);
      if (index >= 0) setActiveObject(index);
    });
  });

  function resetPracticeFocus() {
    input.value = "";
    activeType = "all";
    activePage = "";
    activeIndex = -1;
  }

  input.addEventListener("input", () => {
    activeIndex = -1;
    render();
  });
  input.addEventListener("keydown", (event) => {
    const visible = visibleObjects();
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveObject(visible.length === 0 ? -1 : (activeIndex + 1) % visible.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      const next = activeIndex <= 0 ? visible.length - 1 : activeIndex - 1;
      setActiveObject(visible.length === 0 ? -1 : next);
    } else if (event.key === "Enter" && activeIndex >= 0 && visible[activeIndex]) {
      const link = visible[activeIndex].querySelector(".raya-practice-open");
      if (link && link.href) {
        event.preventDefault();
        window.location.href = link.href;
      }
    } else if (event.key === "Escape") {
      event.preventDefault();
      resetPracticeFocus();
      render();
    }
  });

  if (clear) {
    clear.addEventListener("click", () => {
      resetPracticeFocus();
      render();
      input.focus();
    });
  }

  render();
})();
"""
