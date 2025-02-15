#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Marius Rieder <marius.rieder@scs.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_host_access_info
short_description: Gathers info about an ESXi host's access configuration information
description:
- This module can be used to gather information about an ESXi host's access configuration information when ESXi hostname or Cluster name is given.
author:
  - Marius Rieder (@jiuka)
notes:
- Tested on vSphere 7.0
requirements:
- python >= 3.6
- PyVmomi
options:
  cluster_name:
    description:
    - Name of the cluster from which the ESXi host belong to.
    - If C(esxi_hostname) is not given, this parameter is required.
    type: str
  esxi_hostname:
    description:
    - ESXi hostname to gather information from.
    - If C(cluster_name) is not given, this parameter is required.
    type: str
extends_documentation_fragment:
- community.vmware.vmware.documentation
'''

EXAMPLES = r'''
- name: Gather access info about all ESXi Host in given Cluster
  community.vmware.vmware_host_access_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: cluster_name
  delegate_to: localhost

- name: Gather access info about ESXi Host
  community.vmware.vmware_host_access_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
  delegate_to: localhost
'''

RETURN = r'''
hosts_access_info:
    description: metadata about host's access configuration
    returned: on success
    type: dict
    sample: {
            "esxi_hostname_0001": {
                "lockdown_mode": "disabled",
                "lockdown_exceptions": [],
                "access": {
                    "dcui": {"access": "admin", "group": false},
                    "root": {"access": "admin", "group": false},
                    "vpxuser": {"access": "admin", "group": false}
                }
            }
        }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import vmware_argument_spec, PyVmomi


class VmwareHostAccessInfo(PyVmomi):
    LOCKDOWN_MODE_MAP = {
        'lockdownDisabled': 'disabled',
        'lockdownNormal': 'normal',
        'lockdownStrict': 'strict'
    }
    ACCESS_MODE_MAP = {
        'accessAdmin': 'admin',
        'accessNoAccess': 'no-access',
        'accessReadOnly': 'read-only',
    }

    def __init__(self, module):
        super(VmwareHostAccessInfo, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)

    def gather_host_access_controll_entries_info(self, access_mgr):
        access = {}
        for ace in access_mgr.RetrieveHostAccessControlEntries():
            access[ace.principal] = dict(
                access=self.ACCESS_MODE_MAP.get(ace.accessMode, ace.accessMode),
                group=ace.group,
            )
        return access

    def gather_host_access_info(self):
        hosts_access_info = dict()
        for host in self.hosts:
            access_mgr = host.configManager.hostAccessManager

            if access_mgr:
                hosts_access_info[host.name] = dict(
                    lockdown_mode=self.LOCKDOWN_MODE_MAP.get(access_mgr.lockdownMode, access_mgr.lockdownMode),
                    lockdown_exceptions=[s for s in access_mgr.QueryLockdownExceptions()],
                    access=self.gather_host_access_controll_entries_info(access_mgr)
                )
        return hosts_access_info


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str', required=False),
        esxi_hostname=dict(type='str', required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ],
        supports_check_mode=True
    )

    vmware_host_access = VmwareHostAccessInfo(module)
    module.exit_json(changed=False, hosts_access_info=vmware_host_access.gather_host_access_info())


if __name__ == "__main__":
    main()
