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
        self.api_base_url = config.api_base_url
        self.requests_per_hour = config.requests_per_hour
        self.max_concurrent_requests = config.max_concurrent_requests

        self.headers = {
            "Authorization": f"Bearer {config.token.get_secret_value()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
        }

    async def get_repo(self, repo_owner: str, repo_name: str) -> RepoInfo:
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}"

        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            response = await client.get(url)

        if response.status_code == 200:
            return RepoInfo.model_validate(response.json())
        else:
            raise ValueError("Failed to fetch repository")

    async def list_commits(
        self,
        repo_owner: str,
        repo_name: str,
        since: datetime | None = None,
        max_pages=None,
    ) -> list[Commit]:
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}/commits"
        params: dict = {"per_page": 100}
        if since:
            params["since"] = since.isoformat()

        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            response = await client.get(url, params=params)

        if response.status_code == 200:
            return [Commit.model_validate(item) for item in response.json()]
        else:
            raise ValueError("Failed to fetch repository commits")

    async def list_contributors(self, repo_owner: str, repo_name: str) -> list[Contributor]:
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}/contributors"

        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            response = await client.get(url, params={"per_page": 100})

        if response.status_code == 200:
            return [Contributor.model_validate(item) for item in response.json()]
        else:
            raise ValueError("Failed to fetch repository contributors")

    async def list_issues(
        self, repo_owner: str, repo_name: str, state: str = "all", max_pages=None
    ) -> list[Issue]:
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}/issues"

        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            response = await client.get(url, params={"state": state, "per_page": 100})

        if response.status_code == 200:
            return [Issue.model_validate(item) for item in response.json()]
        else:
            raise ValueError("Failed to fetch repository issues")

    async def list_pulls(
        self, repo_owner: str, repo_name: str, state: str = "all", max_pages=None
    ) -> list[PullRequest]:
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}/pulls"

        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            response = await client.get(url, params={"state": state, "per_page": 100})

        if response.status_code == 200:
            return [PullRequest.model_validate(item) for item in response.json()]
        else:
            raise ValueError("Failed to fetch repository pull requests")

    async def get_tree(self, repo_owner: str, repo_name: str, tree_sha: str) -> RepoTree:
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}/git/trees/{tree_sha}"

        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            response = await client.get(url, params={"recursive": 1})

        if response.status_code == 200:
            return RepoTree.model_validate(response.json())
        else:
            raise ValueError("Failed to fetch repository tree")

    async def get_file_content(
        self, repo_owner: str, repo_name: str, file_path: str, ref: str | None = None
    ) -> FileContent:
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}/contents/{file_path}"
        params = {}
        if ref:
            params["ref"] = ref

        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            response = await client.get(url, params=params)

        if response.status_code == 200:
            return FileContent.model_validate(response.json())
        else:
            raise ValueError("Failed to fetch file content")

    async def get_languages(self, repo_owner: str, repo_name: str) -> LanguageBreakdown:
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}/languages"

        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            response = await client.get(url)

        if response.status_code == 200:
            return LanguageBreakdown.model_validate(response.json())
        else:
            raise ValueError("Failed to fetch repository languages")
