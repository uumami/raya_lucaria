"""Configuration schema for glintstone.yaml."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SiteConfig:
    name: str
    description: str = ""
    language: str = "es"
    author: str = ""


@dataclass
class RepositoryConfig:
    name: str = ""
    org: str = ""
    url: str = ""


@dataclass
class SourceConfig:
    content_dir: str = "clase"
    exclude: List[str] = field(default_factory=lambda: ["b_libros", "README_FLOW.md"])


@dataclass
class ThemeConfig:
    default: str = "raya-lucaria"
    available: List[str] = field(default_factory=lambda: ["raya-lucaria", "leyndell"])


@dataclass
class BuildConfig:
    output_dir: str = "_site"


@dataclass
class NavigationConfig:
    show_breadcrumbs: bool = True
    show_sidebar: bool = True
    show_prev_next: bool = True
    show_toc: bool = True


@dataclass
class FeaturesConfig:
    search: bool = True
    theme_toggle: bool = True
    font_toggle: bool = True
    copy_code_button: bool = True
    math: bool = True
    mermaid: bool = True
    docs: bool = True
    graph: bool = True


@dataclass
class TaskPageConfig:
    type: str
    title: str
    slug: str


@dataclass
class TasksConfig:
    pages: List[TaskPageConfig] = field(default_factory=lambda: [
        TaskPageConfig("homework", "Tareas", "tareas"),
        TaskPageConfig("exam", "Exámenes", "examenes"),
        TaskPageConfig("project", "Proyectos", "proyectos"),
    ])


@dataclass
class GlintstoneConfig:
    site: SiteConfig
    repository: RepositoryConfig = field(default_factory=RepositoryConfig)
    source: SourceConfig = field(default_factory=SourceConfig)
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    build: BuildConfig = field(default_factory=BuildConfig)
    navigation: NavigationConfig = field(default_factory=NavigationConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
    tasks: TasksConfig = field(default_factory=TasksConfig)
