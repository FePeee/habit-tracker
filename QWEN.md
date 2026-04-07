# Habit Tracker — Project Context & AI Assistant Instructions

## Project Overview

A full-stack habit tracking application with:
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL (SQLite fallback for local dev)
- **Bot**: aiogram 3.x + APScheduler + OpenRouter AI (weekly reports)
- **Frontend**: React 18 + Vite 5 (no router, no CSS framework, inline styles)
- **Database**: PostgreSQL 16 (Docker) / SQLite (local dev)
- **DevOps**: Docker Compose (5 services), pgAdmin, GitHub Actions CI

---

## Core Architecture

### Backend (`backend/`)
- **Entry point**: `main.py` — FastAPI app with all REST endpoints
- **Models**: `models.py` — User, Habit, Completion (SQLAlchemy ORM)
- **Database**: `database.py` — Reads `DATABASE_URL` env var, falls back to SQLite
- **Auth**: JWT tokens via `python-jose`, bcrypt password hashing
- **Key endpoints**:
  - `/api/auth/register`, `/api/auth/login`, `/api/auth/me` — Web auth
  - `/api/habits` (GET/POST/DELETE) — Web habit CRUD
  - `/api/habits/{id}/complete` — Mark complete
  - `/api/register-telegram`, `/api/link-telegram` — Telegram linking
  - `/api/habits-by-telegram/{telegram_id}` — Bot habit endpoints
  - `/api/all-users-habits`, `/api/all-users-stats` — Bot bulk endpoints
  - `/api/user-report-schedule/{telegram_id}` — Schedule AI reports
  - `/api/users-with-report-schedule` — Get users with schedules

### Bot (`bot/`)
- **Entry point**: `main.py` — aiogram bot with FSM states
- **Commands**: `/start`, `/add`, `/done`, `/list`, `/stats`, `/report`, `/schedule`, `/delete`, `/timezone`, `/help`
- **Scheduled jobs** (APScheduler):
  - `send_reminders` — every minute, habit reminders by timezone
  - `ai_accountability_check` — daily at 21:00, AI nudges for skipped habits
  - `send_weekly_reports` — every 5 minutes, checks user schedules and sends AI reports
- **AI**: OpenRouter API (`openai/gpt-oss-120b` model) for accountability messages

### Frontend (`frontend/`)
- **Entry point**: `src/main.jsx` → `App.jsx`
- **Pages**: `AuthPage.jsx` (login/register), `Dashboard.jsx` (main UI)
- **API**: `src/api/client.js` — thin fetch wrapper with JWT in localStorage
- **No routing library** — conditional rendering based on auth state
- **No state management** — plain React useState/useEffect

### Docker Compose Services
1. `db` — PostgreSQL 16 Alpine (port 5432)
2. `backend` — FastAPI on port 8000 (with `--reload`)
3. `bot` — aiogram bot (depends on backend)
4. `frontend` — React dev server on port 3000 (with Vite HMR)
5. `pgadmin` — pgAdmin 4 on port 5050 (login: `admin@habit.local` / `admin`)

---

## Testing Standards

### Backend Tests (pytest)
- **Location**: `backend/tests/`
- **Config**: `backend/pytest.ini`
- **Fixtures**: `conftest.py` provides `db` (fresh in-memory SQLite per test) and `client` (FastAPI TestClient)
- **Structure**: Class-based (`TestAuth`, `TestHabits`, etc.) with descriptive test names
- **Run**: `cd backend && pytest tests/ -v --cov=. --cov-report=term-missing`

**Rules for writing backend tests:**
1. Use `client` fixture for HTTP requests (FastAPI TestClient)
2. Use `db` fixture for direct DB access (auto-created/dropped per test)
3. Always register a user first, then use JWT token for authenticated requests
4. Test both success and failure paths
5. Test edge cases: duplicates, non-existent resources, user isolation
6. Use `fastapi.status` constants for status code assertions
7. Keep tests independent — no shared state between tests

### Frontend Tests (Vitest + Testing Library)
- **Location**: `frontend/src/tests/`
- **Config**: `frontend/vitest.config.js`
- **Setup**: `setup.js` imports `@testing-library/jest-dom` matchers
- **Run**: `cd frontend && pnpm test` (or `pnpm test:watch`, `pnpm test:coverage`)

**Rules for writing frontend tests:**
1. Mock `global.fetch` — never hit real API in unit tests
2. Use `@testing-library/react` for rendering and queries
3. Use `@testing-library/user-event` for interactions (click, type)
4. Use `vi.waitFor()` for async state updates
5. Clean up with `afterEach(() => cleanup())` (already in setup.js)
6. Test user-facing behavior, not implementation details
7. Mock localStorage when testing auth flows
8. Test error states, loading states, and empty states

### Bot Tests (pytest)
- **Location**: `bot/tests/`
- **Config**: `bot/pytest.ini`
- **Approach**: Test handler existence, callback parsing, config validation (no real Telegram)
- **Run**: `cd bot && pytest tests/ -v`

**Rules for writing bot tests:**
1. Use `unittest.mock.MagicMock` and `AsyncMock` for bot/message objects
2. Test callback data parsing logic (split, extract ID, etc.)
3. Verify all handlers are async coroutines with `asyncio.iscoroutinefunction()`
4. Test timezone validation, time format validation
5. Test day mapping correctness (Python weekday: 0=Monday, 6=Sunday)
6. Mock `httpx.AsyncClient` for backend API calls
7. Mock `AsyncOpenAI` for AI response tests

---

## Code Style & Conventions

### Python (Backend & Bot)
- No linter enforced currently (ruff available but not mandatory)
- Use type hints where practical
- Docstrings for functions > 5 lines
- Snake_case for functions/variables, PascalCase for classes
- Import order: stdlib → third-party → local
- Error handling: return error messages to user, log exceptions

### JavaScript/JSX (Frontend)
- No linting configured yet
- Inline CSS styles (no CSS modules, no styled-components)
- Functional components only (no class components)
- `useState`/`useEffect` for all state and side effects
- API errors caught and stored in local state for display
- Token in `localStorage` — no refresh token logic

### Database
- Migrations via `Base.metadata.create_all()` on startup (no Alembic in use)
- For SQLite manual migrations: `backend/migrate_report_schedule.py`
- For PostgreSQL: schema auto-created on container start
- **Never** commit `.db` files or `postgres_data/` volumes

---

## Critical Rules for AI Assistant

### When Adding Features

1. **ALWAYS write tests alongside new code** — no exceptions
   - Backend: add tests to `backend/tests/test_api.py` or create new test file
   - Frontend: add tests to `frontend/src/tests/` with `.test.jsx` or `.test.js` extension
   - Bot: add tests to `bot/tests/test_bot.py` or create new test file

2. **Test structure must match existing patterns**:
   - Backend: class-based with `Test*` naming, use `client` and `db` fixtures
   - Frontend: `describe`/`it` blocks, mock `fetch`, use Testing Library
   - Bot: validate handler existence, test callback parsing, mock external calls

3. **Never break existing functionality**:
   - Run existing tests before submitting changes
   - If tests can't run (missing deps), at minimum verify syntax with `python -m py_compile`

4. **Update documentation when API changes**:
   - Add new endpoints to README.md API section
   - Update bot commands table if adding commands
   - Update `CHANGES.md` with summary

### When Fixing Bugs

1. **Write a regression test first** — reproduce the bug as a failing test
2. Fix the bug, confirm test passes
3. Never delete a test that caught a real bug — it prevents regression

### When Refactoring

1. **Never change test assertions** unless the expected behavior genuinely changed
2. If tests fail after refactoring, the refactor broke something — fix the code, not the test
3. Maintain backward compatibility for API endpoints (bot depends on them)

### Database Changes

1. **Always consider both SQLite and PostgreSQL** — test with in-memory SQLite for unit tests
2. For new columns: add to `models.py` AND provide migration script in `backend/migrate_*.py`
3. Update `conftest.py` if schema changes affect test fixtures
4. Never hardcode database paths — use `os.getenv("DATABASE_URL", ...)` pattern

### Docker & CI

1. **Never commit `.env`** — only commit `.env.example` with placeholders
2. If adding new env vars: update `.env.example`, `docker-compose.yml`, and README
3. CI runs on push/PR — broken CI blocks merges
4. Test Docker builds locally with `docker compose build` before pushing

---

## Quick Reference Commands

```bash
# Run all tests
cd backend && pytest tests/ -v
cd frontend && pnpm test
cd bot && pytest tests/ -v

# Run with coverage
cd backend && pytest --cov=. --cov-report=html
cd frontend && pnpm test:coverage

# Syntax check (when deps not installed)
python -m py_compile path/to/file.py

# Docker
docker-compose up --build           # Start all services
docker-compose up backend -d        # Start backend only
docker-compose down -v              # Stop and remove volumes

# Frontend dev
cd frontend && pnpm install
cd frontend && pnpm dev

# Backend dev (without Docker)
cd backend && pip install -r requirements.txt
cd backend && uvicorn main:app --reload

# Bot dev (without Docker)
cd bot && pip install -r requirements.txt
cd bot && BOT_TOKEN=xxx OPENROUTER_API_KEY=yyy API_URL=http://localhost:8000 python main.py
```

---

## Environment Variables

| Variable | Service | Required | Description |
|----------|---------|----------|-------------|
| `BOT_TOKEN` | bot | Yes | Telegram bot token from @BotFather |
| `OPENROUTER_API_KEY` | bot | Yes | OpenRouter API key for AI reports |
| `API_URL` | bot | No | Backend URL (default: `http://backend:8000`) |
| `DATABASE_URL` | backend | No | DB URL (default: `sqlite:///./habittracker.db`) |
| `VITE_API_URL` | frontend | No | Backend URL for frontend (default: `http://localhost:8000`) |
| `PGADMIN_DEFAULT_EMAIL` | pgadmin | No | pgAdmin login email |
| `PGADMIN_DEFAULT_PASSWORD` | pgadmin | No | pgAdmin login password |

---

## Known Limitations & Technical Debt

1. **No input validation on habit names** — empty strings accepted
2. **No rate limiting** — bot/backend can be spammed
3. **No refresh tokens** — JWT expires in 7 days, user must re-login
4. **No pagination** — `/api/habits` returns all habits at once
5. **No e2e tests** — only unit/integration tests, no Cypress/Playwright
6. **No linting in CI** — ruff configured but set to `|| true` (non-blocking)
7. **Streak calculation edge case** — doesn't handle timezone-aware dates properly
8. **Bot uses MemoryStorage** — FSM state lost on restart (fine for dev, not for prod)
9. **No health check endpoint** — `/docs` works but no dedicated `/health`
10. **Frontend has no error boundary** — unhandled errors crash the entire app

### Resolved Issues

1. **AI report returning "None"** (April 2026) — Fixed with:
   - `ask_ai()` now checks for `None`/empty content and returns motivational fallback
   - `cmd_report` and `send_report_to_user` detect 0% week completion and skip AI entirely
   - Fresh start message sent directly: "🌱 Week zero — and that's okay!"

---

## File Map

```
habit-tracker/
├── backend/
│   ├── main.py                  # FastAPI app, all REST endpoints
│   ├── models.py                # SQLAlchemy models (User, Habit, Completion)
│   ├── database.py              # DB engine setup (SQLite/PostgreSQL)
│   ├── requirements.txt         # Python deps
│   ├── pytest.ini               # Pytest config
│   ├── migrate_report_schedule.py  # SQLite migration
│   └── tests/
│       ├── conftest.py          # Fixtures: db, client
│       └── test_api.py          # 25+ API tests
│
├── bot/
│   ├── main.py                  # aiogram bot, handlers, scheduled jobs
│   ├── requirements.txt         # Python deps
│   ├── pytest.ini               # Pytest config
│   └── tests/
│       └── test_bot.py          # 20+ bot tests
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx             # React entry point
│   │   ├── App.jsx              # Auth check → Dashboard or AuthPage
│   │   ├── api/client.js        # Fetch wrapper (register, login, habits)
│   │   ├── pages/
│   │   │   ├── AuthPage.jsx     # Login/Register form
│   │   │   └── Dashboard.jsx    # Habits list, stats, add form
│   │   └── tests/
│   │       ├── setup.js         # Testing Library setup
│   │       ├── api.test.js      # API client tests
│   │       ├── AuthPage.test.jsx
│   │       └── Dashboard.test.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── vitest.config.js         # Vitest config
│
├── pgadmin/
│   └── servers.json             # pgAdmin auto-connect config
│
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI (7 jobs)
│
├── docker-compose.yml           # 5 services: db, backend, bot, frontend, pgadmin
├── .env.example                 # Environment template
├── .gitignore
├── LICENSE                      # MIT
├── README.md                    # Full documentation
└── CHANGES.md                   # Detailed change log
└── QWEN.md                      # THIS FILE — project context for AI assistant
```

---

## AI Assistant Priority Rules

When working on this project, follow these priorities:

1. **Tests first** — Always write tests before or alongside implementation
2. **Don't break CI** — Changes must pass existing tests
3. **Follow patterns** — Match existing code style and test structure
4. **Document changes** — Update README/CHANGES when adding features
5. **Be explicit** — Never assume dependencies; verify before using
6. **Safety over speed** — No destructive operations without confirmation
7. **Russian explanations** — Prefer Russian for explanations, English for code/comments

---

*Last updated: April 2026*
