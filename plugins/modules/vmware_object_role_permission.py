#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Derek Rushing <derek.rushing@geekops.com>
# Copyright: (c) 2018, VMware, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_object_role_permission
short_description: Manage local roles on an ESXi host
description: This module can be used to manage object permissions on the given host.
author:
- Derek Rushing (@kryptsi)
- Joseph Andreatta (@vmwjoseph)
notes:
    - Tested on ESXi 6.5, vSphere 6.7
    - The ESXi login user must have the appropriate rights to administer permissions.
    - Permissions for a distributed switch must be defined and managed on either the datacenter or a folder containing the switch.
requirements:
    - "python >= 2.7"
    - PyVmomi
options:
  role:
    description:
    - The role to be assigned permission.
    - User can also specify role name presented in Web UI. Supported added in 1.5.0.
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
  object_name:
    description:
    - The object name to assigned permission.
    - Required if C(object_moid) is not specified.
    type: str
    required: False
  object_moid:
    description:
    - The Managed Object ID to assigned permission.
    - Required if C(object_name) is not specified.
    type: str
    required: False
  object_type:
    description:
    - The object type being targeted.
    default: 'Folder'
    choices: ['Folder', 'VirtualMachine', 'Datacenter', 'ResourcePool',
              'Datastore', 'Network', 'HostSystem', 'ComputeResource',
              'ClusterComputeResource', 'DistributedVirtualSwitch']
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
- name: Assign user to VM folder
  community.vmware.vmware_object_role_permission:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    role: Admin
    principal: user_bob
    object_name: services
    state: present
  delegate_to: localhost

- name: Remove user from VM folder
  community.vmware.vmware_object_role_permission:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    role: Admin
    principal: user_bob
    object_name: services
    state: absent
  delegate_to: localhost

- name: Assign finance group to VM folder
  community.vmware.vmware_object_role_permission:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    role: Limited Users
    group: finance
    object_name: Accounts
    state: present
  delegate_to: localhost

- name: Assign view_user Read Only permission at root folder
  community.vmware.vmware_object_role_permission:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    role: ReadOnly
    principal: view_user
    object_name: rootFolder
    state: present
  delegate_to: localhost

- name: Assign domain user to VM folder
  community.vmware.vmware_object_role_permission:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: false
    role: Admin
    principal: "vsphere.local\\domainuser"
    object_name: services
    state: present
  delegate_to: localhost

- name: Assign domain user to VM folder with MOID
  community.vmware.vmware_object_role_permission:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: false
    role: Admin
    principal: "vsphere.local\\domainuser"
    object_moid: group-v272542
    state: present
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
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi, vmware_argument_spec, find_obj


class VMwareObjectRolePermission(PyVmomi):
    def __init__(self, module):
        super(VMwareObjectRolePermission, self).__init__(module)
        self.module = module
        self.params = module.params
        self.is_group = False
        self.role_list = {}
        self.role = None
        self.auth_manager = self.content.authorizationManager
        self.populate_role_list()

        if self.params.get('principal', None) is not None:
            self.applied_to = self.params['principal']
        elif self.params.get('group', None) is not None:
            self.applied_to = self.params['group']
            self.is_group = True

        self.get_role()
        self.get_object()
        self.get_perms()
        self.perm = self.setup_permission()
        self.state = self.params['state']

    def populate_role_list(self):
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
        for role in self.auth_manager.roleList:
            self.role_list[role.name] = role
            if user_friendly_role_names.get(role.name):
                for role_name in user_friendly_role_names[role.name]:
                    self.role_list[role_name] = role

    def get_perms(self):
        self.current_perms = self.auth_manager.RetrieveEntityPermissions(self.current_obj, False)

    def same_permission(self, perm_one, perm_two):
        return perm_one.principal.lower() == perm_two.principal.lower() \
            and perm_one.roleId == perm_two.roleId

    def get_state(self):
        for perm in self.current_perms:
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

    def setup_permission(self):
        perm = vim.AuthorizationManager.Permission()
        perm.entity = self.current_obj
        perm.group = self.is_group
        perm.principal = self.applied_to
        perm.roleId = self.role.roleId
        perm.propagate = self.params['recursive']
        return perm

    def add_permission(self):
        if not self.module.check_mode:
            self.auth_manager.SetEntityPermissions(self.current_obj, [self.perm])
        self.module.exit_json(changed=True)

    def remove_permission(self):
        if not self.module.check_mode:
            self.auth_manager.RemoveEntityPermission(self.current_obj, self.applied_to, self.is_group)
        self.module.exit_json(changed=True)

    def get_role(self):
        self.role = self.role_list.get(self.params['role'], None)
        if not self.role:
            self.module.fail_json(msg="Specified role (%s) was not found" % self.params['role'])

    def get_object(self):
        # find_obj doesn't include rootFolder
        if self.params['object_type'] == 'Folder' and self.params['object_name'] == 'rootFolder':
            self.current_obj = self.content.rootFolder
            return
        try:
            getattr(vim, self.params['object_type'])
        except AttributeError:
            self.module.fail_json(msg="Object type %s is not valid." % self.params['object_type'])

        if self.params['object_moid']:
            moid = self.params['object_moid']
            all_objects = find_obj(content=self.content,
                                   vimtype=[getattr(vim, self.params['object_type'])],
                                   name=None,
                                   first=False)
            found_obj = [obj for obj in all_objects if moid == obj._moId]
            self.current_obj = found_obj[0] if found_obj else None

        else:
            self.current_obj = find_obj(content=self.content,
                                        vimtype=[getattr(vim, self.params['object_type'])],
                                        name=self.params['object_name'])

        if self.current_obj is None:
            self.module.fail_json(
                msg="Specified object %s of type %s was not found."
                % (self.params['object_name'] or self.params['object_moid'], self.params['object_type'])
            )
        if self.params['object_type'] == 'DistributedVirtualSwitch':
            msg = "You are applying permissions to a Distributed vSwitch. " \
                  "This will probably fail, since Distributed vSwitches inherits permissions " \
                  "from the datacenter or a folder level. " \
                  "Define permissions on the datacenter or the folder containing the switch."
            self.module.warn(msg)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            role=dict(required=True, type='str'),
            object_name=dict(required=False, type='str'),
            object_moid=dict(required=False, type='str'),
            object_type=dict(
                type='str',
                default='Folder',
                choices=[
                    'Folder',
                    'VirtualMachine',
                    'Datacenter',
                    'ResourcePool',
                    'Datastore',
                    'Network',
                    'HostSystem',
                    'ComputeResource',
                    'ClusterComputeResource',
                    'DistributedVirtualSwitch',
                ],
            ),
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
            ['principal', 'group'],
            ['object_name', 'object_moid']
        ],
        required_one_of=[
            ['principal', 'group'],
            ['object_name', 'object_moid']
        ],
    )

    vmware_object_permission = VMwareObjectRolePermission(module)
    vmware_object_permission.process_state()


if __name__ == '__main__':
    main()
