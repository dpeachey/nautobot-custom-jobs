"""Nautobot custom jobs credentials class."""

import os

from nautobot_plugin_nornir.plugins.credentials.nautobot_orm import (
    NautobotORMCredentials,
)


class CustomNautobotORMCredentials(NautobotORMCredentials):
    """Custom credentials per platform."""

    def get_device_creds(self, device):
        """Get device credentials."""
        return (
            self._get_env_var_value(f"{device.platform.name.upper()}_USERNAME"),
            self._get_env_var_value(f"{device.platform.name.upper()}_PASSWORD"),
            None,
        )

    def _get_env_var_value(self, env_var):
        """Get environment variable value."""
        try:
            return os.environ[env_var]
        except KeyError:
            raise KeyError(f"Environment variable not found: {env_var}") from KeyError()
