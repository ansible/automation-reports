import base64
import pytest
import responses

from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.models import ClusterVersionChoices, Cluster
from backend.apps.clusters.encryption import Fernet256, encrypt_value, get_encryption_key

from .fixtures import all_aap_versions
from .fixtures import cluster_26, dict_cluster_26, aap_api_responses_26
from .fixtures import cluster_25, dict_cluster_25, aap_api_responses_25
from .fixtures import cluster_24, dict_cluster_24, aap_api_responses_24
from .fixtures.aap_common import cluster_from_dict_cluster, load_file, dict_cluster_versioned
from responses import matchers


# How to "combine" smaller fixtures - syntax suygar
# https://smarie.github.io/python-pytest-cases/pytest_goodies/#unpack_fixture-unpack_into


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestAAPTokenrefresh:
    @pytest.mark.parametrize("aap_version", all_aap_versions)
    def test_get(self, aap_version):
        aap_version_slug = aap_version.replace(".", "")
        dict_cluster = dict_cluster_versioned(aap_version_slug)
        cluster_from_dict_cluster(dict_cluster)

        key = get_encryption_key()
        f = Fernet256(key)

        ping_filename = f"ping-{aap_version_slug}.json"
        responses.add(load_file(f"tests/mock_aap/fixtures/aap_{aap_version_slug}/{ping_filename}"))
        if aap_version_slug == "24":
            # for v2.4 the v2.5/2.6 ping URL is also needed.
            responses.add(load_file(f"tests/mock_aap/fixtures/aap_24/ping-25.json"))
        access_token_1 = dict_cluster["access_token"]
        refresh_token_1 = dict_cluster["refresh_token"]
        access_token_2 = access_token_1 + "-2"
        refresh_token_2 = refresh_token_1 + "-2"
        client_id = f"client-id-{aap_version_slug}"
        client_secret = f"client-secret-{aap_version_slug}"
        #
        basic_auth_client_id_secret = base64.b64encode(bytes(f"{client_id}:{client_secret}", "UTF-8")).decode("utf-8")
        if aap_version_slug == "24":
            expected_org_ids = [1, 2]
            aap_port = 8443
            endpoint = "/api/v2/organizations/?page_size=100&page=1"
            url_token = f"https://aap{aap_version_slug}.example.com:8443/api/o/token/"
        elif aap_version_slug == "25":
            expected_org_ids = [1, 2]
            aap_port = 443
            endpoint = "/api/controller/v2/organizations/?page_size=100&page=1"
            url_token = f"https://aap{aap_version_slug}.example.com:443/o/token/"
        elif aap_version_slug == "26":
            expected_org_ids = [1, 8]
            aap_port = 443
            endpoint = "/api/controller/v2/organizations/?page_size=100&page=1"
            url_token = f"https://aap{aap_version_slug}.example.com:443/o/token/"

        url_organizations = f"https://aap{aap_version_slug}.example.com:{aap_port}" + endpoint

        responses.add(load_file(
            f"tests/mock_aap/fixtures/aap_{aap_version_slug}/organizations.json",
            match=[
                matchers.header_matcher({
                    "Authorization": f"Bearer {access_token_1}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    }),
            ],
        ))

        cluster = Cluster.objects.get(address=f"aap{aap_version_slug}.example.com")
        cluster.access_token = encrypt_value(access_token_1)
        cluster.save()
        apiconn = ApiConnector(cluster)

        # the apiconn.access_token is set by .check_aap_version
        apiconn.check_aap_version() 
        assert apiconn.access_token == f"access-token-{aap_version_slug}"
        assert f.decrypt(cluster.access_token) == f"access-token-{aap_version_slug}".encode("utf-8")
        assert f.decrypt(cluster.refresh_token) == f"refresh-token-{aap_version_slug}".encode("utf-8")

        # a valid access token just works
        response = apiconn.execute_get(endpoint)

        for results in response:
            for result in results:
                assert result["id"] in expected_org_ids
        assert responses.assert_call_count(url_token, 0)
        assert responses.assert_call_count(url_organizations, 1) 
        assert apiconn.access_token == access_token_1
        assert f.decrypt(cluster.access_token).decode("utf-8") == access_token_1
        assert f.decrypt(cluster.refresh_token).decode("utf-8") == refresh_token_1

        # ====================================================================================
        # access token expired
        responses.replace(load_file(
            f"tests/mock_aap/fixtures/aap_{aap_version_slug}_organizations-401.json",
            match=[
                matchers.header_matcher({
                    "Authorization": f"Bearer {access_token_1}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    }),
            ],
        ))
        responses.add(load_file(
            f"tests/mock_aap/fixtures/aap_{aap_version_slug}/organizations.json",
            match=[
                matchers.header_matcher({
                    "Authorization": f"Bearer {access_token_2}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    }),
            ],
        ))
        responses.add(load_file(
            f"tests/mock_aap/fixtures/aap_{aap_version_slug}/token-refresh.json",
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
        assert responses.assert_call_count(url_token, 1)
        assert responses.assert_call_count(url_organizations, 3)
        assert apiconn.access_token == access_token_2
        assert f.decrypt(cluster.access_token).decode("utf-8") == access_token_2
        assert f.decrypt(cluster.refresh_token).decode("utf-8") == refresh_token_2
