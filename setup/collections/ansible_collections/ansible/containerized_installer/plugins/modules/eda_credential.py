#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2023, Ansible Automation Platform
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: eda_credential

short_description: Creates a container registry credential in Automation EDA Controller

version_added: "2.4"

description: Creates a container registry credential in Automation EDA Controller

options:
    eda_server_url:
        description: Automation EDA Controller server URL
        required: true
        type: str
    eda_username:
        description: Automation EDA Controller server administrator username
        required: true
        type: str
    eda_password:
        description: Automation EDA Controller server administrator password
        required: true
        type: str
    name:
        description: Name for credential
        required: true
        type: str
    username:
        description: Username for container repository
        required: true
        type: str
    token:
        description: Token for container repository
        required: true
        type: str
    validate_certs:
        description: Validate SSL certificates for connection
        required: true
        type: bool

author:
    - Ansible Automation Platform Team
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.parse import quote_plus
import json


def run_module():
    module_args = dict(
        eda_server_url=dict(type="str", required=True),
        eda_username=dict(type="str", required=True),
        eda_password=dict(type="str", required=True, no_log=True),
        name=dict(type="str", required=True),
        username=dict(type="str", required=True),
        token=dict(type="str", required=True, no_log=True),
        validate_certs=dict(type="bool", required=True),
    )

    result = dict(
        changed=False,
        message=[],
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(**result)

    api_url_base = f"{module.params['eda_server_url']}/api/eda/v1"

    api_username = module.params["eda_username"]
    api_password = module.params["eda_password"]
    validate_certs = module.params["validate_certs"]
    header = {"Content-Type": "application/json"}

    cred_api_url = f"{api_url_base}/credentials/"
    name = module.params["name"]
    username = module.params["username"]
    token = module.params["token"]

    payload = {
        "name": name,
        "username": username,
        "secret": token,
        "credential_type": "Container Registry",
    }

    cred_api_url_by_name = f"{cred_api_url}?name={quote_plus(name)}"
    try:
        cred_check = json.loads(
            open_url(
                cred_api_url_by_name,
                method="GET",
                headers=header,
                validate_certs=validate_certs,
                force_basic_auth=True,
                url_username=api_username,
                url_password=api_password,
            ).read()
        )
    except Exception as e:
        result["message"].append(
            f"Failed to check if '{name}' already exists, skipping creation. Error: {e}"
        )
        module.fail_json("", **result)
    else:
        if not cred_check["count"]:
            try:
                open_url(
                    cred_api_url,
                    method="POST",
                    headers=header,
                    validate_certs=validate_certs,
                    force_basic_auth=True,
                    url_username=api_username,
                    url_password=api_password,
                    data=json.dumps(payload),
                )
            except Exception as e:
                result["message"].append(f"Failed to create '{name}'. Error: {e}")
                module.fail_json("", **result)
            else:
                result["message"].append(f"Created '{name}' credential")
                result["changed"] = True
        else:
            result["message"].append(f"'{name}' credential already exists")

        module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
