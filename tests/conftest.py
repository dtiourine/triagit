from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
import pytest

from codescope.analysis.schemas import (
    GetRepoResponse,
    CommitResponse,
    ContributorResponse,
    IssueResponse,
    PullRequestResponse,
    TreeEntryResponse,
    LanguageBreakdownResponse,
)


@pytest.fixture
def raw_analysis() -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        repo=GetRepoResponse(
            full_name="owner/repo",
            description="A test repo",
            default_branch="main",
            pushed_at=now,
            size=2048,
            language="Python",
            archived=False,
            disabled=False,
            stars=150,
            forks=12,
        ),
        commits=[
            CommitResponse(sha="a1", author="gh:alice", authored_at=now - timedelta(days=1)),
            CommitResponse(sha="a2", author="gh:alice", authored_at=now - timedelta(days=8)),
            CommitResponse(sha="b1", author="gh:bob",   authored_at=now - timedelta(days=15)),
            CommitResponse(sha="c1", author="gh:carol", authored_at=now - timedelta(days=22)),
        ],
        contributors=[
            ContributorResponse(login="alice", contributions=70, type="User"),
            ContributorResponse(login="bob",   contributions=20, type="User"),
            ContributorResponse(login="carol", contributions=10, type="User"),
        ],
        issues=[
            IssueResponse(number=1, state="closed", created_at=now - timedelta(days=30), closed_at=now - timedelta(days=25), is_pull_request=False),
            IssueResponse(number=2, state="closed", created_at=now - timedelta(days=20), closed_at=now - timedelta(days=18), is_pull_request=False),
            IssueResponse(number=3, state="open",   created_at=now - timedelta(days=5),  closed_at=None, is_pull_request=False),
        ],
        pulls=[
            PullRequestResponse(number=10, state="closed", draft=False, created_at=now - timedelta(days=10), merged_at=now - timedelta(days=8), was_merged=True),
            PullRequestResponse(number=11, state="open",   draft=False, created_at=now - timedelta(days=2),  merged_at=None, was_merged=False),
        ],
        tree=[
            TreeEntryResponse(path="README.md",                  type="blob", sha="r1"),
            TreeEntryResponse(path="LICENSE",                    type="blob", sha="r2"),
            TreeEntryResponse(path=".gitignore",                 type="blob", sha="r3"),
            TreeEntryResponse(path=".github/workflows/ci.yml",   type="blob", sha="r4"),
            TreeEntryResponse(path="tests/test_main.py",         type="blob", sha="r5"),
        ],
        languages=LanguageBreakdownResponse(bytes_per_language={"Python": 9000, "Shell": 1000}),
    )
