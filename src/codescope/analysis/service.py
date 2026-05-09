from urllib.parse import urlparse

from codescope.github.client import GitHubClient

from .schemas import GetRepoResponse


class AnalysisService:
    def __init__(self, github: GitHubClient):
        self.github = github

    def _parse_repo_url(self, url: str) -> tuple[str, str]:
        owner, repo = urlparse(url).path.strip("/").split("/")[:2]
        return owner, repo

    async def get_repo(self, url: str) -> GetRepoResponse:
        owner, repo = self._parse_repo_url(url)
        repo_info = await self.github.get_repo(owner, repo)
        return GetRepoResponse.model_validate(repo_info.model_dump())
