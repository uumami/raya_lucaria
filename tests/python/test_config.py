"""Tests for config loading."""
import sys
sys.path.insert(0, 'src')

import pytest
from pathlib import Path
from preprocessing.config import load_config


def test_load_config(tmp_config):
    config = load_config(tmp_config)
    assert config.site.name == "Test Course"
    assert config.theme.default == "raya-lucaria"
    assert "b_libros" in config.source.exclude


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config(Path("/nonexistent/glintstone.yaml"))


def test_load_config_missing_site_name(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("theme:\n  default: dark\n", encoding='utf-8')
    with pytest.raises(ValueError):
        load_config(bad)


def test_config_defaults(tmp_path):
    minimal = tmp_path / "min.yaml"
    minimal.write_text('site:\n  name: "Minimal"\n', encoding='utf-8')
    config = load_config(minimal)
    assert config.source.content_dir == "clase"
    assert config.features.search is True
    assert config.navigation.show_toc is True
