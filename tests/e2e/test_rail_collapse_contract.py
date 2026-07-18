from raya_static.shell import shell_resources
from raya_static.shell_prepaint import shell_prepaint_javascript
from raya_static.shell_geometry import RAIL_EFFECTIVE_DERIVATION_JS


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
