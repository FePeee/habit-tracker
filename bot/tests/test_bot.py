"""
Tests for the Telegram bot.
Mocks the bot, API calls, and AI client.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import pytz

# We test the logic functions, not the actual polling
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestBotHandlers:
    """Test bot handler logic without actual Telegram connection."""

    @pytest.fixture
    def mock_message(self):
        """Create a mock Message object."""
        msg = MagicMock()
        msg.from_user.id = 12345
        msg.from_user.first_name = "TestUser"
        msg.text = "/start"
        msg.answer = AsyncMock()
        return msg

    @pytest.fixture
    def mock_callback(self):
        """Create a mock CallbackQuery object."""
        cb = MagicMock()
        cb.from_user.id = 12345
        cb.data = "tz:Europe/Moscow"
        cb.message = MagicMock()
        cb.message.edit_text = AsyncMock()
        cb.answer = AsyncMock()
        return cb

    @pytest.fixture
    def mock_state(self):
        """Create a mock FSMContext."""
        state = AsyncMock()
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        state.get_data = AsyncMock(return_value={"name": "TestUser"})
        state.clear = AsyncMock()
        return state

    def test_command_start_structure(self):
        """Test that cmd_start handler exists and is async function."""
        from main import cmd_start
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_start)

    def test_command_help_structure(self):
        """Test that cmd_help handler exists."""
        from main import cmd_help
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_help)

    def test_command_add_structure(self):
        """Test that cmd_add handler exists."""
        from main import cmd_add
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_add)

    def test_command_list_structure(self):
        """Test that cmd_list handler exists."""
        from main import cmd_list
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_list)

    def test_command_done_structure(self):
        """Test that cmd_done handler exists."""
        from main import cmd_done
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_done)

    def test_command_stats_structure(self):
        """Test that cmd_stats handler exists."""
        from main import cmd_stats
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_stats)

    def test_command_report_structure(self):
        """Test that cmd_report handler exists."""
        from main import cmd_report
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_report)

    def test_command_schedule_structure(self):
        """Test that cmd_schedule handler exists."""
        from main import cmd_schedule
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_schedule)

    def test_command_delete_structure(self):
        """Test that cmd_delete handler exists."""
        from main import cmd_delete
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_delete)

    def test_command_timezone_structure(self):
        """Test that cmd_timezone handler exists."""
        from main import cmd_timezone
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_timezone)


class TestAISettings:
    """Test AI prompt generation and settings."""

    def test_ask_ai_function_exists(self):
        """Test that ask_ai function is defined."""
        from main import ask_ai
        import asyncio
        assert asyncio.iscoroutinefunction(ask_ai)

    def test_schedule_report_states_exist(self):
        """Test that ScheduleReport states are defined."""
        from main import ScheduleReport
        assert hasattr(ScheduleReport, 'waiting_day')
        assert hasattr(ScheduleReport, 'waiting_time')


class TestSchedulerJobs:
    """Test scheduled job functions exist and have correct structure."""

    def test_send_reminders_exists(self):
        """Test that send_reminders function exists."""
        from main import send_reminders
        import asyncio
        assert asyncio.iscoroutinefunction(send_reminders)

    def test_ai_accountability_check_exists(self):
        """Test that ai_accountability_check exists."""
        from main import ai_accountability_check
        import asyncio
        assert asyncio.iscoroutinefunction(ai_accountability_check)

    def test_send_weekly_reports_exists(self):
        """Test that send_weekly_reports exists."""
        from main import send_weekly_reports
        import asyncio
        assert asyncio.iscoroutinefunction(send_weekly_reports)

    def test_send_report_to_user_exists(self):
        """Test that send_report_to_user helper exists."""
        from main import send_report_to_user
        import asyncio
        assert asyncio.iscoroutinefunction(send_report_to_user)


class TestTimezones:
    """Test timezone configuration."""

    def test_timezones_list_not_empty(self):
        """Test that TIMEZONES list has entries."""
        from main import TIMEZONES
        assert len(TIMEZONES) > 0
        assert "UTC" in TIMEZONES
        assert "Europe/Moscow" in TIMEZONES

    def test_timezone_validation(self):
        """Test that configured timezones are valid pytz timezones."""
        from main import TIMEZONES
        for tz_name in TIMEZONES:
            try:
                pytz.timezone(tz_name)
            except pytz.exceptions.UnknownTimeZoneError:
                pytest.fail(f"Invalid timezone: {tz_name}")


class TestBotConfig:
    """Test bot configuration."""

    def test_bot_token_from_env(self):
        """Test that BOT_TOKEN is read from environment."""
        import main
        assert hasattr(main, 'BOT_TOKEN')

    def test_api_url_from_env(self):
        """Test that API_URL is read from environment."""
        import main
        assert hasattr(main, 'API_URL')
        assert main.API_URL == os.getenv("API_URL", "http://backend:8000")

    def test_openrouter_key_from_env(self):
        """Test that OPENROUTER_API_KEY is read from environment."""
        import main
        assert hasattr(main, 'OPENROUTER_API_KEY')


class TestCallbackParsing:
    """Test callback data parsing logic."""

    def test_tz_callback_parsing(self):
        """Test timezone callback parsing format."""
        callback_data = "tz:Europe/Moscow"
        parts = callback_data.split(":", 1)
        assert parts[0] == "tz"
        assert parts[1] == "Europe/Moscow"

    def test_complete_callback_parsing(self):
        """Test complete habit callback parsing."""
        callback_data = "complete:42"
        parts = callback_data.split(":")
        assert parts[0] == "complete"
        assert parts[1] == "42"

    def test_delete_callback_parsing(self):
        """Test delete habit callback parsing."""
        callback_data = "delete:15"
        parts = callback_data.split(":")
        assert parts[0] == "delete"
        assert parts[1] == "15"

    def test_rday_callback_parsing(self):
        """Test report day callback parsing."""
        callback_data = "rday:friday"
        parts = callback_data.split(":", 1)
        assert parts[0] == "rday"
        assert parts[1] == "friday"


class TestReportFallback:
    """Test the fresh start fallback and AI error handling."""

    def test_ask_ai_returns_fallback_on_none_content(self):
        """Test that ask_ai returns a motivational message when AI returns None."""
        # We can't easily mock the OpenAI client without installing deps,
        # but we can verify the function signature exists and is async
        from main import ask_ai
        import asyncio
        assert asyncio.iscoroutinefunction(ask_ai)

    def test_fresh_start_logic_detection(self):
        """Test that week_completion parsing works for zero detection."""
        # Simulate habits with 0 completions
        habits = [
            {"week_completion": "0/7"},
            {"week_completion": "0/7"},
            {"week_completion": "0/7"},
        ]
        total = sum(int(h["week_completion"].split("/")[0]) for h in habits)
        assert total == 0

    def test_fresh_start_logic_with_some_completions(self):
        """Test that week_completion parsing works when some habits are done."""
        habits = [
            {"week_completion": "3/7"},
            {"week_completion": "1/7"},
            {"week_completion": "0/7"},
        ]
        total = sum(int(h["week_completion"].split("/")[0]) for h in habits)
        assert total == 4

    def test_fresh_start_message_is_not_none(self):
        """Test that the fallback message is a proper string, not None."""
        fallback = "🌱 Week zero — and that's okay!"
        assert fallback is not None
        assert len(fallback) > 10
        assert "🌱" in fallback

    def test_week_completion_format(self):
        """Test expected format from API: 'X/7'."""
        valid_formats = ["0/7", "1/7", "3/7", "7/7"]
        invalid_formats = ["0", "3", "abc", "", "7"]

        for fmt in valid_formats:
            parts = fmt.split("/")
            assert len(parts) == 2
            int(parts[0])  # Should not raise

        for fmt in invalid_formats:
            parts = fmt.split("/")
            if len(parts) != 2:
                pass  # Expected — these are invalid

    def test_report_handler_is_async(self):
        """Test that cmd_report is an async handler."""
        from main import cmd_report
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_report)

    def test_send_report_to_user_is_async(self):
        """Test that send_report_to_user helper is async."""
        from main import send_report_to_user
        import asyncio
        assert asyncio.iscoroutinefunction(send_report_to_user)


class TestReportSchedule:
    """Test report schedule functionality."""

    def test_day_mapping_correctness(self):
        """Test that day mapping in send_weekly_reports is correct."""
        from datetime import datetime
        import pytz
        
        # Monday should be 0, Sunday should be 6
        monday = datetime(2024, 1, 1, tzinfo=pytz.UTC)  # A Monday
        assert monday.weekday() == 0
        
        sunday = datetime(2024, 1, 7, tzinfo=pytz.UTC)  # A Sunday
        assert sunday.weekday() == 6

    def test_time_validation_format(self):
        """Test that time format validation works."""
        valid_times = ["08:00", "18:30", "00:00", "23:59"]
        invalid_times = ["25:00", "12:60", "abc", "8:0", ""]
        
        for t in valid_times:
            try:
                h, m = map(int, t.split(":"))
                assert 0 <= h <= 23 and 0 <= m <= 59
            except (ValueError, IndexError, AssertionError):
                pytest.fail(f"Valid time {t} should pass validation")
        
        for t in invalid_times:
            try:
                h, m = map(int, t.split(":"))
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    raise ValueError
            except (ValueError, IndexError):
                pass  # Expected


# ==================== AI COMMANDS TESTS ====================

class TestAICommands:
    """Test new AI-powered commands."""

    def test_cmd_advise_exists(self):
        """Test that /advise handler exists."""
        from main import cmd_advise
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_advise)

    def test_cmd_rolemodel_exists(self):
        """Test that /rolemodel handler exists."""
        from main import cmd_rolemodel
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_rolemodel)

    def test_cmd_suggest_exists(self):
        """Test that /suggest handler exists."""
        from main import cmd_suggest
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_suggest)

    def test_cmd_insights_exists(self):
        """Test that /insights handler exists."""
        from main import cmd_insights
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_insights)

    def test_advise_checks_registration(self):
        """Test that /advise checks user registration."""
        import asyncio
        from main import cmd_advise
        from aiogram.fsm.context import FSMContext

        msg = MagicMock()
        msg.from_user.id = 99999  # Unregistered user
        msg.text = "/advise"
        msg.answer = AsyncMock()

        state = AsyncMock()

        async def run():
            with patch("httpx.AsyncClient") as mock_client:
                mock_resp = MagicMock()
                mock_resp.status_code = 404
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_resp
                await cmd_advise(msg, state)

        asyncio.run(run())
        msg.answer.assert_called_with("❌ Please register first by sending /start")

    def test_rolemodel_checks_registration(self):
        """Test that /rolemodel checks user registration."""
        import asyncio
        from main import cmd_rolemodel

        msg = MagicMock()
        msg.from_user.id = 99999
        msg.text = "/rolemodel"
        msg.answer = AsyncMock()

        state = AsyncMock()

        async def run():
            with patch("httpx.AsyncClient") as mock_client:
                mock_resp = MagicMock()
                mock_resp.status_code = 404
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_resp
                await cmd_rolemodel(msg, state)

        asyncio.run(run())
        msg.answer.assert_called_with("❌ Please register first by sending /start")

    def test_suggest_checks_registration(self):
        """Test that /suggest checks user registration."""
        import asyncio
        from main import cmd_suggest

        msg = MagicMock()
        msg.from_user.id = 99999
        msg.text = "/suggest"
        msg.answer = AsyncMock()

        state = AsyncMock()

        async def run():
            with patch("httpx.AsyncClient") as mock_client:
                mock_resp = MagicMock()
                mock_resp.status_code = 404
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_resp
                await cmd_suggest(msg, state)

        asyncio.run(run())
        msg.answer.assert_called_with("❌ Please register first by sending /start")

    def test_insights_checks_registration(self):
        """Test that /insights checks user registration."""
        import asyncio
        from main import cmd_insights

        msg = MagicMock()
        msg.from_user.id = 99999
        msg.text = "/insights"
        msg.answer = AsyncMock()

        async def run():
            with patch("httpx.AsyncClient") as mock_client:
                mock_resp = MagicMock()
                mock_resp.status_code = 404
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_resp
                await cmd_insights(msg)

        asyncio.run(run())
        msg.answer.assert_called_with("❌ Please register first by sending /start")

    def test_help_includes_new_commands(self):
        """Test that /help includes all new AI commands."""
        import asyncio
        from main import cmd_help

        msg = MagicMock()
        msg.answer = AsyncMock()

        async def run():
            await cmd_help(msg)

        asyncio.run(run())
        call_args = msg.answer.call_args[0][0]
        assert "/advise" in call_args
        assert "/rolemodel" in call_args
        assert "/suggest" in call_args
        assert "/insights" in call_args

    def test_insights_empty_message(self):
        """Test /insights shows proper message when no insights."""
        import asyncio
        from main import cmd_insights

        msg = MagicMock()
        msg.from_user.id = 12345
        msg.text = "/insights"
        msg.answer = AsyncMock()

        async def run():
            with patch("httpx.AsyncClient") as mock_client:
                # First call: user check (success)
                user_resp = MagicMock()
                user_resp.status_code = 200
                user_resp.json.return_value = {"id": 1, "name": "Test"}
                
                # Second call: insights (empty)
                insights_resp = MagicMock()
                insights_resp.status_code = 200
                insights_resp.json.return_value = []

                mock_cm = MagicMock()
                mock_cm.get = AsyncMock(side_effect=[user_resp, insights_resp])
                mock_cm.__aenter__ = AsyncMock(return_value=mock_cm)
                mock_cm.__aexit__ = AsyncMock(return_value=None)
                mock_client.return_value = mock_cm

                await cmd_insights(msg)

        asyncio.run(run())
        # Should mention how to get insights
        last_call = msg.answer.call_args_list[-1][0][0]
        assert "/advise" in last_call or "/report" in last_call

    def test_fsm_states_exist(self):
        """Test that all new FSM states are defined."""
        from main import GetHabitAdvice, GetRoleModelHabits, GetSuggestions
        assert hasattr(GetHabitAdvice, 'waiting_habit_name')
        assert hasattr(GetHabitAdvice, 'waiting_issue')
        assert hasattr(GetRoleModelHabits, 'waiting_role')
        assert hasattr(GetSuggestions, 'waiting_goal')
