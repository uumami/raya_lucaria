#!/usr/bin/env python3
"""Generate examples/courses/rail-density-fixture.

A 41-page, 3-level tree used to measure course-map density. The 6-page
render-fixture is too small: its map never reaches the rail's max-height
clamp, so the flex leftover distribution the density tests assert is never
exercised.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "courses" / "rail-density-fixture"
COURSE = FIXTURE / "course"

RAYA_YAML = """course_id: rail-density-fixture
title: Rail Density Fixture
description: Wide, deep tree for measuring course-map density.
language: en
source: course
artifact: artifact
hierarchy:
  levels:
    - key: unit
      label: Unit
    - key: section
      label: Section
    - key: topic
      label: Topic
"""

SECTIONS = [
    ("1_foundations", "Foundations"),
    ("2_representation", "Representation"),
    ("3_verification", "Verification"),
]
TOPICS = [
    ("1_orientation", "Orientation"),
    ("2_structure", "Structure And Ordering Rules"),
    ("3_review", "Review"),
]
# Deliberately long titles: the density tests need labels that exceed two
# clamped lines at 0.8125rem in a ~150px column.
LEAVES = [
    ("1_overview", "Overview Of Long Structural Titles"),
    ("2_details", "Detailed Requirements And Registration Constraints"),
    ("3_summary", "Summary"),
]


def write(path: Path, page_id: str, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nid: {page_id}\ntitle: {title}\nstatus: ready\n---\n\n"
        f"# {title}\n\n{body}\n",
        encoding="utf-8",
    )


def _slug(dir_name: str) -> str:
    # Strip the ordering prefix ("1_foundations" -> "foundations") so
    # stable ids do not depend on order prefixes, per the course contract.
    return dir_name.split("_", 1)[1].replace("_", "-")


def main() -> None:
    write(
        COURSE / "0_index.md",
        "rail-density-root",
        "Rail Density Fixture",
        "Root page for the rail density fixture.",
    )
    for s_dir, s_title in SECTIONS:
        s_slug = _slug(s_dir)
        write(
            COURSE / s_dir / "0_index.md",
            f"rail-density-{s_slug}",
            s_title,
            f"Section landing page for {s_title}.",
        )
        for t_dir, t_title in TOPICS:
            t_slug = _slug(t_dir)
            write(
                COURSE / s_dir / t_dir / "0_index.md",
                f"rail-density-{s_slug}-{t_slug}",
                t_title,
                f"Topic landing page for {t_title}.",
            )
            for l_name, l_title in LEAVES:
                l_slug = _slug(l_name)
                write(
                    COURSE / s_dir / t_dir / f"{l_name}.md",
                    f"rail-density-{s_slug}-{t_slug}-{l_slug}",
                    l_title,
                    "Leaf page body.",
                )
    # One page whose title is a single unbroken 55-character identifier, so
    # the emergency overflow-wrap:break-word path stays covered.
    write(
        COURSE / "4_identifier.md",
        "rail-density-identifier",
        "ProjectionResidualsWithAnUnbrokenAuthorIdentifierXYZ007",
        "Covers the unbreakable-token path.",
    )
    (FIXTURE / "raya.yaml").write_text(RAYA_YAML, encoding="utf-8")
    pages = sorted(COURSE.rglob("*.md"))
    print(f"wrote {len(pages)} pages under {COURSE}")


if __name__ == "__main__":
    main()
