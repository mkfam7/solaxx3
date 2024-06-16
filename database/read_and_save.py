"""Example of reading and saving some inverter registers."""

import sys
from datetime import datetime, timedelta
from os import environ

from solaxx3.solaxx3 import SolaxX3

from .mysql_data_source import MySQLDataSource


def _get_datetime(inverter_time: datetime) -> datetime:
    return inverter_time - timedelta(hours=TIMEZONE_OFFSET)


MYSQL_CONNECTION_INFO = {
    "user": environ["MYSQL_DB_USERNAME"],
    "host": environ["MYSQL_DB_HOST_IP"],
    "password": environ["MYSQL_DB_PASSWORD"],
}
DATABASE = environ["MYSQL_DB_DATABASE"]
TIMEZONE_OFFSET = 2

s = SolaxX3(port="/dev/ttyUSB0", baudrate=115200)
if not s.connect():
    print("Could not connect to inverter")
    sys.exit(1)

s.read_all_registers()

mysql_export_data = [
    {
        "database": DATABASE,
        "table": "solax_local",
        "data": {
            "uploadTime": _get_datetime(s.read("rtc_datetime")[0]),
            "inverter_status": s.read("run_mode")[0],
            "dc_solar_power": s.read("power_dc1")[0] + s.read("power_dc2")[0],
            "grid_voltage_r": s.read("grid_voltage_r")[0],
            "grid_voltage_s": s.read("grid_voltage_s")[0],
            "grid_voltage_t": s.read("grid_voltage_t")[0],
            "battery_capacity": s.read("battery_capacity")[0],
            "battery_power": s.read("battery_power_charge1")[0],
            "feed_in_power": s.read("feed_in_power")[0],
            "time_count_down": s.read("time_count_down")[0],
            "inverter_ac_power": s.read("grid_power")[0],
            "consumeenergy": s.read("energy_from_grid_meter")[0],
            "feedinenergy": s.read("energy_to_grid_meter")[0],
            "power_dc1": s.read("power_dc1")[0],
            "power_dc2": s.read("power_dc2")[0],
            "inv_volt_r": s.read("inv_volt_r")[0],
            "inv_volt_s": s.read("inv_volt_s")[0],
            "inv_volt_t": s.read("inv_volt_t")[0],
            "off_grid_power_active_r": s.read("off_grid_power_active_r")[0],
            "off_grid_power_active_s": s.read("off_grid_power_active_s")[0],
            "off_grid_power_active_t": s.read("off_grid_power_active_t")[0],
            "grid_power_r": s.read("grid_power_r")[0],
            "grid_power_s": s.read("grid_power_s")[0],
            "grid_power_t": s.read("grid_power_t")[0],
        },
    },
    {
        "database": DATABASE,
        "table": "solax_daily",
        "data": {
            "uploadDate": _get_datetime(s.read("rtc_datetime")[0]).date(),
            "feed_in": s.read("feed_in_energy_today")[0],
            "total_yield": s.read("energy_to_grid_today")[0],
        },
    },
]
mysql_data_source = MySQLDataSource(MYSQL_CONNECTION_INFO)


def bulk_save():
    """Save collected data."""

    mysql_data_source.bulk_save(mysql_export_data)


def _transfer(index: int, **extras) -> None:
    """Save a record of collected data."""

    data_record = mysql_export_data[index]
    database, tablename = data_record["database"], data_record["table"]
    data = data_record["data"]
    mysql_data_source.save_record(database, tablename, data, **extras)


save = bulk_save

if __name__ == "__main__":
    save()
