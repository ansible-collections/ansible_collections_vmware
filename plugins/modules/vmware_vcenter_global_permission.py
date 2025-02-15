#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Christian Neugum
# Copyright: (c) 2022, VMware, Inc.
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_vcenter_global_permission
short_description: Manage global permission
description: This module can be used to manage global permissions on the given vCenter.
author:
- Christian Neugum
notes:
    - The user must have the appropriate rights to administer permissions.
options:
  role:
    description:
    - The role to be assigned permission.
    - User can also specify role name presented in Web UI.
    required: True
    type: str
  principal:
    description:
    - The user to be assigned permission.
    - Required if C(group) is not specified.
    - If specifying domain user, required separator of domain uses backslash.
    type: str
  group:
    description:
    - The group to be assigned permission.
    - Required if C(principal) is not specified.
    type: str
  recursive:
    description:
    - Should the permissions be recursively applied.
    default: True
    type: bool
  state:
    description:
    - Indicate desired state of the object's permission.
    - When C(state=present), the permission will be added if it doesn't already exist.
    - When C(state=absent), the permission is removed if it exists.
    choices: ['present', 'absent']
    default: present
    type: str
extends_documentation_fragment:
- community.vmware.vmware.documentation
'''

EXAMPLES = r'''
- name: Assign user global permission
  community.vmware.vmware_vcenter_global_permission:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    role: Admin
    principal: user_bob
    state: present
  delegate_to: localhost
- name: Unassign user global permission
  community.vmware.vmware_vcenter_global_permission:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    role: Admin
    principal: user_bob
    state: absent
  delegate_to: localhost
'''

RETURN = r'''
changed:
    description: whether or not a change was made to the object's role
    returned: always
    type: bool
'''

try:
    from pyVmomi import vim, vmodl

    import pandas as pd
    from urllib import request, parse
    import ssl
    import re
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi, vmware_argument_spec

class VMwareVcenterGlobalPermission(PyVmomi):
    def __init__(self, module):
        super(VMwareVcenterGlobalPermission, self).__init__(module)
        self.module = module
        self.params = module.params
        self.state = self.params['state']
        self.role_list = self.populate_role_list()
        self.perm = self.build_perm()
        self.perm_before = {}

        self._init_urllib_context()
        self.session_nonce_regex = re.compile('name=\"vmware-session-nonce\"\stype=\"hidden\"\svalue=\"?([^\s^\"]+)\"')

    def _init_urllib_context(self):
        # build SSL context
        context = ssl.SSLContext()
        if self.params['validate_certs']:
            context.verify_mode = ssl.CERT_REQUIRED
        else:
            context.verify_mode = ssl.CERT_NONE
        httpsHandler = request.HTTPSHandler(context = context)

        # build auth context
        manager = request.HTTPPasswordMgrWithDefaultRealm()
        manager.add_password(None, "https://"+self.params['hostname'], self.params['username'], self.params['password'])
        authHandler = request.HTTPBasicAuthHandler(manager)

        # configure opener with contexts
        opener = request.build_opener(httpsHandler, authHandler)
        request.install_opener(opener)

    def _mob_post(self, url, data={}):
        # get vmware-session-nonce and session cookie
        response = request.urlopen(url)
        content = response.read().decode(response.headers.get_content_charset())
        cookies = response.info().get_all('Set-Cookie')

        session_cookie = cookies[0]
        mob_vmware_session_nonce = self.session_nonce_regex.search(content).group(1)

        # get all permissions
        data_session = {'vmware-session-nonce': mob_vmware_session_nonce}
        data_complete = {**data, **data_session}
        data_complete = parse.urlencode(data_complete).encode("utf-8")
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': session_cookie
            }
        req = request.Request(url, headers=headers, data=data_complete)
        response = request.urlopen(req)

        return response.read().decode(response.headers.get_content_charset())

    def populate_role_list(self):
        # this function is copied from
        # community.vmware.vmware_object_role_permission
        # to implement the same look&feel here

        user_friendly_role_names = {
            'Admin': ['Administrator'],
            'ReadOnly': ['Read-Only'],
            'com.vmware.Content.Admin': [
                'Content library administrator (sample)',
                'Content library administrator'
            ],
            'NoCryptoAdmin': ['No cryptography administrator'],
            'NoAccess': ['No access'],
            'VirtualMachinePowerUser': [
                'Virtual machine power user (sample)',
                'Virtual machine power user'
            ],
            'VirtualMachineUser': [
                'Virtual machine user (sample)',
                'Virtual machine user'
            ],
            'ResourcePoolAdministrator': [
                'Resource pool administrator (sample)',
                'Resource pool administrator'
            ],
            'VMwareConsolidatedBackupUser': [
                'VMware Consolidated Backup user (sample)',
                'VMware Consolidated Backup user'
            ],
            'DatastoreConsumer': [
                'Datastore consumer (sample)',
                'Datastore consumer'
            ],
            'NetworkConsumer': [
                'Network administrator (sample)',
                'Network administrator'
            ],
            'VirtualMachineConsoleUser': ['Virtual Machine console user'],
            'InventoryService.Tagging.TaggingAdmin': ['Tagging Admin'],
        }
        role_list = {}
        for role in self.content.authorizationManager.roleList:
            role_list[role.name] = role
            if user_friendly_role_names.get(role.name):
                for role_name in user_friendly_role_names[role.name]:
                    role_list[role_name] = role

        return role_list

    def get_role_id(self, role_name):
        role = self.role_list.get(role_name, None)
        if not role:
            self.module.fail_json(msg="Specified role (%s) was not found" % role_name)
        return role.roleId

    def get_perms(self):
        mob_uri = "/invsvc/mob3/?moid=authorizationService&method=AuthorizationService.GetGlobalAccessControlList"

        # get permissions as HTML
        html_permissions = self._mob_post(url="https://"+self.params['hostname']+mob_uri)

        # parse permissions
        tables = pd.read_html(html_permissions)
        global_permissions = []
        perm_found = False

        # we got many tables in the HTML response
        for table in tables:
            # buffer vars to get the role and propagate attribute
            # needs to be reset for each table
            #  as this information should be in the same table
            current_role = None
            current_propagate = None
            # we have to parse each row in the table
            for row in table.values:
                row_list = row.tolist()

                # until a permission table is not found we search for one
                if not perm_found:
                    # looking for the row describing the role ID
                    if row_list[0] == "roles":
                        current_role = int(row_list[2])
                    # looking for the row describing the propagation
                    if row_list[0] == "propagate":
                        current_propagate = True if row_list[2] == "true" else False

                    # when we found a role and propagate attribute
                    #  we can create a new permission dict and the next table will be
                    #  the principal description
                    if current_role != None and current_propagate != None:
                        permission = {
                            'roleId': current_role,
                            'propagate': current_propagate,
                            'isGroup': None,
                            'principal': None
                        }
                        global_permissions.append(permission)
                        perm_found = True
                        break
                # we found the permission table so the next table has to
                #  be the principal table
                else:
                    # looking for the row describing if the principal is a group
                    if row_list[0] == "group":
                        global_permissions[-1]['isGroup'] = True if row_list[2] == "true" else False
                    # looking for the row describing the principals name
                    elif row_list[0] == "name":
                        global_permissions[-1]['principal'] = row_list[2]

                    # after we found the group and name attribute
                    #  we can look for the next permission
                    if global_permissions[-1]['isGroup'] != None and global_permissions[-1]['principal'] != None:
                        perm_found = False
                        break

        return global_permissions

    def build_perm(self):
        if self.params.get('principal', None) is not None:
            principal = self.params['principal']
            is_group = False
        elif self.params.get('group', None) is not None:
            principal = self.params['group']
            is_group = True
        else:
            self.module.fail_json(msg="You must define principal or group")

        permission = {
            'roleId': self.get_role_id(self.params['role']),
            'propagate': self.params['recursive'],
            'isGroup': is_group,
            'principal': principal
        }

        return permission

    def same_permission(self, perm_one, perm_two):
        return perm_one['principal'].lower() == perm_two['principal'].lower() \
            and perm_one['roleId'] == perm_two['roleId'] \
            and perm_one['propagate'] == perm_two['propagate']

    def get_state(self):
        for perm in self.get_perms():
            if self.perm['principal'].lower() == perm['principal'].lower():
                self.perm_before = perm
            if self.same_permission(self.perm, perm):
                return 'present'
        return 'absent'

    def process_state(self):
        local_permission_states = {
            'absent': {
                'present': self.remove_permission,
                'absent': self.state_exit_unchanged,
            },
            'present': {
                'present': self.state_exit_unchanged,
                'absent': self.add_permission,
            }
        }
        try:
            local_permission_states[self.state][self.get_state()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))
        except Exception as e:
            self.module.fail_json(msg=to_native(e))

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def add_permission(self):
        if not self.module.check_mode:
            mob_uri = "/invsvc/mob3/?moid=authorizationService&method=AuthorizationService.AddGlobalAccessControlList"
            permission = {
                'permissions': "<permissions><principal><name>"+self.perm['principal']+"</name><group>"+str(self.perm['isGroup'])+"</group></principal><roles>"+str(self.perm['roleId'])+"</roles><propagate>"+str(self.perm['propagate'])+"</propagate></permissions>"
            }
            self._mob_post(url="https://"+self.params['hostname']+mob_uri, data=permission)

        self.module.exit_json(changed=True, before=self.perm_before, after=self.perm)

    def remove_permission(self):
        if not self.module.check_mode:
            # TODO: implement call to remove permission
            mob_uri = "/invsvc/mob3/?moid=authorizationService&method=AuthorizationService.RemoveGlobalAccess"
            principal = {
                'principals': "<principals><name>"+self.perm['principal']+"</name><group>"+str(self.perm['isGroup'])+"</group></principals>"
            }
            self._mob_post(url="https://"+self.params['hostname']+mob_uri, data=principal)

        self.module.exit_json(changed=True, before=self.perm_before, after="Deleted")

def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            role=dict(required=True, type='str'),
            principal=dict(type='str'),
            group=dict(type='str'),
            recursive=dict(type='bool', default=True),
            state=dict(default='present', choices=['present', 'absent'], type='str'),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['principal', 'group']
        ],
        required_one_of=[
            ['principal', 'group']
        ],
    )

    vmware_global_permission = VMwareVcenterGlobalPermission(module)
    vmware_global_permission.process_state()


if __name__ == '__main__':
    main()
