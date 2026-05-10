import pytest
from unittest.mock import AsyncMock

from codescope.domains.metrics.schemas import GetRepoResponse, MetricsReport
from codescope.domains.metrics.service import AnalysisService
from datetime import datetime, timezone


def test_get_repo_response_has_stars_and_forks():
    r = GetRepoResponse(
        full_name="owner/repo",
        description="A repo",
        default_branch="main",
        pushed_at=datetime.now(timezone.utc),
        size=1000,
        language="Python",
        archived=False,
        disabled=False,
        stars=42,
        forks=7,
    )
    assert r.stars == 42
    assert r.forks == 7


def _make_service(raw_analysis) -> AnalysisService:
    mock_github = AsyncMock()
    mock_github.get_repo.return_value = raw_analysis.repo
    mock_github.list_commits.return_value = raw_analysis.commits
    mock_github.list_contributors.return_value = raw_analysis.contributors
    mock_github.get_tree.return_value = raw_analysis.tree
    mock_github.get_languages.return_value = raw_analysis.languages
    mock_github.count_issues.side_effect = raw_analysis.count_issues
    return AnalysisService(mock_github)


async def test_get_metrics_report_returns_metrics_report(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert isinstance(result, MetricsReport)


async def test_score_is_int(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert isinstance(result.score, int)


async def test_score_in_range(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert 0 <= result.score <= 100


async def test_score_label_is_string(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert isinstance(result.score_label, str)


async def test_breakdown_keys(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert set(result.breakdown.keys()) == {"Activity", "Issues / PRs", "Hygiene", "Contributors"}


async def test_commits_90d(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert result.commits_90d == len(raw_analysis.commits)


async def test_per_week_length(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert len(result.per_week) == 13


async def test_hygiene_all_passed(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert result.hygiene_passed == len(result.hygiene)


async def test_language_pcts_sum_to_100(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert sum(result.language_pcts.values()) == 100


async def test_issue_counts(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert result.open_issues == 1
    assert result.closed_issues == 2


async def test_pr_counts(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert result.open_prs == 1
    assert result.closed_prs == 1


async def test_size_fmt_mb(raw_analysis):
    from codescope.infrastructure.github.schemas import RepoInfo
    raw_analysis.repo = raw_analysis.repo.model_copy(update={"size": 1025})
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert "MB" in result.size_fmt


async def test_top_contributors_excludes_bots(raw_analysis):
    from codescope.infrastructure.github.schemas import Contributor
    raw_analysis.contributors.append(
        Contributor(login="dependabot[bot]", contributions=999, type="Bot")
    )
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert all(c.login != "dependabot[bot]" for c in result.top_contributors)


async def test_repo_stars_and_forks_in_report(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert result.repo.stars == 150
    assert result.repo.forks == 12
