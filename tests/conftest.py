from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
import pytest

from triagit.infrastructure.github.schemas import (
    Commit,
    CommitDetail,
    Contributor,
    GitAuthor,
    GitHubUser,
    LanguageBreakdown,
    RepoInfo,
    RepoTree,
    TreeEntry,
)


@pytest.fixture
def raw_analysis() -> SimpleNamespace:
    now = datetime.now(timezone.utc)

    async def count_issues(owner, repo, is_pr, state):
        counts = {
            (False, "open"):   1,
            (False, "closed"): 2,
            (True,  "open"):   1,
            (True,  "closed"): 1,
        }
        return counts[(is_pr, state)]

    return SimpleNamespace(
        repo=RepoInfo(
            full_name="owner/repo",
            description="A test repo",
            default_branch="main",
            pushed_at=now,
            size=2048,
            language="Python",
            archived=False,
            disabled=False,
            license=None,
            stargazers_count=150,
            forks_count=12,
        ),
        commits=[
            Commit(sha="a1", commit=CommitDetail(author=GitAuthor(name="alice", email="a@x.com", date=now - timedelta(days=1))),  author=GitHubUser(login="alice", id=1)),
            Commit(sha="a2", commit=CommitDetail(author=GitAuthor(name="alice", email="a@x.com", date=now - timedelta(days=8))),  author=GitHubUser(login="alice", id=1)),
            Commit(sha="b1", commit=CommitDetail(author=GitAuthor(name="bob",   email="b@x.com", date=now - timedelta(days=15))), author=GitHubUser(login="bob",   id=2)),
            Commit(sha="c1", commit=CommitDetail(author=GitAuthor(name="carol", email="c@x.com", date=now - timedelta(days=22))), author=GitHubUser(login="carol", id=3)),
        ],
        contributors=[
            Contributor(login="alice", contributions=70, type="User"),
            Contributor(login="bob",   contributions=20, type="User"),
            Contributor(login="carol", contributions=10, type="User"),
        ],
        tree=RepoTree(
            sha="tree_sha",
            truncated=False,
            tree=[
                TreeEntry(path="README.md",               type="blob", size=100, sha="r1"),
                TreeEntry(path="LICENSE",                 type="blob", size=200, sha="r2"),
                TreeEntry(path=".gitignore",              type="blob", size=50,  sha="r3"),
                TreeEntry(path=".github/workflows/ci.yml",type="blob", size=300, sha="r4"),
                TreeEntry(path="tests/test_main.py",      type="blob", size=400, sha="r5"),
            ],
        ),
        languages=LanguageBreakdown(bytes_per_language={"Python": 9000, "Shell": 1000}),
        count_issues=count_issues,
    )
