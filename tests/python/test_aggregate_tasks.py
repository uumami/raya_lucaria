"""Tests for task aggregation."""
import sys
sys.path.insert(0, 'src')

from preprocessing.extract_metadata import extract_all_metadata
from preprocessing.aggregate_tasks import aggregate_all_tasks, is_overdue


def test_aggregate_tasks(tmp_content):
    metadata = extract_all_metadata(tmp_content, exclude=[])
    tasks = aggregate_all_tasks(tmp_content, metadata)

    assert len(tasks["homework"]) == 1
    assert tasks["homework"][0]["id"] == "hw-01"
    assert tasks["homework"][0]["title"] == "First Task"

    assert len(tasks["exams"]) == 1
    assert tasks["exams"][0]["id"] == "exam-01"


def test_is_overdue():
    assert is_overdue("2020-01-01") is True
    assert is_overdue("2099-12-31") is False
    assert is_overdue("") is False
    assert is_overdue(None) is False


def test_task_urls(tmp_content):
    metadata = extract_all_metadata(tmp_content, exclude=[])
    tasks = aggregate_all_tasks(tmp_content, metadata)

    hw = tasks["homework"][0]
    assert hw["url"].endswith("/")
    assert ".md" not in hw["url"]
