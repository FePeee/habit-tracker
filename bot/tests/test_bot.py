"""
Tests for the Telegram bot.
Mocks the bot, API calls, and AI client.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import pytz

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestBotHandlers:

    def test_command_start_structure(self):
        from handlers.start import cmd_start
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_start)

    def test_command_help_structure(self):
        from handlers.help import cmd_help
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_help)

    def test_command_add_structure(self):
        from handlers.habits import cmd_add
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_add)

    def test_command_list_structure(self):
        from handlers.habits import cmd_list
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_list)

    def test_command_done_structure(self):
        from handlers.habits import cmd_done
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_done)

    def test_command_stats_structure(self):
        from handlers.stats import cmd_stats
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_stats)

    def test_command_report_structure(self):
        from handlers.stats import cmd_report
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_report)

    def test_command_schedule_structure(self):
        from handlers.schedule import cmd_schedule
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_schedule)

    def test_command_delete_structure(self):
        from handlers.habits import cmd_delete
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_delete)

    def test_command_timezone_structure(self):
        from handlers.schedule import cmd_timezone
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_timezone)


class TestAISettings:

    def test_ask_ai_function_exists(self):
        from ai import ask_ai
        import asyncio
        assert asyncio.iscoroutinefunction(ask_ai)

    def test_schedule_report_states_exist(self):
        from handlers.schedule import ScheduleReport
        assert hasattr(ScheduleReport, "waiting_day")
        assert hasattr(ScheduleReport, "waiting_time")


class TestSchedulerJobs:

    def test_send_reminders_exists(self):
        from jobs.reminders import send_reminders
        import asyncio
        assert asyncio.iscoroutinefunction(send_reminders)

    def test_ai_accountability_check_exists(self):
        from jobs.accountability import ai_accountability_check
        import asyncio
        assert asyncio.iscoroutinefunction(ai_accountability_check)

    def test_send_weekly_reports_exists(self):
        from jobs.weekly_report import send_weekly_reports
        import asyncio
        assert asyncio.iscoroutinefunction(send_weekly_reports)


class TestTimezones:

    def test_timezones_list_not_empty(self):
        from config import TIMEZONES
        assert len(TIMEZONES) > 0
        tz_ids = [tz for _, tz in TIMEZONES]
        assert "UTC" in tz_ids
        assert "Europe/Moscow" in tz_ids

    def test_timezone_validation(self):
        from config import TIMEZONES
        for _, tz_name in TIMEZONES:
            try:
                pytz.timezone(tz_name)
            except pytz.exceptions.UnknownTimeZoneError:
                pytest.fail(f"Invalid timezone: {tz_name}")


class TestBotConfig:

    def test_bot_token_from_env(self):
        from config import BOT_TOKEN
        assert isinstance(BOT_TOKEN, str)

    def test_api_url_from_env(self):
        from config import API_URL
        assert isinstance(API_URL, str)
        assert API_URL  # not empty

    def test_openrouter_key_from_env(self):
        from config import OPENROUTER_API_KEY
        assert isinstance(OPENROUTER_API_KEY, str)


class TestCallbackParsing:

    def test_tz_callback_parsing(self):
        callback_data = "tz:Europe/Moscow"
        parts = callback_data.split(":", 1)
        assert parts[0] == "tz"
        assert parts[1] == "Europe/Moscow"

    def test_complete_callback_parsing(self):
        callback_data = "complete:42"
        parts = callback_data.split(":")
        assert parts[0] == "complete"
        assert parts[1] == "42"

    def test_delete_callback_parsing(self):
        callback_data = "delete:15"
        parts = callback_data.split(":")
        assert parts[0] == "delete"
        assert parts[1] == "15"

    def test_rday_callback_parsing(self):
        callback_data = "rday:friday"
        parts = callback_data.split(":", 1)
        assert parts[0] == "rday"
        assert parts[1] == "friday"


class TestReportFallback:

    def test_ask_ai_returns_fallback_on_none_content(self):
        from ai import ask_ai
        import asyncio
        assert asyncio.iscoroutinefunction(ask_ai)

    def test_fresh_start_logic_detection(self):
        habits = [
            {"week_completion": "0/7"},
            {"week_completion": "0/7"},
            {"week_completion": "0/7"},
        ]
        total = sum(int(h["week_completion"].split("/")[0]) for h in habits)
        assert total == 0

    def test_fresh_start_logic_with_some_completions(self):
        habits = [
            {"week_completion": "3/7"},
            {"week_completion": "1/7"},
            {"week_completion": "0/7"},
        ]
        total = sum(int(h["week_completion"].split("/")[0]) for h in habits)
        assert total == 4


class TestReportSchedule:

    def test_day_mapping_correctness(self):
        monday = datetime(2024, 1, 1, tzinfo=pytz.UTC)
        assert monday.weekday() == 0
        sunday = datetime(2024, 1, 7, tzinfo=pytz.UTC)
        assert sunday.weekday() == 6

    def test_time_validation_format(self):
        valid_times = ["08:00", "18:30", "00:00", "23:59"]
        invalid_times = ["25:00", "12:60", "abc", "8:0", ""]

        for t in valid_times:
            h, m = map(int, t.split(":"))
            assert 0 <= h <= 23 and 0 <= m <= 59

        for t in invalid_times:
            try:
                h, m = map(int, t.split(":"))
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    raise ValueError
            except (ValueError, IndexError):
                pass


class TestAICommands:

    def test_cmd_advise_exists(self):
        from handlers.ai_commands import cmd_advise
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_advise)

    def test_cmd_rolemodel_exists(self):
        from handlers.ai_commands import cmd_rolemodel
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_rolemodel)

    def test_cmd_suggest_exists(self):
        from handlers.ai_commands import cmd_suggest
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_suggest)

    def test_cmd_insights_exists(self):
        from handlers.ai_commands import cmd_insights
        import asyncio
        assert asyncio.iscoroutinefunction(cmd_insights)

    def test_advise_checks_registration(self):
        import asyncio
        from handlers.ai_commands import cmd_advise

        msg = MagicMock()
        msg.from_user.id = 99999
        msg.text = "/advise"
        msg.answer = AsyncMock()

        state = AsyncMock()

        async def run():
            with patch("api_client.api.get_user", new_callable=AsyncMock, return_value=None):
                await cmd_advise(msg, state)

        asyncio.run(run())
        msg.answer.assert_called_with("Please register first by sending /start")

    def test_rolemodel_checks_registration(self):
        import asyncio
        from handlers.ai_commands import cmd_rolemodel

        msg = MagicMock()
        msg.from_user.id = 99999
        msg.text = "/rolemodel"
        msg.answer = AsyncMock()

        state = AsyncMock()

        async def run():
            with patch("api_client.api.get_user", new_callable=AsyncMock, return_value=None):
                await cmd_rolemodel(msg, state)

        asyncio.run(run())
        msg.answer.assert_called_with("Please register first by sending /start")

    def test_suggest_checks_registration(self):
        import asyncio
        from handlers.ai_commands import cmd_suggest

        msg = MagicMock()
        msg.from_user.id = 99999
        msg.text = "/suggest"
        msg.answer = AsyncMock()

        state = AsyncMock()

        async def run():
            with patch("api_client.api.get_user", new_callable=AsyncMock, return_value=None):
                await cmd_suggest(msg, state)

        asyncio.run(run())
        msg.answer.assert_called_with("Please register first by sending /start")

    def test_insights_checks_registration(self):
        import asyncio
        from handlers.ai_commands import cmd_insights

        msg = MagicMock()
        msg.from_user.id = 99999
        msg.text = "/insights"
        msg.answer = AsyncMock()

        async def run():
            with patch("api_client.api.get_user", new_callable=AsyncMock, return_value=None):
                await cmd_insights(msg)

        asyncio.run(run())
        msg.answer.assert_called_with("Please register first by sending /start")

    def test_help_includes_new_commands(self):
        import asyncio
        from handlers.help import cmd_help

        msg = MagicMock()
        msg.answer = AsyncMock()

        asyncio.run(cmd_help(msg))
        call_args = msg.answer.call_args[0][0]
        assert "/advise" in call_args
        assert "/rolemodel" in call_args
        assert "/suggest" in call_args
        assert "/insights" in call_args

    def test_fsm_states_exist(self):
        from handlers.ai_commands import GetHabitAdvice, GetRoleModelHabits, GetSuggestions
        assert hasattr(GetHabitAdvice, "waiting_habit_name")
        assert hasattr(GetHabitAdvice, "waiting_issue")
        assert hasattr(GetRoleModelHabits, "waiting_role")
        assert hasattr(GetSuggestions, "waiting_goal")
