#!/usr/bin/python
# -*- coding: utf-8 -*-

# This module is also sponsored by E.T.A.I. (www.etai.fr)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_guest
short_description: Manages virtual machines in vCenter
description: >
   This module can be used to create new virtual machines from templates or other virtual machines,
   manage power state of virtual machine such as power on, power off, suspend, shutdown, reboot, restart etc.,
   modify various virtual machine components like network, disk, customization etc.,
   rename a virtual machine and remove a virtual machine with associated components.
author:
- Loic Blot (@nerzhul) <loic.blot@unix-experience.fr>
- Philippe Dellaert (@pdellaert) <philippe@dellaert.org>
- Abhijeet Kasurde (@Akasurde) <akasurde@redhat.com>
notes:
    - Please make sure that the user used for M(community.vmware.vmware_guest) has the correct level of privileges.
    - For example, following is the list of minimum privileges required by users to create virtual machines.
    - "   DataStore > Allocate Space"
    - "   Virtual Machine > Configuration > Add New Disk"
    - "   Virtual Machine > Configuration > Add or Remove Device"
    - "   Virtual Machine > Inventory > Create New"
    - "   Network > Assign Network"
    - "   Resource > Assign Virtual Machine to Resource Pool"
    - "Module may require additional privileges as well, which may be required for gathering facts - e.g. ESXi configurations."
    - Use SCSI disks instead of IDE when you want to expand online disks by specifying a SCSI controller.
    - Uses SysPrep for Windows VM (depends on 'guest_id' parameter match 'win') with PyVmomi.
    - In order to change the VM's parameters (e.g. number of CPUs), the VM must be powered off unless the hot-add
      support is enabled and the O(state=present) must be used to apply the changes.
    - "For additional information please visit Ansible VMware community wiki - U(https://github.com/ansible/community/wiki/VMware)."
options:
  state:
    description:
    - Specify the state the virtual machine should be in.
    - If V(present) and virtual machine exists, ensure the virtual machine configurations conforms to task arguments.
    - If V(absent) and virtual machine exists, then the specified virtual machine is removed with it's associated components.
    - If set to one of V(poweredon), V(powered-on), V(poweredoff), V(powered-off),
      V(present), V(restarted), V(suspended) and virtual machine does not exists, virtual machine is deployed with the given parameters.
    - If set to V(poweredon) or V(powered-on) and virtual machine exists with powerstate other than powered on,
      then the specified virtual machine is powered on.
    - If set to V(poweredoff) or V(powered-off) and virtual machine exists with powerstate other than powered off,
      then the specified virtual machine is powered off.
    - If set to V(restarted) and virtual machine exists, then the virtual machine is restarted.
    - If set to V(suspended) and virtual machine exists, then the virtual machine is set to suspended mode.
    - If set to V(shutdownguest) or V(shutdown-guest) and virtual machine exists, then the virtual machine is shutdown.
    - If set to V(rebootguest) or V(reboot-guest) and virtual machine exists, then the virtual machine is rebooted.
    default: present
    type: str
    choices: [ absent, poweredon, powered-on, poweredoff, powered-off, present, rebootguest, reboot-guest, restarted, suspended, shutdownguest, shutdown-guest]
  name:
    description:
    - Name of the virtual machine to work with.
    - Virtual machine names in vCenter are not necessarily unique, which may be problematic, see O(name_match).
    - If multiple virtual machines with same name exists, then O(folder) is required parameter to
      identify uniqueness of the virtual machine.
    - This parameter is required, if O(state=poweredon), O(state=powered-on), O(state=poweredoff), O(state=powered-off),
      O(state=present), O(state=restarted), O(state=suspended) and virtual machine does not exists.
    type: str
  name_match:
    description:
    - If multiple virtual machines matching the name, use the first or last found.
    default: 'first'
    choices: [ 'first', 'last' ]
    type: str
  uuid:
    description:
    - UUID of the virtual machine to manage if known, this is VMware's unique identifier.
    - This is required if O(name) is not supplied.
    - If virtual machine does not exists, then this parameter is ignored.
    - Please note that a supplied UUID will be ignored on virtual machine creation, as VMware creates the UUID internally.
    type: str
  use_instance_uuid:
    description:
    - Whether to use the VMware instance UUID rather than the BIOS UUID.
    default: false
    type: bool
  template:
    description:
    - Template or existing virtual machine used to create new virtual machine.
    - If this value is not set, virtual machine is created without using a template.
    - If the virtual machine already exists, this parameter will be ignored.
    - From version 2.8 onwards, absolute path to virtual machine or template can be used.
    aliases: [ 'template_src' ]
    type: str
  is_template:
    description:
    - Flag the instance as a template.
    - This will mark the given virtual machine as template.
    - Note, this may need to be done in a dedicated task invocation that is not making
      any other changes. For example, user cannot change the state from powered-on to
      powered-off AND save as template in the same task.
    - See M(community.vmware.vmware_guest) source for more details.
    default: false
    type: bool
  folder:
    description:
    - Destination folder, absolute path to find an existing guest or create the new guest.
    - "The folder should include the datacenter. ESXi's datacenter is ha-datacenter."
    - 'If multiple machines are found with same name, this parameter is used to identify'
    - 'uniqueness of the virtual machine.'
    - 'Examples:'
    - '   folder: /ha-datacenter/vm'
    - '   folder: ha-datacenter/vm'
    - '   folder: /datacenter1/vm'
    - '   folder: datacenter1/vm'
    - '   folder: /datacenter1/vm/folder1'
    - '   folder: datacenter1/vm/folder1'
    - '   folder: /folder1/datacenter1/vm'
    - '   folder: folder1/datacenter1/vm'
    - '   folder: /folder1/datacenter1/vm/folder2'
    type: str
  hardware:
    type: dict
    default: {}
    description:
    - "Manage virtual machine's hardware attributes."
    suboptions:
        hotadd_cpu:
            type: bool
            description: Allow virtual CPUs to be added while the virtual machine is running.
        hotremove_cpu:
            type: bool
            description: Allow virtual CPUs to be removed while the virtual machine is running.
        hotadd_memory:
            type: bool
            description: Allow memory to be added while the virtual machine is running.
        memory_mb:
            type: int
            description: Amount of memory in MB.
        num_cpus:
            type: int
            description:
            - Number of CPUs.
            - Must be a multiple of O(hardware.num_cpu_cores_per_socket).
            - For example, to create a VM with 2 sockets of 4 cores, specify O(hardware.num_cpus) as 8 and O(hardware.num_cpu_cores_per_socket) as 4.
        num_cpu_cores_per_socket:
            type: int
            description: Number of Cores Per Socket.
        cpu_shares_level:
            type: str
            choices: [ 'low', 'normal', 'high', 'custom' ]
            description:
            - The allocation level of CPU resources for the virtual machine.
            version_added: '3.2.0'
        cpu_shares:
            type: int
            description:
            - The number of shares of CPU allocated to this virtual machine
            - cpu_shares_level will automatically be set to 'custom'
            version_added: '3.2.0'
        vpmc_enabled:
            version_added: '3.2.0'
            type: bool
            description: Enable virtual CPU Performance Counters.
        scsi:
            type: str
            description:
            - Valid values are V(buslogic), V(lsilogic), V(lsilogicsas) and V(paravirtual).
            - V(paravirtual) is default.
            choices: [ 'buslogic', 'lsilogic', 'lsilogicsas', 'paravirtual' ]
        secure_boot:
            type: bool
            description: Whether to enable or disable (U)EFI secure boot.
        memory_reservation_lock:
            type: bool
            description:
            - If set V(true), memory resource reservation for the virtual machine.
        max_connections:
            type: int
            description:
            - Maximum number of active remote display connections for the virtual machines.
        mem_limit:
            type: int
            description:
            - The memory utilization of a virtual machine will not exceed this limit.
            - Unit is MB.
        mem_reservation:
            type: int
            description: The amount of memory resource that is guaranteed available to the virtual machine.
            aliases: [ 'memory_reservation' ]
        mem_shares_level:
            type: str
            description:
            - The allocation level of memory resources for the virtual machine.
            choices: [ 'low', 'normal', 'high', 'custom' ]
            version_added: '3.2.0'
        mem_shares:
            type: int
            description:
            - The number of shares of memory allocated to this virtual machine
            - mem_shares_level will automatically be set to 'custom'
            version_added: '3.2.0'
        cpu_limit:
            type: int
            description:
            - The CPU utilization of a virtual machine will not exceed this limit.
            - Unit is MHz.
        cpu_reservation:
            type: int
            description: The amount of CPU resource that is guaranteed available to the virtual machine.
        version:
            type: str
            description:
            - The Virtual machine hardware versions.
            - Default is 10 (ESXi 5.5 and onwards).
            - If set to V(latest), the specified virtual machine will be upgraded to the most current hardware version supported on the host.
            - Please check VMware documentation for correct virtual machine hardware version.
            - Incorrect hardware version may lead to failure in deployment. If hardware version is already equal to the given.
        boot_firmware:
            type: str
            description: Choose which firmware should be used to boot the virtual machine.
            choices: [ 'bios', 'efi' ]
        nested_virt:
            type: bool
            description:
            - Enable nested virtualization.
        virt_based_security:
            type: bool
            description:
            - Enable Virtualization Based Security feature for Windows on ESXi 6.7 and later, from hardware version 14.
            - Supported Guest OS are Windows 10 64 bit, Windows Server 2016, Windows Server 2019 and later.
            - The firmware of virtual machine must be EFI and secure boot must be enabled.
            - Virtualization Based Security depends on nested virtualization and Intel Virtualization Technology for Directed I/O.
            - Deploy on unsupported ESXi, hardware version or firmware may lead to failure or deployed VM with unexpected configurations.
        iommu:
            type: bool
            description: Flag to specify if I/O MMU is enabled for this virtual machine.
  encryption:
    type: dict
    default: {}
    description:
    - Manage virtual machine encryption settings
    version_added: '3.9.0'
    suboptions:
        encrypted_vmotion:
            type: str
            description: Controls encryption for live migrations with vmotion
            choices: ['disabled', 'opportunistic', 'required']
        encrypted_ft:
            type: str
            description: Controls encryption for fault tolerance replication
            choices: ['disabled', 'opportunistic', 'required']
  guest_id:
    type: str
    description:
    - Set the guest ID.
    - This field is required when creating a virtual machine, not required when creating from the template.
    - >
         Valid values are referenced here:
         U(https://code.vmware.com/apis/358/doc/vim.vm.GuestOsDescriptor.GuestOsIdentifier.html)
  disk:
    description:
    - A list of disks to add.
    - Shrinking disks is not supported.
    - Removing existing disks of the virtual machine is not supported.
    - 'Attributes O(disk[].controller_type), O(disk[].controller_number), O(disk[].unit_number) are used to configure multiple types of disk
      controllers and disks for creating or reconfiguring virtual machine.'
    type: list
    default: []
    elements: dict
    suboptions:
        size:
            description:
            - Disk storage size.
            - Please specify storage unit like [kb, mb, gb, tb].
            type: str
        size_kb:
            description: Disk storage size in kb.
            type: int
        size_mb:
            description: Disk storage size in mb.
            type: int
        size_gb:
            description: Disk storage size in gb.
            type: int
        size_tb:
            description: Disk storage size in tb.
            type: int
        type:
            description:
            - Type of disk.
            - If not specified, disk type is inherited from the source VM or template when cloned and thick disk, no eagerzero otherwise.
            type: str
            choices: [ 'thin', 'thick', 'eagerzeroedthick' ]
        datastore:
            type: str
            description:
            - The name of datastore which will be used for the disk.
            - If O(disk[].autoselect_datastore) is set to True, will select the less used datastore whose name contains this "disk.datastore" string.
        filename:
            type: str
            description:
            - Existing disk image to be used.
            - Filename must already exist on the datastore.
            - Specify filename string in C([datastore_name] path/to/file.vmdk) format.
        autoselect_datastore:
            type: bool
            description:
            - Select the less used datastore.
            - O(disk[].datastore) and O(disk[].autoselect_datastore) will not be used if O(datastore) is specified outside this O(disk[]) configuration.
        disk_mode:
            type: str
            choices: ['persistent', 'independent_persistent', 'independent_nonpersistent']
            description:
            - Type of disk mode.
            - If V(persistent) specified, changes are immediately and permanently written to the virtual disk. This is default.
            - If V(independent_persistent) specified, same as persistent, but not affected by snapshots.
            - If V(independent_nonpersistent) specified, changes to virtual disk are made to a redo log and discarded at power off,
              but not affected by snapshots.
        controller_type:
            type: str
            choices: ['buslogic', 'lsilogic', 'lsilogicsas', 'paravirtual', 'sata', 'nvme']
            description:
            - Type of disk controller.
              Set this type on not supported ESXi or VM hardware version will lead to failure in deployment.
            - When set to V(sata), please make sure O(disk[].unit_number) is correct and not used by SATA CDROMs.
            - If set to V(sata) type, please make sure O(disk[].controller_number) and O(disk[].unit_number) are set correctly when O(cdrom=sata).
        controller_number:
            type: int
            choices: [0, 1, 2, 3]
            description:
            - Disk controller bus number.
            - The maximum number of same type controller is 4 per VM.
        unit_number:
            type: int
            description:
            - Disk Unit Number.
            - Valid value range from 0 to 15 for SCSI controller, except 7.
            - Valid value range from 0 to 14 for NVME controller.
            - Valid value range from 0 to 29 for SATA controller.
            - O(disk[].controller_type), O(disk[].controller_number) and O(disk[].unit_number) are required when creating or reconfiguring VMs
              with multiple types of disk controllers and disks.
            - When creating new VM, the first configured disk in the O(disk[]) list will be "Hard Disk 1".
  nvdimm:
    description:
    - Add or remove a virtual NVDIMM device to the virtual machine.
    - VM virtual hardware version must be 14 or higher on vSphere 6.7 or later.
    - Verify that guest OS of the virtual machine supports PMem before adding virtual NVDIMM device.
    - Verify that you have the I(Datastore.Allocate) space privilege on the virtual machine.
    - Make sure that the host or the cluster on which the virtual machine resides has available PMem resources.
    - To add or remove virtual NVDIMM device to the existing virtual machine, it must be in power off state.
    type: dict
    default: {}
    suboptions:
        state:
             type: str
             description:
             - If set to V(absent), then the NVDIMM device with specified O(nvdimm.label) will be removed.
             choices: ['present', 'absent']
        size_mb:
            type: int
            description: Virtual NVDIMM device size in MB.
            default: 1024
        label:
             type: str
             description:
             - The label of the virtual NVDIMM device to be removed or configured, e.g., "NVDIMM 1".
             - 'This parameter is required when O(nvdimm.state=absent), or O(nvdimm.state=present) to reconfigure NVDIMM device
               size. When add a new device, please do not set.'
  cdrom:
    description:
    - A list of CD-ROM configurations for the virtual machine.
    - For V(ide) controller, hot-add or hot-remove CD-ROM is not supported.
    type: list
    default: []
    elements: dict
    suboptions:
        type:
            type: str
            description:
            - The type of CD-ROM.
            - With V(none) the CD-ROM will be disconnected but present.
            choices: [ 'none', 'client', 'iso' ]
            default: client
        iso_path:
            type: str
            description:
            - The datastore path to the ISO file to use, in the form of C([datastore1] path/to/file.iso).
            - Required if type is set V(iso).
        controller_type:
            type: str
            description:
            - When set to V(sata), please make sure O(cdrom[].unit_number) is correct and not used by SATA disks.
            choices: [ 'ide', 'sata' ]
            default: ide
        controller_number:
            type: int
            description:
            - For O(cdrom[].controller_type=ide), valid value is 0 or 1.
            - For O(cdrom[].controller_type=sata), valid value is 0 to 3.
        unit_number:
            type: int
            description:
            - For O(cdrom[].controller_type=ide), valid value is 0 or 1.
            - For O(cdrom[].controller_type=sata), valid value is 0 to 29.
            - O(cdrom[].controller_number) and O(cdrom[].unit_number) are mandatory attributes.
        state:
            type: str
            description:
            - If set to V(absent), then the specified CD-ROM will be removed.
            choices: [ 'present', 'absent' ]
            default: present
  resource_pool:
    description:
    - Use the given resource pool for virtual machine operation.
    - Resource pool should be child of the selected host parent.
    - When not specified I(Resources) is taken as default value.
    type: str
  wait_for_ip_address:
    description:
    - Wait until vCenter detects an IP address for the virtual machine.
    - This requires vmware-tools (vmtoolsd) to properly work after creation.
    - "vmware-tools needs to be installed on the given virtual machine in order to work with this parameter."
    default: false
    type: bool
  wait_for_ip_address_timeout:
    description:
    - Define a timeout (in seconds) for the wait_for_ip_address parameter.
    default: '300'
    type: int
  wait_for_customization_timeout:
    description:
    - Define a timeout (in seconds) for the wait_for_customization parameter.
    - Be careful when setting this value since the time guest customization took may differ among guest OSes.
    default: '3600'
    type: int
  wait_for_customization:
    description:
    - Wait until vCenter detects all guest customizations as successfully completed.
    - When enabled, the VM will automatically be powered on.
    - "If vCenter does not detect guest customization start or succeed, failed events after time
      O(wait_for_customization_timeout) parameter specified, warning message will be printed and task result is fail."
    default: false
    type: bool
  state_change_timeout:
    description:
    - If the O(state=shutdownguest), by default the module will return immediately after sending the shutdown signal.
    - If this argument is set to a positive integer, the module will instead wait for the virtual machine to reach the poweredoff state.
    - The value sets a timeout in seconds for the module to wait for the state change.
    default: 0
    type: int
  snapshot_src:
    description:
    - Name of the existing snapshot to use to create a clone of a virtual machine.
    - While creating linked clone using O(linked_clone) parameter, this parameter is required.
    type: str
  linked_clone:
    description:
    - Whether to create a linked clone from the snapshot specified.
    - If specified, then O(snapshot_src) is required parameter.
    default: false
    type: bool
  force:
    description:
    - Ignore warnings and complete the actions.
    - This parameter is useful while removing virtual machine which is powered on state.
    - 'This module reflects the VMware vCenter API and UI workflow, as such, in some cases the `force` flag will
       be mandatory to perform the action to ensure you are certain the action has to be taken, no matter what the consequence.
       This is specifically the case for removing a powered on the virtual machine when O(state=absent).'
    default: false
    type: bool
  delete_from_inventory:
    description:
    - Whether to delete Virtual machine from inventory or delete from disk.
    default: false
    type: bool
  datacenter:
    description:
    - Destination datacenter for the deploy operation.
    default: ha-datacenter
    type: str
  cluster:
    description:
    - The cluster name where the virtual machine will run.
    - This is a required parameter, if O(esxi_hostname) is not set.
    - O(esxi_hostname) and O(cluster) are mutually exclusive parameters.
    type: str
  esxi_hostname:
    description:
    - The ESXi hostname where the virtual machine will run.
    - This is a required parameter, if O(cluster) is not set.
    - O(esxi_hostname) and O(cluster) are mutually exclusive parameters.
    type: str
  advanced_settings:
    description:
    - Define a list of advanced settings to be added to the VMX config.
    - An advanced settings object takes the two fields C(key) and C(value).
    - Incorrect key and values will be ignored.
    elements: dict
    type: list
    default: []
  annotation:
    description:
    - A note or annotation to include in the virtual machine.
    type: str
    aliases: [ 'notes' ]
  customvalues:
    description:
    - Define a list of custom values to set on virtual machine.
    - A custom value object takes the two fields C(key) and C(value).
    - Incorrect key and values will be ignored.
    elements: dict
    type: list
    default: []
  networks:
    description:
    - A list of networks (in the order of the NICs).
    - Removing NICs is not allowed, while reconfiguring the virtual machine.
    - The I(type), I(ip), I(netmask), I(gateway), I(domain), I(dns_servers) options don't set to a guest when creating a blank new virtual machine.
      They are set by the customization via vmware-tools.
      If you want to set the value of the options to a guest, you need to clone from a template with installed OS and vmware-tools (also Perl when Linux).
    type: list
    default: []
    elements: dict
    suboptions:
        name:
            type: str
            description:
            - Name of the portgroup or distributed virtual portgroup for this interface.
            - This is required if C(vlan) isn't defined.
            - When specifying distributed virtual portgroup make sure given O(esxi_hostname) or O(cluster) is associated with it.
        vlan:
            type: int
            description:
            - VLAN number for this interface.
            - This is required if C(name) isn't defined.
        device_type:
            type: str
            description:
            - Virtual network device.
            - Valid value can be one of C(e1000), C(e1000e), C(pcnet32), C(vmxnet2), C(vmxnet3), C(sriov).
            - C(vmxnet3) is default.
            - Optional per entry.
            - Used for virtual hardware.
        mac:
            type: str
            description:
            - Customize MAC address.
            - Optional per entry.
            - Used for virtual hardware.
        dvswitch_name:
            type: str
            description:
            - Name of the distributed vSwitch.
            - Optional per entry.
            - Used for virtual hardware.
        type:
            type: str
            description:
            - Type of IP assignment.
            - Valid values are one of C(dhcp), C(static).
            - C(dhcp) is default.
            - Optional per entry.
            - Used for OS customization.
        ip:
            type: str
            description:
            - Static IP address. Implies C(type=static).
            - Optional per entry.
            - Used for OS customization.
        netmask:
            type: str
            description:
            - Static netmask required for C(ip).
            - Optional per entry.
            - Used for OS customization.
        gateway:
            type: str
            description:
            - Static gateway.
            - Optional per entry.
            - Used for OS customization.
        typev6:
            version_added: '4.1.0'
            type: str
            description:
            - Type of IP assignment.
            - Valid values are one of C(dhcp), C(static).
            - C(dhcp) is default.
            - Optional per entry.
            - Used for OS customization.
        ipv6:
            version_added: '4.1.0'
            type: str
            description:
            - Static IP address. Implies C(type=static).
            - Optional per entry.
            - Used for OS customization.
        netmaskv6:
            version_added: '4.1.0'
            type: str
            description:
            - Static netmask required for C(ip).
            - Optional per entry.
            - Used for OS customization.
        gatewayv6:
            version_added: '4.1.0'
            type: str
            description:
            - Static gateway.
            - Optional per entry.
            - Used for OS customization.
        dns_servers:
            type: str
            description:
            - DNS servers for this network interface (Windows).
            - Optional per entry.
            - Used for OS customization.
        domain:
            type: str
            description:
            - Domain name for this network interface (Windows).
            - Optional per entry.
            - Used for OS customization.
        connected:
            type: bool
            description:
            - Indicates whether the NIC is currently connected.
        start_connected:
            type: bool
            description:
            - Specifies whether or not to connect the device when the virtual machine starts.
  customization:
    description:
    - Parameters for OS customization when cloning from the template or the virtual machine, or apply to the existing virtual machine directly.
    - Not all operating systems are supported for customization with respective vCenter version,
      please check VMware documentation for respective OS customization.
    - For supported customization operating system matrix, (see U(http://partnerweb.vmware.com/programs/guestOS/guest-os-customization-matrix.pdf))
    - Linux based OSes requires Perl package to be installed for OS customizations.
    suboptions:
        existing_vm:
            type: bool
            description:
            - If set to V(true), do OS customization on the specified virtual machine directly.
            - Common for Linux and Windows customization.
        dns_servers:
            type: list
            elements: str
            description:
            - List of DNS servers to configure.
            - Common for Linux and Windows customization.
        dns_suffix:
            type: list
            elements: str
            description:
            - List of domain suffixes, also known as DNS search path.
            - Default C(domain) parameter.
            - Common for Linux and Windows customization.
        domain:
            type: str
            description:
            - DNS domain name to use.
            - Common for Linux and Windows customization.
        hostname:
            type: str
            description:
            - Computer hostname.
            - Default is shortened O(name) parameter.
            - Allowed characters are alphanumeric (uppercase and lowercase) and minus, rest of the characters are dropped as per RFC 952.
            - Common for Linux and Windows customization.
        timezone:
            type: str
            description:
            - Timezone.
            - See List of supported time zones for different vSphere versions in Linux/Unix.
            - Common for Linux and Windows customization.
            - L(Windows, https://msdn.microsoft.com/en-us/library/ms912391.aspx).
        hwclockUTC:
            type: bool
            description:
            - Specifies whether the hardware clock is in UTC or local time.
            - Specific to Linux customization.
        script_text:
            type: str
            description:
            - Script to run with shebang.
            - Needs to be enabled in vmware tools with vmware-toolbox-cmd config set deployPkg enable-custom-scripts true
            - https://docs.vmware.com/en/VMware-vSphere/7.0/com.vmware.vsphere.vm_admin.doc/GUID-9A5093A5-C54F-4502-941B-3F9C0F573A39.html
            - Specific to Linux customization.
            version_added: '3.1.0'
        autologon:
            type: bool
            description:
            - Auto logon after virtual machine customization.
            - Specific to Windows customization.
        autologoncount:
            type: int
            description:
            - Number of autologon after reboot.
            - Specific to Windows customization.
            - Ignored if O(customization.autologon) is unset or set to O(customization.autologon=false).
            - If unset, 1 will be used.
        domainadmin:
            type: str
            description:
            - User used to join in AD domain.
            - Required if O(customization.joindomain) specified.
            - Specific to Windows customization.
        domainadminpassword:
            type: str
            description:
            - Password used to join in AD domain.
            - Required if O(customization.joindomain) specified.
            - Specific to Windows customization.
        fullname:
            type: str
            description:
            - Server owner name.
            - Specific to Windows customization.
            - If unset, "Administrator" will be used as a fall-back.
        joindomain:
            type: str
            description:
            - AD domain to join.
            - Not compatible with O(customization.joinworkgroup).
            - Specific to Windows customization.
        joinworkgroup:
            type: str
            description:
            - Workgroup to join.
            - Not compatible with O(customization.joindomain).
            - Specific to Windows customization.
            - If unset, "WORKGROUP" will be used as a fall-back.
        orgname:
            type: str
            description:
            - Organization name.
            - Specific to Windows customization.
            - If unset, "ACME" will be used as a fall-back.
        password:
            type: str
            description:
            - Local administrator password.
            - If not defined, the password will be set to blank (that is, no password).
            - Specific to Windows customization.
        productid:
            type: str
            description:
            - Product ID.
            - Specific to Windows customization.
        runonce:
            type: list
            elements: str
            description:
            - List of commands to run at first user logon.
            - Specific to Windows customization.
        domain_ou:
            type: str
            description:
            - The full LDAP path name of the OU to which the computer belongs.
            - Specific to Windows customization.
            - Work for vSphere 8.0U2 and above
    type: dict
    default: {}
  vapp_properties:
    description:
    - A list of vApp properties.
    - 'For full list of attributes and types refer to: U(https://code.vmware.com/apis/704/vsphere/vim.vApp.PropertyInfo.html)'
    type: list
    default: []
    elements: dict
    suboptions:
        id:
            type: str
            description:
            - Property ID.
            - Required per entry.
        value:
            type: str
            description:
            - Property value.
        type:
            type: str
            description:
            - Value type, string type by default.
        operation:
            type: str
            description:
            - The C(remove) attribute is required only when removing properties.
  customization_spec:
    description:
    - Unique name identifying the requested customization specification.
    - If set, then overrides O(customization) parameter values.
    type: str
  datastore:
    description:
    - Specify datastore or datastore cluster to provision virtual machine.
    - This parameter takes precedence over O(disk[].datastore) parameter.
    - This parameter can be used to override datastore or datastore cluster setting
      of the virtual machine when deployed from the template.
    - Please see example for more usage.
    type: str
  convert:
    description:
    - Specify convert disk type while cloning template or virtual machine.
    choices: [ 'thin', 'thick', 'eagerzeroedthick' ]
    type: str
extends_documentation_fragment:
- community.vmware.vmware.documentation

'''

EXAMPLES = r'''
- name: Create a virtual machine on given ESXi hostname
  community.vmware.vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    folder: /DC1/vm/
    name: test_vm_0001
    state: poweredon
    guest_id: centos64Guest
    # This is hostname of particular ESXi server on which user wants VM to be deployed
    esxi_hostname: "{{ esxi_hostname }}"
    disk:
    - size_gb: 10
      type: thin
      datastore: datastore1
    hardware:
      memory_mb: 512
      num_cpus: 4
      scsi: paravirtual
    networks:
    - name: VM Network
      mac: aa:bb:dd:aa:00:14
      ip: 10.10.10.100
      netmask: 255.255.255.0
      device_type: vmxnet3
    wait_for_ip_address: true
    wait_for_ip_address_timeout: 600
  delegate_to: localhost
  register: deploy_vm

- name: Create a virtual machine from a template
  community.vmware.vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    folder: /testvms
    name: testvm_2
    state: poweredon
    template: template_el7
    disk:
    - size_gb: 10
      type: thin
      datastore: g73_datastore
    # Add another disk from an existing VMDK
    - filename: "[datastore1] testvms/testvm_2_1/testvm_2_1.vmdk"
    hardware:
      memory_mb: 512
      num_cpus: 6
      num_cpu_cores_per_socket: 3
      scsi: paravirtual
      memory_reservation_lock: true
      mem_limit: 8096
      mem_reservation: 4096
      cpu_shares_level: "high"
      mem_shares_level: "high"
      cpu_limit: 8096
      cpu_reservation: 4096
      max_connections: 5
      hotadd_cpu: true
      hotremove_cpu: true
      hotadd_memory: false
      version: 12 # Hardware version of virtual machine
      boot_firmware: "efi"
    cdrom:
        - controller_number: 0
          unit_number: 0
          state: present
          type: iso
          iso_path: "[datastore1] livecd.iso"
    networks:
    - name: VM Network
      mac: aa:bb:dd:aa:00:14
    wait_for_ip_address: true
  delegate_to: localhost
  register: deploy

- name: Clone a virtual machine from Windows template and customize
  community.vmware.vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: datacenter1
    cluster: cluster
    name: testvm-2
    template: template_windows
    networks:
    - name: VM Network
      ip: 192.168.1.100
      netmask: 255.255.255.0
      gateway: 192.168.1.1
      mac: aa:bb:dd:aa:00:14
      domain: my_domain
      dns_servers:
      - 192.168.1.1
      - 192.168.1.2
    - vlan: 1234
      type: dhcp
    customization:
      autologon: true
      dns_servers:
      - 192.168.1.1
      - 192.168.1.2
      domain: my_domain
      password: new_vm_password
      runonce:
      - powershell.exe -ExecutionPolicy Unrestricted -File C:\Windows\Temp\ConfigureRemotingForAnsible.ps1 -ForceNewSSLCert -EnableCredSSP
  delegate_to: localhost

- name:  Clone a virtual machine from Linux template and customize
  community.vmware.vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter }}"
    state: present
    folder: /DC1/vm
    template: "{{ template }}"
    name: "{{ vm_name }}"
    cluster: DC1_C1
    networks:
      - name: VM Network
        ip: 192.168.10.11
        netmask: 255.255.255.0
    wait_for_ip_address: true
    customization:
      domain: "{{ guest_domain }}"
      dns_servers:
        - 8.9.9.9
        - 7.8.8.9
      dns_suffix:
        - example.com
        - example2.com
      script_text: |
        #!/bin/bash
        touch /tmp/touch-from-playbook
  delegate_to: localhost

- name: Rename a virtual machine (requires the virtual machine's uuid)
  community.vmware.vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    uuid: "{{ vm_uuid }}"
    name: new_name
    state: present
  delegate_to: localhost

- name: Remove a virtual machine by uuid
  community.vmware.vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    uuid: "{{ vm_uuid }}"
    state: absent
  delegate_to: localhost

- name: Remove a virtual machine from inventory
  community.vmware.vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    name: vm_name
    delete_from_inventory: true
    state: absent
  delegate_to: localhost

- name: Manipulate vApp properties
  community.vmware.vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    name: vm_name
    state: present
    vapp_properties:
      - id: remoteIP
        category: Backup
        label: Backup server IP
        type: string
        value: 10.10.10.1
      - id: old_property
        operation: remove
  delegate_to: localhost

- name: Set powerstate of a virtual machine to poweroff by using UUID
  community.vmware.vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    uuid: "{{ vm_uuid }}"
    state: poweredoff
  delegate_to: localhost

- name: Deploy a virtual machine in a datastore different from the datastore of the template
  community.vmware.vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    name: "{{ vm_name }}"
    state: present
    template: "{{ template_name }}"
    # Here datastore can be different which holds template
    datastore: "{{ virtual_machine_datastore }}"
    hardware:
      memory_mb: 512
      num_cpus: 2
      scsi: paravirtual
  delegate_to: localhost

- name: Create a diskless VM
  community.vmware.vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ dc1 }}"
    state: poweredoff
    cluster: "{{ ccr1 }}"
    name: diskless_vm
    folder: /Asia-Datacenter1/vm
    guest_id: centos64Guest
    datastore: "{{ ds1 }}"
    hardware:
        memory_mb: 1024
        num_cpus: 2
        num_cpu_cores_per_socket: 1

- name: Create a VM with multiple disks of different disk controller types
  community.vmware.vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    folder: /DC1/vm/
    name: test_vm_multi_disks
    state: poweredoff
    guest_id: centos64Guest
    datastore: datastore1
    disk:
    - size_gb: 10
      controller_type: 'nvme'
      controller_number: 0
      unit_number: 0
    - size_gb: 10
      controller_type: 'paravirtual'
      controller_number: 0
      unit_number: 1
    - size_gb: 10
      controller_type: 'sata'
      controller_number: 0
      unit_number: 2
    hardware:
      memory_mb: 512
      num_cpus: 4
      version: 14
    networks:
    - name: VM Network
      device_type: vmxnet3
  delegate_to: localhost
  register: deploy_vm

- name: Create a VM with NVDIMM device
  community.vmware.vmware_guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    folder: /DC1/vm/
    name: test_vm_nvdimm
    state: poweredoff
    guest_id: centos7_64Guest
    datastore: datastore1
    hardware:
      memory_mb: 512
      num_cpus: 4
      version: 14
    networks:
    - name: VM Network
      device_type: vmxnet3
    nvdimm:
      state: present
      size_mb: 2048
  delegate_to: localhost
  register: deploy_vm
'''

RETURN = r'''
instance:
    description: metadata about the new virtual machine
    returned: always
    type: dict
    sample: None
'''

import re
import time
import string

HAS_PYVMOMI = False
try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.network import is_mac
from ansible.module_utils._text import to_text, to_native
from ansible_collections.community.vmware.plugins.module_utils.vmware import (
    gather_vm_facts,
    get_all_objs,
    compile_folder_path_for_object,
    serialize_spec,
    vmware_argument_spec,
    set_vm_power_state,
    PyVmomi,
    find_dvs_by_name,
    find_dvspg_by_name,
    wait_for_vm_ip,
    quote_obj_name,
)
from ansible_collections.community.vmware.plugins.module_utils.vm_device_helper import PyVmomiDeviceHelper
from ansible_collections.community.vmware.plugins.module_utils.vmware_spbm import SPBM


class PyVmomiCache(PyVmomi):
    """ This class caches references to objects which are requested multiples times but not modified """

    def __init__(self, content, dc_name=None):
        self.content = content
        self.dc_name = dc_name
        self.networks = {}
        self.clusters = {}
        self.esx_hosts = {}
        self.parent_datacenters = {}

    def find_obj_wrapper(self, types, name, confine_to_datacenter=True):
        """ Wrapper around PyVmomi.find_obj to set datacenter context """
        result = self.find_obj(types, name)
        if result and confine_to_datacenter:
            if to_text(self.get_parent_datacenter(result).name) != to_text(self.dc_name):
                result = None
                objects = self.get_all_objs(self.content, types, confine_to_datacenter=True)
                for obj in objects:
                    if name is None or to_text(obj.name) == to_text(name):
                        return obj
        return result

    def get_all_objs(self, content, types, confine_to_datacenter=True):
        """ Wrapper around get_all_objs to set datacenter context """
        objects = get_all_objs(content, types)
        if confine_to_datacenter:
            if hasattr(objects, 'items'):
                # resource pools come back as a dictionary
                # make a copy
                for k, v in tuple(objects.items()):
                    parent_dc = self.get_parent_datacenter(k)
                    if parent_dc.name != self.dc_name:
                        del objects[k]
            else:
                # everything else should be a list
                objects = [x for x in objects if self.get_parent_datacenter(x).name == self.dc_name]

        return objects

    def get_network(self, network_name):
        network_name = quote_obj_name(network_name)

        if network_name not in self.networks:
            networks = self.find_network_by_name(network_name)
            if len(networks) == 1:
                self.networks[network_name] = networks[0]
            else:
                self.networks[network_name] = self.find_obj_wrapper([vim.Network], network_name)

        return self.networks[network_name]

    def get_cluster(self, cluster):
        if cluster not in self.clusters:
            self.clusters[cluster] = self.find_obj_wrapper([vim.ClusterComputeResource], cluster)

        return self.clusters[cluster]

    def get_esx_host(self, host):
        if host not in self.esx_hosts:
            self.esx_hosts[host] = self.find_obj_wrapper([vim.HostSystem], host)

        return self.esx_hosts[host]

    def get_parent_datacenter(self, obj):
        """ Walk the parent tree to find the objects datacenter """
        if isinstance(obj, vim.Datacenter):
            return obj
        if obj in self.parent_datacenters:
            return self.parent_datacenters[obj]
        datacenter = None
        while True:
            if not hasattr(obj, 'parent'):
                break
            obj = obj.parent
            if isinstance(obj, vim.Datacenter):
                datacenter = obj
                break
        self.parent_datacenters[obj] = datacenter
        return datacenter


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.device_helper = PyVmomiDeviceHelper(self.module)
        self.configspec = None
        self.relospec = None
        self.change_detected = False  # a change was detected and needs to be applied through reconfiguration
        self.change_applied = False   # a change was applied meaning at least one task succeeded
        self.tracked_changes = {}     # dict of changes made or would-be-made in check mode, updated when change_applied is set
        self.customspec = None
        self.cache = PyVmomiCache(self.content, dc_name=self.params['datacenter'])

    def gather_facts(self, vm):
        return gather_vm_facts(self.content, vm)

    def remove_vm(self, vm, delete_from_inventory=False):
        # https://www.vmware.com/support/developer/converter-sdk/conv60_apireference/vim.ManagedEntity.html#destroy
        if vm.summary.runtime.powerState.lower() == 'poweredon':
            self.module.fail_json(msg="Virtual machine %s found in 'powered on' state, "
                                      "please use 'force' parameter to remove or poweroff VM "
                                      "and try removing VM again." % vm.name)
        # Delete VM from Inventory
        if delete_from_inventory:
            try:
                vm.UnregisterVM()
            except (vim.fault.TaskInProgress,
                    vmodl.RuntimeFault) as e:
                return {'changed': self.change_applied, 'failed': True, 'msg': e.msg, 'op': 'UnregisterVM'}
            self.change_applied = True
            return {'changed': self.change_applied, 'failed': False}
        # Delete VM from Disk
        task = vm.Destroy()
        error_msg = self.wait_for_task(task)
        if task.info.state == 'error':
            return {'changed': self.change_applied, 'failed': True, 'msg': error_msg, 'op': 'destroy'}
        else:
            return {'changed': self.change_applied, 'failed': False}

    def configure_guestid(self, vm_obj, vm_creation=False):
        # guest_id is not required when using templates
        if self.params['template']:
            return

        # guest_id is only mandatory on VM creation
        if vm_creation and self.params['guest_id'] is None:
            self.module.fail_json(msg="guest_id attribute is mandatory for VM creation")

        if self.params['guest_id'] and \
                (vm_obj is None or self.params['guest_id'].lower() != vm_obj.summary.config.guestId.lower()):
            self.change_detected = True
            self.configspec.guestId = self.params['guest_id']

    def configure_resource_alloc_info(self, vm_obj):
        """
        Function to configure resource allocation information about virtual machine
        :param vm_obj: VM object in case of reconfigure, None in case of deploy
        :return: None
        """
        rai_change_detected = False
        memory_allocation = vim.ResourceAllocationInfo()
        cpu_allocation = vim.ResourceAllocationInfo()

        memory_shares_info = vim.SharesInfo()
        cpu_shares_info = vim.SharesInfo()

        mem_shares_level = self.params['hardware']['mem_shares_level']
        if mem_shares_level is not None:
            memory_shares_info.level = mem_shares_level
            memory_allocation.shares = memory_shares_info

            if vm_obj is None or \
                    memory_allocation.shares.level != vm_obj.config.memoryAllocation.shares.level:
                rai_change_detected = True

        cpu_shares_level = self.params['hardware']['cpu_shares_level']
        if cpu_shares_level is not None:
            cpu_shares_info.level = cpu_shares_level
            cpu_allocation.shares = cpu_shares_info
            if vm_obj is None or \
                    cpu_allocation.shares.level != vm_obj.config.cpuAllocation.shares.level:
                rai_change_detected = True

        mem_shares = self.params['hardware']['mem_shares']
        if mem_shares is not None:
            memory_shares_info.level = 'custom'
            memory_shares_info.shares = mem_shares
            memory_allocation.shares = memory_shares_info
            if vm_obj is None or \
                    memory_allocation.shares != vm_obj.config.memoryAllocation.shares:
                rai_change_detected = True

        cpu_shares = self.params['hardware']['cpu_shares']
        if cpu_shares is not None:
            cpu_shares_info.level = 'custom'
            cpu_shares_info.shares = cpu_shares
            cpu_allocation.shares = cpu_shares_info
            if vm_obj is None or \
                    cpu_allocation.shares != vm_obj.config.cpuAllocation.shares:
                rai_change_detected = True

        mem_limit = self.params['hardware']['mem_limit']
        if mem_limit is not None:
            memory_allocation.limit = mem_limit
            if vm_obj is None or \
                    memory_allocation.limit != vm_obj.config.memoryAllocation.limit:
                rai_change_detected = True

        mem_reservation = self.params['hardware']['mem_reservation']
        if mem_reservation is not None:
            memory_allocation.reservation = mem_reservation
            if vm_obj is None or \
                    memory_allocation.reservation != vm_obj.config.memoryAllocation.reservation:
                rai_change_detected = True

        cpu_limit = self.params['hardware']['cpu_limit']
        if cpu_limit is not None:
            cpu_allocation.limit = cpu_limit
            if vm_obj is None or \
                    cpu_allocation.limit != vm_obj.config.cpuAllocation.limit:
                rai_change_detected = True

        cpu_reservation = self.params['hardware']['cpu_reservation']
        if cpu_reservation is not None:
            cpu_allocation.reservation = cpu_reservation
            if vm_obj is None or \
                    cpu_allocation.reservation != vm_obj.config.cpuAllocation.reservation:
                rai_change_detected = True

        if rai_change_detected:
            self.configspec.memoryAllocation = memory_allocation
            self.configspec.cpuAllocation = cpu_allocation
            self.change_detected = True

    def configure_cpu_and_memory(self, vm_obj, vm_creation=False):
        # set cpu/memory/etc
        num_cpus = self.params['hardware']['num_cpus']
        if num_cpus is not None:
            # check VM power state and cpu hot-add/hot-remove state before re-config VM
            # Allow VM to be powered on during this check when in check mode, when no changes will actually be made
            if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn and not self.module.check_mode:
                if not vm_obj.config.cpuHotRemoveEnabled and num_cpus < vm_obj.config.hardware.numCPU:
                    self.module.fail_json(msg="Configured cpu number is less than the cpu number of the VM, "
                                              "cpuHotRemove is not enabled")
                if not vm_obj.config.cpuHotAddEnabled and num_cpus > vm_obj.config.hardware.numCPU:
                    self.module.fail_json(msg="Configured cpu number is more than the cpu number of the VM, "
                                              "cpuHotAdd is not enabled")

            num_cpu_cores_per_socket = self.params['hardware']['num_cpu_cores_per_socket']
            if num_cpu_cores_per_socket is not None:
                if num_cpus % num_cpu_cores_per_socket != 0:
                    self.module.fail_json(msg="hardware.num_cpus attribute should be a multiple "
                                              "of hardware.num_cpu_cores_per_socket")
                if vm_obj is None or num_cpu_cores_per_socket != vm_obj.config.hardware.numCoresPerSocket:
                    self.change_detected = True
                    self.configspec.numCoresPerSocket = num_cpu_cores_per_socket
            if vm_obj is None or num_cpus != vm_obj.config.hardware.numCPU:
                self.change_detected = True
                self.configspec.numCPUs = num_cpus
        # num_cpu is mandatory for VM creation
        elif vm_creation and not self.params['template']:
            self.module.fail_json(msg="hardware.num_cpus attribute is mandatory for VM creation")

        memory_mb = self.params['hardware']['memory_mb']
        if memory_mb is not None:
            # check VM power state and memory hotadd state before re-config VM
            if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                if vm_obj.config.memoryHotAddEnabled and memory_mb < vm_obj.config.hardware.memoryMB:
                    self.module.fail_json(msg="Configured memory is less than memory size of the VM, "
                                              "operation is not supported")
                # Allow VM to be powered on during this check when in check mode, when no changes will actually be made
                elif not vm_obj.config.memoryHotAddEnabled and memory_mb != vm_obj.config.hardware.memoryMB and not self.module.check_mode:
                    self.module.fail_json(msg="memoryHotAdd is not enabled")
            if vm_obj is None or memory_mb != vm_obj.config.hardware.memoryMB:
                self.change_detected = True
                self.configspec.memoryMB = memory_mb
        # memory_mb is mandatory for VM creation
        elif vm_creation and not self.params['template']:
            self.module.fail_json(msg="hardware.memory_mb attribute is mandatory for VM creation")

        hotadd_memory = self.params['hardware']['hotadd_memory']
        if hotadd_memory is not None:
            # Allow VM to be powered on during this check when in check mode, when no changes will actually be made
            if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn and \
                    vm_obj.config.memoryHotAddEnabled != hotadd_memory and not self.module.check_mode:
                self.module.fail_json(msg="Configure hotadd memory operation is not supported when VM is power on")
            if vm_obj is None or hotadd_memory != vm_obj.config.memoryHotAddEnabled:
                self.change_detected = True
                self.configspec.memoryHotAddEnabled = hotadd_memory

        hotadd_cpu = self.params['hardware']['hotadd_cpu']
        if hotadd_cpu is not None:
            # Allow VM to be powered on during this check when in check mode, when no changes will actually be made
            if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn and \
                    vm_obj.config.cpuHotAddEnabled != hotadd_cpu and not self.module.check_mode:
                self.module.fail_json(msg="Configure hotadd cpu operation is not supported when VM is power on")
            if vm_obj is None or hotadd_cpu != vm_obj.config.cpuHotAddEnabled:
                self.change_detected = True
                self.configspec.cpuHotAddEnabled = hotadd_cpu

        hotremove_cpu = self.params['hardware']['hotremove_cpu']
        if hotremove_cpu is not None:
            # Allow VM to be powered on during this check when in check mode, when no changes will actually be made
            if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn and \
                    vm_obj.config.cpuHotRemoveEnabled != hotremove_cpu and not self.module.check_mode:
                self.module.fail_json(msg="Configure hotremove cpu operation is not supported when VM is power on")
            if vm_obj is None or hotremove_cpu != vm_obj.config.cpuHotRemoveEnabled:
                self.change_detected = True
                self.configspec.cpuHotRemoveEnabled = hotremove_cpu

        memory_reservation_lock = self.params['hardware']['memory_reservation_lock']
        if memory_reservation_lock is not None:
            if vm_obj is None or memory_reservation_lock != vm_obj.config.memoryReservationLockedToMax:
                self.change_detected = True
                self.configspec.memoryReservationLockedToMax = memory_reservation_lock

        vpmc_enabled = self.params['hardware']['vpmc_enabled']
        if vpmc_enabled is not None:
            # Allow VM to be powered on during this check when in check mode, when no changes will actually be made
            if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn and \
                    vm_obj.config.vPMCEnabled != vpmc_enabled and not self.module.check_mode:
                self.module.fail_json(msg="Configure vPMC cpu operation is not supported when VM is power on")
            if vm_obj is None or vpmc_enabled != vm_obj.config.vPMCEnabled:
                self.change_detected = True
                self.configspec.vPMCEnabled = vpmc_enabled

        boot_firmware = self.params['hardware']['boot_firmware']
        if boot_firmware is not None:
            # boot firmware re-config can cause boot issue
            if vm_obj is not None:
                return
            self.configspec.firmware = boot_firmware
            self.change_detected = True

    def sanitize_cdrom_params(self):
        cdrom_specs = []
        expected_cdrom_spec = self.params.get('cdrom')
        if expected_cdrom_spec:
            for cdrom_spec in expected_cdrom_spec:
                cdrom_spec['controller_type'] = cdrom_spec.get('controller_type')
                cdrom_spec['state'] = cdrom_spec.get('state')

                if cdrom_spec['state'] == 'present':
                    # set CDROM type is 'client' by default
                    cdrom_spec['type'] = cdrom_spec.get('type')
                    if cdrom_spec['type'] == 'iso' and not cdrom_spec.get('iso_path'):
                        self.module.fail_json(msg="cdrom.iso_path is mandatory when cdrom.type is set to iso.")

                if 'controller_number' not in cdrom_spec or 'unit_number' not in cdrom_spec:
                    self.module.fail_json(msg="'cdrom.controller_number' and 'cdrom.unit_number' are required"
                                              " parameters when configure CDROM list.")

                cdrom_ctl_num = int(cdrom_spec.get('controller_number'))
                cdrom_ctl_unit_num = int(cdrom_spec.get('unit_number'))

                if cdrom_spec['controller_type'] == 'ide' and (cdrom_ctl_num not in [0, 1] or cdrom_ctl_unit_num not in [0, 1]):
                    self.module.fail_json(msg="Invalid cdrom.controller_number: %s or cdrom.unit_number: %s, valid"
                                              " values are 0 or 1 for IDE controller."
                                              % (cdrom_spec.get('controller_number'), cdrom_spec.get('unit_number')))

                if cdrom_spec['controller_type'] == 'sata' and (cdrom_ctl_num not in range(0, 4) or cdrom_ctl_unit_num not in range(0, 30)):
                    self.module.fail_json(msg="Invalid cdrom.controller_number: %s or cdrom.unit_number: %s,"
                                              " valid controller_number value is 0-3, valid unit_number is 0-29"
                                              " for SATA controller." % (cdrom_spec.get('controller_number'),
                                                                         cdrom_spec.get('unit_number')))
                cdrom_spec['controller_number'] = cdrom_ctl_num
                cdrom_spec['unit_number'] = cdrom_ctl_unit_num

                ctl_exist = False
                for exist_spec in cdrom_specs:
                    if exist_spec.get('ctl_num') == cdrom_spec['controller_number'] and \
                            exist_spec.get('ctl_type') == cdrom_spec['controller_type']:
                        for cdrom_same_ctl in exist_spec['cdroms']:
                            if cdrom_same_ctl['unit_number'] == cdrom_spec['unit_number']:
                                self.module.fail_json(msg="Duplicate cdrom.controller_type: %s, cdrom.controller_number: %s,"
                                                          "cdrom.unit_number: %s parameters specified."
                                                          % (cdrom_spec['controller_type'], cdrom_spec['controller_number'], cdrom_spec['unit_number']))
                        ctl_exist = True
                        exist_spec['cdroms'].append(cdrom_spec)
                        break
                if not ctl_exist:
                    cdrom_specs.append({'ctl_num': cdrom_spec['controller_number'],
                                        'ctl_type': cdrom_spec['controller_type'], 'cdroms': [cdrom_spec]})

        return cdrom_specs

    def configure_cdrom(self, vm_obj):
        # Configure the VM CD-ROM
        if self.params.get('cdrom'):
            if vm_obj and vm_obj.config.template:
                # Changing CD-ROM settings on a template is not supported
                return

            self.configure_cdrom_list(vm_obj)

    def configure_cdrom_list(self, vm_obj):
        configured_cdroms = self.sanitize_cdrom_params()
        # get existing CDROM devices
        cdrom_devices = self.get_vm_cdrom_devices(vm=vm_obj)
        # get existing IDE and SATA controllers
        ide_devices = self.get_vm_ide_devices(vm=vm_obj)
        sata_devices = self.get_vm_sata_devices(vm=vm_obj)

        for expected_cdrom_spec in configured_cdroms:
            ctl_device = None
            if expected_cdrom_spec['ctl_type'] == 'ide' and ide_devices:
                for device in ide_devices:
                    if device.busNumber == expected_cdrom_spec['ctl_num']:
                        ctl_device = device
                        break
            if expected_cdrom_spec['ctl_type'] == 'sata' and sata_devices:
                for device in sata_devices:
                    if device.busNumber == expected_cdrom_spec['ctl_num']:
                        ctl_device = device
                        break
            # if not find create new ide or sata controller
            if not ctl_device:
                if expected_cdrom_spec['ctl_type'] == 'ide':
                    ide_ctl = self.device_helper.create_ide_controller(bus_number=expected_cdrom_spec['ctl_num'])
                    ctl_device = ide_ctl.device
                    self.change_detected = True
                    self.configspec.deviceChange.append(ide_ctl)
                if expected_cdrom_spec['ctl_type'] == 'sata':
                    sata_ctl = self.device_helper.create_sata_controller(bus_number=expected_cdrom_spec['ctl_num'])
                    ctl_device = sata_ctl.device
                    self.change_detected = True
                    self.configspec.deviceChange.append(sata_ctl)

            for cdrom in expected_cdrom_spec['cdroms']:
                cdrom_device = None
                iso_path = cdrom.get('iso_path')
                unit_number = cdrom.get('unit_number')
                for target_cdrom in cdrom_devices:
                    if target_cdrom.controllerKey == ctl_device.key and target_cdrom.unitNumber == unit_number:
                        cdrom_device = target_cdrom
                        break
                # create new CD-ROM
                if not cdrom_device and cdrom.get('state') != 'absent':
                    # Allow VM to be powered on during this check when in check mode, when no changes will actually be made
                    if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn and \
                            isinstance(ctl_device, vim.vm.device.VirtualIDEController) and not self.module.check_mode:
                        self.module.fail_json(msg='CD-ROM attach to IDE controller not support hot-add.')
                    if len(ctl_device.device) == 2 and isinstance(ctl_device, vim.vm.device.VirtualIDEController):
                        self.module.fail_json(msg='Maximum number of CD-ROMs attached to IDE controller is 2.')
                    if len(ctl_device.device) == 30 and isinstance(ctl_device, vim.vm.device.VirtualAHCIController):
                        self.module.fail_json(msg='Maximum number of CD-ROMs attached to SATA controller is 30.')

                    cdrom_spec = self.device_helper.create_cdrom(ctl_device=ctl_device, cdrom_type=cdrom['type'],
                                                                 iso_path=iso_path, unit_number=unit_number)
                    self.change_detected = True
                    self.configspec.deviceChange.append(cdrom_spec)
                # re-configure CD-ROM
                elif cdrom_device and cdrom.get('state') != 'absent' and \
                        not self.device_helper.is_equal_cdrom(vm_obj=vm_obj, cdrom_device=cdrom_device,
                                                              cdrom_type=cdrom['type'], iso_path=iso_path):
                    self.device_helper.update_cdrom_config(vm_obj, cdrom, cdrom_device, iso_path=iso_path)
                    cdrom_spec = vim.vm.device.VirtualDeviceSpec()
                    cdrom_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                    cdrom_spec.device = cdrom_device
                    self.change_detected = True
                    self.configspec.deviceChange.append(cdrom_spec)
                # delete CD-ROM
                elif cdrom_device and cdrom.get('state') == 'absent':
                    # Allow VM to be powered on during this check when in check mode, when no changes will actually be made
                    if vm_obj and vm_obj.runtime.powerState != vim.VirtualMachinePowerState.poweredOff and \
                            isinstance(ctl_device, vim.vm.device.VirtualIDEController) and not self.module.check_mode:
                        self.module.fail_json(msg='CD-ROM attach to IDE controller not support hot-remove.')
                    cdrom_spec = self.device_helper.remove_cdrom(cdrom_device)
                    self.change_detected = True
                    self.configspec.deviceChange.append(cdrom_spec)

    def configure_hardware_params(self, vm_obj):
        """
        Function to configure hardware related configuration of virtual machine
        Args:
            vm_obj: virtual machine object
        """
        max_connections = self.params['hardware']['max_connections']
        if max_connections is not None:
            if vm_obj is None or max_connections != vm_obj.config.maxMksConnections:
                self.change_detected = True
                self.configspec.maxMksConnections = max_connections

        nested_virt = self.params['hardware']['nested_virt']
        if nested_virt is not None:
            if vm_obj is None or nested_virt != bool(vm_obj.config.nestedHVEnabled):
                self.change_detected = True
                self.configspec.nestedHVEnabled = nested_virt

        temp_version = self.params['hardware']['version']
        if temp_version is not None:
            new_version = None
            if temp_version.lower() == 'latest':
                # Check is to make sure vm_obj is not of type template
                if vm_obj and not vm_obj.config.template:
                    config_option_descriptors = vm_obj.environmentBrowser.QueryConfigOptionDescriptor()
                    available_hw_versions = [int(option_desc.key.split("-")[1]) for option_desc in config_option_descriptors if option_desc.upgradeSupported]
                    temp_version = max(available_hw_versions)
            else:
                try:
                    temp_version = int(temp_version)
                except ValueError:
                    self.module.fail_json(msg="Failed to set hardware.version '%s' value as valid"
                                          " values are either 'latest' or a number."
                                          " Please check VMware documentation for valid VM hardware versions." % temp_version)

            if isinstance(temp_version, int):
                # Hardware version is denoted as "vmx-10"
                new_version = "vmx-%02d" % temp_version

            if vm_obj is None:
                self.change_detected = True
                self.configspec.version = new_version
            # Check is to make sure vm_obj is not of type template
            elif not vm_obj.config.template:
                # VM exists and we need to update the hardware version
                current_version = vm_obj.config.version
                # Hardware version is denoted as "vmx-10"
                version_digit = int(current_version.split("-", 1)[-1])
                if temp_version < version_digit:
                    self.module.fail_json(msg="Current hardware version '%d' which is greater than the specified"
                                          " version '%d'. Downgrading hardware version is"
                                          " not supported. Please specify version greater"
                                          " than the current version." % (version_digit,
                                                                          temp_version))
                elif temp_version > version_digit:
                    self.change_detected = True
                    self.tracked_changes['hardware.version'] = temp_version
                    self.configspec.version = new_version
                    # Only perform the upgrade if not in check mode.
                    if not self.module.check_mode:
                        task = vm_obj.UpgradeVM_Task(new_version)
                        error_msg = self.wait_for_task(task)
                        if task.info.state == 'error':
                            return {'changed': self.change_applied, 'failed': True, 'msg': error_msg, 'op': 'upgrade'}
                        self.change_applied = True

        secure_boot = self.params['hardware']['secure_boot']
        if secure_boot is not None:
            if vm_obj is None or secure_boot != vm_obj.config.bootOptions.efiSecureBootEnabled:
                self.change_detected = True
                self.configspec.bootOptions = vim.vm.BootOptions()
                self.configspec.bootOptions.efiSecureBootEnabled = secure_boot

        iommu = self.params['hardware']['iommu']
        if iommu is not None:
            if vm_obj is None or iommu != vm_obj.config.flags.vvtdEnabled:
                self.change_detected = True
                if self.configspec.flags is None:
                    self.configspec.flags = vim.vm.FlagInfo()
                self.configspec.flags.vvtdEnabled = iommu

        virt_based_security = self.params['hardware']['virt_based_security']
        if virt_based_security is not None:
            if vm_obj is None or virt_based_security != vm_obj.config.flags.vbsEnabled:
                self.change_detected = True
                if self.configspec.flags is None:
                    self.configspec.flags = vim.vm.FlagInfo()
                self.configspec.flags.vbsEnabled = virt_based_security

    def configure_encryption_params(self, vm_obj):

        encrypted_vmotion = self.params['encryption']['encrypted_vmotion']
        if encrypted_vmotion is not None:
            if vm_obj is None or encrypted_vmotion != vm_obj.config.migrateEncryption:
                self.change_detected = True
                self.configspec.migrateEncryption = encrypted_vmotion

        encrypted_ft = self.params['encryption']['encrypted_ft']
        if encrypted_ft is not None:
            if encrypted_ft == "disabled":
                encrypted_ft_cfg = "ftEncryptionDisabled"
            elif encrypted_ft == "opportunistic":
                encrypted_ft_cfg = "ftEncryptionOpportunistic"
            elif encrypted_ft == "required":
                encrypted_ft_cfg = "ftEncryptionRequired"
            if vm_obj is None or encrypted_ft_cfg != vm_obj.config.ftEncryptionMode:
                self.change_detected = True
                self.configspec.ftEncryptionMode = encrypted_ft_cfg

    def get_device_by_type(self, vm=None, type=None):
        device_list = []
        if vm is None or type is None:
            return device_list
        for device in vm.config.hardware.device:
            if isinstance(device, type):
                device_list.append(device)

        return device_list

    def get_vm_cdrom_devices(self, vm=None):
        return self.get_device_by_type(vm=vm, type=vim.vm.device.VirtualCdrom)

    def get_vm_ide_devices(self, vm=None):
        return self.get_device_by_type(vm=vm, type=vim.vm.device.VirtualIDEController)

    def get_vm_sata_devices(self, vm=None):
        return self.get_device_by_type(vm=vm, type=vim.vm.device.VirtualAHCIController)

    def get_vm_nvdimm_ctl_device(self, vm=None):
        return self.get_device_by_type(vm=vm, type=vim.vm.device.VirtualNVDIMMController)

    def get_vm_nvdimm_devices(self, vm=None):
        return self.get_device_by_type(vm=vm, type=vim.vm.device.VirtualNVDIMM)

    def configure_nvdimm(self, vm_obj):
        """
        Manage virtual NVDIMM device to the virtual machine
        Args:
            vm_obj: virtual machine object
        """
        if self.params['nvdimm']['state']:
            # Label is required when remove device
            if self.params['nvdimm']['state'] == 'absent' and not self.params['nvdimm']['label']:
                self.module.fail_json(msg="Please specify the label of virtual NVDIMM device using 'label' parameter"
                                          " when state is set to 'absent'.")
            # Reconfigure device requires VM in power off state
            if vm_obj and not vm_obj.config.template:
                # Allow VM to be powered on during this check when in check mode, when no changes will actually be made
                if vm_obj.runtime.powerState != vim.VirtualMachinePowerState.poweredOff and not self.module.check_mode:
                    self.module.fail_json(msg="VM is not in power off state, can not do virtual NVDIMM configuration.")

            nvdimm_ctl_exists = False
            if vm_obj and not vm_obj.config.template:
                # Get existing NVDIMM controller
                nvdimm_ctl = self.get_vm_nvdimm_ctl_device(vm=vm_obj)
                if len(nvdimm_ctl) != 0:
                    nvdimm_ctl_exists = True
                    nvdimm_ctl_key = nvdimm_ctl[0].key
                    if self.params['nvdimm']['label'] is not None:
                        nvdimm_devices = self.get_vm_nvdimm_devices(vm=vm_obj)
                        if len(nvdimm_devices) != 0:
                            existing_nvdimm_dev = self.device_helper.find_nvdimm_by_label(
                                nvdimm_label=self.params['nvdimm']['label'],
                                nvdimm_devices=nvdimm_devices
                            )
                            if existing_nvdimm_dev is not None:
                                if self.params['nvdimm']['state'] == 'absent':
                                    nvdimm_remove_spec = self.device_helper.remove_nvdimm(
                                        nvdimm_device=existing_nvdimm_dev
                                    )
                                    self.change_detected = True
                                    self.configspec.deviceChange.append(nvdimm_remove_spec)
                                else:
                                    if existing_nvdimm_dev.capacityInMB < self.params['nvdimm']['size_mb']:
                                        nvdimm_config_spec = self.device_helper.update_nvdimm_config(
                                            nvdimm_device=existing_nvdimm_dev,
                                            nvdimm_size=self.params['nvdimm']['size_mb']
                                        )
                                        self.change_detected = True
                                        self.configspec.deviceChange.append(nvdimm_config_spec)
                                    elif existing_nvdimm_dev.capacityInMB > self.params['nvdimm']['size_mb']:
                                        self.module.fail_json(msg="Can not change NVDIMM device size to %s MB, which is"
                                                                  " smaller than the current size %s MB."
                                                                  % (self.params['nvdimm']['size_mb'],
                                                                     existing_nvdimm_dev.capacityInMB))
            # New VM or existing VM without label specified, add new NVDIMM device
            if vm_obj is None or (vm_obj and not vm_obj.config.template and self.params['nvdimm']['label'] is None):
                if self.params['nvdimm']['state'] == 'present':
                    vc_pmem_profile_id = None
                    # Get default PMem storage policy when host is vCenter
                    if self.is_vcenter():
                        storage_profile_name = "Host-local PMem Default Storage Policy"
                        spbm = SPBM(self.module)
                        pmem_profile = spbm.find_storage_profile_by_name(profile_name=storage_profile_name)
                        if pmem_profile is None:
                            self.module.fail_json(msg="Can not find PMem storage policy with name '%s'." % storage_profile_name)
                        vc_pmem_profile_id = pmem_profile.profileId.uniqueId

                    if not nvdimm_ctl_exists:
                        nvdimm_ctl_spec = self.device_helper.create_nvdimm_controller()
                        self.configspec.deviceChange.append(nvdimm_ctl_spec)
                        nvdimm_ctl_key = nvdimm_ctl_spec.device.key

                    nvdimm_dev_spec = self.device_helper.create_nvdimm_device(
                        nvdimm_ctl_dev_key=nvdimm_ctl_key,
                        pmem_profile_id=vc_pmem_profile_id,
                        nvdimm_dev_size_mb=self.params['nvdimm']['size_mb']
                    )
                    self.change_detected = True
                    self.configspec.deviceChange.append(nvdimm_dev_spec)

    def get_vm_network_interfaces(self, vm=None):
        device_list = []
        if vm is None:
            return device_list

        for device in vm.config.hardware.device:
            for device_type in self.device_helper.nic_device_type.values():
                if isinstance(device, device_type):
                    device_list.append(device)

        return device_list

    def sanitize_network_params(self):
        """
        Sanitize user provided network provided params

        Returns: A sanitized list of network params, else fails

        """
        network_devices = list()
        # Clean up user data here
        for network in self.params['networks']:
            if 'name' not in network and 'vlan' not in network:
                self.module.fail_json(msg="Please specify at least a network name or"
                                          " a VLAN name under VM network list.")

            if 'name' in network and self.cache.get_network(network['name']) is None:
                self.module.fail_json(msg="Network '%(name)s' does not exist." % network)
            elif 'vlan' in network:
                dvps = self.cache.get_all_objs(self.content, [vim.dvs.DistributedVirtualPortgroup])
                for dvp in dvps:
                    if hasattr(dvp.config.defaultPortConfig, 'vlan') and \
                            isinstance(dvp.config.defaultPortConfig.vlan.vlanId, int) and \
                            str(dvp.config.defaultPortConfig.vlan.vlanId) == str(network['vlan']):
                        network['name'] = dvp.config.name
                        break
                    if 'dvswitch_name' in network and \
                            dvp.config.distributedVirtualSwitch.name == network['dvswitch_name'] and \
                            dvp.config.name == network['vlan']:
                        network['name'] = dvp.config.name
                        break

                    if dvp.config.name == network['vlan']:
                        network['name'] = dvp.config.name
                        break
                else:
                    self.module.fail_json(msg="VLAN '%(vlan)s' does not exist." % network)

            if 'type' in network:
                if network['type'] not in ['dhcp', 'static']:
                    self.module.fail_json(msg="Network type '%(type)s' is not a valid parameter."
                                              " Valid parameters are ['dhcp', 'static']." % network)
                if network['type'] != 'static' and ('ip' in network or 'netmask' in network):
                    self.module.fail_json(msg='Static IP information provided for network "%(name)s",'
                                              ' but "type" is set to "%(type)s".' % network)
            else:
                # Type is optional parameter, if user provided IP or Subnet assume
                # network type as 'static'
                if 'ip' in network or 'netmask' in network:
                    network['type'] = 'static'
                else:
                    # User wants network type as 'dhcp'
                    network['type'] = 'dhcp'

            if network.get('type') == 'static':
                if 'ip' in network and 'netmask' not in network:
                    self.module.fail_json(msg="'netmask' is required if 'ip' is"
                                              " specified under VM network list.")
                if 'ip' not in network and 'netmask' in network:
                    self.module.fail_json(msg="'ip' is required if 'netmask' is"
                                              " specified under VM network list.")

            if 'typev6' in network:
                if network['typev6'] not in ['dhcp', 'static']:
                    self.module.fail_json(msg="Network type '%(typev6)s' for IPv6 is not a valid parameter."
                                              " Valid parameters are ['dhcp', 'static']." % network)
                    if network['typev6'] != 'static' and ('ipv6' in network or 'netmaskv6' in network):
                        self.module.fail_json(msg='Static IPv6 information provided for network "%(name)s",'
                                                  ' but "typev6" is set to "%(typev6)s".' % network)
            else:
                # Type is optional parameter, if user provided IP or Subnet assume
                # network type as 'static'
                if 'ipv6' in network or 'netmaskv6' in network:
                    network['typev6'] = 'static'
                else:
                    # User wants network type as 'dhcp'
                    network['typev6'] = 'dhcp'

            if network.get('typev6') == 'static':
                if 'ipv6' in network and 'netmaskv6' not in network:
                    self.module.fail_json(msg="'netmaskv6' is required if 'ipv6' is"
                                              " specified under VM network list.")
                if 'ipv6' not in network and 'netmaskv6' in network:
                    self.module.fail_json(msg="'ipv6' is required if 'netmaskv6' is"
                                              " specified under VM network list.")

            if 'device_type' in network and network['device_type'] not in self.device_helper.nic_device_type.keys():
                self.module.fail_json(msg="Device type specified '%s' is not valid. Please specify correct device type"
                                          " from ['%s']." % (network['device_type'],
                                                             "', '".join(self.device_helper.nic_device_type.keys())))

            if 'mac' in network and not is_mac(network['mac']):
                self.module.fail_json(msg="Device MAC address '%s' is invalid."
                                          " Please provide correct MAC address." % network['mac'])

            network_devices.append(network)

        return network_devices

    def configure_network(self, vm_obj):
        # Ignore empty networks, this permits to keep networks when deploying a template/cloning a VM
        if not self.params['networks']:
            return

        network_devices = self.sanitize_network_params()

        # List current device for Clone or Idempotency
        current_net_devices = self.get_vm_network_interfaces(vm=vm_obj)
        if len(network_devices) < len(current_net_devices):
            self.module.fail_json(msg="Given network device list is lesser than current VM device list (%d < %d). "
                                      "Removing interfaces is not allowed"
                                      % (len(network_devices), len(current_net_devices)))

        for key in range(0, len(network_devices)):
            nic_change_detected = False
            network_name = network_devices[key]['name']
            if key < len(current_net_devices) and (vm_obj or self.params['template']):
                # We are editing existing network devices, this is either when
                # are cloning from VM or Template
                nic = vim.vm.device.VirtualDeviceSpec()
                nic.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit

                nic.device = current_net_devices[key]
                if "wake_on_lan" in network_devices[key] and \
                   nic.device.wakeOnLanEnabled != network_devices[key].get("wake_on_lan"):
                    nic.device.wakeOnLanEnabled = network_devices[key].get("wake_on_lan")
                    nic_change_detected = True
                if "start_connected" in network_devices[key] and \
                   nic.device.connectable.startConnected != network_devices[key].get("start_connected"):
                    nic.device.connectable.startConnected = network_devices[key].get("start_connected")
                    nic_change_detected = True
                if "connected" in network_devices[key] and \
                   nic.device.connectable.connected != network_devices[key].get("connected"):
                    nic.device.connectable.connected = network_devices[key].get("connected")
                    nic_change_detected = True
                if "allow_guest_control" in network_devices[key] and \
                   nic.device.connectable.allowGuestControl != network_devices[key].get("allow_guest_control"):
                    nic.device.connectable.allowGuestControl = network_devices[key].get("allow_guest_control")
                    nic_change_detected = True

                if nic.device.deviceInfo.summary != network_name:
                    if 'DVSwitch' not in nic.device.deviceInfo.summary:
                        nic.device.deviceInfo.summary = network_name
                        nic_change_detected = True
                    else:
                        pgs = self.find_network_by_name(network_name)
                        if len(pgs) == 1:
                            pg = pgs[0]
                        else:
                            pg = self.find_obj([vim.DistributedVirtualPortgroup], network_name)
                        if pg is None or nic.device.backing.port.portgroupKey != pg.key:
                            nic.device.deviceInfo.summary = network_name
                            nic_change_detected = True

                if 'device_type' in network_devices[key]:
                    device = self.device_helper.nic_device_type.get(network_devices[key]['device_type'])
                    if not isinstance(nic.device, device):
                        self.module.fail_json(msg="Changing the device type is not possible when interface is already"
                                                  " present. The failing device type is %s"
                                                  % network_devices[key]['device_type'])
                # Changing mac address has no effect when editing interface
                if 'mac' in network_devices[key] and nic.device.macAddress != current_net_devices[key].macAddress:
                    self.module.fail_json(msg="Changing MAC address has not effect when interface is already present. "
                                              "The failing new MAC address is %s" % nic.device.macAddress)

            else:
                # Default device type is vmxnet3, VMware best practice
                device_type = network_devices[key].get('device_type', 'vmxnet3')
                nic = self.device_helper.create_nic(device_type,
                                                    'Network Adapter %s' % (key + 1),
                                                    network_devices[key])
                nic.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
                nic_change_detected = True

            net_obj = self.cache.get_network(network_name)
            if hasattr(net_obj, 'portKeys'):
                # VDS switch
                pg_obj = None
                if 'dvswitch_name' in network_devices[key]:
                    dvs_name = network_devices[key]['dvswitch_name']
                    dvs_obj = find_dvs_by_name(self.content, dvs_name)
                    if dvs_obj is None:
                        self.module.fail_json(msg="Unable to find distributed virtual switch %s" % dvs_name)
                    pg_obj = find_dvspg_by_name(dvs_obj, network_name)
                    if pg_obj is None:
                        self.module.fail_json(msg="Unable to find distributed port group %s" % network_name)
                else:
                    networks = self.find_network_by_name(network_name)
                    if len(networks) == 1:
                        pg_obj = networks[0]
                    else:
                        pg_obj = self.cache.find_obj_wrapper([vim.dvs.DistributedVirtualPortgroup], network_name)

                # TODO: (akasurde) There is no way to find association between resource pool and distributed virtual portgroup
                # For now, check if we are able to find distributed virtual switch
                if not pg_obj.config.distributedVirtualSwitch:
                    self.module.fail_json(
                        msg="Failed to find distributed virtual switch which is associated with"
                        " distributed virtual portgroup '%s'. Make sure hostsystem is associated with"
                        " the given distributed virtual portgroup. Also, check if user has correct"
                        " permission to access distributed virtual switch in the given portgroup."
                        % pg_obj.name
                    )
                if nic.device.backing and (
                    not hasattr(nic.device.backing, "port")
                    or (
                        nic.device.backing.port.portgroupKey != pg_obj.key
                        or nic.device.backing.port.switchUuid
                        != pg_obj.config.distributedVirtualSwitch.uuid
                    )
                ):
                    nic_change_detected = True

                dvs_port_connection = vim.dvs.PortConnection()
                dvs_port_connection.portgroupKey = pg_obj.key
                # If user specifies distributed port group without associating to the hostsystem on which
                # virtual machine is going to be deployed then we get error. We can infer that there is no
                # association between given distributed port group and host system.
                host_system = self.params.get('esxi_hostname')
                if host_system and host_system not in [host.config.host.name for host in pg_obj.config.distributedVirtualSwitch.config.host]:
                    self.module.fail_json(msg="It seems that host system '%s' is not associated with distributed"
                                              " virtual portgroup '%s'. Please make sure host system is associated"
                                              " with given distributed virtual portgroup" % (host_system, pg_obj.name))
                dvs_port_connection.switchUuid = pg_obj.config.distributedVirtualSwitch.uuid
                nic.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                nic.device.backing.port = dvs_port_connection

            elif isinstance(net_obj, vim.OpaqueNetwork):
                # NSX-T Logical Switch
                nic.device.backing = vim.vm.device.VirtualEthernetCard.OpaqueNetworkBackingInfo()
                network_id = net_obj.summary.opaqueNetworkId
                nic.device.backing.opaqueNetworkType = 'nsx.LogicalSwitch'
                nic.device.backing.opaqueNetworkId = network_id
                nic.device.deviceInfo.summary = 'nsx.LogicalSwitch: %s' % network_id
                nic_change_detected = True
            else:
                # vSwitch
                if not isinstance(nic.device.backing, vim.vm.device.VirtualEthernetCard.NetworkBackingInfo):
                    nic.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                    nic_change_detected = True

                if nic.device.backing.network != net_obj:
                    nic.device.backing.network = net_obj
                    nic_change_detected = True

                if nic.device.backing.deviceName != network_name:
                    nic.device.backing.deviceName = network_name
                    nic_change_detected = True

            if nic_change_detected:
                # Change to fix the issue found while configuring opaque network
                # VMs cloned from a template with opaque network will get disconnected
                # Replacing deprecated config parameter with relocation Spec
                if isinstance(net_obj, vim.OpaqueNetwork):
                    self.relospec.deviceChange.append(nic)
                else:
                    self.configspec.deviceChange.append(nic)
                self.change_detected = True

    def set_vapp_properties(self, property_spec):
        # Sets the values in property_info
        property_info = vim.vApp.PropertyInfo()
        property_info.classId = property_spec.get('classId')
        property_info.instanceId = property_spec.get('instanceId')
        property_info.id = property_spec.get('id')
        property_info.category = property_spec.get('category')
        property_info.label = property_spec.get('label')
        property_info.type = property_spec.get('type', 'string')
        property_info.userConfigurable = property_spec.get('userConfigurable', True)
        property_info.defaultValue = property_spec.get('defaultValue')
        property_info.value = property_spec.get('value', '')
        property_info.description = property_spec.get('description')
        return property_info

    def configure_vapp_properties(self, vm_obj):
        if not self.params['vapp_properties']:
            return

        for x in self.params['vapp_properties']:
            if not x.get('id'):
                self.module.fail_json(msg="id is required to set vApp property")

        new_vmconfig_spec = vim.vApp.VmConfigSpec()

        if vm_obj:
            # VM exists
            orig_spec = vm_obj.config.vAppConfig
            orig_properties = orig_spec.property if orig_spec is not None else []

            vapp_properties_current = dict((x.id, x) for x in orig_properties)
            vapp_properties_to_change = dict((x['id'], x) for x in self.params['vapp_properties'])

            # each property must have a unique key
            # init key counter with max value + 1
            all_keys = [x.key for x in orig_properties]
            new_property_index = max(all_keys) + 1 if all_keys else 0

            for property_id, property_spec in vapp_properties_to_change.items():
                is_property_changed = False
                new_vapp_property_spec = vim.vApp.PropertySpec()

                if property_id in vapp_properties_current:
                    if property_spec.get('operation') == 'remove':
                        new_vapp_property_spec.operation = 'remove'
                        new_vapp_property_spec.removeKey = vapp_properties_current[property_id].key
                        is_property_changed = True
                    else:
                        # this is 'edit' branch
                        new_vapp_property_spec.operation = 'edit'
                        new_vapp_property_spec.info = vapp_properties_current[property_id]
                        try:
                            for property_name, property_value in property_spec.items():

                                if property_name == 'operation':
                                    # operation is not an info object property
                                    # if set to anything other than 'remove' we don't fail
                                    continue

                                # Updating attributes only if needed
                                if getattr(new_vapp_property_spec.info, property_name) != property_value:
                                    setattr(new_vapp_property_spec.info, property_name, property_value)
                                    is_property_changed = True

                        except Exception as e:
                            msg = "Failed to set vApp property field='%s' and value='%s'. Error: %s" % (property_name, property_value, to_text(e))
                            self.module.fail_json(msg=msg)
                else:
                    if property_spec.get('operation') == 'remove':
                        # attempt to delete non-existent property
                        continue

                    # this is add new property branch
                    new_vapp_property_spec.operation = 'add'

                    # Configure the values in property_value
                    property_info = self.set_vapp_properties(property_spec)

                    new_vapp_property_spec.info = property_info
                    new_vapp_property_spec.info.key = new_property_index
                    new_property_index += 1
                    is_property_changed = True

                if is_property_changed:
                    new_vmconfig_spec.property.append(new_vapp_property_spec)
        else:
            # New VM
            all_keys = [x.key for x in new_vmconfig_spec.property]
            new_property_index = max(all_keys) + 1 if all_keys else 0
            vapp_properties_to_change = dict((x['id'], x) for x in self.params['vapp_properties'])
            is_property_changed = False

            for property_id, property_spec in vapp_properties_to_change.items():
                new_vapp_property_spec = vim.vApp.PropertySpec()
                # this is add new property branch
                new_vapp_property_spec.operation = 'add'

                # Configure the values in property_value
                property_info = self.set_vapp_properties(property_spec)

                new_vapp_property_spec.info = property_info
                new_vapp_property_spec.info.key = new_property_index
                new_property_index += 1
                is_property_changed = True

                if is_property_changed:
                    new_vmconfig_spec.property.append(new_vapp_property_spec)

        if new_vmconfig_spec.property:
            self.configspec.vAppConfig = new_vmconfig_spec
            self.change_detected = True

    def customize_advanced_settings(self, vm_obj, config_spec):
        if not self.params['advanced_settings']:
            return

        vm_custom_spec = config_spec
        vm_custom_spec.extraConfig = []

        changed = False
        facts = self.gather_facts(vm_obj)
        for kv in self.params['advanced_settings']:
            if 'key' not in kv or 'value' not in kv:
                self.module.exit_json(msg="advanced_settings items required both 'key' and 'value' fields.")

            # If kv is not kv fetched from facts, change it
            if isinstance(kv['value'], (bool, int)):
                specifiedvalue = str(kv['value']).upper()
                comparisonvalue = facts['advanced_settings'].get(kv['key'], '').upper()
            else:
                specifiedvalue = kv['value']
                comparisonvalue = facts['advanced_settings'].get(kv['key'], '')

            if (kv['key'] not in facts['advanced_settings'] and kv['value'] != '') or comparisonvalue != specifiedvalue:
                option = vim.option.OptionValue()
                option.key = kv['key']
                option.value = specifiedvalue

                vm_custom_spec.extraConfig.append(option)
                changed = True

            if changed:
                self.change_detected = True

    def customize_customvalues(self, vm_obj):
        if not self.params['customvalues']:
            return

        if not self.is_vcenter():
            self.module.warn("Currently connected to ESXi. "
                             "customvalues are a vCenter feature, this parameter will be ignored.")
            return

        facts = self.gather_facts(vm_obj)
        for kv in self.params['customvalues']:
            if 'key' not in kv or 'value' not in kv:
                self.module.exit_json(msg="customvalues items required both 'key' and 'value' fields.")

            key_id = None
            for field in self.content.customFieldsManager.field:
                if field.name == kv['key']:
                    key_id = field.key
                    break

            if not key_id:
                self.module.fail_json(msg="Unable to find custom value key %s" % kv['key'])

            # If kv is not kv fetched from facts, change it
            if kv['key'] not in facts['customvalues'] or facts['customvalues'][kv['key']] != kv['value']:
                self.content.customFieldsManager.SetField(entity=vm_obj, key=key_id, value=kv['value'])
                self.change_detected = True

    def customize_vm(self, vm_obj):

        # User specified customization specification
        custom_spec_name = self.params.get('customization_spec')
        if custom_spec_name:
            cc_mgr = self.content.customizationSpecManager
            if cc_mgr.DoesCustomizationSpecExist(name=custom_spec_name):
                temp_spec = cc_mgr.GetCustomizationSpec(name=custom_spec_name)
                self.customspec = temp_spec.spec
                return
            self.module.fail_json(msg="Unable to find customization specification"
                                      " '%s' in given configuration." % custom_spec_name)

        # Network settings
        adaptermaps = []
        for network in self.params['networks']:

            guest_map = vim.vm.customization.AdapterMapping()
            guest_map.adapter = vim.vm.customization.IPSettings()

            if 'ip' in network and 'netmask' in network:
                guest_map.adapter.ip = vim.vm.customization.FixedIp()
                guest_map.adapter.ip.ipAddress = str(network['ip'])
                guest_map.adapter.subnetMask = str(network['netmask'])
            elif 'type' in network and network['type'] == 'dhcp':
                guest_map.adapter.ip = vim.vm.customization.DhcpIpGenerator()

            if "ipv6" in network and 'netmaskv6' in network:
                guest_map.adapter.ipV6Spec = vim.vm.customization.IPSettings.IpV6AddressSpec()
                guest_map.adapter.ipV6Spec.ip = [vim.vm.customization.FixedIpV6()]
                guest_map.adapter.ipV6Spec.ip[0].ipAddress = str(network['ipv6'])
                guest_map.adapter.ipV6Spec.ip[0].subnetMask = int(network['netmaskv6'])
            elif 'typev6' in network and network['typev6'] == 'dhcp':
                guest_map.adapter.ipV6Spec = vim.vm.customization.IPSettings.IpV6AddressSpec()
                guest_map.adapter.ipV6Spec.ip = [vim.vm.customization.DhcpIpV6Generator()]

            if 'gateway' in network:
                guest_map.adapter.gateway = network['gateway']

            if "gatewayv6" in network:
                guest_map.adapter.ipV6Spec.gateway = network['gatewayv6']

            # On Windows, DNS domain and DNS servers can be set by network interface
            # https://pubs.vmware.com/vi3/sdk/ReferenceGuide/vim.vm.customization.IPSettings.html
            if 'domain' in network:
                guest_map.adapter.dnsDomain = network['domain']
            elif self.params['customization']['domain'] is not None:
                guest_map.adapter.dnsDomain = self.params['customization']['domain']

            if 'dns_servers' in network:
                guest_map.adapter.dnsServerList = network['dns_servers']
            elif self.params['customization']['dns_servers'] is not None:
                guest_map.adapter.dnsServerList = self.params['customization']['dns_servers']

            adaptermaps.append(guest_map)

        # Global DNS settings
        globalip = vim.vm.customization.GlobalIPSettings()
        if self.params['customization']['dns_servers'] is not None:
            globalip.dnsServerList = self.params['customization']['dns_servers']

        # TODO: Maybe list the different domains from the interfaces here by default ?
        dns_suffixes = []
        dns_suffix = self.params['customization']['dns_suffix']
        if dns_suffix:
            if isinstance(dns_suffix, list):
                dns_suffixes += dns_suffix
            else:
                dns_suffixes.append(dns_suffix)

            globalip.dnsSuffixList = dns_suffixes

        if self.params['customization']['domain'] is not None:
            dns_suffixes.insert(0, self.params['customization']['domain'])
            globalip.dnsSuffixList = dns_suffixes

        if self.params['guest_id'] is not None:
            guest_id = self.params['guest_id']
        else:
            guest_id = vm_obj.summary.config.guestId

        # For windows guest OS, use SysPrep
        # https://pubs.vmware.com/vi3/sdk/ReferenceGuide/vim.vm.customization.Sysprep.html#field_detail
        if 'win' in guest_id:
            ident = vim.vm.customization.Sysprep()

            ident.userData = vim.vm.customization.UserData()

            # Setting hostName, orgName and fullName is mandatory, so we set some default when missing
            ident.userData.computerName = vim.vm.customization.FixedName()
            # computer name will be truncated to 15 characters if using VM name
            default_name = ""
            if 'name' in self.params and self.params['name']:
                default_name = self.params['name'].replace(' ', '')
            elif vm_obj:
                default_name = vm_obj.name.replace(' ', '')
            punctuation = string.punctuation.replace('-', '')
            default_name = ''.join([c for c in default_name if c not in punctuation])

            if self.params['customization']['hostname'] is not None:
                ident.userData.computerName.name = self.params['customization']['hostname'][0:15]
            else:
                ident.userData.computerName.name = default_name[0:15]

            ident.userData.fullName = str(self.params['customization'].get('fullname', 'Administrator'))
            ident.userData.orgName = str(self.params['customization'].get('orgname', 'ACME'))

            if self.params['customization']['productid'] is not None:
                ident.userData.productId = str(self.params['customization']['productid'])

            ident.guiUnattended = vim.vm.customization.GuiUnattended()

            if self.params['customization']['autologon'] is not None:
                ident.guiUnattended.autoLogon = self.params['customization']['autologon']
                ident.guiUnattended.autoLogonCount = self.params['customization'].get('autologoncount', 1)

            if self.params['customization']['timezone'] is not None:
                # Check if timezone value is a int before proceeding.
                ident.guiUnattended.timeZone = self.device_helper.integer_value(
                    self.params['customization']['timezone'],
                    'customization.timezone')

            ident.identification = vim.vm.customization.Identification()

            if self.params['customization']['password'] is None or self.params['customization']['password'] == '':
                ident.guiUnattended.password = None
            else:
                ident.guiUnattended.password = vim.vm.customization.Password()
                ident.guiUnattended.password.value = str(self.params['customization']['password'])
                ident.guiUnattended.password.plainText = True

            if self.params['customization']['joindomain'] is not None:
                if self.params['customization']['domainadmin'] is None or self.params['customization']['domainadminpassword'] is None:
                    self.module.fail_json(msg="'domainadmin' and 'domainadminpassword' entries are mandatory in 'customization' section to use "
                                              "joindomain feature")

                ident.identification.domainAdmin = self.params['customization']['domainadmin']
                ident.identification.joinDomain = self.params['customization']['joindomain']
                ident.identification.domainAdminPassword = vim.vm.customization.Password()
                ident.identification.domainAdminPassword.value = self.params['customization']['domainadminpassword']
                ident.identification.domainAdminPassword.plainText = True

                # Add new spec param for vSphere 8.0U2
                ident.identification.domainOU = self.params['customization']['domain_ou']

            elif self.params['customization']['joinworkgroup'] is not None:
                ident.identification.joinWorkgroup = self.params['customization']['joinworkgroup']

            if self.params['customization']['runonce'] is not None:
                ident.guiRunOnce = vim.vm.customization.GuiRunOnce()
                ident.guiRunOnce.commandList = self.params['customization']['runonce']

        else:
            # FIXME: We have no clue whether this non-Windows OS is actually Linux, hence it might fail!

            # For Linux guest OS, use LinuxPrep
            # https://pubs.vmware.com/vi3/sdk/ReferenceGuide/vim.vm.customization.LinuxPrep.html
            ident = vim.vm.customization.LinuxPrep()

            # TODO: Maybe add domain from interface if missing ?
            if self.params['customization']['domain'] is not None:
                ident.domain = self.params['customization']['domain']

            ident.hostName = vim.vm.customization.FixedName()
            default_name = ""
            if 'name' in self.params and self.params['name']:
                default_name = self.params['name']
            elif vm_obj:
                default_name = vm_obj.name

            if self.params['customization']['hostname'] is not None:
                hostname = self.params['customization']['hostname'].split('.')[0]
            else:
                hostname = default_name.split('.')[0]

            # Remove all characters except alphanumeric and minus which is allowed by RFC 952
            valid_hostname = re.sub(r"[^a-zA-Z0-9\-]", "", hostname)
            ident.hostName.name = valid_hostname

            # List of supported time zones for different vSphere versions in Linux/Unix systems
            # https://kb.vmware.com/s/article/2145518
            if self.params['customization']['timezone'] is not None:
                ident.timeZone = self.params['customization']['timezone']
            if self.params['customization']['hwclockUTC'] is not None:
                ident.hwClockUTC = self.params['customization']['hwclockUTC']
            if self.params['customization']['script_text'] is not None:
                ident.scriptText = self.params['customization']['script_text']

        self.customspec = vim.vm.customization.Specification()
        self.customspec.nicSettingMap = adaptermaps
        self.customspec.globalIPSettings = globalip
        self.customspec.identity = ident

    def get_vm_scsi_controllers(self, vm_obj):
        # If vm_obj doesn't exist there is no SCSI controller to find
        scsi_ctls = []
        if vm_obj is None:
            return None

        for device in vm_obj.config.hardware.device:
            if self.device_helper.is_scsi_controller(device):
                scsi_ctl = vim.vm.device.VirtualDeviceSpec()
                scsi_ctl.device = device
                scsi_ctls.append(scsi_ctl)

        return scsi_ctls

    def get_configured_disk_size(self, expected_disk_spec):
        # what size is it?
        if [x for x in expected_disk_spec.keys() if (x.startswith('size_') or x == 'size') and expected_disk_spec[x]]:
            # size, size_tb, size_gb, size_mb, size_kb
            if expected_disk_spec['size']:
                size_regex = re.compile(r'(\d+(?:\.\d+)?)([tgmkTGMK][bB])')
                disk_size_m = size_regex.match(expected_disk_spec['size'])
                try:
                    if disk_size_m:
                        expected = disk_size_m.group(1)
                        unit = disk_size_m.group(2)
                    else:
                        raise ValueError

                    if re.match(r'\d+\.\d+', expected):
                        # We found float value in string, let's typecast it
                        expected = float(expected)
                    else:
                        # We found int value in string, let's typecast it
                        expected = int(expected)

                    if not expected or not unit:
                        raise ValueError

                except (TypeError, ValueError, NameError):
                    # Common failure
                    self.module.fail_json(msg="Failed to parse disk size please review value"
                                              " provided using documentation.")
            else:
                param = [x for x in expected_disk_spec.keys() if x.startswith('size_') and expected_disk_spec[x]][0]
                unit = param.split('_')[-1]
                expected = expected_disk_spec[param]

            disk_units = dict(tb=3, gb=2, mb=1, kb=0)
            if unit in disk_units:
                unit = unit.lower()
                return expected * (1024 ** disk_units[unit])
            else:
                self.module.fail_json(msg="%s is not a supported unit for disk size."
                                          " Supported units are ['%s']." % (unit,
                                                                            "', '".join(disk_units.keys())))

        # No size found but disk, fail
        self.module.fail_json(
            msg="No size, size_kb, size_mb, size_gb or size_tb defined in disk configuration")

    def add_existing_vmdk(self, vm_obj, expected_disk_spec, diskspec, scsi_ctl):
        """
        Adds vmdk file described by expected_disk_spec['filename'], retrieves the file
        information and adds the correct spec to self.configspec.deviceChange.
        """
        filename = expected_disk_spec['filename']
        # If this is a new disk, or the disk file names are different
        if (vm_obj and diskspec.device.backing.fileName != filename) or vm_obj is None:
            diskspec.device.backing.fileName = filename
            diskspec.device.key = -1
            self.change_detected = True
            self.configspec.deviceChange.append(diskspec)

    def sanitize_disk_parameters(self, vm_obj):
        """

        Sanitize user provided disk parameters to configure multiple types of disk controllers and attached disks

        Returns: A sanitized dict of disk params, else fails
                 e.g., [{'type': 'nvme', 'num': 1, 'disk': []}, {}, {}, {}]}

        """
        controllers = []
        for disk_spec in self.params.get('disk'):
            if disk_spec['controller_type'] is None or disk_spec['controller_number'] is None or disk_spec['unit_number'] is None:
                self.module.fail_json(msg="'disk.controller_type', 'disk.controller_number' and 'disk.unit_number' are"
                                          " mandatory parameters when configure multiple disk controllers and disks.")

            ctl_num = disk_spec['controller_number']
            ctl_unit_num = disk_spec['unit_number']

            disk_spec['unit_number'] = ctl_unit_num
            ctl_type = disk_spec['controller_type']

            if len(controllers) != 0:
                ctl_exist = False
                for ctl in controllers:
                    if ctl['type'] in self.device_helper.scsi_device_type.keys() and ctl_type in self.device_helper.scsi_device_type.keys():
                        if ctl['type'] != ctl_type and ctl['num'] == ctl_num:
                            self.module.fail_json(msg="Specified SCSI controller '%s' and '%s' have the same bus number"
                                                      ": '%s'" % (ctl['type'], ctl_type, ctl_num))

                    if ctl['type'] == ctl_type and ctl['num'] == ctl_num:
                        for i in range(0, len(ctl['disk'])):
                            if disk_spec['unit_number'] == ctl['disk'][i]['unit_number']:
                                self.module.fail_json(msg="Specified the same 'controller_type, controller_number, "
                                                          "unit_number in disk configuration '%s:%s'" % (ctl_type, ctl_num))
                        ctl['disk'].append(disk_spec)
                        ctl_exist = True
                        break
                if not ctl_exist:
                    controllers.append({'type': ctl_type, 'num': ctl_num, 'disk': [disk_spec]})
            else:
                controllers.append({'type': ctl_type, 'num': ctl_num, 'disk': [disk_spec]})

        return controllers

    def set_disk_parameters(self, disk_spec, expected_disk_spec, reconfigure=False):
        disk_modified = False
        if expected_disk_spec['disk_mode']:
            disk_mode = expected_disk_spec.get('disk_mode')
            if reconfigure:
                if disk_spec.device.backing.diskMode != disk_mode:
                    disk_spec.device.backing.diskMode = disk_mode
                    disk_modified = True
            else:
                disk_spec.device.backing.diskMode = disk_mode
        # default is persistent for new deployed VM
        elif not reconfigure:
            disk_spec.device.backing.diskMode = "persistent"

        if not reconfigure:
            disk_type = expected_disk_spec.get('type', 'thin')
            if disk_type == 'thin':
                disk_spec.device.backing.thinProvisioned = True
            elif disk_type == 'eagerzeroedthick':
                disk_spec.device.backing.eagerlyScrub = True

        kb = self.get_configured_disk_size(expected_disk_spec)
        if reconfigure:
            if disk_spec.device.capacityInKB > kb:
                self.module.fail_json(msg="Given disk size is smaller than found (%d < %d)."
                                          "Reducing disks is not allowed." % (kb, disk_spec.device.capacityInKB))
            if disk_spec.device.capacityInKB != kb:
                disk_spec.device.capacityInKB = kb
                disk_modified = True
        else:
            disk_spec.device.capacityInKB = kb
            disk_modified = True

        return disk_modified

    def configure_multiple_controllers_disks(self, vm_obj):
        ctls = self.sanitize_disk_parameters(vm_obj)
        if len(ctls) == 0:
            return
        for ctl in ctls:
            # get existing specified disk controller and attached disks
            disk_ctl, disk_list = self.device_helper.get_controller_disks(vm_obj, ctl['type'], ctl['num'])
            if disk_ctl is None:
                # check if scsi controller key already used
                if ctl['type'] in self.device_helper.scsi_device_type.keys() and vm_obj is not None:
                    scsi_ctls = self.get_vm_scsi_controllers(vm_obj)
                    if scsi_ctls:
                        for scsi_ctl in scsi_ctls:
                            if scsi_ctl.device.busNumber == ctl['num']:
                                self.module.fail_json(msg="Specified SCSI controller number '%s' is already used"
                                                          " by: %s" % (ctl['num'], scsi_ctl))
                # create new disk controller if not exist
                disk_ctl_spec = self.device_helper.create_disk_controller(ctl['type'], ctl['num'])
                self.change_detected = True
                self.configspec.deviceChange.append(disk_ctl_spec)
            else:
                disk_ctl_spec = vim.vm.device.VirtualDeviceSpec()
                disk_ctl_spec.device = disk_ctl
            for j in range(0, len(ctl['disk'])):
                hard_disk = None
                hard_disk_spec = None
                hard_disk_exist = False
                disk_modified_for_spec = False
                disk_modified_for_disk = False
                disk_unit_number = ctl['disk'][j]['unit_number']
                # from attached disk list find the specified one
                if len(disk_list) != 0:
                    for disk in disk_list:
                        if disk.unitNumber == disk_unit_number:
                            hard_disk = disk
                            hard_disk_exist = True
                            break
                # if find the disk do reconfigure
                if hard_disk_exist:
                    hard_disk_spec = vim.vm.device.VirtualDeviceSpec()
                    hard_disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                    hard_disk_spec.device = hard_disk
                    disk_modified_for_spec = self.set_disk_parameters(hard_disk_spec, ctl['disk'][j], reconfigure=True)
                # if no disk or the specified one not exist do create new disk
                if len(disk_list) == 0 or not hard_disk_exist:
                    hard_disk = self.device_helper.create_hard_disk(disk_ctl_spec, disk_unit_number)
                    hard_disk.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.create
                    disk_modified_for_disk = self.set_disk_parameters(hard_disk, ctl['disk'][j])

                # Only update the configspec that will be applied in reconfigure_vm if something actually changed
                if disk_modified_for_spec:
                    self.change_detected = True
                    self.configspec.deviceChange.append(hard_disk_spec)
                if disk_modified_for_disk:
                    self.change_detected = True
                    self.configspec.deviceChange.append(hard_disk)

    def configure_disks(self, vm_obj):
        # Ignore empty disk list, this permits to keep disks when deploying a template/cloning a VM
        if not self.params['disk']:
            return

        # if one of 'controller_type', 'controller_number', 'unit_number' parameters set in one of disks' configuration
        # will call configure_multiple_controllers_disks() function
        # do not support mixed old scsi disks configuration and new multiple controller types of disks configuration
        configure_multiple_ctl = False
        for disk_spec in self.params.get('disk'):
            if disk_spec['controller_type'] or disk_spec['controller_number'] or disk_spec['unit_number']:
                configure_multiple_ctl = True
                break
        if configure_multiple_ctl:
            self.configure_multiple_controllers_disks(vm_obj)
            return

        # do single controller type disks configuration
        scsi_ctls = self.get_vm_scsi_controllers(vm_obj)

        # Create scsi controller only if we are deploying a new VM, not a template or reconfiguring
        if vm_obj is None or not scsi_ctls:
            scsi_ctl = self.device_helper.create_scsi_controller(self.get_scsi_type(), 0)
            self.change_detected = True
            self.configspec.deviceChange.append(scsi_ctl)
        else:
            scsi_ctl = scsi_ctls[0]

        disks = [x for x in vm_obj.config.hardware.device if isinstance(x, vim.vm.device.VirtualDisk)] \
            if vm_obj is not None else None

        if disks is not None and self.params.get('disk') and len(self.params.get('disk')) < len(disks):
            self.module.fail_json(msg="Provided disks configuration has less disks than "
                                      "the target object (%d vs %d)" % (len(self.params.get('disk')), len(disks)))

        disk_index = 0
        disk_index_scsi = 0
        for expected_disk_spec in self.params.get('disk'):
            disk_modified = False
            # If we are manipulating and existing objects which has disks and disk_index is in disks
            if vm_obj is not None and disks is not None and disk_index < len(disks):
                diskspec = vim.vm.device.VirtualDeviceSpec()
                # set the operation to edit so that it knows to keep other settings
                diskspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                diskspec.device = disks[disk_index]
            else:
                diskspec = self.device_helper.create_hard_disk(scsi_ctl, disk_index_scsi)
                diskspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
                disk_modified = True

            # increment index for next disk search
            disk_index += 1
            disk_index_scsi += 1
            # index 7 is reserved to SCSI controller
            if disk_index_scsi == 7:
                disk_index_scsi += 1

            if expected_disk_spec['disk_mode']:
                disk_mode = expected_disk_spec.get('disk_mode', 'persistent')

                if (vm_obj and diskspec.device.backing.diskMode != disk_mode) or (vm_obj is None):
                    diskspec.device.backing.diskMode = disk_mode
                    disk_modified = True
            else:
                diskspec.device.backing.diskMode = "persistent"

            # is it thin?
            if expected_disk_spec['type']:
                disk_type = expected_disk_spec.get('type', '').lower()
                if disk_type == 'thin':
                    diskspec.device.backing.thinProvisioned = True
                elif disk_type == 'eagerzeroedthick':
                    diskspec.device.backing.eagerlyScrub = True

            if expected_disk_spec['filename']:
                self.add_existing_vmdk(vm_obj, expected_disk_spec, diskspec, scsi_ctl)
                continue

            # Only create virtual device if not backed by vmdk in original template
            if diskspec.device.backing.fileName == '':
                diskspec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.create

            # which datastore?
            if expected_disk_spec.get('datastore'):
                # TODO: This is already handled by the relocation spec,
                # but it needs to eventually be handled for all the
                # other disks defined
                pass

            kb = self.get_configured_disk_size(expected_disk_spec)
            # VMware doesn't allow to reduce disk sizes
            if kb < diskspec.device.capacityInKB:
                self.module.fail_json(
                    msg="Given disk size is smaller than found (%d < %d). Reducing disks is not allowed." %
                        (kb, diskspec.device.capacityInKB))

            if kb != diskspec.device.capacityInKB or disk_modified:
                diskspec.device.capacityInKB = kb
                self.configspec.deviceChange.append(diskspec)

                self.change_detected = True

    def select_host(self):
        hostsystem = self.cache.get_esx_host(self.params['esxi_hostname'])
        if not hostsystem:
            self.module.fail_json(msg='Failed to find ESX host "%(esxi_hostname)s"' % self.params)
        if hostsystem.runtime.connectionState != 'connected' or hostsystem.runtime.inMaintenanceMode:
            self.module.fail_json(msg='ESXi "%(esxi_hostname)s" is in invalid state or in maintenance mode.' % self.params)
        return hostsystem

    def autoselect_datastore(self):
        datastore = None
        datastores = self.cache.get_all_objs(self.content, [vim.Datastore])

        if datastores is None or len(datastores) == 0:
            self.module.fail_json(msg="Unable to find a datastore list when autoselecting")

        datastore_freespace = 0
        for ds in datastores:
            if not self.is_datastore_valid(datastore_obj=ds):
                continue

            if ds.summary.freeSpace > datastore_freespace:
                datastore = ds
                datastore_freespace = ds.summary.freeSpace

        return datastore

    def select_datastore(self, vm_obj=None):
        datastore = None
        datastore_name = None

        if self.params['disk']:
            # TODO: really use the datastore for newly created disks
            if self.params['disk'][0]['autoselect_datastore']:
                datastores = []

                if self.params['cluster']:
                    cluster = self.find_cluster_by_name(self.params['cluster'], self.content)

                    for host in cluster.host:
                        for mi in host.configManager.storageSystem.fileSystemVolumeInfo.mountInfo:
                            if mi.volume.type == "VMFS" or mi.volume.type == "NFS":
                                datastores.append(self.cache.find_obj_wrapper([vim.Datastore], mi.volume.name))
                elif self.params['esxi_hostname']:
                    host = self.find_hostsystem_by_name(self.params['esxi_hostname'])

                    for mi in host.configManager.storageSystem.fileSystemVolumeInfo.mountInfo:
                        if mi.volume.type == "VMFS" or mi.volume.type == "NFS":
                            datastores.append(self.cache.find_obj_wrapper([vim.Datastore], mi.volume.name))
                else:
                    datastores = self.cache.get_all_objs(self.content, [vim.Datastore])
                    datastores = [x for x in datastores if self.cache.get_parent_datacenter(x).name == self.params['datacenter']]

                datastore_freespace = 0
                for ds in datastores:
                    if not self.is_datastore_valid(datastore_obj=ds):
                        continue

                    if (ds.summary.freeSpace > datastore_freespace) or (ds.summary.freeSpace == datastore_freespace and not datastore):
                        # If datastore field is provided, filter destination datastores
                        if self.params['disk'][0]['datastore'] and ds.name.find(self.params['disk'][0]['datastore']) < 0:
                            continue

                        datastore = ds
                        datastore_name = datastore.name
                        datastore_freespace = ds.summary.freeSpace

            elif self.params['disk'][0]['datastore']:
                datastore_name = self.params['disk'][0]['datastore']
                # Check if user has provided datastore cluster first
                datastore_cluster = self.cache.find_obj_wrapper([vim.StoragePod], datastore_name)
                if datastore_cluster:
                    # If user specified datastore cluster so get recommended datastore
                    datastore_name = self.get_recommended_datastore(datastore_cluster_obj=datastore_cluster)
                # Check if get_recommended_datastore or user specified datastore exists or not
                datastore = self.cache.find_obj_wrapper([vim.Datastore], datastore_name)
            else:
                self.module.fail_json(msg="Either datastore or autoselect_datastore should be provided to select datastore")

        if not datastore and self.params['template']:
            # use the template's existing DS
            disks = [x for x in vm_obj.config.hardware.device if isinstance(x, vim.vm.device.VirtualDisk)]
            if disks:
                datastore = disks[0].backing.datastore
                datastore_name = datastore.name
            # validation
            if datastore:
                dc = self.cache.get_parent_datacenter(datastore)
                if dc.name != self.params['datacenter']:
                    datastore = self.autoselect_datastore()
                    datastore_name = datastore.name

        if not datastore:
            if len(self.params['disk']) != 0 or self.params['template'] is None:
                self.module.fail_json(msg="Unable to find the datastore with given parameters."
                                          " This could mean, %s is a non-existent virtual machine and module tried to"
                                          " deploy it as new virtual machine with no disk. Please specify disks parameter"
                                          " or specify template to clone from." % self.params['name'])
            self.module.fail_json(msg="Failed to find a matching datastore")

        return datastore, datastore_name

    def obj_has_parent(self, obj, parent):
        if obj is None and parent is None:
            raise AssertionError()
        current_parent = obj

        while True:
            if current_parent.name == parent.name:
                return True

            # Check if we have reached till root folder
            moid = current_parent._moId
            if moid in ['group-d1', 'ha-folder-root']:
                return False

            current_parent = current_parent.parent
            if current_parent is None:
                return False

    def get_scsi_type(self):
        disk_controller_type = self.params['hardware']['scsi']
        if disk_controller_type is not None:
            return disk_controller_type
        return "paravirtual"

    def find_folder(self, searchpath):
        """ Walk inventory objects one position of the searchpath at a time """

        # split the searchpath so we can iterate through it
        paths = [x.replace('/', '') for x in searchpath.split('/')]
        paths_total = len(paths) - 1
        position = 0

        # recursive walk while looking for next element in searchpath
        root = self.content.rootFolder
        while root and position <= paths_total:
            change = False
            if hasattr(root, 'childEntity'):
                for child in root.childEntity:
                    if child.name == paths[position]:
                        root = child
                        position += 1
                        change = True
                        break
            elif isinstance(root, vim.Datacenter):
                if hasattr(root, 'vmFolder'):
                    if root.vmFolder.name == paths[position]:
                        root = root.vmFolder
                        position += 1
                        change = True
            else:
                root = None

            if not change:
                root = None

        return root

    def get_resource_pool(self, cluster=None, host=None, resource_pool=None):
        """ Get a resource pool, filter on cluster, esxi_hostname or resource_pool if given """

        cluster_name = cluster or self.params.get('cluster', None)
        host_name = host or self.params.get('esxi_hostname', None)
        resource_pool_name = resource_pool or self.params.get('resource_pool', None)

        # get the datacenter object
        datacenter = self.find_obj([vim.Datacenter], self.params['datacenter'])
        if not datacenter:
            self.module.fail_json(msg='Unable to find datacenter "%s"' % self.params['datacenter'])

        # if cluster is given, get the cluster object
        if cluster_name:
            cluster = self.find_obj([vim.ComputeResource], cluster_name, folder=datacenter)
            if not cluster:
                self.module.fail_json(msg='Unable to find cluster "%s"' % cluster_name)
        # if host is given, get the cluster object using the host
        elif host_name:
            host = self.find_obj([vim.HostSystem], host_name, folder=datacenter)
            if not host:
                self.module.fail_json(msg='Unable to find host "%s"' % host_name)
            cluster = host.parent
        else:
            cluster = None

        # get resource pools limiting search to cluster or datacenter
        resource_pool = self.find_obj([vim.ResourcePool], resource_pool_name, folder=cluster or datacenter)
        if not resource_pool:
            if resource_pool_name:
                self.module.fail_json(msg='Unable to find resource_pool "%s"' % resource_pool_name)
            else:
                self.module.fail_json(msg='Unable to find resource pool, need esxi_hostname, resource_pool, or cluster')
        return resource_pool

    def deploy_vm(self):
        # https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/clone_vm.py
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.vm.CloneSpec.html
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.vm.ConfigSpec.html
        # https://www.vmware.com/support/developer/vc-sdk/visdk41pubs/ApiReference/vim.vm.RelocateSpec.html

        # FIXME:
        #   - static IPs

        self.folder = self.params.get('folder', None)
        if self.folder is None:
            self.module.fail_json(msg="Folder is required parameter while deploying new virtual machine")

        # Prepend / if it was missing from the folder path, also strip trailing slashes
        if not self.folder.startswith('/'):
            self.folder = '/%(folder)s' % self.params
        self.folder = self.folder.rstrip('/')

        datacenter = self.cache.find_obj_wrapper([vim.Datacenter], self.params['datacenter'])
        if datacenter is None:
            self.module.fail_json(msg='No datacenter named %(datacenter)s was found' % self.params)

        dcpath = compile_folder_path_for_object(datacenter)

        # Nested folder does not have trailing /
        if not dcpath.endswith('/'):
            dcpath += '/'

        # Check for full path first in case it was already supplied
        if self.folder.startswith(
            dcpath + self.params["datacenter"] + "/vm"
        ) or self.folder.startswith(dcpath + "/" + self.params["datacenter"] + "/vm"):
            fullpath = self.folder
        elif self.folder.startswith("/vm/") or self.folder == "/vm":
            fullpath = "%s%s%s" % (dcpath, self.params["datacenter"], self.folder)
        elif self.folder.startswith("/"):
            fullpath = "%s%s/vm%s" % (dcpath, self.params["datacenter"], self.folder)
        else:
            fullpath = "%s%s/vm/%s" % (dcpath, self.params["datacenter"], self.folder)

        f_obj = self.content.searchIndex.FindByInventoryPath(fullpath)

        # abort if no strategy was successful
        if f_obj is None:
            # Add some debugging values in failure.
            details = {
                'datacenter': datacenter.name,
                'datacenter_path': dcpath,
                'folder': self.folder,
                'full_search_path': fullpath,
            }
            self.module.fail_json(msg='No folder %s matched in the search path : %s' % (self.folder, fullpath),
                                  details=details)

        destfolder = f_obj

        if self.params['template']:
            vm_obj = self.get_vm_or_template(template_name=self.params['template'])
            if vm_obj is None:
                self.module.fail_json(msg="Could not find a template named %(template)s" % self.params)
            if self.params['guest_id'] is not None and vm_obj.summary.config.guestId is not None and self.params['guest_id'] != vm_obj.summary.config.guestId:
                details = {
                    'vm_guest_id': self.params['guest_id'],
                    'template_guest_id': vm_obj.summary.config.guestId,
                }
                self.module.fail_json(msg="Could not create vm from template with different guest_ids",
                                      details=details)

        else:
            vm_obj = None

        # always get a resource_pool
        resource_pool = self.get_resource_pool()

        # set the destination datastore for VM & disks
        if self.params['datastore']:
            # Give precedence to datastore value provided by user
            # User may want to deploy VM to specific datastore.
            datastore_name = self.params['datastore']
            # Check if user has provided datastore cluster first
            datastore_cluster = self.cache.find_obj_wrapper([vim.StoragePod], datastore_name)
            if datastore_cluster:
                # If user specified datastore cluster so get recommended datastore
                datastore_name = self.get_recommended_datastore(datastore_cluster_obj=datastore_cluster)
            # Check if get_recommended_datastore or user specified datastore exists or not
            datastore = self.cache.find_obj_wrapper([vim.Datastore], datastore_name)
        else:
            (datastore, datastore_name) = self.select_datastore(vm_obj)

        self.configspec = vim.vm.ConfigSpec()
        self.configspec.deviceChange = []
        # create the relocation spec
        self.relospec = vim.vm.RelocateSpec()
        self.relospec.deviceChange = []
        self.configure_guestid(vm_obj=vm_obj, vm_creation=True)
        self.configure_cpu_and_memory(vm_obj=vm_obj, vm_creation=True)
        self.configure_hardware_params(vm_obj=vm_obj)
        self.configure_encryption_params(vm_obj=vm_obj)
        self.configure_resource_alloc_info(vm_obj=vm_obj)
        self.configure_vapp_properties(vm_obj=vm_obj)
        self.configure_disks(vm_obj=vm_obj)
        self.configure_network(vm_obj=vm_obj)
        self.configure_cdrom(vm_obj=vm_obj)
        self.configure_nvdimm(vm_obj=vm_obj)

        # Find if we need network customizations (find keys in dictionary that requires customizations)
        network_changes = False
        for nw in self.params['networks']:
            for key in nw:
                # We don't need customizations for these keys
                if key == 'type' and nw['type'] == 'dhcp':
                    network_changes = True
                    break
                if key not in ('device_type', 'mac', 'name', 'vlan', 'type', 'start_connected', 'dvswitch_name'):
                    network_changes = True
                    break

        if any(v is not None for v in self.params['customization'].values()) or network_changes or self.params.get('customization_spec') is not None:
            self.customize_vm(vm_obj=vm_obj)

        clonespec = None
        clone_method = None
        try:
            if self.params['template']:
                # Only select specific host when ESXi hostname is provided
                if self.params['esxi_hostname']:
                    self.relospec.host = self.select_host()
                self.relospec.datastore = datastore

                # Convert disk present in template if is set
                if self.params['convert']:
                    for device in vm_obj.config.hardware.device:
                        if isinstance(device, vim.vm.device.VirtualDisk):
                            disk_locator = vim.vm.RelocateSpec.DiskLocator()
                            disk_locator.diskBackingInfo = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
                            if self.params['convert'] == 'thin':
                                disk_locator.diskBackingInfo.thinProvisioned = True
                            if self.params['convert'] == 'eagerzeroedthick':
                                disk_locator.diskBackingInfo.eagerlyScrub = True
                            if self.params['convert'] == 'thick':
                                disk_locator.diskBackingInfo.diskMode = "persistent"
                            disk_locator.diskId = device.key
                            disk_locator.datastore = datastore
                            self.relospec.disk.append(disk_locator)

                # https://www.vmware.com/support/developer/vc-sdk/visdk41pubs/ApiReference/vim.vm.RelocateSpec.html
                # > pool: For a clone operation from a template to a virtual machine, this argument is required.
                self.relospec.pool = resource_pool
                linked_clone = self.params.get('linked_clone')
                snapshot_src = self.params.get('snapshot_src', None)
                if linked_clone:
                    if snapshot_src is not None:
                        self.relospec.diskMoveType = vim.vm.RelocateSpec.DiskMoveOptions.createNewChildDiskBacking
                    else:
                        self.module.fail_json(msg="Parameter 'linked_src' and 'snapshot_src' are"
                                                  " required together for linked clone operation.")

                clonespec = vim.vm.CloneSpec(template=self.params['is_template'], location=self.relospec)
                if self.customspec:
                    clonespec.customization = self.customspec

                if snapshot_src is not None:
                    if vm_obj.snapshot is None:
                        self.module.fail_json(msg="No snapshots present for virtual machine or template [%(template)s]" % self.params)
                    snapshot = self.get_snapshots_by_name_recursively(snapshots=vm_obj.snapshot.rootSnapshotList,
                                                                      snapname=snapshot_src)
                    if len(snapshot) != 1:
                        self.module.fail_json(msg='virtual machine "%(template)s" does not contain'
                                                  ' snapshot named "%(snapshot_src)s"' % self.params)

                    clonespec.snapshot = snapshot[0].snapshot

                clonespec.config = self.configspec
                clone_method = 'Clone'
                try:
                    task = vm_obj.Clone(folder=destfolder, name=self.params['name'], spec=clonespec)
                except vim.fault.NoPermission as e:
                    self.module.fail_json(msg="Failed to clone virtual machine %s to folder %s "
                                              "due to permission issue: %s" % (self.params['name'],
                                                                               destfolder,
                                                                               to_native(e.msg)))
                self.change_detected = True
            else:
                # ConfigSpec require name for VM creation
                self.configspec.name = self.params['name']
                self.configspec.files = vim.vm.FileInfo(logDirectory=None,
                                                        snapshotDirectory=None,
                                                        suspendDirectory=None,
                                                        vmPathName="[" + datastore_name + "]")
                esx_host = None
                # Only select specific host when ESXi hostname is provided
                if self.params['esxi_hostname']:
                    esx_host = self.select_host()

                clone_method = 'CreateVM_Task'
                try:
                    task = destfolder.CreateVM_Task(config=self.configspec, pool=resource_pool, host=esx_host)
                except vmodl.fault.InvalidRequest as e:
                    self.module.fail_json(msg="Failed to create virtual machine due to invalid configuration "
                                              "parameter %s" % to_native(e.msg))
                except vim.fault.RestrictedVersion as e:
                    self.module.fail_json(msg="Failed to create virtual machine due to "
                                              "product versioning restrictions: %s" % to_native(e.msg))
                self.change_detected = True
            error_msg = self.wait_for_task(task)
        except TypeError as e:
            self.module.fail_json(msg="TypeError was returned, please ensure to give correct inputs. %s" % to_text(e))

        if task.info.state == 'error':
            # https://kb.vmware.com/selfservice/microsites/search.do?language=en_US&cmd=displayKC&externalId=2021361
            # https://kb.vmware.com/selfservice/microsites/search.do?language=en_US&cmd=displayKC&externalId=2173

            # provide these to the user for debugging
            clonespec_json = serialize_spec(clonespec)
            configspec_json = serialize_spec(self.configspec)
            kwargs = {
                'changed': self.change_applied,
                'failed': True,
                'msg': error_msg,
                'clonespec': clonespec_json,
                'configspec': configspec_json,
                'clone_method': clone_method
            }

            return kwargs
        else:
            # set annotation
            vm = task.info.result
            if self.params['annotation']:
                annotation_spec = vim.vm.ConfigSpec()
                annotation_spec.annotation = str(self.params['annotation'])
                task = vm.ReconfigVM_Task(annotation_spec)
                error_msg = self.wait_for_task(task)
                if task.info.state == 'error':
                    return {'changed': self.change_applied, 'failed': True, 'msg': error_msg, 'op': 'annotation'}

            if self.params['advanced_settings']:
                vm_custom_spec = vim.vm.ConfigSpec()
                self.customize_advanced_settings(vm_obj=vm, config_spec=vm_custom_spec)
                task = vm.ReconfigVM_Task(vm_custom_spec)
                error_msg = self.wait_for_task(task)
                if task.info.state == 'error':
                    return {'changed': self.change_applied, 'failed': True, 'msg': error_msg, 'op': 'advanced_settings'}

            if self.params['customvalues']:
                self.customize_customvalues(vm_obj=vm)

            if self.params['wait_for_ip_address'] or self.params['wait_for_customization'] or self.params['state'] in ['poweredon', 'powered-on', 'restarted']:
                set_vm_power_state(self.content, vm, 'poweredon', force=False)

                if self.params['wait_for_ip_address']:
                    wait_for_vm_ip(self.content, vm, self.params['wait_for_ip_address_timeout'])

                if self.params['wait_for_customization']:
                    is_customization_ok = self.wait_for_customization(vm=vm, timeout=self.params['wait_for_customization_timeout'])
                    if not is_customization_ok:
                        vm_facts = self.gather_facts(vm)
                        return {'changed': self.change_applied, 'failed': True,
                                'msg': 'Customization failed. For detailed information see warnings',
                                'instance': vm_facts, 'op': 'customization'}

            vm_facts = self.gather_facts(vm)
            return {'changed': self.change_applied, 'failed': False, 'instance': vm_facts}

    def get_snapshots_by_name_recursively(self, snapshots, snapname):
        snap_obj = []
        for snapshot in snapshots:
            if snapshot.name == snapname:
                snap_obj.append(snapshot)
            else:
                snap_obj = snap_obj + self.get_snapshots_by_name_recursively(snapshot.childSnapshotList, snapname)
        return snap_obj

    def reconfigure_vm(self):
        self.configspec = vim.vm.ConfigSpec()
        self.configspec.deviceChange = []
        # create the relocation spec
        self.relospec = vim.vm.RelocateSpec()
        self.relospec.deviceChange = []
        self.configure_guestid(vm_obj=self.current_vm_obj)
        self.configure_cpu_and_memory(vm_obj=self.current_vm_obj)
        err = self.configure_hardware_params(vm_obj=self.current_vm_obj)
        if err is not None:
            return err
        self.configure_encryption_params(vm_obj=self.current_vm_obj)
        self.configure_disks(vm_obj=self.current_vm_obj)
        self.configure_network(vm_obj=self.current_vm_obj)
        self.configure_cdrom(vm_obj=self.current_vm_obj)
        self.configure_nvdimm(vm_obj=self.current_vm_obj)
        self.customize_advanced_settings(vm_obj=self.current_vm_obj, config_spec=self.configspec)
        self.customize_customvalues(vm_obj=self.current_vm_obj)
        self.configure_resource_alloc_info(vm_obj=self.current_vm_obj)
        self.configure_vapp_properties(vm_obj=self.current_vm_obj)

        if self.params['annotation'] and self.current_vm_obj.config.annotation != self.params['annotation']:
            self.configspec.annotation = str(self.params['annotation'])
            self.change_detected = True

        if self.params['resource_pool']:
            self.relospec.pool = self.get_resource_pool()

            if self.relospec.pool != self.current_vm_obj.resourcePool:
                self.tracked_changes['resourcePool'] = str(self.relospec.pool)
                if self.module.check_mode:
                    self.change_applied = True
                else:
                    task = self.current_vm_obj.RelocateVM_Task(spec=self.relospec)
                    error_msg = self.wait_for_task(task)
                    if task.info.state == 'error':
                        return {'changed': self.change_applied, 'failed': True, 'msg': error_msg, 'op': 'relocate'}

        # Only send VMware task if we see a modification
        if self.change_detected:
            self.tracked_changes['configspec'] = str(self.configspec)
            if self.module.check_mode:
                self.change_applied = True
            else:
                task = None
                try:
                    task = self.current_vm_obj.ReconfigVM_Task(spec=self.configspec)
                except vim.fault.RestrictedVersion as e:
                    self.module.fail_json(msg="Failed to reconfigure virtual machine due to"
                                              " product versioning restrictions: %s" % to_native(e.msg))
                error_msg = self.wait_for_task(task)
                if task.info.state == 'error':
                    return {'changed': self.change_applied, 'failed': True, 'msg': error_msg, 'op': 'reconfig'}

        # Rename VM
        if self.params['uuid'] and self.params['name'] and self.params['name'] != self.current_vm_obj.config.name:
            self.tracked_changes['name'] = self.params['name']
            if self.module.check_mode:
                self.change_applied = True
            else:
                task = self.current_vm_obj.Rename_Task(self.params['name'])
                error_msg = self.wait_for_task(task)
                if task.info.state == 'error':
                    return {'changed': self.change_applied, 'failed': True, 'msg': error_msg, 'op': 'rename'}

        # Mark VM as Template
        if self.params['is_template'] and not self.current_vm_obj.config.template:
            try:
                if not self.module.check_mode:
                    self.current_vm_obj.MarkAsTemplate()
                self.change_applied = True
                self.tracked_changes['MarkAsTemplate'] = True
            except vmodl.fault.NotSupported as e:
                self.module.fail_json(msg="Failed to mark virtual machine [%s] "
                                          "as template: %s" % (self.params['name'], e.msg))

        # Mark Template as VM
        elif not self.params['is_template'] and self.current_vm_obj.config.template:
            resource_pool = self.get_resource_pool()
            kwargs = dict(pool=resource_pool)

            if self.params.get('esxi_hostname', None):
                host_system_obj = self.select_host()
                kwargs.update(host=host_system_obj)

            try:
                if not self.module.check_mode:
                    self.current_vm_obj.MarkAsVirtualMachine(**kwargs)
                self.change_applied = True
                self.tracked_changes['MarkAsVirtualMachine'] = True
            except vim.fault.InvalidState as invalid_state:
                self.module.fail_json(msg="Virtual machine is not marked"
                                          " as template : %s" % to_native(invalid_state.msg))
            except vim.fault.InvalidDatastore as invalid_ds:
                self.module.fail_json(msg="Converting template to virtual machine"
                                          " operation cannot be performed on the"
                                          " target datastores: %s" % to_native(invalid_ds.msg))
            except vim.fault.CannotAccessVmComponent as cannot_access:
                self.module.fail_json(msg="Failed to convert template to virtual machine"
                                          " as operation unable access virtual machine"
                                          " component: %s" % to_native(cannot_access.msg))
            except vmodl.fault.InvalidArgument as invalid_argument:
                self.module.fail_json(msg="Failed to convert template to virtual machine"
                                          " due to : %s" % to_native(invalid_argument.msg))
            except Exception as generic_exc:
                self.module.fail_json(msg="Failed to convert template to virtual machine"
                                          " due to generic error : %s" % to_native(generic_exc))

        # add customize existing VM after VM re-configure
        if self.params['customization']['existing_vm']:
            if self.current_vm_obj.config.template:
                self.module.fail_json(msg="VM is template, not support guest OS customization.")
            if self.current_vm_obj.runtime.powerState != vim.VirtualMachinePowerState.poweredOff and not self.module.check_mode:
                self.module.fail_json(msg="VM is not in poweroff state, can not do guest OS customization.")
            # TODO not sure if it is possible to query the current customspec to compare against the one being provided to check in check mode.
            # Maybe by breaking down the individual fields and querying, but it needs more research.
            # For now, assume changed...
            self.tracked_changes['customization'] = True
            if self.module.check_mode:
                self.change_applied = True
            else:
                cus_result = self.customize_exist_vm()
                if cus_result['failed']:
                    return cus_result

        vm_facts = self.gather_facts(self.current_vm_obj)
        return {'changed': self.change_applied, 'failed': False, 'instance': vm_facts, 'changes': self.tracked_changes}

    def customize_exist_vm(self):
        task = None
        # Find if we need network customizations (find keys in dictionary that requires customizations)
        network_changes = False
        for nw in self.params['networks']:
            for key in nw:
                # We don't need customizations for these keys
                if key not in ('device_type', 'mac', 'name', 'vlan', 'type', 'start_connected', 'dvswitch_name'):
                    network_changes = True
                    break
        if any(v is not None for v in self.params['customization'].values()) or network_changes or self.params.get('customization_spec'):
            self.customize_vm(vm_obj=self.current_vm_obj)
        try:
            task = self.current_vm_obj.CustomizeVM_Task(self.customspec)
        except vim.fault.CustomizationFault as e:
            self.module.fail_json(msg="Failed to customization virtual machine due to CustomizationFault: %s" % to_native(e.msg))
        except vim.fault.RuntimeFault as e:
            self.module.fail_json(msg="failed to customization virtual machine due to RuntimeFault: %s" % to_native(e.msg))
        except Exception as e:
            self.module.fail_json(msg="failed to customization virtual machine due to fault: %s" % to_native(e.msg))
        error_msg = self.wait_for_task(task)
        if task.info.state == 'error':
            return {'changed': self.change_applied, 'failed': True, 'msg': error_msg, 'op': 'customize_exist'}

        if self.params['wait_for_customization']:
            set_vm_power_state(self.content, self.current_vm_obj, 'poweredon', force=False)
            is_customization_ok = self.wait_for_customization(vm=self.current_vm_obj, timeout=self.params['wait_for_customization_timeout'])
            if not is_customization_ok:
                return {'changed': self.change_applied, 'failed': True,
                        'msg': 'Customization failed. For detailed information see warnings',
                        'op': 'wait_for_customize_exist'}

        return {'changed': self.change_applied, 'failed': False}

    def wait_for_task(self, task, poll_interval=1):
        """
        Wait for a VMware task to complete.  Terminal states are 'error' and 'success'.

        Inputs:
          - task: the task to wait for
          - poll_interval: polling interval to check the task, in seconds

        Modifies:
          - self.change_applied
        """
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.Task.html
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.TaskInfo.html
        # https://github.com/virtdevninja/pyvmomi-community-samples/blob/master/samples/tools/tasks.py
        error_msg = ''
        while task.info.state not in ['error', 'success']:
            time.sleep(poll_interval)

        if task.info.state == 'error':
            error_msg = task.info.error.msg
            if hasattr(task.info.error, 'faultMessage'):
                for fault in task.info.error.faultMessage:
                    if hasattr(fault, 'message') and fault.message:
                        error_msg += fault.message + ';'
                error_msg = error_msg.rstrip(';')
        self.change_applied = self.change_applied or task.info.state == 'success'
        return error_msg

    def get_vm_events(self, vm, eventTypeIdList):
        byEntity = vim.event.EventFilterSpec.ByEntity(entity=vm, recursion="self")
        filterSpec = vim.event.EventFilterSpec(entity=byEntity, eventTypeId=eventTypeIdList)
        eventManager = self.content.eventManager
        return eventManager.QueryEvent(filterSpec)

    def wait_for_customization(self, vm, timeout=3600, sleep=10):
        poll = int(timeout // sleep)
        thispoll = 0
        while thispoll <= poll:
            eventStarted = self.get_vm_events(vm, ['CustomizationStartedEvent'])
            if len(eventStarted):
                thispoll = 0
                while thispoll <= poll:
                    eventsFinishedResult = self.get_vm_events(vm, ['CustomizationSucceeded', 'CustomizationFailed'])
                    if len(eventsFinishedResult):
                        if not isinstance(eventsFinishedResult[0], vim.event.CustomizationSucceeded):
                            self.module.warn("Customization failed with error {%s}:{%s}"
                                             % (eventsFinishedResult[0]._wsdlName, eventsFinishedResult[0].fullFormattedMessage))
                            return False
                        else:
                            return True
                    else:
                        time.sleep(sleep)
                        thispoll += 1
                if len(eventsFinishedResult) == 0:
                    self.module.warn('Waiting for customization result event timed out.')
                    return False
            else:
                time.sleep(sleep)
                thispoll += 1
        if len(eventStarted):
            self.module.warn('Waiting for customization result event timed out.')
        else:
            self.module.warn('Waiting for customization start event timed out.')
        return False


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present',
                   choices=['absent', 'poweredoff', 'powered-off',
                            'poweredon', 'powered-on', 'present',
                            'rebootguest', 'reboot-guest', 'restarted',
                            'shutdownguest', 'shutdown-guest', 'suspended']),
        template=dict(type='str', aliases=['template_src']),
        is_template=dict(type='bool', default=False),
        annotation=dict(type='str', aliases=['notes']),
        customvalues=dict(type='list', default=[], elements='dict'),
        advanced_settings=dict(type='list', default=[], elements='dict'),
        name=dict(type='str'),
        name_match=dict(type='str', choices=['first', 'last'], default='first'),
        uuid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        folder=dict(type='str'),
        guest_id=dict(type='str'),
        disk=dict(
            type='list',
            default=[],
            elements='dict',
            options=dict(
                autoselect_datastore=dict(type='bool'),
                controller_number=dict(type='int', choices=[0, 1, 2, 3]),
                controller_type=dict(type='str', choices=['buslogic', 'lsilogic', 'paravirtual', 'lsilogicsas', 'sata', 'nvme']),
                datastore=dict(type='str'),
                disk_mode=dict(type='str', choices=['persistent', 'independent_persistent', 'independent_nonpersistent']),
                filename=dict(type='str'),
                size=dict(type='str'),
                size_gb=dict(type='int'),
                size_kb=dict(type='int'),
                size_mb=dict(type='int'),
                size_tb=dict(type='int'),
                type=dict(type='str', choices=['thin', 'eagerzeroedthick', 'thick']),
                unit_number=dict(type='int'),
            )
        ),
        nvdimm=dict(
            type='dict',
            default={},
            options=dict(
                state=dict(type='str', choices=['present', 'absent']),
                label=dict(type='str'),
                size_mb=dict(type='int', default=1024),
            )
        ),
        cdrom=dict(
            type='list',
            default=[],
            elements='dict',
            options=dict(
                type=dict(type='str', choices=['none', 'client', 'iso'], default='client'),
                iso_path=dict(type='str'),
                controller_type=dict(type='str', choices=['ide', 'sata'], default='ide'),
                controller_number=dict(type='int'),
                unit_number=dict(type='int'),
                state=dict(type='str', choices=['present', 'absent'], default='present'),
            )
        ),
        hardware=dict(
            type='dict',
            default={},
            options=dict(
                boot_firmware=dict(type='str', choices=['bios', 'efi']),
                cpu_limit=dict(type='int'),
                cpu_reservation=dict(type='int'),
                hotadd_cpu=dict(type='bool'),
                hotadd_memory=dict(type='bool'),
                hotremove_cpu=dict(type='bool'),
                vpmc_enabled=dict(type='bool'),
                max_connections=dict(type='int'),
                mem_limit=dict(type='int'),
                cpu_shares_level=dict(type='str', choices=['low', 'normal', 'high', 'custom']),
                mem_shares_level=dict(type='str', choices=['low', 'normal', 'high', 'custom']),
                cpu_shares=dict(type='int'),
                mem_shares=dict(type='int'),
                mem_reservation=dict(type='int', aliases=['memory_reservation']),
                memory_mb=dict(type='int'),
                memory_reservation_lock=dict(type='bool'),
                nested_virt=dict(type='bool'),
                num_cpu_cores_per_socket=dict(type='int'),
                num_cpus=dict(type='int'),
                scsi=dict(type='str', choices=['buslogic', 'lsilogic', 'lsilogicsas', 'paravirtual']),
                secure_boot=dict(type='bool'),
                version=dict(type='str'),
                virt_based_security=dict(type='bool'),
                iommu=dict(type='bool')
            )),
        encryption=dict(
            type='dict',
            default={},
            options=dict(
                encrypted_vmotion=dict(type='str', choices=['disabled', 'opportunistic', 'required']),
                encrypted_ft=dict(type='str', choices=['disabled', 'opportunistic', 'required'])
            )),
        force=dict(type='bool', default=False),
        datacenter=dict(type='str', default='ha-datacenter'),
        esxi_hostname=dict(type='str'),
        cluster=dict(type='str'),
        wait_for_ip_address=dict(type='bool', default=False),
        wait_for_ip_address_timeout=dict(type='int', default=300),
        state_change_timeout=dict(type='int', default=0),
        snapshot_src=dict(type='str'),
        linked_clone=dict(type='bool', default=False),
        networks=dict(type='list', default=[], elements='dict'),
        resource_pool=dict(type='str'),
        customization=dict(
            type='dict',
            default={},
            options=dict(
                autologon=dict(type='bool'),
                autologoncount=dict(type='int'),
                dns_servers=dict(type='list', elements='str'),
                dns_suffix=dict(type='list', elements='str'),
                domain=dict(type='str'),
                domainadmin=dict(type='str'),
                domainadminpassword=dict(type='str', no_log=True),
                domain_ou=dict(type='str'),
                existing_vm=dict(type='bool'),
                fullname=dict(type='str'),
                hostname=dict(type='str'),
                hwclockUTC=dict(type='bool'),
                joindomain=dict(type='str'),
                joinworkgroup=dict(type='str'),
                orgname=dict(type='str'),
                password=dict(type='str', no_log=True),
                productid=dict(type='str'),
                runonce=dict(type='list', elements='str'),
                script_text=dict(type='str'),
                timezone=dict(type='str')
            )),
        customization_spec=dict(type='str', default=None),
        wait_for_customization=dict(type='bool', default=False),
        wait_for_customization_timeout=dict(type='int', default=3600),
        vapp_properties=dict(type='list', default=[], elements='dict'),
        datastore=dict(type='str'),
        convert=dict(type='str', choices=['thin', 'thick', 'eagerzeroedthick']),
        delete_from_inventory=dict(type='bool', default=False),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           mutually_exclusive=[
                               ['cluster', 'esxi_hostname'],
                           ],
                           required_one_of=[
                               ['name', 'uuid'],
                           ],
                           )
    result = {'failed': False, 'changed': False}
    pyv = PyVmomiHelper(module)

    # Check requirements for virtualization based security
    if pyv.params['hardware']['virt_based_security']:
        if not pyv.params['hardware']['nested_virt']:
            pyv.module.fail_json(msg="Virtualization based security requires nested virtualization. Please enable nested_virt.")

        if not pyv.params['hardware']['secure_boot']:
            pyv.module.fail_json(msg="Virtualization based security requires (U)EFI secure boot. Please enable secure_boot.")

        if not pyv.params['hardware']['iommu']:
            pyv.module.fail_json(msg="Virtualization based security requires I/O MMU. Please enable iommu.")

    # Check if the VM exists before continuing
    vm = pyv.get_vm()

    # VM already exists
    if vm:
        if module.params['state'] == 'absent':
            # destroy it
            if module.check_mode:
                result.update(
                    vm_name=vm.name,
                    changed=True,
                    current_powerstate=vm.summary.runtime.powerState.lower(),
                    desired_operation='remove_vm',
                )
                module.exit_json(**result)
            if module.params['force']:
                # has to be poweredoff first
                set_vm_power_state(pyv.content, vm, 'poweredoff', module.params['force'])
            result = pyv.remove_vm(vm, module.params['delete_from_inventory'])
        elif module.params['state'] == 'present':
            # Note that check_mode is handled inside reconfigure_vm
            result = pyv.reconfigure_vm()
        elif module.params['state'] in ['poweredon', 'powered-on', 'poweredoff',
                                        'powered-off', 'restarted', 'suspended',
                                        'shutdownguest', 'shutdown-guest',
                                        'rebootguest', 'reboot-guest']:
            if module.check_mode:
                # Identify if the power state would have changed if not in check mode
                current_powerstate = vm.summary.runtime.powerState.lower()
                powerstate_will_change = False
                if ((current_powerstate == 'poweredon' and module.params['state'] not in ['poweredon', 'powered-on'])
                        or (current_powerstate == 'poweredoff' and module.params['state']
                            not in ['poweredoff', 'powered-off', 'shutdownguest', 'shutdown-guest'])
                        or (current_powerstate == 'suspended' and module.params['state'] != 'suspended')):
                    powerstate_will_change = True

                result.update(
                    vm_name=vm.name,
                    changed=powerstate_will_change,
                    current_powerstate=current_powerstate,
                    desired_operation='set_vm_power_state',
                )
                module.exit_json(**result)
            # set powerstate
            tmp_result = set_vm_power_state(pyv.content, vm, module.params['state'], module.params['force'], module.params['state_change_timeout'])
            if tmp_result['changed']:
                result["changed"] = True
                if module.params['state'] in ['poweredon', 'powered-on', 'restarted', 'rebootguest', 'reboot-guest'] and module.params['wait_for_ip_address']:
                    wait_result = wait_for_vm_ip(pyv.content, vm, module.params['wait_for_ip_address_timeout'])
                    if not wait_result:
                        module.fail_json(msg='Waiting for IP address timed out')
                    tmp_result['instance'] = wait_result
            if not tmp_result["failed"]:
                result["failed"] = False
            result['instance'] = tmp_result['instance']
            if tmp_result["failed"]:
                result["failed"] = True
                result["msg"] = tmp_result["msg"]
        else:
            # This should not happen
            raise AssertionError()
    # VM doesn't exist
    else:
        if module.params['state'] in ['poweredon', 'powered-on', 'poweredoff', 'powered-off',
                                      'present', 'restarted', 'suspended']:
            if module.check_mode:
                result.update(
                    changed=True,
                    desired_operation='deploy_vm',
                )
                module.exit_json(**result)
            result = pyv.deploy_vm()
            if result['failed']:
                module.fail_json(msg='Failed to create a virtual machine : %s' % result['msg'])

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
