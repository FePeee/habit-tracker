# Habit Tracker — Daily Streaks, Telegram Reminders & AI Insights

[![CI](https://github.com/yourusername/habit-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/habit-tracker/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A full-stack habit tracking application with Telegram bot integration, AI-powered weekly reports, and a modern React dashboard.

## Features

- 🎯 **Track Daily Habits** — Add habits with optional daily reminders
- ✅ **Quick Completion** — Mark habits as done with inline buttons (Telegram) or checkboxes (Web)
- 📊 **Weekly Stats** — View streaks, completion rates, and progress metrics
- 🤖 **AI Reports** — Get personalized weekly accountability reports powered by AI
- ⏰ **Automatic Scheduling** — Choose when to receive weekly reports (day & time)
- 🔗 **Telegram Integration** — Link your web account to Telegram for on-the-go tracking
- 📱 **Responsive Web UI** — Modern dashboard with real-time stats

---

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/yourusername/habit-tracker.git
cd habit-tracker
cp .env.example .env
```

Edit `.env` and set your tokens:

```env
BOT_TOKEN=your_telegram_bot_token
OPENROUTER_API_KEY=your_openrouter_api_key
```

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

This starts 4 services:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **PostgreSQL**: Port 5432

### 3. How to use

1. **Register** at http://localhost:3000
2. **Copy your 6-digit link code** shown on the dashboard
3. **Open your Telegram bot** and send: `/start 123456`
4. **Add habits** via `/add` in bot or on the web dashboard
5. **Schedule AI reports** with `/schedule` in the bot

---

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start CODE` | Link your web account to Telegram |
| `/add` | Add a new habit with optional reminder time |
| `/done` | Mark habits as complete today (inline buttons) |
| `/list` | View all your habits |
| `/stats` | View streaks and weekly completion stats |
| `/report` | Get AI-generated weekly accountability report (manual) |
| `/schedule` | Set up automatic weekly reports (choose day & time) |
| `/delete` | Delete a habit |
| `/timezone` | Change your timezone |
| `/help` | Show all commands |

---

## Automatic Weekly Reports

Use `/schedule` in the Telegram bot to configure automatic AI-powered weekly reports:

1. **Choose a day** of the week (Monday–Sunday)
2. **Set a time** (e.g., `18:00`)
3. **Receive personalized AI insights** every week at that time

The AI report includes:
- Your strongest habit this week
- Habits that need more attention
- Specific actionable tips
- Encouragement and motivation

You can still get instant reports anytime with `/report`.

---

## Services & Ports

| Service | URL / Port | Description |
|---------|-----------|-------------|
| **Frontend** | http://localhost:3000 | React + Vite web app |
| **Backend API** | http://localhost:8000 | FastAPI REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI (interactive) |
| **PostgreSQL** | localhost:5432 | Database server |

---

## Project Structure

```
habit-tracker/
├── backend/                    # FastAPI + PostgreSQL
│   ├── main.py                 # API routes & business logic
│   ├── models.py               # SQLAlchemy ORM models
│   ├── database.py             # DB connection (SQLite/PostgreSQL)
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile
│   ├── pytest.ini              # Test configuration
│   ├── migrate_report_schedule.py  # Migration script
│   └── tests/                  # Backend tests (pytest)
│       ├── conftest.py
│       └── test_api.py
│
├── bot/                        # Telegram bot (aiogram 3)
│   ├── main.py                 # Bot handlers & scheduled jobs
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── pytest.ini
│   └── tests/                  # Bot tests (pytest)
│       └── test_bot.py
│
├── frontend/                   # React 18 + Vite 5
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js       # API wrapper (fetch)
│   │   ├── pages/
│   │   │   ├── AuthPage.jsx    # Login / Register
│   │   │   └── Dashboard.jsx   # Main habit tracking UI
│   │   ├── tests/              # Frontend tests (Vitest)
│   │   │   ├── setup.js
│   │   │   ├── api.test.js
│   │   │   ├── AuthPage.test.jsx
│   │   │   └── Dashboard.test.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   ├── vitest.config.js        # Test configuration
│   └── Dockerfile
│
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI/CD
│
├── docker-compose.yml          # Multi-service orchestration
├── .env.example                # Environment template
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI 0.111, SQLAlchemy 2.0, JWT Auth, PostgreSQL/SQLite |
| **Bot** | aiogram 3.7, APScheduler 3.10, OpenRouter AI (GPT) |
| **Frontend** | React 18, Vite 5, Fetch API, localStorage |
| **Database** | PostgreSQL 16 (Docker) / SQLite (local dev fallback) |
| **Testing** | pytest (backend/bot), Vitest + Testing Library (frontend) |
| **CI/CD** | GitHub Actions (automated testing on push/PR) |
| **DevOps** | Docker Compose |

---

## Testing

### Backend (pytest)

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v --cov=. --cov-report=term-missing
```

**Coverage includes:**
- Authentication (register, login, JWT validation)
- Habits CRUD (create, read, delete, user isolation)
- Completions (mark done, streak calculation, duplicate prevention)
- Telegram integration (linking, habits via telegram_id)
- Stats & report scheduling endpoints

### Frontend (Vitest + Testing Library)

```bash
cd frontend
pnpm install
pnpm test           # Run once
pnpm test:watch     # Watch mode
pnpm test:coverage  # Coverage report
```

**Coverage includes:**
- API client (mocked fetch, auth headers, error handling)
- AuthPage (login/register flows, error states, form validation)
- Dashboard (habits list, stats, completion, deletion, add form)

### Bot (pytest)

```bash
cd bot
pip install -r requirements.txt
pytest tests/ -v
```

**Coverage includes:**
- Handler existence and structure
- Callback data parsing
- Timezone validation
- Report scheduling logic
- Bot configuration

---

## Continuous Integration (GitHub Actions)

The project uses automated testing on every push and pull request:

### Jobs:
1. **Backend Tests** — pytest with coverage report
2. **Frontend Tests** — Vitest with coverage report
3. **Bot Tests** — pytest handler validation
4. **Backend Lint** — ruff linter & import checks
5. **Frontend Build** — Vite production build validation
6. **Docker Build** — Full docker compose build validation

### Status Badge:
Add this to your repo after pushing:
```markdown
[![CI](https://github.com/YOUR_USERNAME/habit-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/habit-tracker/actions/workflows/ci.yml)
```

---

## Development (without Docker)

### Database Setup

By default, the backend uses SQLite for local development. To use PostgreSQL:

```bash
# Set environment variable
export DATABASE_URL=postgresql://user:pass@localhost:5432/habitdb

# Or edit backend/database.py directly
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

API docs: http://localhost:8000/docs

### Bot

```bash
cd bot
pip install -r requirements.txt
BOT_TOKEN=your_token OPENROUTER_API_KEY=your_key API_URL=http://localhost:8000 python main.py
```

### Frontend

```bash
cd frontend
pnpm install    # or: npm install
pnpm dev        # or: npm run dev
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
# Telegram Bot Token (get from @BotFather)
BOT_TOKEN=your_telegram_bot_token_here

# OpenRouter API Key (for AI reports, get from https://openrouter.ai)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# (Optional) Custom database URL (defaults to PostgreSQL in docker-compose)
# DATABASE_URL=postgresql://habit_user:habit_pass@db:5432/habitdb
```

See `.env.example` for a template.

---

## Database Migrations

If you're adding the scheduling feature for the first time (SQLite):

```bash
cd backend
python migrate_report_schedule.py
```

This adds `report_day` and `report_time` columns to the `users` table.

For PostgreSQL in Docker, the schema is auto-created on startup via `Base.metadata.create_all()`.

---

## API Endpoints

### Authentication
- `POST /api/auth/register` — Register new user
- `POST /api/auth/login` — Login (OAuth2 password flow)
- `GET /api/auth/me` — Get current user info (requires token)

### Habits (Web)
- `GET /api/habits` — List all habits
- `POST /api/habits` — Create habit
- `DELETE /api/habits/{id}` — Delete habit
- `POST /api/habits/{id}/complete` — Mark as complete

### Telegram Integration
- `POST /api/register-telegram` — Register via Telegram
- `GET /api/user-by-telegram/{telegram_id}` — Lookup user
- `POST /api/link-telegram` — Link Telegram to web account
- `GET /api/habits-by-telegram/{telegram_id}` — List habits
- `POST /api/habits-by-telegram-create/{telegram_id}` — Create habit
- `DELETE /api/habits-by-telegram-delete/{telegram_id}/{habit_id}` — Delete habit
- `POST /api/complete-by-telegram/{telegram_id}/{habit_id}` — Complete habit

### Stats & Reports
- `GET /api/stats/{telegram_id}` — Weekly stats for user
- `GET /api/all-users-habits` — All users' habits (for bot reminders)
- `GET /api/all-users-stats` — All users' stats (for AI accountability)
- `GET /api/users-with-report-schedule` — Users with scheduled reports

### User Settings
- `PATCH /api/user-timezone/{telegram_id}` — Update timezone
- `PATCH /api/user-report-schedule/{telegram_id}` — Set report schedule

Full interactive docs: http://localhost:8000/docs

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Ensure all tests pass: `pytest` (backend/bot), `pnpm test` (frontend)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
- [aiogram](https://docs.aiogram.dev/) — Telegram Bot API framework
- [OpenRouter](https://openrouter.ai/) — Unified AI API
- [React](https://react.dev/) — UI library
- [Vitest](https://vitest.dev/) — Blazing fast test framework
