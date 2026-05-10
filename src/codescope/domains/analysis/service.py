import asyncio
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from codescope.infrastructure.github.client import GitHubClient
from codescope.infrastructure.github.schemas import RepoInfo

from .schemas import ContributorResponse, GetRepoResponse, HygieneCheck, MetricsReport


class AnalysisService:
    def __init__(self, github: GitHubClient):
        self.github = github

    def _parse_repo_url(self, url: str) -> tuple[str, str]:
        owner, repo = urlparse(url).path.strip("/").split("/")[:2]
        return owner, repo

    async def get_metrics_report(self, url: str) -> MetricsReport:
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=90)
        owner, repo_name = self._parse_repo_url(url)

        repo: RepoInfo = await self.github.get_repo(owner, repo_name)

        (commits, contributors, tree, languages), (open_issues, closed_issues, open_prs, closed_prs) = (
            await asyncio.gather(
                asyncio.gather(
                    self.github.list_commits(owner, repo_name, since=since),
                    self.github.list_contributors(owner, repo_name),
                    self.github.get_tree(owner, repo_name, repo.default_branch),
                    self.github.get_languages(owner, repo_name),
                ),
                asyncio.gather(
                    self.github.count_issues(owner, repo_name, is_pr=False, state="open"),
                    self.github.count_issues(owner, repo_name, is_pr=False, state="closed"),
                    self.github.count_issues(owner, repo_name, is_pr=True,  state="open"),
                    self.github.count_issues(owner, repo_name, is_pr=True,  state="closed"),
                ),
            )
        )

        # Commit activity
        latest = max((c.authored_at for c in commits), default=None)
        if latest and latest.tzinfo is None:
            latest = latest.replace(tzinfo=timezone.utc)
        days_since_last = (now - latest).days if latest else 999
        unique_authors = len({c.author_identity for c in commits})

        buckets = [0] * 13
        for c in commits:
            dt = c.authored_at if c.authored_at.tzinfo else c.authored_at.replace(tzinfo=timezone.utc)
            weeks_ago = (now - dt).days // 7
            if 0 <= weeks_ago < 13:
                buckets[12 - weeks_ago] += 1
        per_week = buckets

        # Contributors (exclude bots)
        non_bot = [c for c in contributors if c.type != "Bot"]
        top_contributors = [
            ContributorResponse(login=c.login, contributions=c.contributions, type=c.type)
            for c in sorted(non_bot, key=lambda c: -c.contributions)[:5]
        ]
        total_contrib = sum(c.contributions for c in contributors)
        top3 = sum(c.contributions for c in sorted(contributors, key=lambda c: -c.contributions)[:3])
        bus_factor_pct = round(top3 / total_contrib * 100) if total_contrib else 0

        # Hygiene
        tree_paths = {e.path for e in tree.tree}
        hygiene = _hygiene(tree_paths)
        hygiene_passed = sum(1 for h in hygiene if h.ok)

        # Languages
        total_bytes = sum(languages.bytes_per_language.values()) or 1
        language_pcts = {
            lang: round(b / total_bytes * 100)
            for lang, b in sorted(languages.bytes_per_language.items(), key=lambda x: -x[1])
        }

        # Scoring
        if days_since_last <= 1:
            activity_score = 100
        elif days_since_last <= 7:
            activity_score = 85
        elif days_since_last <= 30:
            activity_score = 65
        elif days_since_last <= 90:
            activity_score = 35
        else:
            activity_score = 10

        total_i = open_issues + closed_issues
        if not total_i:
            issues_score = 50
        else:
            rate = closed_issues / total_i
            if rate >= 0.9:
                issues_score = 100
            elif rate >= 0.7:
                issues_score = 75
            elif rate >= 0.5:
                issues_score = 55
            else:
                issues_score = 30

        if bus_factor_pct <= 20:
            contrib_score = 100
        elif bus_factor_pct <= 40:
            contrib_score = 75
        elif bus_factor_pct <= 60:
            contrib_score = 50
        else:
            contrib_score = 25

        hygiene_score = round(hygiene_passed / len(hygiene) * 100) if hygiene else 0
        score = round(activity_score * 0.4 + hygiene_score * 0.3 + contrib_score * 0.3)

        if score >= 90:
            score_label = "Excellent"
        elif score >= 75:
            score_label = "Healthy"
        elif score >= 55:
            score_label = "Fair"
        elif score >= 35:
            score_label = "At risk"
        else:
            score_label = "Critical"

        size_kb = repo.size
        if size_kb < 1024:
            size_fmt = f"{size_kb} KB"
        elif size_kb < 1024 * 1024:
            size_fmt = f"{size_kb / 1024:.1f} MB"
        else:
            size_fmt = f"{size_kb / 1024 / 1024:.2f} GB"

        return MetricsReport(
            slug=repo.full_name,
            repo=GetRepoResponse(
                full_name=repo.full_name,
                description=repo.description,
                default_branch=repo.default_branch,
                pushed_at=repo.pushed_at,
                size=repo.size,
                language=repo.language,
                archived=repo.archived,
                disabled=repo.disabled,
                stars=repo.stargazers_count,
                forks=repo.forks_count,
            ),
            size_fmt=size_fmt,
            score=score,
            score_label=score_label,
            breakdown={
                "Activity":     activity_score,
                "Issues / PRs": issues_score,
                "Hygiene":      hygiene_score,
                "Contributors": contrib_score,
            },
            commits_90d=len(commits),
            unique_authors=unique_authors,
            days_since_last=days_since_last,
            bus_factor_pct=bus_factor_pct,
            per_week=per_week,
            top_contributors=top_contributors,
            open_issues=open_issues,
            closed_issues=closed_issues,
            open_prs=open_prs,
            closed_prs=closed_prs,
            hygiene=hygiene,
            hygiene_passed=hygiene_passed,
            language_pcts=language_pcts,
        )


# ── Private helpers ───────────────────────────────────────────────────────────

def _hygiene(paths: set[str]) -> list[HygieneCheck]:
    def has(*names: str) -> bool:
        return any(p in paths for p in names)

    def has_prefix(prefix: str) -> bool:
        return any(p.startswith(prefix) for p in paths)

    ci_ok = has_prefix(".github/workflows/")
    return [
        HygieneCheck(ok=has("README.md", "README.rst", "README.txt", "README"),  label="Has README"),
        HygieneCheck(ok=has("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE"),  label="Has LICENSE"),
        HygieneCheck(ok=ci_ok, label="Has CI configuration", note=".github/workflows" if ci_ok else None),
        HygieneCheck(ok=has_prefix("tests/") or has_prefix("test/"),             label="Has tests/ directory"),
        HygieneCheck(ok=has(".gitignore"),                                        label="Has .gitignore"),
    ]
