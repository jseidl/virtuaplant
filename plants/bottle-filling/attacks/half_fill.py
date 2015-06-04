
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.exceptions import ConnectionException
import time
import logging

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

#####################################
# Code
#####################################
RATIO = 2
def init_was_zero():
    rr = client.read_holding_registers(0x4, 1)
    return rr.registers[0] == 0

def calibrate_time():
    calibrated = False
    was_zero = init_was_zero()
    while not calibrated:
        rr = client.read_holding_registers(0x4, 1)
        if rr.registers[0] == 1:
            if was_zero:
                    start = time.clock()

        else :
            if not was_zero:
                if statt in locals():
                    fill_time = time.clock() - start
                    calibrated = True
        was_zero = rr.registers[0] == 0

    return fill_time

client = ModbusClient('localhost', port=5020)
fill_time = 0
try:
    client.connect()
    while True:
        if fill_time == 0:
            fill_time = calibrate_time()

        rr = client.read_holding_registers(0x4, 1)
        if rr.registers[0] == 1:
            time.sleep(2.7*fill_time/RATIO)
            rq = client.write_register(0x10, 1) # Run Plant, Run!
            rq = client.write_register(0x1, 1) # Level Sensor
            rq = client.write_register(0x2, 0) # Limit Switch
            rq = client.write_register(0x3, 0) # Motor
            rq = client.write_register(0x4, 0) # Nozzle
except KeyboardInterrupt:
    client.close()
except ConnectionException:
    print "Unable to connect / Connection lost"
