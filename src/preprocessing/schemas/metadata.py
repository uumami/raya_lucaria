"""Dataclass schemas for all preprocessing JSON output."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ComponentData:
    """A single component (homework, exercise, etc.) found in a file."""
    type: str
    attrs: Dict[str, str] = field(default_factory=dict)
    content_preview: str = ""
    line_number: int = 0


@dataclass
class FileMetadata:
    """Metadata extracted from a single markdown file."""
    path: str
    title: str
    type: str = "lesson"
    order: int = 999
    summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    components: List[ComponentData] = field(default_factory=list)
    has_frontmatter: bool = False


@dataclass
class HierarchyNode:
    """A node in the navigation hierarchy tree."""
    name: str
    path: str
    type: str  # "root", "directory", "file"
    title: str
    has_index: bool = False
    children: List['HierarchyNode'] = field(default_factory=list)
    summary: Optional[str] = None
    no_number: bool = False


@dataclass
class TaskItem:
    """A single aggregated task (homework, exam, or project)."""
    id: str
    title: str
    type: str
    chapter: str
    file: str
    url: str
    due: Optional[str] = None
    date: Optional[str] = None
    points: Optional[str] = None
    location: Optional[str] = None
    duration: Optional[str] = None
    team_size: Optional[str] = None
    summary: str = ""
    overdue: bool = False


@dataclass
class RepoInfo:
    """Repository configuration for path prefix and URLs."""
    repo_name: str
    org: str
    base_url: str
    upstream_url: str = ""
    pr_compare_url: str = ""
