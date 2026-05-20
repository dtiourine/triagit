import asyncio
import time
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
        self._config = config
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
        max_attempts = self._config.retry_max_attempts
        threshold = self._config.retry_rate_limit_threshold_seconds
        backoff_base = self._config.retry_backoff_base_seconds

        for attempt in range(max_attempts):
            try:
                response = await self._client.get(path, params=params)
            except httpx.RequestError as e:
                if attempt < max_attempts - 1:
                    await asyncio.sleep(backoff_base * (2 ** attempt))
                    continue
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
                    reset_at_header = response.headers.get("X-RateLimit-Reset")
                    exc = GitHubRateLimitError(message, status, body, reset_at=reset_at_header)
                    if attempt < max_attempts - 1 and reset_at_header:
                        try:
                            wait = int(reset_at_header) - time.time()
                            if 0 < wait <= threshold:
                                await asyncio.sleep(wait + 1)
                                continue
                        except (ValueError, TypeError):
                            pass
                    raise exc
                case 429:
                    retry_after_raw = response.headers.get("Retry-After")
                    exc = GitHubRateLimitError(message, status, body, reset_at=None)
                    if attempt < max_attempts - 1 and retry_after_raw is not None:
                        try:
                            retry_after = int(retry_after_raw)
                            if retry_after <= threshold:
                                await asyncio.sleep(retry_after)
                                continue
                        except (ValueError, TypeError):
                            pass
                    raise exc
                # plain 403 — keep after all guarded 403 cases
                case 403:
                    raise GitHubForbiddenError(message, status, body)
                case 404:
                    raise GitHubNotFoundError(message, status, body)
                case 422:
                    raise GitHubValidationError(message, status, body)
                case _ if status >= 500:
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(backoff_base * (2 ** attempt))
                        continue
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
