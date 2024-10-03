from fastapi_cloud_healthcheck import HealthCheckBase, HealthCheckStatusEnum
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.core.exceptions import ResourceNotFoundError


class HealthCheckAzureVM(HealthCheckBase):
    def __init__(self, vm_name: str, resource_group: str, subscription_id: str, region: str) -> None:
        super().__init__()
        self._vm_name = vm_name
        self._resource_group = resource_group
        self._subscription_id = subscription_id
        self._region = region

        self._identifier = vm_name
        self._metadata = {
            "provider": "azure",
            "region": region,
            "category": "compute",
            "serviceName": "VM",
            "subId": subscription_id
        }
        self._statusMessages = {}

        # Initialize Azure credentials and clients
        credential = DefaultAzureCredential()
        self.compute_client = ComputeManagementClient(credential, subscription_id)
        self.network_client = NetworkManagementClient(credential, subscription_id)

    def __checkHealth__(self) -> HealthCheckStatusEnum:
        """Perform Azure VM health checks."""

        if not self._check_vm_power_state() or not self._check_vm_disks() or not self._check_vm_nics():
            return HealthCheckStatusEnum.UNHEALTHY

        return HealthCheckStatusEnum.HEALTHY

    def _check_vm_power_state(self) -> bool:
        """Check if the VM is running."""
        try:
            instance_view = self.compute_client.virtual_machines.instance_view(self._resource_group, self._vm_name)
            for status in instance_view.statuses:
                if "PowerState/running" in status.code:
                    self._statusMessages["powerStateCheck"] = "VM is running."
                    return True
            self._statusMessages["powerStateCheck"] = "VM is not running."
            return False
        except (ResourceNotFoundError, Exception) as e:
            self._statusMessages["powerStateCheck"] = f"Error: {str(e)}"
            return False

    def _check_vm_disks(self) -> bool:
        """Check the health of attached disks."""
        try:
            vm = self.compute_client.virtual_machines.get(self._resource_group, self._vm_name)
            for disk in vm.storage_profile.data_disks:
                if disk.managed_disk:
                    disk_info = self.compute_client.disks.get_by_id(disk.managed_disk.id)
                    if disk_info.provisioning_state != "Succeeded":
                        self._statusMessages["diskHealthCheck"] = f"Disk {disk_info.name} is not healthy."
                        return False
            self._statusMessages["diskHealthCheck"] = "All disks are healthy."
            return True
        except (ResourceNotFoundError, Exception) as e:
            self._statusMessages["diskHealthCheck"] = f"Error: {str(e)}"
            return False

    def _check_vm_nics(self) -> bool:
        """Check the health of VM network interfaces."""
        try:
            vm = self.compute_client.virtual_machines.get(self._resource_group, self._vm_name)
            for nic_ref in vm.network_profile.network_interfaces:
                # Extract NIC name from the NIC ID (last part of the ID)
                nic_name = nic_ref.id.split("/")[-1]
                nic_info = self.network_client.network_interfaces.get(self._resource_group, nic_name)

                if nic_info.provisioning_state != "Succeeded":
                    self._statusMessages["networkInterfaceCheck"] = f"NIC {nic_info.name} is not healthy."
                    return False
            self._statusMessages["networkInterfaceCheck"] = "All NICs are healthy."
            return True
        except (ResourceNotFoundError, Exception) as e:
            self._statusMessages["networkInterfaceCheck"] = f"Error: {str(e)}"
            return False

