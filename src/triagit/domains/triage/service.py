import asyncio
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from triagit.domains.triage.schemas import RecentActivity
from triagit.infrastructure.github.client import GitHubClient
from triagit.infrastructure.llm.base import LLMClient


class TriageService:
    def __init__(self, github: GitHubClient, llm: LLMClient):
        self._github = github
        self._llm = llm

    async def get_triage_report(self, repo_url: str):
        repo_owner, repo_name = urlparse(repo_url).path.strip("/").split("/")[:2]
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)

        repo_info, commits, pull_requests = await asyncio.gather(
            self._github.get_repo(repo_owner=repo_owner, repo_name=repo_name),
            self._github.list_commits(
                repo_owner=repo_owner, repo_name=repo_name, since=cutoff
            ),
            self._github.list_pulls(
                repo_owner=repo_owner, repo_name=repo_name, state="open"
            ),
        )

        recent_activity = self._check_recent_activity(
            repo_info, commits, pull_requests, cutoff
        )

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
