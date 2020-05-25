#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_tag
short_description: Manage VMware tags
description:
- This module can be used to create / delete / update VMware tags.
- Tag feature is introduced in vSphere 6 version, so this module is not supported in the earlier versions of vSphere.
- All variables and VMware object names are case sensitive.
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
- vSphere Automation SDK
options:
    tag_name:
      description:
      - The name of tag to manage.
      required: True
      type: str
    tag_description:
      description:
      - The tag description.
      - This is required only if C(state) is set to C(present).
      - This parameter is ignored, when C(state) is set to C(absent).
      - Process of updating tag only allows description change.
      required: False
      default: ''
      type: str
    category_id:
      description:
      - The unique ID generated by vCenter should be used to.
      - User can get this unique ID from facts module.
      required: False
      type: str
    state:
      description:
      - The state of tag.
      - If set to C(present) and tag does not exists, then tag is created.
      - If set to C(present) and tag exists, then tag is updated.
      - If set to C(absent) and tag exists, then tag is deleted.
      - If set to C(absent) and tag does not exists, no action is taken.
      required: False
      default: 'present'
      choices: [ 'present', 'absent' ]
      type: str
extends_documentation_fragment:
- community.vmware.vmware_rest_client.documentation

'''

EXAMPLES = r'''
- name: Create a tag
  community.vmware.vmware_tag:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    validate_certs: no
    category_id: 'urn:vmomi:InventoryServiceCategory:e785088d-6981-4b1c-9fb8-1100c3e1f742:GLOBAL'
    tag_name: Sample_Tag_0002
    tag_description: Sample Description
    state: present
  delegate_to: localhost

- name: Update tag description
  community.vmware.vmware_tag:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    tag_name: Sample_Tag_0002
    tag_description: Some fancy description
    state: present
  delegate_to: localhost

- name: Delete tag
  community.vmware.vmware_tag:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    tag_name: Sample_Tag_0002
    state: absent
  delegate_to: localhost
'''

RETURN = r'''
tag_status:
  description: dictionary of tag metadata
  returned: on success
  type: dict
  sample: {
        "msg": "Tag 'Sample_Tag_0002' created.",
        "tag_id": "urn:vmomi:InventoryServiceTag:bff91819-f529-43c9-80ca-1c9dfda09441:GLOBAL"
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware_rest_client import VmwareRestClient
try:
    from com.vmware.vapi.std.errors_client import Error
except ImportError:
    pass


class VmwareTag(VmwareRestClient):
    def __init__(self, module):
        super(VmwareTag, self).__init__(module)
        self.global_tags = list()
        # api_client to call APIs instead of individual service
        self.tag_service = self.api_client.tagging.Tag
        self.tag_name = self.params.get('tag_name')
        self.get_all_tags()
        self.category_service = self.api_client.tagging.Category
        self.tag_obj = None

    def ensure_state(self):
        """
        Manage internal states of tags

        """
        desired_state = self.params.get('state')
        states = {
            'present': {
                'present': self.state_update_tag,
                'absent': self.state_create_tag,
            },
            'absent': {
                'present': self.state_delete_tag,
                'absent': self.state_unchanged,
            }
        }
        states[desired_state][self.check_tag_status()]()

    def state_create_tag(self):
        """
        Create tag

        """
        tag_spec = self.tag_service.CreateSpec()
        tag_spec.name = self.tag_name
        tag_spec.description = self.params.get('tag_description')
        category_id = self.params.get('category_id', None)
        if category_id is None:
            self.module.fail_json(msg="'category_id' is required parameter while creating tag.")

        category_found = False
        for category in self.category_service.list():
            category_obj = self.category_service.get(category)
            if category_id == category_obj.id:
                category_found = True
                break

        if not category_found:
            self.module.fail_json(msg="Unable to find category specified using 'category_id' - %s" % category_id)

        tag_spec.category_id = category_id
        tag_id = ''
        try:
            tag_id = self.tag_service.create(tag_spec)
        except Error as error:
            self.module.fail_json(msg="%s" % self.get_error_message(error))

        if tag_id:
            self.module.exit_json(changed=True,
                                  tag_status=dict(msg="Tag '%s' created." % tag_spec.name, tag_id=tag_id))
        self.module.exit_json(changed=False,
                              tag_status=dict(msg="No tag created", tag_id=tag_id))

    def state_unchanged(self):
        """
        Return unchanged state

        """
        self.module.exit_json(changed=False)

    def state_update_tag(self):
        """
        Update tag

        """
        changed = False
        tag_id = self.tag_obj['tag_id']
        results = dict(msg="Tag %s is unchanged." % self.tag_name,
                       tag_id=tag_id)
        tag_desc = self.tag_obj['tag_description']
        desired_tag_desc = self.params.get('tag_description')
        if tag_desc != desired_tag_desc:
            tag_update_spec = self.tag_service.UpdateSpec()
            tag_update_spec.description = desired_tag_desc
            try:
                self.tag_service.update(tag_id, tag_update_spec)
            except Error as error:
                self.module.fail_json(msg="%s" % self.get_error_message(error))

            results['msg'] = 'Tag %s updated.' % self.tag_name
            changed = True

        self.module.exit_json(changed=changed, tag_status=results)

    def state_delete_tag(self):
        """
        Delete tag

        """
        tag_id = self.tag_obj['tag_id']
        try:
            self.tag_service.delete(tag_id=tag_id)
        except Error as error:
            self.module.fail_json(msg="%s" % self.get_error_message(error))
        self.module.exit_json(changed=True,
                              tag_status=dict(msg="Tag '%s' deleted." % self.tag_name, tag_id=tag_id))

    def check_tag_status(self):
        """
        Check if tag exists or not
        Returns: 'present' if tag found, else 'absent'

        """
        ret = 'absent'
        for tag in self.global_tags:
            if self.tag_name == tag['tag_name']:
                if 'category_id' in self.params:
                    if self.params['category_id'] == tag['tag_category_id']:
                        ret = 'present'
                        self.tag_obj = tag
                        break
                    else:
                        continue
                else:
                    ret = 'present'
                    self.tag_obj = tag
                    break
        return ret

    def get_all_tags(self):
        """
        Retrieve all tag information

        """
        for tag in self.tag_service.list():
            tag_obj = self.tag_service.get(tag)
            self.global_tags.append(dict(
                tag_name=tag_obj.name,
                tag_description=tag_obj.description,
                tag_used_by=tag_obj.used_by,
                tag_category_id=tag_obj.category_id,
                tag_id=tag_obj.id
            ))


def main():
    argument_spec = VmwareRestClient.vmware_client_argument_spec()
    argument_spec.update(
        tag_name=dict(type='str', required=True),
        tag_description=dict(type='str', default='', required=False),
        category_id=dict(type='str', required=False),
        state=dict(type='str', choices=['present', 'absent'], default='present', required=False),
    )
    module = AnsibleModule(argument_spec=argument_spec)

    vmware_tag = VmwareTag(module)
    vmware_tag.ensure_state()


if __name__ == '__main__':
    main()
