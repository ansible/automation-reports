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


# RequestSpec = namedtuple('RequestSpec', ['filename', 'url'])
class RequestSpec:
    def __init__(self, filename: str, url: str, valid_status_codes=[200]):
        self.filename = filename
        self.url = url
        self.valid_status_codes = valid_status_codes


job_ids = [spec.expected["id"] for spec in jobs]

req_specs_26_only = [
    RequestSpec("ping-26.json", "/api/gateway/v1/ping/", ),
    RequestSpec("ping-24.json", "/api/v2/ping/", [404]),
]
req_specs_25_only = [
    RequestSpec("ping-25.json", "/api/gateway/v1/ping/", ),
    RequestSpec("ping-24.json", "/api/v2/ping/", [404]),
]
req_specs_24_only = [
    RequestSpec("ping-25.json", "/api/gateway/v1/ping/", [404]),
    RequestSpec("ping-24.json", "/api/v2/ping/"),
]
# for AAP 2.4, we replace "/api/controller/v2" with ""/api/v2"
req_specs_any_version = [
    RequestSpec("jobs-1.json", "/api/controller/v2/jobs/?page_size=100&page=1&order_by=finished&finished__gt=2025-08-08T00:00:00Z"),
    #RequestSpec("jobs-2.json", "/api/controller/v2/jobs/?page_size=100&page=1&order_by=finished&finished__gt=2025-10-23T13:01:09.768681Z"),
    RequestSpec("job_templates.json", "/api/controller/v2/job_templates/?page_size=200&page=1"),
    RequestSpec("organizations.json", "/api/controller/v2/organizations/?page_size=100&page=1"),
] + [
    RequestSpec(f"jobs_{job_id}_job_host_summaries.json", f"/api/controller/v2/jobs/{job_id}/job_host_summaries?page_size=100&page=1&order_by=modified")
    for job_id in job_ids
]

req_specs_26 = req_specs_26_only + req_specs_any_version
req_specs_25 = req_specs_25_only + req_specs_any_version
req_specs_24 = req_specs_24_only + req_specs_any_version


def get_req(aap: AAP, req_spec: RequestSpec):
    def copy_header_if_present(header_name):
        if header_name in resp.headers:
            headers.update({header_name: resp.headers[header_name]})

    OUT_DIR = f"fixtures/aap_{aap.version}"
    mock_port = "8443" if aap.version == "24" else "443"
    MOCK_AAP_URL = f"https://aap{aap.version}.example.com:{mock_port}"

    if aap.version == "24":
        eff_api_url = req_spec.url
        eff_api_url = eff_api_url.replace("/api/controller/v2/", "/api/v2/")
    else:
        eff_api_url = req_spec.url
    url = aap.base_url + eff_api_url
    mock_url = MOCK_AAP_URL + eff_api_url
    # resp = _get(aap, url)
    resp = aap.get(eff_api_url, req_spec.valid_status_codes)
    logger.info(f"Status: {resp.status_code} Url: {url}")
    headers={}
    copy_header_if_present("X-Api-Product-Name")
    copy_header_if_present("content-type")
    # if "X-Api-Product-Name" in resp.headers:
    #     headers.update({"X-Api-Product-Name": resp.headers["X-Api-Product-Name"]})
    if resp.headers.get('content-type') == 'application/json':
        body_kwargs = dict(json_body=resp.json())
    else:
        body_kwargs = dict(body=resp.text)
    data = dict(
        url=mock_url,
        status=resp.status_code,
        headers=headers,
        # json_body=resp.json(),
        # body=resp.text,
        **body_kwargs,
    )
    filename = os.path.join(OUT_DIR, req_spec.filename)
    with open(filename, "w") as fout:
        json.dump(data + "\n", fout, indent=2)


def main():
    aap = AAP.get_instance()
    aap.login()
    print(f"AAP version {aap.version}")
    # aap.create_access_token("get-mock-data-token", "read")
    if aap.version == "24":
        req_specs = req_specs_24
    else:
        req_specs = req_specs_26
    
    for req_spec in req_specs:
        get_req(aap, req_spec)


if __name__ == "__main__":
    main()
