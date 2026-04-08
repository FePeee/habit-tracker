import os


def _env(name: str, default: str = "") -> str:
    v = (os.getenv(name) or default).strip()
    if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
        v = v[1:-1].strip()
    return v


SECRET_KEY = _env("SECRET_KEY", "habit-tracker-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

OPENROUTER_API_KEY = _env("OPENROUTER_API_KEY")
OPENROUTER_HTTP_REFERER = _env("OPENROUTER_HTTP_REFERER", "https://localhost")
OPENROUTER_APP_TITLE = _env("OPENROUTER_APP_TITLE", "Habit Tracker")

BOT_API_SECRET = _env("BOT_API_SECRET")
