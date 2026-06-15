from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RENDER_FIXTURE = ROOT / "examples" / "courses" / "render-fixture"
SCRIPT = ROOT / "scripts" / "check-render-debug.sh"


def run_gate(
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = {**os.environ, **(env or {})}
    merged_env.setdefault("UV_PROJECT_ENVIRONMENT", ".venv-local")
    return subprocess.run(
        [str(SCRIPT), *args],
        cwd=ROOT,
        env=merged_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )


def test_render_debug_parity_gate_passes_on_render_fixture_copy(tmp_path: Path) -> None:
    course = tmp_path / "render-fixture"
    debug_dir = tmp_path / "debug"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    result = run_gate(
        env={
            "RAYA_RENDER_DEBUG_COURSE": str(course),
            "RAYA_RENDER_DEBUG_OUTPUT_DIR": str(debug_dir),
            "RAYA_RENDER_DEBUG_KEEP": "1",
        },
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "check-render-debug: passed" in result.stdout
    assert (debug_dir / "summary.json").is_file()
    assert (debug_dir / "desktop-index.png").stat().st_size > 0
    assert (debug_dir / "mobile-static-path.png").stat().st_size > 0
    report_json = json.loads((debug_dir / "report.json").read_text(encoding="utf-8"))
    report_html = (debug_dir / "index.html").read_text(encoding="utf-8")

    assert report_json["ok"] is True
    assert report_json["copied_site_dir"] is not None
    copied_site_dir = Path(report_json["copied_site_dir"]).resolve()
    original_site_dir = (course / "artifact" / "site").resolve()
    assert not copied_site_dir.exists()
    assert copied_site_dir != original_site_dir
    assert not copied_site_dir.is_relative_to(course.resolve())
    original_fonts = sorted(
        path.relative_to(original_site_dir)
        for path in (original_site_dir / "_raya" / "render" / "math" / "fonts").glob(
            "*.woff2"
        )
    )
    assert original_fonts
    assert any(check["id"] == "site:copied-site" for check in report_json["checks"])
    assert any(
        check["id"] == "copied-site:html:index.html"
        and check["status"] == "pass"
        for check in report_json["checks"]
    )
    assert any(
        check["id"] == "copied-site:math:css"
        and check["status"] == "pass"
        for check in report_json["checks"]
    )
    assert "Render Debug Inspection Report" in report_html
    assert "Copied site:" in report_html


def test_render_debug_parity_gate_inspects_explicit_copied_site_contents(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    copied_site = tmp_path / "copied-site"
    shutil.copytree(site_dir, copied_site)

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir), str(copied_site))

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((debug_dir / "report.json").read_text(encoding="utf-8"))
    assert report["ok"] is True
    assert Path(report["copied_site_dir"]).resolve() == copied_site.resolve()
    assert any(check["id"] == "site:copied-site" for check in report["checks"])

    assert copied_site.is_dir()
    assert copied_site.resolve() != site_dir.resolve()
    assert not copied_site.resolve().is_relative_to(site_dir.resolve())
    assert (copied_site / "index.html").read_text(encoding="utf-8") == (
        site_dir / "index.html"
    ).read_text(encoding="utf-8")
    assert (
        copied_site / "_raya" / "render" / "math" / "mathjax.css"
    ).read_text(encoding="utf-8") == (
        site_dir / "_raya" / "render" / "math" / "mathjax.css"
    ).read_text(encoding="utf-8")
    original_fonts = {
        path.relative_to(site_dir): path
        for path in site_dir.rglob("*.woff2")
        if path.is_file()
    }
    copied_fonts = {
        path.relative_to(copied_site): path
        for path in copied_site.rglob("*.woff2")
        if path.is_file()
    }
    assert original_fonts
    assert set(copied_fonts) == set(original_fonts)
    for relative_path, original_font in original_fonts.items():
        assert copied_fonts[relative_path].read_bytes() == original_font.read_bytes()


def test_render_debug_parity_gate_fails_on_visible_raw_tex(tmp_path: Path) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    summary_path = debug_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["captures"][0]["raw_tex_visible"] = True
    summary["captures"][0]["raw_tex_markers"] = ["$x^2$"]
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir))

    assert result.returncode == 1
    assert "visible raw TeX" in result.stderr


def test_render_debug_parity_gate_fails_on_external_requests(tmp_path: Path) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    summary_path = debug_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["captures"][1]["external_requests"] = ["https://cdn.example/math.css"]
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir))

    assert result.returncode == 1
    assert "external requests" in result.stderr


def test_render_debug_parity_gate_fails_on_missing_screenshot(tmp_path: Path) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    (debug_dir / "mobile-static-path.png").unlink()

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir))

    assert result.returncode == 1
    assert "missing or empty screenshot" in result.stderr


def test_render_debug_parity_gate_report_is_written_on_failure(tmp_path: Path) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    (debug_dir / "mobile-static-path.png").unlink()

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir))

    assert result.returncode == 1
    assert "debug report" in result.stderr or "render-debug-report:" in result.stdout
    assert (debug_dir / "report.json").is_file()
    assert (debug_dir / "index.html").is_file()
    report = json.loads((debug_dir / "report.json").read_text(encoding="utf-8"))
    assert report["ok"] is False
    assert any(
        "missing or empty screenshot" in item["message"]
        for item in report["diagnostics"]
    )


def test_render_debug_parity_gate_fails_on_horizontal_overflow(tmp_path: Path) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    summary_path = debug_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["captures"][2]["horizontal_overflow"] = 12
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir))

    assert result.returncode == 1
    assert "horizontal overflow" in result.stderr


def test_render_debug_parity_gate_fails_on_browser_side_mathjax_runtime(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    html_path = site_dir / "index.html"
    html_path.write_text(
        (
            '<html><head><script src="https://cdn.jsdelivr.net/npm/mathjax/'
            'tex-mml-chtml.js"></script></head></html>'
        ),
        encoding="utf-8",
    )

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir))

    assert result.returncode == 1
    assert "browser-side or external renderer dependency" in result.stderr


def test_render_debug_parity_gate_fails_on_local_mathjax_runtime_script(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    html_path = site_dir / "index.html"
    html_path.write_text(
        '<html><head><script src="_raya/render/math/tex-chtml.js"></script></head></html>',
        encoding="utf-8",
    )

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir))

    assert result.returncode == 1
    assert "browser-side or external renderer dependency" in result.stderr


def test_render_debug_parity_gate_fails_when_copied_site_has_browser_runtime(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    copied_site = tmp_path / "copied-site"
    shutil.copytree(site_dir, copied_site)
    (copied_site / "index.html").write_text(
        '<html><head><script src="_raya/render/math/tex-chtml.js"></script></head></html>',
        encoding="utf-8",
    )

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir), str(copied_site))

    assert result.returncode == 1
    report = json.loads((debug_dir / "report.json").read_text(encoding="utf-8"))
    assert any(
        item["path"].startswith(str(copied_site))
        and "browser-side or external renderer dependency" in item["message"]
        for item in report["diagnostics"]
    )


def test_render_debug_parity_gate_fails_when_copied_site_lacks_math_css(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    copied_site = tmp_path / "copied-site"
    shutil.copytree(site_dir, copied_site)
    (copied_site / "_raya" / "render" / "math" / "mathjax.css").unlink()

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir), str(copied_site))

    assert result.returncode == 1
    assert "missing local MathJax CSS" in result.stderr


def test_render_debug_parity_gate_fails_when_copied_site_lacks_math_fonts(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    copied_site = tmp_path / "copied-site"
    shutil.copytree(site_dir, copied_site)
    (copied_site / "_raya" / "render" / "math" / "fonts" / "fixture.woff2").unlink()

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir), str(copied_site))

    assert result.returncode == 1
    report = json.loads((debug_dir / "report.json").read_text(encoding="utf-8"))
    assert any(
        item["path"].startswith(str(copied_site))
        and "missing local MathJax font asset" in item["message"]
        for item in report["diagnostics"]
    )


def test_render_debug_parity_gate_fails_on_screenshot_outside_debug_dir(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = write_debug_fixture(tmp_path)
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    summary_path = debug_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    for capture in summary["captures"]:
        screenshot = outside_dir / Path(capture["screenshot"]).name
        screenshot.write_bytes(b"stale-png")
        Path(capture["screenshot"]).unlink()
        capture["screenshot"] = str(screenshot)
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    result = run_gate("--inspect-only", str(site_dir), str(debug_dir))

    assert result.returncode == 1
    assert "outside debug directory" in result.stderr


def write_debug_fixture(tmp_path: Path) -> tuple[Path, Path]:
    site_dir = tmp_path / "site"
    debug_dir = tmp_path / "debug"
    (site_dir / "static-path").mkdir(parents=True)
    math_dir = site_dir / "_raya" / "render" / "math"
    (math_dir / "fonts").mkdir(parents=True)
    debug_dir.mkdir()
    (site_dir / "index.html").write_text(
        "<html><body><mjx-container></mjx-container></body></html>",
        encoding="utf-8",
    )
    (site_dir / "static-path" / "index.html").write_text(
        "<html><body>static</body></html>",
        encoding="utf-8",
    )
    (math_dir / "mathjax.css").write_text(
        '@font-face { src: url("fonts/fixture.woff2"); }\n'
        "mjx-container {}",
        encoding="utf-8",
    )
    (math_dir / "fonts" / "fixture.woff2").write_bytes(b"font")

    captures = []
    for page, viewport, screenshot in (
        ("index", "desktop", "desktop-index.png"),
        ("index", "mobile", "mobile-index.png"),
        ("static-path", "desktop", "desktop-static-path.png"),
        ("static-path", "mobile", "mobile-static-path.png"),
    ):
        screenshot_path = debug_dir / screenshot
        screenshot_path.write_bytes(b"png")
        captures.append(
            {
                "page": page,
                "url": f"http://127.0.0.1/{page}/index.html",
                "viewport": {
                    "name": viewport,
                    "width": 1280 if viewport == "desktop" else 390,
                    "height": 900 if viewport == "desktop" else 844,
                },
                "screenshot": str(screenshot_path),
                "mathjax_container_count": 1,
                "raw_tex_visible": False,
                "raw_tex_markers": [],
                "external_requests": [],
                "horizontal_overflow": 0,
            }
        )
    (debug_dir / "summary.json").write_text(
        json.dumps({"captures": captures}),
        encoding="utf-8",
    )
    return site_dir, debug_dir
