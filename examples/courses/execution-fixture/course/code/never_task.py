from pathlib import Path


Path("SHOULD_NOT_EXIST_NEVER_SENTINEL").write_text("executed", encoding="utf-8")
print("never policy should refuse before this script runs")
