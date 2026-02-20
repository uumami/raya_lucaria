"""Process calendario_temas.csv into calendar_topics.json for Eleventy.

Usage (called from build scripts):
    PYTHONPATH=/app/glintstone/src python3 -m preprocessing.process_calendar

Reads calendario_temas.csv from CWD, writes calendar_topics.json to _data.
"""
import csv
import json
import sys
from pathlib import Path


def process_calendar(csv_path: Path, output_path: Path) -> list:
    """Read calendar CSV and return list of week records."""
    weeks = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            weeks.append({
                'semana': row.get('semana', '').strip(),
                'fecha': row.get('fecha', '').strip(),
                'tema': row.get('tema', '').strip(),
                'nota': row.get('nota', '').strip(),
            })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(weeks, f, indent=2, ensure_ascii=False)

    return weeks


def main():
    csv_path = Path('calendario_temas.csv')
    if not csv_path.exists():
        print(f"[calendario] No {csv_path} found, skipping.", file=sys.stderr)
        sys.exit(0)

    output_path = Path('glintstone/src/eleventy/_data/calendar_topics.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    weeks = process_calendar(csv_path, output_path)
    print(f"[calendario] {len(weeks)} weeks written to {output_path}")


if __name__ == '__main__':
    main()
