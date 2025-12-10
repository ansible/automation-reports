import responses
import json
import os

from backend.apps.clusters.encryption import encrypt_value
from backend.apps.clusters.models import Cluster

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


def cluster_from_dict_cluster(dict_cluster):
    """Creates temporary data."""
    Cluster.objects.create(
        protocol=dict_cluster["protocol"],
        address=dict_cluster["address"],
        port=dict_cluster["port"],
        access_token=encrypt_value(dict_cluster["access_token"].encode("utf-8")),
        refresh_token=encrypt_value(dict_cluster["refresh_token"].encode("utf-8")),
        client_id=dict_cluster["client_id"],
        client_secret=encrypt_value(dict_cluster["client_secret"].encode("utf-8")),
        verify_ssl=dict_cluster["verify_ssl"],
    )


def load_file(filepath: str, match=[]):
    with open(filepath, "r") as fin:
        data = json.load(fin)
    if "json_body" in data:
        body_kwargs = dict(json=data["json_body"])
    else:
        body_kwargs = dict(body=data["body"])

    resp = responses.Response(
        method=data.get("method", responses.GET),
        url=data["url"],
        status=data["status"],
        # json=data["json_body"], TODO
        # body=data["body"], TODO
        # content_type='application/json',
        **body_kwargs,
        headers=data["headers"],
        match=match,
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
