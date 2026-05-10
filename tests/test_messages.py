"""Tests for the pet message system."""

import pytest
from src.core.messages import MessageProvider, get_message, load_custom_messages
import src.core.messages as messages_mod
from src.core.timer import TimerPhase


class TestMessageProvider:
    """Test message selection based on timer phase."""

    def test_work_messages_exist(self):
        """Work phase has at least one message."""
        messages = MessageProvider.get_messages(TimerPhase.WORK)
        assert len(messages) > 0

    def test_break_messages_exist(self):
        """Break phase has at least one message."""
        messages = MessageProvider.get_messages(TimerPhase.BREAK)
        assert len(messages) > 0

    def test_get_message_returns_string(self):
        """get_message returns a non-empty string."""
        msg = get_message(TimerPhase.WORK)
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_get_message_break_phase(self):
        """get_message works for break phase."""
        msg = get_message(TimerPhase.BREAK)
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_messages_are_different_types_for_phases(self):
        """Work and break messages are distinct sets."""
        work_msgs = MessageProvider.get_messages(TimerPhase.WORK)
        break_msgs = MessageProvider.get_messages(TimerPhase.BREAK)
        # At least some messages should differ
        assert set(work_msgs) != set(break_msgs)

    def test_custom_messages_override(self):
        """Custom messages can be provided."""
        custom = ["Go go go!", "Stay focused!"]
        msg = MessageProvider.get_message_with_custom(TimerPhase.WORK, custom)
        assert msg in custom


class TestCustomMessagesFile:
    def setup_method(self):
        """Reset custom messages before each test."""
        messages_mod._custom_messages = None

    def teardown_method(self):
        messages_mod._custom_messages = None

    def test_load_from_file(self, tmp_path):
        f = tmp_path / "msgs.txt"
        f.write_text("Keep going!\nYou rock!\nAlmost there!\n")
        load_custom_messages(str(f))
        assert messages_mod._custom_messages == ["Keep going!", "You rock!", "Almost there!"]

    def test_custom_messages_used_by_provider(self, tmp_path):
        f = tmp_path / "msgs.txt"
        f.write_text("Custom one\nCustom two\n")
        load_custom_messages(str(f))
        msgs = MessageProvider.get_messages(TimerPhase.WORK)
        assert msgs == ["Custom one", "Custom two"]

    def test_missing_file_ignored(self):
        load_custom_messages("/nonexistent/path.txt")
        assert messages_mod._custom_messages is None

    def test_empty_file_ignored(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        load_custom_messages(str(f))
        assert messages_mod._custom_messages is None
