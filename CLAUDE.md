# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`triagit` is a FastAPI service that analyzes the health of any GitHub repository. It fetches repo metadata, commits, contributors, issues, PRs, file tree, and language breakdown via the GitHub API and returns a consolidated report. LLM-based analysis (`src/triagit/llm/`) is under active development.

> **⚠️ Planned pivot — read before doing feature work.** The product is being
> reframed from a generic repo-health analyzer into a **project revival tool**
> ("revive that side project you abandoned"). When the user returns to feature
> work, remind them of these already-made decisions:
>
> - One repo at a time (paste a URL); no account scanning.
> - Hybrid "done" definition: LLM infers project type + proposes what "minimally
>   finished" means, user confirms/adjusts, *then* the roadmap is generated.
> - Revival report is the primary output (state → what "done" means → ordered
>   roadmap of remaining work). Code-quality review stays as a secondary tab.
> - Likely shape: a new `revival` domain module alongside `review`, two
>   synchronous LLM calls (infer target → confirm → build roadmap), reusing the
>   existing metrics/sampling/review code.
>
> None of this is built yet — it is planning only, deferred at the user's
> request. Do not start implementing it unprompted. See README "Direction" section.

## Commands

```bash
# Install (use uv if available, matches Dockerfile)
uv pip install --system -e ".[dev]"
# or
pip install -e ".[dev]"

# Run dev server
uvicorn triagit.main:app --reload

# Lint
ruff check src/
ruff format src/

# Type check
mypy src/

# Tests
pytest
pytest tests/path/to/test_file.py::test_name   # single test

# Docker (includes postgres + redis)
docker-compose up
```

## Required environment variables

All configs use `pydantic-settings` reading from `.env`:

| Variable | Required | Notes |
|---|---|---|
| `GITHUB_TOKEN` | Yes | GitHub personal access token |
| `LLM_API_KEY` | No | For future LLM providers |

The `GlobalConfig` (no prefix) and `GitHubConfig` (`GITHUB_` prefix) classes both load from `.env`.

## Architecture

### Request flow

```
HTTP request
  → FastAPI router (analysis/router.py)
  → AnalysisService (analysis/service.py)      # parses URLs, orchestrates
  → GitHubClient (github/client.py)            # async httpx wrapper
  → GitHub REST API
```

`POST /api/v1/analysis/analyses` runs all fetches concurrently via `asyncio.gather` and returns `AnalysisResponse` (the full report).

### Module layout

- **`triagit/main.py`** — FastAPI app entry point; registers the analysis router and global exception handlers for `GitHubAPIError` and `GitHubTransportError`.
- **`triagit/analysis/`** — The core domain layer. `router.py` defines all endpoints under `/api/v1/analysis`. `service.py` is the only place that calls `GitHubClient`. `dependencies.py` wires FastAPI DI: each request gets a fresh `GitHubClient` instance (via async context manager) and a new `AnalysisService`.
- **`triagit/github/`** — Self-contained GitHub API client. `schemas.py` holds frozen Pydantic models that mirror GitHub's JSON. `exceptions.py` has a hierarchy rooted at `GitHubClientError`; the client maps HTTP status codes to specific exception types. Rate-limit detection checks the `X-RateLimit-Remaining` header specifically.
- **`triagit/llm/`** — New module (in progress). `providers/` will hold `anthropic.py` and `openai.py` implementations. `config.py` has a commented-out `AnthropicConfig` template to follow when implementing.
- **`triagit/config.py`** — `GlobalConfig` with app-wide limits: `max_concurrent_github_requests`, `max_concurrent_llm_requests`, `daily_llm_budget_usd`, `per_ip_daily_analyses`.

### Schema pattern

GitHub API responses (`github/schemas.py`) use `GitHubModel` (frozen, `extra="ignore"`) and are never exposed directly to API callers. `AnalysisService` maps them to response schemas in `analysis/schemas.py`. The `GitHubRepoUrl` type in `analysis/schemas.py` validates repo URLs via `AfterValidator`.

### Dependency injection

`AnalysisServiceDep` (a typed alias in `analysis/dependencies.py`) is the only dep used in routes. It composes `get_github_client` → `get_analysis_service`. Adding new dependencies (e.g., an LLM client) follows this pattern.
