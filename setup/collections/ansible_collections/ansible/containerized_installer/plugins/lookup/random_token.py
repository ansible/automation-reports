# -*- coding: utf-8 -*-
# Copyright (c) 2022, Dimitri Savineau <dsavinea@redhat.com>
# Apache License version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    name: random_token
    author:
      - Dimitri Savineau (@dsavineau)
    short_description: Generates random token
    description:
      - Generates random token.
"""

EXAMPLES = r"""
- name: Generate random token
  ansible.builtin.debug:
    var: lookup('random_token')
"""

RETURN = r"""
  _raw:
    description: A one-element list containing a random token
    type: list
    elements: str
"""

from cryptography.fernet import Fernet

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        token = Fernet.generate_key().decode("utf-8")

        return [token]
