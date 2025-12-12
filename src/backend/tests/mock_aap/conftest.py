import pytest

from .fixtures.aap_common import all_aap_versions, all_aap_versions_slug

from .fixtures.aap_api_26 import dict_cluster_26, cluster_26, aap_api_responses_26
from .fixtures.aap_api_25 import dict_cluster_25, cluster_25, aap_api_responses_25
from .fixtures.aap_api_24 import dict_cluster_24, cluster_24, aap_api_responses_24


@pytest.fixture
def aap_api_responses(request):
    for version_slug in all_aap_versions_slug:
        request.getfixturevalue("aap_api_responses_" + version_slug)
