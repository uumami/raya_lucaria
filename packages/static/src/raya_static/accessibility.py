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
  const storageKey = "raya:open-dyslexic";
  const activeValue = "true";

  function storedPreference() {
    try {
      return localStorage.getItem(storageKey) === activeValue;
    } catch {
      return false;
    }
  }

  function storePreference(enabled) {
    try {
      localStorage.setItem(storageKey, enabled ? activeValue : "false");
    } catch {
      return;
    }
  }

  function apply(enabled) {
    document.documentElement.setAttribute(
      "data-raya-open-dyslexic",
      enabled ? "true" : "false"
    );
    document.querySelectorAll(".raya-font-toggle").forEach((button) => {
      button.setAttribute("aria-pressed", enabled ? "true" : "false");
    });
  }

  apply(storedPreference());

  document.addEventListener("click", (event) => {
    const button = event.target.closest(".raya-font-toggle");
    if (!button) {
      return;
    }
    const enabled = button.getAttribute("aria-pressed") !== "true";
    storePreference(enabled);
    apply(enabled);
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
