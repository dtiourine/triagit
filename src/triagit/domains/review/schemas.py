from typing import Literal

from pydantic import BaseModel, Field, computed_field

from src.triagit.domains.shared.schemas import GitHubRepoUrl

Severity = Literal["critical", "major", "minor", "info"]

Category = Literal[
    "error_handling",
    "complexity",
    "testing",
    "security",
    "style",
    "docs",
    "performance",
]


class ReviewRequest(BaseModel):
    repo_url: GitHubRepoUrl


class ExcerptLine(BaseModel):
    num: int
    text: str
    highlight: bool = False


class Finding(BaseModel):
    id: str
    severity: Severity
    category: Category
    title: str
    file: str
    line_start: int
    line_end: int
    description: str
    suggestion: str | None = None
    excerpt: list[ExcerptLine] = []
    confidence: float = Field(ge=0.0, le=1.0)


class SampledFile(BaseModel):
    path: str
    loc: int
    findings: int
    score: int  # 0-100 (derived from findings)


class ReviewReport(BaseModel):
    model: str
    duration_sec: float
    files_sampled: int
    files_total: int
    sampling_note: str
    overall: int  # 0-100, computed from findings
    files: list[SampledFile]
    findings: list[Finding]

    @computed_field
    @property
    def severity_counts(self) -> dict[Severity, int]:
        counts = {"critical": 0, "major": 0, "minor": 0, "info": 0}
        for f in self.findings:
            counts[f.severity] += 1
        return counts

    @computed_field
    @property
    def categories(self) -> list[Category]:
        seen: list[Category] = []
        for f in self.findings:
            if f.category not in seen:
                seen.append(f.category)
        return seen


class _LLMFinding(BaseModel):
    severity: Severity
    category: Category
    title: str
    file: str
    line_start: int
    line_end: int
    description: str
    suggestion: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class _LLMReviewOutput(BaseModel):
    findings: list[_LLMFinding]
