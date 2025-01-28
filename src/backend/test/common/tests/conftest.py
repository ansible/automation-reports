import datetime
from unittest.mock import patch,MagicMock
import pytest

FAKE_NOW = datetime.datetime(2025, 10, 21, 22, 22, 22)

@pytest.fixture()
def patch_datetime_now(monkeypatch):
    #with patch("datetime.datetime") as mock_datetime:
    print_date_mock = MagicMock(wraps=datetime.datetime)
    print_date_mock.now.return_value = FAKE_NOW
    monkeypatch.setattr(datetime, "datetime", print_date_mock)
