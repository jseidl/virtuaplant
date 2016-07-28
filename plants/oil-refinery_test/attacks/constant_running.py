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
        rq = client.write_register(0x01, 1) # Run Plant, Run!
        rq = client.write_register(0x02, 0) # Level Sensor
        rq = client.write_register(0x04, 0) # Limit Switch
        
except KeyboardInterrupt:
    client.close()
except ConnectionException:
    print "Unable to connect / Connection lost"
