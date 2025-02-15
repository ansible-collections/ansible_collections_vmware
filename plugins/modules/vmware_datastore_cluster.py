#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018, Ansible Project
# Copyright (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: vmware_datastore_cluster
short_description: Manage VMware vSphere datastore clusters
description:
    - This module can be used to add and delete datastore cluster in given VMware environment.
author:
-  Abhijeet Kasurde (@Akasurde)
options:
    datacenter_name:
      description:
      - The name of the datacenter.
      - You must specify either a O(datacenter_name) or a O(folder).
      - Mutually exclusive with O(folder) parameter.
      required: false
      aliases: [ datacenter ]
      type: str
    datastore_cluster_name:
      description:
      - The name of the datastore cluster.
      required: true
      type: str
    state:
      description:
      - If the datastore cluster should be present or absent.
      choices: [ present, absent ]
      default: present
      type: str
    folder:
      description:
      - Destination folder, absolute path to place datastore cluster in.
      - The folder should include the datacenter.
      - You must specify either a O(folder) or a O(datacenter_name).
      - 'Examples:'
      - '   folder: /datacenter1/datastore'
      - '   folder: datacenter1/datastore'
      - '   folder: /datacenter1/datastore/folder1'
      - '   folder: datacenter1/datastore/folder1'
      - '   folder: /folder1/datacenter1/datastore'
      - '   folder: folder1/datacenter1/datastore'
      - '   folder: /folder1/datacenter1/datastore/folder2'
      required: false
      type: str
    enable_sdrs:
      description:
      - Whether or not storage DRS is enabled.
      default: false
      type: bool
      required: false
    automation_level:
      description:
      - Run SDRS automated or manually.
      choices: [ automated, manual ]
      default: manual
      type: str
      required: false
    keep_vmdks_together:
      description:
      - Specifies whether or not each VM in this datastore cluster should have its virtual disks on the same datastore by default.
      default: true
      type: bool
      required: false
    loadbalance_interval:
      description:
      - Specify the interval in minutes that storage DRS runs to load balance among datastores.
      default: 480
      type: int
      required: false
    enable_io_loadbalance:
      description:
      - Whether or not storage DRS takes into account storage I/O workload when making load balancing and initial placement recommendations.
      default: false
      type: bool
      required: false
    space_balance_automation_level:
        description:
        - Specifies whether the space balance automation level is automated, manual or use the cluster settings.
        - Specifies the Storage DRS behavior when it generates recommendations for correcting space load imbalance in a datastore cluster.
        choices: [automated, manual, cluster_settings]
        type: str
        version_added: '2.3.0'
    rule_enforcement_automation_level:
        description:
        - Specifies whether the rule enforcement automation level is automated, manual or use the cluster settings.
        - Specifies the Storage DRS behavior when it generates recommendations for correcting affinity rule violations in a datastore cluster.
        choices: [automated, manual, cluster_settings]
        type: str
        version_added: '2.3.0'
    policy_enforcement_automation_level:
        description:
        - Specifies whether the policy enforcement automation level is automated, manual or use the cluster settings.
        - Specifies the Storage DRS behavior when it generates recommendations for correcting storage and VM policy violations in a datastore cluster
        choices: [automated, manual, cluster_settings]
        type: str
        version_added: '2.3.0'
    vm_evacuation_automation_level:
        description:
        - Specifies whether the vm evacuation enforcement automation level is automated, manual or use the cluster settings.
        - Specifies the Storage DRS behavior when it generates recommendations for VM evacuations from datastores in a datastore cluster.
        choices: [automated, manual, cluster_settings]
        type: str
        version_added: '2.3.0'
    min_space_utilization_difference:
        description:
        - This threshold ensures that there is some minimum difference between the space utilization of the source and destination before make recommendations.
        - Value between 1% and 50%
        type: int
        version_added: '2.3.0'
    free_space_threshold_gb:
        description:
        - Runtime thresholds govern when Storage DRS performs or recommends migrations (based on the selected automation level).
        - Dictates the minimum level of free space for each datastore that is the threshold for action.
        - Value in GB
        - Use free_space_threshold_gb or space_utilization_threshold to define the threshold.
        type: int
        version_added: '2.3.0'
    space_utilization_threshold:
        description:
        - Runtime thresholds govern when Storage DRS performs or recommends migrations (based on the selected automation level).
        - Dictates the minimum level of consumed space for each datastore that is the threshold for action.
        - Value between 50% and 100%
        - Use space_utilization_threshold or free_space_threshold_gb to define the threshold.
        type: int
        version_added: '2.3.0'
    io_balance_automation_level:
        description:
        - Specifies whether the I/O balance automation level is automated, manual or use the cluster settings.
        - Specifies the Storage DRS behavior when it generates recommendations for correcting I/O load imbalance in a datastore cluster.
        choices: [automated, manual, cluster_settings]
        type: str
        version_added: '2.3.0'
    io_latency_threshold:
        description:
        - Dictates the minimum I/O latency for each datastore below which I/O load balancing moves are not considered.
        type: int
    io_load_imbalanc_threshold:
        description:
        - The I/O imbalance threshold is the amount of imbalance that Storage DRS should tolerate.
        - When you use an aggressive setting (Small value), Storage DRS corrects small imbalances if possible.
        - When you use a conservative setting (Big value), Storage DRS produces recommendations only when the imbalance across datastores is very high.
        - Value between 1 and 100.
        type: int
    vm_overrides:
        description:
        - Override the datastore cluster-wide automation level for individual virtual machines.
        - And override default virtual disk affinity rules
        type: list
        elements: dict
        version_added: '2.3.0'
        suboptions:
            vm_name:
                description:
                - Name of the virtual machine that should have a an override.
                type: str
                required: true
            keep_vmdks_together:
                description:
                - None (Not set) -> No override
                - true -> This VM should have its virtual disks on the same datastore.
                - False -> This VM should not have its virtual disks on the same datastore.
                type: bool
            automation_level:
                description:
                - none (or Not set) -> No override
                - automated -> Placement and migration recommendations run automatically.
                - manual -> Placement and migration recommendations are displayed, but do not run until you manually apply the recommendation.
                - disabled -> vCenter Server does not migrate the virtual machine or provide migration recommendations for it.
                choices: [none, automated, manual, disabled]
                default: none
                type: str
extends_documentation_fragment:
- community.vmware.vmware.documentation

'''

EXAMPLES = r'''
- name: Create/Modify datastore cluster with enable SDRS
  community.vmware.vmware_datastore_cluster:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: '{{ datacenter_name }}'
    datastore_cluster_name: '{{ datastore_cluster_name }}'
    enable_sdrs: true
    state: present
  delegate_to: localhost

- name: Create/Modify datastore cluster with enable SDRS
  community.vmware.vmware_datastore_cluster:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: '{{ datacenter_name }}'
    datastore_cluster_name: '{{ datastore_cluster_name }}'
    enable_sdrs: true
    state: present
  delegate_to: localhost

- name: Create/Modify datastore cluster with enable SDRS and set the automation levels to manual
  community.vmware.vmware_datastore_cluster:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: '{{ datacenter_name }}'
    datastore_cluster_name: '{{ datastore_cluster_name }}'
    enable_sdrs: true
    state: present
    space_balance_automation_level: manual
    io_balance_automation_level: manual
    rule_enforcement_automation_level: manual
    policy_enforcement_automation_level: manual
    vm_evacuation_automation_level: manual
  delegate_to: localhost

- name: Create datastore cluster using folder
  community.vmware.vmware_datastore_cluster:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    folder: '/{{ datacenter_name }}/datastore/ds_folder'
    datastore_cluster_name: '{{ datastore_cluster_name }}'
    state: present
  delegate_to: localhost

- name: Delete datastore cluster
  community.vmware.vmware_datastore_cluster:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: '{{ datacenter_name }}'
    datastore_cluster_name: '{{ datastore_cluster_name }}'
    state: absent
  delegate_to: localhost
'''

RETURN = r'''
result:
    description: information about datastore cluster operation
    returned: always
    type: str
    sample: "Datastore cluster 'DSC2' created successfully."
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi, vmware_argument_spec, wait_for_task, find_vm_by_name
from ansible.module_utils._text import to_native


class VMwareDatastoreClusterManager(PyVmomi):
    def __init__(self, module):
        super(VMwareDatastoreClusterManager, self).__init__(module)
        folder = self.params['folder']
        if folder:
            self.folder_obj = self.content.searchIndex.FindByInventoryPath(folder)
            if not self.folder_obj:
                self.module.fail_json(msg="Failed to find the folder specified by %(folder)s" % self.params)
        else:
            datacenter_name = self.params.get('datacenter_name')
            datacenter_obj = self.find_datacenter_by_name(datacenter_name)
            if not datacenter_obj:
                self.module.fail_json(msg="Failed to find datacenter '%s' required"
                                          " for managing datastore cluster." % datacenter_name)
            self.folder_obj = datacenter_obj.datastoreFolder

        self.datastore_cluster_name = self.params.get('datastore_cluster_name')
        self.datastore_cluster_obj = self.find_datastore_cluster_by_name(self.datastore_cluster_name)

    def ensure(self):
        """
        Manage internal state of datastore cluster

        """
        results = dict(changed=False, result='')
        state = self.module.params.get('state')
        enable_sdrs = self.params.get('enable_sdrs')
        automation_level = self.params.get('automation_level')
        keep_vmdks_together = self.params.get('keep_vmdks_together')
        enable_io_loadbalance = self.params.get('enable_io_loadbalance')
        loadbalance_interval = self.params.get('loadbalance_interval')

        # Automation overrides
        space_balance_automation_level = self.params.get('space_balance_automation_level')
        rule_enforcement_automation_level = self.params.get('rule_enforcement_automation_level')
        policy_enforcement_automation_level = self.params.get('policy_enforcement_automation_level')
        vm_evacuation_automation_level = self.params.get('vm_evacuation_automation_level')

        # Space Load Balance Config
        min_space_utilization_difference = self.params.get('min_space_utilization_difference')
        if min_space_utilization_difference is not None and min_space_utilization_difference not in range(1, 51):  # between 1% and 50%
            self.module.fail_json(msg="min_space_utilization_difference can only be set between 1% and 50%.")
        free_space_threshold_gb = self.params.get('free_space_threshold_gb')
        space_utilization_threshold = self.params.get('space_utilization_threshold')
        if space_utilization_threshold is not None and space_utilization_threshold not in range(50, 101):  # between 50% and 100%
            self.module.fail_json(msg="space_utilization_threshold can only be set between 50% and 100%.")

        # IO Load Balance Config
        io_balance_automation_level = self.params.get('io_balance_automation_level')
        io_latency_threshold = self.params.get('io_latency_threshold')
        io_load_imbalanc_threshold = self.params.get('io_load_imbalanc_threshold')
        if io_load_imbalanc_threshold is not None and io_load_imbalanc_threshold not in range(1, 101):  # between 1 and 100
            self.module.fail_json(msg="io_load_imbalanc_threshold can only be set between 1 and 100.")

        vm_overrides = {} if self.params.get('vm_overrides') is None else self.params.get('vm_overrides')

        if self.datastore_cluster_obj:
            if state == 'present':
                results['result'] = "Datastore cluster '%s' already available." % self.datastore_cluster_name
                sdrs_spec = vim.storageDrs.ConfigSpec()
                currentPodConfig = self.datastore_cluster_obj.podStorageDrsEntry.storageDrsConfig.podConfig

                change = False
                # Storage Pod Config
                sdrs_spec.podConfigSpec = vim.storageDrs.PodConfigSpec()
                sdrs_spec.podConfigSpec.automationOverrides = currentPodConfig.automationOverrides
                sdrs_spec.podConfigSpec.spaceLoadBalanceConfig = currentPodConfig.spaceLoadBalanceConfig
                sdrs_spec.podConfigSpec.ioLoadBalanceConfig = currentPodConfig.ioLoadBalanceConfig
                sdrs_spec.podConfigSpec.enabled = enable_sdrs  # Must be set because automationOverrides not be written otherwise

                if enable_sdrs != currentPodConfig.enabled:
                    results['result'] += results['result'] + " Changed SDRS to '%s'." % enable_sdrs
                    change = True

                if automation_level != currentPodConfig.defaultVmBehavior:
                    sdrs_spec.podConfigSpec.defaultVmBehavior = automation_level
                    results['result'] += results['result'] + " Changed automation level to '%s'." % automation_level
                    change = True

                if keep_vmdks_together != currentPodConfig.defaultIntraVmAffinity:
                    sdrs_spec.podConfigSpec.defaultIntraVmAffinity = keep_vmdks_together
                    results['result'] += results['result'] + " Changed VMDK affinity to '%s'." % keep_vmdks_together
                    change = True

                if enable_io_loadbalance != currentPodConfig.ioLoadBalanceEnabled:
                    sdrs_spec.podConfigSpec.ioLoadBalanceEnabled = enable_io_loadbalance
                    results['result'] += results['result'] + " Changed I/O workload balancing to '%s'." % enable_io_loadbalance
                    change = True

                if loadbalance_interval != currentPodConfig.loadBalanceInterval:
                    sdrs_spec.podConfigSpec.loadBalanceInterval = loadbalance_interval
                    results['result'] += results['result'] + " Changed load balance interval to '%s' minutes." % loadbalance_interval
                    change = True

                # Automation overrides
                if space_balance_automation_level is not None and \
                        (currentPodConfig.automationOverrides.spaceLoadBalanceAutomationMode is None
                         or space_balance_automation_level != currentPodConfig.automationOverrides.spaceLoadBalanceAutomationMode):
                    sdrs_spec.podConfigSpec.automationOverrides.spaceLoadBalanceAutomationMode = space_balance_automation_level \
                        if space_balance_automation_level != "cluster_settings" else None
                    results['result'] += " Changed Space balance automation level to '%s'." % space_balance_automation_level
                    change = True

                if rule_enforcement_automation_level is not None and \
                        (currentPodConfig.automationOverrides.ruleEnforcementAutomationMode is None
                         or rule_enforcement_automation_level != currentPodConfig.automationOverrides.ruleEnforcementAutomationMode):
                    sdrs_spec.podConfigSpec.automationOverrides.ruleEnforcementAutomationMode = rule_enforcement_automation_level \
                        if rule_enforcement_automation_level != "cluster_settings" else None
                    results['result'] += " Changed Rule enforcement automation level to '%s'." % rule_enforcement_automation_level
                    change = True

                if policy_enforcement_automation_level is not None and \
                        (currentPodConfig.automationOverrides.policyEnforcementAutomationMode is None
                         or policy_enforcement_automation_level != currentPodConfig.automationOverrides.policyEnforcementAutomationMode):
                    sdrs_spec.podConfigSpec.automationOverrides.policyEnforcementAutomationMode = policy_enforcement_automation_level \
                        if policy_enforcement_automation_level != "cluster_settings" else None
                    results['result'] += " Changed Policy enforcement automation level to '%s'." % policy_enforcement_automation_level
                    change = True

                if vm_evacuation_automation_level is not None and \
                        (currentPodConfig.automationOverrides.vmEvacuationAutomationMode is None
                         or vm_evacuation_automation_level != currentPodConfig.automationOverrides.vmEvacuationAutomationMode):
                    sdrs_spec.podConfigSpec.automationOverrides.vmEvacuationAutomationMode = vm_evacuation_automation_level \
                        if vm_evacuation_automation_level != "cluster_settings" else None
                    results['result'] += " Changed VM evacuation automation level to '%s'." % vm_evacuation_automation_level
                    change = True

                # Space Load Balance Config
                if min_space_utilization_difference is not None and \
                        min_space_utilization_difference != currentPodConfig.spaceLoadBalanceConfig.minSpaceUtilizationDifference:
                    sdrs_spec.podConfigSpec.spaceLoadBalanceConfig.minSpaceUtilizationDifference = min_space_utilization_difference
                    results['result'] += " Changed minimum space utilization difference to '%s' prozent." % min_space_utilization_difference
                    change = True

                if free_space_threshold_gb is not None and free_space_threshold_gb != currentPodConfig.spaceLoadBalanceConfig.freeSpaceThresholdGB:
                    sdrs_spec.podConfigSpec.spaceLoadBalanceConfig.freeSpaceThresholdGB = free_space_threshold_gb
                    sdrs_spec.podConfigSpec.spaceLoadBalanceConfig.spaceThresholdMode = "freeSpace"
                    results['result'] += " Changed Space threshold to '%s'GB." % free_space_threshold_gb
                    change = True

                if space_utilization_threshold is not None and \
                        space_utilization_threshold != currentPodConfig.spaceLoadBalanceConfig.spaceUtilizationThreshold:
                    sdrs_spec.podConfigSpec.spaceLoadBalanceConfig.spaceUtilizationThreshold = space_utilization_threshold
                    sdrs_spec.podConfigSpec.spaceLoadBalanceConfig.spaceThresholdMode = "utilization"
                    results['result'] += " Changed Space threshold to '%s' prozent." % space_utilization_threshold
                    change = True

                # IO Load Balance Config
                if io_balance_automation_level is not None and io_balance_automation_level != currentPodConfig.automationOverrides.ioLoadBalanceAutomationMode:
                    sdrs_spec.podConfigSpec.automationOverrides.ioLoadBalanceAutomationMode = io_balance_automation_level \
                        if io_balance_automation_level != "cluster_settings" else None
                    results['result'] += " Changed I/O balance automation level to '%s'." % io_balance_automation_level
                    change = True

                if io_latency_threshold is not None and io_latency_threshold != currentPodConfig.ioLoadBalanceConfig.ioLatencyThreshold:
                    sdrs_spec.podConfigSpec.ioLoadBalanceConfig.ioLatencyThreshold = io_latency_threshold
                    results['result'] += " Changed latency_ threshold to '%s'." % io_latency_threshold
                    change = True

                if io_load_imbalanc_threshold is not None and io_load_imbalanc_threshold != currentPodConfig.ioLoadBalanceConfig.ioLoadImbalanceThreshold:
                    sdrs_spec.podConfigSpec.ioLoadBalanceConfig.ioLoadImbalanceThreshold = io_load_imbalanc_threshold
                    results['result'] += " Changed load imbalance threshold to '%s'." % io_load_imbalanc_threshold
                    change = True

                # Storage DRS VM Config
                sdrs_spec.vmConfigSpec = None
                vmConfig = self.datastore_cluster_obj.podStorageDrsEntry.storageDrsConfig.vmConfig

                vmConfigSpecs = []
                for vm in vm_overrides:
                    changed = False

                    # get the virtual machine
                    virtual_machine = find_vm_by_name(self.content, vm_name=vm['vm_name'])
                    if not virtual_machine:
                        self.module.fail_json(msg="Failed to find virtual machine %s" % vm['vm_name'])

                    vmConfigSpec = vim.storageDrs.VmConfigSpec()
                    vmConfigSpec.operation = "add"
                    vmConfigSpec.info = vim.storageDrs.VmConfigInfo()
                    vmConfigSpec.info.vm = virtual_machine

                    foundVm = None
                    for storageDrsVmConfigInfo in vmConfig:
                        if storageDrsVmConfigInfo.vm.name == vm['vm_name']:
                            foundVm = storageDrsVmConfigInfo
                            break

                    if foundVm:
                        if vm['automation_level'] == "disabled":
                            if foundVm.behavior is not None:
                                vmConfigSpec.info.behavior = None
                                changed = True
                            if foundVm.enabled is not False:
                                vmConfigSpec.info.enabled = False
                                changed = True
                        elif vm['automation_level'] == "none":
                            if foundVm.behavior is not None:
                                vmConfigSpec.info.behavior = None
                                changed = True
                            if foundVm.enabled is not None:
                                vmConfigSpec.info.enabled = None
                                changed = True
                        else:
                            if foundVm.behavior is not None:
                                vmConfigSpec.info.behavior = vm['automation_level']
                                changed = True
                            if foundVm.enabled is not False:
                                vmConfigSpec.info.enabled = False
                                changed = True

                        if foundVm.intraVmAffinity != vm['keep_vmdks_together']:
                            vmConfigSpec.info.intraVmAffinity = vm['keep_vmdks_together']
                            changed = True
                    else:
                        changed = True
                        if vm['automation_level'] == "disabled":
                            vmConfigSpec.info.behavior = None
                            vmConfigSpec.info.enabled = False
                        elif vm['automation_level'] == "none":
                            vmConfigSpec.info.behavior = None
                            vmConfigSpec.info.enabled = None
                        else:
                            vmConfigSpec.info.behavior = vm['automation_level']
                            vmConfigSpec.info.enabled = False
                        vmConfigSpec.info.intraVmAffinity = vm['keep_vmdks_together']

                    if changed:
                        vmConfigSpecs.append(vmConfigSpec)

                sdrs_spec.vmConfigSpec = vmConfigSpecs

                # Check for changes or run changes
                if change or len(sdrs_spec.vmConfigSpec) != 0:
                    if not self.module.check_mode:
                        try:
                            task = self.content.storageResourceManager.ConfigureStorageDrsForPod_Task(pod=self.datastore_cluster_obj,
                                                                                                      spec=sdrs_spec, modify=True)
                            changed, result = wait_for_task(task)
                        except Exception as generic_exc:
                            self.module.fail_json(msg="Failed to configure datastore cluster"
                                                      " '%s' due to %s" % (self.datastore_cluster_name,
                                                                           to_native(generic_exc)))
                    else:
                        changed = True
                    results['changed'] = changed
            elif state == 'absent':
                # Delete datastore cluster
                if not self.module.check_mode:
                    task = self.datastore_cluster_obj.Destroy_Task()
                    changed, result = wait_for_task(task)
                else:
                    changed = True
                if changed:
                    results['result'] = "Datastore cluster '%s' deleted successfully." % self.datastore_cluster_name
                    results['changed'] = changed
                else:
                    self.module.fail_json(msg="Failed to delete datastore cluster '%s'." % self.datastore_cluster_name)
        else:
            if state == 'present':
                # Create datastore cluster
                if not self.module.check_mode:
                    try:
                        self.datastore_cluster_obj = self.folder_obj.CreateStoragePod(name=self.datastore_cluster_name)
                    except Exception as generic_exc:
                        self.module.fail_json(msg="Failed to create datastore cluster"
                                                  " '%s' due to %s" % (self.datastore_cluster_name,
                                                                       to_native(generic_exc)))
                    try:
                        sdrs_spec = vim.storageDrs.ConfigSpec()
                        sdrs_spec.podConfigSpec = vim.storageDrs.PodConfigSpec()
                        sdrs_spec.podConfigSpec.enabled = enable_sdrs
                        sdrs_spec.podConfigSpec.defaultVmBehavior = automation_level
                        sdrs_spec.podConfigSpec.defaultIntraVmAffinity = keep_vmdks_together
                        sdrs_spec.podConfigSpec.ioLoadBalanceEnabled = enable_io_loadbalance
                        sdrs_spec.podConfigSpec.loadBalanceInterval = loadbalance_interval

                        # Automation Overrides
                        if policy_enforcement_automation_level is not None or \
                                rule_enforcement_automation_level is not None or \
                                space_balance_automation_level is not None or \
                                vm_evacuation_automation_level is not None or \
                                io_balance_automation_level is not None:
                            sdrs_spec.podConfigSpec.automationOverrides = vim.storageDrs.AutomationConfig()

                        if policy_enforcement_automation_level:
                            sdrs_spec.podConfigSpec.automationOverrides.policyEnforcementAutomationMode = policy_enforcement_automation_level \
                                if policy_enforcement_automation_level != "cluster_settings" else None
                        if rule_enforcement_automation_level:
                            sdrs_spec.podConfigSpec.automationOverrides.ruleEnforcementAutomationMode = rule_enforcement_automation_level \
                                if rule_enforcement_automation_level != "cluster_settings" else None
                        if space_balance_automation_level:
                            sdrs_spec.podConfigSpec.automationOverrides.spaceLoadBalanceAutomationMode = space_balance_automation_level \
                                if space_balance_automation_level != "cluster_settings" else None
                        if vm_evacuation_automation_level:
                            sdrs_spec.podConfigSpec.automationOverrides.vmEvacuationAutomationMode = vm_evacuation_automation_level \
                                if vm_evacuation_automation_level != "cluster_settings" else None

                        # Space Load Balance Config
                        sdrs_spec.podConfigSpec.spaceLoadBalanceConfig = vim.storageDrs.SpaceLoadBalanceConfig()
                        sdrs_spec.podConfigSpec.spaceLoadBalanceConfig.minSpaceUtilizationDifference = min_space_utilization_difference

                        if free_space_threshold_gb:
                            sdrs_spec.podConfigSpec.spaceLoadBalanceConfig.freeSpaceThresholdGB = free_space_threshold_gb
                            sdrs_spec.podConfigSpec.spaceLoadBalanceConfig.spaceThresholdMode = "freeSpace"

                        if space_utilization_threshold:
                            sdrs_spec.podConfigSpec.spaceLoadBalanceConfig.spaceUtilizationThreshold = space_utilization_threshold
                            sdrs_spec.podConfigSpec.spaceLoadBalanceConfig.spaceThresholdMode = "utilization"

                        # IO Load Balance Config
                        if io_balance_automation_level:
                            sdrs_spec.podConfigSpec.automationOverrides.ioLoadBalanceAutomationMode = io_balance_automation_level \
                                if io_balance_automation_level != "cluster_settings" else None

                        if io_latency_threshold is not None or io_load_imbalanc_threshold is not None:
                            sdrs_spec.podConfigSpec.ioLoadBalanceConfig = vim.storageDrs.IoLoadBalanceConfig()

                        if io_latency_threshold:
                            sdrs_spec.podConfigSpec.ioLoadBalanceConfig.ioLatencyThreshold = io_latency_threshold

                        if io_load_imbalanc_threshold:
                            sdrs_spec.podConfigSpec.ioLoadBalanceConfig.ioLoadImbalanceThreshold = io_load_imbalanc_threshold

                        vmConfigSpecs = []
                        for vm in vm_overrides:
                            # get the virtual machine
                            virtual_machine = find_vm_by_name(self.content, vm_name=vm['vm_name'])
                            if not virtual_machine:
                                self.module.fail_json(msg="Failed to find virtual machine %s" % vm['vm_name'])

                            vmConfigSpec = vim.storageDrs.VmConfigSpec()
                            vmConfigSpec.operation = "add"
                            vmConfigSpec.info = vim.storageDrs.VmConfigInfo()
                            vmConfigSpec.info.vm = virtual_machine

                            if vm['automation_level'] == "disabled":
                                vmConfigSpec.info.behavior = None
                                vmConfigSpec.info.enabled = False
                            elif vm['automation_level'] == "none":
                                vmConfigSpec.info.behavior = None
                                vmConfigSpec.info.enabled = None
                            else:
                                vmConfigSpec.info.behavior = vm['automation_level']
                                vmConfigSpec.info.enabled = False

                            vmConfigSpec.info.intraVmAffinity = vm['keep_vmdks_together']
                            vmConfigSpecs.append(vmConfigSpec)

                        sdrs_spec.vmConfigSpec = vmConfigSpecs

                        task = self.content.storageResourceManager.ConfigureStorageDrsForPod_Task(pod=self.datastore_cluster_obj, spec=sdrs_spec, modify=True)
                        changed, result = wait_for_task(task)
                    except Exception as generic_exc:
                        self.module.fail_json(msg="Failed to configure datastore cluster"
                                                  " '%s' due to %s" % (self.datastore_cluster_name,
                                                                       to_native(generic_exc)))
                results['changed'] = True
                results['result'] = "Datastore cluster '%s' created successfully." % self.datastore_cluster_name
            elif state == 'absent':
                results['result'] = "Datastore cluster '%s' not available or already deleted." % self.datastore_cluster_name
        self.module.exit_json(**results)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            datacenter_name=dict(type='str', required=False, aliases=['datacenter']),
            datastore_cluster_name=dict(type='str', required=True),
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            folder=dict(type='str', required=False),
            enable_sdrs=dict(type='bool', default=False, required=False),
            keep_vmdks_together=dict(type='bool', default=True, required=False),
            automation_level=dict(type='str', choices=['automated', 'manual'], default='manual'),
            enable_io_loadbalance=dict(type='bool', default=False, required=False),
            loadbalance_interval=dict(type='int', default=480, required=False),
            # Automation overrides
            space_balance_automation_level=dict(type='str', choices=['automated', 'manual', 'cluster_settings']),
            rule_enforcement_automation_level=dict(type='str', choices=['automated', 'manual', 'cluster_settings']),
            policy_enforcement_automation_level=dict(type='str', choices=['automated', 'manual', 'cluster_settings']),
            vm_evacuation_automation_level=dict(type='str', choices=['automated', 'manual', 'cluster_settings']),
            # Space Load Balance Config
            min_space_utilization_difference=dict(type='int', required=False),
            free_space_threshold_gb=dict(type='int', required=False),
            space_utilization_threshold=dict(type='int', required=False),
            # IO Load Balance Config
            io_balance_automation_level=dict(type='str', choices=['automated', 'manual', 'cluster_settings']),
            io_latency_threshold=dict(type='int', required=False),
            io_load_imbalanc_threshold=dict(type='int', required=False),
            # VM overrides
            vm_overrides=dict(type='list', elements='dict', required=False, options=dict(
                vm_name=dict(type='str', required=True),
                keep_vmdks_together=dict(type='bool', default=None),
                automation_level=dict(type='str', choices=['none', 'automated', 'manual', 'disabled'], default='none'))
            )
        )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['datacenter_name', 'folder'],
            ['free_space_threshold_gb', 'space_utilization_threshold'],
        ],
        required_one_of=[
            ['datacenter_name', 'folder'],
        ]
    )

    datastore_cluster_mgr = VMwareDatastoreClusterManager(module)
    datastore_cluster_mgr.ensure()


if __name__ == '__main__':
    main()
