from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ACCESSIBILITY_RESOURCE_PATH = "_raya/render/accessibility"
OPEN_DYSLEXIC_CSS_NAME = "open-dyslexic.css"
OPEN_DYSLEXIC_JS_NAME = "open-dyslexic-toggle.js"
OPEN_DYSLEXIC_FONT_NAME = "OpenDyslexic-Regular.woff"
OPEN_DYSLEXIC_SOURCE_FONT = (
    Path(__file__).resolve().parents[2]
    / "assets"
    / "accessibility"
    / "open-dyslexic"
    / OPEN_DYSLEXIC_FONT_NAME
)


@dataclass(frozen=True)
class AccessibilityResources:
    css: str
    javascript: str
    source_font: Path
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

  function apply(enabled) {
    document.documentElement.setAttribute(
      "data-raya-open-dyslexic",
      enabled ? "true" : "false"
    );
    document.querySelectorAll(".raya-font-toggle").forEach((button) => {
      button.setAttribute("aria-pressed", enabled ? "true" : "false");
    });
  }

  const initial = localStorage.getItem(storageKey) === activeValue;
  apply(initial);

  document.addEventListener("click", (event) => {
    const button = event.target.closest(".raya-font-toggle");
    if (!button) {
      return;
    }
    const enabled = button.getAttribute("aria-pressed") !== "true";
    localStorage.setItem(storageKey, enabled ? activeValue : "false");
    apply(enabled);
  });
})();
'''
    return AccessibilityResources(
        css=css,
        javascript=javascript,
        source_font=OPEN_DYSLEXIC_SOURCE_FONT,
        font_name=OPEN_DYSLEXIC_FONT_NAME,
    )
