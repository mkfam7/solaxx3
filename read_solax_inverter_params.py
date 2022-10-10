from pymodbus.client.sync import ModbusSerialClient
from datetime import date, datetime, timedelta
import pytz


def unsigned16(result, addr):
    return result.getRegister(addr)


def join_msb_lsb(msb, lsb):
    return (msb << 16) | lsb


def twos_comp(val, bits):
    """compute the 2's complement of int value val"""

    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)  # compute negative value
    return val  # return positive value as is


client = ModbusSerialClient(
    method="rtu",
    port="/dev/ttyUSB0",
    # baudrate=9600,
    baudrate=115200,
    timeout=3,
    parity="N",
    stopbits=1,
    bytesize=8,
)

if client.connect():  # Trying for connect to Modbus Server/Slave
    """Reading from a holding register with the below content."""

    # print("Client connected successfully...")

    battery_capacity = client.read_input_registers(
        address=0x01C, count=1, unit=1
    ).getRegister(0)
    print(f"Battery capacity: {battery_capacity}%")

    feed_in_today_pack = client.read_input_registers(address=0x0098, count=2, unit=1)
    feed_in_today = (
        join_msb_lsb(
            unsigned16(feed_in_today_pack, 1), unsigned16(feed_in_today_pack, 0)
        )
        / 100
    )
    print(f"Feedin today: {feed_in_today}")

    consumtion_today = client.read_input_registers(address=0x009A, count=2, unit=1)
    print(
        f"Consumption today: {join_msb_lsb(unsigned16(consumtion_today, 1), unsigned16(consumtion_today, 0))}"
    )

    battery_charging = client.read_input_registers(
        address=0x0016, count=1, unit=1
    ).getRegister(0)
    if battery_charging > 0xFF:
        battery_charging = twos_comp(battery_charging, 16)
    print(f"Battery charging: {battery_charging},  , {battery_charging:b}")

    grid_voltage_r = (
        client.read_input_registers(address=0x006A, count=1, unit=1).getRegister(0) / 10
    )
    print(f"Grid voltage R: {grid_voltage_r}V")

    grid_voltage_s = (
        client.read_input_registers(address=0x006E, count=1, unit=1).getRegister(0) / 10
    )
    print(f"Grid voltage S: {grid_voltage_s}V")

    grid_voltage_t = (
        client.read_input_registers(address=0x0072, count=1, unit=1).getRegister(0) / 10
    )
    print(f"Grid voltage T: {grid_voltage_t}V")

    mode = {
        0: "Waiting",
        1: "Checking",
        2: "Normal",
        3: "Fault",
        4: "Permanent fault",
        5: "Update",
        6: "Off-grid waiting",
        7: "Off-grid",
        8: "Self testing",
        9: "Idle",
        10: "Standby",
    }
    run_mode = client.read_input_registers(address=0x0009, count=1, unit=1).getRegister(
        0
    )
    print(f"Run mode: {mode[run_mode]}")

    time_count_down = client.read_input_registers(
        address=0x0013, count=1, unit=1
    ).getRegister(0)
    print(f"time_count_down: {time_count_down}")

    inverter_ac_power = client.read_input_registers(
        address=0x0002, count=1, unit=1
    ).getRegister(0)
    print(f"inverter ac power???: {inverter_ac_power}")

    etoday_togrid = (
        client.read_input_registers(address=0x0050, count=1, unit=1).getRegister(0) / 10
    )
    print(f"etoday_togrid/yieldtoday: {etoday_togrid}")

    solar_energy_today = (
        client.read_input_registers(address=0x0096, count=1, unit=1).getRegister(0) / 10
    )
    print(f"solar_energy_today: {solar_energy_today}")

    echarge_today = (
        client.read_input_registers(address=0x0091, count=1, unit=1).getRegister(0) / 10
    )
    print(f"echarge_today: {echarge_today}")

    # d = client.read_input_registers(address=0x0016, count=1, unit=1)
    # print(f"something 1: {d.getRegister(0)}")

    # c = client.read_input_registers(address=0x00B0, count=2, unit=1)
    # print(f"something 2: {join_msb_lsb(unsigned16(c, 1), unsigned16(c, 0))/100}")

    energy_from_grid_pack = client.read_input_registers(address=0x004A, count=2, unit=1)
    energy_from_grid = (
        join_msb_lsb(
            unsigned16(energy_from_grid_pack, 1), unsigned16(energy_from_grid_pack, 0)
        )
        / 100
    )
    print(f"energy_from_grid/consume_energy: {energy_from_grid}")

    energy_to_grid_pack = client.read_input_registers(address=0x0048, count=2, unit=1)
    energy_to_grid = (
        join_msb_lsb(
            unsigned16(energy_to_grid_pack, 1), unsigned16(energy_to_grid_pack, 0)
        )
        / 100
    )
    print(f"energy_to_grid/feedin_energy: {energy_to_grid}")

    power_to_ev = client.read_input_registers(address=0x0026, count=2, unit=1)
    print(
        f"power_to_ev: {join_msb_lsb(unsigned16(power_to_ev, 1), unsigned16(power_to_ev, 0))}"
    )

    feed_in_power_bytes = client.read_input_registers(address=0x0046, count=2, unit=1)
    feed_in_power = join_msb_lsb(
        unsigned16(feed_in_power_bytes, 1), unsigned16(feed_in_power_bytes, 0)
    )

    if feed_in_power > 0xFFFF:
        feed_in_power = twos_comp(feed_in_power, 32)
    print(f"feed_in_power inst: {feed_in_power}")

    output_energy_charge = client.read_input_registers(address=0x001D, count=2, unit=1)
    print(
        f"Output energy charge: {join_msb_lsb(unsigned16(output_energy_charge, 1), unsigned16(output_energy_charge, 0))/10}"
    )

    output_energy_today = (
        client.read_input_registers(address=0x0020, count=1, unit=1).getRegister(0) / 10
    )
    print(f"output_energy_today: {output_energy_today}")

    input_energy_today = (
        client.read_input_registers(address=0x0023, count=1, unit=1).getRegister(0) / 10
    )
    print(f"input_energy_today: {input_energy_today}")

    power_dc1 = client.read_input_registers(address=0x00A, count=1, unit=1).getRegister(
        0
    )
    # print(f"Power DC1: {power_dc1}")

    power_dc2 = client.read_input_registers(address=0x00B, count=1, unit=1).getRegister(
        0
    )
    # print(f"Power DC2: {power_dc2}")

    total_power = power_dc1 + power_dc2
    print(f"Total power solar?: {total_power}W")

    sec = client.read_holding_registers(address=0x0085, count=1, unit=1).getRegister(0)
    min = client.read_holding_registers(address=0x0086, count=1, unit=1).getRegister(0)
    hr = client.read_holding_registers(address=0x0087, count=1, unit=1).getRegister(0)
    day = client.read_holding_registers(address=0x0088, count=1, unit=1).getRegister(0)
    mon = client.read_holding_registers(address=0x0089, count=1, unit=1).getRegister(0)
    year = client.read_holding_registers(address=0x008A, count=1, unit=1).getRegister(0)

    inverter_datetime = f"{(year+2000):02}-{mon:02}-{day:02} {hr:02}:{min:02}:{sec:02}"
    uploadTime = datetime.strptime(inverter_datetime, "%Y-%m-%d %H:%M:%S")
    uploadDate = uploadTime.date()

    print(uploadTime)

    # def timezone_converter(input_dt, current_tz='Europe/Bucharest', target_tz='UTC'):
    #    current_tz = pytz.timezone(current_tz)
    #    target_tz = pytz.timezone(target_tz)
    #    target_dt = current_tz.localize(input_dt).astimezone(target_tz)
    #    return target_tz.normalize(target_dt)

    timezone_difference_from_utc = 2
    uploadTime = uploadTime - timedelta(hours=timezone_difference_from_utc, minutes=0)

    print(uploadTime)
    print(uploadDate)

else:
    print("Cannot connect to the Modbus Server/Slave")
    exit()


import mysql.connector

# from datetime import datetime

mydb = mysql.connector.connect(
    host="172.17.7.77", user="root", passwd="rootroot", database="solax"
)

mycursor = mydb.cursor()

sn = "SPNXLAQHWX"

try:

    # create the sql statement
    sql = """REPLACE INTO solax_local (
                                      uploadTime,
                                      inverter_status,
                                      dc_solar_power,
                                      grid_voltage_r,
                                      grid_voltage_s,
                                      grid_voltage_t,
                                      battery_capacity,
                                      battery_power,
                                      feed_in_power,
                                      time_count_down,
                                      inverter_ac_power,
                                      consumeenergy,
                                      feedinenergy,
                                      power_dc1,
                                      power_dc2
           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           """
    # upload_time = datetime.now()

    values = (
        # upload_time,
        uploadTime,
        # mode[run_mode.getRegister(0)],
        run_mode,
        total_power,
        grid_voltage_r,
        grid_voltage_s,
        grid_voltage_t,
        battery_capacity,
        battery_charging,
        feed_in_power,
        time_count_down,
        inverter_ac_power,
        energy_from_grid,
        energy_to_grid,
        power_dc1,
        power_dc2,
    )

    mycursor.execute(sql, values)
    mydb.commit()
    print(values)

    # update daily values
    sql = """REPLACE INTO solax_daily (
                                      uploadDate,
                                      feed_in,
                                      total_yield
           ) VALUES (%s, %s, %s)
           """
    values = (uploadDate, feed_in_today, etoday_togrid)
    mycursor.execute(sql, values)
    mydb.commit()
    print(values)


except mysql.connector.Error as error:
    print("parameterized query failed {}".format(error))

    with open("/tmp/solax_numbers.log", "a") as l:
        l.write(f"Battery charging: {battery_charging}, {battery_charging:b}\n")
        l.write(
            f"feed_in_power inst: {join_msb_lsb(unsigned16(feed_in_power_bytes, 1), unsigned16(feed_in_power_bytes, 0))}W,  {join_msb_lsb(unsigned16(feed_in_power_bytes, 1), unsigned16(feed_in_power_bytes, 0)):b}\n"
        )
        l.write("\n\n")


print("ok")


client.close()
