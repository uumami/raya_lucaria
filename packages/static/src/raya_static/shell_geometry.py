from __future__ import annotations

RAIL_STRUCTURAL_PX = 640
RAIL_APPROVED_PX = 894
RAIL_DESKTOP_PX = 1280

# The one definition of the effective-state rule, embedded verbatim in BOTH
# the prepaint and runtime scripts. Pure function of (preference, width):
#   < 640            -> both expanded (left is presented as a drawer in CSS/JS)
#   >= 894           -> caller's preference (default expanded)
#   640..893, both expanded -> collapse both (medium-band mutual exclusion)
#
# NOTE: built directly from the RAIL_STRUCTURAL_PX / RAIL_APPROVED_PX ints
# (not from the __RAYA_*_PX__ placeholder tokens) so this constant is already
# the final, byte-identical JS text. apply_rail_geometry_tokens's single
# text.replace pass would otherwise resolve any placeholder tokens embedded
# here too (see the docstring below), which would make the embedded text
# diverge from this module-level constant after substitution — breaking the
# byte-identical-across-scripts guarantee the guardrail test checks for.
RAIL_EFFECTIVE_DERIVATION_JS = (
    "function rayaEffectiveRailState(courseMap, learningRail, width) {\n"
    f"  if (width < {RAIL_STRUCTURAL_PX}) {{\n"
    "    return { courseMap: \"expanded\", learningRail: \"expanded\" };\n"
    "  }\n"
    f"  if (width < {RAIL_APPROVED_PX} && courseMap === \"expanded\""
    " && learningRail === \"expanded\") {\n"
    "    return { courseMap: \"collapsed\", learningRail: \"collapsed\" };\n"
    "  }\n"
    "  return { courseMap: courseMap, learningRail: learningRail };\n"
    "}"
)

_TOKENS = {
    "__RAYA_RAIL_DERIVATION__": RAIL_EFFECTIVE_DERIVATION_JS,
    "__RAYA_STRUCTURAL_PX__": str(RAIL_STRUCTURAL_PX),
    "__RAYA_APPROVED_PX__": str(RAIL_APPROVED_PX),
    "__RAYA_DESKTOP_PX__": str(RAIL_DESKTOP_PX),
}


def apply_rail_geometry_tokens(text: str) -> str:
    """Substitute rail-geometry placeholder tokens.

    Placeholder tokens (not f-strings/.format) are required because the JS/CSS
    bodies are dense with braces. The derivation token is expanded first, then
    the numeric tokens inside it are resolved.
    """
    for token, value in _TOKENS.items():
        text = text.replace(token, str(value))
    return text
