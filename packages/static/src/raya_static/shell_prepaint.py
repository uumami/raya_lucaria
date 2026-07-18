from __future__ import annotations

from raya_static.shell_geometry import apply_rail_geometry_tokens


SHELL_PREPAINT_SCRIPT_NAME = "shell-prepaint.js"


def shell_prepaint_javascript() -> str:
    return apply_rail_geometry_tokens(_SHELL_PREPAINT_JAVASCRIPT)


_SHELL_PREPAINT_JAVASCRIPT = r"""
(() => {
  const root = document.documentElement;
  const courseId = root.dataset.rayaCourseId || "";
  __RAYA_RAIL_DERIVATION__
  const applyEffective = (courseMap, learningRail) => {
    const result = rayaEffectiveRailState(courseMap, learningRail, innerWidth);
    root.dataset.rayaCourseMap = result.courseMap;
    root.dataset.rayaLearningRail = result.learningRail;
  };
  const applyDefaults = () => {
    const expanded = innerWidth < __RAYA_STRUCTURAL_PX__ || innerWidth >= __RAYA_APPROVED_PX__;
    applyEffective(expanded ? "expanded" : "collapsed", expanded ? "expanded" : "collapsed");
  };
  if (!/^[a-z0-9][a-z0-9._-]*$/.test(courseId)) {
    applyDefaults();
    root.dataset.rayaShellPrepaint = "invalid";
    return;
  }
  let raw;
  try {
    raw = sessionStorage.getItem(`raya:reader-shell:v1:${courseId}`);
  } catch (_error) {
    applyDefaults();
    root.dataset.rayaShellPrepaint = "unavailable";
    return;
  }
  if (raw === null) {
    applyDefaults();
    root.dataset.rayaShellPrepaint = "missing";
    return;
  }
  try {
    const value = JSON.parse(raw);
    const keys = Object.keys(value || {}).sort();
    const valid = (state) => state === "expanded" || state === "collapsed";
    if (keys.length !== 2 || keys[0] !== "courseMap" || keys[1] !== "learningRail"
        || !valid(value.courseMap) || !valid(value.learningRail)) {
      applyDefaults();
      root.dataset.rayaShellPrepaint = "invalid";
      return;
    }
    root.dataset.rayaCourseMapPreference = value.courseMap;
    root.dataset.rayaLearningRailPreference = value.learningRail;
    applyEffective(value.courseMap, value.learningRail);
    root.dataset.rayaShellPrepaint = "valid";
  } catch (_error) {
    applyDefaults();
    root.dataset.rayaShellPrepaint = "invalid";
  }
})();
"""
