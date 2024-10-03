# fastapi_cloud_healthcheck_azure_vm

A FastAPI-based health check module for monitoring the health of Azure Virtual Machines (VMs) using the `fastapi_cloud_healthcheck` package.

## Features

* **VM Power State Check**: Verifies if the Azure VM is currently running.
* **Disk Health Check**: Checks the health status of attached disks to ensure they are provisioned successfully.
* **Network Interface Check**: Validates the health of network interfaces (NICs) associated with the Azure VM.

## Adding Health Checks

Here is a sample FastAPI application that integrates the Azure VM health check:

```python
from fastapi import FastAPI
from fastapi_cloud_healthcheck import HealthCheckFactory, create_health_check_route
from fastapi_cloud_healthcheck_azure_vm import HealthCheckAzureVM

app = FastAPI()

# Create Health Check Factory
health_check_factory = HealthCheckFactory()

# Add the Azure VM Health Check
health_check_factory.add(
    HealthCheckAzureVM(
        vm_name="my-azure-vm",
        resource_group="my-resource-group",
        subscription_id="my-subscription-id",
        region="eastus"
    )
)

# Add the health check route to FastAPI
app.add_api_route('/health', endpoint=create_health_check_route(factory=health_check_factory))

# Start the FastAPI server using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=5000)
