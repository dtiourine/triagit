import asyncio
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from codescope.github.client import GitHubClient

from .schemas import (
    CommitResponse,
    ContributorResponse,
    FileContentResponse,
    GetRepoResponse,
    HygieneCheck,
    IssueResponse,
    LanguageBreakdownResponse,
    MetricsReport,
    PullRequestResponse,
    TreeEntryResponse,
)


class AnalysisService:
    def __init__(self, github: GitHubClient):
        self.github = github

    def _parse_repo_url(self, url: str) -> tuple[str, str]:
        owner, repo = urlparse(url).path.strip("/").split("/")[:2]
        return owner, repo

    async def get_repo(self, url: str) -> GetRepoResponse:
        owner, repo = self._parse_repo_url(url)
        data = await self.github.get_repo(owner, repo)
        return GetRepoResponse(
            full_name=data.full_name,
            description=data.description,
            default_branch=data.default_branch,
            pushed_at=data.pushed_at,
            size=data.size,
            language=data.language,
            archived=data.archived,
            disabled=data.disabled,
            stars=data.stargazers_count,
            forks=data.forks_count,
        )

    async def list_commits(self, url: str, since: datetime | None = None) -> list[CommitResponse]:
        owner, repo = self._parse_repo_url(url)
        commits = await self.github.list_commits(owner, repo, since=since)
        return [
            CommitResponse(sha=c.sha, author=c.author_identity, authored_at=c.authored_at)
            for c in commits
        ]

    async def list_contributors(self, url: str) -> list[ContributorResponse]:
        owner, repo = self._parse_repo_url(url)
        contributors = await self.github.list_contributors(owner, repo)
        return [ContributorResponse.model_validate(c.model_dump()) for c in contributors]

    async def list_issues(self, url: str, state: str = "all") -> list[IssueResponse]:
        owner, repo = self._parse_repo_url(url)
        issues = await self.github.list_issues(owner, repo, state=state)
        return [
            IssueResponse(
                number=i.number,
                state=i.state,
                created_at=i.created_at,
                closed_at=i.closed_at,
                is_pull_request=i.is_pull_request,
            )
            for i in issues
        ]

    async def list_pulls(self, url: str, state: str = "all") -> list[PullRequestResponse]:
        owner, repo = self._parse_repo_url(url)
        pulls = await self.github.list_pulls(owner, repo, state=state)
        return [
            PullRequestResponse(
                number=p.number,
                state=p.state,
                draft=p.draft,
                created_at=p.created_at,
                merged_at=p.merged_at,
                was_merged=p.was_merged,
            )
            for p in pulls
        ]

    async def get_tree(self, url: str, tree_sha: str) -> list[TreeEntryResponse]:
        owner, repo = self._parse_repo_url(url)
        tree = await self.github.get_tree(owner, repo, tree_sha)
        return [TreeEntryResponse.model_validate(e.model_dump()) for e in tree.tree]

    async def get_file_content(
        self, url: str, file_path: str, ref: str | None = None
    ) -> FileContentResponse:
        owner, repo = self._parse_repo_url(url)
        file = await self.github.get_file_content(owner, repo, file_path, ref=ref)
        return FileContentResponse(
            name=file.name,
            path=file.path,
            sha=file.sha,
            size=file.size,
            content=file.decoded_text(),
        )

    async def get_languages(self, url: str) -> LanguageBreakdownResponse:
        owner, repo = self._parse_repo_url(url)
        breakdown = await self.github.get_languages(owner, repo)
        return LanguageBreakdownResponse.model_validate(breakdown.model_dump())

    async def get_metrics_report(self, url: str) -> MetricsReport:
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=90)

        repo = await self.get_repo(url)
        commits, contributors, issues, pulls, tree, languages = await asyncio.gather(
            self.list_commits(url, since=since),
            self.list_contributors(url),
            self.list_issues(url),
            self.list_pulls(url),
            self.get_tree(url, repo.default_branch),
            self.get_languages(url),
        )

        # Commit activity
        latest = max((c.authored_at for c in commits), default=None)
        if latest and latest.tzinfo is None:
            latest = latest.replace(tzinfo=timezone.utc)
        days_since_last = (now - latest).days if latest else 999
        unique_authors = len({c.author for c in commits})

        buckets = [0] * 13
        for c in commits:
            dt = c.authored_at if c.authored_at.tzinfo else c.authored_at.replace(tzinfo=timezone.utc)
            weeks_ago = (now - dt).days // 7
            if 0 <= weeks_ago < 13:
                buckets[12 - weeks_ago] += 1
        per_week = buckets

        # Contributors (exclude bots)
        non_bot_contributors = [c for c in contributors if c.type != "Bot"]
        top_contributors = sorted(non_bot_contributors, key=lambda c: -c.contributions)[:5]
        total_contrib = sum(c.contributions for c in contributors)
        top3 = sum(c.contributions for c in sorted(contributors, key=lambda c: -c.contributions)[:3])
        bus_factor_pct = round(top3 / total_contrib * 100) if total_contrib else 0

        # Issues / PRs
        real_issues = [i for i in issues if not i.is_pull_request]
        open_issues = sum(1 for i in real_issues if i.state == "open")
        closed_issues = sum(1 for i in real_issues if i.state == "closed")
        open_prs = sum(1 for p in pulls if p.state == "open")
        closed_prs = sum(1 for p in pulls if p.state == "closed")

        # Hygiene
        tree_paths = {e.path for e in tree}
        hygiene = _hygiene(tree_paths)
        hygiene_passed = sum(1 for h in hygiene if h.ok)

        # Languages
        total_bytes = sum(languages.bytes_per_language.values()) or 1
        language_pcts = {
            lang: round(b / total_bytes * 100)
            for lang, b in sorted(languages.bytes_per_language.items(), key=lambda x: -x[1])
        }

        # Scoring
        if days_since_last <= 1:
            activity_score = 100
        elif days_since_last <= 7:
            activity_score = 85
        elif days_since_last <= 30:
            activity_score = 65
        elif days_since_last <= 90:
            activity_score = 35
        else:
            activity_score = 10

        total_i = open_issues + closed_issues
        if not total_i:
            issues_score = 50
        else:
            rate = closed_issues / total_i
            if rate >= 0.9:
                issues_score = 100
            elif rate >= 0.7:
                issues_score = 75
            elif rate >= 0.5:
                issues_score = 55
            else:
                issues_score = 30

        if bus_factor_pct <= 20:
            contrib_score = 100
        elif bus_factor_pct <= 40:
            contrib_score = 75
        elif bus_factor_pct <= 60:
            contrib_score = 50
        else:
            contrib_score = 25

        hygiene_score = round(hygiene_passed / len(hygiene) * 100) if hygiene else 0
        score = round(activity_score * 0.4 + hygiene_score * 0.3 + contrib_score * 0.3)

        if score >= 90:
            score_label = "Excellent"
        elif score >= 75:
            score_label = "Healthy"
        elif score >= 55:
            score_label = "Fair"
        elif score >= 35:
            score_label = "At risk"
        else:
            score_label = "Critical"

        score_summary = _score_summary(score, repo.full_name)

        size_kb = repo.size
        if size_kb < 1024:
            size_fmt = f"{size_kb} KB"
        elif size_kb < 1024 * 1024:
            size_fmt = f"{size_kb / 1024:.1f} MB"
        else:
            size_fmt = f"{size_kb / 1024 / 1024:.2f} GB"

        return MetricsReport(
            slug=repo.full_name,
            repo=repo,
            size_fmt=size_fmt,
            score=score,
            score_label=score_label,
            score_summary=score_summary,
            breakdown={
                "Activity":     activity_score,
                "Issues / PRs": issues_score,
                "Hygiene":      hygiene_score,
                "Contributors": contrib_score,
            },
            commits_90d=len(commits),
            unique_authors=unique_authors,
            days_since_last=days_since_last,
            bus_factor_pct=bus_factor_pct,
            per_week=per_week,
            top_contributors=top_contributors,
            open_issues=open_issues,
            closed_issues=closed_issues,
            open_prs=open_prs,
            closed_prs=closed_prs,
            hygiene=hygiene,
            hygiene_passed=hygiene_passed,
            language_pcts=language_pcts,
        )


# ── Private helpers ───────────────────────────────────────────────────────────

def _hygiene(paths: set[str]) -> list[HygieneCheck]:
    def has(*names: str) -> bool:
        return any(p in paths for p in names)

    def has_prefix(prefix: str) -> bool:
        return any(p.startswith(prefix) for p in paths)

    ci_ok = has_prefix(".github/workflows/")
    return [
        HygieneCheck(ok=has("README.md", "README.rst", "README.txt", "README"),  label="Has README"),
        HygieneCheck(ok=has("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE"),  label="Has LICENSE"),
        HygieneCheck(ok=ci_ok, label="Has CI configuration", note=".github/workflows" if ci_ok else None),
        HygieneCheck(ok=has_prefix("tests/") or has_prefix("test/"),             label="Has tests/ directory"),
        HygieneCheck(ok=has(".gitignore"),                                        label="Has .gitignore"),
    ]


def _score_summary(score: int, name: str) -> str:
    if score >= 90:
        return f"{name} is actively maintained with strong contributor diversity and good hygiene."
    if score >= 75:
        return f"{name} is healthy with regular activity and reasonable project hygiene."
    if score >= 55:
        return f"{name} shows moderate activity. Some hygiene or contributor diversity improvements could help."
    if score >= 35:
        return f"{name} shows signs of reduced activity or hygiene gaps that may need attention."
    return f"{name} appears to have low activity or significant maintenance concerns."
