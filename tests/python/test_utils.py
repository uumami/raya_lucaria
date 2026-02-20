"""Tests for preprocessing utilities."""
import sys
sys.path.insert(0, 'src')

from preprocessing.utils import (
    title_from_name, get_sort_key, get_nav_number,
    parse_attributes, get_chapter_name, is_wip, is_index,
)


def test_title_from_name_numeric():
    assert title_from_name("01_hello_world.md") == "Hello World"


def test_title_from_name_index():
    assert title_from_name("00_index.md") == "Index"


def test_title_from_name_letter_prefix():
    assert title_from_name("a_appendix") == "Appendix"


def test_title_from_name_no_prefix():
    assert title_from_name("readme.md") == "Readme"


def test_sort_key_numbered():
    assert get_sort_key("01_intro") < get_sort_key("02_chapter")


def test_sort_key_appendix_after_numbered():
    assert get_sort_key("02_chapter") < get_sort_key("a_appendix")


def test_sort_key_z_last():
    assert get_sort_key("a_appendix") < get_sort_key("z_docs")


def test_nav_number_numeric():
    assert get_nav_number("01_intro") == "1"
    assert get_nav_number("02_chapter") == "2"


def test_nav_number_letter():
    assert get_nav_number("a_appendix") == "A"
    assert get_nav_number("b_extra") == "B"


def test_nav_number_z():
    assert get_nav_number("z_docs") == "Z"


def test_parse_attributes():
    result = parse_attributes('id="hw-01" title="Task" points="10"')
    assert result == {"id": "hw-01", "title": "Task", "points": "10"}


def test_parse_attributes_single_quotes():
    result = parse_attributes("id='hw-01' title='Task'")
    assert result == {"id": "hw-01", "title": "Task"}


def test_parse_attributes_empty():
    assert parse_attributes("") == {}
    assert parse_attributes(None) == {}


def test_get_chapter_name():
    assert get_chapter_name("01_intro/01_hello.md") == "Intro"
    assert get_chapter_name("a_appendix/01_ref.md") == "Appendix"
    assert get_chapter_name("standalone.md") == "General"


def test_is_wip():
    assert is_wip("??_draft") is True
    assert is_wip("01_intro") is False


def test_is_index():
    assert is_index("00_index.md") is True
    assert is_index("01_intro.md") is False
