#!/usr/bin/env python

from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.exceptions import ConnectionException
import logging

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

#####################################
# Code
#####################################
client = ModbusClient('localhost', port=5020)

try:
    client.connect()
    while True:
        rq = client.write_register(0x10, 1) # Run Plant, Run!
        rq = client.write_register(0x1, 0) # Level Sensor
        rq = client.write_register(0x2, 0) # Limit Switch
        rq = client.write_register(0x3, 1) # Motor
        rq = client.write_register(0x4, 1) # Nozzle
except KeyboardInterrupt:
    client.close()
except ConnectionException:
    print "Unable to connect / Connection lost"
