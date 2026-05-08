import httpx
from datetime import datetime

from .config import GitHubConfig
from .schemas import (
    Commit,
    Contributor,
    FileContent,
    Issue,
    LanguageBreakdown,
    PullRequest,
    RepoInfo,
    RepoTree,
)


class GitHubClient:
    def __init__(self, config: GitHubConfig):
        self.requests_per_hour = config.requests_per_hour
        self.max_concurrent_requests = config.max_concurrent_requests
        self._client = httpx.AsyncClient(
            base_url=config.api_base_url,
            headers={
                "Authorization": f"Bearer {config.token.get_secret_value()}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
            },
            timeout=10.0,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self._client.aclose()

    async def _get(self, path: str, params: dict | None = None):
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def get_repo(self, repo_owner: str, repo_name: str) -> RepoInfo:
        data = await self._get(f"/repos/{repo_owner}/{repo_name}")
        return RepoInfo.model_validate(data)

    async def list_commits(
        self,
        repo_owner: str,
        repo_name: str,
        since: datetime | None = None,
        max_pages=None,
    ) -> list[Commit]:
        params: dict = {"per_page": 100}
        if since:
            params["since"] = since.isoformat()
        data = await self._get(f"/repos/{repo_owner}/{repo_name}/commits", params)
        return [Commit.model_validate(item) for item in data]

    async def list_contributors(self, repo_owner: str, repo_name: str) -> list[Contributor]:
        data = await self._get(
            f"/repos/{repo_owner}/{repo_name}/contributors", {"per_page": 100}
        )
        return [Contributor.model_validate(item) for item in data]

    async def list_issues(
        self, repo_owner: str, repo_name: str, state: str = "all", max_pages=None
    ) -> list[Issue]:
        data = await self._get(
            f"/repos/{repo_owner}/{repo_name}/issues",
            {"state": state, "per_page": 100},
        )
        return [Issue.model_validate(item) for item in data]

    async def list_pulls(
        self, repo_owner: str, repo_name: str, state: str = "all", max_pages=None
    ) -> list[PullRequest]:
        data = await self._get(
            f"/repos/{repo_owner}/{repo_name}/pulls",
            {"state": state, "per_page": 100},
        )
        return [PullRequest.model_validate(item) for item in data]

    async def get_tree(self, repo_owner: str, repo_name: str, tree_sha: str) -> RepoTree:
        data = await self._get(
            f"/repos/{repo_owner}/{repo_name}/git/trees/{tree_sha}",
            {"recursive": 1},
        )
        return RepoTree.model_validate(data)

    async def get_file_content(
        self, repo_owner: str, repo_name: str, file_path: str, ref: str | None = None
    ) -> FileContent:
        params = {"ref": ref} if ref else None
        data = await self._get(
            f"/repos/{repo_owner}/{repo_name}/contents/{file_path}", params
        )
        return FileContent.model_validate(data)

    async def get_languages(self, repo_owner: str, repo_name: str) -> LanguageBreakdown:
        data = await self._get(f"/repos/{repo_owner}/{repo_name}/languages")
        return LanguageBreakdown.model_validate(data)
