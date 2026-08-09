from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "reusable-course-pages.yml"


def test_reusable_course_pages_workflow_is_hardened() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_call:" in workflow
    assert "course_path:" in workflow
    assert "permissions:\n      contents: read" in workflow
    assert "repository: ${{ job.workflow_repository }}" in workflow
    assert "ref: ${{ job.workflow_sha }}" in workflow
    assert "uv sync --directory .raya-framework --locked --python 3.10 --all-packages --dev" in workflow
    assert 'raya validate "$course_root"' in workflow
    assert 'raya build "$course_root"' in workflow
    assert 'raya artifacts inspect "$course_root/artifact"' in workflow
    assert "actions/upload-pages-artifact@7b1f4a764d45c48632c6b24a0339c27f5614fb0b" in workflow
    assert "path: ${{ github.workspace }}/${{ inputs.course_path }}/artifact/site" in workflow
    assert "needs: verify" in workflow
    assert "name: github-pages" in workflow
    assert "actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e" in workflow
    assert "github.ref == format('refs/heads/{0}', github.event.repository.default_branch)" in workflow
