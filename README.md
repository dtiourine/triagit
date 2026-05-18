# triagit

> ⚠️ Work in progress

**Remember that side project you completely forgot about?** triagit looks at an
abandoned GitHub repository and tells you the state you left it in, how close it
is to "done," and the shortest roadmap to a minimal finished version so it no
longer feels abandoned.

Point it at an `owner/repo` and it pulls metadata, commits, contributors, issues,
PRs, the file tree, and language breakdown via the GitHub API, then turns that
into a revival report.

## Status

| Area | State |
|---|---|
| Metrics report (web UI + JSON API) | Working |
| File sampling API | Working |
| LLM code-quality review | In progress — provider infra in place; web report renders mock data |
| Revival report | Planned, not started |

## Quickstart

Requires Python 3.12+.

```bash
# Install (uv recommended, matches the Dockerfile)
uv pip install --system -e ".[dev]"

# Configure
cp .env.example .env   # set GITHUB_TOKEN

# Run
uvicorn triagit.main:app --reload
```

Then open <http://localhost:8000> for the web UI.

Docker (includes Postgres + Redis):

```bash
docker-compose up
```

## Configuration

Settings load from `.env` via `pydantic-settings`.

| Variable | Required | Notes |
|---|---|---|
| `GITHUB_TOKEN` | Yes | GitHub personal access token |
| `LLM_API_KEY` | No | Only for the in-progress LLM features |

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/metrics/analyses` | Full health report for a repo |
| `POST` | `/api/v1/samples` | Sample representative files from a repo |
| `GET` | `/` · `POST /analyze` · `GET /report` | Web UI |

## Development

```bash
ruff check src/ && ruff format src/
mypy src/
pytest
```
