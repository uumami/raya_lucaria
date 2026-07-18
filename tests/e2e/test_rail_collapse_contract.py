from pathlib import Path

import raya_static.rendering as rendering_module
from raya_static.rendering import rich_render_css
from raya_static.shell import shell_resources
from raya_static.shell_prepaint import shell_prepaint_javascript
from raya_static.shell_geometry import (
    _TOKENS,
    RAIL_APPROVED_PX,
    RAIL_EFFECTIVE_DERIVATION_JS,
)


def test_rail_geometry_is_single_sourced_across_scripts():
    runtime = shell_resources().javascript
    prepaint = shell_prepaint_javascript()
    # No un-substituted tokens leak into emitted scripts.
    for token in ("__RAYA_STRUCTURAL_PX__", "__RAYA_APPROVED_PX__",
                  "__RAYA_DESKTOP_PX__", "__RAYA_RAIL_DERIVATION__"):
        assert token not in runtime, token
        assert token not in prepaint, token
    # Boundaries agree across scripts.
    assert "(min-width: 894px)" in runtime
    assert "894" in prepaint and "640" in prepaint and "640" in runtime
    # The pairwise derivation is byte-identical in both scripts (no rule drift).
    assert RAIL_EFFECTIVE_DERIVATION_JS in runtime
    assert RAIL_EFFECTIVE_DERIVATION_JS in prepaint


def test_css_and_js_share_the_same_rail_boundaries():
    # The approved-geometry complement token must exist in the single source
    # of truth (guards against the CSS boundary being re-hardcoded instead
    # of derived from RAIL_APPROVED_PX).
    assert _TOKENS["__RAYA_APPROVED_MINUS_PX__"] == str(RAIL_APPROVED_PX - 1)

    # Assert against the UN-SUBSTITUTED template source, not the substituted
    # output. rich_render_css() resolves tokens before returning, so checking
    # only its output can never distinguish "value happens to match" from
    # "value is sourced from the shared token" — a hardcoded literal that
    # equals the current token value would pass an output-only check and
    # silently reintroduce drift risk the next time RAIL_APPROVED_PX etc.
    # change. Reading the template source is what actually proves the
    # rail-collapse @media boundaries are token-sourced.
    source = Path(rendering_module.__file__).read_text(encoding="utf-8")
    assert "(min-width: __RAYA_STRUCTURAL_PX__px)" in source
    assert "(min-width: __RAYA_APPROVED_PX__px)" in source
    assert "(max-width: __RAYA_APPROVED_MINUS_PX__px)" in source

    # And the substituted output is still the final, token-free CSS with the
    # expected resolved boundaries (belt-and-suspenders on top of the
    # source-level check above).
    css = rich_render_css()
    for token in ("__RAYA_STRUCTURAL_PX__", "__RAYA_APPROVED_PX__",
                  "__RAYA_DESKTOP_PX__", "__RAYA_APPROVED_MINUS_PX__"):
        assert token not in css, token
    # The approved-geometry boundary appears in CSS exactly as in JS.
    assert "(min-width: 894px)" in css
    # Its complement is emitted from the same source (guards the sub-pixel gap).
    assert "(max-width: 893px)" in css
    # The structural boundary is shared too.
    assert "(min-width: 640px)" in css
