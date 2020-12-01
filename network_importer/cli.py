"""main cli for the network importer.

(c) 2020 Network To Code

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
# pylint: disable=C0103,W0102,C0415,R1724,W0611,R1710,R1710,E1101,W0613,,C0413,R0904,E1120

import logging
import sys
import pdb

import click
import urllib3
from diffsync.logging import enable_console_logging

from rich.console import Console
from rich.table import Table

import network_importer.config as config
from network_importer.utils import build_filter_params
from network_importer.main import NetworkImporter

import network_importer.performance as perf

urllib3.disable_warnings()

__author__ = "Damien Garros <damien.garros@networktocode.com>"

LOGGER = logging.getLogger("network-importer")

# pylint: disable=too-many-arguments


@click.version_option()
@click.option(
    "--config",
    "config_file",
    default="network_importer.toml",
    help="Network Importer Configuration file (TOML format)",
    type=str,
    show_default=True,
)
@click.option(
    "--limit",
    default=False,
    help="limit the execution on a specific device or group of devices --limit=device1 or --limit='site=sitea' ",
    type=str,
)
@click.option("--diff", is_flag=True, help="Show the diff for all objects")
@click.option("--apply", is_flag=True, help="Save changes in Backend")
@click.option(
    "--check", is_flag=True, help="Display what are the differences but do not save them",
)
@click.option(
    "--debug", is_flag=True, help="Keep the script in interactive mode once finished for troubleshooting", hidden=True
)
@click.option("--update-configs", is_flag=True, help="Pull the latest configs from the devices")
@click.group()
def main(config_file, limit, diff, apply, check, debug, update_configs, inventory):
    """Main CLI command for the network_importer."""
    config.load(config_file_name=config_file)
    perf.init()

    # ------------------------------------------------------------
    # Setup Logging
    # ------------------------------------------------------------
    logging.getLogger("pybatfish").setLevel(logging.ERROR)
    logging.getLogger("netaddr").setLevel(logging.ERROR)

    if config.SETTINGS.logs.level != "debug":
        logging.getLogger("paramiko.transport").setLevel(logging.CRITICAL)
        logging.getLogger("nornir.core.task").setLevel(logging.CRITICAL)

    logging.basicConfig(stream=sys.stdout, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    if config.SETTINGS.logs.level == "debug":
        LOGGER.setLevel(logging.DEBUG)
    elif config.SETTINGS.logs.level == "warning":
        LOGGER.setLevel(logging.WARNING)
    else:
        LOGGER.setLevel(logging.INFO)

    # Disable logging in console for DiffSync
    enable_console_logging(verbosity=0)

    filters = {}
    build_filter_params(config.SETTINGS.inventory.filter.split((",")), filters)

    ni = NetworkImporter()

    if update_configs:
        ni.build_inventory(limit=limit)
        ni.update_configurations()
        if not check and not apply:
            sys.exit(0)

    ni.init(limit=limit)

    if apply:
        ni.sync()

    elif check:
        diff = ni.diff()
        print(diff.str())

    perf.TIME_TRACKER.set_nbr_devices(len(ni.nornir.inventory.hosts.keys()))
    if config.SETTINGS.logs.performance_log:
        perf.TIME_TRACKER.print_all()

    LOGGER.info("Execution finished, processed %s device(s)", perf.TIME_TRACKER.nbr_devices)
    if debug:
        pdb.set_trace()


@click.option(
    "--config",
    "config_file",
    default="network_importer.toml",
    help="Network Importer Configuration file (TOML format)",
    type=str,
    show_default=True,
)
@click.option(
    "--limit",
    default=False,
    help="limit the execution on a specific device or group of devices --limit=device1 or --limit='site=sitea' ",
    type=str,
)
@main.command()
def inventory(config_file, limit):
    """Main CLI command for the network_importer."""
    config.load(config_file_name=config_file)

    if limit:
        table = Table(title=f"Device Inventory (limit:{limit})")
    else:
        table = Table(title="Device Inventory (all)")

    filters = {}
    build_filter_params(config.SETTINGS.inventory.filter.split((",")), filters)

    ni = NetworkImporter()
    ni.build_inventory(limit=limit)
    # ni.update_configurations()

    table.add_column("Device", style="cyan", no_wrap=True)
    table.add_column("Platform", style="magenta")
    table.add_column("Hostname")
    table.add_column("Reachable")
    table.add_column("Reason")

    for hostname, host in ni.nornir.inventory.hosts.items():
        if host.data["is_reachable"]:
            is_reachable = "[green]True"
            reason = None
        else:
            is_reachable = "[red]False"
            reason = f"[red]{host.data['not_reachable_reason']}"

        table.add_row(hostname, host.data["vendor"], host.hostname, is_reachable, reason)

    console = Console()
    console.print(table)


if __name__ == "__main__":
    main()
