# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`triagit` is a FastAPI service that triages abandoned GitHub repositories. Paste a `github.com/owner/repo` URL and it returns a structured triage report: a code refresher (LLM summary + architecture), a completion roadmap (LLM code gaps), and a hygiene checklist. If the repo shows activity in the last 30 days, it surfaces a warning.

The app is stateless — no database, no persistence, pure request/response.

## Commands

```bash
# Install (uv recommended)
uv pip install --system -e ".[dev]"
# or
pip install -e ".[dev]"

# Run dev server
uv run dev
# or
uvicorn triagit.main:app --reload

# Lint
ruff check src/
ruff format src/

# Type check
mypy src/

# Tests
pytest
pytest tests/path/to/test_file.py::test_name   # single test
```

## Required environment variables

All configs use `pydantic-settings` reading from `.env`:

| Variable | Required | Notes |
|---|---|---|
| `GITHUB_TOKEN` | Yes | GitHub personal access token |
| `LLM_API_KEY` | Yes | Anthropic API key |
| `LLM_MODEL` | No | Defaults to `claude-haiku-4-5-20251001` |

## Architecture

### Request flow

```
Browser form (POST /analyze)
  → loading.html fetches GET /report?url=...
  → web/router.py calls TriageService
  → TriageService orchestrates via asyncio.gather:
      GitHubClient (6 parallel API calls)
      + LLM analysis (summary, architecture, code gaps)
  → report.html rendered and returned
```

API consumers can call `GET /api/v1/triage/reports?url=<github_url>` directly for the JSON response.

### Module layout

- **`triagit/main.py`** — FastAPI app entry point; registers routers and global exception handlers.
- **`triagit/domains/triage/`** — Core domain. `service.py` orchestrates all GitHub fetches and LLM calls. `schemas.py` defines `TriageReport` and its nested models. `router.py` exposes `GET /triage/reports`.
- **`triagit/domains/sampling/`** — File sampling logic used by the triage service to select representative files for LLM analysis.
- **`triagit/domains/shared/`** — `GitHubRepoUrl` validated type, shared URL validation utilities.
- **`triagit/domains/web/`** — Jinja2 templates and web routes (`/`, `/analyze`, `/report`). Uses `TriageServiceDep` directly to render the report page.
- **`triagit/infrastructure/github/`** — Async httpx wrapper around the GitHub REST API. `client.py` maps HTTP errors to typed exceptions. `schemas.py` holds frozen Pydantic models mirroring GitHub's JSON (never exposed to callers directly).
- **`triagit/infrastructure/llm/`** — LLM provider abstraction. `base.py` defines `LLMClient` protocol. `providers/anthropic.py` is the active implementation. `dependencies.py` wires FastAPI DI.

### Dependency injection pattern

Dependencies are typed aliases (`Annotated[T, Depends(...)]`) defined in each domain's `dependencies.py`. Routes only import the alias, not the underlying service. Example: `TriageServiceDep` composes `get_github_client` → `get_llm_client` → `get_triage_service`.

### Schema pattern

GitHub API responses use `GitHubModel` (frozen, `extra="ignore"`) and are never returned directly to callers. The triage service maps them to `TriageReport` defined in `triage/schemas.py`.

## TODO

The following are known improvements to work on in future sessions. Remind the user of these when relevant.

- **GitHub client retries** — Add retry logic with exponential backoff for rate-limit responses (`429`, `X-RateLimit-Remaining: 0`) and transient errors (`5xx`). The client currently raises immediately on these.

- **API rate limiting & security** — Add per-IP rate limiting to the triage endpoints to prevent abuse (the LLM call makes each request expensive). Also review other security hardening: input validation, request size limits, timeouts.

- **Async correctness audit** — Audit the service and client for any blocking calls running on the event loop (e.g. synchronous I/O, CPU-bound work). Verify `asyncio.gather` usage is optimal and no tasks are inadvertently serialized.

- **Dependency injection review** — Verify all DI wiring is correct: clients are properly scoped per-request, no shared mutable state leaks between requests, async context managers are used where needed.

- **Code cleanup** — General pass for modularity and readability: long functions, unclear naming, any logic that belongs in a different layer, dead code.

- **UI polish** — Continue iterating on the web templates (report page layout, loading experience, mobile responsiveness, edge cases like repos with no code gaps or no languages detected).

## Direction

One repo at a time — paste a URL, get a triage. No account scanning, no dashboards.

A future **revival workflow** is planned but not started: LLM infers what "minimally finished" means for the project type, user confirms/adjusts, then a prioritized roadmap is generated. This would live in a new `revival` domain module. Do not start implementing it unprompted.
