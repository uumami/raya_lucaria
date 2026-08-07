from __future__ import annotations

from dataclasses import dataclass

from raya_static.shell_geometry import apply_rail_geometry_tokens


SHELL_SCRIPT_NAME = "shell.js"
SHELL_RESOURCE_PATH = "_raya/render"


@dataclass(frozen=True)
class ShellResources:
    javascript: str


def shell_resources() -> ShellResources:
    return ShellResources(javascript=apply_rail_geometry_tokens(_SHELL_JAVASCRIPT))


_SHELL_JAVASCRIPT = r"""
(() => {
  const root = document.documentElement;
  __RAYA_RAIL_DERIVATION__
  const shell = document.querySelector(".raya-learning-shell");
  const map = document.querySelector("#raya-course-map");
  const mapHeader = document.querySelector(".raya-course-map-header");
  const mapBody = document.querySelector("#raya-course-map-body");
  const mapMini = document.querySelector("[data-raya-course-map-mini]");
  const mapNavigation = document.querySelector("[data-raya-course-map-navigation]");
  const mapCollapseButton = document.querySelector("[data-raya-course-map-collapse]");
  const mapExpandButton = document.querySelector("[data-raya-course-map-expand]");
  const article = document.querySelector("#raya-article");
  const skipLink = document.querySelector('.raya-skip-link[href="#raya-article"]');
  const mobileMapOpener = document.querySelector(".raya-mobile-course-map-open");
  const toggleButtons = Array.from(document.querySelectorAll("[data-raya-course-map-toggle]"));
  const learningRail = document.querySelector("#raya-learning-rail");
  const learningRailBody = document.querySelector("#raya-learning-rail-body");
  const learningRailCollapse = document.querySelector("[data-raya-learning-rail-collapse]");
  const learningRailExpand = document.querySelector("[data-raya-learning-rail-expand]");
  const learningRailDrawerBackdrop = document.querySelector(
    "[data-raya-learning-rail-drawer-backdrop]"
  );
  const learningRailToggleButtons = Array.from(
    document.querySelectorAll("[data-raya-learning-rail-toggle]")
  );
  const railToggleButtons = Array.from(document.querySelectorAll("[data-raya-rail-toggle]"));
  const mapNodeToggles = Array.from(document.querySelectorAll("[data-raya-map-node-toggle]"));
  const mapCloseButton = document.querySelector("[data-raya-course-map-close]");
  const mapDrawerBackdrop = document.querySelector("[data-raya-course-map-drawer-backdrop]");
  const mapFilter = document.querySelector("[data-raya-course-map-filter]");
  const mapFilterEmpty = document.querySelector("[data-raya-map-filter-empty]");
  const assetInspectButtons = Array.from(document.querySelectorAll("[data-raya-asset-inspect]"));
  const desktopMapQuery = window.matchMedia("(min-width: __RAYA_DESKTOP_PX__px)");
  const structuralRailQuery = window.matchMedia("(min-width: __RAYA_STRUCTURAL_PX__px)");
  const compactStructuralRailQuery = window.matchMedia(
    "(min-width: __RAYA_STRUCTURAL_PX__px) and (max-width: __RAYA_COMPACT_MINUS_PX__px)"
  );
  const approvedRailGeometryQuery = window.matchMedia("(min-width: __RAYA_APPROVED_PX__px)");
  const reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
  const printQuery = window.matchMedia("print");
  const tocLinks = Array.from(document.querySelectorAll(".raya-page-toc a[href^='#']"));
  const currentSectionLinks = Array.from(
    document.querySelectorAll("[data-raya-current-section-link]")
  );
  const keyObjectLinks = Array.from(
    document.querySelectorAll(".raya-page-toc-objects a[data-raya-key-object-link]")
  );
  const keyObjectTargets = keyObjectLinks
    .map((link) => {
      const id = link.getAttribute("data-raya-key-object-link") || "";
      return id ? document.getElementById(id) : null;
    })
    .filter(Boolean);
  const headings = tocLinks
    .map((link) => {
      const href = link.getAttribute("href");
      if (!href || href === "#") {
        return null;
      }
      let id = href.slice(1);
      try {
        id = decodeURIComponent(id);
      } catch {
        id = href.slice(1);
      }
      const target = document.getElementById(id);
      return target ? { link, target } : null;
    })
    .filter(Boolean);

  if (
    !shell ||
    !map ||
    !mapHeader ||
    !mapBody ||
    !mapMini ||
    !mapNavigation ||
    !mapCollapseButton ||
    !mapExpandButton ||
    toggleButtons.length === 0
  ) {
    return;
  }
  let courseMapDrawerOpener = null;
  let assetInspector = null;
  let assetInspectorOpener = null;
  let learningRailDrawerOpener = null;
  let courseMapTransitionTimer = 0;
  let learningRailTransitionTimer = 0;
  const explicitlyCollapsedCurrentMapNodes = new WeakSet();
  const SHELL_TRANSITION_MS = 240;

  function applyRailBodyInert(body, collapsed) {
    const hide = isStructuralRailShell() && collapsed;
    body.setAttribute("aria-hidden", hide ? "true" : "false");
    setElementInert(body, hide);
    setFocusableDescendantsEnabled(body, !hide);
  }

  function updateMapLinkTabOrder(nextExpanded) {
    const collapsed = isStructuralRailShell() && !nextExpanded;
    applyRailBodyInert(mapBody, !nextExpanded);
    mapHeader.setAttribute("aria-hidden", collapsed ? "true" : "false");
    setElementInert(mapHeader, collapsed);
    setFocusableDescendantsEnabled(mapHeader, !collapsed);
    mapMini.setAttribute("aria-hidden", collapsed ? "false" : "true");
    setElementInert(mapMini, !collapsed);
    setFocusableDescendantsEnabled(mapMini, collapsed);
    if (desktopMapQuery.matches) {
      map.removeAttribute("tabindex");
    } else {
      map.setAttribute("tabindex", "-1");
    }
  }

  function setButtonLabel(button, label) {
    const labelNode = button.querySelector(
      ".raya-visually-hidden, .raya-command-label"
    );
    if (labelNode) {
      labelNode.textContent = label;
    } else {
      button.textContent = label;
    }
  }

  function describedControl(target) {
    return target instanceof Element ? target.closest("[aria-describedby]") : null;
  }

  function describedTooltip(target) {
    const trigger = describedControl(target);
    if (!trigger) return null;
    const describedBy = (trigger.getAttribute("aria-describedby") || "")
      .split(/\s+/)
      .filter(Boolean);
    return describedBy
      .map((id) => document.getElementById(id))
      .find((candidate) => candidate?.getAttribute("role") === "tooltip") || null;
  }

  function syncTooltipDescription(trigger, label) {
    const tooltip = describedTooltip(trigger);
    if (tooltip) {
      tooltip.textContent = label;
    }
  }

  function positionTooltip(trigger, tooltip) {
    if (!trigger || !tooltip) return;
    const triggerRect = trigger.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    const footer = trigger.closest(".raya-course-map-footer");
    const mini = trigger.closest(".raya-course-map-mini");
    const anchorTop = footer ? footer.getBoundingClientRect().top : triggerRect.top;
    const viewportGap = 8;
    const triggerGap = 6;
    const viewportWidth = document.documentElement.clientWidth;
    if (mini) {
      const left = Math.min(
        triggerRect.right + triggerGap,
        viewportWidth - tooltipRect.width - viewportGap
      );
      const top = Math.max(
        viewportGap,
        Math.min(
          triggerRect.top + ((triggerRect.height - tooltipRect.height) / 2),
          window.innerHeight - tooltipRect.height - viewportGap
        )
      );
      tooltip.style.left = `${Math.round(Math.max(viewportGap, left))}px`;
      tooltip.style.top = `${Math.round(top)}px`;
      return;
    }
    const left = Math.max(
      viewportGap,
      Math.min(triggerRect.left, viewportWidth - tooltipRect.width - viewportGap)
    );
    const above = anchorTop - tooltipRect.height - triggerGap;
    const below = triggerRect.bottom + triggerGap;
    const top = above >= viewportGap
      ? above
      : Math.min(below, window.innerHeight - tooltipRect.height - viewportGap);
    tooltip.style.left = `${Math.round(left)}px`;
    tooltip.style.top = `${Math.round(Math.max(viewportGap, top))}px`;
  }

  function restoreTooltip(event) {
    const currentTrigger = describedControl(event.target);
    const previousTrigger = describedControl(event.relatedTarget);
    if (
      event.type === "pointerover"
      && currentTrigger
      && currentTrigger === previousTrigger
    ) {
      return;
    }
    const tooltip = event.target?.getAttribute?.("role") === "tooltip"
      ? event.target
      : describedTooltip(event.target);
    if (tooltip) {
      const focusedTooltip = describedTooltip(document.activeElement);
      if (
        event.type === "pointerover"
        && focusedTooltip
        && focusedTooltip !== tooltip
      ) {
        tooltip.hidden = true;
        tooltip.setAttribute("data-raya-tooltip-dismissed", "true");
        return;
      }
      if (event.type === "focusin") {
        document.querySelectorAll('[role="tooltip"]').forEach((candidate) => {
          if (candidate === tooltip) return;
          candidate.hidden = true;
          candidate.setAttribute("data-raya-tooltip-dismissed", "true");
        });
      }
      tooltip.removeAttribute("data-raya-tooltip-dismissed");
      tooltip.hidden = false;
      const trigger = currentTrigger || Array.from(
        document.querySelectorAll("[aria-describedby]")
      ).find((candidate) => describedTooltip(candidate) === tooltip);
      positionTooltip(trigger, tooltip);
    }
  }

  function hideTooltipWhenIdle(event) {
    const tooltip = event.target?.getAttribute?.("role") === "tooltip"
      ? event.target
      : describedTooltip(event.target);
    if (!tooltip) return;
    window.setTimeout(() => {
      const trigger = Array.from(document.querySelectorAll("[aria-describedby]"))
        .find((candidate) => describedTooltip(candidate) === tooltip);
      const triggerActive = trigger
        && (trigger.matches(":hover") || trigger === document.activeElement);
      if (!triggerActive && !tooltip.matches(":hover")) {
        tooltip.hidden = true;
      }
    }, 0);
  }

  function dismissActiveTooltip() {
    const focusedTooltip = describedTooltip(document.activeElement);
    const tooltipIsVisible = (candidate) => {
      if (!candidate) return false;
      const candidateStyle = getComputedStyle(candidate);
      return candidateStyle.display !== "none"
        && candidateStyle.visibility !== "hidden";
    };
    const hoveredTooltip = Array.from(
      document.querySelectorAll("[aria-describedby]")
    ).filter((trigger) => trigger.matches(":hover"))
      .map(describedTooltip)
      .find(tooltipIsVisible);
    const tooltip = hoveredTooltip || (
      tooltipIsVisible(focusedTooltip) ? focusedTooltip : Array.from(
        document.querySelectorAll('[role="tooltip"]')
      ).find(tooltipIsVisible)
    );
    if (!tooltip) return false;
    tooltip.hidden = true;
    tooltip.setAttribute("data-raya-tooltip-dismissed", "true");
    return true;
  }

  document.addEventListener("focusin", restoreTooltip);
  document.addEventListener("pointerover", restoreTooltip);
  document.addEventListener("focusout", hideTooltipWhenIdle);
  document.addEventListener("pointerout", hideTooltipWhenIdle);

  function syncCourseMapToggleButtons(nextExpanded) {
    toggleButtons.forEach((button) => {
      button.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
      if (button === mapCollapseButton) {
        button.setAttribute("aria-label", "Hide course map");
        setButtonLabel(button, "Hide map");
      } else if (button === mapExpandButton) {
        button.setAttribute("aria-label", "Expand course map");
        setButtonLabel(button, "Map");
      } else {
        button.setAttribute(
          "aria-label",
          nextExpanded ? "Collapse course map" : "Expand course map"
        );
      }
      syncTooltipDescription(button, button.getAttribute("aria-label") || "");
    });
  }

  function isDesktopShell() {
    return desktopMapQuery.matches;
  }

  function isStructuralRailShell() {
    return structuralRailQuery.matches;
  }

  function courseMapFocusTarget(nextState) {
    if (!isStructuralRailShell()) {
      return mobileMapOpener || article;
    }
    return nextState === "collapsed"
      ? mapExpandButton || article
      : mapCollapseButton || article;
  }

  function isCompactStructuralRailShell() {
    return structuralRailQuery.matches && compactStructuralRailQuery.matches;
  }

  function isPhoneDrawerShell() {
    return !isStructuralRailShell() && !printQuery.matches;
  }

  function isMediumStructuralShell() {
    return isStructuralRailShell() && !approvedRailGeometryQuery.matches;
  }

  function validCourseId() {
    const value = root.dataset.rayaCourseId || "";
    return /^[a-z0-9][a-z0-9._-]*$/.test(value) ? value : "";
  }

  function readerShellStorageKey() {
    const courseId = validCourseId();
    return courseId ? `raya:reader-shell:v1:${courseId}` : "";
  }

  function savedReaderShellPreference() {
    const courseMap = root.dataset.rayaCourseMapPreference;
    const learningRail = root.dataset.rayaLearningRailPreference;
    const valid = (value) => value === "expanded" || value === "collapsed";
    return valid(courseMap) && valid(learningRail) ? { courseMap, learningRail } : null;
  }

  function readReaderShellPreference() {
    const key = readerShellStorageKey();
    if (!key) return null;
    try {
      const raw = sessionStorage.getItem(key);
      if (raw === null) return null;
      const value = JSON.parse(raw);
      const keys = Object.keys(value || {}).sort();
      const valid = (state) => state === "expanded" || state === "collapsed";
      return keys.length === 2 && keys[0] === "courseMap" && keys[1] === "learningRail"
        && valid(value.courseMap) && valid(value.learningRail) ? value : null;
    } catch (_error) {
      return null;
    }
  }

  function effectiveReaderShellState(preference = savedReaderShellPreference()) {
    const bands = rayaRailBands();
    const next = preference || {
      courseMap: "expanded",
      learningRail: bands.structural && !bands.approved ? "collapsed" : "expanded",
    };
    return rayaEffectiveRailState(next.courseMap, next.learningRail, rayaRailBands());
  }

  function intermediateWinnerForTransition() {
    if (map.contains(document.activeElement)) return "courseMap";
    if (learningRail && learningRail.contains(document.activeElement)) return "learningRail";
    return "courseMap";
  }

  function reconcileFocusedIntermediateState(
    preference = savedReaderShellPreference(),
    focusOwner = null
  ) {
    const next = effectiveReaderShellState(preference);
    if (
      !isMediumStructuralShell() ||
      !preference ||
      preference.courseMap !== "expanded" ||
      preference.learningRail !== "expanded"
    ) {
      return next;
    }
    let winner = intermediateWinnerForTransition();
    if (focusOwner instanceof Element) {
      if (map.contains(focusOwner)) {
        winner = "courseMap";
      } else if (learningRail && learningRail.contains(focusOwner)) {
        winner = "learningRail";
      }
    }
    return winner === "learningRail"
      ? { courseMap: "collapsed", learningRail: "expanded" }
      : { courseMap: "expanded", learningRail: "collapsed" };
  }

  function reconcileRailPair(courseMapState, learningRailState, options = {}) {
    const preference = {
      courseMap: courseMapState === "collapsed" ? "collapsed" : "expanded",
      learningRail: learningRailState === "collapsed" ? "collapsed" : "expanded",
    };
    if (options.preferFocusedIntermediate) {
      return reconcileFocusedIntermediateState(preference, options.previousFocus);
    }
    return rayaEffectiveRailState(
      preference.courseMap,
      preference.learningRail,
      options.bands || rayaRailBands()
    );
  }

  function saveReaderShellPreference() {
    const key = readerShellStorageKey();
    if (!key || !isStructuralRailShell()) return;
    const value = {
      courseMap: root.dataset.rayaCourseMap === "expanded" ? "expanded" : "collapsed",
      learningRail: root.dataset.rayaLearningRail === "expanded" ? "expanded" : "collapsed",
    };
    root.dataset.rayaCourseMapPreference = value.courseMap;
    root.dataset.rayaLearningRailPreference = value.learningRail;
    try { sessionStorage.setItem(key, JSON.stringify(value)); } catch (_error) { return; }
  }

  function restoreValidFocus(previousFocus, next, options = {}) {
    if (options.restoreFocus === false) return;
    let focusTarget = options.focusTarget || null;
    if (!focusTarget && previousFocus instanceof Element) {
      focusTarget = readerShellReconciliationFocusTarget(previousFocus, next);
    }
    if (!focusTarget) return;
    const visibleTarget = focusTarget.getClientRects().length > 0
      ? focusTarget
      : article;
    if (visibleTarget) visibleTarget.focus();
  }

  function applyStructuralRailPair(courseMapState, learningRailState, options = {}) {
    const previousFocus = options.previousFocus instanceof Element
      ? options.previousFocus
      : document.activeElement;
    const previousPair = {
      courseMap: root.dataset.rayaCourseMap === "collapsed" ? "collapsed" : "expanded",
      learningRail: root.dataset.rayaLearningRail === "collapsed"
        ? "collapsed"
        : "expanded",
    };
    const next = reconcileRailPair(courseMapState, learningRailState, {
      ...options,
      previousFocus,
    });
    const immediate = options.immediate === true;

    if (immediate) root.dataset.rayaShellReconciling = "true";
    root.dataset.rayaCourseMapDrawer = "closed";
    root.dataset.rayaLearningRailDrawer = "closed";
    if (isMediumStructuralShell()) {
      if (next.courseMap === "collapsed") {
        root.dataset.rayaCourseMap = "collapsed";
      }
      if (next.learningRail === "collapsed") {
        root.dataset.rayaLearningRail = "collapsed";
      }
    }
    root.dataset.rayaCourseMap = next.courseMap;
    root.dataset.rayaLearningRail = next.learningRail;
    syncCourseMapState(next.courseMap, {
      ...options,
      previousState: previousPair.courseMap,
    });
    syncLearningRailState(next.learningRail, {
      ...options,
      previousState: previousPair.learningRail,
    });
    if (immediate) {
      shell.getBoundingClientRect();
      map.getBoundingClientRect();
      if (learningRail) learningRail.getBoundingClientRect();
      delete root.dataset.rayaShellReconciling;
    }
    if (options.persist !== false) saveReaderShellPreference();
    restoreValidFocus(previousFocus, next, options);
    return next;
  }

  function setFocusableDescendantsEnabled(container, enabled) {
    container
      .querySelectorAll("a[href], button, input, select, textarea, summary, [tabindex]")
      .forEach((element) => {
        if (enabled) {
          if (element.dataset.rayaPreviousTabindex === "__none__") {
            element.removeAttribute("tabindex");
          } else if (element.dataset.rayaPreviousTabindex) {
            element.setAttribute("tabindex", element.dataset.rayaPreviousTabindex);
          }
          delete element.dataset.rayaPreviousTabindex;
          return;
        }
        if (!element.dataset.rayaPreviousTabindex) {
          element.dataset.rayaPreviousTabindex = element.hasAttribute("tabindex")
            ? element.getAttribute("tabindex")
            : "__none__";
        }
        element.setAttribute("tabindex", "-1");
      });
  }

  function setElementInert(element, inert) {
    if (inert) {
      element.setAttribute("inert", "");
    } else {
      element.removeAttribute("inert");
    }
    element.inert = inert;
  }

  function setAssistiveHidden(element, hidden) {
    if (!element) {
      return;
    }
    if (hidden) {
      element.setAttribute("aria-hidden", "true");
    } else {
      element.removeAttribute("aria-hidden");
    }
    setElementInert(element, hidden);
    setFocusableDescendantsEnabled(element, !hidden);
  }

  function syncCourseMapModalBackground(drawerOpen) {
    const hidden = drawerOpen;
    [skipLink, article, learningRail, mobileMapOpener].forEach((element) => {
      setAssistiveHidden(element, hidden);
    });
    if (!hidden && learningRail) {
      learningRail.setAttribute("aria-hidden", "false");
    }
  }

  function focusableElementsWithin(container) {
    return Array.from(
      container.querySelectorAll(
        "a[href], button, input, select, textarea, summary, [tabindex]"
      )
    ).filter((element) => {
      if (element.disabled || element.getAttribute("tabindex") === "-1") {
        return false;
      }
      const style = window.getComputedStyle(element);
      return (
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        element.getClientRects().length > 0
      );
    });
  }

  function trapCourseMapDrawerFocus(event) {
    if (
      event.key !== "Tab" ||
      root.dataset.rayaCourseMapDrawer !== "open" ||
      !isPhoneDrawerShell()
    ) {
      return false;
    }
    const focusable = focusableElementsWithin(map);
    if (focusable.length === 0) {
      event.preventDefault();
      map.focus();
      return true;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const activeElement = document.activeElement;
    if (!map.contains(activeElement)) {
      event.preventDefault();
      (event.shiftKey ? last : first).focus();
      return true;
    }
    if (event.shiftKey && activeElement === first) {
      event.preventDefault();
      last.focus();
      return true;
    }
    if (!event.shiftKey && activeElement === last) {
      event.preventDefault();
      first.focus();
      return true;
    }
    return false;
  }

  function trapLearningRailDrawerFocus(event) {
    if (
      event.key !== "Tab" ||
      root.dataset.rayaLearningRailDrawer !== "open" ||
      isDesktopShell() ||
      !learningRail
    ) {
      return false;
    }
    const focusable = focusableElementsWithin(learningRail);
    if (focusable.length === 0) {
      event.preventDefault();
      learningRail.focus();
      return true;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const activeElement = document.activeElement;
    if (!learningRail.contains(activeElement)) {
      event.preventDefault();
      (event.shiftKey ? last : first).focus();
      return true;
    }
    if (event.shiftKey && activeElement === first) {
      event.preventDefault();
      last.focus();
      return true;
    }
    if (!event.shiftKey && activeElement === last) {
      event.preventDefault();
      first.focus();
      return true;
    }
    return false;
  }

  function clearCourseMapFilter() {
    if (mapFilter && mapFilter.value) {
      mapFilter.value = "";
      applyCourseMapFilter();
    }
  }

  function syncCourseMapDrawerState() {
    const drawerOpen = root.dataset.rayaCourseMapDrawer === "open";
    const structuralShell = isStructuralRailShell();
    const modalDrawerOpen = drawerOpen && !structuralShell && isPhoneDrawerShell();
    const structuralExpanded = root.dataset.rayaCourseMap === "expanded";
    const commandExpanded = !structuralShell ? drawerOpen : structuralExpanded;
    root.setAttribute(
      "data-raya-course-map-scroll-lock",
      modalDrawerOpen ? "true" : "false"
    );
    toggleButtons
      .filter((button) => button.classList.contains("raya-command-map"))
      .forEach((button) => {
        button.setAttribute("aria-expanded", commandExpanded ? "true" : "false");
        const label = !structuralShell
            ? commandExpanded
              ? "Close course map"
              : "Open course map"
            : commandExpanded
              ? "Collapse course map"
              : "Expand course map";
        button.setAttribute("aria-label", label);
        syncTooltipDescription(button, label);
    });
    if (mapDrawerBackdrop) {
      mapDrawerBackdrop.hidden = !modalDrawerOpen;
    }
    if (!structuralShell) {
      if (modalDrawerOpen) {
        map.setAttribute("role", "dialog");
        map.setAttribute("aria-modal", "true");
      } else {
        map.removeAttribute("role");
        map.removeAttribute("aria-modal");
      }
      syncCourseMapModalBackground(modalDrawerOpen);
      setElementInert(map, !drawerOpen);
      setFocusableDescendantsEnabled(map, drawerOpen);
      map.setAttribute("aria-hidden", drawerOpen ? "false" : "true");
      return;
    }
    syncCourseMapModalBackground(false);
    map.removeAttribute("role");
    map.removeAttribute("aria-modal");
    setElementInert(map, false);
    setFocusableDescendantsEnabled(map, true);
    map.setAttribute("aria-hidden", "false");
    updateMapLinkTabOrder(root.dataset.rayaCourseMap !== "collapsed");
    if (root.dataset.rayaCourseMapDrawer !== "closed") {
      root.dataset.rayaCourseMapDrawer = "closed";
    }
    root.setAttribute("data-raya-course-map-scroll-lock", "false");
    if (mapDrawerBackdrop) {
      mapDrawerBackdrop.hidden = true;
    }
  }

  function syncCourseMapState(nextState, options = {}) {
    const nextExpanded = nextState === "expanded";
    const previousExpanded = options.previousState
      ? options.previousState !== "collapsed"
      : root.dataset.rayaCourseMap !== "collapsed";
    const desktopTransition =
      isStructuralRailShell()
      && previousExpanded !== nextExpanded
      && options.immediate !== true
      && !reducedMotionQuery.matches;
    const desktopExpanding = desktopTransition && nextExpanded;
    const focusAfterExpansion = Boolean(
      nextExpanded && options.focusCourseMapAfterExpansion
    );
    if (!nextExpanded) {
      clearCourseMapFilter();
    }
    if (desktopTransition) {
      window.clearTimeout(courseMapTransitionTimer);
      map.dataset.rayaCourseMapTransition = nextExpanded ? "expanding" : "collapsing";
      if (desktopExpanding) {
        updateMapLinkTabOrder(false);
      }
      courseMapTransitionTimer = window.setTimeout(() => {
        const shouldTransferFocus =
          desktopExpanding
          && focusAfterExpansion
          && root.dataset.rayaCourseMap === "expanded"
          && map.dataset.rayaCourseMapTransition === "expanding"
          && (
            document.activeElement === mapExpandButton
            || document.activeElement === document.body
          );
        delete map.dataset.rayaCourseMapTransition;
        if (desktopExpanding && root.dataset.rayaCourseMap === "expanded") {
          updateMapLinkTabOrder(true);
        }
        if (shouldTransferFocus) {
          mapCollapseButton.focus();
        }
      }, SHELL_TRANSITION_MS);
    } else {
      window.clearTimeout(courseMapTransitionTimer);
      delete map.dataset.rayaCourseMapTransition;
    }
    syncCourseMapToggleButtons(nextExpanded);
    if (!desktopExpanding) {
      updateMapLinkTabOrder(nextExpanded);
    }
    syncCourseMapDrawerState();
    if (desktopExpanding) {
      updateMapLinkTabOrder(false);
    }
    if (focusAfterExpansion) {
      if (!desktopExpanding) {
        mapCollapseButton.focus();
      }
    }
  }

  function normalizeMapQuery(value) {
    return String(value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }

  function mapNodeText(node) {
    const link = node.querySelector(":scope > .raya-course-map-node-row a");
    return normalizeMapQuery(
      [
        link ? link.textContent : "",
        link ? link.getAttribute("data-raya-map-label") : "",
      ].join(" ")
    );
  }

  function courseMapBranchStorageKey() {
    const courseId = validCourseId();
    const expected = courseId ? `raya:course-map-branches:v1:${courseId}` : "";
    return map.getAttribute("data-raya-course-map-storage-key") === expected
      ? expected
      : "";
  }

  function loadCollapsedMapNodeIds() {
    const key = courseMapBranchStorageKey();
    if (!key) {
      return null;
    }
    let raw;
    try {
      raw = window.sessionStorage.getItem(key);
    } catch (_error) {
      return null;
    }
    if (raw === null) {
      return null;
    }
    try {
      const value = JSON.parse(raw);
      if (
        !Array.isArray(value) ||
        value.some((item) => typeof item !== "string" || !item)
      ) {
        return null;
      }
      const currentIds = new Set(
        mapNodeToggles
          .map((toggle) => toggle.closest("[data-raya-map-node]"))
          .map((node) => mapNodeId(node))
          .filter(Boolean)
      );
      return new Set(value.filter((item) => currentIds.has(item)));
    } catch (_error) {
      return null;
    }
  }

  function mapNodeId(node) {
    return node && node.dataset ? node.dataset.rayaMapNode || "" : "";
  }

  function controlledMapNodeChildren(node, toggle) {
    const childrenId = toggle ? toggle.getAttribute("aria-controls") : "";
    const children = childrenId ? document.getElementById(childrenId) : null;
    return (
      node
      && children
      && children.parentElement === node
      && children.matches("[data-raya-map-children]")
    ) ? children : null;
  }

  function replaceInvalidMapNodeToggle(node, toggle) {
    console.error(`Invalid course map disclosure target: ${mapNodeId(node)}`);
    const spacer = document.createElement("span");
    spacer.className = "raya-course-map-node-spacer";
    spacer.setAttribute("aria-hidden", "true");
    toggle.replaceWith(spacer);
  }

  function saveCollapsedMapBranches() {
    const key = courseMapBranchStorageKey();
    if (!key) {
      return;
    }
    const collapsed = mapNodeToggles
      .map((button) => button.closest("[data-raya-map-node]"))
      .filter((node) => node && node.dataset.rayaMapExpanded !== "true")
      .map((node) => mapNodeId(node))
      .filter(Boolean);
    try {
      window.sessionStorage.setItem(
        key,
        JSON.stringify(collapsed)
      );
    } catch (_error) {
      return;
    }
  }

  function setMapNodePreference(node, expanded) {
    if (!node || !node.dataset) {
      return;
    }
    node.dataset.rayaMapExpanded = expanded ? "true" : "false";
  }

  function setMapNodeEffective(node, expanded) {
    const row = node
      ? node.querySelector(":scope > .raya-course-map-node-row")
      : null;
    const toggle = row
      ? row.querySelector("[data-raya-map-node-toggle]")
      : null;
    const children = controlledMapNodeChildren(node, toggle);
    if (!toggle || !children) {
      return;
    }
    const label = row.getAttribute("data-raya-map-label") || "";
    toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
    toggle.setAttribute(
      "aria-label",
      `${expanded ? "Collapse" : "Expand"}${label ? ` ${label}` : ""}`
    );
    if (!expanded && children.contains(document.activeElement)) {
      toggle.focus();
    }
    children.hidden = !expanded;
    children.setAttribute("aria-hidden", expanded ? "false" : "true");
  }

  function normalizedPreferenceExpansion(nodes, protectedPath) {
    const expanded = new Set();
    const groupsWithEligibleExpansion = new Set();
    nodes.forEach((node) => {
      if (node.dataset.rayaMapExpanded !== "true") {
        return;
      }
      if (protectedPath.has(node)) {
        expanded.add(node);
        return;
      }
      const siblingGroup = node.parentElement;
      if (!siblingGroup || groupsWithEligibleExpansion.has(siblingGroup)) {
        return;
      }
      groupsWithEligibleExpansion.add(siblingGroup);
      expanded.add(node);
    });
    return expanded;
  }

  function applyEffectiveMapState({ filterQuery = "" } = {}) {
    const nodes = mapNodeToggles
      .map((toggle) => toggle.closest("[data-raya-map-node]"))
      .filter(Boolean);
    const protectedPath = currentCourseMapNodes();
    const expanded = normalizedPreferenceExpansion(nodes, protectedPath);

    protectedPath.forEach((node) => expanded.add(node));
    nodes.forEach((node) => {
      if (explicitlyCollapsedCurrentMapNodes.has(node)) {
        expanded.delete(node);
      }
    });

    if (filterQuery) {
      nodes.forEach((node) => {
        const visibleDescendant = Array.from(
          node.querySelectorAll("[data-raya-map-children] [data-raya-map-node]")
        ).some((descendant) => !descendant.hidden);
        if (visibleDescendant) {
          expanded.add(node);
        }
      });
    }

    nodes.forEach((node) => setMapNodeEffective(node, expanded.has(node)));
  }

  function setMapNodeExpanded(node, nextExpanded, options = {}) {
    if (!options.temporary) {
      setMapNodePreference(node, nextExpanded);
    }
    setMapNodeEffective(node, nextExpanded);
    if (!options.temporary && !options.skipPersist) {
      saveCollapsedMapBranches();
    }
  }

  function applyMapUserTransition(node, nextExpanded) {
    const protectedPath = currentCourseMapNodes();
    const nodes = mapNodeToggles
      .map((toggle) => toggle.closest("[data-raya-map-node]"))
      .filter(Boolean);
    const normalizedExpansion = normalizedPreferenceExpansion(nodes, protectedPath);
    nodes.forEach((candidate) => {
      if (
        candidate.dataset.rayaMapExpanded === "true"
        && !normalizedExpansion.has(candidate)
      ) {
        setMapNodePreference(candidate, false);
      }
    });
    const togglesCurrentPath = protectedPath.has(node);
    setMapNodePreference(node, nextExpanded);
    if (nextExpanded && node.parentElement) {
      const depth = node.getAttribute("data-raya-map-depth");
      Array.from(node.parentElement.children).forEach((sibling) => {
        if (
          sibling === node
          || !sibling.matches("[data-raya-map-node]")
          || sibling.getAttribute("data-raya-map-depth") !== depth
          || sibling.dataset.rayaMapExpanded !== "true"
          || protectedPath.has(sibling)
        ) {
          return;
        }
        setMapNodePreference(sibling, false);
      });
    }
    if (togglesCurrentPath) {
      if (nextExpanded) {
        explicitlyCollapsedCurrentMapNodes.delete(node);
      } else {
        explicitlyCollapsedCurrentMapNodes.add(node);
      }
    }
    applyEffectiveMapState({
      filterQuery: mapFilter ? normalizeMapQuery(mapFilter.value) : "",
    });
    saveCollapsedMapBranches();
    return togglesCurrentPath;
  }

  function applyDirectMapBranchAction(node, action) {
    const toggle = node
      ? node.querySelector(
        ":scope > .raya-course-map-node-row [data-raya-map-node-toggle]"
      )
      : null;
    if (!toggle) {
      return false;
    }
    clearCourseMapFilter();
    const expanded = toggle.getAttribute("aria-expanded") === "true";
    let nextExpanded;
    if (action === "toggle") {
      nextExpanded = !expanded;
    } else if (action === "expand" && !expanded) {
      nextExpanded = true;
    } else if (action === "collapse" && expanded) {
      nextExpanded = false;
    } else {
      return false;
    }
    applyMapUserTransition(node, nextExpanded);
    return true;
  }

  function applyStoredMapExpansion(node) {
    setMapNodeExpanded(node, node.dataset.rayaMapExpanded === "true", {
      temporary: true,
    });
  }

  function filterMapNode(node, query) {
    const childNodes = Array.from(
      node.querySelectorAll(":scope > [data-raya-map-children] > [data-raya-map-node]")
    );
    const selfMatches = !query || mapNodeText(node).includes(query);
    const childMatches = childNodes.map((child) => filterMapNode(child, query));
    const descendantMatches = childMatches.some(Boolean);
    const visible = selfMatches || descendantMatches;
    node.hidden = !visible;
    if (query && descendantMatches) {
      setMapNodeExpanded(node, true, { temporary: true });
    } else if (!query) {
      applyStoredMapExpansion(node);
    }
    return visible;
  }

  function applyCourseMapFilter(options = {}) {
    if (!mapFilter) {
      return;
    }
    const query = normalizeMapQuery(mapFilter.value);
    const topNodes = Array.from(
      map.querySelectorAll("#raya-course-map-list > ol > [data-raya-map-node]")
    );
    let visibleCount = 0;
    topNodes.forEach((node) => {
      if (filterMapNode(node, query)) {
        visibleCount += 1;
      }
    });
    if (mapFilterEmpty) {
      mapFilterEmpty.hidden = visibleCount !== 0;
    }
    if (options.normalizeEffective !== false) {
      applyEffectiveMapState({ filterQuery: query });
    } else if (!query && options.exposeCurrentPath !== false) {
      expandCurrentCourseMapPath({ clearFilter: false });
    }
  }

  function isVisibleCourseMapElement(element) {
    if (!(element instanceof Element)) {
      return false;
    }
    const style = window.getComputedStyle(element);
    return (
      style.display !== "none" &&
      style.visibility !== "hidden" &&
      element.getClientRects().length > 0
    );
  }

  function courseMapLinkForNode(node) {
    return node
      ? node.querySelector(":scope > .raya-course-map-node-row a[href]")
      : null;
  }

  function visibleCourseMapLinks() {
    const mapList = map.querySelector("#raya-course-map-list");
    if (!mapList || !isVisibleCourseMapElement(mapList)) {
      return [];
    }
    return Array.from(
      mapList.querySelectorAll("[data-raya-map-node] > .raya-course-map-node-row a[href]")
    ).filter((link) => isVisibleCourseMapElement(link));
  }

  function focusedCourseMapNode() {
    const activeElement = document.activeElement;
    if (!(activeElement instanceof Element)) {
      return null;
    }
    const mapList = map.querySelector("#raya-course-map-list");
    if (!mapList || !mapList.contains(activeElement)) {
      return null;
    }
    return activeElement.closest("[data-raya-map-node]");
  }

  function parentCourseMapLink(node) {
    const parentNode = node && node.parentElement
      ? node.parentElement.closest("[data-raya-map-node]")
      : null;
    return parentNode ? courseMapLinkForNode(parentNode) : null;
  }

  function firstVisibleChildCourseMapLink(node) {
    if (!node) {
      return null;
    }
    const childLinks = Array.from(
      node.querySelectorAll(
        ":scope > [data-raya-map-children] > [data-raya-map-node] > .raya-course-map-node-row a[href]"
      )
    );
    return childLinks.find((link) => isVisibleCourseMapElement(link)) || null;
  }

  function focusCourseMapLinkAtOffset(offset) {
    const links = visibleCourseMapLinks();
    const activeElement = document.activeElement;
    const currentIndex = links.indexOf(activeElement);
    if (currentIndex === -1) {
      return false;
    }
    const nextIndex = Math.max(0, Math.min(links.length - 1, currentIndex + offset));
    const nextLink = links[nextIndex];
    if (!nextLink || nextLink === activeElement) {
      return false;
    }
    nextLink.focus();
    return true;
  }

  function focusCourseMapBoundary(boundary) {
    const links = visibleCourseMapLinks();
    const nextLink = boundary === "last" ? links[links.length - 1] : links[0];
    if (!nextLink || nextLink === document.activeElement) {
      return false;
    }
    nextLink.focus();
    return true;
  }

  function handleCourseMapKeyboardNavigation(event) {
    if (isEditableNavigationTarget(event.target)) {
      return false;
    }
    if (event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) {
      return false;
    }
    const titleLink = event.target instanceof Element
      ? event.target.closest(
        "[data-raya-map-node] > .raya-course-map-node-row a[href]"
      )
      : null;
    if (!titleLink || titleLink !== event.target) {
      return false;
    }
    const node = focusedCourseMapNode();
    if (!node) {
      return false;
    }
    const mapNavigationKeys = new Set([
      "ArrowDown",
      "ArrowUp",
      "Home",
      "End",
      "ArrowRight",
      "ArrowLeft",
    ]);
    if (!mapNavigationKeys.has(event.key)) {
      return false;
    }
    let handled = false;
    if (event.key === "ArrowDown") {
      handled = focusCourseMapLinkAtOffset(1);
    } else if (event.key === "ArrowUp") {
      handled = focusCourseMapLinkAtOffset(-1);
    } else if (event.key === "Home") {
      handled = focusCourseMapBoundary("first");
    } else if (event.key === "End") {
      handled = focusCourseMapBoundary("last");
    } else if (event.key === "ArrowRight") {
      if (applyDirectMapBranchAction(node, "expand")) {
        handled = true;
      } else {
        const childLink = firstVisibleChildCourseMapLink(node);
        if (childLink) {
          childLink.focus();
          handled = true;
        }
      }
    } else if (event.key === "ArrowLeft") {
      if (applyDirectMapBranchAction(node, "collapse")) {
        handled = true;
      } else {
        const parentLink = parentCourseMapLink(node);
        if (parentLink && isVisibleCourseMapElement(parentLink)) {
          parentLink.focus();
          handled = true;
        }
      }
    }
    event.preventDefault();
    event.stopPropagation();
    return handled;
  }

  function orientCourseMapToCurrentPage(options = {}) {
    const mapList = map.querySelector("#raya-course-map-list");
    const currentLink = mapList
      ? mapList.querySelector('a[aria-current="page"]')
      : null;
    if (!mapList || !currentLink) {
      return false;
    }
    if (mapFilter && mapFilter.value && !options.force) {
      return false;
    }
    if (
      mapNavigation.dataset.rayaCourseMapOriented === "true" &&
      !options.force
    ) {
      return false;
    }
    currentLink.scrollIntoView({ block: "nearest", inline: "nearest" });
    mapNavigation.dataset.rayaCourseMapOriented = "true";
    return true;
  }

  function currentCourseMapNodes() {
    const currentLink = map.querySelector("#raya-course-map-list a[aria-current='page']");
    if (!currentLink) {
      return new Set();
    }
    const currentNode = currentLink.closest("[data-raya-map-node]");
    const nodes = new Set();
    let node = currentNode && currentNode.parentElement
      ? currentNode.parentElement.closest("[data-raya-map-node]")
      : null;
    while (node && map.contains(node)) {
      if (node.matches("[data-raya-map-node]")) {
        nodes.add(node);
      }
      node = node.parentElement ? node.parentElement.closest("[data-raya-map-node]") : null;
    }
    return nodes;
  }

  function expandCurrentCourseMapPath(options = {}) {
    if (options.clearFilter !== false) {
      clearCourseMapFilter();
    }
    const currentNodes = currentCourseMapNodes();
    mapNodeToggles.forEach((button) => {
      const node = button.closest("[data-raya-map-node]");
      if (
        node
        && currentNodes.has(node)
        && !explicitlyCollapsedCurrentMapNodes.has(node)
      ) {
        setMapNodeExpanded(node, true, {
          temporary: true,
          skipPersist: true,
        });
      }
    });
    orientCourseMapToCurrentPage({ force: true });
  }

  function openCourseMapDrawer(opener = null) {
    if (opener instanceof Element) {
      courseMapDrawerOpener = opener;
    }
    applyStructuralRailPair("expanded", root.dataset.rayaLearningRail, {
      persist: false,
      restoreFocus: false,
    });
    root.dataset.rayaCourseMapDrawer = "open";
    syncCourseMapDrawerState();
    window.requestAnimationFrame(() => {
      const focusTarget =
        map.querySelector(".raya-course-map-home") ||
        map.querySelector("[data-raya-course-map-close]") ||
        map.querySelector("a, button");
      if (focusTarget) {
        focusTarget.focus();
      }
      orientCourseMapToCurrentPage();
    });
  }

  function closeCourseMapDrawer(options = {}) {
    root.dataset.rayaCourseMapDrawer = "closed";
    clearCourseMapFilter();
    syncCourseMapDrawerState();
    if (options.restoreFocus && courseMapDrawerOpener) {
      courseMapDrawerOpener.focus();
    }
  }

  window.rayaOrientCourseMapToCurrentPage = () =>
    orientCourseMapToCurrentPage({ force: true });
  window.rayaOrientCourseMapToCurrentPageAutomatic = () =>
    orientCourseMapToCurrentPage();

  function syncLearningRailToggleButtons(nextExpanded) {
    const drawerOpen = root.dataset.rayaLearningRailDrawer === "open";
    const structuralShell = isStructuralRailShell();
    const commandExpanded = !structuralShell ? drawerOpen : nextExpanded;
    learningRailToggleButtons.forEach((button) => {
      button.setAttribute("aria-expanded", commandExpanded ? "true" : "false");
      const label = !structuralShell
          ? commandExpanded
            ? "Close learning context"
            : "Open learning context"
          : nextExpanded
            ? "Hide learning context"
            : "Show learning context";
      button.setAttribute("aria-label", label);
      syncTooltipDescription(button, label);
    });
  }

  function syncLearningRailDrawerState() {
    if (!learningRail || !learningRailBody) {
      return;
    }
    const structuralShell = isStructuralRailShell();
    if (!structuralShell && root.dataset.rayaLearningRailDrawer !== "closed") {
      root.dataset.rayaLearningRailDrawer = "closed";
    }
    const drawerOpen = root.dataset.rayaLearningRailDrawer === "open";
    root.setAttribute(
      "data-raya-learning-rail-scroll-lock",
      drawerOpen && !structuralShell ? "true" : "false"
    );
    if (learningRailDrawerBackdrop) {
      learningRailDrawerBackdrop.hidden = !drawerOpen;
    }
    if (!structuralShell) {
      learningRail.setAttribute("aria-hidden", "false");
      setElementInert(learningRail, false);
      setFocusableDescendantsEnabled(learningRail, true);
      applyRailBodyInert(learningRailBody, root.dataset.rayaLearningRail === "collapsed");
      railToggleButtons.forEach((button) => {
        setRailPanelExpanded(button, button.getAttribute("aria-expanded") === "true");
      });
      syncLearningRailToggleButtons(root.dataset.rayaLearningRail !== "collapsed");
      return;
    }
    learningRail.setAttribute("aria-hidden", "false");
    setElementInert(learningRail, false);
    setFocusableDescendantsEnabled(learningRail, true);
    const railExpanded = root.dataset.rayaLearningRail !== "collapsed";
    applyRailBodyInert(learningRailBody, !railExpanded);
    if (root.dataset.rayaLearningRailDrawer !== "closed") {
      root.dataset.rayaLearningRailDrawer = "closed";
    }
    root.setAttribute("data-raya-learning-rail-scroll-lock", "false");
    if (learningRailDrawerBackdrop) {
      learningRailDrawerBackdrop.hidden = true;
    }
    syncLearningRailToggleButtons(root.dataset.rayaLearningRail !== "collapsed");
    if (railExpanded) {
      railToggleButtons.forEach((button) => {
        setRailPanelExpanded(button, button.getAttribute("aria-expanded") === "true");
      });
    }
  }

  function syncLearningRailState(nextState, options = {}) {
    if (!learningRail || !learningRailBody) {
      return;
    }
    const nextExpanded = nextState === "expanded";
    const previousExpanded = options.previousState
      ? options.previousState !== "collapsed"
      : root.dataset.rayaLearningRail !== "collapsed";
    const desktopTransition =
      isStructuralRailShell()
      && previousExpanded !== nextExpanded
      && options.immediate !== true
      && !reducedMotionQuery.matches;
    const desktopExpanding = desktopTransition && nextExpanded;
    const focusAfterExpansion = Boolean(
      nextExpanded && options.focusAfterExpansion
    );
    if (desktopTransition) {
      window.clearTimeout(learningRailTransitionTimer);
      learningRail.dataset.rayaLearningRailTransition = nextExpanded
        ? "expanding"
        : "collapsing";
      learningRailTransitionTimer = window.setTimeout(() => {
        const shouldTransferFocus =
          desktopExpanding
          && focusAfterExpansion
          && root.dataset.rayaLearningRail === "expanded"
          && learningRail.dataset.rayaLearningRailTransition === "expanding"
          && document.activeElement === learningRailExpand;
        delete learningRail.dataset.rayaLearningRailTransition;
        if (shouldTransferFocus && learningRailCollapse) {
          learningRailCollapse.focus();
        }
      }, SHELL_TRANSITION_MS);
    } else {
      window.clearTimeout(learningRailTransitionTimer);
      delete learningRail.dataset.rayaLearningRailTransition;
    }
    syncLearningRailToggleButtons(nextExpanded);
    applyRailBodyInert(learningRailBody, !nextExpanded);
    if (nextExpanded) {
      railToggleButtons.forEach((button) => {
        setRailPanelExpanded(button, button.getAttribute("aria-expanded") === "true");
      });
    }
    if (learningRailCollapse) {
      learningRailCollapse.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
    }
    if (learningRailExpand) {
      learningRailExpand.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
    }
    syncLearningRailDrawerState();
    if (focusAfterExpansion) {
      if (desktopExpanding && learningRailExpand) {
        learningRailExpand.focus();
      } else if (learningRailCollapse) {
        learningRailCollapse.focus();
      }
    }
  }

  function openLearningRailDrawer(opener = null) {
    if (!learningRail || !learningRailBody) {
      return;
    }
    if (opener instanceof Element) {
      learningRailDrawerOpener = opener;
    }
    root.dataset.rayaLearningRailDrawer = "open";
    syncLearningRailDrawerState();
    window.requestAnimationFrame(() => {
      const focusTarget = learningRail.querySelector("button, a[href], summary");
      if (focusTarget) {
        focusTarget.focus();
      } else {
        learningRail.focus();
      }
    });
  }

  function closeLearningRailDrawer(options = {}) {
    root.dataset.rayaLearningRailDrawer = "closed";
    syncLearningRailDrawerState();
    if (options.restoreFocus && learningRailDrawerOpener) {
      learningRailDrawerOpener.focus();
    }
  }

  function setRailPanelExpanded(button, nextExpanded) {
    const bodyId = button.getAttribute("aria-controls");
    if (!bodyId) {
      return;
    }
    const body = document.getElementById(bodyId);
    const panel = button.closest(".raya-rail-panel");
    if (!body || !panel) {
      return;
    }
    panel.dataset.rayaRailPanelState = nextExpanded ? "expanded" : "collapsed";
    button.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
    body.setAttribute("aria-hidden", nextExpanded ? "false" : "true");
    setElementInert(body, !nextExpanded);
    setFocusableDescendantsEnabled(body, nextExpanded);
  }

  function isEditableNavigationTarget(target) {
    if (!(target instanceof Element)) {
      return false;
    }
    const tagName = target.tagName.toLowerCase();
    return (
      target.isContentEditable ||
      tagName === "input" ||
      tagName === "textarea" ||
      tagName === "select"
    );
  }

  function navigateToSequenceLink(selector) {
    const link = document.querySelector(selector);
    const href = link ? link.getAttribute("href") : "";
    if (!href) {
      return false;
    }
    window.location.href = href;
    return true;
  }

  function handleSequenceKeyboardNavigation(event) {
    if (isEditableNavigationTarget(event.target)) {
      return false;
    }
    if (event.ctrlKey || event.metaKey || event.shiftKey) {
      return false;
    }
    const previousRequested =
      (!event.altKey && event.key === "ArrowLeft") ||
      (event.altKey && event.key === "k");
    const nextRequested =
      (!event.altKey && event.key === "ArrowRight") ||
      (event.altKey && event.key === "j");
    if (!previousRequested && !nextRequested) {
      return false;
    }
    const selector = previousRequested
      ? "[data-raya-prev-page]"
      : "[data-raya-next-page]";
    if (!navigateToSequenceLink(selector)) {
      return false;
    }
    event.preventDefault();
    return true;
  }

  function resetCopyButton(button) {
    window.setTimeout(() => {
      button.textContent = "Copy";
      button.setAttribute("aria-label", "Copy code block");
      button.removeAttribute("data-raya-copy-state");
    }, 1600);
  }

  function copyWithFallback(text) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.top = "-1000px";
    document.body.appendChild(textarea);
    textarea.select();
    try {
      return document.execCommand("copy");
    } finally {
      textarea.remove();
    }
  }

  async function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
    return copyWithFallback(text);
  }

  function initializeCodeCopyControls() {
    document.querySelectorAll("[data-raya-copy-code]").forEach((button) => {
      button.addEventListener("click", async () => {
        const block = button.closest(".raya-code-block");
        const code = block ? block.querySelector("pre code") : null;
        if (!code) {
          return;
        }
        try {
          const copied = await copyText(code.textContent || "");
          button.textContent = copied ? "Copied" : "Copy failed";
          button.setAttribute(
            "aria-label",
            copied ? "Code block copied" : "Code block copy failed"
          );
          button.dataset.rayaCopyState = copied ? "copied" : "failed";
        } catch {
          button.textContent = "Copy failed";
          button.setAttribute("aria-label", "Code block copy failed");
          button.dataset.rayaCopyState = "failed";
        }
        resetCopyButton(button);
      });
    });
  }

  function ensureAssetInspector() {
    if (assetInspector) {
      return assetInspector;
    }
    assetInspector = document.createElement("div");
    assetInspector.className = "raya-asset-inspector";
    assetInspector.hidden = true;
    assetInspector.setAttribute("aria-hidden", "true");
    assetInspector.setAttribute("aria-modal", "true");
    assetInspector.setAttribute("data-raya-asset-inspector", "");
    assetInspector.setAttribute("role", "dialog");
    assetInspector.innerHTML = `
      <div class="raya-asset-inspector-panel" data-raya-asset-inspector-panel>
        <div class="raya-asset-inspector-header">
          <h2 id="raya-asset-inspector-title" data-raya-asset-inspector-title>Image</h2>
          <button class="raya-asset-inspector-close" type="button" data-raya-asset-inspector-close aria-label="Close image inspector">Close</button>
        </div>
        <figure class="raya-asset-inspector-figure">
          <img data-raya-asset-inspector-image alt="">
        </figure>
        <p class="raya-asset-inspector-actions">
          <a data-raya-asset-inspector-open href="">Open image file</a>
        </p>
      </div>
    `;
    assetInspector.setAttribute("aria-labelledby", "raya-asset-inspector-title");
    document.body.appendChild(assetInspector);
    assetInspector.addEventListener("click", (event) => {
      if (event.target === assetInspector) {
        closeAssetInspector({ restoreFocus: true });
      }
    });
    const close = assetInspector.querySelector("[data-raya-asset-inspector-close]");
    if (close) {
      close.addEventListener("click", () => closeAssetInspector({ restoreFocus: true }));
    }
    return assetInspector;
  }

  function assetInspectorIsOpen() {
    return Boolean(assetInspector && !assetInspector.hidden);
  }

  function trapAssetInspectorFocus(event) {
    if (!assetInspectorIsOpen() || event.key !== "Tab" || !assetInspector) {
      return false;
    }
    const focusable = focusableElementsWithin(assetInspector);
    if (focusable.length === 0) {
      event.preventDefault();
      assetInspector.focus();
      return true;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
      return true;
    }
    if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
      return true;
    }
    return false;
  }

  function openAssetInspector(button) {
    const inspector = ensureAssetInspector();
    const src = button.getAttribute("data-raya-asset-src") || "";
    const alt = button.getAttribute("data-raya-asset-alt") || "Image";
    const title = inspector.querySelector("[data-raya-asset-inspector-title]");
    const image = inspector.querySelector("[data-raya-asset-inspector-image]");
    const open = inspector.querySelector("[data-raya-asset-inspector-open]");
    assetInspectorOpener = button;
    if (title) title.textContent = alt;
    if (image) {
      image.setAttribute("src", src);
      image.setAttribute("alt", alt);
    }
    if (open) {
      open.setAttribute("href", src);
    }
    inspector.hidden = false;
    inspector.setAttribute("aria-hidden", "false");
    const close = inspector.querySelector("[data-raya-asset-inspector-close]");
    if (close) close.focus();
  }

  function closeAssetInspector({ restoreFocus } = { restoreFocus: false }) {
    if (!assetInspector) {
      return;
    }
    assetInspector.hidden = true;
    assetInspector.setAttribute("aria-hidden", "true");
    if (restoreFocus && assetInspectorOpener) {
      assetInspectorOpener.focus();
    }
    assetInspectorOpener = null;
  }

  function initializeAssetInspectorControls() {
    assetInspectButtons.forEach((button) => {
      button.addEventListener("click", () => openAssetInspector(button));
    });
  }

  function printableDisclosureElements() {
    return Array.from(
      document.querySelectorAll(
        ".raya-static-environment, .raya-official-reveal, .raya-connection-preview"
      )
    ).filter((element) => element instanceof HTMLDetailsElement);
  }

  function openPrintDisclosures() {
    printableDisclosureElements().forEach((details) => {
      if (details.open) {
        return;
      }
      details.dataset.rayaPrintOpened = "true";
      details.open = true;
    });
  }

  function restorePrintDisclosures() {
    printableDisclosureElements().forEach((details) => {
      if (details.dataset.rayaPrintOpened !== "true") {
        return;
      }
      details.open = false;
      delete details.dataset.rayaPrintOpened;
    });
  }

  function syncPrintDisclosureState() {
    if (printQuery.matches) {
      openPrintDisclosures();
    } else {
      restorePrintDisclosures();
    }
  }

  function readerShellReconciliationFocusTarget(activeElement, next) {
    if (!(activeElement instanceof Element)) {
      return null;
    }
    if (mobileMapOpener === activeElement && isStructuralRailShell()) {
      return courseMapFocusTarget(next.courseMap);
    }
    if (map.contains(activeElement)) {
      if (!isStructuralRailShell()) {
        return courseMapFocusTarget(next.courseMap);
      }
      if (activeElement === mapCloseButton) {
        return courseMapFocusTarget(next.courseMap);
      }
      if (
        next.courseMap === "collapsed" &&
        activeElement !== mapExpandButton
      ) {
        return courseMapFocusTarget(next.courseMap);
      }
      if (
        next.courseMap === "expanded" &&
        activeElement === mapExpandButton
      ) {
        return courseMapFocusTarget(next.courseMap);
      }
    }
    if (learningRail && learningRail.contains(activeElement)) {
      if (!isStructuralRailShell()) {
        if (
          activeElement === learningRailExpand ||
          activeElement === learningRailCollapse
        ) {
          return article;
        }
      } else if (
        next.learningRail === "collapsed" &&
        activeElement !== learningRailExpand
      ) {
        return learningRailExpand || article;
      } else if (
        next.learningRail === "expanded" &&
        activeElement === learningRailExpand
      ) {
        return article;
      }
    }
    return null;
  }

  function reconcileReaderShellState({
    restoreFocus = true,
    focusOwner = null,
    preferFocusedIntermediate = false,
  } = {}) {
    const activeElement = focusOwner instanceof Element ? focusOwner : document.activeElement;
    const preference = savedReaderShellPreference();
    const transitionPreference = preference || (
      preferFocusedIntermediate &&
      isMediumStructuralShell() &&
      root.dataset.rayaCourseMap === "expanded" &&
      root.dataset.rayaLearningRail === "expanded"
        ? {
          courseMap: root.dataset.rayaCourseMap,
          learningRail: root.dataset.rayaLearningRail,
        }
        : null
    );
    const next = preferFocusedIntermediate
      ? reconcileFocusedIntermediateState(transitionPreference, activeElement)
      : effectiveReaderShellState(preference);
    const arbitratingExpandedPair =
      preferFocusedIntermediate &&
      isMediumStructuralShell() &&
      transitionPreference &&
      transitionPreference.courseMap === "expanded" &&
      transitionPreference.learningRail === "expanded";
    const focusedRailBecomesInert =
      (next.courseMap === "collapsed" && map.contains(activeElement)) ||
      (next.learningRail === "collapsed" &&
        learningRail &&
        learningRail.contains(activeElement));
    let focusTarget = restoreFocus
      ? readerShellReconciliationFocusTarget(activeElement, next)
      : null;
    if (restoreFocus && focusedRailBecomesInert && arbitratingExpandedPair) {
      focusTarget = next.courseMap === "expanded"
        ? mapCollapseButton || mapExpandButton || article
        : learningRailCollapse || learningRailExpand || article;
    }
    applyStructuralRailPair(next.courseMap, next.learningRail, {
      immediate: true,
      persist: false,
      previousFocus: activeElement,
      focusTarget,
      restoreFocus,
    });
  }

  let pendingReaderShellFocusOwner = null;
  let pendingReaderShellFocusOwnerFrame = 0;

  function clearPendingReaderShellFocusOwner() {
    pendingReaderShellFocusOwner = null;
    if (pendingReaderShellFocusOwnerFrame) {
      window.cancelAnimationFrame(pendingReaderShellFocusOwnerFrame);
      pendingReaderShellFocusOwnerFrame = 0;
    }
  }

  function takePendingReaderShellFocusOwner() {
    const focusOwner =
      pendingReaderShellFocusOwner && pendingReaderShellFocusOwner.isConnected
        ? pendingReaderShellFocusOwner
        : null;
    clearPendingReaderShellFocusOwner();
    return focusOwner;
  }

  const handleReaderShellMediaChange = () => {
    const focusOwner = takePendingReaderShellFocusOwner();
    reconcileReaderShellState({
      restoreFocus: true,
      focusOwner,
      preferFocusedIntermediate: true,
    });
  };
  document.addEventListener("focusout", (event) => {
    const focusOwner = event.target;
    const ownsFocus =
      focusOwner instanceof Element &&
      focusOwner.isConnected &&
      (focusOwner === mobileMapOpener ||
        map.contains(focusOwner) ||
        (learningRail && learningRail.contains(focusOwner)));
    if (event.relatedTarget !== null || !ownsFocus) {
      return;
    }
    clearPendingReaderShellFocusOwner();
    pendingReaderShellFocusOwner = focusOwner;
    pendingReaderShellFocusOwnerFrame = window.requestAnimationFrame(() => {
      pendingReaderShellFocusOwner = null;
      pendingReaderShellFocusOwnerFrame = 0;
    });
  }, true);
  document.addEventListener("focusin", clearPendingReaderShellFocusOwner, true);
  window.addEventListener("pagehide", clearPendingReaderShellFocusOwner);
  window.addEventListener("pageshow", (event) => {
    clearPendingReaderShellFocusOwner();
    if (!event.persisted) return;
    const preference = readReaderShellPreference();
    if (preference) {
      root.dataset.rayaCourseMapPreference = preference.courseMap;
      root.dataset.rayaLearningRailPreference = preference.learningRail;
    } else {
      delete root.dataset.rayaCourseMapPreference;
      delete root.dataset.rayaLearningRailPreference;
    }
    reconcileReaderShellState({ restoreFocus: true, preferFocusedIntermediate: true });
    if (mapFilter) {
      applyCourseMapFilter();
    } else {
      applyEffectiveMapState();
    }
  });
  [
    structuralRailQuery,
    compactStructuralRailQuery,
    approvedRailGeometryQuery,
    desktopMapQuery,
  ].forEach((query) => {
    if (query.addEventListener) {
      query.addEventListener("change", handleReaderShellMediaChange);
    } else if (query.addListener) {
      query.addListener(handleReaderShellMediaChange);
    }
  });
  if (printQuery.addEventListener) {
    printQuery.addEventListener("change", syncPrintDisclosureState);
  } else if (printQuery.addListener) {
    printQuery.addListener(syncPrintDisclosureState);
  }
  window.addEventListener("beforeprint", openPrintDisclosures);
  window.addEventListener("afterprint", restorePrintDisclosures);

  toggleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (!isStructuralRailShell()) {
        if (root.dataset.rayaCourseMapDrawer === "open") {
          closeCourseMapDrawer({ restoreFocus: true });
        } else {
          openCourseMapDrawer(button);
        }
        return;
      }
      const nextExpanded = root.dataset.rayaCourseMap !== "expanded";
      const nextLearningRail = nextExpanded && isMediumStructuralShell()
        ? "collapsed"
        : root.dataset.rayaLearningRail;
      applyStructuralRailPair(
        nextExpanded ? "expanded" : "collapsed",
        nextLearningRail,
        {
          restoreFocus: !(nextExpanded && button === mapExpandButton),
          focusTarget: map.contains(button) && !nextExpanded
            ? courseMapFocusTarget(nextExpanded ? "expanded" : "collapsed")
            : null,
          focusCourseMapAfterExpansion: nextExpanded && button === mapExpandButton,
        }
      );
    });
  });

  if (mapCloseButton) {
    mapCloseButton.addEventListener("click", () => {
      closeCourseMapDrawer({ restoreFocus: true });
    });
  }

  if (mapDrawerBackdrop) {
    mapDrawerBackdrop.addEventListener("click", () => {
      closeCourseMapDrawer({ restoreFocus: true });
    });
  }

  if (learningRailDrawerBackdrop) {
    learningRailDrawerBackdrop.addEventListener("click", () => {
      closeLearningRailDrawer({ restoreFocus: true });
    });
  }

  const storedCollapsedMapBranches = loadCollapsedMapNodeIds();
  const hasStoredMapBranchState = storedCollapsedMapBranches !== null;
  mapNodeToggles.forEach((button) => {
    const node = button.closest("[data-raya-map-node]");
    if (!node) {
      return;
    }
    if (!controlledMapNodeChildren(node, button)) {
      replaceInvalidMapNodeToggle(node, button);
      return;
    }
    const nodeId = mapNodeId(node);
    const defaultExpanded = button.getAttribute("aria-expanded") === "true";
    const restoredExpanded = hasStoredMapBranchState
      ? !storedCollapsedMapBranches.has(nodeId)
      : defaultExpanded;
    setMapNodePreference(node, restoredExpanded);
    button.addEventListener("click", () => {
      applyDirectMapBranchAction(node, "toggle");
    });
  });
  if (mapFilter) {
    mapFilter.addEventListener("input", () => {
      applyCourseMapFilter();
    });
    applyCourseMapFilter();
  } else {
    applyEffectiveMapState();
    expandCurrentCourseMapPath();
  }

  map.addEventListener("keydown", handleCourseMapKeyboardNavigation);

  railToggleButtons.forEach((button) => {
    setRailPanelExpanded(button, button.getAttribute("aria-expanded") === "true");
    button.addEventListener("click", () => {
      setRailPanelExpanded(button, button.getAttribute("aria-expanded") !== "true");
    });
  });

  if (learningRailCollapse) {
    learningRailCollapse.addEventListener("click", () => {
      if (!isStructuralRailShell()) {
        closeLearningRailDrawer({ restoreFocus: true });
        return;
      }
      applyStructuralRailPair(
        root.dataset.rayaCourseMap,
        "collapsed",
        { focusTarget: learningRailExpand }
      );
    });
  }

  if (learningRailExpand) {
    learningRailExpand.addEventListener("click", () => {
      applyStructuralRailPair(
        isMediumStructuralShell() ? "collapsed" : root.dataset.rayaCourseMap,
        "expanded",
        {
          persist: true,
          restoreFocus: false,
          focusAfterExpansion: true,
        }
      );
    });
  }

  learningRailToggleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (!isStructuralRailShell()) {
        if (root.dataset.rayaCourseMapDrawer === "open") {
          closeCourseMapDrawer({ restoreFocus: false });
        }
        applyStructuralRailPair("expanded", "expanded", {
          immediate: true,
          persist: false,
          restoreFocus: false,
        });
        if (learningRail) {
          learningRail.setAttribute("tabindex", "-1");
          window.requestAnimationFrame(() => {
            learningRail.scrollIntoView({ block: "start" });
            learningRail.focus();
          });
        }
        return;
      }
      const nextExpanded = root.dataset.rayaLearningRail !== "expanded";
      applyStructuralRailPair(
        nextExpanded && isMediumStructuralShell()
          ? "collapsed"
          : root.dataset.rayaCourseMap,
        nextExpanded ? "expanded" : "collapsed",
        {
          persist: true,
          restoreFocus: !nextExpanded,
          focusTarget: nextExpanded ? null : learningRailExpand,
          focusAfterExpansion: nextExpanded,
        }
      );
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && root.dataset.rayaCourseMapDrawer === "open") {
      event.preventDefault();
      closeCourseMapDrawer({ restoreFocus: true });
      return;
    }
    if (event.key === "Escape" && dismissActiveTooltip()) {
      event.preventDefault();
      return;
    }
    if (assetInspectorIsOpen()) {
      if (event.key === "Escape") {
        event.preventDefault();
        closeAssetInspector({ restoreFocus: true });
        return;
      }
      if (trapAssetInspectorFocus(event)) {
        return;
      }
    }
    if (handleSequenceKeyboardNavigation(event)) {
      return;
    }
    if (trapCourseMapDrawerFocus(event)) {
      return;
    }
    if (trapLearningRailDrawerFocus(event)) {
      return;
    }
    if (event.key === "Escape" && root.dataset.rayaLearningRailDrawer === "open") {
      closeLearningRailDrawer({ restoreFocus: true });
      return;
    }
    let structuralRailChanged = false;
    if (
      event.key === "Escape" &&
      isStructuralRailShell() &&
      root.dataset.rayaCourseMap === "expanded"
    ) {
      const activeElement = document.activeElement;
      const mapOwnsFocus =
        activeElement instanceof Element &&
        map.contains(activeElement);
      if (mapOwnsFocus) {
        applyStructuralRailPair(
          "collapsed",
          root.dataset.rayaLearningRail,
          { persist: false, focusTarget: courseMapFocusTarget("collapsed") }
        );
        structuralRailChanged = true;
      }
    }
    if (
      event.key === "Escape" &&
      isStructuralRailShell() &&
      root.dataset.rayaLearningRail === "expanded"
    ) {
      const activeElement = document.activeElement;
      const shouldMoveFocus =
        activeElement instanceof Element &&
        learningRail &&
        learningRail.contains(activeElement);
      if (shouldMoveFocus) {
        applyStructuralRailPair(
          root.dataset.rayaCourseMap,
          "collapsed",
          { persist: false, focusTarget: learningRailExpand }
        );
        structuralRailChanged = true;
      }
    }
    if (structuralRailChanged) {
      saveReaderShellPreference();
    }
  });

  function updateActiveHeading() {
    if (headings.length === 0) {
      return;
    }
    const activationLine = window.innerHeight * 0.3;
    const active = headings.reduce((current, item) => {
      const top = item.target.getBoundingClientRect().top;
      if (top <= activationLine) {
        return item;
      }
      return current;
    }, headings[0]);
    tocLinks.forEach((link) => link.removeAttribute("aria-current"));
    active.link.setAttribute("aria-current", "location");
    syncCurrentSection(active.link);
  }

  function syncCurrentSection(activeLink) {
    if (currentSectionLinks.length === 0 || !activeLink) {
      return;
    }
    const href = activeLink.getAttribute("href") || "";
    if (href.startsWith("#raya-generated-")) {
      return;
    }
    const label = activeLink.textContent || "Current section";
    currentSectionLinks.forEach((currentSectionLink) => {
      const isCommandChip = currentSectionLink.classList.contains("raya-reading-context-section");
      const nextLabel = isCommandChip ? `Current section: ${label}` : label;
      if (currentSectionLink.getAttribute("href") !== href) {
        currentSectionLink.setAttribute("href", href);
      }
      if (isCommandChip) {
        const visibleLabel = currentSectionLink.querySelector(".raya-reading-context-section-label");
        if (visibleLabel && visibleLabel.textContent !== label) {
          visibleLabel.textContent = label;
        } else if (!visibleLabel && currentSectionLink.textContent !== `Now ${label}`) {
          currentSectionLink.textContent = `Now ${label}`;
        }
      } else if (currentSectionLink.textContent !== label) {
        currentSectionLink.textContent = label;
      }
      if (currentSectionLink.getAttribute("aria-label") !== nextLabel) {
        currentSectionLink.setAttribute("aria-label", nextLabel);
      }
    });
  }

  function setActiveKeyObject(id) {
    keyObjectLinks.forEach((link) => {
      const isActive = Boolean(id) && link.getAttribute("data-raya-key-object-link") === id;
      if (isActive) {
        link.setAttribute("aria-current", "location");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  }

  function initializeOfficialQuizControls() {
    const questions = Array.from(document.querySelectorAll("[data-raya-official-quiz-question]"));
    questions.forEach((question) => {
      const options = Array.from(
        question.querySelectorAll("[data-raya-official-quiz-option]")
      );
      const reset = question.querySelector("[data-raya-official-quiz-reset]");
      const feedback = question.querySelector("[data-raya-official-quiz-feedback]");
      if (options.length === 0 || !reset || !feedback) {
        return;
      }

      function setReady() {
        question.setAttribute("data-raya-official-quiz-state", "ready");
        options.forEach((option) => {
          option.disabled = false;
          option.removeAttribute("aria-pressed");
          option.removeAttribute("data-raya-official-quiz-selected");
          option.removeAttribute("data-raya-official-quiz-result");
        });
        reset.hidden = true;
        feedback.textContent = "Choose an option.";
      }

      options.forEach((option) => {
        option.addEventListener("click", () => {
          const isCorrect =
            option.getAttribute("data-raya-official-quiz-correct") === "true";
          question.setAttribute("data-raya-official-quiz-state", "answered");
          options.forEach((candidate) => {
            const candidateCorrect =
              candidate.getAttribute("data-raya-official-quiz-correct") === "true";
            candidate.disabled = true;
            candidate.setAttribute(
              "aria-pressed",
              candidate === option ? "true" : "false"
            );
            candidate.removeAttribute("data-raya-official-quiz-selected");
            candidate.removeAttribute("data-raya-official-quiz-result");
            if (candidate === option) {
              candidate.setAttribute("data-raya-official-quiz-selected", "true");
            }
            if (candidateCorrect) {
              candidate.setAttribute("data-raya-official-quiz-result", "correct");
            }
          });
          if (!isCorrect) {
            option.setAttribute("data-raya-official-quiz-result", "incorrect");
          }
          feedback.textContent = isCorrect
            ? "Correct."
            : "Try again. The correct option is available below.";
          reset.hidden = false;
        });
      });

      reset.addEventListener("click", setReady);
      setReady();
    });
  }

  if (headings.length > 0) {
    updateActiveHeading();
    window.addEventListener("scroll", updateActiveHeading, { passive: true });
    window.addEventListener("resize", updateActiveHeading);
  }
  if (keyObjectLinks.length > 0 && keyObjectTargets.length > 0 && "IntersectionObserver" in window) {
    const activeObjects = new Set();
    const objectObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          activeObjects.add(entry.target.id);
        } else {
          activeObjects.delete(entry.target.id);
        }
      });
      const activeTarget = keyObjectTargets.find((target) => activeObjects.has(target.id));
      setActiveKeyObject(activeTarget ? activeTarget.id : "");
    }, { rootMargin: "-20% 0px -55% 0px", threshold: 0 });
    keyObjectTargets.forEach((target) => objectObserver.observe(target));
  }

  reconcileReaderShellState({ restoreFocus: false });
  window.requestAnimationFrame(() => orientCourseMapToCurrentPage());
  initializeCodeCopyControls();
  initializeAssetInspectorControls();
  initializeOfficialQuizControls();
  root.dataset.rayaShellReady = "true";
})();
"""
