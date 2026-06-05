"""Reference fixture script.

The static builder may preview this source, but it must not execute it.
"""


def clean_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{key: value.strip() for key, value in row.items()} for row in rows]
