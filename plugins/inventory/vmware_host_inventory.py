# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2020, dacrystal
# Copyright: (c) 2021, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    name: vmware_host_inventory
    short_description: VMware ESXi hostsystem inventory source
    author:
      - Abhijeet Kasurde (@Akasurde)
    description:
        - Get VMware ESXi hostsystem as inventory hosts from VMware environment.
        - Uses any file which ends with vmware.yml, vmware.yaml, vmware_host_inventory.yml, or vmware_host_inventory.yaml as a YAML configuration file.
    extends_documentation_fragment:
      - inventory_cache
      - constructed
    requirements:
      - "vSphere Automation SDK - For tag feature"
    options:
        hostname:
            description:
            - Name or IP of vCenter or ESXi server.
            - Accepts vault encrypted variable.
            required: true
            env:
              - name: VMWARE_HOST
              - name: VMWARE_SERVER
        username:
            description:
            - Name of vSphere user.
            - Accepts vault encrypted variable.
            required: true
            env:
              - name: VMWARE_USER
              - name: VMWARE_USERNAME
        password:
            description:
            - Password of vSphere user.
            - Accepts vault encrypted variable.
            required: true
            env:
              - name: VMWARE_PASSWORD
        port:
            description: Port number used to connect to vCenter or ESXi Server.
            default: 443
            type: int
            env:
              - name: VMWARE_PORT
        validate_certs:
            description:
            - Allows connection when SSL certificates are not valid.
            - Set to C(false) when certificates are not trusted.
            default: true
            type: bool
            env:
              - name: VMWARE_VALIDATE_CERTS
        with_tags:
            description:
            - Include tags and associated hosts.
            - Requires 'vSphere Automation SDK' library to be installed on the given controller machine.
            - Please refer following URLs for installation steps
            - U(https://code.vmware.com/web/sdk/7.0/vsphere-automation-python)
            default: false
            type: bool
        hostnames:
            description:
            - A list of templates in order of precedence to compose inventory_hostname.
            - Ignores template if resulted in an empty string or None value.
            - You can use property specified in I(properties) as variables in the template.
            type: list
            elements: string
            default: ['name']
        properties:
            description:
            - Specify the list of VMware schema properties associated with the ESXi hostsystem.
            - These properties will be populated in hostvars of the given ESXi hostsystem.
            - Each value in the list can be a path to a specific property in hostsystem object or a path to a collection of hostsystem objects.
            - C(summary.runtime.powerState) are required if C(keyed_groups) is set to default.
            - Please make sure that all the properties that are used in other parameters are included in this options.
            - In addition to ESXi hostsystem's properties, the following are special values
            - Use C(customValue) to populate ESXi hostsystem's custom attributes. C(customValue) is only supported by vCenter and not by ESXi.
            - Use C(all) to populate all the properties of the virtual machine.
              The value C(all) is time consuming operation, do not use unless required absolutely.
            type: list
            elements: string
            default: [ 'name', 'customValue', 'summary.runtime.powerState' ]
        with_nested_properties:
            description:
            - This option transform flatten properties name to nested dictionary.
            type: bool
            default: true
        keyed_groups:
            description:
            - Add hosts to group based on the values of a variable.
            type: list
            default: [
                {key: 'summary.runtime.powerState', separator: ''},
            ]
        filters:
            description:
            - This option allows client-side filtering hosts with jinja templating.
            - When server-side filtering is introduced, it should be preferred over this.
            type: list
            elements: str
            default: []
        resources:
            description:
            - A list of resources to limit search scope.
            - Each resource item is represented by exactly one C('vim_type_snake_case):C(list of resource names) pair and optional nested I(resources)
            - Key name is based on snake case of a vim type name; e.g C(host_system) correspond to C(vim.HostSystem)
            required: false
            type: list
            elements: dict
            default: []
        with_path:
            description:
            - Include ESXi hostsystem's path.
            - Set this option to a string value to replace root name from I('Datacenters').
            default: false
            type: bool
        with_sanitized_property_name:
            description:
                - This option allows property name sanitization to create safe property names for use in Ansible.
                - Also, transforms property name to snake case.
            type: bool
            default: false
        proxy_host:
          description:
          - Address of a proxy that will receive all HTTPS requests and relay them.
          - The format is a hostname or a IP.
          - This feature depends on a version of pyvmomi>=v6.7.1.2018.12.
          type: str
          required: false
          env:
            - name: VMWARE_PROXY_HOST
        proxy_port:
          description:
          - Port of the HTTP proxy that will receive all HTTPS requests and relay them.
          type: int
          required: false
          env:
            - name: VMWARE_PROXY_PORT
"""

EXAMPLES = r"""
# Sample configuration file for VMware Host dynamic inventory
    plugin: community.vmware.vmware_host_inventory
    strict: false
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: false
    with_tags: true

# Using compose
    plugin: community.vmware.vmware_host_inventory
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: false
    properties:
    - name
    - summary
    - config.lockdownMode
    compose:
        ansible_user: "'root'"
        ansible_connection: "'ssh'"
"""

try:
    from com.vmware.vapi.std_client import DynamicID
except ImportError:
    # Already handled in module_utils/inventory.py
    pass

try:
    from pyVmomi import vim
except ImportError:
    # Already handled in module_utils/inventory.py
    pass

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text, to_native
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.six import text_type
from ansible_collections.community.vmware.plugins.plugin_utils.inventory import (
    to_nested_dict,
    to_flatten_dict,
)
from ansible_collections.community.vmware.plugins.inventory.vmware_vm_inventory import BaseVMwareInventory
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = "community.vmware.vmware_host_inventory"

    def verify_file(self, path):
        """
        Verify plugin configuration file and mark this plugin active
        Args:
            path: Path of configuration YAML file
        Returns: True if everything is correct, else False
        """
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(
                (
                    "vmware.yaml",
                    "vmware.yml",
                    "vmware_host_inventory.yaml",
                    "vmware_host_inventory.yml",
                )
            ):
                valid = True

        return valid

    def parse(self, inventory, loader, path, cache=True):
        """
        Parses the inventory file
        """
        super(InventoryModule, self).parse(inventory, loader, path, cache=cache)

        cache_key = self.get_cache_key(path)

        config_data = self._read_config_data(path)

        # set _options from config data
        self._consume_options(config_data)

        hostname = self.get_option("hostname")
        username = self.get_option("username")
        password = self.get_option("password")

        if isinstance(hostname, AnsibleVaultEncryptedUnicode):
            hostname = hostname.data

        if isinstance(username, AnsibleVaultEncryptedUnicode):
            username = username.data

        if isinstance(password, AnsibleVaultEncryptedUnicode):
            password = password.data

        self.pyv = BaseVMwareInventory(
            hostname=hostname,
            username=username,
            password=password,
            port=self.get_option("port"),
            with_tags=self.get_option("with_tags"),
            validate_certs=self.get_option("validate_certs"),
            http_proxy_host=self.get_option("proxy_host"),
            http_proxy_port=self.get_option("proxy_port")
        )

        self.pyv.do_login()

        if cache:
            cache = self.get_option("cache")

        update_cache = False
        if cache:
            try:
                cacheable_results = self._cache[cache_key]
            except KeyError:
                update_cache = True

        if cache and not update_cache:
            self._populate_from_cache(cacheable_results)
        else:
            cacheable_results = self._populate_from_source()

        if update_cache or (not cache and self.get_option("cache")):
            self._cache[cache_key] = cacheable_results

    def _populate_from_cache(self, cache_data):
        """
        Populate cache using source data

        """
        for host, host_properties in cache_data.items():
            self._populate_host_properties(host_properties, host)

    def _populate_from_source(self):
        """
        Populate inventory data from direct source

        """
        hostvars = {}
        strict = self.get_option("strict")

        host_properties = self.get_option("properties")
        if not isinstance(host_properties, list):
            host_properties = [host_properties]

        if len(host_properties) == 0:
            host_properties = ["name"]

        if "all" in host_properties:
            query_props = None
            host_properties.remove("all")
        else:
            if "runtime.connectionState" not in host_properties:
                host_properties.append("runtime.connectionState")
            query_props = [x for x in host_properties if x != "customValue"]

        objects = self.pyv.get_managed_objects_properties(
            vim_type=vim.HostSystem,
            properties=query_props,
            resources=self.get_option("resources"),
            strict=strict,
        )

        tags_info = dict()
        if self.pyv.with_tags:
            tag_svc = self.pyv.rest_content.tagging.Tag
            cat_svc = self.pyv.rest_content.tagging.Category

            tags = tag_svc.list()
            for tag in tags:
                tag_obj = tag_svc.get(tag)
                tags_info[tag_obj.id] = (
                    tag_obj.name,
                    cat_svc.get(tag_obj.category_id).name,
                )

        hostnames = self.get_option("hostnames")

        for host_obj in objects:
            properties = dict()
            for host_obj_property in host_obj.propSet:
                properties[host_obj_property.name] = host_obj_property.val

            if (
                properties.get("runtime.connectionState")
                or properties["runtime"].connectionState
            ) in ("disconnected", "notResponding"):
                continue

            # Custom values
            if "customValue" in host_properties:
                field_mgr = []
                if self.pyv.content.customFieldsManager:  # not an ESXi
                    field_mgr = self.pyv.content.customFieldsManager.field
                for cust_value in host_obj.obj.customValue:
                    properties[
                        [y.name for y in field_mgr if y.key == cust_value.key][0]
                    ] = cust_value.value

            # Tags
            if self.pyv.with_tags:
                properties["tags"] = []
                properties["categories"] = []
                properties["tag_category"] = {}

            if tags_info:
                # Add virtual machine to appropriate tag group
                host_mo_id = host_obj.obj._GetMoId()  # pylint: disable=protected-access
                host_dynamic_id = DynamicID(type="HostSystem", id=host_mo_id)
                tag_association = self.pyv.rest_content.tagging.TagAssociation
                for tag_id in tag_association.list_attached_tags(host_dynamic_id):
                    if tag_id not in tags_info:
                        # Ghost Tags
                        continue
                    # Add tags related to VM
                    properties["tags"].append(tags_info[tag_id][0])
                    # Add categories related to VM
                    properties["categories"].append(tags_info[tag_id][1])
                    # Add tag and categories related to VM
                    if tags_info[tag_id][1] not in properties["tag_category"]:
                        properties["tag_category"][tags_info[tag_id][1]] = []
                    properties["tag_category"][tags_info[tag_id][1]].append(
                        tags_info[tag_id][0]
                    )

            # Path
            with_path = self.get_option("with_path")
            if with_path:
                path = []
                parent = host_obj.obj.parent
                while parent:
                    path.append(parent.name)
                    parent = parent.parent
                path.reverse()
                properties["path"] = "/".join(path)

            host_properties = to_nested_dict(properties)

            # Check if we can add host as per filters
            host_filters = self.get_option("filters")
            if not self._can_add_host(host_filters, host_properties, strict=strict):
                continue

            host = self._get_hostname(host_properties, hostnames, strict=strict)

            if host not in hostvars:
                hostvars[host] = host_properties
                self._populate_host_properties(host_properties, host)
                self.inventory.set_variable(
                    host, "ansible_host", self.get_management_ip(host_obj.obj)
                )

        return hostvars

    def _get_hostname(self, properties, hostnames, strict=False):
        hostname = None
        errors = []

        for preference in hostnames:
            try:
                hostname = self._compose(preference, properties)
            except Exception as e:  # pylint: disable=broad-except
                if strict:
                    raise AnsibleError(
                        "Could not compose %s as hostnames - %s"
                        % (preference, to_native(e))
                    )

                errors.append((preference, str(e)))
            if hostname:
                return to_text(hostname)

        raise AnsibleError(
            "Could not template any hostname for host, errors for each preference: %s"
            % (", ".join(["%s: %s" % (pref, err) for pref, err in errors]))
        )

    def _can_add_host(self, host_filters, host_properties, strict=False):
        can_add_host = True
        for host_filter in host_filters:
            try:
                can_add_host = self._compose(host_filter, host_properties)
            except Exception as e:  # pylint: disable=broad-except
                if strict:
                    raise AnsibleError(
                        "Could not evaluate %s as host filters - %s"
                        % (host_filter, to_native(e))
                    )

            if not can_add_host:
                return False
        return True

    @staticmethod
    def get_management_ip(host):
        try:
            vnic_manager = host.configManager.virtualNicManager
            net_config = vnic_manager.QueryNetConfig("management")
            # filter nics that are selected
            for nic in net_config.candidateVnic:
                if nic.key in net_config.selectedVnic:
                    # add hostvar 'management_ip' to each host
                    return nic.spec.ip.ipAddress
        except Exception:
            return ""
        return ""

    def _populate_host_properties(self, host_properties, host):
        # Load VM properties in host_vars
        self.inventory.add_host(host)

        # Use constructed if applicable
        strict = self.get_option("strict")

        # Composed variables
        compose = self.get_option("compose")
        self._set_composite_vars(compose, host_properties, host, strict=strict)
        # Complex groups based on jinja2 conditionals, hosts that meet the conditional are added to group
        self._add_host_to_composed_groups(
            self.get_option("groups"), host_properties, host, strict=strict
        )
        # Create groups based on variable values and add the corresponding hosts to it
        self._add_host_to_keyed_groups(
            self.get_option("keyed_groups"), host_properties, host, strict=strict
        )

        with_path = self.get_option("with_path")
        if with_path:
            parents = host_properties["path"].split("/")
            if parents:
                if isinstance(with_path, text_type):
                    parents = [with_path] + parents

                c_name = self._sanitize_group_name("/".join(parents))
                c_group = self.inventory.add_group(c_name)
                self.inventory.add_host(host, c_group)
                parents.pop()

                while len(parents) > 0:
                    p_name = self._sanitize_group_name("/".join(parents))
                    p_group = self.inventory.add_group(p_name)

                    self.inventory.add_child(p_group, c_group)
                    c_group = p_group
                    parents.pop()

        can_sanitize = self.get_option("with_sanitized_property_name")

        # Sanitize host properties: to snake case
        if can_sanitize:  # to snake case
            host_properties = camel_dict_to_snake_dict(host_properties)

        with_nested_properties = self.get_option("with_nested_properties")
        if with_nested_properties:
            for k, v in host_properties.items():
                k = self._sanitize_group_name(k) if can_sanitize else k
                self.inventory.set_variable(host, k, v)

        # For backward compatability
        host_properties = to_flatten_dict(host_properties)
        for k, v in host_properties.items():
            k = self._sanitize_group_name(k) if can_sanitize else k
            self.inventory.set_variable(host, k, v)
