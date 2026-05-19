import asyncio
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from triagit.domains.triage.schemas import RepoStatistics
from triagit.infrastructure.github.client import GitHubClient
from triagit.infrastructure.llm.base import LLMClient


class TriageService:
    def __init__(self, github: GitHubClient, llm: LLMClient):
        self._github = github
        self._llm = llm

    async def get_triage_report(self, repo_url: str):
        repo_owner, repo_name = urlparse(repo_url).path.strip("/").split("/")[:2]
        statistics = await self._get_repo_statistics(repo_owner, repo_name)
        pass 

    async def _get_repo_statistics(self, repo_owner: str, repo_name: str):
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)

        basic_repo_info, last_30_days_commits, pull_requests = await asyncio.gather(
            self._github.get_repo(repo_owner=repo_owner, repo_name=repo_name),
            self._github.list_commits(repo_owner=repo_owner, repo_name=repo_name, since=cutoff),
            self._github.list_pulls(repo_owner=repo_owner, repo_name=repo_name, state="open"),
        )

        last_30_days_pull_requests = [
            pr for pr in pull_requests if pr.updated_at >= cutoff
        ]

        contributor_counts = Counter(c.author_identity for c in last_30_days_commits)
        top_5_recent_contributors = [name for name, _ in contributor_counts.most_common(5)]

        return RepoStatistics(
            owner=repo_owner,
            name=repo_name,
            stars_count=basic_repo_info.stargazers_count,
            forks_count=basic_repo_info.forks_count,
            last_30_days_commits=last_30_days_commits,
            last_30_days_pull_requests=last_30_days_pull_requests,
            top_5_recent_contributors=top_5_recent_contributors,
            last_commit_date=basic_repo_info.pushed_at,
        )
