from urllib.parse import urlparse

from triagit.infrastructure.github.client import GitHubClient

from .sampler import sample_repo
from .schemas import SampledFile, SamplingReport


class SamplingService:
    def __init__(self, github: GitHubClient):
        self.github = github

    async def sample(self, repo_url: str) -> SamplingReport:
        owner, name = urlparse(repo_url).path.strip("/").split("/")[:2]
        repo = await self.github.get_repo(owner, name)
        result = await sample_repo(self.github, owner, name, repo)
        return SamplingReport(
            files=[SampledFile(path=f.path, loc=f.loc) for f in result.files],
            candidate_count=result.candidate_count,
            note=result.note,
        )
