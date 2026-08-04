from __future__ import annotations

RAIL_STRUCTURAL_PX = 640
RAIL_APPROVED_PX = 894
RAIL_EXPANDED_PX = 256
RAIL_MINI_PX = 48
RAIL_DESKTOP_PX = 1280
RAIL_COMPACT_PX = 768

# defaultRailExpanded() (shell.py) drops its isDesktopShell() term because
# desktop implies approved. That reduction is only valid while this holds,
# and nothing else enforces it -- make it structural, not coincidental.
assert RAIL_DESKTOP_PX > RAIL_APPROVED_PX > RAIL_STRUCTURAL_PX

# The one definition of the effective-state rule, embedded verbatim in BOTH
# the prepaint and runtime scripts. Pure function of (preference, bands):
#   not structural   -> both expanded (left is presented as a drawer in CSS/JS)
#   approved         -> caller's preference (default expanded)
#   structural & !approved & both expanded -> keep left expanded (medium-band
#                                             mutual exclusion)
#
# Bands are read via matchMedia against the SAME boundary strings the CSS
# @media rules use, so JS and CSS converge on the same answer. Deriving from
# innerWidth instead allows a PERMANENT mismatch on engines where the
# media-query width excludes a classic scrollbar.
#
# The prepaint read is PROVISIONAL: shell-prepaint.js runs before any
# stylesheet and before <body>, so no scrollbar exists yet and the query
# returns the no-scrollbar answer. Agreement is reached once shell.js runs
# and the MQ change listeners fire.
#
# `printing` forces the widest band. During print, viewport media features
# resolve against the PAGE BOX (~700-760px at A4/Letter 96dpi), which would
# otherwise flip `approved` false and collapse BOTH rails in the printout for
# any user with an expanded/expanded preference. innerWidth was immune
# because it is not re-scoped to the page box.
#
# NOTE: built directly from the RAIL_STRUCTURAL_PX / RAIL_APPROVED_PX ints
# (not from the __RAYA_*_PX__ placeholder tokens) so this constant is already
# the final, byte-identical JS text — it contains no embedded __RAYA_*__
# tokens. If it were built from placeholder tokens instead,
# apply_rail_geometry_tokens's text.replace pass would resolve those tokens
# too (see the docstring below), which would make the embedded text diverge
# from this module-level constant after substitution — breaking the
# byte-identical-across-scripts guarantee the guardrail test checks for.
RAIL_EFFECTIVE_DERIVATION_JS = (
    "function rayaRailBands() {\n"
    "  var printing = matchMedia(\"print\").matches;\n"
    "  return {\n"
    "    structural: printing || matchMedia(\"(min-width: "
    + str(RAIL_STRUCTURAL_PX) + "px)\").matches,\n"
    "    approved: printing || matchMedia(\"(min-width: "
    + str(RAIL_APPROVED_PX) + "px)\").matches\n"
    "  };\n"
    "}\n"
    "function rayaEffectiveRailState(courseMap, learningRail, bands) {\n"
    "  if (!bands.structural) {\n"
    "    return { courseMap: \"expanded\", learningRail: \"expanded\" };\n"
    "  }\n"
    "  if (!bands.approved && courseMap === \"expanded\""
    " && learningRail === \"expanded\") {\n"
    "    return { courseMap: \"expanded\", learningRail: \"collapsed\" };\n"
    "  }\n"
    "  return { courseMap: courseMap, learningRail: learningRail };\n"
    "}"
)

_TOKENS = {
    "__RAYA_RAIL_DERIVATION__": RAIL_EFFECTIVE_DERIVATION_JS,
    "__RAYA_STRUCTURAL_PX__": str(RAIL_STRUCTURAL_PX),
    "__RAYA_APPROVED_PX__": str(RAIL_APPROVED_PX),
    "__RAYA_RAIL_EXPANDED_PX__": str(RAIL_EXPANDED_PX),
    "__RAYA_RAIL_MINI_PX__": str(RAIL_MINI_PX),
    "__RAYA_DESKTOP_PX__": str(RAIL_DESKTOP_PX),
    "__RAYA_STRUCTURAL_MINUS_PX__": str(RAIL_STRUCTURAL_PX - 1),
    "__RAYA_APPROVED_MINUS_PX__": str(RAIL_APPROVED_PX - 1),
    "__RAYA_COMPACT_MINUS_PX__": str(RAIL_COMPACT_PX - 1),
}


def apply_rail_geometry_tokens(text: str) -> str:
    """Substitute rail-geometry placeholder tokens.

    Placeholder tokens (not f-strings/.format) are required because the JS/CSS
    bodies are dense with braces. Each token is substituted via a plain
    str.replace pass. RAIL_EFFECTIVE_DERIVATION_JS is already pre-resolved
    from the numeric ints (RAIL_STRUCTURAL_PX / RAIL_APPROVED_PX) and contains
    no embedded __RAYA_*__ tokens, so substituting it introduces nothing
    further to resolve. _TOKENS retains an explicit ordering (derivation
    token first, then the numeric tokens) for interface stability, not
    because substitution order affects correctness — dict iteration order
    matches insertion order, and each replace pass is independent.
    """
    for token, value in _TOKENS.items():
        text = text.replace(token, str(value))
    return text
