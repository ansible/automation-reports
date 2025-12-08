import base64
import pytest
import responses

from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.models import ClusterVersionChoices, Cluster
from backend.apps.clusters.encryption import Fernet256, encrypt_value, get_encryption_key

from .fixtures import all_aap_versions
from .fixtures import cluster_26, aap_api_responses_26
from .fixtures import cluster_25, aap_api_responses_25
from .fixtures import cluster_24, aap_api_responses_24



# @pytest.fixture
# def aap_api_responses_26():
#     responses.add(
#         responses.GET,
#         "https://aap26.example.com:443/api/gateway/v1/ping/",
#         json={"status":"good","version":"2.6","pong":"2025-11-19 08:19:48.890695","db_connected":True,"proxy_connected":True},
#         status=200,
#         content_type='application/json'
#     )


# @pytest.fixture
# def aap_api_responses_25():
#     responses.add(
#         responses.GET,
#         "https://aap25.example.com:443/api/gateway/v1/ping/",
#         json={"version":"2.5","pong":"2025-11-19 09:38:32.398165","status":"good","db_connected":True,"proxy_connected":True},
#         status=200,
#         content_type='application/json'
#     )


# @pytest.fixture
# def aap_api_responses_24():
#     responses.add(
#         responses.GET,
#         "https://aap24.example.com:8443/api/gateway/v1/ping/",
#         json={"detail":"The requested resource could not be found."},
#         status=404,
#         content_type='application/json'
#     )
#     responses.add(
#         responses.GET,
#         "https://aap24.example.com:8443/api/v2/ping/",
#         json={"ha":False,"version":"4.5.15","active_node":"rh-savings-aap24.novalocal","install_uuid":"4994da8f-a38f-4610-a6c3-ef410cbd2e2e","instances":[{"node":"rh-savings-aap24.novalocal","node_type":"hybrid","uuid":"eba627ff-78dd-4aaa-8b46-6e539880b808","heartbeat":"2025-11-19T09:40:51.214112Z","capacity":136,"version":"4.5.15"}],"instance_groups":[{"name":"controlplane","capacity":136,"instances":["rh-savings-aap24.novalocal"]},{"name":"default","capacity":136,"instances":["rh-savings-aap24.novalocal"]}]},
#         status=200,
#         content_type='application/json'
#     )


# How to "combine" smaller fixtures - syntax suygar
# https://smarie.github.io/python-pytest-cases/pytest_goodies/#unpack_fixture-unpack_into

from .fixtures.aap_common import cluster_from_dict_cluster, load_file
import json
def token_request_callback(request):
    # payload = json.loads(request.body)
    # resp_body = {"value": sum(payload["numbers"])}
    # headers = {"request-id": "728d329e-0e86-11e4-a748-0c84dc037c13"}
    # return (200, headers, json.dumps(resp_body))

    access_token = "aa"
    refresh_token = "rr"
    payload = json.loads(request.body)
    print(f"TTRT token_request_callback payload={payload}")
    if payload["refresh_token"]:
        pass
    11/0

    token_refresh, data = load_file("tests/mock_aap/fixtures/aap_26/token-refresh.json")
    resp_body = data["json_body"]
    headers = {}
    return (201, headers, json.dumps(resp_body))

from responses import matchers
from .fixtures.aap_api_26 import dict_cluster_26
from .fixtures.aap_api_25 import dict_cluster_25
from .fixtures.aap_api_24 import dict_cluster_24

@pytest.mark.django_db(transaction=True, reset_sequences=True)
# @pytest.mark.usefixtures("cluster_26")
# @pytest.mark.parametrize("load_cluster", all_aap_versions, indirect=True)
class TestAAPTokenrefreshV26:

    @pytest.mark.parametrize("aap_version", all_aap_versions)
    def test_get(self, aap_version):
        aap_version_slug = aap_version.replace(".", "")
        dict_cluster = eval("dict_cluster_" + aap_version_slug)
        cluster_from_dict_cluster(dict_cluster)

        key = get_encryption_key()
        f = Fernet256(key)

        responses.add(load_file("tests/mock_aap/fixtures/aap_26/ping.json"))
        access_token_1 = dict_cluster_26["access_token"]
        refresh_token_1 = dict_cluster_26["refresh_token"]
        access_token_2 = access_token_1 + "-2"
        refresh_token_2 = refresh_token_1 + "-2"
        client_id = "client-id-26"
        client_secret = "client-secret-26"
        expected_org_ids = [1, 8]
        #
        basic_auth_client_id_secret = base64.b64encode(bytes(f"{client_id}:{client_secret}", 'UTF-8')).decode("utf-8")

        responses.add(load_file(
            "tests/mock_aap/fixtures/aap_26/organizations.json",
            match=[
                matchers.header_matcher({
                    "Authorization": f"Bearer {access_token_1}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    }),
            ],
        ))

        cluster = Cluster.objects.get(address="aap26.example.com")
        cluster.access_token = encrypt_value(access_token_1)
        cluster.save()
        apiconn = ApiConnector(cluster)
        endpoint = '/api/controller/v2/organizations/?page_size=100&page=1'

        # the access_token is set by .check_aap_version
        apiconn.check_aap_version() 
        assert apiconn.access_token == "access-token-26"
        assert f.decrypt(cluster.access_token) == b"access-token-26"
        assert f.decrypt(cluster.refresh_token) == b"refresh-token-26"

        # a valid access token just works
        response = apiconn.execute_get(endpoint)

        for results in response:
            for result in results:
                assert result["id"] in expected_org_ids
        assert responses.assert_call_count("https://aap26.example.com:443/o/token/", 0)
        assert responses.assert_call_count("https://aap26.example.com:443/api/controller/v2/organizations/?page_size=100&page=1", 1)
        assert apiconn.access_token == access_token_1
        assert f.decrypt(cluster.access_token).decode('utf-8') == access_token_1
        assert f.decrypt(cluster.refresh_token).decode('utf-8') == refresh_token_1

        # ====================================================================================
        # access token expired
        responses.replace(load_file(
            "tests/mock_aap/fixtures/aap_26_organizations-401.json",
            match=[
                matchers.header_matcher({
                    "Authorization": f"Bearer {access_token_1}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    }),
            ],
        ))
        responses.add(load_file(
            "tests/mock_aap/fixtures/aap_26/organizations.json",
            match=[
                matchers.header_matcher({
                    "Authorization": f"Bearer {access_token_2}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    }),
            ],
        ))
        responses.add(load_file(
            "tests/mock_aap/fixtures/aap_26/token-refresh.json",
            match=[
                matchers.urlencoded_params_matcher({
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token_1,
                    }),
                matchers.header_matcher({
                    "Authorization": f"Basic {basic_auth_client_id_secret}",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    }),
            ],
        ))

        # an invalid access token requires refresh
        response = apiconn.execute_get(endpoint)

        for results in response:
            for result in results:
                assert result["id"] in expected_org_ids
        assert responses.assert_call_count("https://aap26.example.com:443/o/token/", 1)
        assert responses.assert_call_count("https://aap26.example.com:443/api/controller/v2/organizations/?page_size=100&page=1", 3)
        assert apiconn.access_token == access_token_2
        assert f.decrypt(cluster.access_token).decode('utf-8') == access_token_2
        assert f.decrypt(cluster.refresh_token).decode('utf-8') == refresh_token_2


# @pytest.fixture
# def aap_fixtures(request):
#     aap_version_str = request.param
#     aap_version_str_short = aap_version_str.replace(".", "")
#     assert aap_version_str in all_aap_versions

#     cluster = request.getfixturevalue("cluster_" + aap_version_str_short)
#     api_reponses = request.getfixturevalue("aap_api_responses_" + aap_version_str_short)
#     return aap_version_str, cluster, api_reponses


# @pytest.mark.parametrize("aap_fixtures", all_aap_versions, indirect=True)
# @pytest.mark.django_db(transaction=True, reset_sequences=True)
# class TestApiConnector:
#     def test_detect_aap_version(self, aap_fixtures):
#         # aap_version_str, cluster, api_reponses = aap_fixtures
#         aap_version_str = aap_fixtures[0]
#         expected_aap_version = "AAP " + aap_version_str
#         address = "aap" + aap_version_str.replace(".", "") + ".example.com"

#         cluster = Cluster.objects.get(address=address)
#         apiconn = ApiConnector(cluster)
#         aap_version = apiconn.detect_aap_version()
#         assert aap_version in ClusterVersionChoices.values
#         assert aap_version == expected_aap_version
