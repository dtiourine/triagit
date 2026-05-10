import pytest
from unittest.mock import AsyncMock
from codescope.analysis.schemas import GetRepoResponse
from codescope.analysis.service import AnalysisService
from codescope.github.schemas import RepoInfo
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


async def test_get_repo_maps_stars_and_forks():
    now = datetime.now(timezone.utc)
    mock_repo_info = RepoInfo(
        full_name="owner/repo",
        description="Test repo",
        default_branch="main",
        pushed_at=now,
        size=1000,
        language="Python",
        archived=False,
        disabled=False,
        license=None,
        stargazers_count=500,
        forks_count=42,
    )
    mock_github = AsyncMock()
    mock_github.get_repo.return_value = mock_repo_info

    service = AnalysisService(mock_github)
    result = await service.get_repo("https://github.com/owner/repo")

    assert result.stars == 500
    assert result.forks == 42


from codescope.analysis.schemas import MetricsReport


def _make_service(raw_analysis) -> AnalysisService:
    mock_github = AsyncMock()
    service = AnalysisService(mock_github)
    service.get_repo = AsyncMock(return_value=raw_analysis.repo)
    service.list_commits = AsyncMock(return_value=raw_analysis.commits)
    service.list_contributors = AsyncMock(return_value=raw_analysis.contributors)
    service.list_issues = AsyncMock(return_value=raw_analysis.issues)
    service.list_pulls = AsyncMock(return_value=raw_analysis.pulls)
    service.get_tree = AsyncMock(return_value=raw_analysis.tree)
    service.get_languages = AsyncMock(return_value=raw_analysis.languages)
    return service


async def test_get_metrics_report_returns_metrics_report(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert isinstance(result, MetricsReport)


async def test_commits_90d(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert result.commits_90d == 4


async def test_unique_authors(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert result.unique_authors == 3


async def test_days_since_last_commit(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert result.days_since_last == 1


async def test_bus_factor_pct(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    # alice(70) + bob(20) + carol(10) = 100 / 100 total = 100%
    assert result.bus_factor_pct == 100


async def test_per_week_has_13_buckets(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert len(result.per_week) == 13
    assert all(v >= 0 for v in result.per_week)


async def test_hygiene_readme_found(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    readme = next(h for h in result.hygiene if h.label == "Has README")
    assert readme.ok is True


async def test_hygiene_ci_found(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    ci = next(h for h in result.hygiene if h.label == "Has CI configuration")
    assert ci.ok is True


async def test_hygiene_missing(raw_analysis):
    raw_analysis.tree = [e for e in raw_analysis.tree if not e.path.startswith(".github")]
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    ci = next(h for h in result.hygiene if h.label == "Has CI configuration")
    assert ci.ok is False


async def test_health_score_bounded(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert 0 <= result.score <= 100


async def test_score_label_valid(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert result.score_label in {"Excellent", "Healthy", "Fair", "At risk", "Critical"}


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


async def test_language_pcts_sum_to_100(raw_analysis):
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert sum(result.language_pcts.values()) == 100


async def test_size_fmt_mb(raw_analysis):
    raw_analysis.repo = raw_analysis.repo.model_copy(update={"size": 1025})
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert "MB" in result.size_fmt


async def test_top_contributors_excludes_bots(raw_analysis):
    from codescope.analysis.schemas import ContributorResponse
    raw_analysis.contributors.append(
        ContributorResponse(login="dependabot[bot]", contributions=999, type="Bot")
    )
    service = _make_service(raw_analysis)
    result = await service.get_metrics_report("https://github.com/owner/repo")
    assert all(c.login != "dependabot[bot]" for c in result.top_contributors)
