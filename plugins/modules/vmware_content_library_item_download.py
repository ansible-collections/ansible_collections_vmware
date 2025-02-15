#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, VMWare Inc.
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_content_library_item_download
short_description: Download from CL
description: Downloads contents from a Content Library
author:
- Christian Neugum (@digifuchsi)
- Valentin Yonev (@valentinJonev)
requirements:
- vSphere Automation SDK
options:
    library_name:
      description:
      - content library to be searched
      type: str
      required: True
    item_name:
      description:
      - item name to be downloaded
      type: str
      required: True
    directory:
      description:
      - local directory to download files to
      type: str
      required: True
extends_documentation_fragment:
- community.vmware.vmware_rest_client.documentation
'''

EXAMPLES = r'''
- name: Get List of Content Libraries
  community.vmware.vmware_content_library_item_download:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    library_name: CL1
    item_name: vmware_vcsa
    directory: /tmp/
  delegate_to: localhost
'''

RETURN = r'''
downloaded_files:
  description: dict of downloaded files and their location
  returned: on success
  type: dict
  sample: {
      "VMware-VCSA-all-7.0.3-19234570.iso": "/tmp/VMware-VCSA-all-7.0.3-19234570.iso"
    }
'''

import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible_collections.community.vmware.plugins.module_utils.vmware_rest_client import VmwareRestClient

VAUTOMATION_PYTHON_SDK_IMP_ERR = None
HAS_VAUTOMATION_PYTHON_SDK = False
try:
    from com.vmware.content.library.item_client import DownloadSessionModel
    from com.vmware.content.library.item.downloadsession_client import File as DownloadSessionFile
    HAS_VAUTOMATION_PYTHON_SDK = True

    import requests
except ImportError:
    VAUTOMATION_PYTHON_SDK_IMP_ERR = traceback.format_exc()
    pass

import uuid
import time
import os


class VmwareContentLibItemDownload(VmwareRestClient):
    def __init__(self, module):
        """Constructor."""
        super(VmwareContentLibItemDownload, self).__init__(module)
        self.content_service = self.api_client

    def download(self):
        """
        Establishes a download session and downloads every file the Content Library Item hosts
        """
        downloaded_files_map = {}
        try:
            if not HAS_VAUTOMATION_PYTHON_SDK:
                self.module.fail_json(
                    msg=missing_required_lib('com.vmware'),
                    exception=VAUTOMATION_PYTHON_SDK_IMP_ERR)

            download_session_id = self.content_service.content.library.item.DownloadSession.create(
                create_spec=DownloadSessionModel(library_item_id=self.get_item_id()),
                client_token=str(uuid.uuid4()))
        except Exception as e:
            self.module.fail_json(msg="Could not establish a download session", error=e)

        try:
            file_list = self.content_service.content.library.item.downloadsession.File.list(download_session_id)

            for file in file_list:
                self.content_service.content.library.item.downloadsession.File.prepare(download_session_id, file.name)
                download_info = self.wait_for_prepare(download_session_id, file.name)

                response = requests.get(download_info.download_endpoint.uri, verify=False)
                file_path = os.path.join(self.module.params['directory'], file.name)
                with open(file_path, 'wb') as local_file:
                    local_file.write(response.content)
                downloaded_files_map[file.name] = file_path
        except Exception as e:
            self.content_service.content.library.item.DownloadSession.fail(
                download_session_id,
                "Ansible failed to download files")
            self.module.fail_json(msg='Could not download files', error=e)

        self.content_service.content.library.item.DownloadSession.delete(download_session_id)
        self.module.exit_json(changed=True, downloaded_files=downloaded_files_map, msg="All files are downloaded")

    def get_item_id(self):
        """
        Finds the Content Library Item ID by Content Library and Item name
        """
        content_lib_ids = self.content_service.content.Library.find(
            {'name': self.module.params['library_name']})
        if (len(content_lib_ids) != 1):
            self.module.fail_json(
                msg='No unique Content Library found. Found '
                + str(len(content_lib_ids)) + ' libraries named ' + self.module.params['library_name'] + '.')

        content_lib_item_ids = self.content_service.content.library.Item.find({
            'library_id': content_lib_ids[0],
            'name': self.module.params['item_name']})
        if (len(content_lib_item_ids) != 1):
            self.module.fail_json(
                msg='No unique Content Library Item found. Found '
                + str(len(content_lib_item_ids)) + ' items named ' + self.module.params['item_name'] + '.')

        return content_lib_item_ids[0]

    def wait_for_prepare(self, session_id, file_name,
                         status_list,
                         timeout=30, sleep_interval=1):
        """
        Waits for a file to reach a status in the status list (default: prepared)
        This method will either timeout or return the result of
        downloadSessionFile.get(session_id, file_name)
        """
        if HAS_VAUTOMATION_PYTHON_SDK:
            status_list = (DownloadSessionFile.PrepareStatus.PREPARED,)

        start_time = time.time()
        while (time.time() - start_time) < timeout:
            file_info = self.content_service.content.library.item.downloadsession.File.get(session_id, file_name)
            if file_info.status in status_list:
                return file_info
            else:
                time.sleep(sleep_interval)
        raise Exception(
            'timed out after waiting {0} seconds for file {1} to reach a terminal state'.format(
                timeout, file_name))


def main():
    argument_spec = VmwareRestClient.vmware_client_argument_spec()
    argument_spec.update(
        library_name=dict(type='str', required=True),
        item_name=dict(type='str', required=True),
        directory=dict(type='str', required=True)
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)

    vmware_contentlib_info = VmwareContentLibItemDownload(module)
    vmware_contentlib_info.download()


if __name__ == '__main__':
    main()
