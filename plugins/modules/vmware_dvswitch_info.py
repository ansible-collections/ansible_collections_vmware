#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, sky-joker
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_dvswitch_info
short_description: Gathers info dvswitch configurations
description:
    - This module can be used to gather information about dvswitch configurations.
author:
    - sky-joker (@sky-joker)
options:
    folder:
      description:
        - Specify a folder location of dvswitch to gather information from.
        - 'Examples:'
        - '   folder: /datacenter1/network'
        - '   folder: datacenter1/network'
        - '   folder: /datacenter1/network/folder1'
        - '   folder: datacenter1/network/folder1'
        - '   folder: /folder1/datacenter1/network'
        - '   folder: folder1/datacenter1/network'
        - '   folder: /folder1/datacenter1/network/folder2'
      required: false
      type: str
    switch_name:
      description:
        - Name of a dvswitch to look for.
        - If O(switch_name) not specified gather all dvswitch information.
      aliases: ['switch', 'dvswitch']
      required: false
      type: str
    schema:
      description:
        - Specify the output schema desired.
        - The 'summary' output schema is the legacy output from the module
        - The 'vsphere' output schema is the vSphere API class definition
      choices: ['summary', 'vsphere']
      default: 'summary'
      type: str
    properties:
      description:
        - Specify the properties to retrieve.
        - If not specified, all properties are retrieved (deeply).
        - Results are returned in a structure identical to the vsphere API.
        - 'Example:'
        - '   properties: ['
        - '      "summary.name",'
        - '      "summary.numPorts",'
        - '      "config.maxMtu",'
        - '      "overallStatus"'
        - '   ]'
        - Only valid when O(schema=vsphere).
      type: list
      elements: str
      required: false
extends_documentation_fragment:
    - community.vmware.vmware.documentation
'''

EXAMPLES = r'''
- name: Gather all registered dvswitch
  community.vmware.vmware_dvswitch_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
  delegate_to: localhost
  register: dvswitch_info

- name: Gather info about specific dvswitch
  community.vmware.vmware_dvswitch_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    switch_name: DVSwitch01
  delegate_to: localhost
  register: dvswitch_info

- name: Gather info from folder about specific dvswitch
  community.vmware.vmware_dvswitch_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    folder: /datacenter1/network/F01
    switch_name: DVSwitch02
  delegate_to: localhost
  register: dvswitch_info

- name: Gather some info from a dvswitch using the vSphere API output schema
  community.vmware.vmware_dvswitch_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    schema: vsphere
    properties:
      - summary.name
      - summary.numPorts
      - config.maxMtu
      - overallStatus
    switch_name: DVSwitch01
  register: dvswitch_info
'''

RETURN = r'''
distributed_virtual_switches:
    description: list of dictionary of dvswitch and their information
    returned: always
    type: list
    sample:
      [
        {
          "configure": {
            "folder": "network",
            "hosts": [
              "esxi-test-02.local",
              "esxi-test-01.local"
            ],
            "settings": {
              "healthCheck": {
                "TeamingHealthCheckConfig": false,
                "VlanMtuHealthCheckConfig": false
              },
              "netflow": {
                "activeFlowTimeout": 60,
                "collectorIpAddress": "",
                "collectorPort": 0,
                "idleFlowTimeout": 15,
                "internalFlowsOnly": false,
                "observationDomainId": 0,
                "samplingRate": 0,
                "switchIpAddress": null
              },
              "properties": {
                "administratorContact": {
                  "contact": null,
                  "name": null
                },
                "advanced": {
                  "maxMtu": 1500,
                  "multicastFilteringMode": "legacyFiltering"
                },
                "discoveryProtocol": {
                  "operation": "listen",
                  "protocol": "cdp"
                },
                "general": {
                  "ioControl": true,
                  "name": "DVSwitch01",
                  "numPorts": 10,
                  "numUplinks": 1,
                  "vendor": "VMware, Inc.",
                  "version": "6.6.0"
                }
              },
              "privateVlan": []
            }
          },
          "uuid": "50 30 99 9c a7 60 8a 4f-05 9f e7 b5 da df 8f 17"
        }
      ]
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi, vmware_argument_spec, find_object_by_name
from ansible.module_utils.basic import AnsibleModule


class VMwareDvSwitchInfoManager(PyVmomi):
    def __init__(self, module):
        super(VMwareDvSwitchInfoManager, self).__init__(module)
        self.folder = self.params['folder']
        self.switch_name = self.params['switch_name']

        folder_obj = None
        if self.folder:
            folder_obj = self.content.searchIndex.FindByInventoryPath(self.folder)
            if not folder_obj:
                self.module.fail_json(msg="Failed to find folder specified by %s" % self.folder)

        if self.switch_name:
            self.switch_objs = [find_object_by_name(self.content, self.switch_name, vim.DistributedVirtualSwitch, folder_obj)]
            if None in self.switch_objs:
                self.switch_objs = None
        else:
            self.switch_objs = self.find_obj([vim.DistributedVirtualSwitch], '', first=False)

    def all_info(self):
        distributed_virtual_switches = []
        if not self.switch_objs:
            self.module.exit_json(changed=False, distributed_virtual_switches=distributed_virtual_switches)

        for switch_obj in self.switch_objs:
            pvlans = []
            if switch_obj.config.pvlanConfig:
                for vlan in switch_obj.config.pvlanConfig:
                    pvlans.append({
                        'primaryVlanId': vlan.primaryVlanId,
                        'secondaryVlanId': vlan.secondaryVlanId,
                        'pvlanType': vlan.pvlanType
                    })

            host_members = []
            if switch_obj.summary.hostMember:
                for host in switch_obj.summary.hostMember:
                    host_members.append(host.name)

            health_check = {}
            for health_config in switch_obj.config.healthCheckConfig:
                if isinstance(health_config, vim.dvs.VmwareDistributedVirtualSwitch.VlanMtuHealthCheckConfig):
                    health_check['VlanMtuHealthCheckConfig'] = health_config.enable
                elif isinstance(health_config, vim.dvs.VmwareDistributedVirtualSwitch.TeamingHealthCheckConfig):
                    health_check['TeamingHealthCheckConfig'] = health_config.enable

            distributed_virtual_switches.append({
                'configure': {
                    'settings': {
                        'properties': {
                            'general': {
                                'name': switch_obj.name,
                                'vendor': switch_obj.config.productInfo.vendor,
                                'version': switch_obj.config.productInfo.version,
                                'numUplinks': len(switch_obj.config.uplinkPortPolicy.uplinkPortName),
                                'numPorts': switch_obj.summary.numPorts,
                                'ioControl': switch_obj.config.networkResourceManagementEnabled,
                            },
                            'advanced': {
                                'maxMtu': switch_obj.config.maxMtu,
                                'multicastFilteringMode': switch_obj.config.multicastFilteringMode,
                            },
                            'discoveryProtocol': {
                                'protocol': switch_obj.config.linkDiscoveryProtocolConfig.protocol,
                                'operation': switch_obj.config.linkDiscoveryProtocolConfig.operation,
                            },
                            'administratorContact': {
                                'name': switch_obj.config.contact.name,
                                'contact': switch_obj.config.contact.contact
                            }
                        },
                        'privateVlan': pvlans,
                        'netflow': {
                            'switchIpAddress': switch_obj.config.switchIpAddress,
                            'collectorIpAddress': switch_obj.config.ipfixConfig.collectorIpAddress,
                            'collectorPort': switch_obj.config.ipfixConfig.collectorPort,
                            'observationDomainId': switch_obj.config.ipfixConfig.observationDomainId,
                            'activeFlowTimeout': switch_obj.config.ipfixConfig.activeFlowTimeout,
                            'idleFlowTimeout': switch_obj.config.ipfixConfig.idleFlowTimeout,
                            'samplingRate': switch_obj.config.ipfixConfig.samplingRate,
                            'internalFlowsOnly': switch_obj.config.ipfixConfig.internalFlowsOnly
                        },
                        'healthCheck': health_check
                    },
                    'hosts': host_members,
                    'folder': switch_obj.parent.name,
                    'name': switch_obj.name,
                },
                'uuid': switch_obj.uuid,
            })

        self.module.exit_json(changed=False, distributed_virtual_switches=distributed_virtual_switches)

    def properties_facts(self):
        distributed_virtual_switches = []
        for switch_obj in self.switch_objs:
            distributed_virtual_switches.append(self.to_json(switch_obj, self.params.get('properties')))

        self.module.exit_json(changed=False, distributed_virtual_switches=distributed_virtual_switches)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        folder=dict(type='str', required=False),
        switch_name=dict(type='str', required=False, aliases=['switch', 'dvswitch']),
        schema=dict(type='str', choices=['summary', 'vsphere'], default='summary'),
        properties=dict(type='list', required=False, elements='str')
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    vmware_dvswitch_info_mgr = VMwareDvSwitchInfoManager(module)

    if module.params['schema'] == 'summary':
        vmware_dvswitch_info_mgr.all_info()
    else:
        vmware_dvswitch_info_mgr.properties_facts()


if __name__ == "__main__":
    main()
