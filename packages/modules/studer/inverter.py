#!/usr/bin/env python3

from modules.common import modbus
from modules.common.component_state import InverterState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_inverter_value_store


def get_default_config() -> dict:
    return {
        "name": "Studer Wechselrichter",
        "id": 0,
        "type": "inverter",
        "configuration": {
            "vc_count": 1,  # studer_vc (count MPPT Devices)
            "vc_type": "VS"  # studer_vc_type (MPPT type VS or VT)
        }
    }


class StuderInverter:
    def __init__(self, component_config: dict, tcp_client: modbus.ModbusTcpClient_) -> None:
        self.component_config = component_config
        self.__tcp_client = tcp_client
        self.__store = get_inverter_value_store(component_config["id"])
        self.component_info = ComponentInfo.from_component_config(component_config)

    def update(self) -> None:

        vc_count = self.component_config["configuration"]["vc_count"]
        vc_type = self.component_config["configuration"]["vc_type"]

        with self.__tcp_client:
            if vc_type == 'VS':
                mb_unit = 40
                mb_register = 20  # MB:20; ID: 15010; PV power kW
            elif vc_type == 'VT':
                mb_unit = 20
                mb_register = 8  # MB:8; ID: 11004; Power of the PV generator kW
            else:
                raise FaultState.error("Unbekannter VC-Typ: "+str(vc_type))
            power = 0
            for i in range(1, vc_count+1):
                mb_unit_dev = mb_unit+i
                power += self.__tcp_client.read_input_registers(mb_register, ModbusDataType.FLOAT_32, unit=mb_unit_dev)
            power = power * -1000

            if vc_type == 'VS':
                mb_register = 46  # MB:46; ID: 15023; Desc: Total PV produced energy MWh
            elif vc_type == 'VT':
                mb_register = 18  # MB:18; ID: 11009; Desc: Total produced energy MWh
            exported = 0
            for i in range(1, vc_count + 1):
                mb_unit_dev = mb_unit + i
                exported += self.__tcp_client.read_input_registers(mb_register, ModbusDataType.FLOAT_32,
                                                                   unit=mb_unit_dev)
            exported = exported * 1000000

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.__store.set(inverter_state)
