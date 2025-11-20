#!/usr/bin/env python3

# First
# Manually setup data in AAP.
# Next use this script, to visit all relevant URLs, and store responeses into json files for mock testing.

# Required input, as environ variables:
#   export AAP_URL="https://10.44.17.65:443"
#   export AAP_USERNAME=admin
#   export AAP_PASSWORD=...
# Run:
#   ./get_mock_data.py

import logging
from collections import namedtuple
import time
from typing import NamedTuple
import requests
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
requests.packages.urllib3.disable_warnings(category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

# Fields
# - data is POSTed to AAP.
# - expected are values expected in the AAP response.
# ObjectSpec = namedtuple("ObjectSpec", ["data", "expected", "extra"], defaults=(1, 2))
class ObjectSpec(NamedTuple):
    data: dict
    expected: dict = dict()
    extra: dict = dict()

# RequestSpec = namedtuple('RequestSpec', ['filename', 'url'])
class AAP:
    def __init__(self, base_url, username, password):
        # TODO Referer "https://10.44.17.65" is correct, "https://10.44.17.65:443" is not.
        assert not base_url.endswith("/")
        assert not base_url.endswith(":443")
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = None
        self.access_token = ""

    @classmethod
    def get_instance(cls):
        aap = cls(
            base_url=os.environ["AAP_URL"],
            username=os.environ["AAP_USERNAME"],
            password=os.environ["AAP_PASSWORD"],
        )
        return aap

    def login(self):
        session = requests.Session()
        session.auth = requests.auth.HTTPBasicAuth(self.username, self.password)
        session.verify = False
        self.session = session

    def get(self, url, valid_status_codes=[200]):
        assert url.startswith("/")
        api_url = f"{self.base_url}{url}"
        response = self.session.get(api_url)
        assert response.status_code in valid_status_codes
        return response

    def post(self, url, spec, valid_status_codes=[201]):
        if spec:
            data = spec.data
            expected = spec.expected
        else:
            data = None
            expected = {}
        assert url.startswith("/")
        api_url = f"{self.base_url}{url}"
        response = self.session.post(api_url, json=data)
        assert response.status_code in valid_status_codes, f"status_code {response.status_code} is not {valid_status_codes}, text={response.text}, spec.data={data}"
        if response.text:
            resp_json = response.json()
        else:
            resp_json = {}
        for name, expected_value in expected.items():
            value = resp_json[name]
            assert expected_value == value, f"Mismatch name={name} expected={expected_value}, actual={value}, resp_json={resp_json}, spec.data={data}"
        return response

    def create_access_token(self, description: str, scope="read"):
        # this token is for get_mock_data.py
        token_spec = ObjectSpec({
            "description": description,
            "scope": scope,
            },
        )
        response = self.post("/api/gateway/v1/tokens/", token_spec)
        data = response.json()
        self.access_token = data["token"]
        # "/api/gateway/v1/tokens/" has no refresh_token, and no OAuth2 app is associated.
        print(f"access_token={self.access_token}")


default_org_id = 1
default_execution_environment_id = 4
demo_credential_id = 1
demo_inventory_id = 1
#
org2_id_gw = 2  # id in AAP gateway api
org2_id_cnt = 8  # id in AAP controller api
project2_id = 8 # Demo Project is 6
jobtemplate2_id = 11 # Demo Job Template is 7
jobrun_id = 3 + 1 # first 3 git-sync jobs, then real jobs

# if 0:
#     # TEMP
#     org2_id = 8
#     # project2_id = 16
#     # jobtemplate2_id = 20
#     # jobrun_id = 12

project3_id = project2_id + 1
project4_id = project2_id + 2
jobtemplate3_id = jobtemplate2_id + 1

organizations = [
    ObjectSpec({
            "name": "org2",
            "description": "org2-desc",
            "max_hosts": 0,
        },
        dict(
            id=org2_id_gw,
        )),
]
labels = [
    ObjectSpec({
            "name": "label1-org1",
            "organization": default_org_id,
        },
        dict(
            id=1,
        )),
    ObjectSpec({
            "name": "label2-org1",
            "organization": default_org_id,
        },
        dict(
            id=2,
        )),
    ObjectSpec({
            "name": "label3-org2",
            "organization": org2_id_cnt,
        },
        dict(
            id=3,
        )),
    ObjectSpec({
            "name": "label4-org2",
            "organization": org2_id_cnt,
        },
        dict(
            id=4,
        )),
]
projects = [
    ObjectSpec({
        "name": "project2-org1",
        "description": "project2-org1",
        "scm_url": "https://github.com/ansible/ansible-tower-samples",
        "scm_type": "git",
        # "scm_branch": "",
        # "credential": null,
        "organization": default_org_id,
        },
        dict(
            id=project2_id,
        )),
    ObjectSpec({
        "name": "project3-org1",
        "description": "project3-org1",
        "scm_url": "https://github.com/ansible/ansible-tower-samples",
        "scm_type": "git",
        "organization": default_org_id,
        },
        dict(
            id=project3_id,
        )),
    ObjectSpec({
        "name": "project4-org2",
        "description": "project4-org2",
        "scm_url": "https://github.com/ansible/ansible-tower-samples",
        "scm_type": "git",
        "organization": org2_id_cnt,
        },
        dict(
            id=project4_id,
        )),
]
# inventories = []
# credential = []
# execution_environments = []
job_templates = [
    ObjectSpec({
        "name": "jobtemplate2-org1",
        "description": "jobtemplate2-org1",
        "inventory": demo_inventory_id,
        "project": project2_id,
        "playbook": "hello_world.yml",
        "credential": demo_credential_id,
        "execution_environment": default_execution_environment_id,
        },
        dict(
            id=jobtemplate2_id,
        )),
    ObjectSpec({
        "name": "jobtemplate3-org1",
        "description": "jobtemplate3-org1",
        "inventory": demo_inventory_id,
        "project": project3_id,
        "playbook": "hello_world.yml",
        "credential": demo_credential_id,
        "execution_environment": default_execution_environment_id,
        },
        dict(
            id=jobtemplate3_id,
        )),
]
label_to_template = [
    ObjectSpec({
        "name": "label1-org1",
        "organization": default_org_id, # org2_id_cnt
        },
        dict(),
        dict(
            job_template_id=jobtemplate2_id,
        )
    ),
    ObjectSpec({
        "name": "label1-org1",
        "organization": default_org_id,
        },
        dict(),
        dict(
            job_template_id=jobtemplate3_id,
        )
    ),
    ObjectSpec({
        "name": "label2-org1",
        "organization": default_org_id,
        },
        dict(),
        dict(
            job_template_id=jobtemplate3_id,
        )
    ),
]
jobs = [
    ObjectSpec(
        {},
        dict(
            id=expected_job_id,
        ),
        dict(
            job_template_id=job_templates[job_template_ind].expected["id"],
        )
    )
    for job_template_ind, expected_job_id in
    [
        # run 0th template (jobtemplate2-org1) 2 times
        (0, jobrun_id + 0),
        (0, jobrun_id + 1),
        # run 1st template
        (1, jobrun_id + 2),
        (1, jobrun_id + 3),
    ]
]


def main():
    aap = AAP.get_instance()
    aap.login()
    # aap.create_access_token("bla", "write")
    me = aap.get("/api/controller/v2/me/")
    me = aap.get("/api/gateway/v1/me/")
    
    print("Creating organizations...")
    [aap.post("/api/gateway/v1/organizations/", data, [201]) for data in organizations]
    time.sleep(5)  # gw needs to propagate organizations?
    print("Creating labels...")
    [aap.post("/api/controller/v2/labels/", spec) for spec in labels]
    print("Creating projects...")
    [aap.post("/api/controller/v2/projects/", spec) for spec in projects]
    ## [aap.post(f"/api/controller/v2/projects/{spec.expected["id"]}/update/", None, [202]) for spec in projects]
    time.sleep(10)  # wait on project update, otherwise job_template cannot find playbook file
    print("Creating job_templates...")
    [aap.post("/api/controller/v2/job_templates/", spec) for spec in job_templates]
    print("Assign labels to job_templates...")
    for spec in label_to_template:
        aap.post(f"/api/controller/v2/job_templates/{spec.extra["job_template_id"]}/labels/", spec, [201, 204])
    print("Creating jobs (launch job_templates)...")
    for spec in jobs:
        aap.post(f"/api/controller/v2/job_templates/{spec.extra["job_template_id"]}/launch/", spec)
        time.sleep(1)
    # TODO wait on all jobs to complete

if __name__ == "__main__":
    main()
