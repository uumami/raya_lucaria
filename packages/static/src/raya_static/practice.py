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
  const filters = Array.from(document.querySelectorAll("[data-raya-practice-filter]"));
  const objects = Array.from(document.querySelectorAll("[data-raya-practice-object]"));
  const groups = Array.from(document.querySelectorAll("[data-raya-practice-group]"));
  const fontButtons = Array.from(document.querySelectorAll(".raya-font-toggle"));
  const textSizeButtons = Array.from(document.querySelectorAll(".raya-text-size-toggle"));

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

  const items = Array.isArray(payload.objects) ? payload.objects : [];
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
  const textSizes = ["normal", "large", "x-large"];
  let textSize = "normal";
  let dyslexicEnabled = false;

  function matchesType(item) {
    return activeType === "all" || item.dataset.rayaPracticeType === activeType;
  }

  function matchesSearch(item, query) {
    if (!query) return true;
    const id = item.getAttribute("data-raya-practice-object") || "";
    const haystack = searchableText.get(id) || normalize(item.textContent);
    return haystack.includes(query);
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

  function render() {
    const query = normalize(input.value);
    let visible = 0;
    objects.forEach((item) => {
      const matched = matchesType(item) && matchesSearch(item, query);
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
  }

  filters.forEach((button) => {
    button.addEventListener("click", () => {
      activeType = button.getAttribute("data-raya-practice-filter") || "all";
      render();
    });
  });

  input.addEventListener("input", render);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      input.value = "";
      activeType = "all";
      render();
    }
  });

  if (clear) {
    clear.addEventListener("click", () => {
      input.value = "";
      activeType = "all";
      render();
      input.focus();
    });
  }

  function applyDyslexic(enabled) {
    dyslexicEnabled = Boolean(enabled);
    document.documentElement.setAttribute(
      "data-raya-open-dyslexic",
      dyslexicEnabled ? "true" : "false"
    );
    fontButtons.forEach((button) => {
      button.setAttribute("aria-pressed", dyslexicEnabled ? "true" : "false");
    });
  }

  function applyTextSize(size) {
    textSize = textSizes.includes(size) ? size : "normal";
    document.documentElement.setAttribute("data-raya-text-size", textSize);
    textSizeButtons.forEach((button) => {
      button.setAttribute("aria-pressed", textSize === "normal" ? "false" : "true");
      button.setAttribute("aria-label", `Text size: ${textSize}`);
    });
  }

  fontButtons.forEach((button) => {
    button.addEventListener("click", () => {
      applyDyslexic(!dyslexicEnabled);
    });
  });

  textSizeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const index = textSizes.indexOf(textSize);
      applyTextSize(textSizes[(index + 1) % textSizes.length]);
    });
  });

  applyDyslexic(false);
  applyTextSize("normal");
  render();
})();
"""
