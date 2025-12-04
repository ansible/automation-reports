import responses
import json
import os

all_aap_versions = [
    "2.6",
    "2.5",
    "2.4",
]

all_aap_versions_slug = [
    vv.replace(".", "")
    for vv in all_aap_versions
]

# out_dir = "tests/mock_aap/fixtures/aap_26"
out_dir_template = "tests/mock_aap/fixtures/aap_{version}"


dict_sync_schedule_1min = dict(
    name="Every 1 minute sync",
    rrule="DTSTART;TZID=Europe/Ljubljana:20250630T070000 FREQ=MINUTELY;INTERVAL=1",
    enabled=True,
)


def load_file(filepath: str):
    with open(filepath, "r") as fin:
        data = json.load(fin)
    resp = responses.Response(
        method=responses.GET,
        url=data["url"],
        status=data["status"],
        json=data["json_body"],
        content_type='application/json',
        headers=data["headers"],
    )
    return resp


def aap_api_responses_versioned(version: str):
    assert version in ["24", "25", "26"]
    out_dir = out_dir_template.format(version=version)

    for filename in os.listdir(out_dir):
        if filename in ['.', '..']:
            continue
        filepath = os.path.join(out_dir, filename)
        resp = load_file(filepath)
        responses.add(resp)
