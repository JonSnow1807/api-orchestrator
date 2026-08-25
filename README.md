# API Orchestrator

A self-hosted API development platform — collections, environments, mock servers, test
generation, governance rules, and a visual workflow builder — built as a solo project with a
FastAPI backend and a React frontend. Apache 2.0 licensed.

This README describes what the code actually does. The key numbers below name the command that
produced them, so you can re-measure everything yourself.

## What's here

- **FastAPI backend** (`backend/`) — 307 registered REST endpoints plus 3 WebSocket routes
  across 25 routers: auth (JWT with refresh tokens), collections, environments, workspaces,
  mock servers, governance, monitoring, and more. Boots against SQLite out of the box; Postgres
  is wired in via `DATABASE_URL` (psycopg2 ships in requirements), though verification here used
  SQLite.
- **React 18 + Vite frontend** (`frontend/`) — 78 components, including a drag-and-drop
  workflow builder (reactflow) with API-call / decision / transform / delay blocks.
- **Service virtualization** (`backend/src/service_virtualization.py`) — mock servers with 8
  behaviors: static, dynamic (faker-generated), stateful, conditional, proxy, chaos, record,
  replay. Each has a real handler, not just an enum name.
- **Natural-language test generation** (`backend/src/natural_language_testing.py`) — 28
  regex-to-template patterns that turn phrases like "response time is under 200ms" into
  runnable assertions. Pattern matching, not an LLM.
- **API governance engine** (`backend/src/api_governance.py`) — rule-based OpenAPI validation
  (HTTPS enforcement, naming conventions, documentation requirements) with severity scoring,
  HTML/JSON reports, and a CLI command.
- **Multi-protocol testing** (`backend/src/multi_protocol.py`) — WebSocket, SSE, GraphQL, and
  SOAP clients are real. gRPC support only speaks gRPC-Web JSON over HTTP, not native gRPC.
- **AI-assisted analysis** (`backend/src/agents/ai_agent.py`) — security and performance
  analysis via the Anthropic or OpenAI API when `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` is set.
  **Without a key it returns a canned heuristic report** — see Limitations.
- **SDK generation** — working client generators for 10 languages (Python, JavaScript,
  TypeScript, Java, C#, Go, Ruby, PHP, Rust, Kotlin). Other language names fall back to a
  generic stub.
- **CLI** (`cli/`) — Newman-style collection runner with governance validation. Runs from the
  repo checkout (`python cli/api_orchestrator_cli_enhanced.py --help`) with the backend
  requirements installed; the governance command needs the backend running and an authenticated
  account. A `pip` package definition exists but its installed entry point currently can't
  resolve the backend imports, and nothing is published to PyPI or npm.
- **VS Code extension** (`vscode-extension/`) — published on the marketplace as
  [`ChinmayShrivastava.api-orchestrator`](https://marketplace.visualstudio.com/items?itemName=ChinmayShrivastava.api-orchestrator) (v1.0.0).

## Quick start

Verified on macOS (Apple Silicon) with Python 3.11 and Node 20.

```bash
# Backend — serves http://localhost:8000 (interactive docs at /docs)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
uvicorn src.main:app --port 8000

# Frontend — serves http://localhost:5173
cd frontend
npm install
npm run dev
```

`backend/.env.example` documents the optional configuration (Postgres, Redis cache, AI API
keys, Stripe). Nothing beyond `SECRET_KEY` is required for a local run — without one, a random
key is generated per process, which invalidates sessions on restart.

Note: `docker-compose.yml` currently builds only the backend + Postgres + Redis + nginx; it
does not build or serve the frontend. Use the commands above for local development.

## Testing

```bash
cd backend
python -m pytest tests/unit -v          # 97 tests, all passing
python -m pytest tests/integration -v   # needs the server running on :8000
```

Measured on a clean checkout (2026-08-25): `tests/unit` passes 97/97 in ~9s. The integration
directory adds 11 more, 6 of which are currently skipped (async tests pending pytest-asyncio
configuration). The repository root also contains a number of `test_*.py` scripts from earlier
development — those are standalone demos, not part of the test suite.

## Honest numbers

| Metric | Value | How it was measured |
|---|---|---|
| Registered endpoints | 307 unique (path, method) pairs | Boot the app, iterate `app.routes`, exclude auto HEAD/OPTIONS (fresh venv from `backend/requirements.txt`, 2026-08-25) |
| WebSocket routes | 3 | Same enumeration |
| Routers mounted | 25 | `grep -c include_router backend/src/main.py` |
| React components | 78 files | `find frontend/src/components -name '*.jsx' -o -name '*.tsx' \| wc -l` |
| Backend unit tests | 97 passing | `cd backend && python -m pytest tests/unit` |
| Mock behaviors | 8 implemented | `backend/src/service_virtualization.py` |
| NL test patterns | 28 | `backend/src/natural_language_testing.py` |
| SDK languages with real templates | 10 | `backend/src/agents/code_generator_agent.py` |

## Limitations and honest caveats

Things this project does **not** do, or does less than a feature list might imply:

- **The "AI agents" are mostly not AI.** Of the 19 agent classes, only two can call an LLM
  (`ai_agent.py` and the LLM decision engine), and both require an API key. Everything else —
  including the "AI employee" modules — is deterministic: template generation, regex scanning,
  and keyword routing. With no API key configured, the security analysis endpoint returns a
  hardcoded sample report rather than analyzing your API.
- **No trained ML models ship with this repo.** Modules that import scikit-learn never call
  `.fit()` in the serving path. Any "accuracy" or "confidence" figures produced by the code are
  heuristic constants, not measured model performance.
- **The experimental `kill_shots/` modules are prototypes.** API time-machine snapshotting is
  in-memory only and its rollback generator is a stub; the "telepathic discovery" scanner has 4
  working discovery methods (JS crawling, Swagger probing, GraphQL introspection, WebSocket
  probing) and returns placeholder data for network/DNS/code scanning; "quantum" test
  generation is randomized fuzzing. None of these are mounted as API routes.
- **SSO is scaffolding.** SAML (python3-saml) and OIDC (authlib) integration code exists and
  the user schema supports it, but neither flow completes login as shipped (the SAML callback
  never receives the POSTed assertion, and the OIDC flow requires a session middleware that
  isn't installed). Treat it as a starting point, not a feature.
- **Cloud deployment is AWS-only in practice.** The deployment agent makes real boto3 calls
  for ECS and Lambda; the GCP and Azure paths return formatted strings without calling any SDK.
- **Integrations:** GitHub, Jenkins, Datadog, and Slack have real API validation/sync code;
  other integration names are scaffolding.
- **Single-author project, reviewed but not battle-tested.** No production deployment is
  currently maintained, and there are no load-test results worth citing.

## Architecture

```
backend/src/
  main.py                  # FastAPI app, router mounting, auth endpoints
  routes/                  # 26 routers (25 mounted)
  agents/                  # 13 task modules (codegen, discovery, mocking, docs, ...)
  ai_employee/             # experimental automation modules (deterministic)
  kill_shots/              # experimental prototypes (not mounted)
  service_virtualization.py, api_governance.py, natural_language_testing.py, ...
frontend/src/
  components/              # 78 React components (Dashboard, workflow builder, ...)
cli/                       # pip-installable CLI (collection runner + governance)
vscode-extension/          # published extension source + packaged .vsix
```

## Contributing

```bash
git clone https://github.com/JonSnow1807/api-orchestrator.git
cd api-orchestrator/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/unit -v
```

Issues and PRs are welcome. If you change behavior, add a test under `backend/tests/` and make
sure `pytest tests/unit` stays green.

## License

Apache 2.0 — see [LICENSE](LICENSE). © 2024–2025 Chinmay Shrivastava.
