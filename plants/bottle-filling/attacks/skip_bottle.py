
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
client = ModbusClient('localhost', port=5020)
BOTTLE_TO_SKIP = 1
bottle_counter = 0
was_zero = True
try:
    client.connect()
    while True:
        rr = client.read_holding_registers(0x2, 1)
        if rr.registers[0] == 1:
            if was_zero:
                bottle_counter += 1
                if bottle_counter <= BOTTLE_TO_SKIP:
                    rq = client.write_register(0x10, 1) # Run Plant, Run!
                    rq = client.write_register(0x2, 0) # Limit Switch
                    rq = client.write_register(0x4, 0) # Nozzle
                else:
                    bottle_counter = 0
        was_zero = rr.registers[0] == 0
except KeyboardInterrupt:
    client.close()
except ConnectionException:
    print "Unable to connect / Connection lost"
