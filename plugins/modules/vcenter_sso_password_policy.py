#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2023, Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vcenter_sso_password_policy
short_description: Manage the password policy for the vsphere.local domain
description:
  - Configure the vSphere SSO password policy for local accounts
author:
  - Philipp Fruck (@p-fruck)
requirements: []
options:
  max_identical_adjacent_characters:
    description:
      - The maximum number of adjacent characters
    type: int
    required: False
  max_length:
    description:
      - The maximum password length
    type: int
    required: False
  min_alphabetic_count:
    description:
      - The minimum number of alphabetic characters in the password
    type: int
    required: False
  min_length:
    description:
      - The minimum password length
    type: int
    required: False
  min_lowercase_count:
    description:
      - The minimum number of lower case characters in the password
    type: int
    required: False
  min_numeric_count:
    description:
      - The minimum number of numeric characters in the password
    type: int
    required: False
  min_special_char_count:
    description:
      - The minimum number of special characters in the password
    type: int
    required: False
  min_uppercase_count:
    description:
      - The minimum number of upper case characters in the password
    type: int
    required: False
  password_lifetime_days:
    description:
      - The maximum lifetime before a password expires
    type: int
    required: False
  prohibited_previous_password_count:
    description:
      - The amount of previous passwords that cannot be reused
    type: int
    required: False
extends_documentation_fragment:
  - community.vmware.vmware.documentation
'''

EXAMPLES = r'''
- name: Set the password expiration time to 360 days
  vcenter_sso_password_policy:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    password_lifetime_days: 360
  delegate_to: localhost
'''

RETURN = r'''
password_policy:
  description: The final password policy
  type: str
  returned: success
response:
  description: The failed HTML response
  type: str
  returned: failure
msg:
  description: An explanatory description
  type: str
  returned: failure
'''


import base64
import re
import requests

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import vmware_argument_spec


class VSphereUiClient():
    """Reusable API client that utilizes the internal vSphere UI API endpoints"""
    def __init__(self, module):
        self.module = module
        self.params = module.params

        self.session = requests.session()
        self.session.verify = module.params['validate_certs']

        vcenter_host = module.params['hostname']
        self.ui_base_url = f"https://{vcenter_host}/ui"

        token_plain = f"{self.params['username']}:{self.params['password']}"
        self.auth_token = base64.b64encode(token_plain.encode()).decode()

    @property
    def csrf_token(self):
        return self.session.cookies.get_dict().get("VSPHERE-UI-XSRF-TOKEN")

    def login(self):
        saml_redirect_response = self.session.get(f"{self.ui_base_url}/login")

        login_response = self.session.post(saml_redirect_response.url, data={
            "CastleAuthorization": f"Basic {self.auth_token}"
        })

        try:
            saml_response_match = re.search('name="SAMLResponse" value="(.*?)"', login_response.text)
            saml_response = saml_response_match.group(1)

            relay_state_match = re.search('name="RelayState" value="(.*?)"', login_response.text)
            relay_state = relay_state_match.group(1)
        except Exception:
            self.module.fail_json(msg="Failed to sign in to vCenter due to invalid credentials")

        sso_response = self.session.post(f"{self.ui_base_url}/saml/websso/sso", data={
            "SAMLResponse": saml_response,
            "RelayState": relay_state,
        })

        if sso_response.status_code != 200:
            self.module.fail_json(msg="Failed to sign in to vCenter using SAML")

    def prepare_csrf_request(self):
        """Retrieve the web client id as well as CSRF token as cookie"""
        self.session.headers["Authorization"] = f"Basic {self.auth_token}"

        config_response = self.session.get(f"{self.ui_base_url}/config/h5-config?debug=false", headers={
            "X-Requested-With": "XMLHttpRequest",
        })

        client_id = config_response.json()['clientId']
        self.session.headers['webClientSessionId'] = client_id
        print(self.csrf_token)
        self.session.headers['X-VSPHERE-UI-XSRF-TOKEN'] = self.csrf_token

    def logout(self):
        self.session.get(f"{self.ui_base_url}/logout")


class VSphereClient(VSphereUiClient):
    @property
    def password_policy_url(self):
        return f"{self.ui_base_url}/psc-ui/ctrl/psc/passwordpolicy"

    def get_password_policy(self):
        password_policy_response = self.session.get(self.password_policy_url)
        return password_policy_response.json()["passwordPolicy"]

    def update_password_policy(self, policy):
        policy_update_response = self.session.put(
            self.password_policy_url,
            json={"passwordPolicy": policy},
        )

        if not policy_update_response.status_code == 200:
            self.module.fail_json(
                msg="Failed to update password policy",
                response=policy_update_response.text,
            )

    def process_state(self):
        def to_snake_case(name):
            """transform any camel cased string into snake case"""
            pattern = re.compile(r'(?<!^)(?=[A-Z])')
            return pattern.sub('_', name).lower()

        params = (
            "maxIdenticalAdjacentCharacters",
            "maxLength",
            "minAlphabeticCount",
            "minLength",
            "minLowercaseCount",
            "minNumericCount",
            "minSpecialCharCount",
            "minUppercaseCount",
            "passwordLifetimeDays",
            "prohibitedPreviousPasswordCount",
        )

        policy = self.get_password_policy()
        changed = False
        for param in params:
            new_value = self.params.get(to_snake_case(param))
            if new_value and new_value != policy[param]:
                policy[param] = new_value
                changed = True

        if changed:
            self.update_password_policy(policy)

        self.module.exit_json(changed=changed, password_policy=policy)


def main():
    argument_spec = vmware_argument_spec()

    argument_spec.update(dict(
        max_identical_adjacent_characters=dict(type='int', required=False),
        max_length=dict(type='int', required=False),
        min_alphabetic_count=dict(type='int', required=False),
        min_length=dict(type='int', required=False),
        min_lowercase_count=dict(type='int', required=False),
        min_numeric_count=dict(type='int', required=False),
        min_special_char_count=dict(type='int', required=False),
        min_uppercase_count=dict(type='int', required=False),
        password_lifetime_days=dict(type='int', required=False),
        prohibited_previous_password_count=dict(type='int', required=False),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    client = VSphereClient(module)
    client.login()
    client.prepare_csrf_request()
    client.process_state()
    client.logout()


if __name__ == '__main__':
    main()
