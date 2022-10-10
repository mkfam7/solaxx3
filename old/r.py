from pymodbus.client.sync import ModbusSerialClient
from datetime import date

def unsigned16(result, addr):
    return result.getRegister(addr)

def join_msb_lsb(msb, lsb):
    return (msb << 16) | lsb


def is_negative(byte):
    pass

client = ModbusSerialClient(
    method='rtu',
    port='/dev/ttyUSB0',
    #baudrate=9600,
    baudrate=115200,
    timeout=3,
    parity='N',
    stopbits=1,
    bytesize=8
)

if client.connect():  # Trying for connect to Modbus Server/Slave
    '''Reading from a holding register with the below content.'''

    #print("Client connected successfully...")

    #res = client.read_input_registers(address=0x0096, count=1, unit=1)
    res = client.read_input_registers(address=0x0213, count=1, unit=1)
    #res = client.read_input_registers(address=0x0098, count=2, unit=1)

    #restotal = join_msb_lsb(unsigned16(res, 1), unsigned16(res, 0))

    battery_capacity = client.read_input_registers(address=0x01C, count=1, unit=1).getRegister(0)
    print(f"Battery capacity: {battery_capacity}%")

    feed_in_today_pack = client.read_input_registers(address=0x0098, count=2, unit=1)
    print(f"Feedin today: {join_msb_lsb(unsigned16(feed_in_today_pack, 1), unsigned16(feed_in_today_pack, 0))/100}")
    feed_in_today = join_msb_lsb(unsigned16(feed_in_today_pack, 1), unsigned16(feed_in_today_pack, 0))/100


    breakpoint()
    #consumtion_today = client.read_input_registers(address=0x009A, count=2, unit=1)
    #print(f"Consumption today: {join_msb_lsb(unsigned16(consumtion_today, 1), unsigned16(consumtion_today, 0))}")

    #battery_voltage = client.read_input_registers(address=0x0014, count=1, unit=1)
    #print(f"Battery voltage: {battery_voltage.getRegister(0)/10}")

    #battery_current = client.read_input_registers(address=0x0015, count=1, unit=1).getRegister(0)
    #if battery_current > 0x8000:
    #    battery_current = ~battery_current+1 
    #print(f"Battery current: {battery_current/10}")

    battery_charging = client.read_input_registers(address=0x0016, count=1, unit=1).getRegister(0)
    battery_charging = battery_charging % 65536
    #if battery_charging > 0x80:
    #    battery_charging = battery_charging - 65536

    print(f"Battery charging: {battery_charging}" )

    #ref_power_to_ev = client.read_input_registers(address=0x0016, count=1, unit=1)
    #print(f"ref_power_to_ev: {ref_power_to_ev.getRegister(0)}")

    grid_voltage_r = client.read_input_registers(address=0x006A, count=1, unit=1).getRegister(0)/10
    print(f"Grid voltage R: {grid_voltage_r}V")

    grid_voltage_s = client.read_input_registers(address=0x006E, count=1, unit=1).getRegister(0)/10
    print(f"Grid voltage S: {grid_voltage_s}V")

    grid_voltage_t = client.read_input_registers(address=0x0072, count=1, unit=1).getRegister(0)/10
    print(f"Grid voltage T: {grid_voltage_t}V")

    mode = { 0: "Waiting",
             1: "Checking",
             2: "Normal",
             3: "Fault",
             4: "Permanent fault",
             5: "Update",
             6: "Off-grid waiting",
             7: "Off-grid",
             8: "Self testing",
             9: "Idle",
             10: "Standby"
           } 
    run_mode = client.read_input_registers(address=0x0009, count=1, unit=1).getRegister(0)
    print(f"Run mode: {mode[run_mode]}")

    time_count_down = client.read_input_registers(address=0x0013, count=1, unit=1).getRegister(0)
    print(f"time_count_down: {time_count_down}")

    inverter_ac_power = client.read_input_registers(address=0x0002, count=1, unit=1).getRegister(0)
    print(f"inverter ac power???: {inverter_ac_power}")

    #d = client.read_input_registers(address=0x0016, count=1, unit=1)
    #print(f"something 1: {d.getRegister(0)}")

    #c = client.read_input_registers(address=0x0026, count=2, unit=1)
    #print(f"something 2: {join_msb_lsb(unsigned16(c, 1), unsigned16(c, 0))/10}")

    power_to_ev = client.read_input_registers(address=0x0026, count=2, unit=1)
    print(f"power_to_ev: {join_msb_lsb(unsigned16(power_to_ev, 1), unsigned16(power_to_ev, 0))}")

    feed_in_power_bytes = client.read_input_registers(address=0x0046, count=2, unit=1)
    print(f"feed_in_power inst: {join_msb_lsb(unsigned16(feed_in_power_bytes, 1), unsigned16(feed_in_power_bytes, 0))}W")
    feed_in_power = join_msb_lsb(unsigned16(feed_in_power_bytes, 1), unsigned16(feed_in_power_bytes, 0))
    #if feed_in_power > 0x8000:
    #    feed_in_power = ~feed_in_power+1
    feed_in_power = feed_in_power % 65536
    #if feed_in_power > 0x8000:
    #    feed_in_power = feed_in_power - 65536

    #power_to_ev = client.read_input_registers(address=0x0026, count=2, unit=1)
    #print(f"power_to_ev: {join_msb_lsb(unsigned16(power_to_ev, 1), unsigned16(power_to_ev, 0))}")

    #output_energy_charge = client.read_input_registers(address=0x001D, count=2, unit=1)
    #print(f"Output energy charge: {join_msb_lsb(unsigned16(output_energy_charge, 1), unsigned16(output_energy_charge, 0))/10}")

    #input_energy_charge = client.read_input_registers(address=0x0021, count=2, unit=1)
    #print(f"Input energy charge: {join_msb_lsb(unsigned16(input_energy_charge, 1), unsigned16(input_energy_charge, 0))/10}")

    power_dc1 = client.read_input_registers(address=0x00A, count=1, unit=1)
    #print(f"Power DC1: {power_dc1.getRegister(0)}")
    power_dc2 = client.read_input_registers(address=0x00B, count=1, unit=1)
    #print(f"Power DC2: {power_dc2.getRegister(0)}")    
    total_power = power_dc1.getRegister(0) + power_dc2.getRegister(0)
    print(f"Total power solar?: {total_power}W")

    #if not res.isError():
    #   print(res.registers)
    #    #print(restotal)
    #else:
    #    print(res)

else:
    print('Cannot connect to the Modbus Server/Slave')
    exit()


import mysql.connector
from datetime import datetime

mydb = mysql.connector.connect(
  host="172.17.7.77",
  user="root",
  passwd="rootroot",
  database="solax"
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
                                      inverter_ac_power
           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           """
    upload_time = datetime.now()

    values = (
           upload_time,
           #mode[run_mode.getRegister(0)],
           run_mode,
           total_power,
           grid_voltage_r,
           grid_voltage_s,
           grid_voltage_t,
           battery_capacity,
           battery_charging,
           feed_in_power,
           time_count_down,
           inverter_ac_power           
           )
           
    mycursor.execute(sql, values)
    mydb.commit()
    print(values)

    # update daily values
    sql = """REPLACE INTO solax_daily (
                                      uploadDate,
                                      feed_in
           ) VALUES (%s, %s)
           """
    values = (
             date.today(),
             feed_in_today 
            )
    mycursor.execute(sql, values)
    mydb.commit()
    print(values)
    
    
except mysql.connector.Error as error:
    print("parameterized query failed {}".format(error))


print("ok")





client.close()
