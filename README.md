# triagit

> ⚠️ Work in progress — interfaces and scope are still changing.

A FastAPI service that analyzes the health of any public GitHub repository. Point it
at an `owner/repo`, and it pulls metadata, commits, contributors, issues, PRs, the
file tree, and language breakdown via the GitHub API and returns a consolidated
report — through a web UI or a JSON API.

## Status

| Area | State |
|---|---|
| Metrics report (web UI + JSON API) | Working |
| File sampling API | Working |
| LLM-powered code review | In progress — provider infra in place; the web report currently renders mock review data |

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
| `LLM_API_KEY` | No | Only for the in-progress LLM review feature |

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
