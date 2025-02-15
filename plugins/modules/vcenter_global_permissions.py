#!/usr/bin/python
# -*- coding: utf-8 -*-

# Inspired by https://github.com/lamw/vmware-scripts/blob/master/powershell/GlobalPermissions.ps1
# Copyright: (c) 2023, Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vcenter_global_permissions
short_description: Manages Global Permissions for VMware vCenter
description:
  - Create or delete role mappings for vCenter GlobalPermissions
author:
  - Philipp Fruck (@p-fruck)
requirements: []
options:
  principal:
    description:
      - The name of the external user or role
      - To specify Domain user in Ansible task use DOMAIN\\user
      - To specify Domain user in Ansible inventory use DOMAIN\user
    type: str
    required: true
  is_group:
    description:
      - Indicates whether the given principal is a group or a user
    type: bool
    required: true
  role_id:
    description:
      - The ID of the internal vCenter role
      - IDs can be retrieved using the following PowerCLI command `(Get-VIRole -Name Admin).ExtensionData.RoleId`
      - A list of all vCenter role mappings with corresponding ID can be retrieved at https://{vcenter_host}/invsvc/mob3?moid=authorizationService&method=AuthorizationService.GetPermissions
    type: int
    required: true
  propagate:
    description:
      - Whether to propgate the permission assignment
    type: bool
    required: true
  state:
    description:
      - Whether the assignment should be created C(state=present) or removed C(state=absent)
    type: str
    choices: [absent, present]
    default: present
extends_documentation_fragment:
  - community.vmware.vmware.documentation
'''

EXAMPLES = r'''
- name: Apply a mapping for a single user and the domain admin group
  vcenter_global_permissions:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    principal: "{{ item.name }}"
    is_group: "{{ item.is_group }}"
    role_id: "{{ item.role_id }}"
    propagate: "{{ item.propagate }}"
  delegate_to: localhost
  loop:
    - name: MYDOMAIN\\Administrators
      is_group: true
      role_id: -1 # vCenter Admin role
      propagate: true
    - name: MYDOMAIN\\TheAnswerToEverything
      is_group: false
      role_id: 42 # Insert a valid role here
      propagate: false

- name: Remove admin permissions for user John
  vcenter_global_permissions:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    principal: MYDOEMAIN\\John # must be single backslash when defined through inventory
    is_group: false
    role_id: -1
    propagate: false
    state: absent
  delegate_to: localhost
'''

RETURN = r'''
html:
  description: The HTML response of the server
  type: str
  returned: failure
'''

import re
import requests

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import vmware_argument_spec


class MobClient():
    """Reusable MobClient in case the Mob Service will be required for future modules"""
    def __init__(self, module, method):
        self.module = module
        self.params = module.params

        self.session = requests.session()
        self.session.verify = module.params['validate_certs']

        vcenter_host = module.params['hostname']
        self.base_url = f"https://{vcenter_host}/invsvc/mob3"
        self.mob_url = f"{self.base_url}/?moid=authorizationService&method=AuthorizationService.{method}"

    def login(self):
        self.session.auth = (self.params['username'], self.params['password'])
        res = self.session.get(self.mob_url)

        if res.status_code != 200:
            self.module.fail_json(msg="Cannot login to vCenter")

        # Parse hidden nonce required for CSRF error
        nonce_regex = r'input name="vmware-session-nonce" type="hidden" value="(.*?)"'
        self.vmware_nonce = re.search(nonce_regex, res.text).group(1)

    def logout(self):
        self.session.get(f"{self.base_url}/logout")


class VSphereClient(MobClient):
    def generate_xml_payload(self):
        return """
            <permissions>
                <principal>
                    <name>{name}</name>
                    <group>{is_group}</group>
                </principal>
                <roles>{role_id}</roles>
                <propagate>{propagate}</propagate>
            </permissions>
        """.format(
            name=self.params['principal'],
            is_group=str(self.params['is_group']).lower(),
            role_id=self.params['role_id'],
            propagate=str(self.params['propagate']).lower(),
        )

    def manage_role(self):
        data = {
            "vmware-session-nonce": self.vmware_nonce,
            "permissions": self.generate_xml_payload(),
        }
        return self.session.post(self.mob_url, data=data)


def main():
    argument_spec = vmware_argument_spec()

    argument_spec.update(dict(
        principal=dict(type='str', required=True),
        is_group=dict(type='bool', required=True),
        role_id=dict(type='int', required=True),
        propagate=dict(type='bool', required=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
    )
    if module.params['state'] == "present":
        client = VSphereClient(module, "AddGlobalAccessControlList")
    else:
        client = VSphereClient(module, "RemoveGlobalAccess")
    client.login()
    result = client.manage_role()
    client.logout()

    if re.search("Method Invocation Result: void", result.text):
        # success, no special output is given
        module.exit_json(changed=True)
    # failure, error is displayed as HTML table
    module.fail_json(msg="Failed to add role. See html output for more details", html=result.text)


if __name__ == '__main__':
    main()
