#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2023, Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later


from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_vsan_health
version_added: '3.6.0'
short_description: Repair vSAN cluster objects
description:
  - Repair absent or degraded vSAN objects immediately
  - Triggers a task that puts required objects into repairing queue
  - The completing time for repairing all of objects is unpredictable and depends on vSAN backend
author:
  - Philipp Fruck (@p-fruck)
requirements:
  - vSAN Management SDK, which needs to be downloaded from VMware and installed manually.
options:
  cluster_name:
    description:
      - Name of the vSAN cluster.
    type: str
    required: true
  uuids:
    description:
      - The objects to repair. Leave empty to repair all objects
    type: list
    elements: str
    required: false
extends_documentation_fragment:
  - community.vmware.vmware.documentation
'''

EXAMPLES = r'''
- name: Repair all vSAN health objects
  community.vmware.vmware_vsan_health:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    cluster_name: 'vSAN01'
  delegate_to: localhost
'''

RETURN = r'''#
'''

import traceback

try:
    from pyVmomi import vim
except ImportError:
    pass

VSANPYTHONSDK_IMP_ERR = None
try:
    import vsanapiutils
    HAS_VSANPYTHONSDK = True
except ImportError:
    VSANPYTHONSDK_IMP_ERR = traceback.format_exc()
    HAS_VSANPYTHONSDK = False

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi, vmware_argument_spec, wait_for_task


class VsanApi(PyVmomi):
    def __init__(self, module):
        super(VsanApi, self).__init__(module)

        client_stub = self.si._GetStub()
        ssl_context = client_stub.schemeArgs.get('context')
        apiVersion = vsanapiutils.GetLatestVmodlVersion(module.params['hostname'])
        vcMos = vsanapiutils.GetVsanVcMos(client_stub, context=ssl_context, version=apiVersion)
        self.vsanClusterHealthSystem = vcMos['vsan-cluster-health-system']

        self.cluster = None

    def repair_objects(self):
        cluster_name = self.module.params.get('cluster_name')
        if cluster_name:
            self.cluster = self.find_cluster_by_name(cluster_name=cluster_name)
            if self.cluster is None:
                self.module.fail_json(msg="Cluster %s does not exist." % cluster_name)

        uuids = self.module.params.get('uuids')
        task = self.vsanClusterHealthSystem.VsanHealthRepairClusterObjectsImmediate(
            cluster=self.cluster,
            uuids=uuids,
        )

        changed, result = wait_for_task(vim.Task(task._moId, self.si._stub))
        self.module.exit_json(changed=changed, result=result)


def main():
    argument_spec = vmware_argument_spec()

    argument_spec.update(dict(
        cluster_name=dict(type='str', required=True),
        uuids=dict(type='list', elements='str', required=False)
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    api = VsanApi(module)
    try:
        api.repair_objects()
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
