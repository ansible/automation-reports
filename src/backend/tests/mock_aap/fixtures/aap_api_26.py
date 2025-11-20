import pytest
import responses
import json
import os

from backend.apps.clusters.models import Cluster
from backend.apps.clusters.encryption import encrypt_value


dict_cluster_26 = dict(
    protocol="https",
    address="aap26.example.com",
    port=443,
    access_token="access-token-26",
    refresh_token="refresh-token-26",
    client_id="client-id-26",
    client_secret="client-secret-26",
    verify_ssl=True,
)


@pytest.fixture
def cluster_26():
    """Creates temporary data."""
    Cluster.objects.create(
        protocol="https",
        address="aap26.example.com",
        port=443,
        access_token=encrypt_value(b"access-token-26"),
        refresh_token=encrypt_value(b"refresh-token-26"),
        client_id="client-id-26",
        client_secret=encrypt_value(b"client-secret-26"),
        verify_ssl=True,
    )

# curl -k https://10.44.17.65:443/api/controller/v2/job_templates/ -H "Authorization: Bearer $TOKEN" -v
# 

out_dir="tests/mock_aap/fixtures/aap_26"


def load_file(filename: str):
    filename = os.path.join(out_dir, filename)
    with open(filename, "r") as fin:
        data = json.load(fin)
    resp = responses.Response(
        method=responses.GET,
        url=data["url"],
        json=data["json_body"],
        content_type='application/json',
        headers=data["headers"],
    )
    return resp


@pytest.fixture
def aap_api_responses_26():
    # responses.add(
    #     responses.GET,
    #     "https://aap26.example.com:443/api/gateway/v1/ping/",
    #     json={"status":"good","version":"2.6","pong":"2025-11-19 08:19:48.890695","db_connected":True,"proxy_connected":True},
    #     # json=load_file("ping.json")["json_body"],
    #     status=200,
    #     content_type='application/json',
    # )

    for filename in os.listdir(out_dir):
        if filename in ['.', '..']:
            continue
        resp = load_file(filename)
        responses.add(resp)

