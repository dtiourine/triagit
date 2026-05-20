# triagit

> ⚠️ Work in progress

**Remember that side project you completely forgot about?** triagit looks at an
abandoned GitHub repository and gives you a structured triage: what the project
does, how close it is to "done," and what gaps remain so it no longer feels
abandoned.

Point it at a `github.com/owner/repo` URL and it pulls metadata, commits,
contributors, PRs, the file tree, and language breakdown via the GitHub API,
then runs an LLM analysis to generate a triage report.

## Status

| Area | State |
|---|---|
| Triage report (web UI + JSON API) | Working |
| Recent activity detection | Working |
| Code refresher (LLM summary + architecture) | Working |
| Completion roadmap (LLM code gaps) | Working |
| Hygiene checklist | Working |
| File sampling | Working |

## Quickstart

Requires Python 3.12+.

```bash
# Install (uv recommended)
uv pip install --system -e ".[dev]"

# or
pip install -e ".[dev]"

# Configure
cp .env.example .env   # set GITHUB_TOKEN and LLM_API_KEY

# Run
uv run dev
# or
uvicorn triagit.main:app --reload
```

Then open <http://localhost:8000> for the web UI.

## Configuration

Settings load from `.env` via `pydantic-settings`.

| Variable | Required | Notes |
|---|---|---|
| `GITHUB_TOKEN` | Yes | GitHub personal access token |
| `LLM_API_KEY` | Yes | Anthropic API key |
| `LLM_MODEL` | No | Defaults to `claude-haiku-4-5-20251001` |

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/triage/reports?url=<github_url>` | Full triage report for a repo |
| `GET` | `/` | Web UI landing page |
| `POST` | `/analyze` | Validates URL and shows loading screen |
| `GET` | `/report?url=<github_url>` | Rendered triage report page |

### Triage report response

```
TriageReport
├── recent_activity
│   ├── stars_count, forks_count
│   ├── last_commit_date
│   ├── last_30_days_commits
│   ├── last_30_days_pull_requests
│   └── top_5_recent_contributors
├── refresher
│   ├── summary          (LLM)
│   ├── languages        (GitHub API)
│   └── architecture     (LLM — key files with descriptions)
└── roadmap
    ├── hygiene_checklist (README, LICENSE, CI, tests, .gitignore)
    └── code_gaps        (LLM — major missing functionality)
```

A repo with activity in the last 30 days triggers an "are you sure this is
abandoned?" warning in the UI.

## Development

```bash
ruff check src/ && ruff format src/
mypy src/
pytest
```

## Direction

The product is focused on **one repo at a time** — paste a URL, get a triage.
No account scanning, no dashboards. Stateless by design.

The triage report is the primary output. A future revival workflow (LLM-infers
what "minimally finished" means, user confirms, roadmap generated) is planned
but not yet started.
