from pydantic import BaseModel
from datetime import datetime

from triagit.infrastructure.github.schemas import Commit, PullRequest


class RecentActivity(BaseModel):
    stars_count: int
    forks_count: int

    last_30_days_commits: list[Commit]
    last_30_days_pull_requests: list[PullRequest]
    top_5_recent_contributors: list[str]
    last_commit_date: datetime | None


class HygieneChecklist(BaseModel):
    has_readme: bool
    has_license: bool
    has_ci: bool
    has_tests: bool
    has_gitignore: bool


class ArchitectureEntry(BaseModel):
    path: str
    description: str


class CodeGap(BaseModel):
    description: str
    file: str | None = None


class _LLMAnalysisOutput(BaseModel):
    summary: str
    architecture: list[ArchitectureEntry]
    code_gaps: list[CodeGap]


class CodeRefresher(BaseModel):
    summary: str
    languages: dict[str, int]
    architecture: list[ArchitectureEntry]


class CompletionRoadmap(BaseModel):
    hygiene_checklist: HygieneChecklist
    code_gaps: list[CodeGap]


class TriageReport(BaseModel):
    recent_activity: RecentActivity
    refresher: CodeRefresher
    roadmap: CompletionRoadmap
