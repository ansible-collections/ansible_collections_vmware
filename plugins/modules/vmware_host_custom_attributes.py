#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_host_custom_attributes
short_description: Manage custom attributes from VMware for the given ESXi host
description:
    - This module can be used to add, remove and update custom attributes for the given ESXi host.
author:
    - Hunter Christain (@exp-hc)
    - Hannes Ebelt (@hannesebelt)
version_added: '1.11.0'
notes:
    - Tested on vSphere 6.7, 7.0
requirements:
    - PyVmomi
options:
   esxi_hostname:
     description:
     - Name of the ESXi host to work with.
     - This is a required parameter
     required: true
     type: str
   state:
     description:
     - The action to take.
     - If set to V(present), then custom attribute is added or updated.
     - If set to V(absent), then custom attribute is removed.
     default: 'present'
     choices: ['present', 'absent']
     type: str
   attributes:
     description:
     - A list of name and value of custom attributes that needs to be manage.
     - Value of custom attribute is not required and will be ignored, if O(state=absent).
     suboptions:
        name:
          description:
          - Name of the attribute.
          type: str
          required: true
        value:
          description:
          - Value of the attribute.
          type: str
          default: ''
     default: []
     type: list
     elements: dict
extends_documentation_fragment:
- community.vmware.vmware.documentation

'''

EXAMPLES = r'''
- name: Add ESXi host custom attributes
  community.vmware.vmware_host_custom_attributes:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    esxi_hostname: host1
    state: present
    attributes:
      - name: MyAttribute
        value: MyValue
  delegate_to: localhost
  register: attributes

- name: Remove ESXi host Attribute
  community.vmware.vmware_host_custom_attributes:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    esxi_hostname: host1
    state: absent
    attributes:
      - name: MyAttribute
  delegate_to: localhost
  register: attributes
'''

RETURN = r'''
custom_attributes:
    description: metadata about the ESXi host attributes
    returned: changed
    type: dict
    sample: {
        "mycustom": "my_custom_value",
        "mycustom_2": "my_custom_value_2",
        "sample_1": "sample_1_value",
        "sample_2": "sample_2_value",
        "sample_3": "sample_3_value"
    }
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi, vmware_argument_spec


class HostAttributeManager(PyVmomi):
    def __init__(self, module):
        super(HostAttributeManager, self).__init__(module)
        self.esxi_hostname = module.params.get('esxi_hostname')
        self.host = self.find_hostsystem_by_name(self.esxi_hostname)

    def set_custom_field(self, host, user_fields):
        result_fields = dict()
        change_list = list()
        changed = False

        for field in user_fields:
            field_key = self.check_exists(field['name'])
            found = False
            field_value = field.get('value', '')

            for k, v in [(x.name, v.value) for x in self.custom_field_mgr for v in host.customValue if x.key == v.key]:
                if k == field['name']:
                    found = True
                    if v != field_value:
                        if not self.module.check_mode:
                            self.content.customFieldsManager.SetField(entity=host, key=field_key.key, value=field_value)
                            result_fields[k] = field_value
                        change_list.append(True)
            if not found and field_value != "":
                if not field_key and not self.module.check_mode:
                    field_key = self.content.customFieldsManager.AddFieldDefinition(name=field['name'], moType=vim.HostSystem)
                change_list.append(True)
                if not self.module.check_mode:
                    self.content.customFieldsManager.SetField(entity=host, key=field_key.key, value=field_value)
                result_fields[field['name']] = field_value

        if any(change_list):
            changed = True

        return {'changed': changed, 'failed': False, 'custom_attributes': result_fields}

    def remove_custom_field(self, host, user_fields):
        result_fields = dict()
        change_list = list()
        changed = False

        for field in user_fields:
            field_key = self.check_exists(field['name'])
            for k, v in [(x.name, v.value) for x in self.custom_field_mgr for v in host.customValue if x.key == v.key]:
                if k == field['name']:
                    if not self.module.check_mode:
                        self.content.customFieldsManager.RemoveCustomFieldDef(key=field_key.key)
                    change_list.append(True)

        if any(change_list):
            changed = True

        return {'changed': changed, 'failed': False, 'custom_attributes': result_fields}

    def check_exists(self, field):
        for x in self.custom_field_mgr:
            # The custom attribute should be either global (managedObjectType == None) or host specific
            if x.managedObjectType in (None, vim.HostSystem) and x.name == field:
                return x
        return False


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        esxi_hostname=dict(type='str', required=True),
        state=dict(type='str', default='present',
                   choices=['absent', 'present']),
        attributes=dict(
            type='list',
            default=[],
            elements='dict',
            options=dict(
                name=dict(type='str', required=True),
                value=dict(type='str', default=''),
            )
        ),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    pyv = HostAttributeManager(module)
    results = {'changed': False, 'failed': False, 'instance': dict()}

    # Check if the virtual machine exists before continuing
    host = pyv.host

    if host:
        # host already exists
        if module.params['state'] == "present":
            results = pyv.set_custom_field(host, module.params['attributes'])
        elif module.params['state'] == "absent":
            results = pyv.remove_custom_field(host, module.params['attributes'])
        module.exit_json(**results)
    else:
        # host does not exists
        module.fail_json(msg="Unable to manage custom attributes for non-existing"
                             " host %s" % pyv.esxi_hostname)


if __name__ == '__main__':
    main()
