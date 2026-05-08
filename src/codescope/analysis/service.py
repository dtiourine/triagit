from codescope.github.client import GitHubClient
from codescope.github.schemas import RepoInfo


class AnalysisService:
    def __init__(self, github: GitHubClient):
        self.github = github

    async def get_repo(self, owner: str, repo: str) -> RepoInfo:
        return await self.github.get_repo(owner, repo)
