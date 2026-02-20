"""Shared test fixtures for glintstone preprocessing tests."""
import pytest
from pathlib import Path


@pytest.fixture
def tmp_content(tmp_path):
    """Create a temporary content directory with sample files."""
    content = tmp_path / "clase"
    content.mkdir()

    # Root index
    (content / "00_index.md").write_text(
        "---\ntitle: Test Course\n---\n\n# Test Course\n", encoding='utf-8'
    )

    # Chapter 1
    ch1 = content / "01_intro"
    ch1.mkdir()
    (ch1 / "00_index.md").write_text(
        "---\ntitle: Introduction\n---\n\n# Introduction\n", encoding='utf-8'
    )
    (ch1 / "01_hello.md").write_text(
        "---\ntitle: Hello World\nsummary: First page\n---\n\n# Hello World\n\nSome content.\n",
        encoding='utf-8'
    )
    (ch1 / "02_components.md").write_text(
        '---\ntitle: Components\n---\n\n# Components\n\n'
        ':::homework{id="hw-01" title="First Task" due="2026-03-01" points="10"}\n\n'
        'Do this task.\n\n:::\n\n'
        ':::exercise{title="Practice" difficulty="2"}\n\n'
        'Practice this.\n\n:::\n',
        encoding='utf-8'
    )

    # Chapter 2
    ch2 = content / "02_advanced"
    ch2.mkdir()
    (ch2 / "00_index.md").write_text(
        "---\ntitle: Advanced\n---\n\n# Advanced Topics\n", encoding='utf-8'
    )
    (ch2 / "01_exams.md").write_text(
        '---\ntitle: Exams\n---\n\n'
        ':::exam{id="exam-01" title="Midterm" date="2026-04-01" location="Room 101" duration="2h"}\n\n'
        'Study everything.\n\n:::\n',
        encoding='utf-8'
    )

    # Appendix
    appendix = content / "a_appendix"
    appendix.mkdir()
    (appendix / "00_index.md").write_text(
        "---\ntitle: Appendix\n---\n\n# Appendix\n", encoding='utf-8'
    )
    (appendix / "01_ref.md").write_text(
        "---\ntitle: Reference\n---\n\n# Reference\n\nSee [hello](../01_intro/01_hello.md).\n",
        encoding='utf-8'
    )

    return content


@pytest.fixture
def tmp_config(tmp_path):
    """Create a temporary glintstone.yaml config."""
    config = tmp_path / "glintstone.yaml"
    config.write_text(
        'site:\n'
        '  name: "Test Course"\n'
        '  description: "Test"\n'
        'source:\n'
        '  content_dir: "clase"\n'
        '  exclude:\n'
        '    - "b_libros"\n'
        'theme:\n'
        '  default: "raya-lucaria"\n',
        encoding='utf-8'
    )
    return config
