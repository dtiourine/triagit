import httpx
from datetime import datetime

from codescope.github.schemas import RepoInfo
from .config import GitHubConfig
from .schemas import Commit


class GitHubClient:
    def __init__(self, config: GitHubConfig):
        self.token = config.token
        self.api_base_url = config.api_base_url
        self.requests_per_hour = config.requests_per_hour
        self.max_concurrent_requests = config.max_concurrent_requests

        self.headers = {
            "Authorization": f"Bearer {self.token.get_secret_value()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
        }

    async def get_repo(self, repo_owner: str, repo_name: str):
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}"

        async with httpx.AsyncClient(
            base_url=self.api_base_url, headers=self.headers, timeout=10.0
        ) as client:
            raw = await client.get(url, headers=self.headers, timeout=10.0)

        if raw.status_code == 200:
            return RepoInfo.model_validate(raw.json())

        else:
            raise ValueError("Failed to fetch repository")

    async def list_commits(
        self,
        repo_owner: str,
        repo_name: str,
        since: datetime | None = None,
        max_pages=None,
    ):
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}/commits?per_page=100"
        if since:
            url += f"&since={since}"

        async with httpx.AsyncClient(
            base_url=self.api_base_url, headers=self.headers, timeout=10.0
        ) as client:
            raws = await client.get(url, headers=self.headers, timeout=10.0)

        if raws.status_code == 200:
            return [Commit.model_validate(r) for r in raws.json()]  # correct

        else:
            raise ValueError("Failed to fetch repository commits")

    async def list_contributors(self, repo_owner: str, repo_name: str):
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}/contributors?per_page=100"

        async with httpx.AsyncClient(
            base_url=self.api_base_url, headers=self.headers, timeout=10.0
        ) as client:
            response = await client.get(url, headers=self.headers, timeout=10.0)

        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError("Failed to fetch repository contributors")

    async def list_issues(
        self, repo_owner: str, repo_name: str, state: str = "all", max_pages=None
    ):
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}/issues?state={state}&per_page=100"

        async with httpx.AsyncClient(
            base_url=self.api_base_url, headers=self.headers, timeout=10.0
        ) as client:
            response = await client.get(url, headers=self.headers, timeout=10.0)

        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError("Failed to fetch repository issues")

    async def list_pulls(
        self, repo_owner: str, repo_name: str, state: str = "all", max_pages=None
    ):
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}/pulls?state={state}&per_page=100"

        async with httpx.AsyncClient(
            base_url=self.api_base_url, headers=self.headers, timeout=10.0
        ) as client:
            response = await client.get(url, headers=self.headers, timeout=10.0)

        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError("Failed to fetch repository pull requests")

    async def get_tree(self, repo_owner: str, repo_name: str, tree_sha: str):
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}/git/trees/{tree_sha}?recursive=1"

        async with httpx.AsyncClient(
            base_url=self.api_base_url, headers=self.headers, timeout=10.0
        ) as client:
            response = await client.get(url, headers=self.headers, timeout=10.0)

        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError("Failed to fetch repository tree")

    async def get_file_content(
        self, repo_owner: str, repo_name: str, file_path: str, ref: str
    ):
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}/contents/{file_path}?ref={ref}"

        async with httpx.AsyncClient(
            base_url=self.api_base_url, headers=self.headers, timeout=10.0
        ) as client:
            response = await client.get(url, headers=self.headers, timeout=10.0)

        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError("Failed to fetch file content")

    async def get_languages(self, repo_owner: str, repo_name: str):
        url = f"{self.api_base_url}/repos/{repo_owner}/{repo_name}/languages"

        async with httpx.AsyncClient(
            base_url=self.api_base_url, headers=self.headers, timeout=10.0
        ) as client:
            response = await client.get(url, headers=self.headers, timeout=10.0)

        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError("Failed to fetch repository languages")
