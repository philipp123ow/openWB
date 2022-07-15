#!/usr/bin/env python3
import logging
from typing import Dict, List

from helpermodules.cli import run_using_positional_cli_args
from modules.common import modbus
from modules.common.abstract_device import AbstractDevice
from modules.common.component_context import SingleComponentUpdateContext
from modules.sma_sunny_island import bat

log = logging.getLogger(__name__)


def get_default_config() -> dict:
    return {
        "name": "SMA Sunny Island",
        "type": "sma_sunny_island",
        "id": 0,
        "configuration": {
            "ip_address": None
        }
    }


class Device(AbstractDevice):
    COMPONENT_TYPE_TO_CLASS = {
        "bat": bat.SunnyIslandBat
    }

    def __init__(self, device_config: dict) -> None:
        self.components = {}  # type: Dict[str, bat.SunnyIslandBat]
        try:
            self.device_config = device_config
            ip_address = device_config["configuration"]["ip_address"]
            self.client = modbus.ModbusTcpClient_(ip_address, 502)
        except Exception:
            log.exception("Fehler im Modul "+device_config["name"])

    def add_component(self, component_config: dict) -> None:
        component_type = component_config["type"]
        if component_type in self.COMPONENT_TYPE_TO_CLASS:
            self.components["component"+str(component_config["id"])] = (self.COMPONENT_TYPE_TO_CLASS[component_type](
                component_config,
                self.client))
        else:
            raise Exception(
                "illegal component type " + component_type + ". Allowed values: " +
                ','.join(self.COMPONENT_TYPE_TO_CLASS.keys())
            )

    def update(self) -> None:
        log.debug("Start device reading " + str(self.components))
        if self.components:
            for component in self.components.values():
                # Auch wenn bei einer Komponente ein Fehler auftritt, sollen alle anderen noch ausgelesen werden.
                with SingleComponentUpdateContext(component.component_info):
                    component.update()
        else:
            log.warning(
                self.device_config["name"] +
                ": Es konnten keine Werte gelesen werden, da noch keine Komponenten konfiguriert wurden."
            )


COMPONENT_TYPE_TO_MODULE = {
    "bat": bat
}


def read_legacy(component_type: str, ip_address: str) -> None:
    log.debug("SMA Modbus Ip-Adresse: "+ip_address)
    if component_type in COMPONENT_TYPE_TO_MODULE:
        component_config = COMPONENT_TYPE_TO_MODULE[component_type].get_default_config()
    else:
        raise Exception("illegal component type " + component_type +
                        ". Allowed values: " +
                        ','.join(COMPONENT_TYPE_TO_MODULE.keys()))

    component_config["id"] = None
    device_config = get_default_config()
    device_config["configuration"]["ip_address"] = ip_address
    dev = Device(device_config)
    dev.add_component(component_config)
    dev.update()


def main(argv: List[str]):
    run_using_positional_cli_args(read_legacy, argv)
