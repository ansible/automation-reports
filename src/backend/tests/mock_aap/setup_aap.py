#!/usr/bin/env python3

# First
# Manually setup data in AAP.
# Next use this script, to visit all relevant URLs, and store responses into json files for mock testing.

# Required input, as environ variables:
#   export AAP_VERSION=25
#   export AAP_URL="https://10.44.17.65:443"
#   export AAP_USERNAME=admin
#   export AAP_PASSWORD=...
# Run:
#   ./setup_aap.py

import json
import logging
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
class ObjectSpec(NamedTuple):
    data: dict
    expected: dict = dict()
    extra: dict = dict()


class OAuth2App(NamedTuple):
    id: int
    client_id: str
    client_secret: str


class AAPToken(NamedTuple):
    access_token: str
    refresh_token: str


class AAP:
    def __init__(self, base_url, username, password):
        # TODO Referer "https://10.44.17.65" is correct, "https://10.44.17.65:443" is not.
        assert not base_url.endswith("/")
        # assert not base_url.endswith(":443")
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = None
        self.access_token = ""
        self.version = ""

    @classmethod
    def get_instance(cls):
        aap = cls(
            base_url=os.environ["AAP_URL"],
            username=os.environ["AAP_USERNAME"],
            password=os.environ["AAP_PASSWORD"],
        )
        # print(os.environ["AAP_URL"])
        return aap

    def detect_version(self):
        resp = requests.get(self.base_url + "/api/gateway/v1/ping/", verify=False)
        if resp.status_code == 200:
            # AAP v2.5+
            data = resp.json()
            version = data["version"]  # version is "2.5" or "2.6"
            assert version in ["2.5", "2.6"]
            self.version = version.replace(".", "")
        else:
            # AAP v2.4
            resp = requests.get(self.base_url + "/api/v2/ping/", verify=False)
            data = resp.json()
            version = data["version"]  # version is "4.5.x" - the AWX version
            assert version.startswith("4.5.")
            self.version = "24"

    def login(self):
        self.detect_version()
        session = requests.Session()
        session.auth = requests.auth.HTTPBasicAuth(self.username, self.password)
        session.verify = False
        self.session = session

    def get(self, url, valid_status_codes=None):
        if valid_status_codes is None:
            valid_status_codes = [200]
        assert url.startswith("/")
        api_url = f"{self.base_url}{url}"
        response = self.session.get(api_url)
        assert response.status_code in valid_status_codes, f"status={response.status_code} not one of {valid_status_codes}, url={api_url} text={response.text}"
        return response

    def post(self, url, spec, valid_status_codes=None):
        if valid_status_codes is None:
            valid_status_codes = [201]
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

    def create_oauth2_app(self, description: str, organization_id: int, redirect_uris: str) -> OAuth2App:
        spec = ObjectSpec({
            "name": "ad-app",
            "redirect_uris": "https://aap-ad:8447/auth-callback",
            "description": description,
            "organization": organization_id,
            "app_url": "",
            "client_type": "confidential",
            "authorization_grant_type": "authorization-code"
        })
        response = self.post("/api/gateway/v1/applications/", spec)
        data = response.json()
        # print(f"OAuth2 app created: {data}")
        oauth2app = OAuth2App(
            id=data["id"],
            client_id=data["client_id"],
            client_secret=data["client_secret"],
        )
        return oauth2app

    def create_oauth2_app_token(self, oauth2app: OAuth2App, user_id: int) -> AAPToken:
        spec = ObjectSpec({
            "description": "ad-aap-token",
            "scope": "read",
            "application": oauth2app.id,
            "user": user_id,
        })
        response = self.post("/api/gateway/v1/tokens/", spec)
        data = response.json()
        # print(f"OAuth2 app token created: {data}")
        aaptoken = AAPToken(
            access_token=data["token"],
            refresh_token=data["refresh_token"],
        )
        print(f"AAPToken created: {aaptoken}")
        return aaptoken


aap_version = os.environ["AAP_VERSION"]
default_org_id = 1
admin_user_id = 2
demo_credential_id = 1
demo_inventory_id = 1
org2_id_gw = 2  # id in AAP gateway api
org2_id_cnt = 2  # id in AAP controller api
if aap_version in ["26"]:
    # AAP 2.6, containerised deployment - id is 4
    # AAP 2.6, aap-dev development deployment - id is 2
    default_execution_environment_id = 2
elif aap_version in ["25", "24"]:
    # AAP 2.4, 2.5
    default_execution_environment_id = 2
project2_id = 8 # Demo Project is 6, next project is 8
project3_id = project2_id + 1
project4_id = project2_id + 2
jobtemplate2_id = 11 # Demo Job Template is 7, next job_template is 11
jobtemplate3_id = jobtemplate2_id + 1
jobrun_id = 3 + 1 # first 3 are git-sync jobs, then we have real jobs (4, ...)

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


def create_aap_access_file(oauth2app: OAuth2App, aaptoken: AAPToken, aap_version: str):
    aap_verssion_map = {
        "24": "2.4",
        "25": "2.5",
        "26": "2.6",
    }
    aap_proto = os.environ["AAP_URL"].split(":")[0]
    aap_host_port = os.environ["AAP_URL"].replace("https://", "").replace("http://", "")
    assert "/" not in aap_host_port
    aap_host = aap_host_port.split(":")[0]
    aap_port = aap_host_port.split(":")[1]

    data = {
        "client_id": oauth2app.client_id,
        "client_secret": oauth2app.client_secret,
        "access_token": aaptoken.access_token,
        "refresh_token": aaptoken.refresh_token,
        "aap_url": os.environ["AAP_URL"],
        "aap_protocol": aap_proto,
        "aap_address": aap_host,
        "aap_port": aap_port,
        "aap_version": aap_verssion_map[aap_version],
    }
    with open("aap_access.json", "w") as ff:
        json.dump(data, ff, indent=4)


def main():
    aap = AAP.get_instance()
    aap.login()
    # aap.create_access_token("bla", "write")
    oauth2app = aap.create_oauth2_app("ad-app-desc", default_org_id, "https://aap-ad:8447/auth-callback")
    token =aap.create_oauth2_app_token(oauth2app, admin_user_id)

    create_aap_access_file(oauth2app, token, aap_version)

    assert aap_version == aap.version
    if aap.version in ["25", "26"]:
        me = aap.get("/api/controller/v2/me/")
        me = aap.get("/api/gateway/v1/me/")
    elif aap.version in ["24"]:
        # AAP 2.4
        me = aap.get("/api/v2/me/")

    if aap.version == "24":
        api_url_prefix = "/api/v2"
    else:
        api_url_prefix = "/api/controller/v2"

    print("Creating organizations...")
    if aap.version == "24":
        [aap.post("/api/v2/organizations/", data, [201]) for data in organizations]
    else:
        [aap.post("/api/gateway/v1/organizations/", data, [201]) for data in organizations]
    time.sleep(5)  # gw needs to propagate organizations?
    print("Creating labels...")
    [aap.post(api_url_prefix + "/labels/", spec) for spec in labels]
    print("Creating projects...")
    [aap.post(api_url_prefix + "/projects/", spec) for spec in projects]
    ## [aap.post(api_url_prefix + f"/projects/{spec.expected["id"]}/update/", None, [202]) for spec in projects]
    time.sleep(10)  # wait on project update, otherwise job_template cannot find playbook file
    print("Creating job_templates...")
    [aap.post(api_url_prefix + "/job_templates/", spec) for spec in job_templates]
    print("Assign labels to job_templates...")
    for spec in label_to_template:
        aap.post(api_url_prefix + f"/job_templates/{spec.extra["job_template_id"]}/labels/", spec, [201, 204])
    print("Creating jobs (launch job_templates)...")
    for spec in jobs:
        aap.post(api_url_prefix + f"/job_templates/{spec.extra["job_template_id"]}/launch/", spec)
        time.sleep(1)
    # TODO wait on all jobs to complete

if __name__ == "__main__":
    main()
