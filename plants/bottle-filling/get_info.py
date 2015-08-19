#!/usr/bin/python
# -*- coding: utf-8 -*-
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
interval = 1
duration = 20

client = ModbusClient('localhost', port=5020)
try:
    client.connect()
    for i in range(duration):
        time.sleep(interval)
        rr = client.read_holding_registers(0x1, 4)
        print "Level Sensor : " + str(rr.registers[0])
        print "Limit Switch : " + str(rr.registers[1])
        print "Motor : " + str(rr.registers[2])
        print "Nozzle : " + str(rr.registers[3])
        print "\n"
        #Read all registers
        #Copy them
except KeyboardInterrupt:
    client.close()
except ConnectionException:
    print "Unable to connect / Connection lost"

