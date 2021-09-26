#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, sky-joker
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
module: vmware_vcenter_settings_info
short_description: Gather info vCenter settings
description:
  - This module can be used to gather information about vCenter settings.
author:
  - sky-joker (@sky-joker)
requirements:
  - python >= 2.7
  - PyVmomi
options:
  schema:
    description:
      - Specify the output schema desired.
      - The 'summary' output schema is the legacy output from the module.
      - The 'vsphere' output schema is the vSphere API class definition which requires pyvmomi>6.7.1.
    choices: ['summary', 'vsphere']
    default: 'summary'
    type: str
  properties:
    description:
      - Specify the properties to retrieve.
      - 'Example:'
      - '   properties: ['
      - '      "config.workflow.port"'
      - '   ]'
      - Only valid when C(schema) is C(vsphere).
    type: list
    elements: str
extends_documentation_fragment:
  - community.vmware.vmware.documentation
"""

EXAMPLES = r"""
- name: "Gather info about vCenter settings"
  community.vmware.vmware_vcenter_settings_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
  register: vcenter_settings_info

- name: "Gather some info from vCenter using the vSphere API output schema"
  community.vmware.vmware_vcenter_settings_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    schema: vsphere
    properties:
      - config.workflow.port
  register: vcenter_settings_info_vsphere_api
"""

RETURN = r"""
vcenter_config_info:
  description: dict of vCenter settings
  returned: success
  type: dict
  sample: |
    {
        "db_event_cleanup_previous": true,
        "db_event_retention_previous": 30,
        "db_max_connections_previous": 50,
        "db_task_cleanup_previous": true,
        "db_task_retention_previous": 30,
        "directory_query_limit_previous": true,
        "directory_query_limit_size_previous": 5000,
        "directory_timeout_previous": 60,
        "directory_validation_period_previous": 1440,
        "directory_validation_previous": true,
        "logging_options_previous": "info",
        "mail_sender_previous": "",
        "mail_server_previous": "",
        "runtime_managed_address_previous": "",
        "runtime_server_name_previous": "vcenter.local",
        "runtime_unique_id_previous": 48,
        "snmp_1_community_previous": "public",
        "snmp_1_enabled_previous": true,
        "snmp_1_url_previous": "localhost",
        "snmp_2_community_previous": "",
        "snmp_2_enabled_previous": false,
        "snmp_2_url_previous": "",
        "snmp_3_community_previous": "",
        "snmp_3_enabled_previous": false,
        "snmp_3_url_previous": "",
        "snmp_4_community_previous": "",
        "snmp_4_enabled_previous": false,
        "snmp_4_url_previous": "",
        "snmp_receiver_1_port_previous": 162,
        "snmp_receiver_2_port_previous": 162,
        "snmp_receiver_3_port_previous": 162,
        "snmp_receiver_4_port_previous": 162,
        "timeout_long_operations_previous": 120,
        "timeout_normal_operations_previous": 30
    }
"""

from ansible_collections.community.vmware.plugins.module_utils.vmware import (
    PyVmomi,
    vmware_argument_spec,
)
from ansible.module_utils.basic import AnsibleModule


class VmwareVcenterSettingsInfo(PyVmomi):
    def __init__(self, module):
        super(VmwareVcenterSettingsInfo, self).__init__(module)
        self.schema = self.params["schema"]
        self.properties = self.params["properties"]

        if not self.is_vcenter():
            self.module.fail_json(msg="You have to connect to a vCenter server!")

    def ensure(self):
        result = {}
        exists_vcenter_config = {}
        option_manager = self.content.setting

        for setting in option_manager.setting:
            exists_vcenter_config[setting.key] = setting.value

        if self.schema == "summary":
            common_name_value_map = {
                # Database
                "VirtualCenter.MaxDBConnection": "db_max_connections_previous",
                "task.maxAgeEnabled": "db_task_cleanup_previous",
                "task.maxAge": "db_task_retention_previous",
                "event.maxAgeEnabled": "db_event_cleanup_previous",
                "event.maxAge": "db_event_retention_previous",
                # Runtime settings
                "instance.id": "runtime_unique_id_previous",
                "VirtualCenter.ManagedIP": "runtime_managed_address_previous",
                "VirtualCenter.InstanceName": "runtime_server_name_previous",
                # User directory
                "ads.timeout": "directory_timeout_previous",
                "ads.maxFetchEnabled": "directory_query_limit_previous",
                "ads.maxFetch": "directory_query_limit_size_previous",
                "ads.checkIntervalEnabled": "directory_validation_previous",
                "ads.checkInterval": "directory_validation_period_previous",
                # Mail
                "mail.smtp.server": "mail_server_previous",
                "mail.sender": "mail_sender_previous",
                # SNMP receivers - SNMP receiver #1
                "snmp.receiver.1.enabled": "snmp_1_enabled_previous",
                "snmp.receiver.1.name": "snmp_1_url_previous",
                "snmp.receiver.1.port": "snmp_receiver_1_port_previous",
                "snmp.receiver.1.community": "snmp_1_community_previous",
                # SNMP receivers - SNMP receiver #2
                "snmp.receiver.2.enabled": "snmp_2_enabled_previous",
                "snmp.receiver.2.name": "snmp_2_url_previous",
                "snmp.receiver.2.port": "snmp_receiver_2_port_previous",
                "snmp.receiver.2.community": "snmp_2_community_previous",
                # SNMP receivers - SNMP receiver #3
                "snmp.receiver.3.enabled": "snmp_3_enabled_previous",
                "snmp.receiver.3.name": "snmp_3_url_previous",
                "snmp.receiver.3.port": "snmp_receiver_3_port_previous",
                "snmp.receiver.3.community": "snmp_3_community_previous",
                # SNMP receivers - SNMP receiver #4
                "snmp.receiver.4.enabled": "snmp_4_enabled_previous",
                "snmp.receiver.4.name": "snmp_4_url_previous",
                "snmp.receiver.4.port": "snmp_receiver_4_port_previous",
                "snmp.receiver.4.community": "snmp_4_community_previous",
                # Timeout settings
                "client.timeout.normal": "timeout_normal_operations_previous",
                "client.timeout.long": "timeout_long_operations_previous",
                # Logging settings
                "log.level": "logging_options_previous",
            }

            for key, value in common_name_value_map.items():
                if key in exists_vcenter_config:
                    result[value] = setting.value
        else:
            if self.properties:
                for property in self.properties:
                    if property in exists_vcenter_config:
                        result[property] = exists_vcenter_config[property]
                    else:
                        self.module.fail_json(msg="Propety '%s' not found" % property)
            else:
                for property in exists_vcenter_config.keys():
                    result[property] = exists_vcenter_config[property]

        self.module.exit_json(changed=False, vcenter_config_info=result)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        schema=dict(type="str", choices=["summary", "vsphere"], default="summary"),
        properties=dict(type="list", elements="str"),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    vmware_vcenter_settings_info = VmwareVcenterSettingsInfo(module)
    vmware_vcenter_settings_info.ensure()


if __name__ == "__main__":
    main()
