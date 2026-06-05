from pathlib import Path


Path("SHOULD_NOT_EXIST_FROZEN_SENTINEL").write_text("executed", encoding="utf-8")
print("frozen policy should refuse before this script runs")
