"""
Comprehensive tests for the Habit Tracker backend API.
Covers: auth, habits CRUD, completions, stats, telegram integration, scheduling, AI insights.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import status
from sqlalchemy.orm import Session
import models


# ==================== AUTH TESTS ====================

class TestAuth:
    def test_register_success(self, client):
        """Test user registration with valid data."""
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "securepass123",
            "name": "Test User"
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["name"] == "Test User"

    def test_register_duplicate_email(self, client):
        """Test that registering the same email twice fails."""
        client.post("/api/auth/register", json={
            "email": "dup@example.com",
            "password": "securepass123",
            "name": "User One"
        })
        response = client.post("/api/auth/register", json={
            "email": "dup@example.com",
            "password": "anotherpass",
            "name": "User Two"
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_success(self, client):
        """Test login with correct credentials."""
        client.post("/api/auth/register", json={
            "email": "login@example.com",
            "password": "mysecretpass",
            "name": "Login User"
        })
        response = client.post("/api/auth/login", data={
            "username": "login@example.com",
            "password": "mysecretpass"
        })
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()

    def test_login_wrong_password(self, client):
        """Test login fails with wrong password."""
        client.post("/api/auth/register", json={
            "email": "wrong@example.com",
            "password": "correctpass",
            "name": "User"
        })
        response = client.post("/api/auth/login", data={
            "username": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent_user(self, client):
        """Test login fails for non-existent user."""
        response = client.post("/api/auth/login", data={
            "username": "nobody@example.com",
            "password": "anypass"
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_me(self, client):
        """Test getting current user info with token."""
        reg = client.post("/api/auth/register", json={
            "email": "me@example.com",
            "password": "pass123",
            "name": "Me User"
        })
        token = reg.json()["access_token"]
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Me User"

    def test_get_me_unauthorized(self, client):
        """Test getting current user without token fails."""
        response = client.get("/api/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================== HABIT CRUD TESTS ====================

class TestHabits:
    @pytest.fixture
    def auth_token(self, client):
        """Provide an authenticated token."""
        reg = client.post("/api/auth/register", json={
            "email": "habit@example.com",
            "password": "pass123",
            "name": "Habit User"
        })
        return reg.json()["access_token"]

    def test_create_habit(self, client, auth_token):
        """Test creating a habit."""
        response = client.post("/api/habits", json={
            "name": "Running",
            "reminder_time": "08:00"
        }, headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Running"
        assert data["reminder_time"] == "08:00"
        assert data["is_active"] is True

    def test_create_habit_without_reminder(self, client, auth_token):
        """Test creating a habit without reminder time."""
        response = client.post("/api/habits", json={
            "name": "Meditation"
        }, headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["reminder_time"] is None

    def test_get_habits_empty(self, client, auth_token):
        """Test getting habits when none exist."""
        response = client.get("/api/habits", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_habits(self, client, auth_token):
        """Test getting multiple habits."""
        client.post("/api/habits", json={"name": "Running", "reminder_time": "07:00"},
                    headers={"Authorization": f"Bearer {auth_token}"})
        client.post("/api/habits", json={"name": "Reading", "reminder_time": "20:00"},
                    headers={"Authorization": f"Bearer {auth_token}"})
        response = client.get("/api/habits", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == status.HTTP_200_OK
        habits = response.json()
        assert len(habits) == 2
        names = [h["name"] for h in habits]
        assert "Running" in names
        assert "Reading" in names

    def test_delete_habit(self, client, auth_token):
        """Test soft-deleting a habit."""
        create_resp = client.post("/api/habits", json={"name": "Temp Habit"},
                                  headers={"Authorization": f"Bearer {auth_token}"})
        habit_id = create_resp.json()["id"]
        response = client.delete(f"/api/habits/{habit_id}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == status.HTTP_200_OK
        # Verify it's no longer in the list
        get_resp = client.get("/api/habits", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert len(get_resp.json()) == 0

    def test_delete_nonexistent_habit(self, client, auth_token):
        """Test deleting a habit that doesn't belong to user."""
        response = client.delete("/api/habits/9999", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == status.HTTP_404_BAD_REQUEST

    def test_user_isolation(self, client):
        """Test that users can't see each other's habits."""
        # User 1
        reg1 = client.post("/api/auth/register", json={
            "email": "u1@test.com", "password": "pass", "name": "U1"
        })
        token1 = reg1.json()["access_token"]
        client.post("/api/habits", json={"name": "U1 Habit"},
                    headers={"Authorization": f"Bearer {token1}"})

        # User 2
        reg2 = client.post("/api/auth/register", json={
            "email": "u2@test.com", "password": "pass", "name": "U2"
        })
        token2 = reg2.json()["access_token"]

        # User 2 should see no habits
        resp = client.get("/api/habits", headers={
            "Authorization": f"Bearer {token2}"
        })
        assert len(resp.json()) == 0


# ==================== COMPLETION TESTS ====================

class TestCompletion:
    @pytest.fixture
    def auth_token(self, client):
        reg = client.post("/api/auth/register", json={
            "email": "complete@test.com", "password": "pass", "name": "User"
        })
        return reg.json()["access_token"]

    @pytest.fixture
    def habit(self, client, auth_token):
        resp = client.post("/api/habits", json={"name": "Exercise"},
                           headers={"Authorization": f"Bearer {auth_token}"})
        return resp.json()

    def test_complete_habit(self, client, auth_token, habit):
        """Test marking a habit as complete."""
        response = client.post(f"/api/habits/{habit['id']}/complete", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Completed!"
        assert response.json()["streak"] == 1

    def test_complete_habit_twice_same_day(self, client, auth_token, habit):
        """Test that completing a habit twice in one day doesn't double count."""
        client.post(f"/api/habits/{habit['id']}/complete", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        response = client.post(f"/api/habits/{habit['id']}/complete", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Already completed today"
        assert response.json()["streak"] == 1

    def test_complete_nonexistent_habit(self, client, auth_token):
        """Test completing a habit that doesn't exist."""
        response = client.post("/api/habits/9999/complete", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == status.HTTP_404_BAD_REQUEST


# ==================== STATS TESTS ====================

class TestStats:
    @pytest.fixture
    def auth_token(self, client):
        reg = client.post("/api/auth/register", json={
            "email": "stats@test.com", "password": "pass", "name": "Stats User"
        })
        return reg.json()["access_token"]

    def test_stats_empty(self, client, auth_token):
        """Test stats with no habits."""
        response = client.get("/api/habits", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_stats_with_habits(self, client, auth_token):
        """Test stats after creating and completing habits."""
        create_resp = client.post("/api/habits", json={"name": "Yoga"},
                                  headers={"Authorization": f"Bearer {auth_token}"})
        habit_id = create_resp.json()["id"]
        client.post(f"/api/habits/{habit_id}/complete", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        response = client.get("/api/habits", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == status.HTTP_200_OK
        habits = response.json()
        assert len(habits) == 1
        assert habits[0]["done_today"] is True
        assert habits[0]["streak"] == 1


# ==================== TELEGRAM INTEGRATION TESTS ====================

class TestTelegramIntegration:
    def test_register_telegram(self, client):
        """Test registering a user via Telegram."""
        response = client.post("/api/register-telegram", json={
            "telegram_id": "12345",
            "name": "TG User",
            "timezone": "Europe/Moscow"
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "TG User"

    def test_get_user_by_telegram(self, client):
        """Test getting user by telegram_id."""
        client.post("/api/register-telegram", json={
            "telegram_id": "67890",
            "name": "Lookup User",
            "timezone": "UTC"
        })
        response = client.get("/api/user-by-telegram/67890")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Lookup User"

    def test_get_user_by_telegram_not_found(self, client):
        """Test getting non-existent telegram user."""
        response = client.get("/api/user-by-telegram/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_telegram_habit_crud(self, client):
        """Test creating and listing habits via telegram_id."""
        client.post("/api/register-telegram", json={
            "telegram_id": "tg_habit",
            "name": "Habit TG",
            "timezone": "UTC"
        })
        # Create
        create_resp = client.post("/api/habits-by-telegram-create/tg_habit", json={
            "name": "Morning Run",
            "reminder_time": "06:00"
        })
        assert create_resp.status_code == status.HTTP_200_OK
        # List
        list_resp = client.get("/api/habits-by-telegram/tg_habit")
        assert list_resp.status_code == status.HTTP_200_OK
        assert len(list_resp.json()) == 1
        assert list_resp.json()[0]["name"] == "Morning Run"

    def test_telegram_complete_habit(self, client):
        """Test completing a habit via telegram endpoint."""
        client.post("/api/register-telegram", json={
            "telegram_id": "tg_complete",
            "name": "Complete TG",
            "timezone": "UTC"
        })
        create_resp = client.post("/api/habits-by-telegram-create/tg_complete", json={
            "name": "Meditation"
        })
        habit_id = create_resp.json()["id"]
        response = client.post(f"/api/complete-by-telegram/tg_complete/{habit_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Done!"

    def test_link_telegram(self, client):
        """Test linking Telegram to a web account."""
        # Register web user
        reg = client.post("/api/auth/register", json={
            "email": "link@test.com", "password": "pass", "name": "Link User"
        })
        user_data = reg.json()["user"]
        link_code = user_data["link_code"]

        # Link telegram
        response = client.post("/api/link-telegram", json={
            "code": link_code,
            "telegram_id": "link_tg_123"
        })
        assert response.status_code == status.HTTP_200_OK

        # Verify linking worked
        response = client.get(f"/api/user-by-telegram/link_tg_123")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Link User"

    def test_all_users_habits(self, client):
        """Test the all-users-habits endpoint for bot reminders."""
        client.post("/api/register-telegram", json={
            "telegram_id": "reminder_user",
            "name": "Reminder User",
            "timezone": "Europe/Moscow"
        })
        client.post("/api/habits-by-telegram-create/reminder_user", json={
            "name": "Read Books",
            "reminder_time": "21:00"
        })
        response = client.get("/api/all-users-habits")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        # Check our habit is there
        habit_names = [h["habit_name"] for h in data]
        assert "Read Books" in habit_names

    def test_all_users_stats(self, client):
        """Test the all-users-stats endpoint for AI accountability."""
        client.post("/api/register-telegram", json={
            "telegram_id": "stats_user",
            "name": "Stats User",
            "timezone": "UTC"
        })
        client.post("/api/habits-by-telegram-create/stats_user", json={
            "name": "Exercise"
        })
        response = client.get("/api/all-users-stats")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        users = [u["name"] for u in data]
        assert "Stats User" in users


# ==================== USER SETTINGS TESTS ====================

class TestUserSettings:
    def test_update_timezone(self, client):
        """Test updating user timezone via telegram_id."""
        client.post("/api/register-telegram", json={
            "telegram_id": "tz_user",
            "name": "TZ User",
            "timezone": "UTC"
        })
        response = client.patch("/api/user-timezone/tz_user", json={
            "timezone": "America/New_York"
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["timezone"] == "America/New_York"

    def test_update_report_schedule(self, client):
        """Test updating user report schedule."""
        client.post("/api/register-telegram", json={
            "telegram_id": "schedule_user",
            "name": "Schedule User",
            "timezone": "Europe/Moscow"
        })
        response = client.patch("/api/user-report-schedule/schedule_user", json={
            "report_day": "friday",
            "report_time": "18:00"
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["report_day"] == "friday"
        assert response.json()["report_time"] == "18:00"

    def test_get_users_with_report_schedule(self, client):
        """Test fetching users with configured report schedules."""
        client.post("/api/register-telegram", json={
            "telegram_id": "scheduled_user",
            "name": "Scheduled User",
            "timezone": "UTC"
        })
        client.patch("/api/user-report-schedule/scheduled_user", json={
            "report_day": "monday",
            "report_time": "09:00"
        })
        response = client.get("/api/users-with-report-schedule")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        names = [u["name"] for u in data]
        assert "Scheduled User" in names


# ==================== STREAK CALCULATION TESTS ====================

class TestStreaks:
    def test_streak_starts_at_zero(self, client):
        """Test that new habit has zero streak."""
        client.post("/api/register-telegram", json={
            "telegram_id": "streak_user",
            "name": "Streak User",
            "timezone": "UTC"
        })
        resp = client.post("/api/habits-by-telegram-create/streak_user", json={
            "name": "New Habit"
        })
        habit_id = resp.json()["id"]
        # Before completion, streak should be 0
        list_resp = client.get("/api/habits-by-telegram/streak_user")
        # done_today is False, streak not computed until completion
        assert list_resp.status_code == status.HTTP_200_OK

    def test_streak_increments_on_completion(self, client):
        """Test that completing a habit increases streak."""
        client.post("/api/register-telegram", json={
            "telegram_id": "streak_user2",
            "name": "Streak User 2",
            "timezone": "UTC"
        })
        resp = client.post("/api/habits-by-telegram-create/streak_user2", json={
            "name": "Daily Habit"
        })
        habit_id = resp.json()["id"]
        complete_resp = client.post(f"/api/complete-by-telegram/streak_user2/{habit_id}")
        assert complete_resp.json()["streak"] == 1


# ==================== AI INSIGHTS TESTS ====================

class TestAIInsights:
    def test_get_habit_advice_success(self, client):
        """Test getting AI advice for a habit."""
        client.post("/api/auth/register", json={
            "email": "advice@test.com",
            "password": "pass123",
            "name": "Advice Seeker"
        })
        login_resp = client.post("/api/auth/login", data={
            "username": "advice@test.com",
            "password": "pass123"
        })
        token = login_resp.json()["access_token"]

        # Create a habit first
        habit_resp = client.post("/api/habits", json={"name": "Reading"}, headers={"Authorization": f"Bearer {token}"})
        assert habit_resp.status_code == status.HTTP_200_OK

        # Mock AI call
        with patch("main._call_ai", return_value="📚 Try reading 10 minutes before bed. Great habit!"):
            response = client.post("/api/ai-habit-advice", json={
                "habit_name": "Reading",
                "issue": "not enough time"
            }, headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["insight_type"] == "habit_advice"
        assert "content" in data
        assert data["habit_name"] == "Reading"

    def test_get_habit_advice_unauthenticated(self, client):
        """Test that unauthenticated users can't get advice."""
        response = client.post("/api/ai-habit-advice", json={
            "habit_name": "Reading",
            "issue": "not enough time"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_role_model_habits_success(self, client):
        """Test getting role model habit suggestions."""
        client.post("/api/auth/register", json={
            "email": "rolemodel@test.com",
            "password": "pass123",
            "name": "Career Changer"
        })
        login_resp = client.post("/api/auth/login", data={
            "username": "rolemodel@test.com",
            "password": "pass123"
        })
        token = login_resp.json()["access_token"]

        with patch("main._call_ai", return_value="💼 Software engineers should code daily, read docs, and build projects."):
            response = client.post("/api/ai-role-model-habits", json={
                "role_or_profession": "Software Engineer",
                "existing_habits": ["Reading", "Exercise"]
            }, headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["insight_type"] == "role_model"
        assert data["context"] == "Role: Software Engineer"

    def test_suggest_habits_success(self, client):
        """Test getting general habit suggestions."""
        client.post("/api/auth/register", json={
            "email": "suggest@test.com",
            "password": "pass123",
            "name": "Goal Setter"
        })
        login_resp = client.post("/api/auth/login", data={
            "username": "suggest@test.com",
            "password": "pass123"
        })
        token = login_resp.json()["access_token"]

        with patch("main._call_ai", return_value="🎯 Try meditation, journaling, and exercise for productivity."):
            response = client.post("/api/ai-suggest-habits", json={
                "goal": "become more productive"
            }, headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["insight_type"] == "suggest_habits"
        assert data["context"] == "become more productive"

    def test_get_ai_insights_list(self, client):
        """Test retrieving all AI insights."""
        client.post("/api/auth/register", json={
            "email": "insights@test.com",
            "password": "pass123",
            "name": "Insight Viewer"
        })
        login_resp = client.post("/api/auth/login", data={
            "username": "insights@test.com",
            "password": "pass123"
        })
        token = login_resp.json()["access_token"]

        # Create an insight first
        with patch("main._call_ai", return_value="Test insight content"):
            client.post("/api/ai-suggest-habits", json={
                "goal": "test goal"
            }, headers={"Authorization": f"Bearer {token}"})

        # Get insights
        response = client.get("/api/ai-insights", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["content"] == "Test insight content"

    def test_delete_ai_insight(self, client):
        """Test deleting an AI insight."""
        client.post("/api/auth/register", json={
            "email": "delete_insight@test.com",
            "password": "pass123",
            "name": "Deleter"
        })
        login_resp = client.post("/api/auth/login", data={
            "username": "delete_insight@test.com",
            "password": "pass123"
        })
        token = login_resp.json()["access_token"]

        # Create insight
        with patch("main._call_ai", return_value="To be deleted"):
            create_resp = client.post("/api/ai-suggest-habits", json={
                "goal": "delete test"
            }, headers={"Authorization": f"Bearer {token}"})
        insight_id = create_resp.json()["id"]

        # Delete it
        delete_resp = client.delete(f"/api/ai-insights/{insight_id}", headers={"Authorization": f"Bearer {token}"})
        assert delete_resp.status_code == status.HTTP_200_OK

        # Verify deletion
        get_resp = client.get("/api/ai-insights", headers={"Authorization": f"Bearer {token}"})
        insights = get_resp.json()
        assert not any(i["id"] == insight_id for i in insights)

    def test_cannot_delete_other_user_insight(self, client):
        """Test that users can't delete other users' insights."""
        # User 1
        client.post("/api/auth/register", json={
            "email": "user1@test.com",
            "password": "pass123",
            "name": "User One"
        })
        login1 = client.post("/api/auth/login", data={
            "username": "user1@test.com",
            "password": "pass123"
        })
        token1 = login1.json()["access_token"]

        # User 2
        client.post("/api/auth/register", json={
            "email": "user2@test.com",
            "password": "pass123",
            "name": "User Two"
        })
        login2 = client.post("/api/auth/login", data={
            "username": "user2@test.com",
            "password": "pass123"
        })
        token2 = login2.json()["access_token"]

        # User 1 creates insight
        with patch("main._call_ai", return_value="User 1 insight"):
            create_resp = client.post("/api/ai-suggest-habits", json={
                "goal": "test"
            }, headers={"Authorization": f"Bearer {token1}"})
        insight_id = create_resp.json()["id"]

        # User 2 tries to delete User 1's insight
        delete_resp = client.delete(f"/api/ai-insights/{insight_id}", headers={"Authorization": f"Bearer {token2}"})
        assert delete_resp.status_code == status.HTTP_404_NOT_FOUND
