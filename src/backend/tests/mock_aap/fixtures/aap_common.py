import pytest
import responses
import yaml

all_aap_versions = [
    "2.6",
    "2.5",
    "2.4",
    ]

dict_sync_schedule_1min = dict(
    name="Every 1 minute sync",
    rrule="DTSTART;TZID=Europe/Ljubljana:20250630T070000 FREQ=MINUTELY;INTERVAL=1",
    enabled=True,
)
