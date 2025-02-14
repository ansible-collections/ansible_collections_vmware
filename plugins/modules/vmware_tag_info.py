#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: vmware_tag_info
short_description: Manage VMware tag info
description:
- This module can be used to collect information about VMware tags.
- Tag feature is introduced in vSphere 6 version, so this module is not supported in the earlier versions of vSphere.
author:
- Abhijeet Kasurde (@Akasurde)
requirements:
- vSphere Automation SDK
options:
   tag_name:
     description:
     - Name of the tag.
     - If set, information of this tag will be returned.
     required: false
     type: str
   show_related_objects:
    description:
    - Objects related to the tag are shown if set to V(true).
    default: false
    type: bool
extends_documentation_fragment:
- community.vmware.vmware_rest_client.documentation

'''

EXAMPLES = r'''
- name: Get info about tags
  community.vmware.vmware_tag_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
  delegate_to: localhost

- name: Get info about one tag
  community.vmware.vmware_tag_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    tag_name: 'testTag'
  delegate_to: localhost

- name: Get related objects of one tag
  community.vmware.vmware_tag_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    tag_name: 'testTag'
    show_related_objects: true
  delegate_to: localhost

- name: Get category id from the given tag
  community.vmware.vmware_tag_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
  delegate_to: localhost
  register: tag_details
- debug:
    msg: "{{ tag_details.tag_facts['fedora_machines']['tag_category_id'] }}"

- name: Gather tag id from the given tag
  community.vmware.vmware_tag_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
  delegate_to: localhost
  register: tag_results
- set_fact:
    tag_id: "{{ item.tag_id }}"
  loop: "{{ tag_results.tag_info|json_query(query) }}"
  vars:
    query: "[?tag_name==`tag0001`]"
- debug: var=tag_id
'''

RETURN = r'''
tag_facts:
  description: dictionary of tag metadata
  returned: on success
  type: dict
  sample: {
        "Sample_Tag_0002": {
            "tag_category_id": "urn:vmomi:InventoryServiceCategory:6de17f28-7694-43ec-a783-d09c141819ae:GLOBAL",
            "tag_description": "Sample Description",
            "tag_id": "urn:vmomi:InventoryServiceTag:a141f212-0f82-4f05-8eb3-c49647c904c5:GLOBAL",
            "tag_used_by": [],
            "tag_association_objects": [
                {   "mobid": "vm-2625",
                    "type": "VirtualMachine",
                    "name": "testvm"
                }
            ]
        },
        "fedora_machines": {
            "tag_category_id": "urn:vmomi:InventoryServiceCategory:baa90bae-951b-4e87-af8c-be681a1ba30c:GLOBAL",
            "tag_description": "",
            "tag_id": "urn:vmomi:InventoryServiceTag:7d27d182-3ecd-4200-9d72-410cc6398a8a:GLOBAL",
            "tag_used_by": [],
            "tag_association_objects": [
                {   "mobid": "vm-2625",
                    "type": "VirtualMachine",
                    "name": "testvm"
                }
            ]
        },
        "ubuntu_machines": {
            "tag_category_id": "urn:vmomi:InventoryServiceCategory:89573410-29b4-4cac-87a4-127c084f3d50:GLOBAL",
            "tag_description": "",
            "tag_id": "urn:vmomi:InventoryServiceTag:7f3516d5-a750-4cb9-8610-6747eb39965d:GLOBAL",
            "tag_used_by": [],
            "tag_association_objects": [
                {   "mobid": "vm-2625",
                    "type": "VirtualMachine",
                    "name": "testvm"
                }
            ]
        }
    }

tag_info:
    description: list of tag metadata
    returned: on success
    type: list
    sample: [
        {   "tag_name": "Sample_Tag_0002",
            "tag_category_id": "urn:vmomi:InventoryServiceCategory:6de17f28-7694-43ec-a783-d09c141819ae:GLOBAL",
            "tag_description": "Sample Description",
            "tag_id": "urn:vmomi:InventoryServiceTag:a141f212-0f82-4f05-8eb3-c49647c904c5:GLOBAL",
            "tag_used_by": [],
            "tag_association_objects": [
                {   "mobid": "vm-2625",
                    "type": "VirtualMachine",
                    "name": "testvm"
                }
            ]
        },
        {   "tag_name": "Sample_Tag_0002",
            "tag_category_id": "urn:vmomi:InventoryServiceCategory:6de17f28-7694-43ec-a783-d09c141819ae:GLOBAL",
            "tag_description": "",
            "tag_id": "urn:vmomi:InventoryServiceTag:7d27d182-3ecd-4200-9d72-410cc6398a8a:GLOBAL",
            "tag_used_by": [],
            "tag_association_objects": [
                {   "mobid": "vm-2625",
                    "type": "VirtualMachine",
                    "name": "testvm"
                }
            ]
        },
        {   "tag_name": "ubuntu_machines",
            "tag_category_id": "urn:vmomi:InventoryServiceCategory:89573410-29b4-4cac-87a4-127c084f3d50:GLOBAL",
            "tag_description": "",
            "tag_id": "urn:vmomi:InventoryServiceTag:7f3516d5-a750-4cb9-8610-6747eb39965d:GLOBAL",
            "tag_used_by": [],
            "tag_association_objects": [
                {   "mobid": "vm-2625",
                    "type": "VirtualMachine",
                    "name": "testvm"
                }
            ]
        }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware_rest_client import VmwareRestClient
from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi


class VmTagInfoManager(VmwareRestClient):
    def __init__(self, module):
        """Constructor."""
        super(VmTagInfoManager, self).__init__(module)
        self.vmware_client = PyVmomi(self.module)

    def get_tags(self):
        if self.params.get('tag_name'):
            tag_list = self.get_one_tag()

        else:
            tag_list = self.get_all_tags()

        global_tag_info = list()
        # Backward compatability
        global_tags = dict()

        for tag_obj in tag_list:
            if self.params.get('show_related_objects'):
                tag_association_svc = self.api_client.tagging.TagAssociation
                associations = tag_association_svc.list_attached_objects(tag_id=tag_obj.id)

                association_list = list()
                for assoc in associations:
                    assoc_obj = self.vmware_client.find_obj_by_moid(object_type=assoc.type, moid=assoc.id)
                    association_list.append(dict(
                        mobid=assoc.id,
                        type=assoc.type,
                        name=assoc_obj.name
                    ))

                global_tags[tag_obj.name] = dict(
                    tag_description=tag_obj.description,
                    tag_used_by=tag_obj.used_by,
                    tag_category_id=tag_obj.category_id,
                    tag_id=tag_obj.id,
                    tag_association_objects=association_list
                )
                global_tag_info.append(dict(
                    tag_name=tag_obj.name,
                    tag_description=tag_obj.description,
                    tag_used_by=tag_obj.used_by,
                    tag_category_id=tag_obj.category_id,
                    tag_id=tag_obj.id,
                    tag_association_objects=association_list
                ))

            else:
                global_tags[tag_obj.name] = dict(
                    tag_description=tag_obj.description,
                    tag_used_by=tag_obj.used_by,
                    tag_category_id=tag_obj.category_id,
                    tag_id=tag_obj.id
                )
                global_tag_info.append(dict(
                    tag_name=tag_obj.name,
                    tag_description=tag_obj.description,
                    tag_used_by=tag_obj.used_by,
                    tag_category_id=tag_obj.category_id,
                    tag_id=tag_obj.id
                ))

        self.module.exit_json(
            changed=False,
            tag_facts=global_tags,
            tag_info=global_tag_info,
        )

    def get_one_tag(self):
        """
        Retrieve all tag information for one tag.
        """
        vmware_client = VmwareRestClient(self.module)
        tag_obj = vmware_client.get_tag_by_name(tag_name=self.params.get('tag_name'))

        return [tag_obj]

    def get_all_tags(self):
        """
        Retrieve all tag information.
        """
        tag_list = list()
        tag_service = self.api_client.tagging.Tag
        for tag in tag_service.list():
            tag_obj = tag_service.get(tag)
            tag_list.append(tag_obj)

        return tag_list


def main():
    argument_spec = VmwareRestClient.vmware_client_argument_spec()
    argument_spec.update(
        tag_name=dict(type='str'),
        show_related_objects=dict(type='bool', default=False),
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    vmware_tag_info = VmTagInfoManager(module)
    vmware_tag_info.get_tags()


if __name__ == '__main__':
    main()
