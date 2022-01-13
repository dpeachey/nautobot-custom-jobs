# nautobot-custom-jobs

This repo contains custom jobs for [Nautobot](https://github.com/nautobot/nautobot).


### Installation

---

##### Prerequisites

1. [Nautobot](https://github.com/nautobot/nautobot)

2. [nautobot-plugin-nornir](https://github.com/nautobot/nautobot-plugin-nornir)

3. [nautobot-plugin-golden-config](https://github.com/nautobot/nautobot-plugin-golden-config)


Follow the Nautobot documentation to install the jobs using either the Git repository method ([Git Repositories - Jobs](https://nautobot.readthedocs.io/en/stable/models/extras/gitrepository/#jobs)) or the local **jobs** directory method ([Jobs](https://nautobot.readthedocs.io/en/stable/additional-features/jobs/#writing-jobs)).


### Credentials

---

Jobs that connect to devices need to use credentials to do so and the `nautobot-plugin-nornir` plugin already provides a way to set a default username and password, as detailed here: https://github.com/nautobot/nautobot-plugin-nornir#credentials

If customised credential logic is required it is possible to create a custom credential class and write your own credential logic.

The `custom_credentials.py` file provides an example of how to do this. In this example the credentials are defined by platform sepcific `<PLATFORM>_USERNAME` and `<PLATFORM>_PASSWORD` environment variables. The Nautobot device object is passed to the custom credentials function and the platform related to the device is used to look up the correct environment variables.

For example, if the platform name related to your device is defined as `junos` then the `JUNOS_USERNAME` and `JUNOS_PASSWORD` environment variables will be used.

If you decide to use the custom credentials you will need to change the `nautobot-plugin-nornir` plugin configuration in the `nautobot_config.py` file as follows:

```
PLUGINS_CONFIG = {
    "nautobot_plugin_nornir": {
        "nornir_settings": {
            "credentials": "custom_credentials.CustomNautobotORMCredentials",
        },
    },
}
```


### Jobs

---

`**device_config.py**`

This file provides device configuation jobs. Currently there is a single job '**Replace Device Configuration**' which leverages the Nornir task `napalm_configure` to replace the configuration on the target device. Specifically the job uses the device intended configuration that is generated by the [nautobot-plugin-golden-config](https://github.com/nautobot/nautobot-plugin-golden-config) plugin. 

The job also provides a dry run option which can be used to test deployment of the intended configuration. The job results in the Nautobot UI will be populated with the device configuration diffs.
