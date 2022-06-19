"""Nautobot device configuration jobs."""

from nautobot_golden_config.models import GoldenConfig
from nautobot_golden_config.utilities.helper import get_job_filter

from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory

from nornir import InitNornir
from nornir.core.inventory import Host
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir.core.task import AggregatedResult, MultiResult, Result, Task

from nornir_napalm.plugins.tasks import napalm_configure

from nornir_utils.plugins.functions import print_result

from nautobot.dcim.models import (
    Device,
    DeviceRole,
    DeviceType,
    Manufacturer,
    Platform,
    Region,
    Site,
)
from nautobot.tenancy.models import Tenant, TenantGroup
from nautobot.extras.jobs import BooleanVar, Job, MultiObjectVar

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)
name = "Device Configuration"


def init_nornir(data) -> InitNornir:
    """Initialise Nornir object."""
    return InitNornir(
        runner=NORNIR_SETTINGS.get("runner"),
        logging={"enabled": False},
        dry_run=data["dry_run"],
        inventory={
            "plugin": "nautobot-inventory",
            "options": {
                "credentials_class": NORNIR_SETTINGS.get("credentials"),
                "params": NORNIR_SETTINGS.get("inventory_params"),
                "queryset": get_job_filter(data),
            },
        },
    )


class FormEntry:
    """Form entries."""

    tenant_group = MultiObjectVar(model=TenantGroup, required=False)
    tenant = MultiObjectVar(model=Tenant, required=False)
    region = MultiObjectVar(model=Region, required=False)
    site = MultiObjectVar(model=Site, required=False)
    role = MultiObjectVar(model=DeviceRole, required=False)
    manufacturer = MultiObjectVar(model=Manufacturer, required=False)
    platform = MultiObjectVar(model=Platform, required=False)
    device_type = MultiObjectVar(model=DeviceType, required=False)
    device = MultiObjectVar(model=Device, required=False)
    dry_run = BooleanVar(
        label="Dry run",
        default=True,
        required=False,
    )


class LogResult:
    """Nornir results logging processor."""

    def __init__(self, job, data) -> None:
        """Initialise processor."""
        self.job = job
        self.data = data

    def task_started(self, task: Task) -> None:
        """Task started logger."""
        # Log task started to job results
        if self.data["dry_run"]:
            self.job.log_info(None, f"{task.name} task started (DRY RUN)")
        else:
            self.job.log_info(None, f"{task.name} task started")

    def task_completed(self, task: Task, result: AggregatedResult) -> None:
        """Task completed logger."""
        # Print results to logs
        print_result(result)

        # Log task completed to job results
        if self.data["dry_run"]:
            self.job.log_info(None, f"{task.name} task completed (DRY RUN)")
        else:
            self.job.log_info(None, f"{task.name} task completed")

    def task_instance_started(self, task: Task, host: Host) -> None:
        """Task instance started logger."""

    def task_instance_completed(
        self, task: Task, host: Host, result: MultiResult
    ) -> None:
        """Task instance completed logger."""
        # If device config was changed, log the diff to the job results
        if result.changed:
            self.job.log_success(
                task.host.data["obj"], f"DIFF:\n```\n{result[1].diff}\n```"
            )
        # If device config failed, log the error to the job results
        elif result.failed:
            self.job.log_failure(
                task.host.data["obj"], f"FAILED:\n```\n{result[1].exception}\n```"
            )
        else:
            self.job.log_info(task.host.data["obj"], "No changes for device")

    def subtask_instance_started(self, task: Task, host: Host) -> None:
        """Subtask instance started logger."""

    def subtask_instance_completed(
        self, task: Task, host: Host, result: MultiResult
    ) -> None:
        """Subtask instance completed logger."""


class MergeConfig(FormEntry, Job):
    """Merge configuration job."""

    class Meta:
        """Job attributes."""

        name = "Merge configuration"
        description = "Merge device configuration with intended configuration"
        read_only = True

    tenant_group = FormEntry.tenant_group
    tenant = FormEntry.tenant
    region = FormEntry.region
    site = FormEntry.site
    role = FormEntry.role
    manufacturer = FormEntry.manufacturer
    platform = FormEntry.platform
    device_type = FormEntry.device_type
    device = FormEntry.device
    dry_run = FormEntry.dry_run

    def run(self, data, commit) -> None:
        """Run configure device job."""
        # Init Nornir and run configure device task for each device
        try:
            with init_nornir(data) as nornir_obj:
                nr = nornir_obj.with_processors([LogResult(self, data)])
                nr.run(
                    task=self._config_device,
                    name=self.name,
                )
        except Exception as err:
            self.log_failure(None, f"```\n{err}\n```")
            raise

    def _config_device(self, task: Task) -> Result:
        """NAPALM configure task."""
        # Get device object and intended configuration
        device_obj = task.host.data["obj"]
        intended_config = GoldenConfig.objects.get(
            device=device_obj
        ).intended_config

        # Run NAPALM task to configure device with intended config
        task.run(
            task=napalm_configure,
            replace=False,
            configuration=intended_config,
        )


class ReplaceConfig(FormEntry, Job):
    """Replace configuration job."""

    class Meta:
        """Job attributes."""

        name = "Replace configuration"
        description = "Replace device configuration with intended configuration"
        read_only = True

    tenant_group = FormEntry.tenant_group
    tenant = FormEntry.tenant
    region = FormEntry.region
    site = FormEntry.site
    role = FormEntry.role
    manufacturer = FormEntry.manufacturer
    platform = FormEntry.platform
    device_type = FormEntry.device_type
    device = FormEntry.device
    dry_run = FormEntry.dry_run

    def run(self, data, commit) -> None:
        """Run configure device job."""
        # Init Nornir and run configure device task for each device
        try:
            with init_nornir(data) as nornir_obj:
                nr = nornir_obj.with_processors([LogResult(self, data)])
                nr.run(
                    task=self._config_device,
                    name=self.name,
                )
        except Exception as err:
            self.log_failure(None, f"```\n{err}\n```")
            raise

    def _config_device(self, task: Task) -> Result:
        """NAPALM configure task."""
        # Get device object and intended configuration
        device_obj = task.host.data["obj"]
        intended_config = GoldenConfig.objects.get(
            device=device_obj
        ).intended_config

        # Run NAPALM task to configure device with intended config
        task.run(
            task=napalm_configure,
            replace=True,
            configuration=intended_config,
        )


class RestoreFromBackup(FormEntry, Job):
    """Restore configuration from backup job."""

    class Meta:
        """Job attributes."""

        name = "Restore configuration from backup"
        description = "Replace device configuration with latest backup configuration"
        read_only = True

    tenant_group = FormEntry.tenant_group
    tenant = FormEntry.tenant
    region = FormEntry.region
    site = FormEntry.site
    role = FormEntry.role
    manufacturer = FormEntry.manufacturer
    platform = FormEntry.platform
    device_type = FormEntry.device_type
    device = FormEntry.device
    dry_run = FormEntry.dry_run

    def run(self, data, commit) -> None:
        """Run configure device job."""
        # Init Nornir and run configure device task for each device
        try:
            with init_nornir(data) as nornir_obj:
                nr = nornir_obj.with_processors([LogResult(self, data)])
                nr.run(
                    task=self._config_device,
                    name=self.name,
                )
        except Exception as err:
            self.log_failure(None, f"```\n{err}\n```")
            raise

    def _config_device(self, task: Task) -> Result:
        """NAPALM configure task."""
        # Get device object and backup configuration
        device_obj = task.host.data["obj"]
        backup_config = GoldenConfig.objects.get(
            device=device_obj
        ).backup_config

        # Run NAPALM task to configure device with backup config
        task.run(
            task=napalm_configure,
            replace=True,
            configuration=backup_config,
        )
