from pathlib import Path


counter = Path("execution-side-effect.txt")
count = int(counter.read_text(encoding="utf-8")) + 1 if counter.exists() else 1
counter.write_text(str(count), encoding="utf-8")
print(f"cache execution count: {count}")
