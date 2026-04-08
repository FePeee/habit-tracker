import logging

import httpx

from config import API_URL

logger = logging.getLogger(__name__)

_timeout = httpx.Timeout(30.0, connect=5.0)
_long_timeout = httpx.Timeout(120.0, connect=10.0)


class BackendAPI:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(base_url=API_URL, timeout=_timeout)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def get_user(self, telegram_id: str) -> dict | None:
        c = await self._get_client()
        r = await c.get(f"/api/user-by-telegram/{telegram_id}")
        return r.json() if r.status_code == 200 else None

    async def register(self, telegram_id: str, name: str, timezone: str) -> httpx.Response:
        c = await self._get_client()
        return await c.post(
            "/api/register-telegram",
            json={"telegram_id": telegram_id, "name": name, "timezone": timezone},
        )

    async def link_telegram(self, code: str, telegram_id: str) -> httpx.Response:
        c = await self._get_client()
        return await c.post("/api/link-telegram", json={"code": code, "telegram_id": telegram_id})

    async def get_habits(self, telegram_id: str) -> list[dict] | None:
        c = await self._get_client()
        r = await c.get(f"/api/habits-by-telegram/{telegram_id}")
        return r.json() if r.status_code == 200 else None

    async def create_habit(self, telegram_id: str, name: str, reminder_time: str | None) -> httpx.Response:
        c = await self._get_client()
        return await c.post(
            f"/api/habits-by-telegram-create/{telegram_id}",
            json={"name": name, "reminder_time": reminder_time},
        )

    async def complete_habit(self, telegram_id: str, habit_id: str) -> httpx.Response:
        c = await self._get_client()
        return await c.post(f"/api/complete-by-telegram/{telegram_id}/{habit_id}")

    async def delete_habit(self, telegram_id: str, habit_id: str) -> httpx.Response:
        c = await self._get_client()
        return await c.delete(f"/api/habits-by-telegram-delete/{telegram_id}/{habit_id}")

    async def get_stats(self, telegram_id: str) -> dict | None:
        c = await self._get_client()
        r = await c.get(f"/api/stats/{telegram_id}")
        return r.json() if r.status_code == 200 else None

    async def update_timezone(self, telegram_id: str, timezone: str) -> httpx.Response:
        c = await self._get_client()
        return await c.patch(f"/api/user-timezone/{telegram_id}", json={"timezone": timezone})

    async def update_report_schedule(self, telegram_id: str, day: str, time: str) -> httpx.Response:
        c = await self._get_client()
        return await c.patch(
            f"/api/user-report-schedule/{telegram_id}",
            json={"report_day": day, "report_time": time},
        )

    async def get_all_users_habits(self) -> list[dict]:
        c = await self._get_client()
        r = await c.get("/api/all-users-habits")
        return r.json() if r.status_code == 200 else []

    async def get_all_users_stats(self) -> list[dict]:
        c = await self._get_client()
        r = await c.get("/api/all-users-stats")
        return r.json() if r.status_code == 200 else []

    async def get_users_with_report_schedule(self) -> list[dict]:
        c = await self._get_client()
        r = await c.get("/api/users-with-report-schedule")
        return r.json() if r.status_code == 200 else []

    async def bot_ai_advice(self, telegram_id: str, habit_name: str, issue: str) -> httpx.Response:
        c = await self._get_client()
        return await c.post(
            "/api/bot/ai-habit-advice",
            json={"telegram_id": telegram_id, "habit_name": habit_name, "issue": issue},
            timeout=_long_timeout,
        )

    async def bot_ai_rolemodel(self, telegram_id: str, role: str, existing_habits: list[str]) -> httpx.Response:
        c = await self._get_client()
        return await c.post(
            "/api/bot/ai-role-model-habits",
            json={"telegram_id": telegram_id, "role_or_profession": role, "existing_habits": existing_habits},
            timeout=_long_timeout,
        )

    async def bot_ai_suggest(self, telegram_id: str, goal: str | None) -> httpx.Response:
        c = await self._get_client()
        payload: dict = {"telegram_id": telegram_id}
        if goal:
            payload["goal"] = goal
        return await c.post("/api/bot/ai-suggest-habits", json=payload, timeout=_long_timeout)

    async def bot_ai_insights(self, telegram_id: str) -> list[dict]:
        c = await self._get_client()
        r = await c.get(f"/api/bot/ai-insights/{telegram_id}")
        return r.json() if r.status_code == 200 else []


api = BackendAPI()
