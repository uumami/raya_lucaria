from __future__ import annotations

from dataclasses import dataclass


TASKS_SCRIPT_NAME = "tasks.js"
TASKS_RESOURCE_PATH = "_raya/render"


@dataclass(frozen=True)
class TasksResources:
    javascript: str


def tasks_resources() -> TasksResources:
    return TasksResources(javascript=_TASKS_JAVASCRIPT)


_TASKS_JAVASCRIPT = r"""
(() => {
  const root = document.querySelector("[data-raya-tasks-page]");
  const dataEl = document.getElementById("raya-tasks-data");
  const input = document.getElementById("raya-tasks-search");
  const clear = document.getElementById("raya-tasks-clear");
  const sort = document.getElementById("raya-tasks-sort");
  const status = document.getElementById("raya-tasks-status");
  const empty = document.getElementById("raya-tasks-empty");
  const summaryCount = document.querySelector("[data-raya-tasks-summary-count]");
  const pageFocusNotice = document.querySelector("[data-raya-tasks-page-focus]");
  const contextTitle = document.querySelector("[data-raya-tasks-context-title]");
  const contextMeta = document.querySelector("[data-raya-tasks-context-meta]");
  const filters = Array.from(document.querySelectorAll("[data-raya-task-filter]"));
  const objects = Array.from(document.querySelectorAll("[data-raya-task-object]"));
  const results = document.querySelector("[data-raya-tasks-results]");

  if (!root || !dataEl || !input || !results) {
    return;
  }

  let payload;
  try {
    payload = JSON.parse(dataEl.textContent || "{}");
  } catch {
    if (status) status.textContent = "Task data could not be read.";
    return;
  }

  function normalize(value) {
    return String(value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
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
        item.title,
        item.preview,
        item.due,
        item.available,
        item.points,
        item.weight,
        item.status,
        Array.isArray(item.tags) ? item.tags.join(" ") : "",
      ].join(" ")),
    ])
  );

  let activeType = "all";
  let activePage = "";
  try {
    activePage = new URLSearchParams(window.location.search || "").get("page") || "";
  } catch {
    activePage = "";
  }
  let activeIndex = -1;

  function matchesType(object) {
    return activeType === "all" || object.dataset.rayaTaskType === activeType;
  }

  function matchesPage(object) {
    return !activePage || object.dataset.rayaTaskPage === activePage;
  }

  function matchesSearch(object, query) {
    if (!query) return true;
    const id = object.getAttribute("data-raya-task-object") || "";
    const haystack = searchableText.get(id) || normalize(object.textContent);
    return haystack.includes(query);
  }

  function itemForObject(object) {
    if (!object) return null;
    const id = object.getAttribute("data-raya-task-object") || "";
    return itemsById.get(id) || null;
  }

  function pageTitleForActivePage() {
    if (!activePage) return "";
    const item = items.find((candidate) => candidate.page_id === activePage);
    return item ? (item.page_title || activePage) : "";
  }

  function visibleObjects() {
    return objects.filter((object) => !object.hidden);
  }

  function indexForObject(object) {
    return visibleObjects().indexOf(object);
  }

  function updateFilters() {
    filters.forEach((button) => {
      const pressed = (button.getAttribute("data-raya-task-filter") || "all") === activeType;
      button.setAttribute("aria-pressed", pressed ? "true" : "false");
    });
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
      object.dataset.rayaTaskActive = "false";
      object.setAttribute("data-raya-task-active", "false");
    });
    if (activeIndex >= 0 && visible[activeIndex]) {
      visible[activeIndex].dataset.rayaTaskActive = "true";
      visible[activeIndex].setAttribute("data-raya-task-active", "true");
    }
    updateContext();
  }

  function taskMeta(item) {
    if (!item) return "";
    return [
      item.type_label || item.type || "Task",
      item.page_title ? `From ${item.page_title}` : "",
      item.due ? `Due ${item.due}` : "",
      item.available ? `Available ${item.available}` : "",
      item.points || "",
      item.weight ? `Weight ${item.weight}` : "",
      item.status ? `Status ${item.status}` : "",
    ].filter(Boolean).join(" | ");
  }

  function taskCountText(count) {
    return `${count} visible ${count === 1 ? "task" : "tasks"}.`;
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
      `Focused on page ${title}. ${taskCountText(visibleCount)} Use Clear to show all.`;
  }

  function updateContext() {
    const visible = visibleObjects();
    const item = itemForObject(bestContextObject(visible));
    if (summaryCount) {
      summaryCount.textContent = taskCountText(visible.length);
    }
    if (!item) {
      if (contextTitle) contextTitle.textContent = "No visible task.";
      if (contextMeta) contextMeta.textContent = "Clear the search or choose another task type.";
      return;
    }
    if (contextTitle) {
      contextTitle.textContent = item.title || item.preview || item.id || "Official task";
    }
    if (contextMeta) {
      contextMeta.textContent = taskMeta(item);
    }
  }

  function sortObjects() {
    const mode = sort ? sort.value : "course";
    const ordered = objects.slice().sort((a, b) => {
      const itemA = itemForObject(a) || {};
      const itemB = itemForObject(b) || {};
      if (mode === "due") {
        const dueA = itemA.due || "9999-99-99";
        const dueB = itemB.due || "9999-99-99";
        if (dueA !== dueB) return dueA.localeCompare(dueB);
      } else if (mode === "type") {
        const typeA = itemA.type_label || itemA.type || "";
        const typeB = itemB.type_label || itemB.type || "";
        if (typeA !== typeB) return typeA.localeCompare(typeB);
      }
      return Number(a.dataset.rayaTaskOrder || 0) - Number(b.dataset.rayaTaskOrder || 0);
    });
    ordered.forEach((object) => results.appendChild(object));
  }

  function render() {
    const query = normalize(input.value);
    let visible = 0;
    objects.forEach((object) => {
      const matched = matchesPage(object) && matchesType(object) && matchesSearch(object, query);
      object.hidden = !matched;
      if (matched) visible += 1;
    });
    sortObjects();
    updateFilters();
    if (empty) {
      empty.hidden = visible !== 0;
    }
    if (status) {
      status.textContent = taskCountText(visible);
    }
    updatePageFocusNotice(visible);
    setActiveObject(Math.min(activeIndex, visible - 1));
  }

  filters.forEach((button) => {
    button.addEventListener("click", () => {
      activeType = button.getAttribute("data-raya-task-filter") || "all";
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
      const link = visible[activeIndex].querySelector(".raya-task-open");
      if (link && link.href) {
        event.preventDefault();
        window.location.href = link.href;
      }
    } else if (event.key === "Escape") {
      event.preventDefault();
      input.value = "";
      activeType = "all";
      activePage = "";
      activeIndex = -1;
      render();
    }
  });

  if (sort) {
    sort.addEventListener("change", () => {
      activeIndex = -1;
      render();
    });
  }

  if (clear) {
    clear.addEventListener("click", () => {
      input.value = "";
      activeType = "all";
      activePage = "";
      activeIndex = -1;
      if (sort) sort.value = "course";
      render();
      input.focus();
    });
  }

  render();
})();
"""
