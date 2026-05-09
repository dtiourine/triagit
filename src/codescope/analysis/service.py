from datetime import datetime
from urllib.parse import urlparse

from codescope.github.client import GitHubClient

from .schemas import (
    CommitResponse,
    ContributorResponse,
    FileContentResponse,
    GetRepoResponse,
    IssueResponse,
    LanguageBreakdownResponse,
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
        return GetRepoResponse.model_validate(data.model_dump())

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
