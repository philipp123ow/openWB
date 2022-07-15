#!/usr/bin/env python3
from modules.common import modbus
from modules.common.component_state import CounterState
from modules.common.fault_state import ComponentInfo
from modules.common.modbus import ModbusDataType
from modules.common.store import get_counter_value_store
from modules.solaredge.scale import scale_registers


def get_default_config() -> dict:
    return {
        "name": "SolarEdge Zähler",
        "id": 0,
        "type": "counter",
        "configuration": {
            "modbus_id": 1
        }
    }


class SolaredgeCounter:
    def __init__(self, device_id: int, component_config: dict, tcp_client: modbus.ModbusTcpClient_) -> None:
        self.component_config = component_config
        self.__tcp_client = tcp_client
        self.__store = get_counter_value_store(component_config["id"])
        self.component_info = ComponentInfo.from_component_config(component_config)

    def update(self):
        def read_scaled_int16(address: int, count: int):
            return scale_registers(
                self.__tcp_client.read_holding_registers(
                    address,
                    [ModbusDataType.INT_16] * (count+1),
                    unit=self.component_config["configuration"]["modbus_id"])
            )

        def read_scaled_uint32(address: int, count: int):
            return scale_registers(
                self.__tcp_client.read_holding_registers(
                    address,
                    [ModbusDataType.UINT_32] * (count)+[ModbusDataType.INT_16],
                    unit=self.component_config["configuration"]["modbus_id"])
            )

        # 40206: Total Real Power (sum of active phases)
        # 40207/40208/40209: Real Power by phase
        # 40210: AC Real Power Scale Factor
        powers = [-power for power in read_scaled_int16(40206, 4)]

        # 40191/40192/40193: AC Current by phase
        # 40194: AC Current Scale Factor
        currents = read_scaled_int16(40191, 3)

        # 40196/40197/40198: Voltage per phase
        # 40203: AC Voltage Scale Factor
        voltages = read_scaled_int16(40196, 7)[:3]

        # 40204: AC Frequency
        # 40205: AC Frequency Scale Factor
        frequency = read_scaled_int16(40204, 1)[0]

        # 40222/40223/40224: Power factor by phase (unit=%)
        # 40225: AC Power Factor Scale Factor
        power_factors = [power_factor / 100 for power_factor in read_scaled_int16(40222, 3)]

        # 40226: Total Exported Real Energy
        # 40228/40230/40232: Total Exported Real Energy Phase (not used)
        # 40234: Total Imported Real Energy
        # 40236/40238/40240: Total Imported Real Energy Phase (not used)
        # 40242: Real Energy Scale Factor
        counter_values = read_scaled_uint32(40226, 8)
        counter_exported, counter_imported = [counter_values[i] for i in [0, 4]]

        counter_state = CounterState(
            imported=counter_imported,
            exported=counter_exported,
            power=powers[0],
            powers=powers[1:],
            voltages=voltages,
            currents=currents,
            power_factors=power_factors,
            frequency=frequency
        )
        self.__store.set(counter_state)
