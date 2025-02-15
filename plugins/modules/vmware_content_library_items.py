#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, VMWare Inc.
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: vmware_content_library_items
short_description: Gather information about VMWare Subscribed Content Library
description:
- Module to list all items in specified subscribed content library.
author:
- Aleksandar Kinanov (@aleksandar-kinanov)
- Valentin Yonev (@valentinJonev)
notes:
- Tested on vSphere 6.7
requirements:
- python >= 3.7
- PyVmomi
- vSphere Automation SDK
options:
    subscribed_library_name:
      description:
      - Subscribed content library name
      type: str
      required: True
extends_documentation_fragment:
- community.vmware.vmware.documentation
'''

EXAMPLES = r'''
- name: Get all items present in Subscribed Content Library
  community.vmware.vmware_content_library_items:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    subscribed_library_name: SubscribedContentLibraryName
  delegate_to: localhost
'''

RETURN = r'''
library_items:
  description: list of items found in subscribed content library
  returned: on success
  type: list
  sample: [
        "mikrotik-6.48.5",
        "alpine-standard-3.15.0-x86_64",
        "SVM-CloudVisor-Installer-6.7.0-10737425.x86_64"
    ]
'''

import traceback

from ansible.module_utils._text import to_native
from ansible_collections.community.vmware.plugins.module_utils.vmware import vmware_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import missing_required_lib

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from requests.packages import urllib3
    HAS_URLLIB3 = True
except ImportError:
    try:
        import urllib3
        HAS_URLLIB3 = True
    except ImportError:
        HAS_URLLIB3 = False

VAUTOMATION_PYTHON_SDK_IMP_ERR = None
HAS_VAUTOMATION_PYTHON_SDK = False
try:
    from com.vmware.content_client import SubscribedLibrary
    from com.vmware.content.library_client import Item
    from com.vmware.cis_client import Session

    from vmware.vapi.stdlib.client.factories import StubConfigurationFactory
    from vmware.vapi.security.user_password import create_user_password_security_context
    from vmware.vapi.security.session import create_session_security_context
    from vmware.vapi.lib.connect import get_requests_connector
    from vmware.vapi.exception import CoreException

    HAS_VAUTOMATION_PYTHON_SDK = True
except ImportError:
    VAUTOMATION_PYTHON_SDK_IMP_ERR = traceback.format_exc()
    pass

if HAS_VAUTOMATION_PYTHON_SDK and HAS_REQUESTS:
    class Connection:
        def create_unverified_session(self, session, suppress_warning=True):
            """
            Create a unverified session to disable the server certificate verification.
            This is not recommended in production code.
            """
            session.verify = False
            if suppress_warning:
                # Suppress unverified https request warnings
                if HAS_URLLIB3:
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            return session

        def connect(self, host, user, pwd,
                    suppress_warning=True):
            """
            Create an authenticated stub configuration object that can be used to issue
            requests against vCenter.
            Returns a stub_config that stores the session identifier that can be used
            to issue authenticated requests against vCenter.
            """
            host_url = self.get_jsonrpc_endpoint_url(host)

            session = requests.Session()
            session = self.create_unverified_session(session, suppress_warning)

            connector = get_requests_connector(session=session, url=host_url)

            stub_config = StubConfigurationFactory.new_std_configuration(connector)

            return self.login(stub_config, user, pwd)

        def login(self, stub_config, user, pwd):
            """
            Create an authenticated session with vCenter.
            Returns a stub_config that stores the session identifier that can be used
            to issue authenticated requests against vCenter.
            """
            # Pass user credentials (user/password) in the security context to
            # authenticate.
            user_password_security_context = create_user_password_security_context(user,
                                                                                   pwd)
            stub_config.connector.set_security_context(
                user_password_security_context)

            # Create the stub for the session service and login by creating a session.
            session_svc = Session(stub_config)
            session_id = session_svc.create()

            # Successful authentication.  Store the session identifier in the security
            # context of the stub and use that for all subsequent remote requests
            session_security_context = create_session_security_context(session_id)
            stub_config.connector.set_security_context(session_security_context)

            return stub_config

        def get_jsonrpc_endpoint_url(self, host):
            # The URL for the stub requests are made against the /api HTTP endpoint
            # of the vCenter system.
            return "https://{0}/api".format(host)


class VmwareContentLibInfo():
    def __init__(self, module: AnsibleModule):
        """Constructor."""
        self.module = module
        self._vcenter_connection_arguments = {
            'user': self.module.params['username'],
            'pwd': self.module.params['password'],
            'host': self.module.params['hostname']
        }
        self._cl_name = self.module.params['subscribed_library_name']

        self.connection = self._get_connection_stub(
            self._vcenter_connection_arguments)

    def _get_connection_stub(self, connection_args):
        obj = Connection()
        try:
            return obj.connect(**connection_args)
        except Exception:
            self.module.fail_json(msg=to_native(
                "Failed to authenticate! Please validate vCenter username, password and endpoint"))

    def get_content_library_items(self):
        if not HAS_VAUTOMATION_PYTHON_SDK:
            self.module.fail_json(
                msg=missing_required_lib('com.vmware'),
                exception=VAUTOMATION_PYTHON_SDK_IMP_ERR)

        _library_item_service = Item(self.connection)
        try:
            _library_all_items = _library_item_service.list(
                self._get_content_library_id())
        except CoreException:
            self.module.fail_json(msg=to_native(
                "Could not retrieve Content Library items"))

        _library_items_names = []

        for item in _library_all_items:
            _library_items_names.append("{0}".format(
                _library_item_service.get(item).name))
        self.module.exit_json(
            changed=False, library_items=_library_items_names)

    def _get_content_library_id(self):
        if not HAS_VAUTOMATION_PYTHON_SDK:
            self.module.fail_json(
                msg=missing_required_lib('com.vmware'),
                exception=VAUTOMATION_PYTHON_SDK_IMP_ERR)

        subscribed_library_service = SubscribedLibrary(self.connection)
        items = subscribed_library_service.list()
        for item in items:
            _current_cl = subscribed_library_service.get(item)
            if _current_cl.name == self._cl_name:
                return _current_cl.id
        self.module.fail_json(msg=to_native(
            "Could not find Content Library with name {0}".format(self._cl_name)))


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        subscribed_library_name=dict(type='str', required=True),
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    vmware_contentlib_info = VmwareContentLibInfo(module)
    vmware_contentlib_info.get_content_library_items()


if __name__ == '__main__':
    main()
