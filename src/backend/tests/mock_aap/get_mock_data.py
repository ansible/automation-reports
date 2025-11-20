#!/usr/bin/env python3

# The script run HTTP GET requests to AAP, to predefined API endpoints.
# The responeses are stored into json files for mock testing.
# Before running this script the AAP needs to be:
#  - reset to "empty" state
#  - filled with predefined objects (projects, job templates, jobs, etc)
#    - use setup_aap.py for this

# Required input, as environ variables:
#   export AAP_URL="https://10.44.17.65:443"
#   export AAP_USERNAME=admin
#   export AAP_PASSWORD=...
# Run:
#   ./get_mock_data.py

import logging
from collections import namedtuple
import requests
import os
import json

from setup_aap import AAP, jobs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

requests.packages.urllib3.disable_warnings(category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

RequestSpec = namedtuple('RequestSpec', ['filename', 'url'])

OUT_DIR="fixtures/aap_26"
MOCK_AAP_URL="https://aap26.example.com:443"

job_ids = [spec.expected["id"] for spec in jobs]

ReqSpecs = [
    RequestSpec("ping.json", "/api/gateway/v1/ping/"),
    RequestSpec("jobs-1.json", "/api/controller/v2/jobs/?page_size=100&page=1&order_by=finished&finished__gt=2025-08-08T00:00:00Z"),
    #RequestSpec("jobs-2.json", "/api/controller/v2/jobs/?page_size=100&page=1&order_by=finished&finished__gt=2025-10-23T13:01:09.768681Z"),
    RequestSpec("job_templates.json", "/api/controller/v2/job_templates/?page_size=200&page=1"),
    RequestSpec("organizations.json", "/api/controller/v2/organizations/?page_size=100&page=1"),
] + [
    RequestSpec(f"jobs_{job_id}_job_host_summaries.json", f"/api/controller/v2/jobs/{job_id}/job_host_summaries?page_size=100&page=1&order_by=modified")
    for job_id in job_ids
]


def get_req(aap: AAP, req_spec: RequestSpec):
    headers = {"Authorization": f"Bearer {aap.access_token}"}
    url = aap.base_url + req_spec.url
    mock_url = MOCK_AAP_URL + req_spec.url
    logger.info(f"Url: {url}")
    resp = requests.get(url, headers=headers, verify=False)
    headers={}
    if "X-Api-Product-Name" in resp.headers:
        headers.update({"X-Api-Product-Name": resp.headers["X-Api-Product-Name"]})
    data = dict(
        url=mock_url,
        status=resp.status_code,
        headers=headers,
        json_body=resp.json(),
    )
    filename = os.path.join(OUT_DIR, req_spec.filename)
    with open(filename, "w") as fout:
        json.dump(data, fout, indent=2)


def main():
    aap = AAP.get_instance()
    aap.login()
    aap.create_access_token("get-mock-data-token", "read")
    
    for req_spec in ReqSpecs:
        get_req(aap, req_spec)


if __name__ == "__main__":
    main()
