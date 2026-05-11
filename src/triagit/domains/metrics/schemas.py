from datetime import datetime

from pydantic import BaseModel

from src.triagit.domains.shared.schemas import GitHubRepoUrl


class AnalysisRequest(BaseModel):
    repo_url: GitHubRepoUrl


class GetRepoResponse(BaseModel):
    full_name: str
    description: str | None
    default_branch: str
    pushed_at: datetime | None
    size: int
    language: str | None
    archived: bool
    disabled: bool
    stars: int = 0
    forks: int = 0


class ContributorResponse(BaseModel):
    login: str
    contributions: int
    type: str


class HygieneCheck(BaseModel):
    ok: bool
    label: str
    note: str | None = None


class MetricsReport(BaseModel):
    # Repo identity
    slug: str
    repo: GetRepoResponse
    size_fmt: str
    # Health
    score: int
    score_label: str
    breakdown: dict[str, int]
    # Activity
    commits_90d: int
    unique_authors: int
    days_since_last: int
    bus_factor_pct: int
    per_week: list[int]
    top_contributors: list[ContributorResponse]
    # Issues / PRs
    open_issues: int
    closed_issues: int
    open_prs: int
    closed_prs: int
    # Hygiene
    hygiene: list[HygieneCheck]
    hygiene_passed: int
    # Languages
    language_pcts: dict[str, int]
