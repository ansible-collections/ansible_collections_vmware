#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Marius Rieder <marius.rieder@scs.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
module: vmware_host_access_manager
short_description: Manage permissions and lockdown of ESXi hosts.
author:
  - Marius Rieder (@jiuka)
description:
  - This module can grant and revoke permissions on ESXi hosts.
  - This module can add and remove users from the lockdown exception list on ESXi host.
  - This module can set the lockdown mode on ESXi host.
requirements:
  - python >= 3.6
  - PyVmomi
version_added: '2.3.0'
options:
  esxi_hostname:
    description:
    - Name of the host system to work with.
    - This parameter is required if C(cluster_name) is not specified and you connect to a vCenter.
    - Cannot be used when you connect directly to an ESXi host.
    type: str
  cluster_name:
    description:
    - Name of the cluster from which all host systems will be used.
    - This parameter is required if C(esxi_hostname) is not specified and you connect to a vCenter.
    - Cannot be used when you connect directly to an ESXi host.
    type: str
  user_name:
    description:
      - Name of the local user to grant/revoke permissions of.
    type: str
    required: false
  group_name:
    description:
      - Name of the local user to grant/revoke permissions of.
    type: str
    required: false
  access:
    description:
      - Type of access to grant.
      - C(admin), C(no-access) oder C(readonly) are valid options.
    type: str
    choices:
      - admin
      - no-access
      - read-only
    aliases: [ access_mode ]
    required: False
  lockdown_mode:
    description:
      - Lockdown mode to set.
      - C(disabled), C(normal) oder C(strict) are valid options.
    type: str
    choices:
      - disabled
      - normal
      - strict
    aliases: [ lockdown ]
    required: False
  lockdown_exceptions:
    description:
      - List of users to add or remove from the lockdown exception list.
    type: list
    elements: str
    required: False
  state:
    description:
      - If set to C(present), grant permissions or add users to lockdown exceptions list.
      - If set to C(absent), revoke permissions or remove users to lockdown exceptions list.
    default: present
    type: str
    choices:
      - present
      - absent
extends_documentation_fragment:
  - community.vmware.vmware.documentation
'''

EXAMPLES = r'''
- name: Disable lockdown mode on ESXi host
  community.vmware.vmware_host_access_manager:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: false
    esxi_hostname: "{{ esxi1 }}"
    lockdown: disabled

- name: Add user to lockdown exception list on ESXi host
  community.vmware.vmware_host_access_manager:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: false
    esxi_hostname: "{{ esxi1 }}"
    lockdown_exceptions:
      - example
    state: present

- name: Remove user to lockdown exception list on ESXi host
  community.vmware.vmware_host_access_manager:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: false
    esxi_hostname: "{{ esxi1 }}"
    lockdown_exceptions:
      - example
    state: absent

- name: Grant ReadOnly permission on ESXi host
  community.vmware.vmware_host_access_manager:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: false
    esxi_hostname: "{{ esxi1 }}"
    user_name: example
    access: ReadOnly
    state: present

- name: Revoke permission on ESXi host
  community.vmware.vmware_host_access_manager:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: false
    esxi_hostname: "{{ esxi1 }}"
    user_name: example
    state: absent
'''

RETURN = r'''
msg:
  description: The executed result for the module.
  returned: always
  type: str
  sample: >-
    {
        "msg": "Granted permission 'read-only' to 'root' on 'esxi_hostname_0001'"
    }
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi, vmware_argument_spec


class VmwareHostAccessManager(PyVmomi):
    ACCESS_MODE_MAP = {
        'admin': 'accessAdmin',
        'no-access': 'accessNoAccess',
        'read-only': 'accessReadOnly',
        None: 'accessNone'
    }
    LOCKDOWN_MODE_MAP = {
        'disabled': 'lockdownDisabled',
        'normal': 'lockdownNormal',
        'strict': 'lockdownStrict'
    }

    def __init__(self, module):
        super(VmwareHostAccessManager, self).__init__(module)
        self.principal = module.params["user_name"] or module.params["group_name"]
        self.group = module.params["user_name"] is None
        self.access_mode = module.params["access"]
        self.lockdown_mode = module.params["lockdown_mode"]
        self.lockdown_exceptions = module.params["lockdown_exceptions"]
        self.state = module.params["state"]

        esxi_hostname = self.params['esxi_hostname']
        cluster = self.params['cluster_name']
        self.hosts = self.get_all_host_objs(cluster_name=cluster, esxi_host_name=esxi_hostname)
        if not self.hosts:
            self.module.fail_json(msg="Failed to find host system with given configuration.")

    def get_access_controll_entry(self, access_mgr):
        """
        Search the specified access controll entry from ESXi

        Returns: searched access crontroll entry if found, else None
        """
        for ace in access_mgr.RetrieveHostAccessControlEntries():
            if ace.principal == self.principal and ace.group == self.group:
                return {v: k for k, v in self.ACCESS_MODE_MAP.items()}.get(ace.accessMode)
        return None

    def update_access_controll_entry(self, access_mgr, access_mode):
        """
        Update the access controll entry
        """
        try:
            access_mgr.ChangeAccessMode(self.principal, self.group, self.ACCESS_MODE_MAP[access_mode])
        except vim.fault.UserNotFound as user_not_found:
            self.module.fail_json(msg="Failed to update permission for '%s' due to user"
                                      " not found : %s" % (self.principal, to_native(user_not_found.msg)))
        except Exception as generic_exc:
            self.module.fail_json(msg="Failed to add access: %s" % (to_native(generic_exc)))

    def get_lockdown_mode(self, access_mgr):
        """
        Get the lockdown mode from ESXi

        Returns: Lockdown mode as string
        """
        lockdown_mode = access_mgr.lockdownMode
        return {v: k for k, v in self.LOCKDOWN_MODE_MAP.items()}.get(lockdown_mode)

    def execute_access_controll_entry(self, host, access_mgr):
        access_mode_current = self.get_access_controll_entry(access_mgr)

        if self.state == "present":
            if access_mode_current != self.access_mode:
                self.result['changed'] = True
                if self.module.check_mode:
                    self.result['msg'].append("The permission '%s' will be granted to '%s' on '%s'." %
                                              (self.access_mode, self.principal, host.name))
                else:
                    self.result['msg'].append("Granted permission '%s' to '%s' on '%s'" %
                                              (self.access_mode, self.principal, host.name))
                    self.update_access_controll_entry(access_mgr, self.access_mode)

                self.result['result'][host.name]['access'] = {self.principal: dict(group=self.group, access=self.access_mode)}
                if self.module._diff:
                    self.result['diff']['before'][host.name]['access'] = [dict(principal=self.principal, group=self.group, access=access_mode_current)] if access_mode_current else []
                    self.result['diff']['after'][host.name]['access'] = [dict(principal=self.principal, group=self.group, access=self.access_mode)]
        elif self.state == "absent" and access_mode_current:
            self.result['changed'] = True
            if self.module.check_mode:
                self.result['msg'].append("The permission '%s' will be revoked from '%s' on '%s'." %
                                          (access_mode_current, self.principal, host.name))
            else:
                self.result['msg'].append("Revoked permission '%s' from '%s' on '%s'" %
                                          (access_mode_current, self.principal, host.name))
                self.update_access_controll_entry(access_mgr, None)

            if self.module._diff:
                self.result['diff']['before'][host.name]['access'] = [dict(principal=self.principal, group=self.group, access=access_mode_current)]
                self.result['diff']['after'][host.name]['access'] = []

    def execute_lockdown_exceptions(self, host, access_mgr):
        exceptions = [s for s in access_mgr.QueryLockdownExceptions()]
        exceptions_current = exceptions.copy()

        if self.state == "present":
            for user in self.lockdown_exceptions:
                if user not in exceptions:
                    exceptions.append(user)
                    self.result['changed'] = True
        elif self.state == "absent":
            for user in self.lockdown_exceptions:
                if user in exceptions:
                    exceptions.remove(user)
                    self.result['changed'] = True

        if self.result['changed']:
            if self.module.check_mode:
                self.result['msg'].append("Lockdown exceptions for '%s' would be updated" % (host.name))
            else:
                try:
                    access_mgr.UpdateLockdownExceptions(exceptions)
                except vim.fault.UserNotFound as user_not_found:
                    self.module.fail_json(msg="Failed to update lockdown exceptions due to user"
                                              " not found : %s" % (to_native(user_not_found.msg)))
                except Exception as generic_exc:
                    self.module.fail_json(msg="Failed to update lockdown exceptions due to"
                                              " generic exception : %s" % (to_native(generic_exc)))
                self.result['msg'].append("Updated Lockdown exceptions for '%s'" % (host.name))

            self.result['result'][host.name]['lockdown_exceptions'] = exceptions
            if self.module._diff:
                self.result['diff']['before'][host.name]['lockdown_exceptions'] = exceptions_current
                self.result['diff']['after'][host.name]['lockdown_exceptions'] = exceptions

    def execute_lockdown_mode(self, host, access_mgr):
        mode_current = self.get_lockdown_mode(access_mgr)

        if mode_current != self.lockdown_mode:
            self.result['changed'] = True
            if self.module.check_mode:
                self.result['msg'].append("Lockdown mode for '%s' would be set to '%s'" % (host.name, self.lockdown_mode))
            else:
                access_mgr.ChangeLockdownMode(self.LOCKDOWN_MODE_MAP(self.lockdown_mode))
                self.result['msg'].append("Updated Lockdown mode for '%s' to '%s'" % (host.name, self.lockdown_mode))

            self.result['result'][host.name]['lockdown'] = self.lockdown_mode
            if self.module._diff:
                self.result['diff']['before'][host.name]['lockdown_mode'] = mode_current
                self.result['diff']['after'][host.name]['lockdown_mode'] = self.lockdown_mode
        else:
            self.result['result'][host.name]['lockdown']

    def execute(self):
        self.result = dict(changed=False, msg=[], result={})
        if self.module._diff:
            self.result['diff'] = dict(before=dict(), after=dict())

        for host in self.hosts:

            self.result['result'][host.name] = {}
            if self.module._diff:
                self.result['diff']['before'][host.name] = {}
                self.result['diff']['after'][host.name] = {}

            host_access_mgr = host.configManager.hostAccessManager

            if self.principal:
                self.execute_access_controll_entry(host, host_access_mgr)

            if self.lockdown_exceptions:
                self.execute_lockdown_exceptions(host, host_access_mgr)

            if self.lockdown_mode:
                self.execute_lockdown_mode(host, host_access_mgr)

        self.result['msg'] = ", ".join(self.result['msg'])
        self.module.exit_json(**self.result)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str', required=False),
        esxi_hostname=dict(type='str', required=False),
        user_name=dict(type="str"),
        group_name=dict(type="str"),
        access=dict(type="str", aliases=["access_mode"], choices=["admin", "no-access", "read-only"]),
        lockdown_mode=dict(type="str", aliases=["lockdown"], choices=["disabled", "normal", "strict"]),
        lockdown_exceptions=dict(type="list", elements="str"),
        state=dict(type="str", default="present", choices=["present", "absent"])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['user_name', 'group_name', 'lockdown_mode', 'lockdown_exceptions'],
            ['cluster_name', 'esxi_hostname'],
        ],
        mutually_exclusive=[
            ['user_name', 'group_name', 'lockdown_mode', 'lockdown_exceptions']
        ],
        supports_check_mode=True,
    )
    vmware_host_access_manager = VmwareHostAccessManager(module)
    vmware_host_access_manager.execute()


if __name__ == "__main__":
    main()
