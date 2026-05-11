import time
from urllib.parse import urlparse

from triagit.infrastructure.github.client import GitHubClient
from triagit.infrastructure.llm.base import LLMClient

from .prompts import REVIEW_INSTRUCTIONS
from .sampler import SampledSource, sample_repo
from .schemas import (
    ExcerptLine,
    Finding,
    ReviewReport,
    SampledFile,
    _LLMReviewOutput,
)

_SEVERITY_WEIGHTS = {"critical": 15, "major": 8, "minor": 3, "info": 1}


class ReviewService:
    def __init__(self, github: GitHubClient, llm: LLMClient):
        self.github = github
        self.llm = llm

    async def get_review_report(self, repo_url: str) -> ReviewReport:
        started = time.monotonic()
        owner, name = urlparse(repo_url).path.strip("/").split("/")[:2]

        repo = await self.github.get_repo(owner, name)
        sampling = await sample_repo(self.github, owner, name, repo)

        prompt = _build_prompt(sampling.files)
        llm_output = await self.llm.generate_structured_response(
            prompt, _LLMReviewOutput
        )

        sources_by_path = {f.path: f for f in sampling.files}
        findings: list[Finding] = []
        for i, lf in enumerate(llm_output.findings, start=1):
            source = sources_by_path.get(lf.file)
            excerpt = (
                _make_excerpt(source.content, lf.line_start, lf.line_end)
                if source
                else []
            )
            findings.append(
                Finding(
                    id=f"f{i}",
                    severity=lf.severity,
                    category=lf.category,
                    title=lf.title,
                    file=lf.file,
                    line_start=lf.line_start,
                    line_end=lf.line_end,
                    description=lf.description,
                    suggestion=lf.suggestion,
                    excerpt=excerpt,
                    confidence=lf.confidence,
                )
            )

        files: list[SampledFile] = []
        for source in sampling.files:
            per_file = [f for f in findings if f.file == source.path]
            penalty = sum(_SEVERITY_WEIGHTS[f.severity] for f in per_file)
            files.append(
                SampledFile(
                    path=source.path,
                    loc=source.loc,
                    findings=len(per_file),
                    score=max(0, 100 - penalty),
                )
            )

        overall = max(0, 100 - sum(_SEVERITY_WEIGHTS[f.severity] for f in findings))

        return ReviewReport(
            model=self.llm.model,
            duration_sec=time.monotonic() - started,
            files_sampled=len(sampling.files),
            files_total=sampling.candidate_count,
            sampling_note=sampling.note,
            overall=overall,
            files=files,
            findings=findings,
        )


def _build_prompt(files: list[SampledSource]) -> str:
    parts = [REVIEW_INSTRUCTIONS, "Files:"]
    for f in files:
        parts.append(f"\n--- {f.path} ---")
        parts.append(
            "\n".join(
                f"{i + 1:>4}  {line}" for i, line in enumerate(f.content.splitlines())
            )
        )
    return "\n".join(parts)


def _make_excerpt(
    content: str, line_start: int, line_end: int, context: int = 2
) -> list[ExcerptLine]:
    lines = content.splitlines()
    start = max(1, line_start - context)
    end = min(len(lines), line_end + context)
    return [
        ExcerptLine(num=i, text=lines[i - 1], highlight=(line_start <= i <= line_end))
        for i in range(start, end + 1)
    ]
