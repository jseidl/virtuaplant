#!/usr/bin/python
# -*- coding: utf-8 -*-
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.exceptions import ConnectionException
import time
import logging
import json

#####################################
# Code
#####################################   
INTERVAL = 1
DURATION = 60
CYCLE_LENGTH = 15
data = {}

def get_data():
    client = ModbusClient('localhost', port=5020)
    try:
        client.connect()
        for i in range(DURATION):
            time.sleep(INTERVAL)
            rr = client.read_holding_registers(0x1, 4)
            data[i] = {
                    "levelSensor" : rr.registers[0], 
                    "limitSwitch" : rr.registers[1],
                    "motor" : rr.registers[2],
                    "nozzle" : rr.registers[3]
                    }
        with open('states_data.txt', 'w') as fd:
            json.dump(data, fd)
    except KeyboardInterrupt:
        client.close()
    except ConnectionException:
        print "Unable to connect / Connection lost"

def parse_data():
    data = {}
    result = {}
    with open('states_data.txt', 'r') as fd:
        data = json.load(fd)

    for i in data.keys():
        j = int(i) % CYCLE_LENGTH
        if j not in result:
            result[j] =  {
                   "levelSensor" : [data[i]['levelSensor']],
                   "limitSwitch" : [data[i]['limitSwitch']],
                    "motor" : [data[i]['motor']],
                    "nozzle" : [data[i]['nozzle']]
                        }
        else:
            if data[i]['levelSensor'] not in result[j]['levelSensor'] :
                result[j]['levelSensor'].append(data[i]['levelSensor'])

            if data[i]['limitSwitch'] not in result[j]['limitSwitch'] :
               result[j]['limitSwitch'].append(data[i]['limitSwitch'])

            if data[i]['motor'] not in result[j]['motor']:
                result[j]['motor'].append(data[i]['motor'])

            if data[i]['nozzle'] not in result[j]['nozzle']:
                result[j]['nozzle'].append(data[i]['nozzle'])

    for state in result:
        print result[state]

parse_data()
