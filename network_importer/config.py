"""
(c) 2019 Network To Code

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
  http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import toml
import os.path
from pathlib import Path
from jsonschema import Draft7Validator, validators
from . import schema

# -----------------------------------------------------------------------------
#                                 GLOBALS
# -----------------------------------------------------------------------------

main = None
logs = None
netbox = None
batfish = None
network = None


def extend_with_default(validator_class):
    """
    

    Args:
      validator_class: 

    Returns:

    """
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        """
        

        Args:
          validator: 
          properties: 
          instance: 
          schema: 

        Returns:

        """
        for property_name, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property_name, subschema["default"])

        for error in validate_properties(validator, properties, instance, schema):
            yield error

    return validators.extend(validator_class, {"properties": set_defaults})


def env_var_to_bool(var):
    """
    Try to convert an environment variable into a boolean
    1, True, true & yes >> True
    0, False, false & no >> False
    """
    if str(var).lower() in ["true", "yes"] or var == "1":
        return True

    if str(var).lower() in ["false", "no"] or var == "0":
        return False

    return var


def load_config(config_file_name=None, config_data=None):
    """
    
    Args:
      config_file_name: (Default value = DEFAULT_CONFIG_FILE_NAME)

    Returns:

    """
    global main, logs, netbox, batfish, network

    if config_file_name == None and config_data == None:
        config = {}
    elif config_data:
        config = config_data
    elif not os.path.exists(config_file_name):
        raise Exception(f"Unable to find the configuration file {config_file_name}")
    else:
        config_string = Path(config_file_name).read_text()
        config = toml.loads(config_string)

    # -------------------------------------------------------------------------
    #                                netbox
    # -------------------------------------------------------------------------

    # Read Netbox configuration from the provided file, or default to the
    # alternate environment variables.

    netbox = config.setdefault("netbox", {})

    if "NETBOX_ADDRESS" in os.environ:
        netbox["address"] = os.environ.get("NETBOX_ADDRESS")

    if "NETBOX_TOKEN" in os.environ:
        netbox["token"] = os.environ.get("NETBOX_TOKEN")

    if "NETBOX_CACERT" in os.environ:
        netbox["cacert"] = os.environ.get("NETBOX_CACERT")

    if "NETBOX_VERIFY_SSL" in os.environ:
        netbox["verify_ssl"] = env_var_to_bool(os.environ.get("NETBOX_VERIFY_SSL"))

    # -------------------------------------------------------------------------
    #                                batfish
    # -------------------------------------------------------------------------

    batfish = config.setdefault("batfish", {})

    if "BATFISH_ADDRESS" in os.environ:
        batfish["address"] = bool(os.environ.get("BATFISH_ADDRESS"))

    if "BATFISH_API_KEY" in os.environ:
        batfish["api_key"] = bool(os.environ.get("BATFISH_API_KEY"))

    # -------------------------------------------------------------------------
    #                                network
    # -------------------------------------------------------------------------

    network = config.setdefault("network", {})

    if "NETWORK_DEVICE_LOGIN" in os.environ:
        network["login"] = os.environ.get("NETWORK_DEVICE_LOGIN")

    if "NETWORK_DEVICE_PWD" in os.environ:
        network["password"] = os.environ.get("NETWORK_DEVICE_PWD")

    # -------------------------------------------------------------------------
    # validate the config structure using the JSON schema defined in the
    # `schama` module.  This process will also set the default values to the
    # configuration properties if they are not provided either in the config
    # file or alternate environment variables.
    # -------------------------------------------------------------------------

    config_validator = extend_with_default(Draft7Validator)

    config_validator(schema.config_schema).validate(config)
    # TODO Catch jsonschema.exceptions.ValidationError  and print proper error message

    # since the code will open a netbox connection in multiple places,
    # store the actual value provided to the pynetbox.Api, which is
    # also the underlying requests.Session.verify value, as documented
    # https://requests.readthedocs.io/en/master/user/advanced/#ssl-cert-verification

    netbox["request_ssl_verify"] = netbox.get("cacert") or netbox["verify_ssl"]

    main = config["main"]
    logs = config["logs"]
