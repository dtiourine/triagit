import asyncio
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from triagit.domains.sampling.sampler import SampledSource, sample_repo
from triagit.domains.triage.prompts import ANALYSIS_INSTRUCTIONS
from triagit.domains.triage.schemas import (
    CodeRefresher,
    CompletionRoadmap,
    HygieneChecklist,
    RecentActivity,
    _LLMAnalysisOutput,
)
from triagit.infrastructure.github.client import GitHubClient
from triagit.infrastructure.github.exceptions import GitHubNotFoundError
from triagit.infrastructure.github.schemas import ContentEntry, LanguageBreakdown, RepoInfo
from triagit.infrastructure.llm.base import LLMClient


class TriageService:
    def __init__(self, github: GitHubClient, llm: LLMClient):
        self._github = github
        self._llm = llm

    async def get_triage_report(self, repo_url: str):
        repo_owner, repo_name = urlparse(repo_url).path.strip("/").split("/")[:2]
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)

        repo_info, commits, pull_requests, root_entries, workflows_entries = (
            await asyncio.gather(
                self._github.get_repo(repo_owner=repo_owner, repo_name=repo_name),
                self._github.list_commits(
                    repo_owner=repo_owner, repo_name=repo_name, since=cutoff
                ),
                self._github.list_pulls(
                    repo_owner=repo_owner, repo_name=repo_name, state="open"
                ),
                self._github.list_contents(repo_owner, repo_name, ""),
                self._fetch_workflows(repo_owner, repo_name),
            )
        )

        recent_activity = self._check_recent_activity(
            repo_info, commits, pull_requests, cutoff
        )
        hygiene_checklist = self._check_hygiene(root_entries, workflows_entries)

        return recent_activity, hygiene_checklist

    def _check_recent_activity(self, repo_info, commits, pull_requests, cutoff):
        last_30_days_pull_requests = [
            pr for pr in pull_requests if pr.updated_at >= cutoff
        ]

        contributor_counts = Counter(c.author_identity for c in commits)
        top_5_recent_contributors = [
            name for name, _ in contributor_counts.most_common(5)
        ]

        return RecentActivity(
            stars_count=repo_info.stargazers_count,
            forks_count=repo_info.forks_count,
            last_30_days_commits=commits,
            last_30_days_pull_requests=last_30_days_pull_requests,
            top_5_recent_contributors=top_5_recent_contributors,
            last_commit_date=repo_info.pushed_at,
        )

    async def _fetch_workflows(
        self, repo_owner: str, repo_name: str
    ) -> list[ContentEntry]:
        try:
            return await self._github.list_contents(
                repo_owner, repo_name, ".github/workflows"
            )
        except GitHubNotFoundError:
            return []

    def _check_hygiene(
        self, root_entries: list[ContentEntry], workflows_entries: list[ContentEntry]
    ) -> HygieneChecklist:
        names = {e.path for e in root_entries}

        def has(*targets: str) -> bool:
            return any(t in names for t in targets)

        return HygieneChecklist(
            has_readme=has("README.md", "README.rst", "README.txt", "README"),
            has_license=has("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE"),
            has_ci=len(workflows_entries) > 0,
            has_tests=has("tests", "test"),
            has_gitignore=has(".gitignore"),
        )
