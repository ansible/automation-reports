import datetime
from datetime import timedelta
from unittest.mock import MagicMock

import pytest
import pytz

from backend.apps.scheduler.models import SyncSchedule


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestScheduler:
    # expired in 2015, so next_run should not be populated
    dead_rrule = "DTSTART;TZID=UTC:20140520T190000 RRULE:FREQ=YEARLY;INTERVAL=1;BYMONTH=1;BYMONTHDAY=1;UNTIL=20150530T000000Z"
    continuing_rrule = "DTSTART;TZID=UTC:20140520T190000 RRULE:FREQ=YEARLY;INTERVAL=1;BYMONTH=1;BYMONTHDAY=1"

    def sync_rule(self, cluster, rrule):
        return SyncSchedule.objects.create(name='example schedule', rrule=rrule, cluster=cluster)

    @property
    def distant_rrule(self):
        # this rule should produce a next_run, but it should not overlap with test run time
        this_year = datetime.datetime.now(pytz.utc).year
        return "DTSTART;TZID=UTC:{}0520T190000 RRULE:FREQ=YEARLY;INTERVAL=1;BYMONTH=1;BYMONTHDAY=1;UNTIL={}0530T000000Z".format(this_year + 1, this_year + 2)

    def test_get_end_date_returns_none_if_no_until_or_count(self):
        schedule = SyncSchedule()
        rule1 = MagicMock(_until=None, _count=None)
        rule2 = MagicMock(_until=None, _count=None)
        schedule._rrule = [rule1, rule2]
        assert schedule.get_end_date() is None

    def test_coerce_naive_until_with_utc_until(self):
        # UNTIL already has Z, should not change
        rrule = "DTSTART;TZID=America/New_York:20200601T120000 RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20200601T220000Z"
        result = SyncSchedule.coerce_naive_until(rrule)
        assert "UNTIL=20200601T220000Z" in result

    def test_coerce_naive_until_no_until(self):
        # No UNTIL present, should return unchanged
        rrule = "DTSTART;TZID=America/New_York:20200601T120000 RRULE:FREQ=HOURLY;INTERVAL=1"
        result = SyncSchedule.coerce_naive_until(rrule)
        assert result == rrule

    def test_coerce_naive_until_europe_ljubljana(self):
        # Ljubljana is UTC+2 in summer (CEST)
        rrule = "DTSTART;TZID=Europe/Ljubljana:20240601T120000 RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20240601T170000"
        result = SyncSchedule.coerce_naive_until(rrule)
        # 17:00 in Ljubljana is 15:00 UTC
        assert "UNTIL=20240601T150000Z" in result

    @pytest.mark.parametrize('freq, delta', (('MINUTELY', 1), ('HOURLY', 1)))
    def test_old_dt_start(self, cluster, freq, delta):
        rrule = f'DTSTART;TZID=Europe/Ljubljana:20150101T000000 RRULE:FREQ={freq};INTERVAL={delta}'  # noqa
        s = self.sync_rule(cluster, rrule)
        first_event = s.rrulestr(s.rrule)[0]
        assert datetime.datetime.now(pytz.timezone("Europe/Ljubljana")) - first_event < timedelta(days=1)

        # the next few scheduled events should be the next minute/hour incremented
        next_five_events = list(s.rrulestr(s.rrule).xafter(datetime.datetime.now(pytz.timezone("Europe/Ljubljana")), count=5))

        assert next_five_events[0] > datetime.datetime.now(pytz.timezone("Europe/Ljubljana"))
        last = None
        for event in next_five_events:
            if last:
                assert event == last + (timedelta(minutes=1) if freq == 'MINUTELY' else timedelta(hours=1))
            last = event

    def test_repeats_forever(self, cluster):
        rrule = 'DTSTART:20300112T210000Z RRULE:FREQ=DAILY;INTERVAL=1'
        s = self.sync_rule(cluster, rrule)
        assert str(s.next_run) == str(s.dtstart) == '2030-01-12 21:00:00+00:00'
        assert s.dtend is None

    def test_no_recurrence_utc(self, cluster):
        rrule = 'DTSTART:20300112T210000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1'
        s = self.sync_rule(cluster, rrule)
        assert str(s.next_run) == str(s.dtstart) == str(s.dtend) == '2030-01-12 21:00:00+00:00'

    def test_no_recurrence_cet(self, cluster):
        rrule = 'DTSTART;TZID=Europe/Ljubljana:20300112T210000 RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1'
        s = self.sync_rule(cluster, rrule)
        assert str(s.next_run) == str(s.dtstart) == str(s.dtend) == '2030-01-12 20:00:00+00:00'

    def test_next_run_utc(self, cluster):
        rrule = 'DTSTART:20300112T210000Z RRULE:FREQ=MONTHLY;INTERVAL=1;BYDAY=SA;BYSETPOS=1;COUNT=4'
        s = self.sync_rule(cluster, rrule)
        assert str(s.next_run) == '2030-02-02 21:00:00+00:00'
        assert str(s.next_run) == str(s.dtstart)
        assert str(s.dtend) == '2030-05-04 21:00:00+00:00'

    def test_next_run_cet(self, cluster):
        rrule = 'DTSTART;TZID=Europe/Ljubljana:20300112T210000 RRULE:FREQ=MONTHLY;INTERVAL=1;BYDAY=SA;BYSETPOS=1;COUNT=4'
        s = self.sync_rule(cluster, rrule)
        assert str(s.next_run) == '2030-02-02 20:00:00+00:00'
        assert str(s.next_run) == str(s.dtstart)

        # March 10, 2030 is when DST takes effect in Ljubljana
        assert str(s.dtend) == '2030-05-04 19:00:00+00:00'

    def test_year_boundary(self, cluster):
        rrule = 'DTSTART;TZID=America/New_York:20301231T230000 RRULE:FREQ=YEARLY;INTERVAL=1;BYMONTH=12;BYMONTHDAY=31;COUNT=4'  # noqa
        s = self.sync_rule(cluster, rrule)

        assert str(s.next_run) == '2031-01-01 04:00:00+00:00'  # UTC = +5 EST
        assert str(s.next_run) == str(s.dtstart)
        assert str(s.dtend) == '2034-01-01 04:00:00+00:00'  # UTC = +5 EST

    def test_leap_year_day(self, cluster):
        rrule = 'DTSTART;TZID=Europe/Ljubljana:20320229T050000 RRULE:FREQ=YEARLY;INTERVAL=1;BYMONTH=02;BYMONTHDAY=29;COUNT=2'  # noqa
        s = self.sync_rule(cluster, rrule)

        assert str(s.next_run) == '2032-02-29 04:00:00+00:00'  # UTC = +1 CET
        assert str(s.next_run) == str(s.dtstart)
        assert str(s.dtend) == '2036-02-29 04:00:00+00:00'  # UTC = +1 CET

    @pytest.mark.parametrize(
        'until, dtend',
        [
            ['20300602T170000Z', '2030-06-02 12:00:00+00:00'],
            ['20300602T000000Z', '2030-06-01 12:00:00+00:00'],
        ],
    )
    def test_utc_until(self, cluster, until, dtend):
        rrule = 'DTSTART:20300601T120000Z RRULE:FREQ=DAILY;INTERVAL=1;UNTIL={}'.format(until)
        s = self.sync_rule(cluster, rrule)

        assert str(s.next_run) == '2030-06-01 12:00:00+00:00'
        assert str(s.next_run) == str(s.dtstart)
        assert str(s.dtend) == dtend

    @pytest.mark.parametrize(
        'rrule, length',
        [
            ['DTSTART:20380601T120000Z RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T170000', 6],  # noon UTC to 5PM UTC (noon, 1pm, 2, 3, 4, 5pm)
            ['DTSTART;TZID=Europe/Ljubljana:20380601T120000 RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T170000', 6],  # noon EST to 5PM EST
        ],
    )
    def test_tzinfo_naive_until(self, cluster, rrule, length):
        s = self.sync_rule(cluster, rrule)
        gen = SyncSchedule.rrulestr(s.rrule).xafter(datetime.datetime.now(pytz.utc), count=20)
        assert len(list(gen)) == length

    def test_utc_until_in_the_past(self, cluster):
        rrule = 'DTSTART:20180601T120000Z RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20150101T100000Z'
        s = self.sync_rule(cluster, rrule)
        s.save()

        assert s.next_run is s.dtstart is s.dtend is None

    def test_beginning_of_time(self, cluster):
        start = datetime.datetime.now(pytz.utc)
        rrule = 'DTSTART:19700101T000000Z RRULE:FREQ=MINUTELY;INTERVAL=1'
        s = self.sync_rule(cluster, rrule)
        assert s.next_run > start
        assert (s.next_run - start).total_seconds() < 60

    def test_utc_naive_coercion(self, cluster):
        rrule = 'DTSTART:20380601T120000Z RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T170000'
        s = self.sync_rule(cluster, rrule)

        assert s.rrule.endswith('20380601T170000Z')
        assert str(s.dtend) == '2038-06-01 17:00:00+00:00'

    def test_cet_naive_coercion(self, cluster):
        rrule = 'DTSTART;TZID=Europe/Ljubljana:20380601T120000 RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T170000'
        s = self.sync_rule(cluster, rrule)
        assert s.rrule.endswith('20380601T160000Z')  # 5PM CET = 4PM UTC
        assert str(s.dtend) == '2038-06-01 16:00:00+00:00'

    # Test coerce_naive_until, this method takes a naive until field and forces it into utc
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        'rrule, expected_result',
        [
            pytest.param(
                'DTSTART:20380601T120000Z RRULE:FREQ=HOURLY;INTERVAL=1',
                'DTSTART:20380601T120000Z RRULE:FREQ=HOURLY;INTERVAL=1',
                id="No untils present",
            ),
            pytest.param(
                'DTSTART:20380601T120000Z RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T170000Z',
                'DTSTART:20380601T120000Z RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T170000Z',
                id="One until already in UTC",
            ),
            pytest.param(
                'DTSTART;TZID=America/New_York:20380601T120000 RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T170000',
                'DTSTART;TZID=America/New_York:20380601T120000 RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T220000Z',
                id="One until with local tz",
            ),
            pytest.param(
                'DTSTART:20380601T120000Z RRULE:FREQ=MINUTLEY;INTERVAL=1;UNTIL=20380601T170000Z EXRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T170000Z',
                'DTSTART:20380601T120000Z RRULE:FREQ=MINUTLEY;INTERVAL=1;UNTIL=20380601T170000Z EXRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T170000Z',
                id="Multiple untils all in UTC",
            ),
            pytest.param(
                'DTSTART;TZID=America/New_York:20380601T120000 RRULE:FREQ=MINUTELY;INTERVAL=1;UNTIL=20380601T170000 EXRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T170000',
                'DTSTART;TZID=America/New_York:20380601T120000 RRULE:FREQ=MINUTELY;INTERVAL=1;UNTIL=20380601T220000Z EXRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T220000Z',
                id="Multiple untils with local tz",
            ),
            pytest.param(
                'DTSTART;TZID=America/New_York:20380601T120000 RRULE:FREQ=MINUTELY;INTERVAL=1;UNTIL=20380601T170000Z EXRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T170000',
                'DTSTART;TZID=America/New_York:20380601T120000 RRULE:FREQ=MINUTELY;INTERVAL=1;UNTIL=20380601T170000Z EXRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20380601T220000Z',
                id="Multiple untils mixed",
            ),
        ],
    )
    def test_coerce_naive_until(self, rrule, expected_result):
        new_rrule = SyncSchedule.coerce_naive_until(rrule)
        assert new_rrule == expected_result

    def test_skip_sundays(self):
        rrule = '''
          DTSTART;TZID=Europe/Ljubljana:20220310T150000
          RRULE:INTERVAL=1;FREQ=DAILY
          EXRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU
        '''
        timezone = pytz.timezone("Europe/Ljubljana")
        friday_apr_29th = datetime.datetime(2022, 4, 29, 0, 0, 0, 0, timezone)
        monday_may_2nd = datetime.datetime(2022, 5, 2, 23, 59, 59, 999, timezone)
        ruleset = SyncSchedule.rrulestr(rrule)
        gen = ruleset.between(friday_apr_29th, monday_may_2nd, True)
        # We should only get Fri, Sat and Mon (skipping Sunday)
        assert len(list(gen)) == 3
        saturday_night = datetime.datetime(2022, 4, 30, 23, 59, 59, 9999, timezone)
        monday_morning = datetime.datetime(2022, 5, 2, 0, 0, 0, 0, timezone)
        gen = ruleset.between(saturday_night, monday_morning, True)
        assert len(list(gen)) == 0

    @pytest.mark.parametrize(
        'rrule, expected_result',
        [
            pytest.param(
                'DTSTART;TZID=Europe/Ljubljana:20210310T150000 RRULE:INTERVAL=1;FREQ=DAILY;UNTIL=20210430T150000Z EXRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU;COUNT=5',
                datetime.datetime(2021, 4, 30, 13, 0, 0, tzinfo=pytz.utc),
                id="Single rule in rule set with UTC TZ aware until",
            ),
            pytest.param(
                'DTSTART;TZID=Europe/Ljubljana:20220310T150000 RRULE:INTERVAL=1;FREQ=DAILY;UNTIL=20220430T150000 EXRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU;COUNT=5',
                datetime.datetime(2022, 4, 30, 13, 0, tzinfo=pytz.utc),
                id="Single rule in ruleset with naive until",
            ),
            pytest.param(
                'DTSTART;TZID=Europe/Ljubljana:20220310T150000 RRULE:INTERVAL=1;FREQ=DAILY;COUNT=4 EXRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU;COUNT=5',
                datetime.datetime(2022, 3, 12, 14, 0, tzinfo=pytz.utc),
                id="Single rule in ruleset with count",
            ),
            pytest.param(
                'DTSTART;TZID=Europe/Ljubljana:20220310T150000 RRULE:INTERVAL=1;FREQ=DAILY EXRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU;COUNT=5',
                None,
                id="Single rule in ruleset with no end",
            ),
            pytest.param(
                'DTSTART;TZID=Europe/Ljubljana:20220310T150000 RRULE:INTERVAL=1;FREQ=DAILY',
                None,
                id="Single rule in rule with no end",
            ),
            pytest.param(
                'DTSTART;TZID=Europe/Ljubljana:20220310T150000 RRULE:INTERVAL=1;FREQ=DAILY;UNTIL=20220430T150000Z',
                datetime.datetime(2022, 4, 30, 13, 0, tzinfo=pytz.utc),
                id="Single rule in rule with UTZ TZ aware until",
            ),
            pytest.param(
                'DTSTART;TZID=Europe/Ljubljana:20220310T150000 RRULE:INTERVAL=1;FREQ=DAILY;UNTIL=20220430T150000',
                datetime.datetime(2022, 4, 30, 13, 0, tzinfo=pytz.utc),
                id="Single rule in rule with naive until",
            ),
            pytest.param(
                'DTSTART;TZID=Europe/Ljubljana:20220310T150000 RRULE:INTERVAL=1;FREQ=DAILY;BYDAY=SU RRULE:INTERVAL=1;FREQ=DAILY;BYDAY=MO',
                None,
                id="Multi rule with no end",
            ),
            pytest.param(
                'DTSTART;TZID=Europe/Ljubljana:20220310T150000 RRULE:INTERVAL=1;FREQ=DAILY;BYDAY=SU RRULE:INTERVAL=1;FREQ=DAILY;BYDAY=MO;COUNT=4',
                None,
                id="Multi rule one with no end and one with an count",
            ),
            pytest.param(
                'DTSTART;TZID=Europe/Ljubljana:20220310T150000 RRULE:INTERVAL=1;FREQ=DAILY;BYDAY=SU;UNTIL=20220430T1500Z RRULE:INTERVAL=1;FREQ=DAILY;BYDAY=MO;COUNT=4',
                datetime.datetime(2022, 4, 24, 13, 0, tzinfo=pytz.utc),
                id="Multi rule one with until and one with an count",
            ),
            pytest.param(
                'DTSTART;TZID=Europe/Ljubljana:20010430T1500 RRULE:INTERVAL=1;FREQ=DAILY;BYDAY=SU;COUNT=1',
                datetime.datetime(2001, 5, 6, 13, 0, tzinfo=pytz.utc),
                id="Rule with count but ends in the past",
            ),
            pytest.param(
                'DTSTART;TZID=Europe/Ljubljana:20220430T1500 RRULE:INTERVAL=1;FREQ=DAILY;BYDAY=SU;UNTIL=20010430T1500',
                None,
                id="Rule with until that ends in the past",
            ),
        ],
    )
    def test_get_end_date(self, rrule, expected_result):
        ruleset = SyncSchedule.rrulestr(rrule)
        assert expected_result == SyncSchedule.get_end_date(ruleset)

    def test_disabled_sync_schedule(self, cluster):
        schedule = SyncSchedule.objects.create(
            name="Disabled Schedule",
            enabled=False,
            rrule="DTSTART;TZID=UTC:20240101T000000 RRULE:FREQ=MINUTELY;INTERVAL=1;COUNT=1",
            cluster=cluster,
        )
        schedule.update_computed_fields()
        assert schedule.next_run is None
