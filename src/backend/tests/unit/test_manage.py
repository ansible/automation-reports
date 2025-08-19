import pytest

from django.core.management import call_command
from django.test import TestCase


class TestUpdatePassword(TestCase):
    @pytest.fixture(autouse=True)
    def mycapsys(self, capsys):
        self._capsys = capsys

    def test_mycommand(self):
        username = "testuser"
        call_command("createsuperuser", "--no-input", username=username, email="testuser@example.com")
        call_command("update_password", username="testuser", password="testpass")
        outlines = self._capsys.readouterr().out.splitlines()
        assert outlines[0] == "Superuser created successfully."
        assert outlines[1] == f"Password updated for user {username}."
