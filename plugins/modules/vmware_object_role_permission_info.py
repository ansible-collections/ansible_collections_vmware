#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Derek Rushing <derek.rushing@geekops.com>
# Copyright: (c) 2018, VMware, Inc.
# Copyright: (c) 2021, Ansible Project
# Copyright: (c) 2021, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: vmware_object_role_permission_info
short_description: Gather information about object's permissions
description: This module can be used to gather object permissions on the given VMware object.
author:
- Abhijeet Kasurde (@Akasurde)
notes:
    - The ESXi or vCenter login user must have the appropriate rights to administer permissions.
    - Supports check mode.
options:
  principal:
    description:
    - The optional name of an entity, such as a user, assigned permissions on an object.
    - If provided, actual permissions on the specified object are returned for the principal, instead of roles.
    type: str
    required: false
  object_name:
    description:
    - The object name to assigned permission.
    - Mutually exclusive with O(moid).
    type: str
  object_type:
    description:
    - The object type being targeted.
    default: 'Folder'
    choices: ['Folder', 'VirtualMachine', 'Datacenter', 'ResourcePool',
              'Datastore', 'Network', 'HostSystem', 'ComputeResource',
              'ClusterComputeResource', 'DistributedVirtualSwitch',
              'DistributedVirtualPortgroup', 'StoragePod']
    type: str
  moid:
    description:
    - Managed object ID for the given object.
    - Mutually exclusive with O(object_name).
    aliases: ['object_moid']
    type: 'str'
extends_documentation_fragment:
- community.vmware.vmware.documentation
"""

EXAMPLES = r"""
- name: Gather role information about Datastore
  community.vmware.vmware_object_role_permission_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: false
    object_name: ds_200
    object_type: Datastore

- name: Gather permissions on Datastore for a User
  community.vmware.vmware_object_role_permission_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: false
    principal: some.user@company.com
    object_name: ds_200
    object_type: Datastore
"""

RETURN = r"""
permission_info:
    description: information about object's permission
    returned: always
    type: list
    sample: [
        {
            "principal": "VSPHERE.LOCAL\\vpxd-extension-12e0b667-892c-4694-8a5e-f13147e45dbd",
            "propagate": true,
            "role_id": -1,
            "role_name": "Admin"
        }
    ]
"""

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import (
    PyVmomi,
    vmware_argument_spec,
    find_obj,
)


class VMwareObjectRolePermission(PyVmomi):
    def __init__(self, module):
        super(VMwareObjectRolePermission, self).__init__(module)
        self.module = module
        self.params = module.params
        self.role_list = {}
        self.auth_manager = self.content.authorizationManager

        self.principal = self.params.get('principal')
        self.get_object()
        self.get_perms()
        self.populate_role_list()
        self.populate_permission_list()

    def populate_permission_list(self):
        results = []
        if self.principal is None:
            for permission in self.current_perms:
                results.append(
                    {
                        "principal": permission.principal,
                        "role_name": self.role_list.get(permission.roleId, ""),
                        "role_id": permission.roleId,
                        "propagate": permission.propagate,
                    }
                )
        else:
            results = self.to_json(self.current_perms)
        self.module.exit_json(changed=False, permission_info=results)

    def populate_role_list(self):
        user_friendly_role_names = {
            "Admin": ["Administrator"],
            "ReadOnly": ["Read-Only"],
            "com.vmware.Content.Admin": [
                "Content library administrator (sample)",
                "Content library administrator",
            ],
            "NoCryptoAdmin": ["No cryptography administrator"],
            "NoAccess": ["No access"],
            "VirtualMachinePowerUser": [
                "Virtual machine power user (sample)",
                "Virtual machine power user",
            ],
            "VirtualMachineUser": [
                "Virtual machine user (sample)",
                "Virtual machine user",
            ],
            "ResourcePoolAdministrator": [
                "Resource pool administrator (sample)",
                "Resource pool administrator",
            ],
            "VMwareConsolidatedBackupUser": [
                "VMware Consolidated Backup user (sample)",
                "VMware Consolidated Backup user",
            ],
            "DatastoreConsumer": ["Datastore consumer (sample)", "Datastore consumer"],
            "NetworkConsumer": [
                "Network administrator (sample)",
                "Network administrator",
            ],
            "VirtualMachineConsoleUser": ["Virtual Machine console user"],
            "InventoryService.Tagging.TaggingAdmin": ["Tagging Admin"],
        }
        for role in self.content.authorizationManager.roleList:
            self.role_list[role.roleId] = role.name
            if user_friendly_role_names.get(role.name):
                for role_name in user_friendly_role_names[role.name]:
                    self.role_list[role.roleId] = role_name

    def get_perms(self):
        if self.principal is None:
            self.current_perms = self.auth_manager.RetrieveEntityPermissions(
                self.current_obj, True
            )
        else:
            moid_list = []
            moid_list.append(self.current_obj)
            self.current_perms = self.auth_manager.FetchUserPrivilegeOnEntities(
                moid_list, self.principal
            )

    def get_object(self):
        # find_obj doesn't include rootFolder
        if (
            self.params["object_type"] == "Folder" and self.params["object_name"] == "rootFolder"
        ):
            self.current_obj = self.content.rootFolder
            return

        vim_type = None
        try:
            vim_type = getattr(vim, self.params["object_type"])
        except AttributeError:
            pass
        if not vim_type:
            self.module.fail_json(
                msg="Object type %s is not valid." % self.params["object_type"]
            )

        msg = "Specified object "
        if "moid" in self.params and self.params["moid"]:
            self.current_obj = vim_type(self.params["moid"], self.si._stub)
            msg += "with moid %s of type %s" % (
                self.params["moid"],
                self.params["object_type"],
            )
        elif "object_name" in self.params and self.params["object_name"]:
            self.current_obj = find_obj(
                content=self.content,
                vimtype=[vim_type],
                name=self.params["object_name"],
            )
            msg = "%s of type %s " % (
                self.params["object_name"],
                self.params["object_type"],
            )

        if self.current_obj is None:
            msg += "was not found"
            self.module.fail_json(msg=msg)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            principal=dict(
                type="str",
                required=False
            ),
            object_name=dict(type="str"),
            object_type=dict(
                type="str",
                default="Folder",
                choices=[
                    "Folder",
                    "VirtualMachine",
                    "Datacenter",
                    "ResourcePool",
                    "Datastore",
                    "Network",
                    "HostSystem",
                    "ComputeResource",
                    "ClusterComputeResource",
                    "DistributedVirtualSwitch",
                    "DistributedVirtualPortgroup",
                    "StoragePod",
                ],
            ),
            moid=dict(
                type="str",
                aliases=["object_moid"],
            ),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ["object_name", "moid"],
        ],
        mutually_exclusive=[
            ["object_name", "moid"],
        ],
    )

    VMwareObjectRolePermission(module)


if __name__ == "__main__":
    main()
