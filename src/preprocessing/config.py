"""Load and validate glintstone.yaml configuration."""
import re
import subprocess
from pathlib import Path
from typing import Optional

import yaml

from preprocessing.logger import get_logger
from preprocessing.schemas.config import (
    GlintstoneConfig, SiteConfig, RepositoryConfig, SourceConfig,
    ThemeConfig, BuildConfig, NavigationConfig, FeaturesConfig,
    TasksConfig, TaskPageConfig,
)

log = get_logger()


def load_config(config_path: Path) -> GlintstoneConfig:
    """Load and validate glintstone.yaml configuration file."""
    if not config_path.exists():
        raise FileNotFoundError(
            f"The stars cannot align: config file not found at {config_path}"
        )

    with open(config_path, 'r', encoding='utf-8') as f:
        raw = yaml.safe_load(f)

    if not raw or not isinstance(raw, dict):
        raise ValueError(f"The stars cannot align: {config_path} is empty or invalid")

    if 'site' not in raw or 'name' not in raw.get('site', {}):
        raise ValueError(
            f"The stars cannot align: 'site.name' is required in {config_path}"
        )

    # Build config dataclass from raw YAML
    site_raw = raw.get('site', {})
    site = SiteConfig(
        name=site_raw['name'],
        description=site_raw.get('description', ''),
        language=site_raw.get('language', 'es'),
        author=site_raw.get('author', ''),
    )

    repo_raw = raw.get('repository', {})
    repository = RepositoryConfig(
        name=repo_raw.get('name', ''),
        org=repo_raw.get('org', ''),
        url=repo_raw.get('url', ''),
    )

    source_raw = raw.get('source', {})
    source = SourceConfig(
        content_dir=source_raw.get('content_dir', 'clase'),
        exclude=source_raw.get('exclude', ['b_libros', 'README_FLOW.md']),
    )

    theme_raw = raw.get('theme', {})
    theme = ThemeConfig(
        default=theme_raw.get('default', 'raya-lucaria'),
        available=theme_raw.get('available', ['raya-lucaria', 'leyndell']),
    )

    build_raw = raw.get('build', {})
    build = BuildConfig(output_dir=build_raw.get('output_dir', '_site'))

    nav_raw = raw.get('navigation', {})
    navigation = NavigationConfig(
        show_breadcrumbs=nav_raw.get('show_breadcrumbs', True),
        show_sidebar=nav_raw.get('show_sidebar', True),
        show_prev_next=nav_raw.get('show_prev_next', True),
        show_toc=nav_raw.get('show_toc', True),
    )

    feat_raw = raw.get('features', {})
    features = FeaturesConfig(
        search=feat_raw.get('search', True),
        theme_toggle=feat_raw.get('theme_toggle', True),
        font_toggle=feat_raw.get('font_toggle', True),
        copy_code_button=feat_raw.get('copy_code_button', True),
        math=feat_raw.get('math', True),
        mermaid=feat_raw.get('mermaid', True),
        docs=feat_raw.get('docs', True),
        graph=feat_raw.get('graph', True),
    )

    tasks_raw = raw.get('tasks', {})
    task_pages = []
    for p in tasks_raw.get('pages', []):
        task_pages.append(TaskPageConfig(
            type=p['type'], title=p['title'], slug=p['slug']
        ))
    tasks = TasksConfig(pages=task_pages) if task_pages else TasksConfig()

    return GlintstoneConfig(
        site=site,
        repository=repository,
        source=source,
        theme=theme,
        build=build,
        navigation=navigation,
        features=features,
        tasks=tasks,
    )


def detect_git_info(verbose: bool = False) -> dict:
    """Auto-detect repository information from git remote."""
    try:
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            capture_output=True, text=True, check=True
        )
        remote_url = result.stdout.strip()

        if verbose:
            log.debug(f"Detected git remote: {remote_url}")

        # Parse SSH: git@github.com:org/repo.git
        match = re.match(r'git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$', remote_url)
        if not match:
            # Parse HTTPS: https://github.com/org/repo.git
            match = re.match(r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$', remote_url)

        if match:
            org = match.group(1)
            repo_name = match.group(2)
            if verbose:
                log.debug(f"Auto-detected: org={org}, repo={repo_name}")
            return {
                'repo_name': repo_name,
                'org': org,
                'upstream_url': f"git@github.com:{org}/{repo_name}.git",
            }
    except Exception as e:
        if verbose:
            log.debug(f"Could not auto-detect git info: {e}")

    return {'repo_name': '', 'org': '', 'upstream_url': ''}


def resolve_repo_info(config: GlintstoneConfig, verbose: bool = False) -> dict:
    """Resolve repository info from config + git auto-detection."""
    git_info = detect_git_info(verbose)

    repo_name = config.repository.name or git_info.get('repo_name', '')
    org = config.repository.org or git_info.get('org', '')
    upstream_url = config.repository.url or git_info.get('upstream_url', '')

    if not repo_name:
        raise ValueError(
            "The stars cannot align: cannot determine repository name. "
            "Either add a git remote or set repository.name in glintstone.yaml"
        )

    base_url = f"/{repo_name}"
    pr_compare_url = f"https://github.com/{org}/{repo_name}/compare" if org else ""

    return {
        'repo_name': repo_name,
        'org': org,
        'base_url': base_url,
        'upstream_url': upstream_url,
        'pr_compare_url': pr_compare_url,
    }
