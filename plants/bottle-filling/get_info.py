#!/usr/bin/python
# -*- coding: utf-8 -*-
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.exceptions import ConnectionException
import time
import logging
import json
import argparse
import sys

#####################################
# Code
#####################################   
#INTERVAL = 1
#DURATION = 60
#CYCLE_LENGTH = 15
data = {}

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--initiate", type=int, help="Calibrate the operating cycle (3 arguments expected: interval cycle_length and duration)", nargs='+')
    parser.add_argument("-m", "--monitor", help="If initiated, start the monitoring", action="store_true")

    return parser.parse_args()

def get_data(client, interval, duration):
    for i in range(duration):
        time.sleep(interval)
        rr = client.read_holding_registers(0x1, 4)
        data[i] = {
                  "levelSensor" : rr.registers[0], 
                   "limitSwitch" : rr.registers[1],
                   "motor" : rr.registers[2],
                   "nozzle" : rr.registers[3]
                   }
    with open('states_data.txt', 'w') as fd:
        json.dump(data, fd)

def parse_data(cycle_length):
    data = {}
    result = {}
    with open('states_data.txt', 'r') as fd:
        data = json.load(fd)

    for i in data.keys():
        j = int(i) % cycle_length
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
    
    with open('states_result.txt', 'w') as fr:
            json.dump(result, fr)

def monitor(client, interval, cycle_length):
    with open('states_result.txt', 'r') as fr:
        states = json.load(fr)
    j = 0
    while True :
        time.sleep(interval)
        distance = 0
        rr = client.read_holding_registers(0x1, 4)
        print j
        print states[str(j)]
        if rr.registers[0] not in states[str(j)]['levelSensor']:
            print "Alert: unexpected state: levelSensor"
            distance = distance+1
        if rr.registers[1] not in states[str(j)]['limitSwitch']:
            print "Alert: unexpected state: limitSwitch"
            distance = distance+1
        if rr.registers[2] not in states[str(j)]['motor']:
            print "Alert: unexpected state: motor"
            distance = distance+1
        if rr.registers[3] not in states[str(j)]['nozzle']:
            print "Alert: unexpected state: nozzle"
            distance = distance+1
        if distance > 0:
            print "Distance from normal state: "+str(distance)

        j = (j+1)%cycle_length

def wait_for_beginning(client):
    was_zero = True
    while True:
        try:
            rr = client.read_holding_registers(0x2, 1)
            if rr.registers[0] == 1:
                if was_zero:
                    return
            was_zero = rr.registers[0] == 0
        except KeyboardInterrupt:
            return
        except ConnectionException:
            return

def get_cycle_length(client):
    wait_for_beginning
    start_time = time.time()
    wait_for_beginning(client)
    return time.time() - start_time

if __name__ == "__main__":
    client = ModbusClient('localhost', port=5020)
    try:
        client.connect()
        args = parse_args()
        if args.initiate:
            if len(args.initiate) != 2:
                print "Error, -i (--initiate) takes two arguments: interval and iteration"
                sys.exit(0)
            print "Start initialization"
            print "Measuring cycle duration"
            cycle_length = int(get_cycle_length(client))
            print "Cycle duration: "+str(cycle_length)
            if cycle_length > args.initiate[1]:
                print "Error, cycle length must be less than duration"
                sys.exit(0)
            get_data(client, args.initiate[0], args.initiate[1])
            print "Measures done"
            parse_data(cycle_length)
        elif args.monitor:
            monitor(client, 1, 15)
    except KeyboardInterrupt:
        client.close()
    except ConnectionException:
        print "Unable to connect / Connection lost"
    sys.exit(0)
