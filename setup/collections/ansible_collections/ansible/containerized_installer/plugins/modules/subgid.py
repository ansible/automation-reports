#!/usr/bin/python

# Copyright: (c) 2021, Shane McDonald <shanemcd@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: subgid

short_description: Module for managing /etc/subgid

version_added: "1.0.0"

description: This is a module for managing /etc/subgid.

options:
    group:
        description: The group to add or remove from /etc/subgid
        required: true
        type: str
    state:
        description: The desired state of the entry in /etc/subgid
        required: false
        type: str
        default: "present"
        choices: ["present", "absent"]
    start:
        description:
            - The start of the subgid range for the given group
            - If not provided, this module will find the next available gid or start at 100000
        required: false
        type: int
    count:
        description:
            - The number of gids to allocate to the local group
            - The default of 65536 was taken from Fedora 34
        required: false
        type: int
        default: 65536

author:
    - Shane McDonald (@shanemcd)
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ansible.containerized_installer.plugins.module_utils.subids import (
    run,
)


def run_module():
    module_args = dict(
        group=dict(type="str", required=True),
        state=dict(type="str", required=False, default="present"),
        start=dict(type="int", required=False),
        count=dict(type="int", required=False, default=65536),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(**result)

    run(module, result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
