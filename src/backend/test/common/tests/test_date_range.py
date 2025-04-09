#! /usr/bin/env python
# -*- coding: utf-8 -*-
from django.test import TestCase
from freezegun import freeze_time

from backend.apps.clusters.models import DateRangeChoices


@freeze_time("2025-10-21 22:01:45", tz_offset=0)
class TestDateRange(TestCase):

    def test_last_year(self) -> None:
        result = DateRangeChoices.get_date_range(DateRangeChoices.LAST_YEAR).iso_format
        assert result["start"] == "2024-01-01T00:00:00Z"
        assert result["end"] == "2024-12-31T23:59:59.999999Z"

    def test_last_6_month(self) -> None:
        result = DateRangeChoices.get_date_range(DateRangeChoices.LAST_6_MONTH).iso_format
        assert result["start"] == "2025-04-01T00:00:00Z"
        assert result["end"] == "2025-09-30T23:59:59.999999Z"

    def test_last_3_month(self) -> None:
        result = DateRangeChoices.get_date_range(DateRangeChoices.LAST_3_MONTH).iso_format
        assert result["start"] == "2025-07-01T00:00:00Z"
        assert result["end"] == "2025-09-30T23:59:59.999999Z"

    def test_last_month(self) -> None:
        result = DateRangeChoices.get_date_range(DateRangeChoices.LAST_MONTH).iso_format
        assert result["start"] == "2025-09-01T00:00:00Z"
        assert result["end"] == "2025-09-30T23:59:59.999999Z"

    def test_year_to_date(self) -> None:
        result = DateRangeChoices.get_date_range(DateRangeChoices.YEAR_TO_DATE).iso_format
        assert result["start"] == "2025-01-01T00:00:00Z"
        assert result["end"] == "2025-10-21T23:59:59.999999Z"

    def test_quarter_to_date(self) -> None:
        result = DateRangeChoices.get_date_range(DateRangeChoices.QUARTER_TO_DATE).iso_format
        assert result["start"] == "2025-10-01T00:00:00Z"
        assert result["end"] == "2025-10-21T23:59:59.999999Z"

    def test_month_to_date(self) -> None:
        result = DateRangeChoices.get_date_range(DateRangeChoices.MONTH_TO_DATE).iso_format
        assert result["start"] == "2025-10-01T00:00:00Z"
        assert result["end"] == "2025-10-21T23:59:59.999999Z"

    def test_last_3_years(self) -> None:
        result = DateRangeChoices.get_date_range(DateRangeChoices.LAST_3_YEARS).iso_format
        assert result["start"] == "2022-01-01T00:00:00Z"
        assert result["end"] == "2024-12-31T23:59:59.999999Z"

    def test_last_2_years(self) -> None:
        result = DateRangeChoices.get_date_range(DateRangeChoices.LAST_2_YEARS).iso_format
        assert result["start"] == "2023-01-01T00:00:00Z"
        assert result["end"] == "2024-12-31T23:59:59.999999Z"

    def test_custom_date_range(self) -> None:
        result = DateRangeChoices.get_date_range(DateRangeChoices.CUSTOM, '2021-05-14', '2023-10-31').iso_format
        assert result["start"] == "2021-05-14T00:00:00Z"
        assert result["end"] == "2023-10-31T23:59:59.999999Z"

    @freeze_time("2025-12-31 22:01:45", tz_offset=0)
    def test_quarter_to_date_whole_quarter(self) -> None:
        result = DateRangeChoices.get_date_range(DateRangeChoices.QUARTER_TO_DATE).iso_format
        assert result["start"] == "2025-10-01T00:00:00Z"
        assert result["end"] == "2025-12-31T23:59:59.999999Z"

    @freeze_time("2025-01-31 22:01:45", tz_offset=0)
    def test_quarter_to_date_first_quarter(self) -> None:
        result = DateRangeChoices.get_date_range(DateRangeChoices.QUARTER_TO_DATE).iso_format
        assert result["start"] == "2025-01-01T00:00:00Z"
        assert result["end"] == "2025-01-31T23:59:59.999999Z"
