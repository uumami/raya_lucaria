from __future__ import annotations

from dataclasses import dataclass


SCHEDULE_SCRIPT_NAME = "schedule.js"
SCHEDULE_RESOURCE_PATH = "_raya/render"


@dataclass(frozen=True)
class ScheduleResources:
    javascript: str


def schedule_resources() -> ScheduleResources:
    return ScheduleResources(javascript=_SCHEDULE_JAVASCRIPT)


_SCHEDULE_JAVASCRIPT = r"""
(() => {
  const root = document.querySelector("[data-raya-schedule-page]");
  const dataEl = document.getElementById("raya-schedule-data");
  const input = document.getElementById("raya-schedule-search");
  const clear = document.getElementById("raya-schedule-clear");
  const status = document.getElementById("raya-schedule-status");
  const empty = document.getElementById("raya-schedule-empty");
  const summaryCount = document.querySelector("[data-raya-schedule-summary-count]");
  const pageFocusNotice = document.querySelector("[data-raya-schedule-page-focus]");
  const contextTitle = document.querySelector("[data-raya-schedule-context-title]");
  const contextMeta = document.querySelector("[data-raya-schedule-context-meta]");
  const contextActions = document.querySelector("[data-raya-schedule-context-actions]");
  const typeFilters = Array.from(document.querySelectorAll("[data-raya-schedule-type-filter]"));
  const kindFilters = Array.from(document.querySelectorAll("[data-raya-schedule-kind-filter]"));
  const items = Array.from(document.querySelectorAll("[data-raya-schedule-item]"));
  const results = document.querySelector("[data-raya-schedule-results]");

  if (!root || !dataEl || !input || !results) {
    return;
  }

  let payload;
  try {
    payload = JSON.parse(dataEl.textContent || "{}");
  } catch {
    if (status) status.textContent = "Schedule data could not be read.";
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

  const scheduleItems = Array.isArray(payload.items) ? payload.items : [];
  const itemsById = new Map(scheduleItems.map((item) => [item.id, item]));
  const searchableText = new Map(
    scheduleItems.map((item) => [
      item.id,
      normalize([
        item.id,
        item.event_date,
        item.event_kind,
        item.type,
        item.type_label,
        item.authority,
        item.page_id,
        item.page_title,
        item.title,
        item.preview,
        item.points,
        item.weight,
        item.status,
        Array.isArray(item.tags) ? item.tags.join(" ") : "",
      ].join(" ")),
    ])
  );

  let activeType = "all";
  let activeKind = "all";
  let activePage = "";
  try {
    activePage = new URLSearchParams(window.location.search || "").get("page") || "";
  } catch {
    activePage = "";
  }
  let activeIndex = -1;

  function itemForObject(object) {
    if (!object) return null;
    const id = object.getAttribute("data-raya-schedule-item") || "";
    return itemsById.get(id) || null;
  }

  function pageTitleForActivePage() {
    if (!activePage) return "";
    const item = scheduleItems.find((candidate) => candidate.page_id === activePage);
    return item ? (item.page_title || activePage) : "";
  }

  function visibleItems() {
    return items.filter((item) => !item.hidden);
  }

  function indexForObject(object) {
    return visibleItems().indexOf(object);
  }

  function matchesType(object) {
    return activeType === "all" || object.dataset.rayaScheduleType === activeType;
  }

  function matchesKind(object) {
    return activeKind === "all" || object.dataset.rayaScheduleKind === activeKind;
  }

  function matchesPage(object) {
    return !activePage || object.dataset.rayaSchedulePage === activePage;
  }

  function matchesSearch(object, query) {
    if (!query) return true;
    const id = object.getAttribute("data-raya-schedule-item") || "";
    const haystack = searchableText.get(id) || normalize(object.textContent);
    return fuzzyMatch(query, haystack);
  }

  function updatePressed(buttons, attribute, activeValue) {
    buttons.forEach((button) => {
      const pressed = (button.getAttribute(attribute) || "all") === activeValue;
      button.setAttribute("aria-pressed", pressed ? "true" : "false");
    });
  }

  function scheduleCountText(count) {
    return `${count} visible schedule ${count === 1 ? "item" : "items"}.`;
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
      `Focused on page ${title}. ${scheduleCountText(visibleCount)} Use Clear to show all.`;
  }

  function bestContextObject(visible) {
    if (activeIndex >= 0 && visible[activeIndex]) {
      return visible[activeIndex];
    }
    return visible[0];
  }

  function scheduleMeta(item) {
    if (!item) return "";
    return [
      item.event_label || "",
      item.type_label || item.type || "Task",
      item.page_title ? `From ${item.page_title}` : "",
      item.points || "",
      item.weight ? `Weight ${item.weight}` : "",
      item.status ? `Status ${item.status}` : "",
    ].filter(Boolean).join(" | ");
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
    const visible = visibleItems();
    const item = itemForObject(bestContextObject(visible));
    if (summaryCount) {
      summaryCount.textContent = scheduleCountText(visible.length);
    }
    if (!item) {
      if (contextTitle) contextTitle.textContent = "No visible schedule item.";
      if (contextMeta) contextMeta.textContent = "Clear the search or choose another filter.";
      updateContextActions([]);
      return;
    }
    const title = item.title || item.preview || item.id || "Schedule item";
    if (contextTitle) {
      contextTitle.textContent = title;
    }
    if (contextMeta) {
      contextMeta.textContent = scheduleMeta(item);
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

  function setActiveObject(nextIndex) {
    const visible = visibleItems();
    if (visible.length === 0) {
      activeIndex = -1;
    } else {
      activeIndex = Math.max(-1, Math.min(nextIndex, visible.length - 1));
    }
    items.forEach((item) => {
      item.dataset.rayaScheduleActive = "false";
      item.setAttribute("data-raya-schedule-active", "false");
    });
    if (activeIndex >= 0 && visible[activeIndex]) {
      visible[activeIndex].dataset.rayaScheduleActive = "true";
      visible[activeIndex].setAttribute("data-raya-schedule-active", "true");
    }
    updateContext();
  }

  function sortItems() {
    const ordered = items.slice().sort((a, b) => {
      const itemA = itemForObject(a) || {};
      const itemB = itemForObject(b) || {};
      const dateA = itemA.event_date || "9999-99-99";
      const dateB = itemB.event_date || "9999-99-99";
      if (dateA !== dateB) return dateA.localeCompare(dateB);
      return Number(a.dataset.rayaScheduleOrder || 0) - Number(b.dataset.rayaScheduleOrder || 0);
    });
    ordered.forEach((item) => results.appendChild(item));
  }

  function render() {
    const query = normalize(input.value);
    let visible = 0;
    items.forEach((item) => {
      const matched = matchesPage(item) && matchesType(item) && matchesKind(item) && matchesSearch(item, query);
      item.hidden = !matched;
      if (matched) visible += 1;
    });
    sortItems();
    updatePressed(typeFilters, "data-raya-schedule-type-filter", activeType);
    updatePressed(kindFilters, "data-raya-schedule-kind-filter", activeKind);
    if (empty) {
      empty.hidden = visible !== 0;
    }
    if (status) {
      status.textContent = scheduleCountText(visible);
    }
    updatePageFocusNotice(visible);
    setActiveObject(Math.min(activeIndex, visible - 1));
  }

  typeFilters.forEach((button) => {
    button.addEventListener("click", () => {
      activeType = button.getAttribute("data-raya-schedule-type-filter") || "all";
      activeIndex = -1;
      render();
    });
  });

  kindFilters.forEach((button) => {
    button.addEventListener("click", () => {
      activeKind = button.getAttribute("data-raya-schedule-kind-filter") || "all";
      activeIndex = -1;
      render();
    });
  });

  items.forEach((item) => {
    item.addEventListener("focusin", () => {
      const index = indexForObject(item);
      if (index >= 0) setActiveObject(index);
    });
    item.addEventListener("pointerenter", () => {
      const index = indexForObject(item);
      if (index >= 0) setActiveObject(index);
    });
  });

  input.addEventListener("input", () => {
    activeIndex = -1;
    render();
  });
  input.addEventListener("keydown", (event) => {
    const visible = visibleItems();
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveObject(visible.length === 0 ? -1 : (activeIndex + 1) % visible.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      const next = activeIndex <= 0 ? visible.length - 1 : activeIndex - 1;
      setActiveObject(visible.length === 0 ? -1 : next);
    } else if (event.key === "Enter" && activeIndex >= 0 && visible[activeIndex]) {
      const link = visible[activeIndex].querySelector(".raya-schedule-open");
      if (link && link.href) {
        event.preventDefault();
        window.location.href = link.href;
      }
    } else if (event.key === "Escape") {
      event.preventDefault();
      input.value = "";
      activeType = "all";
      activeKind = "all";
      activePage = "";
      activeIndex = -1;
      render();
    }
  });

  if (clear) {
    clear.addEventListener("click", () => {
      input.value = "";
      activeType = "all";
      activeKind = "all";
      activePage = "";
      activeIndex = -1;
      render();
      input.focus();
    });
  }

  render();
})();
"""
