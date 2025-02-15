#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_cluster_ha
short_description: Manage High Availability (HA) on VMware vSphere clusters
description:
    - Manages HA configuration on VMware vSphere clusters.
author:
- Joseph Callen (@jcpowermac)
- Abhijeet Kasurde (@Akasurde)
options:
    cluster_name:
      description:
      - The name of the cluster to be managed.
      type: str
      required: true
    datacenter:
      description:
      - The name of the datacenter.
      type: str
      required: true
      aliases: [ datacenter_name ]
    enable:
      description:
      - Whether to enable HA.
      type: bool
      default: true
    ha_host_monitoring:
      description:
      - Whether HA restarts virtual machines after a host fails.
      - If set to V(enabled), HA restarts virtual machines after a host fails.
      - If set to V(disabled), HA does not restart virtual machines after a host fails.
      - If O(enable=false), this value is ignored.
      type: str
      choices: [ 'enabled', 'disabled' ]
      default: 'enabled'
    ha_vm_monitoring:
      description:
      - State of virtual machine health monitoring service.
      - If set to V(vmAndAppMonitoring), HA response to both virtual machine and application heartbeat failure.
      - If set to V(vmMonitoringDisabled), virtual machine health monitoring is disabled.
      - If set to V(vmMonitoringOnly), HA response to virtual machine heartbeat failure.
      - If O(enable=false), then this value is ignored.
      type: str
      choices: ['vmAndAppMonitoring', 'vmMonitoringOnly', 'vmMonitoringDisabled']
      default: 'vmMonitoringDisabled'
    host_isolation_response:
      description:
      - Indicates whether or VMs should be powered off if a host determines that it is isolated from the rest of the compute resource.
      - If set to V(none), do not power off VMs in the event of a host network isolation.
      - If set to V(powerOff), power off VMs in the event of a host network isolation.
      - If set to V(shutdown), shut down VMs guest operating system in the event of a host network isolation.
      type: str
      choices: ['none', 'powerOff', 'shutdown']
      default: 'none'
    slot_based_admission_control:
      description:
      - Configure slot based admission control policy.
      - O(slot_based_admission_control), O(reservation_based_admission_control) and O(failover_host_admission_control) are mutually exclusive.
      suboptions:
        failover_level:
          description:
            - Number of host failures that should be tolerated.
          type: int
          required: true
      type: dict
    reservation_based_admission_control:
      description:
      - Configure reservation based admission control policy.
      - O(slot_based_admission_control), O(reservation_based_admission_control) and O(failover_host_admission_control) are mutually exclusive.
      suboptions:
        failover_level:
          description:
            - Number of host failures that should be tolerated.
          type: int
          required: true
        auto_compute_percentages:
          description:
            - By default, O(reservation_based_admission_control.failover_level) is used to calculate
              O(reservation_based_admission_control.cpu_failover_resources_percent)
              and O(reservation_based_admission_control.memory_failover_resources_percent).
              If a user wants to override the percentage values, he has to set this field to false.
          type: bool
          default: true
        cpu_failover_resources_percent:
          description:
          - Percentage of CPU resources in the cluster to reserve for failover.
            Ignored if O(reservation_based_admission_control.auto_compute_percentages) is not set to false.
          type: int
          default: 50
        memory_failover_resources_percent:
          description:
          - Percentage of memory resources in the cluster to reserve for failover.
            Ignored if O(reservation_based_admission_control.auto_compute_percentages) is not set to false.
          type: int
          default: 50
      type: dict
    failover_host_admission_control:
      description:
      - Configure dedicated failover hosts.
      - O(slot_based_admission_control), O(reservation_based_admission_control) and O(failover_host_admission_control) are mutually exclusive.
      suboptions:
        failover_hosts:
          description:
            - List of dedicated failover hosts.
          type: list
          required: true
          elements: str
      type: dict
    ha_vm_failure_interval:
      description:
      - The number of seconds after which virtual machine is declared as failed
        if no heartbeat has been received.
      - This setting is only valid if O(ha_vm_monitoring=vmAndAppMonitoring) or O(ha_vm_monitoring=vmMonitoringOnly).
      - Unit is seconds.
      type: int
      default: 30
    ha_vm_min_up_time:
      description:
      - The number of seconds for the virtual machine's heartbeats to stabilize after
        the virtual machine has been powered on.
      - Valid only when O(ha_vm_monitoring=vmAndAppMonitoring) or O(ha_vm_monitoring=vmMonitoringOnly).
      - Unit is seconds.
      type: int
      default: 120
    ha_vm_max_failures:
      description:
      - Maximum number of failures and automated resets allowed during the time
       that O(ha_vm_max_failure_window) specifies.
      - Valid only when O(ha_vm_monitoring=vmAndAppMonitoring) or O(ha_vm_monitoring=vmMonitoringOnly).
      type: int
      default: 3
    ha_vm_max_failure_window:
      description:
      - The number of seconds for the window during which up to O(ha_vm_max_failures) resets
        can occur before automated responses stop.
      - Valid only when O(ha_vm_monitoring=vmAndAppMonitoring) or O(ha_vm_monitoring=vmMonitoringOnly).
      - Unit is seconds.
      - Default specifies no failure window.
      type: int
      default: -1
    ha_restart_priority:
      description:
      - Priority HA gives to a virtual machine if sufficient capacity is not available
        to power on all failed virtual machines.
      - Valid only when O(ha_vm_monitoring=vmAndAppMonitoring) or O(ha_vm_monitoring=vmMonitoringOnly).
      - If set to V(disabled), then HA is disabled for this virtual machine.
      - If set to V(high), then virtual machine with this priority have a higher chance of powering on after a failure,
        when there is insufficient capacity on hosts to meet all virtual machine needs.
      - If set to V(medium), then virtual machine with this priority have an intermediate chance of powering on after a failure,
        when there is insufficient capacity on hosts to meet all virtual machine needs.
      - If set to V(low), then virtual machine with this priority have a lower chance of powering on after a failure,
        when there is insufficient capacity on hosts to meet all virtual machine needs.
      type: str
      default: 'medium'
      choices: [ 'disabled', 'high', 'low', 'medium' ]
    advanced_settings:
      description:
      - A dictionary of advanced HA settings.
      default: {}
      type: dict
    heartbeat_datastores:
      description:
      - A list of the heartbeat datastores.
      - If list ist [] then all datastores of the cluster will be set as heartbeat_datastores.
      type: list
      elements: str
    heartbeat_datastore_candidate_policy:
      description:
      - Heartbeat datastore selection policy
      - allFeasibleDs -> Automatically select datastores accessible from the hosts. Causes that C(heartbeat_datastores) will be ignored.
      - userSelectedDs -> Use datastores only from the specified list.
      - allFeasibleDsWithUserPreference -> Use datastores from the specified list and complement automatically if needed.
      type: str
      choices: ['allFeasibleDs', 'userSelectedDs', 'allFeasibleDsWithUserPreference']
    apd_response:
      description:
      - VM storage protection setting for storage failures categorized as All Paths Down (APD).
      type: str
      default: 'warning'
      choices: [ 'disabled', 'warning', 'restartConservative', 'restartAggressive' ]
    apd_delay:
      description:
      - The response recovery delay time in sec for storage failures categorized as All Paths Down (APD).
      - Only set if O(apd_response=restartConservative) or O(apd_response=restartAggressive).
      type: int
      default: 180
    apd_reaction:
      description:
      - VM response recovery reaction for storage failures categorized as All Paths Down (APD).
      - Only set if O(apd_response=restartConservative) or O(apd_response=restartAggressive).
      type: str
      default: 'reset'
      choices: [ 'reset', 'none' ]
    pdl_response:
      description:
      - VM storage protection setting for storage failures categorized as Permenant Device Loss (PDL).
      type: str
      default: 'warning'
      choices: [ 'disabled', 'warning', 'restartAggressive' ]
extends_documentation_fragment:
- community.vmware.vmware.documentation

'''

EXAMPLES = r'''
- name: Enable HA without admission control
  community.vmware.vmware_cluster_ha:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: datacenter
    cluster_name: cluster
    enable: true
  delegate_to: localhost

- name: Enable HA and VM monitoring without admission control
  community.vmware.vmware_cluster_ha:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter_name: DC0
    cluster_name: "{{ cluster_name }}"
    enable: true
    ha_vm_monitoring: vmMonitoringOnly
  delegate_to: localhost

- name: Enable HA with admission control reserving 50% of resources for HA
  community.vmware.vmware_cluster_ha:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: datacenter
    cluster_name: cluster
    enable: true
    reservation_based_admission_control:
      auto_compute_percentages: false
      failover_level: 1
      cpu_failover_resources_percent: 50
      memory_failover_resources_percent: 50
  delegate_to: localhost
'''

RETURN = r'''#
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import (
    PyVmomi,
    TaskError,
    find_datacenter_by_name,
    vmware_argument_spec,
    wait_for_task,
    option_diff,
    find_datastore_by_name,
)
from ansible.module_utils._text import to_native


class VMwareCluster(PyVmomi):
    def __init__(self, module):
        super(VMwareCluster, self).__init__(module)
        self.cluster_name = module.params['cluster_name']
        self.datacenter_name = module.params['datacenter']
        self.enable_ha = module.params['enable']
        self.datacenter = None
        self.cluster = None
        self.host_isolation_response = getattr(vim.cluster.DasVmSettings.IsolationResponse, self.params.get('host_isolation_response'))

        if self.enable_ha and (
            self.params.get("slot_based_admission_control")
            or self.params.get("reservation_based_admission_control")
            or self.params.get("failover_host_admission_control")
        ):
            self.ha_admission_control = True
        else:
            self.ha_admission_control = False

        self.datacenter = find_datacenter_by_name(self.content, self.datacenter_name)
        if self.datacenter is None:
            self.module.fail_json(msg="Datacenter %s does not exist." % self.datacenter_name)

        self.cluster = self.find_cluster_by_name(cluster_name=self.cluster_name, datacenter_name=self.datacenter)
        if self.cluster is None:
            self.module.fail_json(msg="Cluster %s does not exist." % self.cluster_name)

        self.advanced_settings = self.params.get('advanced_settings')
        if self.advanced_settings:
            self.changed_advanced_settings = option_diff(self.advanced_settings, self.cluster.configurationEx.dasConfig.option, False)
        else:
            self.changed_advanced_settings = None

        if self.params.get('heartbeat_datastore_candidate_policy') == "allFeasibleDs":
            self.heartbeat_datastores_var = None
        else:
            self.heartbeat_datastores_var = self.params.get('heartbeat_datastores')

        if self.heartbeat_datastores_var == []:
            self.heartbeat_datastores = self.cluster.datastore
        else:
            self.heartbeat_datastores = []
            for ds_name in (self.heartbeat_datastores_var or []):
                ds = find_datastore_by_name(self.content, ds_name, self.datacenter)
                if ds is None:
                    self.module.fail_json(msg="Datastore %s does not exist." % ds_name)
                else:
                    self.heartbeat_datastores.append(ds)

    def get_failover_hosts(self):
        """
        Get failover hosts for failover_host_admission_control policy
        Returns: List of ESXi hosts sorted by name

        """
        policy = self.params.get('failover_host_admission_control')
        hosts = []
        all_hosts = dict((h.name, h) for h in self.get_all_hosts_by_cluster(self.cluster_name))
        for host in policy.get('failover_hosts'):
            if host in all_hosts:
                hosts.append(all_hosts.get(host))
            else:
                self.module.fail_json(msg="Host %s is not a member of cluster %s." % (host, self.cluster_name))
        hosts.sort(key=lambda h: h.name)
        return hosts

    def check_ha_config_diff(self):
        """
        Check HA configuration diff
        Returns: True if there is diff, else False

        """
        das_config = self.cluster.configurationEx.dasConfig
        if das_config.enabled != self.enable_ha:
            return True

        if self.enable_ha and (
            das_config.vmMonitoring != self.params.get("ha_vm_monitoring")
            or das_config.hostMonitoring != self.params.get("ha_host_monitoring")
            or das_config.admissionControlEnabled != self.ha_admission_control
            or self.params.get("heartbeat_datastore_candidate_policy")  # Only needed if no default value is there
            and das_config.heartbeat_datastore_candidate_policy != self.params.get("heartbeat_datastore_candidate_policy")
            or self.heartbeat_datastores_var  # Only needed if no default value is there
            and len([ds for ds in das_config.heartbeatDatastore if ds.name not in set(ds.name for ds in self.heartbeat_datastores)]) != 0
            or das_config.defaultVmSettings.restartPriority
            != self.params.get("ha_restart_priority")
            or das_config.defaultVmSettings.isolationResponse
            != self.host_isolation_response
            or das_config.defaultVmSettings.vmToolsMonitoringSettings.vmMonitoring
            != self.params.get("ha_vm_monitoring")
            or das_config.defaultVmSettings.vmToolsMonitoringSettings.failureInterval
            != self.params.get("ha_vm_failure_interval")
            or das_config.defaultVmSettings.vmToolsMonitoringSettings.minUpTime
            != self.params.get("ha_vm_min_up_time")
            or das_config.defaultVmSettings.vmToolsMonitoringSettings.maxFailures
            != self.params.get("ha_vm_max_failures")
            or das_config.defaultVmSettings.vmToolsMonitoringSettings.maxFailureWindow
            != self.params.get("ha_vm_max_failure_window")
            or das_config.defaultVmSettings.vmComponentProtectionSettings.vmStorageProtectionForAPD
            != self.params.get("apd_response")
            or das_config.defaultVmSettings.vmComponentProtectionSettings.vmStorageProtectionForPDL
            != self.params.get("pdl_response")
        ):
            return True

        if self.ha_admission_control:
            if self.params.get('slot_based_admission_control'):
                policy = self.params.get('slot_based_admission_control')
                if not isinstance(das_config.admissionControlPolicy, vim.cluster.FailoverLevelAdmissionControlPolicy) or \
                        das_config.admissionControlPolicy.failoverLevel != policy.get('failover_level'):
                    return True
            elif self.params.get('reservation_based_admission_control'):
                policy = self.params.get('reservation_based_admission_control')
                auto_compute_percentages = policy.get('auto_compute_percentages')
                if not isinstance(das_config.admissionControlPolicy, vim.cluster.FailoverResourcesAdmissionControlPolicy) or \
                        das_config.admissionControlPolicy.autoComputePercentages != auto_compute_percentages or \
                        das_config.admissionControlPolicy.failoverLevel != policy.get('failover_level'):
                    return True
                if not auto_compute_percentages:
                    if das_config.admissionControlPolicy.cpuFailoverResourcesPercent != policy.get('cpu_failover_resources_percent') or \
                            das_config.admissionControlPolicy.memoryFailoverResourcesPercent != policy.get('memory_failover_resources_percent'):
                        return True
            elif self.params.get('failover_host_admission_control'):
                policy = self.params.get('failover_host_admission_control')
                if not isinstance(das_config.admissionControlPolicy, vim.cluster.FailoverHostAdmissionControlPolicy):
                    return True
                das_config.admissionControlPolicy.failoverHosts.sort(key=lambda h: h.name)
                if das_config.admissionControlPolicy.failoverHosts != self.get_failover_hosts():
                    return True

        if self.params.get('apd_response') != 'disabled' and self.params.get('apd_response') != 'warning':
            if das_config.defaultVmSettings.vmComponentProtectionSettings.vmTerminateDelayForAPDSec != self.params.get('apd_delay'):
                return True
            if das_config.defaultVmSettings.vmComponentProtectionSettings.vmReactionOnAPDCleared != self.params.get('apd_reaction'):
                return True

        if self.changed_advanced_settings:
            return True

        return False

    def configure_ha(self):
        """
        Manage HA Configuration

        """
        changed, result = False, None

        if self.check_ha_config_diff():
            if not self.module.check_mode:
                cluster_config_spec = vim.cluster.ConfigSpecEx()
                cluster_config_spec.dasConfig = vim.cluster.DasConfigInfo()
                cluster_config_spec.dasConfig.enabled = self.enable_ha

                if self.enable_ha:
                    vm_tool_spec = vim.cluster.VmToolsMonitoringSettings()
                    vm_tool_spec.enabled = True
                    vm_tool_spec.vmMonitoring = self.params.get('ha_vm_monitoring')
                    vm_tool_spec.failureInterval = self.params.get('ha_vm_failure_interval')
                    vm_tool_spec.minUpTime = self.params.get('ha_vm_min_up_time')
                    vm_tool_spec.maxFailures = self.params.get('ha_vm_max_failures')
                    vm_tool_spec.maxFailureWindow = self.params.get('ha_vm_max_failure_window')

                    das_vm_config = vim.cluster.DasVmSettings()
                    das_vm_config.restartPriority = self.params.get('ha_restart_priority')
                    das_vm_config.isolationResponse = self.host_isolation_response
                    das_vm_config.vmToolsMonitoringSettings = vm_tool_spec

                    das_vm_config.vmComponentProtectionSettings = vim.cluster.VmComponentProtectionSettings()
                    das_vm_config.vmComponentProtectionSettings.vmStorageProtectionForAPD = self.params.get('apd_response')
                    if self.params.get('apd_response') != 'disabled' and self.params.get('apd_response') != 'warning':
                        das_vm_config.vmComponentProtectionSettings.vmTerminateDelayForAPDSec = self.params.get('apd_delay')
                        das_vm_config.vmComponentProtectionSettings.vmReactionOnAPDCleared = self.params.get('apd_reaction')
                    das_vm_config.vmComponentProtectionSettings.vmStorageProtectionForPDL = self.params.get('pdl_response')
                    if (self.params['apd_response'] != "disabled" or self.params['pdl_response'] != "disabled"):
                        cluster_config_spec.dasConfig.vmComponentProtecting = 'enabled'
                    else:
                        cluster_config_spec.dasConfig.vmComponentProtecting = 'disabled'

                    cluster_config_spec.dasConfig.defaultVmSettings = das_vm_config

                cluster_config_spec.dasConfig.admissionControlEnabled = self.ha_admission_control

                if self.ha_admission_control:
                    if self.params.get('slot_based_admission_control'):
                        cluster_config_spec.dasConfig.admissionControlPolicy = vim.cluster.FailoverLevelAdmissionControlPolicy()
                        policy = self.params.get('slot_based_admission_control')
                        cluster_config_spec.dasConfig.admissionControlPolicy.failoverLevel = policy.get('failover_level')
                    elif self.params.get('reservation_based_admission_control'):
                        cluster_config_spec.dasConfig.admissionControlPolicy = vim.cluster.FailoverResourcesAdmissionControlPolicy()
                        policy = self.params.get('reservation_based_admission_control')
                        auto_compute_percentages = policy.get('auto_compute_percentages')
                        cluster_config_spec.dasConfig.admissionControlPolicy.autoComputePercentages = auto_compute_percentages
                        cluster_config_spec.dasConfig.admissionControlPolicy.failoverLevel = policy.get('failover_level')
                        if not auto_compute_percentages:
                            cluster_config_spec.dasConfig.admissionControlPolicy.cpuFailoverResourcesPercent = \
                                policy.get('cpu_failover_resources_percent')
                            cluster_config_spec.dasConfig.admissionControlPolicy.memoryFailoverResourcesPercent = \
                                policy.get('memory_failover_resources_percent')
                    elif self.params.get('failover_host_admission_control'):
                        cluster_config_spec.dasConfig.admissionControlPolicy = vim.cluster.FailoverHostAdmissionControlPolicy()
                        policy = self.params.get('failover_host_admission_control')
                        cluster_config_spec.dasConfig.admissionControlPolicy.failoverHosts = self.get_failover_hosts()

                cluster_config_spec.dasConfig.hostMonitoring = self.params.get('ha_host_monitoring')
                cluster_config_spec.dasConfig.vmMonitoring = self.params.get('ha_vm_monitoring')

                if self.params.get("heartbeat_datastore_candidate_policy"):
                    cluster_config_spec.dasConfig.hBDatastoreCandidatePolicy = self.params.get("heartbeat_datastore_candidate_policy")

                if self.heartbeat_datastores_var:
                    cluster_config_spec.dasConfig.heartbeatDatastore = self.heartbeat_datastores

                if self.changed_advanced_settings:
                    cluster_config_spec.dasConfig.option = self.changed_advanced_settings

                try:
                    task = self.cluster.ReconfigureComputeResource_Task(cluster_config_spec, True)
                    changed, result = wait_for_task(task)
                except vmodl.RuntimeFault as runtime_fault:
                    self.module.fail_json(msg=to_native(runtime_fault.msg))
                except vmodl.MethodFault as method_fault:
                    self.module.fail_json(msg=to_native(method_fault.msg))
                except TaskError as task_e:
                    self.module.fail_json(msg=to_native(task_e))
                except Exception as generic_exc:
                    self.module.fail_json(msg="Failed to update cluster"
                                              " due to generic exception %s" % to_native(generic_exc))
            else:
                changed = True

        self.module.exit_json(changed=changed, result=result)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        cluster_name=dict(type='str', required=True),
        datacenter=dict(type='str', required=True, aliases=['datacenter_name']),
        # HA
        enable=dict(type='bool', default=True),
        ha_host_monitoring=dict(type='str',
                                default='enabled',
                                choices=['enabled', 'disabled']),
        host_isolation_response=dict(type='str',
                                     default='none',
                                     choices=['none', 'powerOff', 'shutdown']),
        advanced_settings=dict(type='dict', default=dict(), required=False),
        heartbeat_datastores=dict(type='list', elements='str', required=False),
        heartbeat_datastore_candidate_policy=dict(type='str',
                                                  required=False,
                                                  choices=['allFeasibleDs', 'userSelectedDs', 'allFeasibleDsWithUserPreference']),
        # HA VM Monitoring related parameters
        ha_vm_monitoring=dict(type='str',
                              choices=['vmAndAppMonitoring', 'vmMonitoringOnly', 'vmMonitoringDisabled'],
                              default='vmMonitoringDisabled'),
        ha_vm_failure_interval=dict(type='int', default=30),
        ha_vm_min_up_time=dict(type='int', default=120),
        ha_vm_max_failures=dict(type='int', default=3),
        ha_vm_max_failure_window=dict(type='int', default=-1),

        ha_restart_priority=dict(type='str',
                                 choices=['high', 'low', 'medium', 'disabled'],
                                 default='medium'),
        # HA Admission Control related parameters
        slot_based_admission_control=dict(type='dict', options=dict(
            failover_level=dict(type='int', required=True),
        )),
        reservation_based_admission_control=dict(type='dict', options=dict(
            auto_compute_percentages=dict(type='bool', default=True),
            failover_level=dict(type='int', required=True),
            cpu_failover_resources_percent=dict(type='int', default=50),
            memory_failover_resources_percent=dict(type='int', default=50),
        )),
        failover_host_admission_control=dict(type='dict', options=dict(
            failover_hosts=dict(type='list', elements='str', required=True),
        )),
        apd_response=dict(type='str',
                          choices=['disabled', 'warning', 'restartConservative', 'restartAggressive'],
                          default='warning'),
        apd_delay=dict(type='int', default=180),
        apd_reaction=dict(type='str',
                          choices=['reset', 'none'],
                          default='reset'),
        pdl_response=dict(type='str',
                          choices=['disabled', 'warning', 'restartAggressive'],
                          default='warning'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['slot_based_admission_control', 'reservation_based_admission_control', 'failover_host_admission_control']
        ]
    )

    vmware_cluster_ha = VMwareCluster(module)
    vmware_cluster_ha.configure_ha()


if __name__ == '__main__':
    main()
