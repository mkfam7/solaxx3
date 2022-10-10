from pymodbus.client.sync import ModbusSerialClient
from datetime import date, datetime, timedelta
from struct import *
import mysql.connector
from solaxx3.rs485 import SolaxX3G4


s = SolaxX3G4(port="/dev/ttyUSB0", baudrate=115200)


if s.connect():
    # print(s.read("battery_capacity"))
    # print(s.read("serial_number"))
    # print(s.list_register_names())
    # print(s.read("firmware_version_dsp"))
    # print(s.read("temperature_battery"))

    for i in s.list_register_names():
        print(f"{i}: {s.read(i)}")

    exit()

    timezone_difference_from_utc = 2

    uploadTime = s.read("rtc_datetime")[0]
    uploadDate = uploadTime.date()

    # convert to UTC
    uploadTime = uploadTime - timedelta(hours=timezone_difference_from_utc, minutes=0)

    print(uploadTime)
    print(uploadDate)


else:
    print("Cannot connect to the Modbus Server/Slave")
    exit()


mydb = mysql.connector.connect(
    host="172.17.7.77", user="root", passwd="rootroot", database="solax"
)

mycursor = mydb.cursor()


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
        uploadTime,
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

    # mycursor.execute(sql, values)
    # mydb.commit()
    print(values)

    # update daily values
    sql = """REPLACE INTO solax_daily (
                                      uploadDate,
                                      feed_in,
                                      total_yield
           ) VALUES (%s, %s, %s)
           """
    values = (uploadDate, feed_in_today, etoday_togrid)
    # mycursor.execute(sql, values)
    # mydb.commit()
    print(values)


except mysql.connector.Error as error:
    print("parameterized query failed {}".format(error))

    with open("/tmp/solax_numbers.log", "a") as l:
        l.write(f"Battery charging: {battery_charging}, {battery_charging:b}\n")
        l.write(
            f"feed_in_power inst: {join_msb_lsb(unsigned16(feed_in_power_bytes, 1), unsigned16(feed_in_power_bytes, 0))}W,  {join_msb_lsb(unsigned16(feed_in_power_bytes, 1), unsigned16(feed_in_power_bytes, 0)):b}\n"
        )
        l.write("\n\n")


# client.close()
