from datetime import datetime
from typing import Literal

import httpx

from .config import GitHubConfig
from .exceptions import (
    GitHubAPIError,
    GitHubForbiddenError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubServerError,
    GitHubTransportError,
    GitHubUnauthorizedError,
    GitHubValidationError,
)
from .schemas import (
    Commit,
    ContentEntry,
    Contributor,
    FileContent,
    Issue,
    IssueSearchResult,
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
        try:
            response = await self._client.get(path, params=params)
        except httpx.RequestError as e:
            raise GitHubTransportError(str(e)) from e

        if response.is_success:
            return response.json()

        try:
            body = response.json()
        except Exception:
            body = {}

        message = body.get("message", response.reason_phrase)
        status = response.status_code

        match status:
            case 401:
                raise GitHubUnauthorizedError(message, status, body)
            case 403 if response.headers.get("X-RateLimit-Remaining") == "0":
                raise GitHubRateLimitError(
                    message,
                    status,
                    body,
                    reset_at=response.headers.get("X-RateLimit-Reset"),
                )
            case 403:
                raise GitHubForbiddenError(message, status, body)
            case 404:
                raise GitHubNotFoundError(message, status, body)
            case 422:
                raise GitHubValidationError(message, status, body)
            case _ if status >= 500:
                raise GitHubServerError(message, status, body)
            case _:
                raise GitHubAPIError(message, status, body)

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

    async def list_contributors(
        self, repo_owner: str, repo_name: str
    ) -> list[Contributor]:
        data = await self._get(
            f"/repos/{repo_owner}/{repo_name}/contributors", {"per_page": 100}
        )
        return [Contributor.model_validate(item) for item in data]

    async def list_issues(
        self, repo_owner: str, repo_name: str, state: Literal["open", "closed", "all"] = "all", max_pages=None
    ) -> list[Issue]:
        data = await self._get(
            f"/repos/{repo_owner}/{repo_name}/issues",
            {"state": state, "per_page": 100},
        )
        return [Issue.model_validate(item) for item in data]

    async def list_pulls(
        self, repo_owner: str, repo_name: str, state: Literal["open", "closed", "all"] = "all", max_pages=None
    ) -> list[PullRequest]:
        data = await self._get(
            f"/repos/{repo_owner}/{repo_name}/pulls",
            {"state": state, "per_page": 100},
        )
        return [PullRequest.model_validate(item) for item in data]

    async def count_issues(
        self, repo_owner: str, repo_name: str, is_pr: bool, state: Literal["open", "closed"]
    ) -> int:
        kind = "pr" if is_pr else "issue"
        data = await self._get(
            "/search/issues",
            {"q": f"repo:{repo_owner}/{repo_name} is:{kind} is:{state}", "per_page": 1},
        )
        return IssueSearchResult.model_validate(data).total_count

    async def get_tree(
        self, repo_owner: str, repo_name: str, tree_sha: str
    ) -> RepoTree:
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

    async def list_contents(
        self, repo_owner: str, repo_name: str, path: str = ""
    ) -> list[ContentEntry]:
        data = await self._get(f"/repos/{repo_owner}/{repo_name}/contents/{path}")
        if not isinstance(data, list):
            return [ContentEntry.model_validate(data)]
        return [ContentEntry.model_validate(item) for item in data]
