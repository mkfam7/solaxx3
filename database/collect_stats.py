"""Sample program for reading and saving some registers from the inverter."""

from datetime import timedelta

import mysql.connector

from solaxx3.solaxx3 import SolaxX3

s = SolaxX3(port="/dev/ttyUSB0", baudrate=115200)

DATABASE_IP = "172.17.7.77"

if s.connect():
    s.read_all_registers()

    # read the stats from the inverter
    battery_capacity = s.read("battery_capacity")[0]
    feed_in_today = s.read("feed_in_energy_today")[0]
    consumtion_today = s.read("consumption_energy_today")[0]
    battery_charging = s.read("battery_power_charge1")[0]
    grid_voltage_r = s.read("grid_voltage_r")[0]
    grid_voltage_s = s.read("grid_voltage_s")[0]
    grid_voltage_t = s.read("grid_voltage_t")[0]
    run_mode = s.read("run_mode")[0]
    time_count_down = s.read("time_count_down")[0]
    inverter_ac_power = s.read("grid_power")[0]
    etoday_togrid = s.read("energy_to_grid_today")[0]
    solar_energy_today = s.read("solar_energy_today")[0]
    echarge_today = s.read("echarge_today")[0]
    energy_from_grid = s.read("energy_from_grid_meter")[0]
    energy_to_grid = s.read("energy_to_grid_meter")[0]
    power_to_ev = s.read("power_to_ev")[0]
    feed_in_power = s.read("feed_in_power")[0]
    output_energy_charge = s.read("output_energy_charge")[0]
    output_energy_today = s.read("output_energy_charge_today")[0]
    input_energy_today = s.read("input_energy_charge_today")[0]
    power_dc1 = s.read("power_dc1")[0]
    power_dc2 = s.read("power_dc2")[0]
    total_power = power_dc1 + power_dc2
    uploadTime = s.read("rtc_datetime")[0]
    uploadDate = uploadTime.date()

    TIMEZONE_DIFFERENCE_FROM_UTC = 2
    uploadTime = uploadTime - timedelta(hours=TIMEZONE_DIFFERENCE_FROM_UTC, minutes=0)

    # store the stats in the database
    mydb = mysql.connector.connect(
        host=DATABASE_IP, user="root", passwd="rootroot", database="solax"
    )
    mycursor = mydb.cursor()

    try:
        # create the sql statement
        SQL_QUERY = """REPLACE INTO solax_local (
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

        mycursor.execute(SQL_QUERY, values)
        mydb.commit()

        # update daily values
        SQL_QUERY = """REPLACE INTO solax_daily (
                                        uploadDate,
                                        feed_in,
                                        total_yield
            ) VALUES (%s, %s, %s)
            """
        values = (uploadDate, feed_in_today, etoday_togrid)
        mycursor.execute(SQL_QUERY, values)
        mydb.commit()

    except mysql.connector.Error as error:
        print(f"parameterized query failed {error}")

else:
    print("Cannot connect to the Modbus Server/Slave")
