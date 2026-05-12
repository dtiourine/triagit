from pydantic import BaseModel

from triagit.domains.shared.schemas import GitHubRepoUrl


class SamplingRequest(BaseModel):
    repo_url: GitHubRepoUrl


class SampledFile(BaseModel):
    path: str
    loc: int


class SamplingReport(BaseModel):
    files: list[SampledFile]
    candidate_count: int
    note: str
