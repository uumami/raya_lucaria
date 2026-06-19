from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from importlib.abc import Traversable


ACCESSIBILITY_RESOURCE_PATH = "_raya/render/accessibility"
OPEN_DYSLEXIC_CSS_NAME = "open-dyslexic.css"
OPEN_DYSLEXIC_JS_NAME = "open-dyslexic-toggle.js"
OPEN_DYSLEXIC_FONT_NAME = "OpenDyslexic-Regular.woff"
OPEN_DYSLEXIC_RESOURCE_PACKAGE = "raya_static"
OPEN_DYSLEXIC_RESOURCE_PATH = (
    "assets/accessibility/open-dyslexic/" + OPEN_DYSLEXIC_FONT_NAME
)


@dataclass(frozen=True)
class AccessibilityResources:
    css: str
    javascript: str
    source_font: Traversable
    font_name: str


def open_dyslexic_resources() -> AccessibilityResources:
    css = f'''@font-face {{
  font-family: "OpenDyslexic";
  src: url("fonts/{OPEN_DYSLEXIC_FONT_NAME}") format("woff");
  font-style: normal;
  font-weight: 400;
  font-display: swap;
}}

[data-raya-open-dyslexic="true"] {{
  --raya-font-body: "OpenDyslexic";
  --raya-font-heading: "OpenDyslexic";
}}

[data-raya-open-dyslexic="true"] body {{
  --raya-font-body: "OpenDyslexic";
  --raya-font-heading: "OpenDyslexic";
}}

:root {{
  --raya-reader-text-scale: 1;
}}

:root[data-raya-text-size="large"] {{
  --raya-reader-text-scale: 1.125;
}}

:root[data-raya-text-size="x-large"] {{
  --raya-reader-text-scale: 1.25;
}}

.raya-font-toggle {{
  align-items: center;
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  cursor: pointer;
  display: inline-flex;
  font: inherit;
  font-size: 0.875rem;
  font-weight: 700;
  gap: 0.4rem;
  padding: 0.45rem 0.65rem;
}}

.raya-font-toggle[aria-pressed="true"] {{
  background: var(--raya-color-accent);
  border-color: var(--raya-color-accent);
  color: var(--raya-color-surface);
}}
'''
    javascript = '''(() => {
  const dyslexicStorageKey = "raya:open-dyslexic";
  const dyslexicActiveValue = "true";
  const textSizeStorageKey = "raya:text-size";
  const textSizes = ["normal", "large", "x-large"];

  function storedDyslexicPreference() {
    try {
      return localStorage.getItem(dyslexicStorageKey) === dyslexicActiveValue;
    } catch {
      return false;
    }
  }

  function storeDyslexicPreference(enabled) {
    try {
      localStorage.setItem(
        dyslexicStorageKey,
        enabled ? dyslexicActiveValue : "false"
      );
    } catch {
      return;
    }
  }

  function storedTextSizePreference() {
    try {
      const value = localStorage.getItem(textSizeStorageKey) || "normal";
      return textSizes.includes(value) ? value : "normal";
    } catch {
      return "normal";
    }
  }

  function storeTextSizePreference(size) {
    try {
      localStorage.setItem(textSizeStorageKey, size);
    } catch {
      return;
    }
  }

  function applyDyslexic(enabled) {
    document.documentElement.setAttribute(
      "data-raya-open-dyslexic",
      enabled ? "true" : "false"
    );
    document.querySelectorAll(".raya-font-toggle").forEach((button) => {
      button.setAttribute("aria-pressed", enabled ? "true" : "false");
    });
  }

  function applyTextSize(size) {
    const normalized = textSizes.includes(size) ? size : "normal";
    document.documentElement.setAttribute("data-raya-text-size", normalized);
    document.querySelectorAll(".raya-text-size-toggle").forEach((button) => {
      button.setAttribute(
        "aria-pressed",
        normalized === "normal" ? "false" : "true"
      );
      button.setAttribute("aria-label", `Text size: ${normalized}`);
    });
  }

  applyDyslexic(storedDyslexicPreference());
  applyTextSize(storedTextSizePreference());

  document.addEventListener("click", (event) => {
    const fontButton = event.target.closest(".raya-font-toggle");
    if (fontButton) {
      const enabled = fontButton.getAttribute("aria-pressed") !== "true";
      storeDyslexicPreference(enabled);
      applyDyslexic(enabled);
      return;
    }

    const sizeButton = event.target.closest(".raya-text-size-toggle");
    if (sizeButton) {
      const current = document.documentElement.getAttribute("data-raya-text-size")
        || "normal";
      const index = textSizes.indexOf(current);
      const next = textSizes[(index + 1) % textSizes.length];
      storeTextSizePreference(next);
      applyTextSize(next);
    }
  });
})();
'''
    return AccessibilityResources(
        css=css,
        javascript=javascript,
        source_font=resources.files(OPEN_DYSLEXIC_RESOURCE_PACKAGE).joinpath(
            OPEN_DYSLEXIC_RESOURCE_PATH
        ),
        font_name=OPEN_DYSLEXIC_FONT_NAME,
    )
