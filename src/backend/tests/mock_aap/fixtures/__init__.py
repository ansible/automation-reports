from .aap_common import all_aap_versions, dict_sync_schedule_1min, dict_sync_schedule_10sec
from .aap_api_26 import dict_cluster_26, cluster_26, aap_api_responses_26
from .aap_api_25 import dict_cluster_25, cluster_25, aap_api_responses_25
from .aap_api_24 import dict_cluster_24, cluster_24, aap_api_responses_24


__all__ = [
    all_aap_versions,
    dict_sync_schedule_1min,
    dict_sync_schedule_10sec,

    dict_cluster_26,
    cluster_26,
    aap_api_responses_26,

    dict_cluster_25,
    cluster_25,
    aap_api_responses_25,

    dict_cluster_24,
    cluster_24,
    aap_api_responses_24,
]
