import os


def _env(name: str, default: str = "") -> str:
    v = (os.getenv(name) or default).strip()
    if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
        v = v[1:-1].strip()
    return v


BOT_TOKEN = _env("BOT_TOKEN")
API_URL = _env("API_URL", "http://backend:8000")
OPENROUTER_API_KEY = _env("OPENROUTER_API_KEY")

OPENROUTER_HEADERS = {
    "HTTP-Referer": _env("OPENROUTER_HTTP_REFERER", "https://openrouter.ai"),
    "X-OpenRouter-Title": _env("OPENROUTER_APP_TITLE", "Habit Tracker"),
}

TIMEZONES = [
    ("UTC+0", "UTC"),
    ("Moscow (UTC+3)", "Europe/Moscow"),
    ("London (UTC+0/1)", "Europe/London"),
    ("Berlin (UTC+1/2)", "Europe/Berlin"),
    ("Yekaterinburg (UTC+5)", "Asia/Yekaterinburg"),
    ("Novosibirsk (UTC+7)", "Asia/Novosibirsk"),
    ("Vladivostok (UTC+10)", "Asia/Vladivostok"),
    ("New York (UTC-5)", "America/New_York"),
    ("Los Angeles (UTC-8)", "America/Los_Angeles"),
    ("Dubai (UTC+4)", "Asia/Dubai"),
]
