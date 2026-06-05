from pathlib import Path


def build_value() -> str:
    Path("SHOULD_NOT_EXIST_RUNTIME_SENTINEL").write_text("executed", encoding="utf-8")
    return "runtime metadata fixture"
